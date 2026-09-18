"""Screen Annotation Service for Jenna AI & Antigravity.

Empowers Jenna to visually annotate, highlight, draw bounding boxes, spotlights,
and arrows on live Android device screens via ADB and SurfaceFlinger touch overlay.
"""

import asyncio
import logging
import math
import os
import re
import subprocess
import time
from typing import Any

from app.ai.vision.live_screen import live_screen_service

logger = logging.getLogger("jenna.vision.annotation")

DEFAULT_WIDTH = 1260
DEFAULT_HEIGHT = 2800


class ScreenAnnotationService:
    """Provides real-time visual annotations, bounding boxes, and spotlights on screen."""

    def __init__(self, serial: str = "localhost:5555") -> None:
        self.serial = os.getenv("ANDROID_SERIAL", serial)
        self._screen_width = DEFAULT_WIDTH
        self._screen_height = DEFAULT_HEIGHT
        self._resolution_cached = False

    def get_display_size(self) -> tuple[int, int]:
        """Query physical screen resolution via ADB wm size."""
        if self._resolution_cached:
            return self._screen_width, self._screen_height

        try:
            out = subprocess.check_output(
                ["adb", "-s", self.serial, "shell", "wm", "size"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            m = re.search(r"(\d+)x(\d+)", out)
            if m:
                self._screen_width = int(m.group(1))
                self._screen_height = int(m.group(2))
                self._resolution_cached = True
        except Exception as exc:
            logger.debug(f"Failed to query display size, using defaults: {exc}")

        return self._screen_width, self._screen_height

    def ensure_pointer_active(self) -> None:
        """Activate touch indicators for visible glowing annotations."""
        try:
            subprocess.run(
                ["adb", "-s", self.serial, "shell", "settings", "put", "system", "show_touches", "1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.5,
            )
        except Exception:
            pass

    def draw_spotlight(self, x: int, y: int, duration_ms: int = 1000) -> None:
        """Draw a glowing spotlight at exact pixel coordinates (x, y)."""
        self.ensure_pointer_active()
        w, h = self.get_display_size()
        cx = max(10, min(w - 10, int(x)))
        cy = max(10, min(h - 10, int(y)))

        try:
            subprocess.run(
                ["adb", "-s", self.serial, "shell", "input", "swipe", str(cx), str(cy), str(cx), str(cy + 2), str(duration_ms)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=(duration_ms / 1000.0) + 2.0,
            )
        except Exception as err:
            logger.warning(f"Spotlight drawing error: {err}")

    def draw_bounding_box(
        self,
        box_norm: list[int],
        label: str = "",
        duration_ms: int = 1500,
    ) -> dict[str, Any]:
        """Draw a visual bounding box on screen given normalized [ymin, xmin, ymax, xmax] (0-1000 scale)."""
        self.ensure_pointer_active()
        w, h = self.get_display_size()

        ymin, xmin, ymax, xmax = box_norm
        x1 = max(10, min(w - 10, int((xmin / 1000.0) * w)))
        y1 = max(10, min(h - 10, int((ymin / 1000.0) * h)))
        x2 = max(10, min(w - 10, int((xmax / 1000.0) * w)))
        y2 = max(10, min(h - 10, int((ymax / 1000.0) * h)))

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # Trace top, right, bottom, left perimeter
        edge_delay = "50"
        try:
            # Top edge: (x1, y1) -> (x2, y1)
            subprocess.run(["adb", "-s", self.serial, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y1), edge_delay], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
            # Right edge: (x2, y1) -> (x2, y2)
            subprocess.run(["adb", "-s", self.serial, "shell", "input", "swipe", str(x2), str(y1), str(x2), str(y2), edge_delay], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
            # Bottom edge: (x2, y2) -> (x1, y2)
            subprocess.run(["adb", "-s", self.serial, "shell", "input", "swipe", str(x2), str(y2), str(x1), str(y2), edge_delay], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
            # Left edge: (x1, y2) -> (x1, y1)
            subprocess.run(["adb", "-s", self.serial, "shell", "input", "swipe", str(x1), str(y2), str(x1), str(y1), edge_delay], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
            # Center spotlight pulse
            self.draw_spotlight(center_x, center_y, duration_ms=duration_ms)
        except Exception as err:
            logger.warning(f"Error drawing perimeter: {err}")

        if label:
            try:
                subprocess.run(["termux-toast", f"🎯 {label}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5)
            except Exception:
                pass

        return {
            "box_norm": [ymin, xmin, ymax, xmax],
            "pixel_coords": {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "center_x": center_x, "center_y": center_y},
            "label": label,
        }

    def draw_circular_highlight(self, x: int, y: int, radius: int = 70, steps: int = 12) -> None:
        """Draw a smooth circular highlight around (x, y)."""
        self.ensure_pointer_active()
        w, h = self.get_display_size()
        cx = max(radius + 10, min(w - radius - 10, int(x)))
        cy = max(radius + 10, min(h - radius - 10, int(y)))

        points = []
        for i in range(steps + 1):
            angle = (2 * math.pi * i) / steps
            px = int(cx + radius * math.cos(angle))
            py = int(cy + radius * math.sin(angle))
            points.append((px, py))

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            try:
                subprocess.run(
                    ["adb", "-s", self.serial, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), "40"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0,
                )
            except Exception:
                break

    async def detect_and_annotate(
        self,
        target_description: str,
        auto_draw: bool = True,
        duration_ms: int = 1500,
    ) -> dict[str, Any]:
        """Locate element on screen via Gemini Vision and physically annotate it."""
        screen_bytes = await live_screen_service.capture_screen_bytes(force_refresh=True)
        if not screen_bytes:
            return {"success": False, "error": "Could not capture device screen."}

        prompt = (
            f"Detect and locate the UI element, button, text, or region described as: '{target_description}'. "
            "Return ONLY a JSON object with format: "
            "{\"box_2d\": [ymin, xmin, ymax, xmax], \"label\": \"brief name\", \"confidence\": 0.95} "
            "where coordinates are normalized integers between 0 and 1000."
        )

        res = await live_screen_service.inspect_live_screen(user_question=prompt)
        desc = res.get("description", "")

        box_match = re.search(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", desc)
        if box_match:
            ymin = int(box_match.group(1))
            xmin = int(box_match.group(2))
            ymax = int(box_match.group(3))
            xmax = int(box_match.group(4))

            annotation = {
                "success": True,
                "target": target_description,
                "box_2d": [ymin, xmin, ymax, xmax],
            }

            if auto_draw:
                draw_info = await asyncio.to_thread(
                    self.draw_bounding_box,
                    [ymin, xmin, ymax, xmax],
                    target_description,
                    duration_ms,
                )
                annotation.update(draw_info)

            return annotation

        # Fallback to screen center
        w, h = self.get_display_size()
        cx, cy = w // 2, h // 2
        if auto_draw:
            await asyncio.to_thread(self.draw_spotlight, cx, cy, duration_ms)

        return {
            "success": False,
            "error": "Exact bounding box could not be extracted. Fallback center spotlight drawn.",
            "pixel_coords": {"center_x": cx, "center_y": cy},
        }


annotation_service = ScreenAnnotationService()
