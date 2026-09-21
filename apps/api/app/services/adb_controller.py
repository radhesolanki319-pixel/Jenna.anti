"""
Jenna AI — ADB Controller (God Mode)
Wraps all ADB shell commands for full phone control:
  • Screen input (tap, swipe, type, keyevent)
  • Screenshot capture
  • App lifecycle management
  • System settings manipulation
  • Device info queries

Designed for non-rooted iQOO Neo 10 (1260x2800), ADB over TCP.
"""

import asyncio
import base64
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("jenna.adb_controller")

# Default ADB device — local wireless ADB
ADB_DEVICE = os.getenv("ADB_DEVICE", "127.0.0.1:5555")
ADB_CMD = f"adb -s {ADB_DEVICE}"

# Screen dimensions for iQOO Neo 10
SCREEN_WIDTH = 1260
SCREEN_HEIGHT = 2800


async def _run_adb(cmd: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Execute an ADB shell command asynchronously."""
    full_cmd = f"{ADB_CMD} {cmd}"
    start = time.time()
    try:
        proc = await asyncio.create_subprocess_shell(
            full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace").strip(),
            "stderr": stderr.decode("utf-8", errors="replace").strip(),
            "exit_code": proc.returncode,
            "duration_ms": round((time.time() - start) * 1000, 1),
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": f"ADB command timed out after {timeout}s", "duration_ms": round((time.time() - start) * 1000, 1)}
    except Exception as e:
        return {"success": False, "error": str(e), "duration_ms": round((time.time() - start) * 1000, 1)}


async def _shell(cmd: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Shortcut for adb shell <cmd>."""
    return await _run_adb(f'shell {cmd}', timeout=timeout)


# ══════════════════════════════════════════════════════════════
#  CONNECTION MANAGEMENT
# ══════════════════════════════════════════════════════════════

async def check_connection() -> Dict[str, Any]:
    """Check if ADB is connected and device is reachable."""
    result = await _run_adb("devices")
    connected = ADB_DEVICE in result.get("stdout", "") and "device" in result.get("stdout", "")
    if not connected:
        # Try reconnect
        reconnect = await _run_adb(f"connect {ADB_DEVICE}", timeout=5.0)
        connected = "connected" in reconnect.get("stdout", "").lower()
    return {"connected": connected, "device": ADB_DEVICE, **result}


async def ensure_connected() -> bool:
    """Ensure ADB connection is active, reconnect if needed."""
    status = await check_connection()
    return status.get("connected", False)


# ══════════════════════════════════════════════════════════════
#  SCREEN CONTROL
# ══════════════════════════════════════════════════════════════

async def screen_tap(x: int, y: int) -> Dict[str, Any]:
    """Tap at specific coordinates."""
    x = max(0, min(x, SCREEN_WIDTH))
    y = max(0, min(y, SCREEN_HEIGHT))
    result = await _shell(f"input tap {x} {y}")
    return {"action": "screen.tap", "x": x, "y": y, **result}


async def screen_swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> Dict[str, Any]:
    """Swipe from (x1,y1) to (x2,y2)."""
    result = await _shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
    return {"action": "screen.swipe", "from": [x1, y1], "to": [x2, y2], "duration_ms": duration_ms, **result}


async def screen_type(text: str) -> Dict[str, Any]:
    """Type text on currently focused input field.
    Handles spaces (ADB input text doesn't support spaces well)."""
    # Replace spaces with %s for ADB
    safe_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
    result = await _shell(f'input text "{safe_text}"')
    return {"action": "screen.type", "text": text, **result}


async def screen_key(keycode: str) -> Dict[str, Any]:
    """Send keyevent. Common keycodes:
    HOME=3, BACK=4, ENTER=66, DEL=67, POWER=26,
    VOLUME_UP=24, VOLUME_DOWN=25, MENU=82,
    TAB=61, ESCAPE=111, CAMERA=27
    """
    # Allow both numeric and named keycodes
    if keycode.isdigit():
        key_str = keycode
    else:
        key_str = f"KEYCODE_{keycode.upper()}" if not keycode.startswith("KEYCODE_") else keycode
    result = await _shell(f"input keyevent {key_str}")
    return {"action": "screen.key", "keycode": key_str, **result}


async def screen_long_press(x: int, y: int, duration_ms: int = 1000) -> Dict[str, Any]:
    """Long press at coordinates (simulated via swipe to same point)."""
    result = await _shell(f"input swipe {x} {y} {x} {y} {duration_ms}")
    return {"action": "screen.long_press", "x": x, "y": y, "duration_ms": duration_ms, **result}


async def screen_scroll_down() -> Dict[str, Any]:
    """Scroll down on screen."""
    mid_x = SCREEN_WIDTH // 2
    return await screen_swipe(mid_x, SCREEN_HEIGHT * 3 // 4, mid_x, SCREEN_HEIGHT // 4, 300)


async def screen_scroll_up() -> Dict[str, Any]:
    """Scroll up on screen."""
    mid_x = SCREEN_WIDTH // 2
    return await screen_swipe(mid_x, SCREEN_HEIGHT // 4, mid_x, SCREEN_HEIGHT * 3 // 4, 300)


async def screen_unlock() -> Dict[str, Any]:
    """Wake screen + unlock (swipe up). No PIN/pattern handling."""
    # Wake screen
    await _shell("input keyevent KEYCODE_WAKEUP")
    await asyncio.sleep(0.3)
    # Swipe up to unlock
    mid_x = SCREEN_WIDTH // 2
    result = await screen_swipe(mid_x, SCREEN_HEIGHT * 3 // 4, mid_x, SCREEN_HEIGHT // 4, 200)
    return {"action": "screen.unlock", **result}


async def screen_screenshot(encode_base64: bool = True) -> Dict[str, Any]:
    """Capture screenshot. Returns base64 PNG if encode_base64=True, else saves to temp path."""
    tmp_path_device = "/data/local/tmp/jenna_screenshot.png"
    tmp_path_local = "/data/data/com.termux/files/home/jenna_screenshot.png"

    # Capture on device
    cap_result = await _shell(f"screencap -p {tmp_path_device}", timeout=5.0)
    if not cap_result.get("success"):
        return {"action": "screen.screenshot", "success": False, "error": cap_result.get("error", cap_result.get("stderr", "screencap failed"))}

    # Pull to local
    pull_result = await _run_adb(f"pull {tmp_path_device} {tmp_path_local}", timeout=5.0)
    if not pull_result.get("success"):
        return {"action": "screen.screenshot", "success": False, "error": "Failed to pull screenshot"}

    if encode_base64:
        try:
            with open(tmp_path_local, "rb") as f:
                img_data = f.read()
            b64 = base64.b64encode(img_data).decode("utf-8")
            return {
                "action": "screen.screenshot",
                "success": True,
                "format": "png",
                "base64": b64,
                "size_bytes": len(img_data),
                "width": SCREEN_WIDTH,
                "height": SCREEN_HEIGHT,
            }
        except Exception as e:
            return {"action": "screen.screenshot", "success": False, "error": str(e)}
    else:
        return {
            "action": "screen.screenshot",
            "success": True,
            "path": tmp_path_local,
            "width": SCREEN_WIDTH,
            "height": SCREEN_HEIGHT,
        }


async def screen_is_on() -> bool:
    """Check if screen is currently on."""
    result = await _shell("dumpsys power | grep 'Display Power'")
    return "ON" in result.get("stdout", "")


# ══════════════════════════════════════════════════════════════
#  APP MANAGEMENT
# ══════════════════════════════════════════════════════════════

async def app_open(package: str, activity: Optional[str] = None) -> Dict[str, Any]:
    """Open an app by package name. If activity not specified, uses monkey launcher."""
    if activity:
        result = await _shell(f"am start -n {package}/{activity}")
    else:
        # Use monkey to launch main activity
        result = await _shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
    return {"action": "app.open", "package": package, **result}


async def app_close(package: str) -> Dict[str, Any]:
    """Force stop an app."""
    result = await _shell(f"am force-stop {package}")
    return {"action": "app.close", "package": package, **result}


async def app_current() -> Dict[str, Any]:
    """Get currently focused app and activity."""
    result = await _shell("dumpsys activity activities | grep mResumedActivity")
    stdout = result.get("stdout", "")
    # Parse: mResumedActivity: ActivityRecord{... com.whatsapp/.Main}
    package = ""
    activity = ""
    if "/" in stdout:
        try:
            parts = stdout.split()
            for p in parts:
                if "/" in p and "." in p:
                    pkg_act = p.rstrip("}")
                    package, activity = pkg_act.split("/", 1)
                    break
        except Exception:
            pass
    return {"action": "app.current", "package": package, "activity": activity, "raw": stdout, **result}


async def app_list_installed() -> Dict[str, Any]:
    """List all installed packages."""
    result = await _shell("pm list packages -3", timeout=15.0)  # -3 = third-party only
    packages = [line.replace("package:", "").strip() for line in result.get("stdout", "").splitlines() if line.startswith("package:")]
    return {"action": "app.list", "count": len(packages), "packages": packages, **result}


async def app_install(apk_path: str) -> Dict[str, Any]:
    """Install an APK."""
    result = await _run_adb(f"install {apk_path}", timeout=60.0)
    return {"action": "app.install", "apk": apk_path, **result}


async def app_uninstall(package: str) -> Dict[str, Any]:
    """Uninstall an app."""
    result = await _shell(f"pm uninstall {package}")
    return {"action": "app.uninstall", "package": package, **result}


# ══════════════════════════════════════════════════════════════
#  SETTINGS CONTROL
# ══════════════════════════════════════════════════════════════

async def wifi_toggle(enable: bool) -> Dict[str, Any]:
    """Enable or disable WiFi."""
    cmd = "svc wifi enable" if enable else "svc wifi disable"
    result = await _shell(cmd)
    return {"action": "wifi.toggle", "enabled": enable, **result}


async def bluetooth_toggle(enable: bool) -> Dict[str, Any]:
    """Enable or disable Bluetooth."""
    cmd = "svc bluetooth enable" if enable else "svc bluetooth disable"
    result = await _shell(cmd)
    return {"action": "bluetooth.toggle", "enabled": enable, **result}


async def volume_set(stream: int, level: int) -> Dict[str, Any]:
    """Set volume level. Streams: 0=voice, 1=system, 2=ring, 3=music, 4=alarm, 5=notification."""
    result = await _shell(f"media volume --stream {stream} --set {level} --show")
    return {"action": "volume.set", "stream": stream, "level": level, **result}


async def brightness_set(level: int) -> Dict[str, Any]:
    """Set screen brightness (0-255)."""
    level = max(0, min(255, level))
    # Disable auto-brightness first
    await _shell("settings put system screen_brightness_mode 0")
    result = await _shell(f"settings put system screen_brightness {level}")
    return {"action": "brightness.set", "level": level, **result}


async def airplane_toggle(enable: bool) -> Dict[str, Any]:
    """Toggle airplane mode."""
    val = "1" if enable else "0"
    result = await _shell(f"settings put global airplane_mode_on {val}")
    # Broadcast intent to apply
    action = "android.intent.action.AIRPLANE_MODE" 
    await _shell(f'am broadcast -a {action} --ez state {str(enable).lower()}')
    return {"action": "airplane.toggle", "enabled": enable, **result}


async def rotation_auto(enable: bool) -> Dict[str, Any]:
    """Toggle auto-rotation."""
    val = "1" if enable else "0"
    result = await _shell(f"settings put system accelerometer_rotation {val}")
    return {"action": "rotation.auto", "enabled": enable, **result}


# ══════════════════════════════════════════════════════════════
#  DEVICE INFO
# ══════════════════════════════════════════════════════════════

async def device_screen_size() -> Tuple[int, int]:
    """Get physical screen size."""
    result = await _shell("wm size")
    # "Physical size: 1260x2800"
    try:
        size_str = result["stdout"].split(":")[-1].strip()
        w, h = size_str.split("x")
        return int(w), int(h)
    except Exception:
        return SCREEN_WIDTH, SCREEN_HEIGHT


async def device_info() -> Dict[str, Any]:
    """Get comprehensive device info."""
    model = await _shell("getprop ro.product.model")
    brand = await _shell("getprop ro.product.brand")
    android = await _shell("getprop ro.build.version.release")
    sdk = await _shell("getprop ro.build.version.sdk")
    uptime = await _shell("uptime")

    return {
        "action": "device.info",
        "model": model.get("stdout", ""),
        "brand": brand.get("stdout", ""),
        "android_version": android.get("stdout", ""),
        "sdk_level": sdk.get("stdout", ""),
        "uptime": uptime.get("stdout", ""),
        "screen": f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}",
        "success": True,
    }


async def device_dumpsys(service: str) -> Dict[str, Any]:
    """Get dumpsys output for a specific service (battery, wifi, bluetooth, etc)."""
    result = await _shell(f"dumpsys {service}", timeout=10.0)
    # Truncate long output
    stdout = result.get("stdout", "")
    if len(stdout) > 5000:
        stdout = stdout[:5000] + "\n... (truncated)"
    return {"action": "device.dumpsys", "service": service, "output": stdout, **result}
