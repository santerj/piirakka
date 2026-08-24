from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from piirakka.services.renderer import render as renderer


class PlayerState(BaseModel):
    # representation of the player bar in json
    playback_status: bool  # True: playing | False: paused
    volume: int
    current_station_name: str | None  # index in stations
    track_title: str | None  # usually from Icy-Title

    class Config:
        alias_generator = to_camel
        populate_by_name = True

    def render(self) -> str:
        template = "components/player.html"
        return renderer(template, player_state=self.model_dump())
