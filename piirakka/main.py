import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.sidebar_item import sidebar_items
from model.player import Player

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request


def create_app(mpv, socket, database, callback):
    player = Player(mpv, socket, database, callback)
    app = FastAPI()
    app.state.player = player
    return app

SPAWN_MPV = os.getenv("MPV", True)
SOCKET = os.getenv("SOCKET", "/tmp/piirakka.sock")
DATABASE = os.getenv("DATABASE", "./piirakka.db")

# server-sent event subscribers
subscribers = []

async def notify_all(message: str):
    # send message to subscribers
    for queue in subscribers:
        await queue.put(message)

def player_callback(message):
    asyncio.create_task(notify_all(message))

async def event_generator(request: Request, queue: asyncio.Queue):
    while True:
        if await request.is_disconnected():
            break
        message = await queue.get()
        yield {
            "event": "update",
            "data": message,
        }

async def periodic_task():
    # TODO: use this function to ping mpv for currently playing track.
    # TODO: if track has changed, generate new PlayerContext and send to SSE clients
    while True:
        # Your logic here
        print("Running periodic task")
        await notify_all("Hello!")
        await asyncio.sleep(5)  # Wait for 5 seconds before running again

app = create_app(SPAWN_MPV, SOCKET, DATABASE, player_callback)
player = app.state.player
templates = Jinja2Templates(directory="piirakka/templates")
app.mount("/static", StaticFiles(directory="piirakka/static"), name="static")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_task())

@app.on_event("shutdown")
async def shutdown_event():
    for queue in subscribers:
        queue.put_nowait(None)
    subscribers.clear()

@app.get("/events")
async def events(request: Request):
    queue = asyncio.Queue()
    subscribers.append(queue)

    async def cleanup():
        subscribers.remove(queue)

    request.state.cleanup = cleanup
    return EventSourceResponse(event_generator(request, queue))

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html",
                {
                    "request": request,
                    "sidebar_items": sidebar_items
                }
    )

@app.get("/stations")
async def stations_page(request: Request):
    return templates.TemplateResponse("legacy_stations.html",
                {
                    "request": request,
                    "reload_token": player.hash,
                    "stations": player.stations
                }
    )

@app.post("/api/radio/volume")
async def set_volume(volume: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(player.set_volume, volume)
    return {"message": "Volume change initiated"}

@app.post("/api/radio/station")
async def set_station(station: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(player.set_station, station)
    return {"message": "Station change initiated"}

if __name__ == "__main__":
    # Run FastAPI with Uvicorn
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
