from piirakka.model.station import Station, StationPydantic

from pydantic import BaseModel
from pydantic.alias_generators import to_camel

class PlayerState(BaseModel):
    # this class is used to hydrate the frontend with server-sent events.
    # it contains everyhting required to populate the frontend with real time data.
    status: str  # playing or paused
    volume: int
    stations: list[StationPydantic]
    current_station_index: int | None  # index in stations
    title: int | None  # usually from Icy-Title

    class Config:
        alias_generator = to_camel
        populate_by_name = True
