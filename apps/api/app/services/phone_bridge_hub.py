"""
Jenna AI Platform — Real-Time Phone Bridge Hub
Maintains live WebSocket connection between Cloud Jenna (Render)
and Boss's physical phone (iQOO Neo 10 Termux).
Enables Cloud Jenna to execute commands, read files, and inspect hardware
directly on Boss's phone with zero battery drain.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from fastapi import WebSocket

logger = logging.getLogger("jenna.phone_bridge")


class PhoneBridgeHub:
    """Central WebSocket hub managing real-time tunnel to Boss's physical phone."""

    def __init__(self):
        self.phone_ws: Optional[WebSocket] = None
        self.phone_meta: Dict[str, Any] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.last_seen: float = 0.0

    @property
    def is_connected(self) -> bool:
        return self.phone_ws is not None and (time.time() - self.last_seen < 60.0)

    async def register_phone(self, ws: WebSocket, metadata: Dict[str, Any]) -> None:
        """Register live physical phone connection."""
        self.phone_ws = ws
        self.phone_meta = {
            **metadata,
            "connected_at": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.last_seen = time.time()
        logger.info(f"Phone bridge connected: {metadata.get('device_model', 'Android')}")

    def unregister_phone(self) -> None:
        """Unregister physical phone."""
        self.phone_ws = None
        self.phone_meta["disconnected_at"] = time.time()
        logger.info("Phone bridge disconnected.")

    def update_heartbeat(self, vitals: Optional[Dict[str, Any]] = None) -> None:
        """Update last seen timestamp and latest phone vitals."""
        self.last_seen = time.time()
        if vitals:
            self.phone_meta["latest_vitals"] = vitals

    def handle_phone_response(self, message: Dict[str, Any]) -> None:
        """Route incoming response from phone to awaiting future."""
        req_id = message.get("id")
        if req_id and req_id in self.pending_requests:
            future = self.pending_requests.pop(req_id)
            if not future.done():
                future.set_result(message.get("result", {}))

    async def execute_on_phone(self, action: str, params: Dict[str, Any], timeout: float = 20.0) -> Dict[str, Any]:
        """Send command across WebSocket tunnel to Boss's physical phone and await result."""
        if not self.is_connected or not self.phone_ws:
            return {
                "success": False,
                "error": "Phone is currently not bridged (Termux phone bridge client is offline or reconnecting).",
                "phone_connected": False,
            }

        req_id = f"cmd-{uuid.uuid4().hex[:8]}"
        payload = {
            "id": req_id,
            "action": action,
            "params": params,
            "timestamp": time.time(),
        }

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[req_id] = future

        try:
            await self.phone_ws.send_text(json.dumps(payload))
            result = await asyncio.wait_for(future, timeout=timeout)
            return {"success": True, "phone_connected": True, "result": result}
        except asyncio.TimeoutError:
            self.pending_requests.pop(req_id, None)
            return {"success": False, "error": f"Command '{action}' timed out after {timeout}s on phone.", "phone_connected": True}
        except Exception as exc:
            self.pending_requests.pop(req_id, None)
            return {"success": False, "error": str(exc), "phone_connected": False}

    def get_status(self) -> Dict[str, Any]:
        """Return status of live phone bridge."""
        return {
            "connected": self.is_connected,
            "last_seen_seconds_ago": round(time.time() - self.last_seen, 1) if self.last_seen else None,
            "device": self.phone_meta.get("device_model", "Unknown Android Device"),
            "metadata": self.phone_meta,
        }


phone_bridge_hub = PhoneBridgeHub()
