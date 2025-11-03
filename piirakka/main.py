import asyncio
import json
import logging
import os
from datetime import datetime
from http import HTTPMethod

import anyio
import uvicorn
from jinja2 import Environment, FileSystemLoader
from setproctitle import setproctitle
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import piirakka.model.event as events
import piirakka.preflight as preflight
from piirakka.__version__ import __version__
from piirakka.model.player import Player
from piirakka.model.recent_track import RecentTrack
from piirakka.model.sidebar_item import sidebar_items
from piirakka.model.station import Station

setproctitle("piirakka")
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="piirakka/templates")

# TODO: hacking to get jinja rendering working,
# doesn't necessarily have to be done twice
file_loader = FileSystemLoader("piirakka/templates")
env = Environment(loader=file_loader)


class Context:
    SPAWN_MPV = os.getenv("MPV", True)
    SOCKET = os.getenv("SOCKET", preflight.generate_socket_path())
    DATABASE = os.getenv("DATABASE", preflight.DB_PATH)
    TRACK_HISTORY_LENGTH = 50

    def player_callback(self, message):
        #loop = asyncio.get_event_loop()
        #loop.create_task(broadcast_message(str(message)))
        match message:  # TODO: doesn't really need matching if pydantic validation passed
            case events.PlayerBarUpdateEvent():
                payload = message.model_dump_json()
                logging.info(f"Broadcasting Websocket message {payload}")
                anyio.from_thread.run(broadcast_message, payload)
            case events.TrackChangeEvent():
                payload = message.model_dump_json()
                logging.info(f"Broadcasting Websocket message {payload}")
                anyio.from_thread.run(broadcast_message, payload)

    def __init__(self):
        self.player = Player(self.SPAWN_MPV, self.SOCKET, self.DATABASE, self.player_callback)
        self.track_history: list[RecentTrack] = []
        self.subscribers = []
        self.db_engine = create_engine(f"sqlite:///{self.DATABASE}", echo=False)

    async def push_player_bar(self):
        player_bar_status = self.player.get_player_state()
        message = events.PlayerBarUpdateEvent(content=player_bar_status)
        await broadcast_message(message.model_dump_json())

    async def push_track(self, track: RecentTrack):
        # updates the in-memory track history
        # and broadcasts updates to websocket subscribers
        if len(self.track_history) == self.TRACK_HISTORY_LENGTH:
            self.track_history.pop()
        self.track_history.insert(0, track)
        message = events.TrackChangeEvent(content=track)

        await broadcast_message(message.model_dump_json())
        await self.push_player_bar()  # also refresh player bar

    def render_bitrate(self) -> str:
        try:
            bitrate = self.player.get_bitrate()
            return f"{round(bitrate / 1000)} kbps"
        except TypeError:
            return "unknown bitrate"


context = Context()


class WebSocketConnection(WebSocketEndpoint):
    encoding = 'text'

    async def on_connect(self, websocket):
        await websocket.accept()
        context.subscribers.append(websocket)

    async def on_disconnect(self, websocket, close_code):
        context.subscribers.remove(websocket)

    async def on_receive(self, websocket, data):
        print(f"Received message: {data}")
        await broadcast_message(data)

async def broadcast_message(message):
    for subscriber in context.subscribers:
        await subscriber.send_text(message)

def task(callback):
    # placeholder
    callback("task")

async def observe_current_track(interval: int = 1):
    while True:
        await asyncio.sleep(interval)
        current_track_title = context.player.current_track()
        if current_track_title is None:
            # did not get Icy-Title
            continue
        else:
            current_track = RecentTrack(
                        title=current_track_title,
                        station=context.player.current_station.name,
                        timestamp=datetime.now().strftime('%H:%M')
                    )

        if len(context.track_history) == 0:
            await context.push_track(current_track)
        elif context.track_history[0].title == current_track_title:
            # track hasn't changed
            continue
        else:
            await context.push_track(current_track)


###--- endpoints

async def index(request):
    return templates.TemplateResponse("index.html",
        {
            "request": request,
            "sidebar_items": sidebar_items,
            "stations": context.player.stations,
            "recent_tracks": context.track_history,
            "volume": context.player.get_volume(),
            "playing": context.player.get_status(),
            "track_name": context.track_history[0].title if len(context.track_history) > 0 else '',
            "station_name": context.player.current_station.name,
            "bitrate": context.render_bitrate(),
            "codec": context.player.get_codec()
        }
    )

async def stations_page(request):
    return templates.TemplateResponse("legacy_stations.html",
                {
                    "request": request,
                    "stations": context.player.stations
                }
    )

async def set_station(request):
    station_id = request.path_params['station_id']
    task = BackgroundTask(context.player.play_station_with_id, station_id)
    return JSONResponse({"message": "station change initiated"}, background=task)

async def toggle_playback(request):
    task = BackgroundTask(context.player.toggle)
    return JSONResponse({"message": "toggle initiated"}, background=task)

async def set_volume(request):
    data = await request.json()
    volume = int(data.get('volume'))
    task = BackgroundTask(context.player.set_volume, volume)
    return JSONResponse({"message": "volume change initiated"}, background=task)

async def shuffle_station(request):
    task = BackgroundTask(context.player.shuffle)
    return JSONResponse({"message": "station shuffle initiated"}, background=task)

async def create_station(request):
    data = await request.json()
    station = Station(
        name=data.get('station_name'),
        url=data.get('station_url')
    )
    with Session(context.db_engine) as session:
        session.add(station)
        session.commit()
        # ensure the instance has its attributes loaded while the session is still open
        session.refresh(station)
    context.player.update_stations()
    return JSONResponse({"message": "station created successfully"})

app = Starlette(
    routes=[
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        Route('/api/station', create_station, methods=[HTTPMethod.POST]),
        Route('/api/radio/station/{station_id}', set_station, methods=[HTTPMethod.PUT]),
        Route('/api/radio/toggle', toggle_playback, methods=[HTTPMethod.PUT]),
        Route('/api/radio/volume', set_volume, methods=[HTTPMethod.PUT]),
        Route('/api/radio/shuffle', shuffle_station, methods=[HTTPMethod.PUT]),
        WebSocketRoute("/ws/socket", WebSocketConnection),
        Mount("/static", app=StaticFiles(directory="piirakka/static"), name="static"),
    ]
)

@app.on_event("startup")
async def startup():
    asyncio.create_task(observe_current_track())

@app.on_event("shutdown")
async def shutdown():
    for subscriber in context.subscribers:
        await subscriber.close()

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, timeout_graceful_shutdown=5, log_config=preflight.LOGGING_CONFIG)


if __name__ == "__main__":
    logger.info(f"Starting piirakka v{__version__}")
    main()
