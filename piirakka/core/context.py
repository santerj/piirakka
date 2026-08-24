"""Application Context - manages player state and database."""

import json
import logging
import os

import anyio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from piirakka.model.event import BroadcastEvent, EventType
from piirakka.model.player import Player
from piirakka.model.recent_track import RecentTrack
from piirakka.model.search_option import list_search_options
from piirakka.model.sidebar_item import \
    sidebar_items  # TODO: hardcode these into template
from piirakka.model.station import list_stations
from piirakka.services.renderer import render

from . import preflight

logger = logging.getLogger(__name__)


class Context:
    """Application context managing player state and database.

    Requires broadcast_message_fn to be passed for WebSocket broadcasting from player callbacks.
    """

    DATABASE = preflight.DB_PATH

    def __init__(self, broadcast_message_fn, track_history_manager, spawn_mpv) -> None:
        """
        Initialize Context with player and database.

        Args:
            broadcast_message_fn: Async callable(message: str) for broadcasting WebSocket updates
            track_history_manager: TrackHistoryManager instance for track history
            spawn_mpv: Bool to indicate if mpv should be spawned as subprocess
        """
        if spawn_mpv:
            self.SOCKET = preflight.generate_socket_path()
        else:
            self.SOCKET = os.getenv("MPV_SOCKET", None)

        self._broadcast_message_fn = broadcast_message_fn
        self._track_history_manager = track_history_manager
        self.player = Player(spawn_mpv, self.SOCKET, self.DATABASE, self.player_callback)
        self.db_engine = create_engine(f"sqlite:///{self.DATABASE}", echo=False)
        self.available_bluetooth_devices = []  # periodically refreshed in background

        with Session(self.db_engine) as session:
            stations = list_stations(session)
            stations_pydantic = [s.to_pydantic() for s in stations]
            self.player.update_stations(stations_pydantic)
            if len(stations) > 0:
                default_index = 0
                self.player.current_station_id = str(stations[default_index].station_id)
                self.player.play_station_with_id(self.player.current_station_id)

    def player_callback(self, event: EventType) -> None:
        # the Player object can call this to broadcast events after state changes
        logger.info(f"Received event {event.event_type} from player via callback")
        payload = self.serialize_events(event)
        logger.info("Broadcasting Websocket message from player callback")
        anyio.from_thread.run(self._broadcast_message_fn, payload)

    async def push_track(self, track: RecentTrack) -> None:
        """Render track history + player bar and push to subscribers"""
        self._track_history_manager.add_track(track)
        search_options = await self.get_search_options()  # populate search dropdown based on app settings

        history = self._track_history_manager.get_history()  # RecentTrack
        # TODO: entire history doesn't exist as component,
        # so here it is hacked together from individual lines
        rendered_history = "\n".join(
            [render("components/recent_track.html", track=t, search_options=search_options) for t in history]
        )

        # pack both track history and new player bar state into events

        track_update_event = BroadcastEvent(event_type=EventType.TRACK_HISTORY_CHANGED, content=rendered_history)

        player_bar_update_event = BroadcastEvent(
            event_type=EventType.PLAYER_BAR_UPDATED, content=self.player.get_player_state().render()
        )

        message = self.serialize_events(track_update_event, player_bar_update_event)
        await self._broadcast_message_fn(message=message)

    async def refresh_stations(self) -> None:
        # refresh stations from db to context
        with Session(self.db_engine) as session:
            stations = list_stations(session)
            stations_pydantic = [s.to_pydantic() for s in stations]
            self.player.update_stations(stations_pydantic)

    async def push_stations(self) -> None:
        """Render both sidebar and station management page content + broadcast via websocket."""
        stations = self.player.stations

        sidebar_stations_update_event = BroadcastEvent(
            event_type=EventType.SIDEBAR_CHANGED,
            content=render(
                component="components/sidebar.html",
                stations=stations,
                sidebar_items=sidebar_items,
            ),
        )
        station_settings_update_event = BroadcastEvent(
            event_type=EventType.STATIONS_CHANGED,
            content=render(component="components/station_settings.html", stations=stations),
        )
        message = self.serialize_events(sidebar_stations_update_event, station_settings_update_event)
        await self._broadcast_message_fn(message=message)

    async def push_devices(self) -> None:
        """Render the device component and broadcast via websocket."""
        pass

    async def get_search_options(self) -> list:
        # fetch search options from db
        with Session(self.db_engine) as session:
            return list_search_options(session)

    @staticmethod
    def serialize_events(*args) -> str:
        """Serialize events to JSON."""
        payload = {"events": []}
        for event in args:
            payload["events"].append(event.model_dump())
        return json.dumps(payload)
