"""
WebSocket subscriber state management and connection handling.
"""

import logging
from typing import TYPE_CHECKING, Callable

from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class WebSocketSubscriberManager:
    """
    Manages active WebSocket connections and broadcasts messages to subscribers
    """

    def __init__(self):
        self.subscribers: list[WebSocket] = []

    async def add_subscriber(self, websocket: WebSocket) -> None:
        # Add a WebSocket subscriber to the broadcast list
        self.subscribers.append(websocket)
        logger.debug(f"WebSocket subscriber connected. Total subscribers: {len(self.subscribers)}")

    async def remove_subscriber(self, websocket: WebSocket) -> None:
        # Remove a WebSocket subscriber from the broadcast list
        self.subscribers.remove(websocket)
        logger.debug(f"WebSocket subscriber disconnected. Total subscribers: {len(self.subscribers)}")

    async def broadcast(self, message: str) -> None:
        # Broadcast a message to all connected subscribers.
        for subscriber in self.subscribers:
            await subscriber.send_text(message)  # starlette.websockets.WebSocket.send_text()


def create_websocket_connection(
    subscriber_manager: WebSocketSubscriberManager, broadcast_func: Callable
) -> type[WebSocketEndpoint]:
    """
    Factory function to create a WebSocketConnection endpoint with dependencies bound.

    Args:
        subscriber_manager: WebSocketSubscriberManager instance
        broadcast_func: Async function to broadcast messages

    Returns:
        A WebSocketEndpoint class configured with the provided dependencies
    """

    class WebSocketConnection(WebSocketEndpoint):
        """WebSocket endpoint for real-time updates."""

        encoding = "text"

        async def on_connect(self, websocket: WebSocket) -> None:
            """Handle new WebSocket connection."""
            await websocket.accept()
            await subscriber_manager.add_subscriber(websocket)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            """Handle WebSocket disconnection."""
            await subscriber_manager.remove_subscriber(websocket)

        async def on_receive(self, websocket: WebSocket, data: str) -> None:
            """Handle incoming WebSocket messages by broadcasting them."""
            logger.debug(f"Received message: {data}")
            await broadcast_func(data)

    return WebSocketConnection
