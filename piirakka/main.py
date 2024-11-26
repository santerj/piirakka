import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.sidebar_item import sidebar_items
from model.player import Player

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request



# Init player
SPAWN_MPV = os.getenv("MPV", True)
SOCKET = os.getenv("SOCKET", "/tmp/piirakka.sock")
DATABASE = os.getenv("DATABASE", "./piirakka.db")

def create_app(mpv, socket, database) -> Player:
    player = Player(mpv, socket, database)
    app = FastAPI()
    app.state.player = player
    return app

app = create_app(SPAWN_MPV, SOCKET, DATABASE)
player = app.state.player
templates = Jinja2Templates(directory="piirakka/templates")
app.mount("/static", StaticFiles(directory="piirakka/static"), name="static")

if __name__ == "__main__":
    # Run FastAPI with Uvicorn
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


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
