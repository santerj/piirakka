import asyncio
import json
import logging
import os
from datetime import datetime

import anyio
import uvicorn
from setproctitle import setproctitle
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.applications import Starlette
from starlette.routing import Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import piirakka
import piirakka.model.event as events
import piirakka.preflight as preflight
from piirakka.__version__ import __version__
from piirakka.model.player import Player
from piirakka.model.recent_track import RecentTrack
from piirakka.model.station import list_stations
from piirakka.services.track_history import TrackHistoryManager
from piirakka.services.websocket import WebSocketSubscriberManager, create_websocket_connection
from piirakka.views import pages, playback, stations

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
WebSocketConnection = create_websocket_connection(subscriber_state) # WebSocketConnection endpoint with bound manager
context = Context()


async def broadcast_message(message: str) -> None:
    """Broadcast message to all WebSocket subscribers."""
    await subscriber_state.broadcast(message)


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


app = Starlette(
    routes=[
        *pages.create_routes(templates, context, track_history),
        *stations.create_routes(context.db_engine, context.refresh_stations, context.push_stations),
        *playback.create_routes(context),
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
