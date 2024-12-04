import os

from datetime import datetime
from http import HTTPMethod
import json

from jinja2 import Environment, FileSystemLoader

#from setproctitle import setproctitle
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import uvicorn
import asyncio

import piirakka.model.event as events
from piirakka.model.player import Player
from piirakka.model.station import Station
from piirakka.model.recent_track import RecentTrack
from piirakka.model.sidebar_item import sidebar_items


#setproctitle("piirakka")


templates = Jinja2Templates(directory="piirakka/templates")

# TODO: hacking to get jinja rendering working,
# doesn't necessarily have to be done twice
file_loader = FileSystemLoader("piirakka/templates")
env = Environment(loader=file_loader)

if False:  # cheap seeding
    engine = create_engine("sqlite:///piirakka.db", echo=True)
    with Session(engine) as session:
        junkkaa = Station(
            name="junkkaa",
            url="http://andromeda.shoutca.st/tunein/differentdrumz.pls"
        )
        lush = Station(
            name="lush",
            url="https://api.somafm.com/lush.pls"
        )
        session.add_all([junkkaa, lush])
        session.commit()

class Context:
    SPAWN_MPV = os.getenv("MPV", True)
    SOCKET = os.getenv("SOCKET", "/tmp/piirakka.sock")
    DATABASE = os.getenv("DATABASE", "piirakka.db")
    TRACK_HISTORY_LENGTH = 50

    @staticmethod
    def player_callback(message):
        loop = asyncio.get_event_loop()
        loop.create_task(broadcast_message(str(message)))

    def __init__(self):
        self.player = Player(self.SPAWN_MPV, self.SOCKET, self.DATABASE, self.player_callback)
        self.track_history: list[RecentTrack] = []
        self.subscribers = []

    async def push_track(self, track):
        if len(self.track_history) == self.TRACK_HISTORY_LENGTH:
            self.track_history.pop()
        self.track_history.insert(0, track)
        template = env.get_template('components/track_history.html')
        html = template.render(recent_tracks=self.track_history)
        await broadcast_message(json.dumps(events.TrackChangeEvent(html=html).model_dump()))  # TODO: functionize

context = Context()


class WebSocketConnection(WebSocketEndpoint):
    encoding = 'text'

    async def on_connect(self, websocket):
        await websocket.accept()
        context.subscribers.append(websocket)
        print("New connection accepted")

    async def on_disconnect(self, websocket, close_code):
        context.subscribers.remove(websocket)
        print("Connection closed")

    async def on_receive(self, websocket, data):
        print(f"Received message: {data}")
        await broadcast_message(data)

async def broadcast_message(message):
    for subscriber in context.subscribers:
        await subscriber.send_text(message)

def task(callback):
    # placeholder
    callback("task")

async def observe_current_track(interval: int = 5):
    while True:
        await asyncio.sleep(interval)
        current_track_title = context.player.current_track()
        if current_track_title == None:
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
            "bitrate": f"{context.player.get_bitrate() / 1000} kbps",
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
    # TODO:
    pass

async def new(request):
    # TODO: dev route for new grid layout
    return templates.TemplateResponse("new_grid.html",
        {
            "request": request,
            "sidebar_items": sidebar_items,
            "stations": context.player.stations,
            "recent_tracks": context.track_history,
            "volume": context.player.get_volume(),
            "playing": context.player.get_status(),
            "track_name": context.track_history[0].title if len(context.track_history) > 0 else '',
            "station_name": context.player.current_station.name,
            "bitrate": f"{context.player.get_bitrate() / 1000} kbps",
            "codec": context.player.get_codec()
        }
    )

app = Starlette(
    routes=[
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        Route("/new", endpoint=new, methods=[HTTPMethod.GET]),
        Route('/api/radio/station/{station_id}', set_station, methods=[HTTPMethod.PUT]),
        Route('/api/radio/toggle', toggle_playback, methods=[HTTPMethod.PUT]),
        Route('/api/radio/volume', set_volume, methods=[HTTPMethod.PUT]),
        WebSocketRoute("/api/websocket", WebSocketConnection),
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

