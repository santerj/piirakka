"""
WebSocket subscriber state management.
"""

import logging

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class WebSocketSubscriberState:
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
