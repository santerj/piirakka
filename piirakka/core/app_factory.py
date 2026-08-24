import asyncio
import contextlib
import logging
import os

from starlette.applications import Starlette
from starlette.routing import Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import piirakka
from piirakka.services.track_history import TrackHistoryManager
from piirakka.services.websocket import (WebSocketSubscriberManager,
                                         create_websocket_connection)
from piirakka.views import devices, pages, playback, settings, stations

from . import preflight
from .background import background_bluetooth_scan, observe_current_track
from .context import Context

logger = logging.getLogger(__name__)


def create_app(spawn_mpv: bool = True):
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
    context = Context(broadcast_message_fn=broadcast_message, track_history_manager=track_history, spawn_mpv=spawn_mpv)

    # create endpoint with the bound state manager
    WebSocketConnection = create_websocket_connection(subscriber_state)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> None:
        asyncio.create_task(observe_current_track(context, track_history))  # startup
        asyncio.create_task(background_bluetooth_scan(context))
        yield
        for subscriber in subscriber_state.subscribers:  # shutdown
            await subscriber.close()

    app = Starlette(
        lifespan=lifespan,
        routes=[
            *pages.create_routes(templates, context, track_history),
            *devices.create_routes(context),
            *stations.create_routes(context),
            *playback.create_routes(context),
            *settings.create_routes(context),
            WebSocketRoute("/ws/subscribe", WebSocketConnection),
            Mount("/static", app=StaticFiles(directory=static_dir), name="static"),
        ],
    )

    return app, context, track_history, subscriber_state
