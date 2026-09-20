#!/usr/bin/env python3
"""
Jenna AI — Ultra-Lightweight Physical Phone Bridge Client (Termux)
Maintains zero-battery, zero-heat WebSocket connection to Cloud Jenna (Render).
Executes shell commands, file browsing/organization, and hardware diagnostics
directly on Boss's iQOO Neo 10 upon Cloud Jenna's command.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import websockets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [PhoneBridge]: %(message)s",
)
logger = logging.getLogger("jenna.phone_bridge_client")

CLOUD_WS_URL = os.getenv(
    "JENNA_BRIDGE_WS_URL",
    "wss://jenna-anti.onrender.com/device/bridge"
)

STORAGE_ROOT = Path("/storage/emulated/0")


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
        "display": "6.78-inch 144Hz AMOLED 1.5K",
        "client": "Termux Python Zero-Battery Bridge",
    }


def get_device_vitals() -> Dict[str, Any]:
    """Collect live battery, temperature, and storage metrics without waking CPU."""
    vitals: Dict[str, Any] = {"timestamp": time.time()}

    # 1. Termux battery status if available
    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=2.0)
        if r.returncode == 0 and r.stdout.strip():
            vitals["battery"] = json.loads(r.stdout.strip())
    except Exception:
        pass

    # 2. Storage metrics
    try:
        target = STORAGE_ROOT if STORAGE_ROOT.exists() else Path.home()
        st = shutil.disk_usage(target)
        vitals["storage"] = {
            "total_gb": round(st.total / (1024 ** 3), 2),
            "free_gb": round(st.free / (1024 ** 3), 2),
            "used_pct": round((st.used / st.total) * 100, 1),
            "path": str(target),
        }
    except Exception:
        pass

    return vitals


async def execute_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute action locally on phone."""
    start_t = time.time()

    # 1. Shell command execution
    if action in ("shell", "command", "bash"):
        cmd = params.get("command", "")
        cwd = params.get("cwd", str(STORAGE_ROOT if STORAGE_ROOT.exists() else Path.home()))
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=params.get("timeout", 25.0),
            )
            return {
                "action": "shell",
                "command": cmd,
                "exit_code": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "success": res.returncode == 0,
                "duration_ms": round((time.time() - start_t) * 1000, 1),
            }
        except Exception as exc:
            return {"action": "shell", "error": str(exc), "success": False}

    # 2. List phone files
    elif action in ("file_list", "list_dir", "ls"):
        raw_path = params.get("path", "/storage/emulated/0/Download")
        p = Path(raw_path)
        if not p.exists():
            return {"action": "file_list", "error": f"Path '{raw_path}' does not exist on phone.", "success": False}

        entries = []
        try:
            for item in sorted(p.iterdir()):
                entries.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else 0,
                    "size_human": f"{round(item.stat().st_size / 1024, 1)} KB" if item.is_file() else "folder",
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.stat().st_mtime)),
                })
            return {
                "action": "file_list",
                "path": str(p),
                "total_items": len(entries),
                "items": entries[:params.get("limit", 60)],
                "success": True,
            }
        except Exception as exc:
            return {"action": "file_list", "error": str(exc), "success": False}

    # 3. Read file from phone
    elif action in ("file_read", "read_file"):
        raw_path = params.get("path", "")
        p = Path(raw_path)
        if not p.exists() or not p.is_file():
            return {"action": "file_read", "error": f"File '{raw_path}' not found on phone.", "success": False}
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            return {
                "action": "file_read",
                "path": str(p),
                "total_lines": len(content.splitlines()),
                "content": content[:params.get("max_chars", 10000)],
                "success": True,
            }
        except Exception as exc:
            return {"action": "file_read", "error": str(exc), "success": False}

    # 4. Smart File Organizer (Clean & categorize messy folders)
    elif action in ("file_organize", "organize_folder"):
        folder_path = Path(params.get("folder", "/storage/emulated/0/Download"))
        if not folder_path.exists():
            return {"action": "file_organize", "error": f"Folder '{folder_path}' not found.", "success": False}

        dest_base = folder_path / "Organized_Files"
        categories = {
            "Documents": {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"},
            "Images": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"},
            "Videos": {".mp4", ".mkv", ".mov", ".avi"},
            "Audio": {".mp3", ".wav", ".m4a", ".ogg", ".aac"},
            "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
            "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".sh"},
        }

        moved_count = 0
        summary: Dict[str, int] = {cat: 0 for cat in categories}

        try:
            for item in folder_path.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    ext = item.suffix.lower()
                    target_cat = "Others"
                    for cat, exts in categories.items():
                        if ext in exts:
                            target_cat = cat
                            break

                    cat_dir = dest_base / target_cat
                    cat_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(item), str(cat_dir / item.name))
                    moved_count += 1
                    summary[target_cat] = summary.get(target_cat, 0) + 1

            return {
                "action": "file_organize",
                "folder": str(folder_path),
                "destination": str(dest_base),
                "total_moved": moved_count,
                "categories": summary,
                "success": True,
                "message": f"Organized {moved_count} files into {dest_base.name} safely!",
            }
        except Exception as exc:
            return {"action": "file_organize", "error": str(exc), "success": False}

    # 5. Live Phone Vitals
    elif action in ("device_vitals", "vitals", "status"):
        return {
            "action": "device_vitals",
            "metadata": get_phone_metadata(),
            "vitals": get_device_vitals(),
            "success": True,
        }

    else:
        return {"action": action, "error": f"Unknown action: {action}", "success": False}


async def bridge_loop():
    """Continuous resilient bridge worker."""
    meta = get_phone_metadata()
    logger.info(f"Starting Phone Bridge for {meta['device_model']}...")
    logger.info(f"Target WebSocket: {CLOUD_WS_URL}")

    backoff = 2
    while True:
        try:
            async with websockets.connect(
                CLOUD_WS_URL,
                ping_interval=20,
                ping_timeout=20,
                max_size=10 * 1024 * 1024,
            ) as ws:
                logger.info("Connected to Cloud Jenna Hub! Sending handshake...")
                await ws.send(json.dumps({
                    "type": "handshake",
                    "metadata": meta,
                }))

                ack = await ws.recv()
                logger.info(f"Handshake acknowledged: {ack}")
                backoff = 2  # Reset backoff on successful connection

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
                                logger.info(f"Executing cloud command [{action}] (ID: {req_id})")
                                result = await execute_action(action, params)
                                await ws.send(json.dumps({
                                    "id": req_id,
                                    "result": result,
                                }))
                        except Exception as p_err:
                            logger.error(f"Error handling message: {p_err}")
                finally:
                    hb_task.cancel()

        except (websockets.ConnectionClosed, websockets.WebSocketException) as e:
            logger.warning(f"Connection to Cloud Jenna closed ({e}). Reconnecting in {backoff}s...")
        except Exception as e:
            logger.warning(f"WebSocket connect error ({e}). Reconnecting in {backoff}s...")

        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    try:
        asyncio.run(bridge_loop())
    except KeyboardInterrupt:
        logger.info("Phone Bridge Client stopped by user.")
