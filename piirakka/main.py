import asyncio
import anyio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.sidebar_item import sidebar_items
from model.player import Player

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

SPAWN_MPV = os.getenv("MPV", True)
SOCKET = os.getenv("SOCKET", "/tmp/piirakka.sock")
DATABASE = os.getenv("DATABASE", "./piirakka.db")

def create_app(mpv, socket, database, callback):
    player = Player(mpv, socket, database, callback)
    app = FastAPI()
    app.state.player = player
    app.state.subscribers = []
    return app

async def notify_all(message: str):
    # send message to SSE subscribers
    for queue in app.state.subscribers:
        await queue.put(message)

def player_callback(message):
    anyio.from_thread.run(notify_all, message)

async def periodic_task():
    while True:
        print("Running periodic task")
        await asyncio.sleep(5)  # Wait for 5 seconds before running again

app = create_app(SPAWN_MPV, SOCKET, DATABASE, player_callback)  # fastapi app initialized here
player = app.state.player
templates = Jinja2Templates(directory="piirakka/templates")
app.mount("/static", StaticFiles(directory="piirakka/static"), name="static")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_task())

@app.on_event("shutdown")
async def shutdown_event():
    for queue in app.state.subscribers:
        queue.put_nowait(None)
    app.state.subscribers.clear()

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

@app.get("/api/events")
async def events(request: Request):
    queue = asyncio.Queue()
    app.state.subscribers.append(queue)
    async def event_generator(request: Request, queue: asyncio.Queue):
        try:
            while True:
                disconnected = await request.is_disconnected()
                if disconnected:
                    print(f"Disconnecting client {request.client}")
                    break
                message = await queue.get()
                #if message == MAGIC_FLUSH_SSE_CONNECTIONS:
                    
                    # a magic message sent with 'await notify_all()' can be used to
                    # tear down all SSE connections. this can be useful due to a deadlock
                    # between event generator lifecycle and uvicorn's shutdown procedure.
                    # https://github.com/fastapi/fastapi/discussions/11237
                    
                #     break
                yield f"data: {message}\n\n"
        except asyncio.CancelledError as e:
            # cleanup tasks here
            del app.state.player # destroy Player()
    return StreamingResponse(event_generator(request, queue), media_type="text/event-stream")

@app.get("/api/radio/playerState")
async def get_player_state():
    return JSONResponse(content=player.to_player_state().dict(by_alias=True))

@app.post("/api/radio/play")
async def play(background_tasks: BackgroundTasks):
    background_tasks.add_task(player.play)
    return {"message": "play task initiated"}

@app.post("/api/radio/pause")
async def pause(background_tasks: BackgroundTasks):
    background_tasks.add_task(player.pause)
    return {"message": "pause task initiated"}

@app.post("/api/radio/toggle")
async def toggle(background_tasks: BackgroundTasks):
    background_tasks.add_task(player.toggle)
    return {"message": "toggle task initiated"}

@app.post("/api/radio/station")
async def set_station(station: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(player.set_station, station)
    return {"message": "Station change initiated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
