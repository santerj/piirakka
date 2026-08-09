"""Application settings and options routes."""

from http import HTTPMethod
import logging

from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.routing import Route

from piirakka.model.search_option import list_search_options, update_search_option


def create_routes(context):
    """
    Factory function that creates playback control route handlers with dependencies injected.

    Args:
        context: The application Context (for player control)

    Returns:
        List of Route objects
    """

    async def list_search_options_handler(request) -> JSONResponse:
        with Session(context.db_engine) as session:
            return JSONResponse(list_search_options(session))
        
    async def update_search_option_handler(request) -> JSONResponse:
        data = await request.json()
        key = request.path_params["key"]
        is_enabled = data.get("is_enabled")

        print(key, is_enabled)

        if key is None or is_enabled is None:
            return JSONResponse({"message": "key and is_enabled are required"}, status_code=400)
        elif is_enabled not in [True, False, "true", "false", 1, 0, "1", "0"]:
            return JSONResponse({"message": "is_enabled must be a boolean or equivalent"}, status_code=400)

        with Session(context.db_engine) as session:
            updated_option = update_search_option(session, key, is_enabled)
            if updated_option is None:
                return JSONResponse({"message": "search option not found"}, status_code=404)

            return JSONResponse(updated_option.to_pydantic().model_dump())

    return [
        Route("/api/settings/search_options", list_search_options_handler, methods=[HTTPMethod.GET]),
        Route("/api/settings/search_options/{key}", update_search_option_handler, methods=[HTTPMethod.PUT]),
    ]
