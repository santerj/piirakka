from pydantic import BaseModel

from piirakka.model.station import StationPydantic
from piirakka.model.player_state import PlayerState
from piirakka.model.recent_track import RecentTrack


class PlayerBarUpdateEvent(BaseModel):
    # any value in represented in player bar changed
    content: PlayerState
    event_type: str = "player_bar_updated"


class StationListChangeEvent(BaseModel):
    # stations updated in db
    content: list[StationPydantic]
    event_type: str = "stations_changed"


class TrackChangeEvent(BaseModel):
    """Currently playing track changed - render entire track history + push update"""
    content: str  # accepts pre-rendered html
    #content: RecentTrack
    event_type: str = "track_history_changed"
