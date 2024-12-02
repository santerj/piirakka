import os

from http import HTTPMethod

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import PlainTextResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import uvicorn
import asyncio

from piirakka.model.player import Player
from piirakka.model.station import Station
from piirakka.model.sidebar_item import sidebar_items


templates = Jinja2Templates(directory="piirakka/templates")

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
        self.track_history = []
        self.subscribers = []

    def push_track(self, track):
        if len(self.track_history) > self.TRACK_HISTORY_LENGTH:
            self.track_history.pop()
        self.track_history.insert(track)
        # TODO: broadcast via websocket

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

async def background_task():
    while True:
        await asyncio.sleep(5)
        task(context.player_callback)

###--- endpoints

async def index(request):
    return templates.TemplateResponse("index.html",
        {
            "request": request,
            "sidebar_items": sidebar_items,
            # placeholders
            "stations": [i for i in range(30)],
            "recent_tracks": [f"Artist name – Track name which is long (Remastered 2009) {i}" for i in range(50)]
        }
    )

async def stations_page(request):
    return templates.TemplateResponse("legacy_stations.html",
                {
                    "request": request,
                    "stations": context.player.stations
                }
    )


app = Starlette(
    routes=[
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        WebSocketRoute("/api/websocket", WebSocketConnection),
        Mount("/static", app=StaticFiles(directory="piirakka/static"), name="static"),
    ]
)

@app.on_event("startup")
async def startup():
    asyncio.create_task(background_task())

@app.on_event("shutdown")
async def shutdown():
    for subscriber in context.subscribers:
        await subscriber.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

