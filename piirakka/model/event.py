"""Definitions of events sent to subscribers over websocket."""

from pydantic import BaseModel

from piirakka.model.station import StationPydantic

# from piirakka.model.player_state import PlayerState
# from piirakka.model.recent_track import RecentTrack

# TODO: clean up of commented out code


class PlayerBarUpdateEvent(BaseModel):
    """Any value represented in the player bar has changed - render entire player bar and broadcast."""

    content: str  # html
    # content: PlayerState
    event_type: str = "player_bar_updated"


class StationListChangeEvent(BaseModel):
    """Station list has changed - render entire station list and broadcast."""

    # TODO: event type unused and not understood by frontend
    # TODO: should be refacored to send rendered html (consumed by station settings page)
    # content: str  # html
    content: list[StationPydantic]
    event_type: str = "stations_changed"


class SidebarChangeEvent(BaseModel):
    """Sidebar has changed - render entire sidebar and broadcast."""

    # TODO: event type unused and not understood by frontend
    content: str  # html
    event_type: str = "sidebar_changed"


class TrackChangeEvent(BaseModel):
    """Currently playing track changed - render entire track history and broadcast."""

    content: str  # html
    # content: RecentTrack
    event_type: str = "track_history_changed"

class BluetoothListChangeEvent(BaseModel):
    """Any value in the bluetooth device list changed - render entire list and broadcast."""

    content: str  # html
    event_type: str = "bluetooth_list_changed"
