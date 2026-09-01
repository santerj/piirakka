"""Template-based page views."""

from http import HTTPMethod

from starlette.routing import Route
from starlette.templating import Jinja2Templates

from piirakka.core.preflight import APP_CONFIG


def create_routes(templates: Jinja2Templates, context, track_history):
    """Factory function that creates page route handlers with dependencies injected.

    Args:
    -------
    templates: Jinja2Templates instance for rendering
    context: The application Context (for player state)
    track_history: TrackHistoryManager instance

    Returns:
    -------
    List of Route objects.

    """

    async def index(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "stations": context.player.stations,
                "recent_tracks": track_history.get_history(),
                "player_state": context.player.get_player_state(),
                "search_options": await context.get_search_options(),
            },
        )

    async def ng(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="ng/index.html",
            context={
                "request": request,
                "stations": context.player.stations,
                "recent_tracks": track_history.get_history(),
                "player_state": context.player.get_player_state(),
                "search_options": await context.get_search_options(),
            },
        )

    async def stations_page(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="stations.html",
            context={
                "request": request,
                "stations": context.player.stations,
                "player_state": context.player.get_player_state(),
            },
        )

    async def settings_page(request) -> Jinja2Templates.TemplateResponse:
        return templates.TemplateResponse(
            request=request,
            name="settings.html",
            context={
                "request": request,
                "stations": context.player.stations,
                "player_state": context.player.get_player_state(),
                "devices": context.available_bluetooth_devices,
                "current_audio_device": context.player.get_device(),
                "APP_CONFIG": APP_CONFIG,
            },
        )

    return [
        Route("/", endpoint=index, methods=[HTTPMethod.GET]),
        Route("/ng", endpoint=ng, methods=[HTTPMethod.GET]),
        Route("/stations", endpoint=stations_page, methods=[HTTPMethod.GET]),
        Route("/settings", endpoint=settings_page, methods=[HTTPMethod.GET]),
    ]
