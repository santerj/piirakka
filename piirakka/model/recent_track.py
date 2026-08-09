from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape

from piirakka.model.search_option import SearchOption

env = Environment(
    loader=FileSystemLoader("piirakka/templates"),
    autoescape=select_autoescape()
)

class RecentTrack(BaseModel):
    title: str
    station: str
    timestamp: str

    def render_html(self, search_options: list[SearchOption] = None) -> str:
        template = env.get_template("components/recent_track.html")
        return template.render(track=self, search_options=search_options)
