"""Application Context - manages player state and database."""

import json
import logging
import os

import anyio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import piirakka.model.event as events
from . import preflight
from piirakka.model.player import Player
from piirakka.model.recent_track import RecentTrack
from piirakka.model.station import list_stations

logger = logging.getLogger(__name__)


class Context:
    """
    Application context managing player state and database.

    Requires broadcast_message_fn to be passed for WebSocket broadcasting from player callbacks.
    """

    SPAWN_MPV = os.getenv("MPV", True)
    SOCKET = os.getenv("SOCKET", preflight.generate_socket_path())
    DATABASE = preflight.DB_PATH

    def __init__(self, broadcast_message_fn, track_history_manager) -> None:
        """
        Initialize Context with player and database.

        Args:
            broadcast_message_fn: Async callable(message: str) for broadcasting WebSocket updates
            track_history_manager: TrackHistoryManager instance for track history
        """
        self._broadcast_message_fn = broadcast_message_fn
        self._track_history_manager = track_history_manager
        self.player = Player(self.SPAWN_MPV, self.SOCKET, self.DATABASE, self.player_callback)
        self.db_engine = create_engine(f"sqlite:///{self.DATABASE}", echo=False)

        with Session(self.db_engine) as session:
            stations = list_stations(session)
            stations_pydantic = [s.to_pydantic() for s in stations]
            self.player.update_stations(stations_pydantic)
            if len(stations) > 0:
                default_index = 0
                self.player.current_station_id = str(stations[default_index].station_id)
                self.player.play_station_with_id(self.player.current_station_id)

    def player_callback(self, message) -> None:
        """Callback from player subprocess via anyio."""
        logging.info(f"Received event {type(message)} from player via callback")
        payload = self.serialize_events(message)
        logging.info(f"Broadcasting Websocket message {payload}")
        anyio.from_thread.run(self._broadcast_message_fn, payload)

    async def push_track(self, track: RecentTrack) -> None:
        """Update track history and broadcast track change event."""
        self._track_history_manager.add_track(track)

        track_update_message = events.TrackChangeEvent(content=track)
        player_bar_update_message = events.PlayerBarUpdateEvent(content=self.player.get_player_state())
        message = self.serialize_events(track_update_message, player_bar_update_message)

        await self._broadcast_message_fn(message=message)

    async def refresh_stations(self) -> None:
        """Refresh stations from database and update player."""
        with Session(self.db_engine) as session:
            stations = list_stations(session)
            stations_pydantic = [s.to_pydantic() for s in stations]
            self.player.update_stations(stations_pydantic)

    async def push_stations(self) -> None:
        """Broadcast station list update to WebSocket subscribers."""
        stations = self.player.stations
        station_update_message = events.StationListChangeEvent(content=stations)
        message = {"events": [station_update_message.model_dump()]}
        await self._broadcast_message_fn(message=json.dumps(message, default=str))

    @staticmethod
    def serialize_events(*args) -> str:
        """Serialize events to JSON."""
        payload = {"events": []}
        for event in args:
            payload["events"].append(event.model_dump())
        return json.dumps(payload)
