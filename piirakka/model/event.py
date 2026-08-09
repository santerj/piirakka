"""Definitions of events sent to subscribers over websocket"""

from pydantic import BaseModel

#from piirakka.model.station import StationPydantic
#from piirakka.model.player_state import PlayerState
#from piirakka.model.recent_track import RecentTrack

# TODO: clean up of commented out code

class PlayerBarUpdateEvent(BaseModel):
    """Any value represented in the player bar has changed - render entire player bar + push update"""
    content: str  # html
    #content: PlayerState
    event_type: str = "player_bar_updated"


class StationListChangeEvent(BaseModel):
    """Station list has changed - render entire station list + push update"""
    # TODO: event type unused and not understood by frontend
    content: str  # html
    #content: list[StationPydantic]
    event_type: str = "stations_changed"


class SidebarChangeEvent(BaseModel):
    """Sidebar has changed - render entire sidebar + push update"""
    # TODO: event type unused and not understood by frontend
    content: str  # html
    event_type: str = "sidebar_changed"


class TrackChangeEvent(BaseModel):
    """Currently playing track changed - render entire track history + push update"""
    content: str  # html
    #content: RecentTrack
    event_type: str = "track_history_changed"
