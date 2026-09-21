"""
Jenna AI — Termux:API Bridge (God Mode)
Wraps all Termux:API commands for direct phone hardware access:
  • SMS send/receive
  • Phone calls
  • Camera & Microphone
  • GPS Location
  • Notifications
  • Clipboard
  • Contacts
  • Battery & Sensors
  • WiFi info
  • TTS (Text-to-Speech)
  • Torch/Flashlight
  • Vibrate

All commands run via Termux:API — requires Termux:API app installed.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jenna.termux_api")

SCREENSHOT_DIR = os.getenv("JENNA_SCREENSHOT_DIR", "/data/data/com.termux/files/home")


async def _run_cmd(cmd: str, timeout: float = 15.0, input_data: Optional[str] = None) -> Dict[str, Any]:
    """Execute a Termux:API command asynchronously."""
    start = time.time()
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None,
        )
        stdin_bytes = input_data.encode() if input_data else None
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=stdin_bytes), timeout=timeout)
        stdout_str = stdout.decode("utf-8", errors="replace").strip()

        # Try JSON parse
        parsed = None
        if stdout_str:
            try:
                parsed = json.loads(stdout_str)
            except json.JSONDecodeError:
                pass

        return {
            "success": proc.returncode == 0,
            "stdout": stdout_str,
            "stderr": stderr.decode("utf-8", errors="replace").strip(),
            "parsed": parsed,
            "exit_code": proc.returncode,
            "duration_ms": round((time.time() - start) * 1000, 1),
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Command timed out after {timeout}s", "duration_ms": round((time.time() - start) * 1000, 1)}
    except Exception as e:
        return {"success": False, "error": str(e), "duration_ms": round((time.time() - start) * 1000, 1)}


# ══════════════════════════════════════════════════════════════
#  SMS
# ══════════════════════════════════════════════════════════════

async def sms_send(number: str, message: str) -> Dict[str, Any]:
    """Send SMS to a phone number."""
    # Escape message for shell
    safe_msg = message.replace("'", "'\\''")
    result = await _run_cmd(f"termux-sms-send -n '{number}' '{safe_msg}'")
    return {"action": "sms.send", "number": number, "message": message, **result}


async def sms_inbox(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Read SMS inbox."""
    result = await _run_cmd(f"termux-sms-list -l {limit} -o {offset}")
    messages = result.get("parsed", []) if isinstance(result.get("parsed"), list) else []
    return {"action": "sms.inbox", "count": len(messages), "messages": messages, **result}


# ══════════════════════════════════════════════════════════════
#  PHONE CALLS
# ══════════════════════════════════════════════════════════════

async def call_dial(number: str) -> Dict[str, Any]:
    """Initiate a phone call."""
    result = await _run_cmd(f"termux-telephony-call '{number}'")
    return {"action": "call.dial", "number": number, **result}


async def call_info() -> Dict[str, Any]:
    """Get current cell info."""
    result = await _run_cmd("termux-telephony-cellinfo")
    return {"action": "call.info", **result}


async def call_device_info() -> Dict[str, Any]:
    """Get telephony device info (IMEI, SIM, etc)."""
    result = await _run_cmd("termux-telephony-deviceinfo")
    return {"action": "call.device_info", **result}


# ══════════════════════════════════════════════════════════════
#  CAMERA & MICROPHONE
# ══════════════════════════════════════════════════════════════

async def camera_photo(camera_id: int = 0, save_path: Optional[str] = None) -> Dict[str, Any]:
    """Take a photo using specified camera (0=back, 1=front)."""
    if not save_path:
        save_path = f"{SCREENSHOT_DIR}/jenna_photo_{int(time.time())}.jpg"
    result = await _run_cmd(f"termux-camera-photo -c {camera_id} '{save_path}'", timeout=10.0)
    return {"action": "camera.photo", "camera_id": camera_id, "path": save_path, **result}


async def camera_info() -> Dict[str, Any]:
    """Get camera info (available cameras)."""
    result = await _run_cmd("termux-camera-info")
    return {"action": "camera.info", **result}


async def mic_record(duration_secs: int = 5, save_path: Optional[str] = None) -> Dict[str, Any]:
    """Record audio from microphone."""
    if not save_path:
        save_path = f"{SCREENSHOT_DIR}/jenna_audio_{int(time.time())}.m4a"
    result = await _run_cmd(
        f"termux-microphone-record -l {duration_secs} -f '{save_path}'",
        timeout=duration_secs + 5.0
    )
    return {"action": "mic.record", "duration": duration_secs, "path": save_path, **result}


async def mic_stop() -> Dict[str, Any]:
    """Stop microphone recording."""
    result = await _run_cmd("termux-microphone-record -q")
    return {"action": "mic.stop", **result}


# ══════════════════════════════════════════════════════════════
#  LOCATION (GPS)
# ══════════════════════════════════════════════════════════════

async def location_get(provider: str = "gps") -> Dict[str, Any]:
    """Get current GPS location. Provider: gps, network, passive."""
    result = await _run_cmd(f"termux-location -p {provider}", timeout=30.0)
    location = result.get("parsed", {})
    return {
        "action": "location.get",
        "provider": provider,
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "altitude": location.get("altitude"),
        "accuracy": location.get("accuracy"),
        **result,
    }


# ══════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════

async def notification_send(
    title: str,
    content: str,
    notification_id: Optional[str] = None,
    priority: str = "default",
    vibrate: bool = False,
    sound: bool = False,
) -> Dict[str, Any]:
    """Send a notification."""
    cmd = f"termux-notification -t '{title}' -c '{content}'"
    if notification_id:
        cmd += f" --id '{notification_id}'"
    if priority != "default":
        cmd += f" --priority {priority}"
    if vibrate:
        cmd += " --vibrate 200,100,200"
    if sound:
        cmd += " --sound"
    result = await _run_cmd(cmd)
    return {"action": "notif.send", "title": title, "content": content, **result}


async def notification_list() -> Dict[str, Any]:
    """List all active notifications."""
    result = await _run_cmd("termux-notification-list")
    notifs = result.get("parsed", []) if isinstance(result.get("parsed"), list) else []
    return {"action": "notif.list", "count": len(notifs), "notifications": notifs, **result}


async def notification_remove(notification_id: str) -> Dict[str, Any]:
    """Remove a notification by ID."""
    result = await _run_cmd(f"termux-notification-remove '{notification_id}'")
    return {"action": "notif.remove", "id": notification_id, **result}


# ══════════════════════════════════════════════════════════════
#  CLIPBOARD
# ══════════════════════════════════════════════════════════════

async def clipboard_get() -> Dict[str, Any]:
    """Get current clipboard content."""
    result = await _run_cmd("termux-clipboard-get")
    return {"action": "clipboard.get", "content": result.get("stdout", ""), **result}


async def clipboard_set(text: str) -> Dict[str, Any]:
    """Set clipboard content."""
    safe_text = text.replace("'", "'\\''")
    result = await _run_cmd(f"termux-clipboard-set '{safe_text}'")
    return {"action": "clipboard.set", "text": text, **result}


# ══════════════════════════════════════════════════════════════
#  CONTACTS
# ══════════════════════════════════════════════════════════════

async def contacts_list() -> Dict[str, Any]:
    """List all contacts."""
    result = await _run_cmd("termux-contact-list", timeout=20.0)
    contacts = result.get("parsed", []) if isinstance(result.get("parsed"), list) else []
    return {"action": "contacts.list", "count": len(contacts), "contacts": contacts, **result}


# ══════════════════════════════════════════════════════════════
#  BATTERY & DEVICE VITALS
# ══════════════════════════════════════════════════════════════

async def battery_status() -> Dict[str, Any]:
    """Get battery status (level, charging, temperature, etc)."""
    result = await _run_cmd("termux-battery-status")
    battery = result.get("parsed", {})
    return {
        "action": "battery.status",
        "percentage": battery.get("percentage"),
        "status": battery.get("status"),
        "temperature": battery.get("temperature"),
        "plugged": battery.get("plugged"),
        **result,
    }


async def wifi_info() -> Dict[str, Any]:
    """Get WiFi connection info."""
    result = await _run_cmd("termux-wifi-connectioninfo")
    return {"action": "wifi.info", **result}


async def wifi_scan() -> Dict[str, Any]:
    """Scan for nearby WiFi networks."""
    result = await _run_cmd("termux-wifi-scaninfo", timeout=15.0)
    networks = result.get("parsed", []) if isinstance(result.get("parsed"), list) else []
    return {"action": "wifi.scan", "count": len(networks), "networks": networks, **result}


# ══════════════════════════════════════════════════════════════
#  TTS (TEXT-TO-SPEECH)
# ══════════════════════════════════════════════════════════════

async def tts_speak(text: str, language: str = "en", rate: float = 1.0) -> Dict[str, Any]:
    """Speak text aloud via TTS."""
    safe_text = text.replace("'", "'\\''")
    result = await _run_cmd(f"termux-tts-speak -l '{language}' -r {rate} '{safe_text}'", timeout=30.0)
    return {"action": "tts.speak", "text": text, "language": language, **result}


# ══════════════════════════════════════════════════════════════
#  MISC HARDWARE
# ══════════════════════════════════════════════════════════════

async def torch_toggle(enable: bool) -> Dict[str, Any]:
    """Toggle flashlight/torch."""
    state = "on" if enable else "off"
    result = await _run_cmd(f"termux-torch {state}")
    return {"action": "torch.toggle", "enabled": enable, **result}


async def vibrate(duration_ms: int = 500, force: bool = True) -> Dict[str, Any]:
    """Vibrate the phone."""
    cmd = f"termux-vibrate -d {duration_ms}"
    if force:
        cmd += " -f"
    result = await _run_cmd(cmd)
    return {"action": "vibrate", "duration_ms": duration_ms, **result}


async def volume_get() -> Dict[str, Any]:
    """Get current volume levels."""
    result = await _run_cmd("termux-volume")
    return {"action": "volume.get", **result}


async def media_player(action: str = "info") -> Dict[str, Any]:
    """Control media playback. Actions: info, play, pause, next, previous."""
    result = await _run_cmd(f"termux-media-player {action}")
    return {"action": f"media.{action}", **result}
