"""
WebSocket subscriber state management and connection handling.
"""

import logging

from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)

# Module-level reference to subscriber manager, set by main.py during initialization
subscriber_state: "WebSocketSubscriberManager | None" = None


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
            await subscriber.send_text(message)


async def broadcast_message(message: str) -> None:
    """
    Broadcast a message to all WebSocket subscribers.

    Delegates to the subscriber_state manager that is set during initialization.
    """
    if subscriber_state is None:
        logger.error("broadcast_message called but subscriber_state not initialized")
        return
    await subscriber_state.broadcast(message)


class WebSocketConnection(WebSocketEndpoint):
    """WebSocket endpoint for real-time updates."""

    encoding = "text"

    async def on_connect(self, websocket: WebSocket) -> None:
        # add subscriber on connect
        await websocket.accept()
        if subscriber_state is not None:
            await subscriber_state.add_subscriber(websocket)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        # remove subscriber on disconnect
        if subscriber_state is not None:
            await subscriber_state.remove_subscriber(websocket)

    async def on_receive(self, websocket: WebSocket, data: str) -> None:
        # echo received message back to all subscribers - consider implications of using
        logger.debug(f"Received message: {data}")
        await broadcast_message(data)
