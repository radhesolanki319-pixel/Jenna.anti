"""Gaze Tracking & Visual Attention Service for Jenna AI.

Estimates where the user is looking on the Android screen using a dual-engine architecture:
1. Front-Camera Gaze Estimation (via termux-camera-photo and multimodal face/eye analysis).
2. Ultra-Fast Low-Power Heuristic Attention Estimation (via input/window/keyboard telemetry).
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
from app.ai.vision.live_screen import live_screen_service

logger = logging.getLogger("jenna.vision.gaze_tracking")


class GazeZone:
    TOP_STATUS_BAR = "TOP_STATUS_BAR"
    HEADER_NAV = "HEADER_NAV"
    CONTENT_MAIN = "CONTENT_MAIN"
    FLOATING_WINDOW = "FLOATING_WINDOW"
    BOTTOM_KEYBOARD = "BOTTOM_KEYBOARD"
    OFF_SCREEN = "OFF_SCREEN"


class GazeTrackingService:
    """Provides real-time user gaze and attention focus estimation on mobile screens."""

    def __init__(self, serial: str = "localhost:5555") -> None:
        self.serial = os.getenv("ANDROID_SERIAL", serial)
        self.provider = GeminiVisionProvider()

    def estimate_gaze_heuristic(self) -> dict[str, Any]:
        """Estimate user focus zone instantaneously (<20ms) without camera battery drain."""
        meta = asyncio.run(live_screen_service.get_screen_metadata()) if not asyncio.get_event_loop().is_running() else {}
        focused_pkg = meta.get("focused_package", "com.termux")
        is_floating = meta.get("is_floating_window_active", False)

        # Check if keyboard is shown
        keyboard_shown = False
        try:
            out = subprocess.check_output(
                ["adb", "-s", self.serial, "shell", "dumpsys input_method"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1.0,
            )
            keyboard_shown = "mInputShown=true" in out or "mIsInputViewShown=true" in out
        except Exception:
            pass

        now_iso = datetime.now(timezone.utc).isoformat()

        if keyboard_shown:
            return {
                "gaze_zone": GazeZone.BOTTOM_KEYBOARD,
                "confidence": 0.92,
                "focus_description": "User is focused on the virtual keyboard & input box at the bottom of the screen.",
                "normalized_box": [650, 50, 980, 950],
                "source": "heuristic_telemetry",
                "focused_package": focused_pkg,
                "timestamp": now_iso,
            }

        if is_floating:
            return {
                "gaze_zone": GazeZone.FLOATING_WINDOW,
                "confidence": 0.85,
                "focus_description": "User is focused on the active floating small window / multi-window display.",
                "normalized_box": [150, 450, 550, 980],
                "source": "heuristic_telemetry",
                "focused_package": focused_pkg,
                "timestamp": now_iso,
            }

        # Default reading content
        return {
            "gaze_zone": GazeZone.CONTENT_MAIN,
            "confidence": 0.78,
            "focus_description": f"User is reading primary content in {focused_pkg}.",
            "normalized_box": [100, 50, 750, 950],
            "source": "heuristic_telemetry",
            "focused_package": focused_pkg,
            "timestamp": now_iso,
        }

    async def estimate_gaze_from_front_camera(self) -> dict[str, Any]:
        """Take a quick front-camera snapshot to determine face orientation and eye gaze direction."""
        photo_path = Path("/data/data/com.termux/files/home/.gemini/tmp_gaze_face.jpg")
        photo_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Capture using Termux front camera (-c 1)
            proc = await asyncio.to_thread(
                subprocess.run,
                ["termux-camera-photo", "-c", "1", str(photo_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=4.0,
            )

            if proc.returncode != 0 or not photo_path.exists() or photo_path.stat().st_size < 1000:
                logger.warning("Front camera photo failed or empty; using heuristic fallback.")
                return self.estimate_gaze_heuristic()

            # Read photo bytes
            with open(photo_path, "rb") as f:
                face_bytes = f.read()

            # Immediately delete for privacy
            try:
                photo_path.unlink()
            except Exception:
                pass

            prompt = (
                "You are Jenna's Gaze Tracking Vision Engine. "
                "Analyze this front camera selfie of the user holding their smartphone. "
                "Determine the user's eye gaze and face orientation relative to the screen. "
                "Are they looking at: "
                "1. TOP_STATUS_BAR (looking slightly up) "
                "2. HEADER_NAV (looking at top bar) "
                "3. CONTENT_MAIN (looking straight at center display) "
                "4. BOTTOM_KEYBOARD (looking downward towards keyboard/typing area) "
                "5. OFF_SCREEN (looking away from phone) "
                "Return a JSON object with schema:\n"
                "{\n"
                "  \"gaze_zone\": \"TOP_STATUS_BAR | HEADER_NAV | CONTENT_MAIN | BOTTOM_KEYBOARD | OFF_SCREEN\",\n"
                "  \"confidence\": 0.90,\n"
                "  \"focus_description\": \"Detailed description of where user's eyes are looking\",\n"
                "  \"head_pitch\": \"level | tilted_down | tilted_up\",\n"
                "  \"eyes_open\": true\n"
                "}"
            )

            res = await self.provider.analyze_screen(
                screen_data=face_bytes,
                mime_type="image/jpeg",
                detect_ui_elements=False,
                prompt=prompt,
            )

            desc = res.description or ""
            m = re.search(r"\{[\s\S]*\}", desc)
            if m:
                import json
                data = json.loads(m.group(0))
                data["source"] = "front_camera_vision"
                data["timestamp"] = datetime.now(timezone.utc).isoformat()
                return data

            return self.estimate_gaze_heuristic()

        except Exception as e:
            logger.error(f"Gaze front camera error: {e}")
            if photo_path.exists():
                try:
                    photo_path.unlink()
                except Exception:
                    pass
            return self.estimate_gaze_heuristic()

    async def get_gaze_state(self, use_camera: bool = False) -> dict[str, Any]:
        """Unified gaze tracking entrypoint."""
        if use_camera:
            return await self.estimate_gaze_from_front_camera()
        return self.estimate_gaze_heuristic()


gaze_tracking_service = GazeTrackingService()
