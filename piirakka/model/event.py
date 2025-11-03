from pydantic import BaseModel

from piirakka.model.station import StationPydantic
from piirakka.model.player_state import PlayerState
from piirakka.model.recent_track import RecentTrack


class PlayerBarUpdateEvent(BaseModel):
    event_type: str = "player_bar_updated"
    content: PlayerState

class StationListChangeEvent(BaseModel):
    # stations updated in db
    event_type: str = "stations_changed"
    content: list[StationPydantic]

class TrackChangeEvent(BaseModel):
    # track changed
    event_type: str = "track_changed"
    content: RecentTrack
