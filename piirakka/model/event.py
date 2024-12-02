from enum import Enum
from pydantic import BaseModel

from piirakka.model.station import StationPydantic


# instead of updating ui always with entire PlayerState, we can
# send smaller event dtos that only contain the changed value.

class StationSetEvent(BaseModel):
    # someone changed stations
    event: str = "station_set"
    station_index: int

class StationsChangeEvent(BaseModel):
    # stations updated in db
    event: str = "stations_changed"
    stations: list[StationPydantic]

class TrackChangeEvent(BaseModel):
    # track changed
    event: str = "track_changed"
    html: str

class VolumeSetEvent(BaseModel):
    # someone changed volume
    event: str = "volume_set"
    volume: int

class StatusChangeEvent(BaseModel):
    # status changed – playing or paused
    event: str = "status_changed"
    status: str

class PlayerEvent(Enum):
    STATION_SET = StationSetEvent
    STATIONS_CHANGED = StationsChangeEvent
    TRACK_CHANGED = TrackChangeEvent
    VOLUME_SET = VolumeSetEvent
    STATUS_CHANGED = StatusChangeEvent

def create_event(event_enum, data):
    event_cls = event_enum.value
    return event_cls(**data)

# examples
# station_set_event = create_event(PlayerEvent.STATION_SET, {"station_index": 3})
# track_change_event = create_event(PlayerEvent.TRACK_CHANGED, {"title": "Kate Havnevik - Disobey"})
# volume_set_event = create_event(PlayerEvent.VOLUME_SET, {"volume": 75})
# status_change_event = create_event(PlayerEvent.STATUS_CHANGED, {"status": "playing"})
# print(station_set_event.model_dump())
# print(track_change_event.model_dump())
# print(volume_set_event.model_dump())
# print(status_change_event.model_dump())
