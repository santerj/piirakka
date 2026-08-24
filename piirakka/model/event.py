"""Definitions of events sent to subscribers over websocket."""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel


class EventType(str, Enum):
    """Match the event name in client side websocket code"""
    PLAYER_BAR_UPDATED = "player_bar_updated"
    STATIONS_CHANGED = "stations_changed"
    SIDEBAR_CHANGED = "sidebar_changed"
    TRACK_HISTORY_CHANGED = "track_history_changed"
    BLUETOOTH_LIST_CHANGED = "bluetooth_list_changed"


class PlayerBarUpdateEvent(BaseModel):
    """Any value represented in the player bar has changed - render entire player bar and broadcast."""
    content: str  # html
    event_type: EventType.PLAYER_BAR_UPDATED

class StationListChangeEvent(BaseModel):
    """Station list has changed - render entire station list and broadcast."""
    content: str  # html
    event_type: str = EventType.STATIONS_CHANGED

class SidebarChangeEvent(BaseModel):
    """Sidebar has changed - render entire sidebar and broadcast."""
    content: str  # html
    event_type: str = EventType.SIDEBAR_CHANGED

class TrackChangeEvent(BaseModel):
    """Currently playing track changed - render entire track history and broadcast."""
    content: str  # html
    event_type: str = EventType.TRACK_HISTORY_CHANGED

class BluetoothListChangeEvent(BaseModel):
    """Any value in the bluetooth device list changed - render entire list and broadcast."""
    content: str  # html
    event_type: str = EventType.BLUETOOTH_LIST_CHANGED
