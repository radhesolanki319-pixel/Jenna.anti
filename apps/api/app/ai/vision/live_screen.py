"""Real-Time Live Screen Vision Service for Jenna AI & Antigravity.

Empowers Jenna to see the user's Android device screen live in real-time,
extract UI state, analyze focused windows, inspect errors, and understand user context
via Wireless ADB and Google Gemini Multimodal Vision.
"""

import asyncio
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any

from app.ai.vision.gemini_vision_provider import GeminiVisionProvider
from app.ai.vision.types import VisionAnalysisResult

logger = logging.getLogger("jenna.vision.live_screen")


class LiveScreenVisionService:
    """Provides high-performance live screen capture and AI multimodal understanding."""

    def __init__(self, serial: str = "127.0.0.1:5555") -> None:
        self.serial = os.getenv("ANDROID_SERIAL", serial)
        self.provider = GeminiVisionProvider()
        self._cached_bytes: bytes | None = None
        self._cached_time: float = 0.0
        self._cache_ttl: float = 1.0  # 1 second cache to avoid redundant screencaps

    def _ensure_adb_connected(self) -> bool:
        """Verify ADB connection or auto-detect active device."""
        # 1. Check if current serial is active
        if self.serial:
            try:
                res = subprocess.run(
                    ["adb", "-s", self.serial, "get-state"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=1.5,
                )
                if res.returncode == 0 and "device" in res.stdout:
                    return True
            except Exception:
                pass

        # 2. Auto-detect from adb devices
        try:
            out = subprocess.check_output(["adb", "devices"], text=True, timeout=2.0)
            for line in out.splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    self.serial = parts[0]
                    return True
        except Exception:
            pass

        # 3. Attempt reconnect to localhost
        for host in ["127.0.0.1:5555", "localhost:5555"]:
            try:
                subprocess.run(
                    ["adb", "connect", host],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=2.0,
                )
                self.serial = host
                return True
            except Exception:
                pass

        return False

    async def capture_screen_bytes(self, force_refresh: bool = False) -> bytes | None:
        """Capture live device screen as PNG bytes via ADB exec-out stream."""
        now = time.monotonic()
        if not force_refresh and self._cached_bytes and (now - self._cached_time) < self._cache_ttl:
            return self._cached_bytes

        def _do_capture() -> bytes | None:
            self._ensure_adb_connected()
            try:
                proc = subprocess.run(
                    ["adb", "-s", self.serial, "exec-out", "screencap", "-p"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5.0,
                )
                if proc.returncode == 0 and len(proc.stdout) > 5000:
                    return proc.stdout
                logger.warning(f"screencap failed (code: {proc.returncode}, len: {len(proc.stdout)})")
                return None
            except Exception as e:
                logger.error(f"Error capturing live screen: {e}")
                return None

        data = await asyncio.to_thread(_do_capture)
        if data:
            self._cached_bytes = data
            self._cached_time = now
        return data

    async def get_screen_metadata(self) -> dict[str, Any]:
        """Extract current window manager focus, active package, and floating window state."""
        def _get_meta() -> dict[str, Any]:
            meta: dict[str, Any] = {
                "focused_window": None,
                "focused_package": None,
                "is_floating_window_active": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                out = subprocess.check_output(
                    ["adb", "-s", self.serial, "shell", "dumpsys window"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=3.0,
                )
                for line in out.splitlines():
                    if "mCurrentFocus=" in line or "mFocusedApp=" in line or "mFocusedWindow=" in line:
                        meta["focused_window"] = line.strip()
                        pkg_match = re.search(r"u0\s+([a-zA-Z0-9_.]+)[/}]", line)
                        if pkg_match:
                            meta["focused_package"] = pkg_match.group(1)
                            break
                if "mode=vivofreeform" in out or "vivofreeform" in out or "FreeformMini" in out:
                    meta["is_floating_window_active"] = True
            except Exception as err:
                logger.warning(f"Failed to query window metadata: {err}")
            return meta

        return await asyncio.to_thread(_get_meta)

    async def inspect_live_screen(self, user_question: str = "") -> dict[str, Any]:
        """Capture live screen, pull window context, and run multimodal visual analysis."""
        screen_bytes = await self.capture_screen_bytes(force_refresh=True)
        if not screen_bytes:
            return {
                "success": False,
                "error": "Could not capture device screen. Please verify wireless ADB status.",
                "description": "Phone screen capture unavailable.",
            }

        metadata = await self.get_screen_metadata()
        focused_pkg = metadata.get("focused_package", "Unknown")
        is_floating = metadata.get("is_floating_window_active", False)

        prompt = (
            "You are Jenna's Live Screen Vision. "
            f"Device context: Currently focused package is '{focused_pkg}'. "
            f"Floating Small Window active: {is_floating}.\n"
        )
        if user_question:
            prompt += f"The user asks: '{user_question}'. "
        else:
            prompt += "Describe what is currently visible on the phone screen in detail. "

        prompt += (
            "Analyze: 1) What app or screen is open, 2) Key visible content, videos, texts, or controls, "
            "3) Any floating windows or notifications, 4) Suggestions or next actions for the user."
        )

        res: VisionAnalysisResult = await self.provider.analyze_screen(
            screen_data=screen_bytes,
            mime_type="image/png",
            detect_ui_elements=True,
            prompt=prompt,
        )

        return {
            "success": True,
            "description": res.description,
            "extracted_text": res.extracted_text,
            "confidence": res.confidence,
            "metadata": metadata,
            "timestamp": res.timestamp.isoformat() if res.timestamp else datetime.now(timezone.utc).isoformat(),
        }

    async def save_snapshot(self, target_path: str = "/storage/emulated/0/Download/jenna_live_screen.png") -> str | None:
        """Capture and save the live screen to a file."""
        data = await self.capture_screen_bytes(force_refresh=True)
        if not data:
            return None
        try:
            path = Path(target_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
            return str(path)
        except Exception as e:
            logger.error(f"Error saving snapshot to {target_path}: {e}")
            return None


# Global singleton
live_screen_service = LiveScreenVisionService()
