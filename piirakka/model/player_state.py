from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader("piirakka/templates"),
    autoescape=select_autoescape()
)

class PlayerState(BaseModel):
    # representation of the player bar in json
    playback_status: bool  # True: playing | False: paused
    volume: int
    current_station_name: str | None  # index in stations
    track_title: str | None  # usually from Icy-Title

    class Config:
        alias_generator = to_camel
        populate_by_name = True

    def render_html(self) -> str:
        template = env.get_template("components/player.html")
        return template.render(
            player_state=self,
            playing=self.playback_status,
            volume=self.volume,
            track_name=self.track_title,
            station_name=self.current_station_name,
        )
