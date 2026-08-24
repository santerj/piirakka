"""Application Context - manages player state and database."""

import json
import logging
import os
import asyncio

import anyio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from piirakka.model.event import BroadcastEvent, EventType
from piirakka.model.player import Player
from piirakka.model.recent_track import RecentTrack
from piirakka.model.search_option import list_search_options
from piirakka.model.sidebar_item import sidebar_items  # TODO: hardcode these into template
from piirakka.model.station import list_stations
from piirakka.services.renderer import render
from piirakka.services.persistence import save_state
from piirakka.services.bluetooth import BluetoothDeviceManager

from . import preflight

logger = logging.getLogger(__name__)


class Context:
    """Application context managing player state and database.

    Requires broadcast_message_fn to be passed for WebSocket broadcasting from player callbacks.
    """

    DATABASE = preflight.DB_PATH

    def __init__(self, broadcast_message_fn, track_history_manager, spawn_mpv, persisted_state=None) -> None:
        """Initialize Context with player and database.

        Args:
        ----
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
        self._persisted_state = persisted_state or {}
        self.state_path = preflight.STATE_PATH
        self._callbacks_ready = False
        self.player = Player(spawn_mpv, self.SOCKET, self.DATABASE, self.player_callback)
        self.player.audio_device_name = self._persisted_state.get("audio_device_name")
        self.player.bluetooth_device_name = self._persisted_state.get("bluetooth_device_name")
        self.player.bluetooth_device_address = self._persisted_state.get("bluetooth_device_address")
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
            self._callbacks_ready = True

    async def restore_audio_device(self) -> None:
        address = self.player.bluetooth_device_address
        logger.info("Attempting to restore audio device: %s", address or self.player.audio_device_name or "none")
        try:
            if address:
                logger.info("Reconnecting Bluetooth device %s", self.player.bluetooth_device_name or address)
                await BluetoothDeviceManager.connect(address)
                for _ in range(10):
                    output_device = next(
                        (device for device in self.player.list_devices() if address.replace(":", "_") in device.name),
                        None,
                    )
                    if output_device:
                        logger.info("Restoring Bluetooth audio output %s", output_device.name)
                        await self.player.set_device(
                            output_device.name,
                            bluetooth_device_name=self.player.bluetooth_device_name,
                            bluetooth_device_address=address,
                        )
                        return
                    await anyio.sleep(1)
            elif self.player.audio_device_name:
                logger.info("Restoring audio output %s", self.player.audio_device_name)
                output_device = next(
                    (device for device in self.player.list_devices() if device.name == self.player.audio_device_name),
                    None,
                )
                if output_device:
                    await self.player.set_device(output_device.name)
                    return
            logger.info("No persisted audio device was available to restore")
        except Exception:
            logger.warning("Unable to restore audio device %s", address or self.player.audio_device_name, exc_info=True)

    def save_state(self) -> None:
        save_state(
            self.state_path,
            {
                "track_history": self._track_history_manager.get_history(),
                "audio_device_name": self.player.audio_device_name,
                "bluetooth_device_name": self.player.bluetooth_device_name,
                "bluetooth_device_address": self.player.bluetooth_device_address,
            },
        )

    def player_callback(self, event: EventType) -> None:
        # the Player object can call this to broadcast events after state changes
        logger.info(f"Received event {event.event_type} from player via callback")
        if not self._callbacks_ready:
            logger.debug("Skipping player callback before application startup")
            return
        payload = self.serialize_events(event)
        logger.info("Broadcasting Websocket message from player callback")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            anyio.from_thread.run(self._broadcast_message_fn, payload)
        else:
            loop.create_task(self._broadcast_message_fn(payload))

    async def push_track(self, track: RecentTrack) -> None:
        """Render track history + player bar and push to subscribers."""
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
        bt_devices_update_event = BroadcastEvent(
            event_type=EventType.BLUETOOTH_LIST_CHANGED,
            content=render(
                component="components/bluetooth_devices.html",
                devices=self.available_bluetooth_devices,
                current_audio_device=self.player.get_device(),
            ),
        )
        message = self.serialize_events(bt_devices_update_event)
        await self._broadcast_message_fn(message=message)

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
