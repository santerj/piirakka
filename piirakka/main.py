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
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import piirakka
import piirakka.model.event as events
import piirakka.preflight as preflight
from piirakka.__version__ import __version__
from piirakka.model.player import Player
from piirakka.model.recent_track import RecentTrack
from piirakka.model.sidebar_item import sidebar_items
from piirakka.model.station import create_station, list_stations, order_stations, update_station, delete_station
from piirakka.services.track_history import TrackHistoryManager
from piirakka.services.websocket import WebSocketSubscriberManager, create_websocket_connection

setproctitle("piirakka")
logger = logging.getLogger(__name__)

templates_dir = os.path.join(os.path.dirname(piirakka.__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)
static_dir = os.path.join(os.path.dirname(piirakka.__file__), "static")


class Context:
    SPAWN_MPV = os.getenv("MPV", True)
    SOCKET = os.getenv("SOCKET", preflight.generate_socket_path())
    DATABASE = preflight.DB_PATH

    def player_callback(self, message) -> None:
        # loop = asyncio.get_event_loop()
        # loop.create_task(broadcast_message(str(message)))

        logging.info(f"Received event {type(message)} from player via callback")
        payload = self.serialize_events(message)
        logging.info(f"Broadcasting Websocket message {payload}")
        anyio.from_thread.run(broadcast_message, payload)

    def __init__(self) -> None:
        self.player = Player(self.SPAWN_MPV, self.SOCKET, self.DATABASE, self.player_callback)
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

    async def push_player_bar(self) -> None:
        # TODO: unused dead code, consider removing
        player_bar_status = self.player.get_player_state()
        message = events.PlayerBarUpdateEvent(content=player_bar_status)
        await broadcast_message(message.model_dump_json())

    async def push_track(self, track: RecentTrack) -> None:
        # updates the in-memory track history
        # and broadcasts updates to websocket subscribers
        track_history.add_track(track)

        track_update_message = events.TrackChangeEvent(content=track)

        # track change also refreshes player bar in the same broadcast
        player_bar_update_message = events.PlayerBarUpdateEvent(content=self.player.get_player_state())
        message = self.serialize_events(track_update_message, player_bar_update_message)

        await broadcast_message(message=message)

    async def refresh_stations(self) -> None:
        with Session(self.db_engine) as session:
            stations = list_stations(session)
            stations_pydantic = [s.to_pydantic() for s in stations]
            self.player.update_stations(stations_pydantic)

    async def push_stations(self) -> None:
        stations = self.player.stations
        station_update_message = events.StationListChangeEvent(content=stations)
        # TODO: serialization of datetime in StationPydantic is tricky,
        # consider refactoring + using serialize_events here
        message = {"events": [station_update_message.model_dump()]}
        await broadcast_message(message=json.dumps(message, default=str))

    @staticmethod
    def serialize_events(*args) -> str:
        # accepts events and serializes to json
        payload = {"events": []}
        for event in args:
            payload["events"].append(event.model_dump())
        return json.dumps(payload)


preflight.run_migrations()
subscriber_state = WebSocketSubscriberManager()
track_history = TrackHistoryManager()
context = Context()


async def broadcast_message(message) -> None:
    await subscriber_state.broadcast(message)


# Create WebSocketConnection endpoint with dependencies bound
WebSocketConnection = create_websocket_connection(subscriber_state, broadcast_message)


def task(callback):
    # placeholder
    callback("task")


async def observe_current_track(interval: int = 1) -> None:
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

        if not track_history:
            await context.push_track(current_track)
        elif track_history.most_recent().title == current_track_title:
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
            "recent_tracks": track_history.get_history(),
            "volume": context.player.get_volume(),
            "playing": context.player.get_status(),
            "track_name": track_history.most_recent().title if track_history else "",
            "station_name": context.player.current_station.name if context.player.current_station else "",
            "version": __version__,
        },
    )


async def stations_page(request):
    return templates.TemplateResponse(
        "stations.html",
        {
            "request": request,
            "sidebar_items": sidebar_items,
            "stations": context.player.stations,
            "volume": context.player.get_volume(),
            "playing": context.player.get_status(),
            "track_name": track_history.most_recent().title if track_history else "",
            "station_name": context.player.current_station.name if context.player.current_station else "",
        },
    )


async def set_station(request) -> JSONResponse:
    station_id = request.path_params["station_id"]
    task = BackgroundTask(context.player.play_station_with_id, station_id)
    return JSONResponse({"message": "station change initiated"}, background=task)


async def toggle_playback(request) -> JSONResponse:
    task = BackgroundTask(context.player.toggle)
    return JSONResponse({"message": "toggle initiated"}, background=task)


async def set_volume(request) -> JSONResponse:
    data = await request.json()
    volume = int(data.get("volume"))
    task = BackgroundTask(context.player.set_volume, volume)
    return JSONResponse({"message": "volume change initiated"}, background=task)


async def shuffle_station(request) -> JSONResponse:
    task = BackgroundTask(context.player.shuffle)
    return JSONResponse({"message": "station shuffle initiated"}, background=task)


async def create_station_handler(request) -> JSONResponse:
    data = await request.json()
    name = data.get("station_name")
    url = data.get("station_url")

    with Session(context.db_engine) as session:
        create_station(session, name, url)

    await context.refresh_stations()
    await context.push_stations()

    return JSONResponse({"message": "station created successfully"})


async def update_station_handler(request) -> JSONResponse:
    station_id = request.path_params["station_id"]
    data = await request.json()
    name = data.get("station_name")
    url = data.get("station_url")

    if not name and not url:
        return JSONResponse({"message": "no update parameters provided"}, status_code=400)

    if station_id not in [s.station_id for s in context.player.stations]:
        return JSONResponse({"message": "station not found"}, status_code=404)

    with Session(context.db_engine) as session:
        station = update_station(session, station_id, name, url)
        if station is None:
            return JSONResponse({"message": "station not updated"}, status_code=500)

    await context.refresh_stations()
    await context.push_stations()

    return JSONResponse({"message": "station updated successfully"})


async def delete_station_handler(request) -> JSONResponse:
    station_id = request.path_params["station_id"]

    if station_id not in [s.station_id for s in context.player.stations]:
        return JSONResponse({"message": "station not found"}, status_code=404)

    with Session(context.db_engine) as session:
        success = delete_station(session, station_id)
        if not success:
            return JSONResponse({"message": "station not deleted"}, status_code=500)

    await context.refresh_stations()
    await context.push_stations()

    return JSONResponse({"message": "station deleted successfully"})


async def sort_stations(request) -> JSONResponse:
    data = await request.json()
    station_ids = data.get("order")

    if not station_ids or not isinstance(station_ids, list):
        return JSONResponse({"message": "invalid station_ids"}, status_code=400)

    with Session(context.db_engine) as session:
        success = order_stations(session, station_ids)
        if not success:
            return JSONResponse({"message": "stations not sorted"}, status_code=500)

    await context.refresh_stations()
    await context.push_stations()

    return JSONResponse({"message": "stations sorted successfully"})


app = Starlette(
    routes=[
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        Route("/api/station", create_station_handler, methods=[HTTPMethod.POST]),
        Route("/api/station/{station_id}", update_station_handler, methods=[HTTPMethod.PATCH]),
        Route("/api/station/{station_id}", delete_station_handler, methods=[HTTPMethod.DELETE]),
        Route("/api/stations/reorder", sort_stations, methods=[HTTPMethod.POST]),
        Route("/api/radio/station/{station_id}", set_station, methods=[HTTPMethod.PUT]),
        Route("/api/radio/toggle", toggle_playback, methods=[HTTPMethod.PUT]),
        Route("/api/radio/volume", set_volume, methods=[HTTPMethod.PUT]),
        Route("/api/radio/shuffle", shuffle_station, methods=[HTTPMethod.PUT]),
        WebSocketRoute("/ws/subscribe", WebSocketConnection),
        Mount("/static", app=StaticFiles(directory=static_dir), name="static"),
    ]
)


@app.on_event("startup")
async def startup():
    asyncio.create_task(observe_current_track())


@app.on_event("shutdown")
async def shutdown():
    for subscriber in subscriber_state.subscribers:
        await subscriber.close()


def main():
    uvicorn.run(
        app, host="0.0.0.0", port=8000, workers=1, timeout_graceful_shutdown=5, log_config=preflight.LOGGING_CONFIG
    )


if __name__ == "__main__":
    logger.info(f"Starting piirakka v{__version__}")
    main()
