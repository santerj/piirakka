from model.station import Station

from pydantic import BaseModel
from pydantic.alias_generators import to_camel

class PlayerState(BaseModel):
    # this class is used to hydrate the frontend with server-sent events.
    # it contains everyhting required to populate the frontend with real time data.
    playing: bool
    volume: int
    stations: list[Station]  # maybe use real Station object
    current_station: Station
    current_station_index: int | None  # index in stations

    class Config:
        alias_generator = to_camel
        populate_by_name = True
