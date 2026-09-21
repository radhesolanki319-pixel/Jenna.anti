"""
Real-time Device Bridge Router for Jenna AI — God Mode Edition.
Provides WebSocket endpoint for phone bridge client + REST endpoints
for God Mode actions, screen vision, and autonomous goal execution.
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.services.phone_bridge_hub import phone_bridge_hub

router = APIRouter(prefix="/device/bridge", tags=["Device Bridge — God Mode"])


# ══════════════════════════════════════════════════════════════
#  MODELS
# ══════════════════════════════════════════════════════════════

class ExecPayload(BaseModel):
    action: str = Field(description="God Mode action name (e.g., screen.tap, sms.send, app.open)")
    params: Dict[str, Any] = Field(default={}, description="Action parameters")
    timeout: float = Field(default=20.0, description="Timeout in seconds")


class ActionSequence(BaseModel):
    actions: List[Dict[str, Any]] = Field(description="List of actions: [{action: 'screen.tap', params: {x: 100, y: 200}}]")
    delay_ms: int = Field(default=200, description="Delay between actions in milliseconds")
    timeout: float = Field(default=60.0, description="Total timeout")


class GoalPayload(BaseModel):
    goal: str = Field(description="Natural language goal (e.g., 'Open WhatsApp and send hello to Rahul')")
    max_steps: int = Field(default=15, description="Maximum vision-action steps")
    timeout: float = Field(default=120.0, description="Total timeout")


# ══════════════════════════════════════════════════════════════
#  WEBSOCKET BRIDGE (Phone ↔ Cloud)
# ══════════════════════════════════════════════════════════════

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
                    "god_mode": metadata.get("god_mode", False),
                }))

            elif msg_type == "heartbeat":
                phone_bridge_hub.update_heartbeat(msg.get("vitals"))
                await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

            elif "id" in msg:
                phone_bridge_hub.handle_phone_response(msg)

    except WebSocketDisconnect:
        if phone_registered:
            phone_bridge_hub.unregister_phone()
        logger.info("God Mode bridge client disconnected.")
    except Exception as exc:
        if phone_registered:
            phone_bridge_hub.unregister_phone()
        logger.warning(f"Error in God Mode bridge: {exc}")


# ══════════════════════════════════════════════════════════════
#  REST ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/status")
async def get_bridge_status():
    """Get God Mode bridge connection status with full device metadata."""
    return phone_bridge_hub.get_status()


@router.post("/exec")
async def execute_phone_action(payload: ExecPayload):
    """Execute a single God Mode action on the phone.

    Examples:
    - {"action": "screen.tap", "params": {"x": 630, "y": 1400}}
    - {"action": "app.open", "params": {"package": "com.whatsapp"}}
    - {"action": "sms.send", "params": {"number": "+91...", "message": "Hello!"}}
    - {"action": "screen.screenshot", "params": {"base64": true}}
    - {"action": "camera.photo", "params": {"camera_id": 0}}
    """
    return await phone_bridge_hub.execute_on_phone(
        action=payload.action,
        params=payload.params,
        timeout=payload.timeout,
    )


@router.post("/exec/sequence")
async def execute_action_sequence(payload: ActionSequence):
    """Execute a sequence of God Mode actions with delay between each.

    Example:
    {
      "actions": [
        {"action": "app.open", "params": {"package": "com.whatsapp"}},
        {"action": "screen.tap", "params": {"x": 1020, "y": 120}},
        {"action": "screen.type", "params": {"text": "Hello"}}
      ],
      "delay_ms": 500
    }
    """
    results = []
    for i, act in enumerate(payload.actions):
        action_name = act.get("action", "")
        params = act.get("params", {})

        result = await phone_bridge_hub.execute_on_phone(
            action=action_name,
            params=params,
            timeout=payload.timeout / max(len(payload.actions), 1),
        )
        results.append({"step": i + 1, "action": action_name, **result})

        if not result.get("success", False):
            logger.warning(f"Sequence step {i+1} failed: {action_name}")

        if payload.delay_ms > 0 and i < len(payload.actions) - 1:
            import asyncio
            await asyncio.sleep(payload.delay_ms / 1000.0)

    return {
        "success": all(r.get("success", False) for r in results),
        "total_steps": len(results),
        "results": results,
    }


@router.get("/actions")
async def list_god_mode_actions():
    """List all available God Mode actions with descriptions."""
    actions = {
        "screen": {
            "screen.tap": {"params": {"x": "int", "y": "int"}, "desc": "Tap at coordinates"},
            "screen.swipe": {"params": {"x1": "int", "y1": "int", "x2": "int", "y2": "int", "duration_ms": "int=300"}, "desc": "Swipe gesture"},
            "screen.type": {"params": {"text": "str"}, "desc": "Type text on focused input"},
            "screen.key": {"params": {"keycode": "str (HOME/BACK/ENTER/POWER etc)"}, "desc": "Send key event"},
            "screen.long_press": {"params": {"x": "int", "y": "int", "duration_ms": "int=1000"}, "desc": "Long press"},
            "screen.scroll_down": {"params": {}, "desc": "Scroll screen down"},
            "screen.scroll_up": {"params": {}, "desc": "Scroll screen up"},
            "screen.unlock": {"params": {}, "desc": "Wake + unlock screen"},
            "screen.screenshot": {"params": {"base64": "bool=true"}, "desc": "Capture screenshot"},
        },
        "apps": {
            "app.open": {"params": {"package": "str"}, "desc": "Open app"},
            "app.close": {"params": {"package": "str"}, "desc": "Force stop app"},
            "app.current": {"params": {}, "desc": "Get current app"},
            "app.list": {"params": {}, "desc": "List installed apps"},
        },
        "communication": {
            "sms.send": {"params": {"number": "str", "message": "str"}, "desc": "Send SMS"},
            "sms.inbox": {"params": {"limit": "int=20"}, "desc": "Read SMS inbox"},
            "call.dial": {"params": {"number": "str"}, "desc": "Make phone call"},
        },
        "media": {
            "camera.photo": {"params": {"camera_id": "int=0"}, "desc": "Take photo"},
            "mic.record": {"params": {"duration": "int=5"}, "desc": "Record audio"},
        },
        "sensors": {
            "location.get": {"params": {"provider": "str=gps"}, "desc": "Get GPS location"},
        },
        "notifications": {
            "notif.send": {"params": {"title": "str", "content": "str"}, "desc": "Send notification"},
            "notif.list": {"params": {}, "desc": "List notifications"},
        },
        "clipboard": {
            "clipboard.get": {"params": {}, "desc": "Get clipboard"},
            "clipboard.set": {"params": {"text": "str"}, "desc": "Set clipboard"},
        },
        "contacts": {
            "contacts.list": {"params": {}, "desc": "List contacts"},
        },
        "settings": {
            "wifi.on": {"params": {}, "desc": "Enable WiFi"},
            "wifi.off": {"params": {}, "desc": "Disable WiFi"},
            "bluetooth.on": {"params": {}, "desc": "Enable Bluetooth"},
            "bluetooth.off": {"params": {}, "desc": "Disable Bluetooth"},
            "volume.set": {"params": {"stream": "int=3", "level": "int"}, "desc": "Set volume"},
            "brightness.set": {"params": {"level": "int (0-255)"}, "desc": "Set brightness"},
        },
        "vitals": {
            "battery.status": {"params": {}, "desc": "Battery status"},
            "device.info": {"params": {}, "desc": "Device info"},
        },
        "hardware": {
            "torch.on": {"params": {}, "desc": "Flashlight on"},
            "torch.off": {"params": {}, "desc": "Flashlight off"},
            "vibrate": {"params": {"duration_ms": "int=500"}, "desc": "Vibrate phone"},
            "tts.speak": {"params": {"text": "str", "language": "str=en"}, "desc": "Speak text aloud"},
        },
        "filesystem": {
            "file.read": {"params": {"path": "str"}, "desc": "Read file"},
            "file.write": {"params": {"path": "str", "content": "str"}, "desc": "Write file"},
            "file.list": {"params": {"path": "str"}, "desc": "List directory"},
            "file.delete": {"params": {"path": "str"}, "desc": "Delete file"},
        },
        "system": {
            "shell": {"params": {"command": "str"}, "desc": "Execute shell command"},
        },
    }

    total = sum(len(v) for v in actions.values())
    return {
        "total_actions": total,
        "categories": list(actions.keys()),
        "actions": actions,
        "god_mode": True,
    }
