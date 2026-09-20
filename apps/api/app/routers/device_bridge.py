"""
Real-time Device Bridge Router for Jenna AI.
Provides WebSocket endpoint for physical Android phone client
and REST status endpoints.
"""

from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.logging import logger
from app.services.phone_bridge_hub import phone_bridge_hub

router = APIRouter(prefix="/device/bridge", tags=["Device Bridge"])


class ExecPayload(BaseModel):
    action: str
    params: Dict[str, Any] = {}
    timeout: float = 20.0


@router.websocket("")
@router.websocket("/")
async def phone_bridge_websocket(websocket: WebSocket):
    """Real-time bi-directional WebSocket tunnel connecting physical phone Termux to Cloud Jenna."""
    await websocket.accept()
    phone_registered = False

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                import json
                msg = json.loads(raw)
            except Exception:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "handshake":
                metadata = msg.get("metadata", {})
                await phone_bridge_hub.register_phone(websocket, metadata)
                phone_registered = True
                await websocket.send_text(json.dumps({
                    "type": "handshake_ack",
                    "status": "connected",
                    "server": "Jenna Cloud on Render",
                }))

            elif msg_type == "heartbeat":
                phone_bridge_hub.update_heartbeat(msg.get("vitals"))
                await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

            elif "id" in msg:
                phone_bridge_hub.handle_phone_response(msg)

    except WebSocketDisconnect:
        if phone_registered:
            phone_bridge_hub.unregister_phone()
        logger.info("Physical phone client disconnected cleanly from bridge.")
    except Exception as exc:
        if phone_registered:
            phone_bridge_hub.unregister_phone()
        logger.warning(f"Error in phone bridge WebSocket: {exc}")


@router.get("/status")
async def get_bridge_status():
    """Check if Boss's physical phone is currently connected via live WebSocket tunnel."""
    return phone_bridge_hub.get_status()


@router.post("/exec")
async def execute_phone_action(payload: ExecPayload):
    """Execute action directly on physical phone via tunnel."""
    return await phone_bridge_hub.execute_on_phone(
        action=payload.action,
        params=payload.params,
        timeout=payload.timeout,
    )
