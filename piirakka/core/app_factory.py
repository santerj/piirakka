import asyncio
import logging
import os

from starlette.applications import Starlette
from starlette.routing import Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import piirakka
from . import preflight
from .context import Context
from .background import observe_current_track
from piirakka.services.track_history import TrackHistoryManager
from piirakka.services.websocket import WebSocketSubscriberManager, create_websocket_connection
from piirakka.views import pages, playback, stations

logger = logging.getLogger(__name__)


def create_app():
    """
    Create and configure the Starlette application with all dependencies.

    Returns:
        tuple: (app, context, track_history, subscriber_state)
    """

    templates_dir = os.path.join(os.path.dirname(piirakka.__file__), "templates")
    templates = Jinja2Templates(directory=templates_dir)
    static_dir = os.path.join(os.path.dirname(piirakka.__file__), "static")

    preflight.run_migrations()
    subscriber_state = WebSocketSubscriberManager()

    # define broadcaster function before context is created to avoid circular imports
    async def broadcast_message(message: str) -> None:
        """Broadcast message to all WebSocket subscribers."""
        await subscriber_state.broadcast(message)

    track_history = TrackHistoryManager()
    context = Context(broadcast_message_fn=broadcast_message, track_history_manager=track_history)

    # create endpoint with the bound state manager
    WebSocketConnection = create_websocket_connection(subscriber_state)

    app = Starlette(
        routes=[
            *pages.create_routes(templates, context, track_history),
            *stations.create_routes(context),
            *playback.create_routes(context),
            WebSocketRoute("/ws/subscribe", WebSocketConnection),
            Mount("/static", app=StaticFiles(directory=static_dir), name="static"),
        ]
    )

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(observe_current_track(context, track_history))

    @app.on_event("shutdown")
    async def shutdown():
        for subscriber in subscriber_state.subscribers:
            await subscriber.close()

    return app, context, track_history, subscriber_state
