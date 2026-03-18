"""Playback control view handlers."""

from http import HTTPMethod

from starlette.background import BackgroundTask
from starlette.responses import JSONResponse
from starlette.routing import Route


def create_routes(context):
    """
    Factory function that creates playback control route handlers with dependencies injected.

    Args:
        context: The application Context (for player control)

    Returns:
        List of Route objects
    """

    async def set_station(request) -> JSONResponse:
        station_id = request.path_params["station_id"]
        task = BackgroundTask(context.player.play_station_with_id, station_id)
        return JSONResponse({"message": "station change initiated"}, background=task)

    async def toggle_playback(request) -> JSONResponse:
        task = BackgroundTask(context.player.toggle)
        return JSONResponse({"message": "toggle initiated"}, background=task)

    async def set_volume(request) -> JSONResponse:
        data = await request.json()
        volume = int(data.get("volume"))
        task = BackgroundTask(context.player.set_volume, volume)
        return JSONResponse({"message": "volume change initiated"}, background=task)

    async def shuffle_station(request) -> JSONResponse:
        task = BackgroundTask(context.player.shuffle)
        return JSONResponse({"message": "station shuffle initiated"}, background=task)

    return [
        Route("/api/radio/station/{station_id}", set_station, methods=[HTTPMethod.PUT]),
        Route("/api/radio/toggle", toggle_playback, methods=[HTTPMethod.PUT]),
        Route("/api/radio/volume", set_volume, methods=[HTTPMethod.PUT]),
        Route("/api/radio/shuffle", shuffle_station, methods=[HTTPMethod.PUT]),
    ]
