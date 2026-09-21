"""
Jenna AI — God Mode Engine
Central command router that gives Jenna full autonomous control over Boss's phone.
Routes natural language or structured commands to the appropriate controller:
  • ADB Controller — screen, apps, settings
  • Termux:API Bridge — SMS, calls, camera, GPS, notifications, clipboard, contacts
  • File System — direct file operations

Designed for iQOO Neo 10 (non-rooted), ADB + Termux:API.
"""

import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jenna.god_mode")

# Import controllers (graceful fallback for cloud-only mode)
try:
    from app.services import adb_controller as adb
    from app.services import termux_api_bridge as tapi
    CONTROLLERS_AVAILABLE = True
except ImportError:
    CONTROLLERS_AVAILABLE = False
    logger.warning("God Mode controllers not available (cloud-only mode?)")

STORAGE_ROOT = Path("/storage/emulated/0")


# ══════════════════════════════════════════════════════════════
#  ACTION REGISTRY — maps action names → handler functions
# ══════════════════════════════════════════════════════════════

ACTION_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_action(name: str, handler, category: str, description: str, risk: str = "low"):
    """Register a god mode action."""
    ACTION_REGISTRY[name] = {
        "handler": handler,
        "category": category,
        "description": description,
        "risk": risk,
    }


def _register_all_actions():
    """Register all available god mode actions."""
    if not CONTROLLERS_AVAILABLE:
        return

    # ── Screen Control ──
    register_action("screen.tap", _screen_tap, "screen", "Tap at coordinates (x, y)")
    register_action("screen.swipe", _screen_swipe, "screen", "Swipe from (x1,y1) to (x2,y2)")
    register_action("screen.type", _screen_type, "screen", "Type text on focused input")
    register_action("screen.key", _screen_key, "screen", "Send keyevent (HOME, BACK, ENTER, etc)")
    register_action("screen.long_press", _screen_long_press, "screen", "Long press at coordinates")
    register_action("screen.scroll_down", _screen_scroll_down, "screen", "Scroll screen down")
    register_action("screen.scroll_up", _screen_scroll_up, "screen", "Scroll screen up")
    register_action("screen.unlock", _screen_unlock, "screen", "Wake and unlock screen")
    register_action("screen.screenshot", _screen_screenshot, "screen", "Capture screenshot")

    # ── App Management ──
    register_action("app.open", _app_open, "apps", "Open app by package name")
    register_action("app.close", _app_close, "apps", "Force stop app")
    register_action("app.current", _app_current, "apps", "Get currently focused app")
    register_action("app.list", _app_list, "apps", "List installed apps")
    register_action("app.install", _app_install, "apps", "Install APK", risk="medium")
    register_action("app.uninstall", _app_uninstall, "apps", "Uninstall app", risk="medium")

    # ── SMS ──
    register_action("sms.send", _sms_send, "communication", "Send SMS")
    register_action("sms.inbox", _sms_inbox, "communication", "Read SMS inbox")

    # ── Calls ──
    register_action("call.dial", _call_dial, "communication", "Make a phone call")
    register_action("call.info", _call_info, "communication", "Get cell info")

    # ── Camera & Mic ──
    register_action("camera.photo", _camera_photo, "media", "Take a photo")
    register_action("camera.info", _camera_info, "media", "Get camera info")
    register_action("mic.record", _mic_record, "media", "Record audio")
    register_action("mic.stop", _mic_stop, "media", "Stop recording")

    # ── Location ──
    register_action("location.get", _location_get, "sensors", "Get GPS location")

    # ── Notifications ──
    register_action("notif.send", _notif_send, "notifications", "Send notification")
    register_action("notif.list", _notif_list, "notifications", "List notifications")
    register_action("notif.remove", _notif_remove, "notifications", "Remove notification")

    # ── Clipboard ──
    register_action("clipboard.get", _clipboard_get, "clipboard", "Get clipboard content")
    register_action("clipboard.set", _clipboard_set, "clipboard", "Set clipboard content")

    # ── Contacts ──
    register_action("contacts.list", _contacts_list, "contacts", "List all contacts")

    # ── Settings ──
    register_action("wifi.on", _wifi_on, "settings", "Enable WiFi")
    register_action("wifi.off", _wifi_off, "settings", "Disable WiFi")
    register_action("wifi.info", _wifi_info, "settings", "Get WiFi info")
    register_action("bluetooth.on", _bt_on, "settings", "Enable Bluetooth")
    register_action("bluetooth.off", _bt_off, "settings", "Disable Bluetooth")
    register_action("volume.set", _volume_set, "settings", "Set volume level")
    register_action("volume.get", _volume_get, "settings", "Get volume levels")
    register_action("brightness.set", _brightness_set, "settings", "Set screen brightness")

    # ── Device Vitals ──
    register_action("battery.status", _battery_status, "vitals", "Get battery status")
    register_action("device.info", _device_info, "vitals", "Get device info")

    # ── File System ──
    register_action("file.read", _file_read, "filesystem", "Read file contents")
    register_action("file.write", _file_write, "filesystem", "Write file contents")
    register_action("file.delete", _file_delete, "filesystem", "Delete file", risk="medium")
    register_action("file.move", _file_move, "filesystem", "Move/rename file")
    register_action("file.list", _file_list, "filesystem", "List directory contents")
    register_action("file.exists", _file_exists, "filesystem", "Check if file exists")

    # ── Misc Hardware ──
    register_action("torch.on", _torch_on, "hardware", "Turn on flashlight")
    register_action("torch.off", _torch_off, "hardware", "Turn off flashlight")
    register_action("vibrate", _vibrate, "hardware", "Vibrate phone")
    register_action("tts.speak", _tts_speak, "hardware", "Speak text aloud")

    # ── Shell (catch-all) ──
    register_action("shell", _shell_exec, "system", "Execute shell command", risk="high")


# ══════════════════════════════════════════════════════════════
#  ACTION HANDLERS (thin wrappers with param extraction)
# ══════════════════════════════════════════════════════════════

# Screen
async def _screen_tap(p: dict): return await adb.screen_tap(p.get("x", 0), p.get("y", 0))
async def _screen_swipe(p: dict): return await adb.screen_swipe(p.get("x1", 0), p.get("y1", 0), p.get("x2", 0), p.get("y2", 0), p.get("duration_ms", 300))
async def _screen_type(p: dict): return await adb.screen_type(p.get("text", ""))
async def _screen_key(p: dict): return await adb.screen_key(p.get("keycode", "HOME"))
async def _screen_long_press(p: dict): return await adb.screen_long_press(p.get("x", 0), p.get("y", 0), p.get("duration_ms", 1000))
async def _screen_scroll_down(p: dict): return await adb.screen_scroll_down()
async def _screen_scroll_up(p: dict): return await adb.screen_scroll_up()
async def _screen_unlock(p: dict): return await adb.screen_unlock()
async def _screen_screenshot(p: dict): return await adb.screen_screenshot(encode_base64=p.get("base64", True))

# Apps
async def _app_open(p: dict): return await adb.app_open(p.get("package", ""), p.get("activity"))
async def _app_close(p: dict): return await adb.app_close(p.get("package", ""))
async def _app_current(p: dict): return await adb.app_current()
async def _app_list(p: dict): return await adb.app_list_installed()
async def _app_install(p: dict): return await adb.app_install(p.get("apk_path", ""))
async def _app_uninstall(p: dict): return await adb.app_uninstall(p.get("package", ""))

# SMS
async def _sms_send(p: dict): return await tapi.sms_send(p.get("number", ""), p.get("message", ""))
async def _sms_inbox(p: dict): return await tapi.sms_inbox(p.get("limit", 20), p.get("offset", 0))

# Calls
async def _call_dial(p: dict): return await tapi.call_dial(p.get("number", ""))
async def _call_info(p: dict): return await tapi.call_info()

# Camera & Mic
async def _camera_photo(p: dict): return await tapi.camera_photo(p.get("camera_id", 0), p.get("save_path"))
async def _camera_info(p: dict): return await tapi.camera_info()
async def _mic_record(p: dict): return await tapi.mic_record(p.get("duration", 5), p.get("save_path"))
async def _mic_stop(p: dict): return await tapi.mic_stop()

# Location
async def _location_get(p: dict): return await tapi.location_get(p.get("provider", "gps"))

# Notifications
async def _notif_send(p: dict): return await tapi.notification_send(p.get("title", "Jenna"), p.get("content", ""), p.get("id"), p.get("priority", "default"), p.get("vibrate", False), p.get("sound", False))
async def _notif_list(p: dict): return await tapi.notification_list()
async def _notif_remove(p: dict): return await tapi.notification_remove(p.get("id", ""))

# Clipboard
async def _clipboard_get(p: dict): return await tapi.clipboard_get()
async def _clipboard_set(p: dict): return await tapi.clipboard_set(p.get("text", ""))

# Contacts
async def _contacts_list(p: dict): return await tapi.contacts_list()

# Settings
async def _wifi_on(p: dict): return await adb.wifi_toggle(True)
async def _wifi_off(p: dict): return await adb.wifi_toggle(False)
async def _wifi_info(p: dict): return await tapi.wifi_info()
async def _bt_on(p: dict): return await adb.bluetooth_toggle(True)
async def _bt_off(p: dict): return await adb.bluetooth_toggle(False)
async def _volume_set(p: dict): return await adb.volume_set(p.get("stream", 3), p.get("level", 7))
async def _volume_get(p: dict): return await tapi.volume_get()
async def _brightness_set(p: dict): return await adb.brightness_set(p.get("level", 128))

# Vitals
async def _battery_status(p: dict): return await tapi.battery_status()
async def _device_info(p: dict): return await adb.device_info()

# Filesystem
async def _file_read(p: dict):
    path = Path(p.get("path", ""))
    if not path.exists() or not path.is_file():
        return {"action": "file.read", "success": False, "error": f"File not found: {path}"}
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        max_chars = p.get("max_chars", 10000)
        return {"action": "file.read", "path": str(path), "content": content[:max_chars], "total_chars": len(content), "success": True}
    except Exception as e:
        return {"action": "file.read", "success": False, "error": str(e)}

async def _file_write(p: dict):
    path = Path(p.get("path", ""))
    content = p.get("content", "")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"action": "file.write", "path": str(path), "bytes_written": len(content), "success": True}
    except Exception as e:
        return {"action": "file.write", "success": False, "error": str(e)}

async def _file_delete(p: dict):
    path = Path(p.get("path", ""))
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            return {"action": "file.delete", "success": False, "error": f"Path not found: {path}"}
        return {"action": "file.delete", "path": str(path), "success": True}
    except Exception as e:
        return {"action": "file.delete", "success": False, "error": str(e)}

async def _file_move(p: dict):
    src = p.get("src", p.get("source", ""))
    dst = p.get("dst", p.get("destination", ""))
    try:
        shutil.move(src, dst)
        return {"action": "file.move", "src": src, "dst": dst, "success": True}
    except Exception as e:
        return {"action": "file.move", "success": False, "error": str(e)}

async def _file_list(p: dict):
    path = Path(p.get("path", str(STORAGE_ROOT / "Download")))
    if not path.exists():
        return {"action": "file.list", "success": False, "error": f"Path not found: {path}"}
    try:
        entries = []
        for item in sorted(path.iterdir()):
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
                })
            except Exception:
                entries.append({"name": item.name, "is_dir": item.is_dir(), "size": 0})
        limit = p.get("limit", 100)
        return {"action": "file.list", "path": str(path), "count": len(entries), "items": entries[:limit], "success": True}
    except Exception as e:
        return {"action": "file.list", "success": False, "error": str(e)}

async def _file_exists(p: dict):
    path = Path(p.get("path", ""))
    return {"action": "file.exists", "path": str(path), "exists": path.exists(), "is_file": path.is_file(), "is_dir": path.is_dir(), "success": True}

# Misc Hardware
async def _torch_on(p: dict): return await tapi.torch_toggle(True)
async def _torch_off(p: dict): return await tapi.torch_toggle(False)
async def _vibrate(p: dict): return await tapi.vibrate(p.get("duration_ms", 500))
async def _tts_speak(p: dict): return await tapi.tts_speak(p.get("text", ""), p.get("language", "en"), p.get("rate", 1.0))

# Shell (catch-all)
async def _shell_exec(p: dict):
    import subprocess
    cmd = p.get("command", "")
    cwd = p.get("cwd", str(STORAGE_ROOT if STORAGE_ROOT.exists() else Path.home()))
    timeout = p.get("timeout", 25.0)
    start = time.time()
    try:
        res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {
            "action": "shell",
            "command": cmd,
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "success": res.returncode == 0,
            "duration_ms": round((time.time() - start) * 1000, 1),
        }
    except Exception as e:
        return {"action": "shell", "success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
#  GOD MODE ENGINE — Main Interface
# ══════════════════════════════════════════════════════════════

class GodModeEngine:
    """Central engine for Jenna's full phone control."""

    def __init__(self):
        self.initialized = False
        self.action_count = 0
        self.last_screenshot_time = 0.0

    async def initialize(self) -> bool:
        """Initialize the engine — register actions and verify ADB."""
        if self.initialized:
            return True

        _register_all_actions()

        if CONTROLLERS_AVAILABLE:
            connected = await adb.ensure_connected()
            if connected:
                logger.info(f"God Mode Engine initialized — {len(ACTION_REGISTRY)} actions registered, ADB connected")
                self.initialized = True
                return True
            else:
                logger.warning("God Mode Engine: ADB not connected, some actions unavailable")
                self.initialized = True
                return True  # Still allow Termux:API actions
        else:
            logger.warning("God Mode Engine: Controllers not available")
            return False

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a god mode action by name."""
        if not self.initialized:
            await self.initialize()

        params = params or {}
        start = time.time()

        if action not in ACTION_REGISTRY:
            # Try fuzzy matching
            similar = [a for a in ACTION_REGISTRY if action in a or a in action]
            return {
                "success": False,
                "error": f"Unknown action: '{action}'",
                "available_similar": similar[:5],
                "hint": "Use god_mode.list_actions() to see all available actions",
            }

        entry = ACTION_REGISTRY[action]
        handler = entry["handler"]

        try:
            result = await handler(params)
            self.action_count += 1
            result["_god_mode"] = {
                "action": action,
                "category": entry["category"],
                "total_actions_executed": self.action_count,
                "duration_ms": round((time.time() - start) * 1000, 1),
            }
            return result
        except Exception as e:
            logger.error(f"God Mode action '{action}' failed: {e}")
            return {"success": False, "error": str(e), "action": action}

    async def execute_sequence(self, actions: List[Dict[str, Any]], delay_ms: int = 200) -> List[Dict[str, Any]]:
        """Execute a sequence of actions with optional delay between them.
        Each action: {"action": "screen.tap", "params": {"x": 100, "y": 200}}
        """
        results = []
        for i, act in enumerate(actions):
            action_name = act.get("action", "")
            params = act.get("params", {})
            result = await self.execute(action_name, params)
            results.append({"step": i + 1, **result})

            if not result.get("success", False):
                logger.warning(f"Sequence step {i+1} failed: {action_name}")
                # Continue by default (don't break sequence)

            if delay_ms > 0 and i < len(actions) - 1:
                await asyncio.sleep(delay_ms / 1000.0)

        return results

    def list_actions(self, category: Optional[str] = None) -> Dict[str, Any]:
        """List all registered god mode actions."""
        actions = {}
        for name, entry in ACTION_REGISTRY.items():
            if category and entry["category"] != category:
                continue
            actions[name] = {
                "category": entry["category"],
                "description": entry["description"],
                "risk": entry["risk"],
            }
        categories = sorted(set(e["category"] for e in ACTION_REGISTRY.values()))
        return {
            "total_actions": len(actions),
            "categories": categories,
            "actions": actions,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get God Mode Engine status."""
        return {
            "initialized": self.initialized,
            "controllers_available": CONTROLLERS_AVAILABLE,
            "total_registered_actions": len(ACTION_REGISTRY),
            "total_actions_executed": self.action_count,
            "categories": sorted(set(e["category"] for e in ACTION_REGISTRY.values())) if ACTION_REGISTRY else [],
        }


# Singleton instance
god_mode = GodModeEngine()
