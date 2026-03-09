"""Template-based page views."""

from http import HTTPMethod

from starlette.routing import Route
from starlette.templating import Jinja2Templates

from piirakka.model.sidebar_item import sidebar_items
from piirakka.__version__ import __version__


def create_routes(templates: Jinja2Templates, context, track_history):
    """
    Factory function that creates page route handlers with dependencies injected.

    Args:
        templates: Jinja2Templates instance for rendering
        context: The application Context (for player state)
        track_history: TrackHistoryManager instance

    Returns:
        List of Route objects
    """

    async def index(request):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "sidebar_items": sidebar_items,
                "stations": context.player.stations,
                "recent_tracks": track_history.get_history(),
                "volume": context.player.get_volume(),
                "playing": context.player.get_status(),
                "track_name": track_history.most_recent().title if track_history else "",
                "station_name": context.player.current_station.name if context.player.current_station else "",
                "version": __version__,
            },
        )

    async def stations_page(request):
        return templates.TemplateResponse(
            "stations.html",
            {
                "request": request,
                "sidebar_items": sidebar_items,
                "stations": context.player.stations,
                "volume": context.player.get_volume(),
                "playing": context.player.get_status(),
                "track_name": track_history.most_recent().title if track_history else "",
                "station_name": context.player.current_station.name if context.player.current_station else "",
            },
        )

    return [
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
    ]
