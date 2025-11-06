import asyncio
import json
import logging
import os
from datetime import datetime
from http import HTTPMethod

import anyio
import uvicorn
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
from piirakka.model.station import create_station, list_stations

setproctitle("piirakka")
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="piirakka/templates")


class Context:
    SPAWN_MPV = os.getenv("MPV", True)
    SOCKET = os.getenv("SOCKET", preflight.generate_socket_path())
    DATABASE = os.getenv("DATABASE", preflight.DB_PATH)
    TRACK_HISTORY_LENGTH = 50

    def player_callback(self, message):
        # loop = asyncio.get_event_loop()
        # loop.create_task(broadcast_message(str(message)))

        logging.info(f"Received event {type(message)} from player via callback")
        payload = self.serialize_events(message)
        logging.info(f"Broadcasting Websocket message {payload}")
        anyio.from_thread.run(broadcast_message, payload)

    def __init__(self):
        self.player = Player(self.SPAWN_MPV, self.SOCKET, self.DATABASE, self.player_callback)
        self.track_history: list[RecentTrack] = []
        self.subscribers = []
        self.db_engine = create_engine(f"sqlite:///{self.DATABASE}", echo=False)

        with Session(self.db_engine) as session:
            stations = list_stations(session)
            stations_pydantic = [s.to_pydantic() for s in stations]
            self.player.update_stations(stations_pydantic)
            if len(stations) > 0:
                # set initial station if db is populated
                default_index = 0
                self.player.current_station_id = str(stations[default_index].station_id)
                self.player.play_station_with_id(self.player.current_station_id)

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

        track_update_message = events.TrackChangeEvent(content=track)

        # track change also refreshes player bar in the same broadcast
        player_bar_update_message = events.PlayerBarUpdateEvent(content=self.player.get_player_state())
        message = self.serialize_events(track_update_message, player_bar_update_message)

        await broadcast_message(message=message)

    @staticmethod
    def serialize_events(*args) -> str:
        # accepts events and serializes to json
        payload = {"events": []}
        for event in args:
            payload["events"].append(event.model_dump())
        return json.dumps(payload)


context = Context()


class WebSocketConnection(WebSocketEndpoint):
    encoding = "text"

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
                timestamp=datetime.now().strftime("%H:%M"),
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
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sidebar_items": sidebar_items,
            "stations": context.player.stations,
            "recent_tracks": context.track_history,
            "volume": context.player.get_volume(),
            "playing": context.player.get_status(),
            "track_name": context.track_history[0].title if len(context.track_history) > 0 else "",
            "station_name": context.player.current_station.name,
        },
    )


async def stations_page(request):
    return templates.TemplateResponse("legacy_stations.html", {"request": request, "stations": context.player.stations})


async def set_station(request):
    station_id = request.path_params["station_id"]
    task = BackgroundTask(context.player.play_station_with_id, station_id)
    return JSONResponse({"message": "station change initiated"}, background=task)


async def toggle_playback(request):
    task = BackgroundTask(context.player.toggle)
    return JSONResponse({"message": "toggle initiated"}, background=task)


async def set_volume(request):
    data = await request.json()
    volume = int(data.get("volume"))
    task = BackgroundTask(context.player.set_volume, volume)
    return JSONResponse({"message": "volume change initiated"}, background=task)


async def shuffle_station(request):
    task = BackgroundTask(context.player.shuffle)
    return JSONResponse({"message": "station shuffle initiated"}, background=task)


async def create_station_handler(request):
    data = await request.json()
    name = data.get("station_name")
    url = data.get("station_url")

    with Session(context.db_engine) as session:
        create_station(session, name, url)

    with Session(context.db_engine) as session:
        stations = list_stations(session)
        stations_pydantic = [s.to_pydantic() for s in stations]
        context.player.update_stations(stations_pydantic)

    return JSONResponse({"message": "station created successfully"})


app = Starlette(
    routes=[
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        Route("/api/station", create_station_handler, methods=[HTTPMethod.POST]),
        Route("/api/radio/station/{station_id}", set_station, methods=[HTTPMethod.PUT]),
        Route("/api/radio/toggle", toggle_playback, methods=[HTTPMethod.PUT]),
        Route("/api/radio/volume", set_volume, methods=[HTTPMethod.PUT]),
        Route("/api/radio/shuffle", shuffle_station, methods=[HTTPMethod.PUT]),
        WebSocketRoute("/ws/subscribe", WebSocketConnection),
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
    uvicorn.run(
        app, host="0.0.0.0", port=8000, workers=1, timeout_graceful_shutdown=5, log_config=preflight.LOGGING_CONFIG
    )


if __name__ == "__main__":
    logger.info(f"Starting piirakka v{__version__}")
    main()
