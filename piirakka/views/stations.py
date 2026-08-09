"""Station management view handlers."""

import ipaddress
import re
from http import HTTPMethod
from urllib.parse import urlparse

import validators
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.routing import Route

from piirakka.model.station import create_station, delete_station, list_stations, order_stations, update_station

MIN_STATION_NAME_LENGTH = 1
MAX_STATION_NAME_LENGTH = 100


def is_valid_station_name(name: str) -> bool:
    if not isinstance(name, str):
        return False

    normalized_name = name.strip()
    if len(normalized_name) < MIN_STATION_NAME_LENGTH or len(normalized_name) > MAX_STATION_NAME_LENGTH:
        return False

    if re.search(r"[<>]", normalized_name):
        return False

    if re.search(r"(?i)<\s*script", normalized_name):
        return False

    return True


def is_valid_station_url(url: str) -> bool:
    if not isinstance(url, str):
        return False

    normalized_url = url.strip()
    if not normalized_url:
        return False

    parsed = urlparse(normalized_url)
    scheme = parsed.scheme.lower()

    def host_is_valid(hostname: str | None) -> bool:
        if hostname is None:
            return False
        if hostname == "localhost":
            return True
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    if scheme in {"http", "https"}:
        if not parsed.netloc:
            return False

        hostname = parsed.hostname
        if host_is_valid(hostname):
            return True

        return bool(validators.domain(hostname or ""))

    if "://" in normalized_url:
        return False

    parsed_no_scheme = urlparse("//" + normalized_url)
    if not parsed_no_scheme.netloc:
        return False

    hostname = parsed_no_scheme.hostname
    return host_is_valid(hostname)


def create_routes(context):
    """Factory function that creates station management route handlers with dependencies injected.

    Args:
    context: The application Context (for player control)

    Returns:
    List of Route objects
    
    """

    async def create_station_handler(request) -> JSONResponse:
        data = await request.json()
        name = data.get("station_name")
        url = data.get("station_url")

        if not is_valid_station_name(name):
            return JSONResponse({"message": "station_name is invalid"}, status_code=400)

        if not is_valid_station_url(url):
            return JSONResponse({"message": "station_url is invalid"}, status_code=400)

        with Session(context.db_engine) as session:
            create_station(session, name.strip(), url.strip())

        await context.refresh_stations()
        await context.push_stations()

        return JSONResponse({"message": "station created successfully"})

    async def update_station_handler(request) -> JSONResponse:
        station_id = request.path_params["station_id"]
        data = await request.json()
        name = data.get("station_name")
        url = data.get("station_url")

        if name is None and url is None:
            return JSONResponse({"message": "no update parameters provided"}, status_code=400)

        if name is not None and not is_valid_station_name(name):
            return JSONResponse({"message": "station_name is invalid"}, status_code=400)

        if url is not None and not is_valid_station_url(url):
            return JSONResponse({"message": "station_url is invalid"}, status_code=400)

        with Session(context.db_engine) as session:
            # Check if station exists before attempting update
            existing_stations = list_stations(session)
            if station_id not in [str(s.station_id) for s in existing_stations]:
                return JSONResponse({"message": "station not found"}, status_code=404)

            station = update_station(
                session,
                station_id,
                name.strip() if isinstance(name, str) else None,
                url.strip() if isinstance(url, str) else None,
            )
            if station is None:
                return JSONResponse({"message": "station not updated"}, status_code=500)

        await context.refresh_stations()
        await context.push_stations()

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

        await context.refresh_stations()
        await context.push_stations()

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

        await context.refresh_stations()
        await context.push_stations()

        return JSONResponse({"message": "stations sorted successfully"})

    return [
        Route("/api/station", create_station_handler, methods=[HTTPMethod.POST]),
        Route("/api/station/{station_id}", update_station_handler, methods=[HTTPMethod.PATCH]),
        Route("/api/station/{station_id}", delete_station_handler, methods=[HTTPMethod.DELETE]),
        Route("/api/stations/reorder", sort_stations, methods=[HTTPMethod.POST]),
    ]
