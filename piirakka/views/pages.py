"""Template-based page views."""

from http import HTTPMethod

from starlette.routing import Route
from starlette.templating import Jinja2Templates

from piirakka.__version__ import __version__
from piirakka.model.sidebar_item import sidebar_items


def create_routes(templates: Jinja2Templates, context, track_history):
    """Factory function that creates page route handlers with dependencies injected.

    Args:
    templates: Jinja2Templates instance for rendering
    context: The application Context (for player state)
    track_history: TrackHistoryManager instance

    Returns:
    List of Route objects.

    """

    async def index(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "sidebar_items": sidebar_items,
                "stations": context.player.stations,
                "recent_tracks": track_history.get_history(),
                "volume": context.player.get_volume(),
                "playing": context.player.get_status(),
                "track_name": track_history.most_recent().title if track_history else "",
                "station_name": context.player.current_station.name if context.player.current_station else "",
                "version": __version__,
                "search_options": await context.get_search_options(),
            },
        )

    async def stations_page(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="stations.html",
            context={
                "request": request,
                "sidebar_items": sidebar_items,
                "stations": context.player.stations,
                "volume": context.player.get_volume(),
                "playing": context.player.get_status(),
                "track_name": track_history.most_recent().title if track_history else "",
                "station_name": context.player.current_station.name if context.player.current_station else "",
            },
        )

    async def settings_page(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="settings.html",
            context={
                "request": request,
                "sidebar_items": sidebar_items,
                "stations": context.player.stations,
                "volume": context.player.get_volume(),
                "playing": context.player.get_status(),
                "track_name": track_history.most_recent().title if track_history else "",
                "station_name": context.player.current_station.name if context.player.current_station else "",
                "devices": context.available_bluetooth_devices
            },
        )

    return [
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        Route("/settings", endpoint=settings_page, methods=[HTTPMethod.GET]),
    ]
