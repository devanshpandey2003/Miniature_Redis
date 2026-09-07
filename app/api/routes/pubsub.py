"""
real Pub/Sub,
using WebSockets instead of a custom binary protocol. A subscriber opens a
persistent connection to a channel; publishers POST a message and every
connected subscriber gets it immediately.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.pubsub import channel_manager
from app.models.schemas import PublishRequest

router = APIRouter(tags=["pubsub"])


@router.websocket("/ws/subscribe/{channel}")
async def subscribe(websocket: WebSocket, channel: str):
    # You MUST accept() before you can send/receive on a WebSocket.
    await websocket.accept()
    channel_manager.add(channel, websocket)
    try:
        while True:
            # We don't expect the client to send us anything meaningful --
            # this just blocks here, keeping the connection open, until the
            # client disconnects (which raises WebSocketDisconnect).
            await websocket.receive_text()
    except WebSocketDisconnect:
        channel_manager.remove(channel, websocket)


@router.post("/publish/{channel}")
async def publish(channel: str, body: PublishRequest):
    delivered = await channel_manager.broadcast(channel, body.message)
    return {"channel": channel, "delivered_to": delivered}
