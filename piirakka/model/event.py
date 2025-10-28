from enum import Enum
from pydantic import BaseModel

from piirakka.model.station import StationPydantic

class ControlBarUpdated(BaseModel):
    event: str = "control_bar_updated"
    html: str = ""

class StationsChangeEvent(BaseModel):
    # stations updated in db
    event: str = "stations_changed"
    stations: list[StationPydantic]

class TrackChangeEvent(BaseModel):
    # track changed
    event: str = "track_changed"
    html: str
