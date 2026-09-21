#!/usr/bin/env python3
"""
Jenna AI — God Mode Phone Bridge Client (Termux)
Full autonomous phone control client running on Boss's iQOO Neo 10.
Executes ALL god mode actions: screen control, apps, SMS, calls, camera,
GPS, notifications, clipboard, contacts, settings, files, hardware.

Connects to Jenna Cloud/Local via WebSocket for remote command execution.
"""

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import websockets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [GodMode]: %(message)s",
)
logger = logging.getLogger("jenna.god_mode_client")

CLOUD_WS_URL = os.getenv(
    "JENNA_BRIDGE_WS_URL",
    "wss://jenna-anti.onrender.com/device/bridge"
)

STORAGE_ROOT = Path("/storage/emulated/0")
HOME_DIR = Path.home()
ADB_DEVICE = os.getenv("ADB_DEVICE", "127.0.0.1:5555")
SCREENSHOT_DIR = HOME_DIR


def get_phone_metadata() -> Dict[str, Any]:
    """Retrieve verified Android properties from Termux getprop."""
    def _gp(prop: str) -> str:
        try:
            r = subprocess.run(["getprop", prop], capture_output=True, text=True, timeout=1.0)
            return r.stdout.strip()
        except Exception:
            return ""

    model = _gp("ro.product.model") or "I2405"
    brand = _gp("ro.product.brand") or "iQOO"
    soc = _gp("ro.soc.model") or "SM8735"
    os_rel = _gp("ro.build.version.release") or "15"

    marketing = "iQOO Neo 10" if model == "I2405" else f"{brand} {model}"
    soc_name = "Qualcomm Snapdragon 8s Gen 4 (SM8735)" if "8735" in soc else (soc or "Qualcomm Snapdragon")

    return {
        "device_model": f"{marketing} ({model})",
        "brand": brand,
        "manufacturer": "vivo / iQOO",
        "soc": soc_name,
        "os": f"Android {os_rel} (Funtouch OS 15)",
        "battery_capacity": "7,000 mAh (Bypass Charging)",
        "display": "6.78-inch 144Hz AMOLED 1.5K (1260x2800)",
        "client": "Jenna God Mode Bridge v2.0",
        "god_mode": True,
        "capabilities": [
            "screen_control", "app_management", "sms", "calls", "camera",
            "microphone", "location", "notifications", "clipboard", "contacts",
            "settings", "filesystem", "torch", "vibrate", "tts", "shell",
        ],
    }


def get_device_vitals() -> Dict[str, Any]:
    """Collect live battery, temperature, and storage metrics."""
    vitals: Dict[str, Any] = {"timestamp": time.time()}

    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3.0)
        if r.returncode == 0 and r.stdout.strip():
            vitals["battery"] = json.loads(r.stdout.strip())
    except Exception:
        pass

    try:
        target = STORAGE_ROOT if STORAGE_ROOT.exists() else HOME_DIR
        st = shutil.disk_usage(target)
        vitals["storage"] = {
            "total_gb": round(st.total / (1024 ** 3), 2),
            "free_gb": round(st.free / (1024 ** 3), 2),
            "used_pct": round((st.used / st.total) * 100, 1),
        }
    except Exception:
        pass

    return vitals


# ══════════════════════════════════════════════════════════════
#  ADB HELPERS (local execution on phone via ADB loopback)
# ══════════════════════════════════════════════════════════════

def _adb(cmd: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Run ADB command synchronously."""
    full_cmd = f"adb -s {ADB_DEVICE} {cmd}"
    start = time.time()
    try:
        r = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            "success": r.returncode == 0,
            "stdout": r.stdout.strip(),
            "stderr": r.stderr.strip(),
            "duration_ms": round((time.time() - start) * 1000, 1),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"ADB timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _adb_shell(cmd: str, timeout: float = 10.0) -> Dict[str, Any]:
    return _adb(f"shell {cmd}", timeout)


def _termux_cmd(cmd: str, timeout: float = 15.0) -> Dict[str, Any]:
    """Run Termux:API command synchronously."""
    start = time.time()
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        parsed = None
        if r.stdout.strip():
            try:
                parsed = json.loads(r.stdout.strip())
            except json.JSONDecodeError:
                pass
        return {
            "success": r.returncode == 0,
            "stdout": r.stdout.strip(),
            "stderr": r.stderr.strip(),
            "parsed": parsed,
            "duration_ms": round((time.time() - start) * 1000, 1),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
#  GOD MODE ACTION EXECUTOR
# ══════════════════════════════════════════════════════════════

async def execute_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute ANY god mode action locally on phone."""
    start_t = time.time()
    result: Dict[str, Any] = {"action": action}

    try:
        # ── Screen Control ──
        if action == "screen.tap":
            result = _adb_shell(f"input tap {params.get('x', 0)} {params.get('y', 0)}")
            result["action"] = "screen.tap"

        elif action == "screen.swipe":
            x1, y1 = params.get("x1", 0), params.get("y1", 0)
            x2, y2 = params.get("x2", 0), params.get("y2", 0)
            dur = params.get("duration_ms", 300)
            result = _adb_shell(f"input swipe {x1} {y1} {x2} {y2} {dur}")
            result["action"] = "screen.swipe"

        elif action == "screen.type":
            text = params.get("text", "")
            safe = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
            result = _adb_shell(f'input text "{safe}"')
            result["action"] = "screen.type"

        elif action == "screen.key":
            kc = params.get("keycode", "HOME")
            if not str(kc).isdigit() and not str(kc).startswith("KEYCODE_"):
                kc = f"KEYCODE_{str(kc).upper()}"
            result = _adb_shell(f"input keyevent {kc}")
            result["action"] = "screen.key"

        elif action == "screen.long_press":
            x, y = params.get("x", 0), params.get("y", 0)
            dur = params.get("duration_ms", 1000)
            result = _adb_shell(f"input swipe {x} {y} {x} {y} {dur}")
            result["action"] = "screen.long_press"

        elif action == "screen.scroll_down":
            result = _adb_shell("input swipe 630 2100 630 700 300")
            result["action"] = "screen.scroll_down"

        elif action == "screen.scroll_up":
            result = _adb_shell("input swipe 630 700 630 2100 300")
            result["action"] = "screen.scroll_up"

        elif action == "screen.unlock":
            _adb_shell("input keyevent KEYCODE_WAKEUP")
            await asyncio.sleep(0.3)
            result = _adb_shell("input swipe 630 2100 630 700 200")
            result["action"] = "screen.unlock"

        elif action == "screen.screenshot":
            tmp_dev = "/data/local/tmp/jenna_ss.png"
            tmp_local = str(HOME_DIR / "jenna_screenshot.png")
            _adb_shell(f"screencap -p {tmp_dev}", timeout=5.0)
            _adb(f"pull {tmp_dev} {tmp_local}", timeout=5.0)

            if params.get("base64", True) and os.path.exists(tmp_local):
                with open(tmp_local, "rb") as f:
                    img = f.read()
                result = {
                    "action": "screen.screenshot",
                    "success": True,
                    "format": "png",
                    "base64": base64.b64encode(img).decode("utf-8"),
                    "size_bytes": len(img),
                    "width": 1260,
                    "height": 2800,
                }
            else:
                result = {"action": "screen.screenshot", "success": os.path.exists(tmp_local), "path": tmp_local}

        elif action == "screen.is_on":
            r = _adb_shell("dumpsys power | grep 'Display Power'")
            result = {"action": "screen.is_on", "is_on": "ON" in r.get("stdout", ""), **r}

        # ── App Management ──
        elif action == "app.open":
            pkg = params.get("package", "")
            act = params.get("activity")
            if act:
                result = _adb_shell(f"am start -n {pkg}/{act}")
            else:
                result = _adb_shell(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
            result["action"] = "app.open"

        elif action == "app.close":
            result = _adb_shell(f"am force-stop {params.get('package', '')}")
            result["action"] = "app.close"

        elif action == "app.current":
            r = _adb_shell("dumpsys activity activities | grep mResumedActivity")
            stdout = r.get("stdout", "")
            pkg, act = "", ""
            if "/" in stdout:
                for p in stdout.split():
                    if "/" in p and "." in p:
                        pkg_act = p.rstrip("}")
                        pkg, act = pkg_act.split("/", 1)
                        break
            result = {"action": "app.current", "package": pkg, "activity": act, **r}

        elif action == "app.list":
            r = _adb_shell("pm list packages -3", timeout=15.0)
            pkgs = [l.replace("package:", "").strip() for l in r.get("stdout", "").splitlines() if l.startswith("package:")]
            result = {"action": "app.list", "count": len(pkgs), "packages": pkgs, **r}

        elif action == "app.install":
            result = _adb(f"install {params.get('apk_path', '')}", timeout=60.0)
            result["action"] = "app.install"

        elif action == "app.uninstall":
            result = _adb_shell(f"pm uninstall {params.get('package', '')}")
            result["action"] = "app.uninstall"

        # ── SMS ──
        elif action == "sms.send":
            num = params.get("number", "")
            msg = params.get("message", "").replace("'", "'\\''")
            result = _termux_cmd(f"termux-sms-send -n '{num}' '{msg}'")
            result["action"] = "sms.send"

        elif action == "sms.inbox":
            limit = params.get("limit", 20)
            result = _termux_cmd(f"termux-sms-list -l {limit}")
            result["action"] = "sms.inbox"

        # ── Calls ──
        elif action == "call.dial":
            result = _termux_cmd(f"termux-telephony-call '{params.get('number', '')}'")
            result["action"] = "call.dial"

        elif action == "call.info":
            result = _termux_cmd("termux-telephony-cellinfo")
            result["action"] = "call.info"

        # ── Camera & Mic ──
        elif action == "camera.photo":
            cam_id = params.get("camera_id", 0)
            save_path = params.get("save_path", str(SCREENSHOT_DIR / f"jenna_photo_{int(time.time())}.jpg"))
            result = _termux_cmd(f"termux-camera-photo -c {cam_id} '{save_path}'", timeout=10.0)
            result["action"] = "camera.photo"
            result["path"] = save_path

        elif action == "camera.info":
            result = _termux_cmd("termux-camera-info")
            result["action"] = "camera.info"

        elif action == "mic.record":
            dur = params.get("duration", 5)
            save_path = params.get("save_path", str(SCREENSHOT_DIR / f"jenna_audio_{int(time.time())}.m4a"))
            result = _termux_cmd(f"termux-microphone-record -l {dur} -f '{save_path}'", timeout=dur + 5)
            result["action"] = "mic.record"
            result["path"] = save_path

        elif action == "mic.stop":
            result = _termux_cmd("termux-microphone-record -q")
            result["action"] = "mic.stop"

        # ── Location ──
        elif action == "location.get":
            provider = params.get("provider", "gps")
            result = _termux_cmd(f"termux-location -p {provider}", timeout=30.0)
            loc = result.get("parsed", {}) or {}
            result["action"] = "location.get"
            result["latitude"] = loc.get("latitude")
            result["longitude"] = loc.get("longitude")
            result["accuracy"] = loc.get("accuracy")

        # ── Notifications ──
        elif action == "notif.send":
            title = params.get("title", "Jenna").replace("'", "'\\''")
            content = params.get("content", "").replace("'", "'\\''")
            cmd = f"termux-notification -t '{title}' -c '{content}'"
            nid = params.get("id")
            if nid:
                cmd += f" --id '{nid}'"
            result = _termux_cmd(cmd)
            result["action"] = "notif.send"

        elif action == "notif.list":
            result = _termux_cmd("termux-notification-list")
            result["action"] = "notif.list"

        elif action == "notif.remove":
            result = _termux_cmd(f"termux-notification-remove '{params.get('id', '')}'")
            result["action"] = "notif.remove"

        # ── Clipboard ──
        elif action == "clipboard.get":
            result = _termux_cmd("termux-clipboard-get")
            result["action"] = "clipboard.get"
            result["content"] = result.get("stdout", "")

        elif action == "clipboard.set":
            text = params.get("text", "").replace("'", "'\\''")
            result = _termux_cmd(f"termux-clipboard-set '{text}'")
            result["action"] = "clipboard.set"

        # ── Contacts ──
        elif action == "contacts.list":
            result = _termux_cmd("termux-contact-list", timeout=20.0)
            result["action"] = "contacts.list"

        # ── Settings ──
        elif action in ("wifi.on", "wifi.off"):
            enable = action == "wifi.on"
            result = _adb_shell(f"svc wifi {'enable' if enable else 'disable'}")
            result["action"] = action

        elif action == "wifi.info":
            result = _termux_cmd("termux-wifi-connectioninfo")
            result["action"] = "wifi.info"

        elif action in ("bluetooth.on", "bluetooth.off"):
            enable = action == "bluetooth.on"
            result = _adb_shell(f"svc bluetooth {'enable' if enable else 'disable'}")
            result["action"] = action

        elif action == "volume.set":
            stream = params.get("stream", 3)
            level = params.get("level", 7)
            result = _adb_shell(f"media volume --stream {stream} --set {level} --show")
            result["action"] = "volume.set"

        elif action == "volume.get":
            result = _termux_cmd("termux-volume")
            result["action"] = "volume.get"

        elif action == "brightness.set":
            level = max(0, min(255, params.get("level", 128)))
            _adb_shell("settings put system screen_brightness_mode 0")
            result = _adb_shell(f"settings put system screen_brightness {level}")
            result["action"] = "brightness.set"

        # ── Device Vitals ──
        elif action == "battery.status":
            result = _termux_cmd("termux-battery-status")
            result["action"] = "battery.status"

        elif action == "device.info":
            model = _adb_shell("getprop ro.product.model").get("stdout", "")
            brand = _adb_shell("getprop ro.product.brand").get("stdout", "")
            android_ver = _adb_shell("getprop ro.build.version.release").get("stdout", "")
            uptime = _adb_shell("uptime").get("stdout", "")
            result = {
                "action": "device.info", "model": model, "brand": brand,
                "android": android_ver, "uptime": uptime, "success": True,
            }

        elif action in ("device_vitals", "vitals", "status"):
            result = {
                "action": "device_vitals",
                "metadata": get_phone_metadata(),
                "vitals": get_device_vitals(),
                "success": True,
            }

        # ── Filesystem ──
        elif action in ("file.read", "file_read", "read_file"):
            raw_path = params.get("path", "")
            p = Path(raw_path)
            if not p.exists() or not p.is_file():
                result = {"action": "file.read", "error": f"File not found: {raw_path}", "success": False}
            else:
                content = p.read_text(encoding="utf-8", errors="replace")
                max_c = params.get("max_chars", 10000)
                result = {"action": "file.read", "path": str(p), "content": content[:max_c], "total_chars": len(content), "success": True}

        elif action in ("file.write", "file_write"):
            p = Path(params.get("path", ""))
            content = params.get("content", "")
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                result = {"action": "file.write", "path": str(p), "bytes_written": len(content), "success": True}
            except Exception as e:
                result = {"action": "file.write", "error": str(e), "success": False}

        elif action in ("file.delete", "file_delete"):
            p = Path(params.get("path", ""))
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
                result = {"action": "file.delete", "path": str(p), "success": True}
            except Exception as e:
                result = {"action": "file.delete", "error": str(e), "success": False}

        elif action in ("file.move", "file_move"):
            src = params.get("src", params.get("source", ""))
            dst = params.get("dst", params.get("destination", ""))
            try:
                shutil.move(src, dst)
                result = {"action": "file.move", "src": src, "dst": dst, "success": True}
            except Exception as e:
                result = {"action": "file.move", "error": str(e), "success": False}

        elif action in ("file.list", "file_list", "list_dir", "ls"):
            raw_path = params.get("path", "/storage/emulated/0/Download")
            p = Path(raw_path)
            if not p.exists():
                result = {"action": "file.list", "error": f"Path not found: {raw_path}", "success": False}
            else:
                entries = []
                for item in sorted(p.iterdir()):
                    try:
                        st = item.stat()
                        entries.append({"name": item.name, "is_dir": item.is_dir(), "size": st.st_size if item.is_file() else 0,
                                        "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))})
                    except:
                        entries.append({"name": item.name, "is_dir": item.is_dir()})
                limit = params.get("limit", 60)
                result = {"action": "file.list", "path": str(p), "count": len(entries), "items": entries[:limit], "success": True}

        elif action == "file.exists":
            p = Path(params.get("path", ""))
            result = {"action": "file.exists", "path": str(p), "exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir(), "success": True}

        elif action in ("file_organize", "organize_folder"):
            folder = Path(params.get("folder", "/storage/emulated/0/Download"))
            if not folder.exists():
                result = {"action": "file_organize", "error": f"Folder not found: {folder}", "success": False}
            else:
                dest = folder / "Organized_Files"
                cats = {
                    "Documents": {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"},
                    "Images": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"},
                    "Videos": {".mp4", ".mkv", ".mov", ".avi"},
                    "Audio": {".mp3", ".wav", ".m4a", ".ogg", ".aac"},
                    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
                    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".sh"},
                }
                moved = 0
                for item in folder.iterdir():
                    if item.is_file() and not item.name.startswith("."):
                        ext = item.suffix.lower()
                        tcat = "Others"
                        for c, exts in cats.items():
                            if ext in exts:
                                tcat = c
                                break
                        cat_dir = dest / tcat
                        cat_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(item), str(cat_dir / item.name))
                        moved += 1
                result = {"action": "file_organize", "total_moved": moved, "success": True}

        # ── Misc Hardware ──
        elif action in ("torch.on", "torch.off"):
            state = "on" if action == "torch.on" else "off"
            result = _termux_cmd(f"termux-torch {state}")
            result["action"] = action

        elif action == "vibrate":
            dur = params.get("duration_ms", 500)
            result = _termux_cmd(f"termux-vibrate -d {dur} -f")
            result["action"] = "vibrate"

        elif action == "tts.speak":
            text = params.get("text", "").replace("'", "'\\''")
            lang = params.get("language", "en")
            rate = params.get("rate", 1.0)
            result = _termux_cmd(f"termux-tts-speak -l '{lang}' -r {rate} '{text}'", timeout=30.0)
            result["action"] = "tts.speak"

        # ── Shell (catch-all, backwards compatible) ──
        elif action in ("shell", "command", "bash"):
            cmd = params.get("command", "")
            cwd = params.get("cwd", str(STORAGE_ROOT if STORAGE_ROOT.exists() else HOME_DIR))
            try:
                res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=params.get("timeout", 25.0))
                result = {"action": "shell", "command": cmd, "exit_code": res.returncode,
                          "stdout": res.stdout.strip(), "stderr": res.stderr.strip(),
                          "success": res.returncode == 0}
            except Exception as e:
                result = {"action": "shell", "error": str(e), "success": False}

        else:
            result = {"action": action, "error": f"Unknown action: {action}", "success": False}

    except Exception as exc:
        result = {"action": action, "error": str(exc), "success": False}

    result["duration_ms"] = round((time.time() - start_t) * 1000, 1)
    return result


# ══════════════════════════════════════════════════════════════
#  WEBSOCKET BRIDGE LOOP
# ══════════════════════════════════════════════════════════════

async def bridge_loop():
    """Continuous resilient God Mode bridge worker."""
    meta = get_phone_metadata()
    logger.info(f"🔥 Starting God Mode Bridge for {meta['device_model']}...")
    logger.info(f"📡 Target WebSocket: {CLOUD_WS_URL}")
    logger.info(f"⚡ {len(meta['capabilities'])} capability categories loaded")

    backoff = 2
    while True:
        try:
            async with websockets.connect(
                CLOUD_WS_URL,
                ping_interval=20,
                ping_timeout=20,
                max_size=50 * 1024 * 1024,  # 50MB for screenshots
            ) as ws:
                logger.info("✅ Connected to Jenna Hub! Sending God Mode handshake...")
                await ws.send(json.dumps({
                    "type": "handshake",
                    "metadata": meta,
                }))

                ack = await ws.recv()
                logger.info(f"🤝 Handshake acknowledged: {ack}")
                backoff = 2

                # Heartbeat background task
                async def heartbeat_sender():
                    while True:
                        await asyncio.sleep(25)
                        try:
                            vt = get_device_vitals()
                            await ws.send(json.dumps({"type": "heartbeat", "vitals": vt}))
                        except Exception:
                            break

                hb_task = asyncio.create_task(heartbeat_sender())

                # Message receiving loop
                try:
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                            req_id = msg.get("id")
                            action = msg.get("action", "")
                            params = msg.get("params", {})

                            if req_id and action:
                                logger.info(f"⚡ Executing [{action}] (ID: {req_id})")
                                result = await execute_action(action, params)
                                await ws.send(json.dumps({
                                    "id": req_id,
                                    "result": result,
                                }))
                                logger.info(f"✅ [{action}] done in {result.get('duration_ms', '?')}ms")
                        except Exception as p_err:
                            logger.error(f"❌ Error handling message: {p_err}")
                finally:
                    hb_task.cancel()

        except (websockets.ConnectionClosed, websockets.WebSocketException) as e:
            logger.warning(f"🔌 Connection closed ({e}). Reconnecting in {backoff}s...")
        except Exception as e:
            logger.warning(f"⚠️ WebSocket error ({e}). Reconnecting in {backoff}s...")

        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    try:
        asyncio.run(bridge_loop())
    except KeyboardInterrupt:
        logger.info("God Mode Bridge stopped by user.")
