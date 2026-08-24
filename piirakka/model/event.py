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


T = TypeVar("T", bound=object)

class BroadcastEvent(BaseModel, Generic[T]):
    event_type: EventType
    content: T  # rendered html

