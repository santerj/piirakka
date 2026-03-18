"""Station management view handlers."""

from http import HTTPMethod

from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.routing import Route

from piirakka.model.station import create_station, delete_station, list_stations, order_stations, update_station


def create_routes(context):
    """
    Factory function that creates station management route handlers with dependencies injected.

    Args:
        context: The application Context (for player control)

    Returns:
        List of Route objects
    """

    async def create_station_handler(request) -> JSONResponse:
        data = await request.json()
        name = data.get("station_name")
        url = data.get("station_url")

        with Session(context.db_engine) as session:
            create_station(session, name, url)

        await context.on_refresh_stations()
        await context.on_stations_changed()

        return JSONResponse({"message": "station created successfully"})

    async def update_station_handler(request) -> JSONResponse:
        station_id = request.path_params["station_id"]
        data = await request.json()
        name = data.get("station_name")
        url = data.get("station_url")

        if not name and not url:
            return JSONResponse({"message": "no update parameters provided"}, status_code=400)

        with Session(context.db_engine) as session:
            # Check if station exists before attempting update
            existing_stations = list_stations(session)
            if station_id not in [str(s.station_id) for s in existing_stations]:
                return JSONResponse({"message": "station not found"}, status_code=404)

            station = update_station(session, station_id, name, url)
            if station is None:
                return JSONResponse({"message": "station not updated"}, status_code=500)

        await context.on_refresh_stations()
        await context.on_stations_changed()

        return JSONResponse({"message": "station updated successfully"})

    async def delete_station_handler(request) -> JSONResponse:
        station_id = request.path_params["station_id"]

        with Session(context.db_engine) as session:
            existing_stations = list_stations(session)
            if station_id not in [str(s.station_id) for s in existing_stations]:
                return JSONResponse({"message": "station not found"}, status_code=404)

            success = delete_station(session, station_id)
            if not success:
                return JSONResponse({"message": "station not deleted"}, status_code=500)

        await context.on_refresh_stations()
        await context.on_stations_changed()

        return JSONResponse({"message": "station deleted successfully"})

    async def sort_stations(request) -> JSONResponse:
        data = await request.json()
        station_ids = data.get("order")

        if not station_ids or not isinstance(station_ids, list):
            return JSONResponse({"message": "invalid station_ids"}, status_code=400)

        with Session(context.db_engine) as session:
            success = order_stations(session, station_ids)
            if not success:
                return JSONResponse({"message": "stations not sorted"}, status_code=500)

        await context.on_refresh_stations()
        await context.on_stations_changed()

        return JSONResponse({"message": "stations sorted successfully"})

    return [
        Route("/api/station", create_station_handler, methods=[HTTPMethod.POST]),
        Route("/api/station/{station_id}", update_station_handler, methods=[HTTPMethod.PATCH]),
        Route("/api/station/{station_id}", delete_station_handler, methods=[HTTPMethod.DELETE]),
        Route("/api/stations/reorder", sort_stations, methods=[HTTPMethod.POST]),
    ]
