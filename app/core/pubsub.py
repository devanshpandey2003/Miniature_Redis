"""
A minimal Pub/Sub implementation. Real Redis clients SUBSCRIBE to a channel
over the same TCP connection they use for commands. Here, WebSockets do the
same job: a client opens a WebSocket to a channel and receives every
message published to it, until it disconnects.
"""
from collections import defaultdict
from fastapi import WebSocket


class ChannelManager:
    def __init__(self):
        # channel name -> set of connected websockets subscribed to it
        self._subscribers: dict[str, set[WebSocket]] = defaultdict(set)

    def add(self, channel: str, websocket: WebSocket) -> None:
        self._subscribers[channel].add(websocket)

    def remove(self, channel: str, websocket: WebSocket) -> None:
        self._subscribers[channel].discard(websocket)
        # Clean up empty channels so the dict doesn't grow forever.
        if not self._subscribers[channel]:
            del self._subscribers[channel]

    async def broadcast(self, channel: str, message: dict) -> int:
        """
        Send `message` to every subscriber of `channel`. Returns how many
        subscribers received it. Dead connections are pruned as we go.
        """
        subscribers = list(self._subscribers.get(channel, ()))
        delivered = 0
        for ws in subscribers:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                # Connection is dead/closed -- drop it.
                self.remove(channel, ws)
        return delivered


# One shared instance for the whole app -- every websocket route and every
# publish request goes through this same object.
channel_manager = ChannelManager()
