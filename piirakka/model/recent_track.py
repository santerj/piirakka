from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

from piirakka.model.search_option import SearchOption

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape())


class RecentTrack(BaseModel):
    title: str
    station: str
    timestamp: str

    def render_html(self, search_options: list[SearchOption] | None = None) -> str:
        template = env.get_template("components/recent_track.html")
        return template.render(track=self, search_options=search_options)
