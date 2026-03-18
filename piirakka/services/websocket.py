import logging

from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class WebSocketSubscriberManager:
    """
    Manages active websocket connections and broadcasts messages to subscribers
    """

    def __init__(self):
        self.subscribers: list[WebSocket] = []

    async def add_subscriber(self, websocket: WebSocket) -> None:
        # add subscriber to the broadcast list
        self.subscribers.append(websocket)
        logger.debug(f"WebSocket subscriber connected. Total subscribers: {len(self.subscribers)}")

    async def remove_subscriber(self, websocket: WebSocket) -> None:
        # remove subscriber from the broadcast list
        self.subscribers.remove(websocket)
        logger.debug(f"WebSocket subscriber disconnected. Total subscribers: {len(self.subscribers)}")

    async def broadcast(self, message: str) -> None:
        # broadcast message to all connected subscribers
        for subscriber in self.subscribers:
            await subscriber.send_text(message)

    def __len__(self) -> int:
        return len(self.subscribers)


def create_websocket_connection(manager: WebSocketSubscriberManager):
    # Factory function that creates a WebSocketConnection endpoint with a bound subscription manager

    async def broadcast_message(message: str) -> None:
        # broadcast message using the manager
        await manager.broadcast(message)

    class WebSocketConnection(WebSocketEndpoint):
        # websocket endpoint

        encoding = "text"

        async def on_connect(self, websocket: WebSocket) -> None:
            # add subscriber on connect
            await websocket.accept()
            await manager.add_subscriber(websocket)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            # remove subscriber on disconnect
            await manager.remove_subscriber(websocket)

        async def on_receive(self, websocket: WebSocket, data: str) -> None:
            # echo received message back to all subscribers – consider the implications of exposing
            logger.debug(f"Received message: {data}")
            await broadcast_message(data)

    return WebSocketConnection
