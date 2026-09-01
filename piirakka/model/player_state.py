from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from piirakka.services.renderer import render as renderer


class PlayerState(BaseModel):
    """Representation of the player's current status."""

    playback_status: bool  # True: playing | False: paused
    volume: int
    current_station_name: str | None  # index in stations
    track_title: str | None  # from icy-title
    bluetooth_device_name: str | None
    audio_device_name: str | None

    codec: str | None
    sample_rate: float | None  # in kHz
    bit_rate: float | None  # in kbps

    genre: str | None  # from icy-genre

    class Config:
        """Config for pydantic."""

        alias_generator = to_camel
        populate_by_name = True

    def render(self) -> str:
        template = "components/player.html"
        return renderer(template, player_state=self.model_dump())
