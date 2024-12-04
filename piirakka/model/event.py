from enum import Enum
from pydantic import BaseModel

from piirakka.model.station import StationPydantic

class ControlBarUpdated(BaseModel):
    event: str = "control_bar_updated"
    html: str

class StationsChangeEvent(BaseModel):
    # stations updated in db
    event: str = "stations_changed"
    stations: list[StationPydantic]

class TrackChangeEvent(BaseModel):
    # track changed
    event: str = "track_changed"
    html: str

#class PlayerEvent(Enum):
#    STATION_SET = StationSetEvent
#    STATIONS_CHANGED = StationsChangeEvent
#    TRACK_CHANGED = TrackChangeEvent
#    VOLUME_SET = VolumeSetEvent
#    STATUS_CHANGED = StatusChangeEvent
#
#def create_event(event_enum, data):
#    event_cls = event_enum.value
#    return event_cls(**data)

# examples
# station_set_event = create_event(PlayerEvent.STATION_SET, {"station_index": 3})
# track_change_event = create_event(PlayerEvent.TRACK_CHANGED, {"title": "Kate Havnevik - Disobey"})
# volume_set_event = create_event(PlayerEvent.VOLUME_SET, {"volume": 75})
# status_change_event = create_event(PlayerEvent.STATUS_CHANGED, {"status": "playing"})
# print(station_set_event.model_dump())
# print(track_change_event.model_dump())
# print(volume_set_event.model_dump())
# print(status_change_event.model_dump())
