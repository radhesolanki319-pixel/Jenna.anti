import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import WebSocket

from app.core.logging import logger


class ConnectionManager:
    """Manages active WebSocket connections with heartbeat and event routing."""

    def __init__(self):
        # Map connection_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # Optional metadata per connection (user_id, client info, subscriptions)
        self.connection_meta: dict[str, dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str | None = None,
        token: str | None = None,
    ) -> str:
        """Accept WebSocket connection and register client.

        Authentication-ready: 'token' is accepted and stored for future validation.
        """
        await websocket.accept()
        conn_id = client_id or str(uuid.uuid4())
        self.active_connections[conn_id] = websocket
        self.connection_meta[conn_id] = {
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "authenticated": bool(token),
            "user_id": None,  # Will be populated by auth in future phases
            "subscriptions": set(),
        }

        logger.info(
            f"WebSocket client connected: {conn_id}",
            extra={"client_id": conn_id, "authenticated": bool(token)},
        )

        # Send initial connected acknowledgement
        await self.send_json(
            conn_id,
            {
                "type": "connection_established",
                "client_id": conn_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "jenna-api",
                "features": ["heartbeat", "events", "subscriptions"],
            },
        )
        return conn_id

    def disconnect(self, client_id: str) -> None:
        """Unregister WebSocket connection cleanly."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_meta:
            del self.connection_meta[client_id]

        logger.info(
            f"WebSocket client disconnected: {client_id}",
            extra={"client_id": client_id},
        )

    async def send_json(self, client_id: str, message: dict[str, Any]) -> bool:
        """Send JSON message to a specific connection."""
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send to WebSocket client {client_id}: {e}")
                self.disconnect(client_id)
        return False

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        for client_id in list(self.active_connections.keys()):
            await self.send_json(client_id, message)

    async def handle_message(self, client_id: str, data: dict[str, Any]) -> None:
        """Process incoming client message and route events."""
        event_type = data.get("type", "").lower()

        logger.info(
            f"WebSocket message received from {client_id}: {event_type}",
            extra={"client_id": client_id, "event_type": event_type},
        )

        # 1. Heartbeat / Ping-Pong
        if event_type == "ping":
            await self.send_json(
                client_id,
                {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "client_id": client_id,
                },
            )

        # 2. Subscription placeholder for future channels
        elif event_type == "subscribe":
            channels = data.get("channels", [])
            meta = self.connection_meta.get(client_id, {})
            if "subscriptions" in meta:
                meta["subscriptions"].update(channels)

            await self.send_json(
                client_id,
                {
                    "type": "subscribed",
                    "channels": list(channels),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # 3. Realtime AI Generation & Streaming
        elif event_type == "ai.generate" or (event_type == "ai_stream" and "messages" in data.get("payload", {})):
            payload = data.get("payload", {})
            try:
                from app.ai.service import get_ai_service
                from app.ai.types import AIRequest
                ai_service = get_ai_service()
                ai_request = AIRequest.model_validate(payload)
                async for stream_event in ai_service.stream(ai_request):
                    await self.send_json(client_id, stream_event)
            except Exception as exc:
                await self.send_json(
                    client_id,
                    {
                        "type": "stream.error",
                        "request_id": payload.get("request_id"),
                        "error_code": type(exc).__name__,
                        "message": str(exc),
                    },
                )

        # 4. Extension points for future phases (voice, agent, devices, or legacy stubs)
        elif event_type in ("ai_stream", "voice_event", "agent_event", "device_event", "notification"):
            await self.send_json(
                client_id,
                {
                    "type": "event_acknowledged",
                    "event_type": event_type,
                    "status": "pending_implementation_in_future_phase",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # 4. Unknown event
        else:
            await self.send_json(
                client_id,
                {
                    "type": "error",
                    "code": "UNKNOWN_EVENT",
                    "message": f"Unrecognized event type: '{event_type}'",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )


ws_manager = ConnectionManager()
