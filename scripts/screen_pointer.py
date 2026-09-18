#!/usr/bin/env python3
"""Live On-Screen Visual Pointer & Element Highlighter for Jenna AI.

Draws live glowing pointers, touch indicators, and spotlights directly
on the Android device screen using ADB and Android SurfaceFlinger touch indicator.
Allows Jenna to point at exact buttons, texts, menus, or videos on the user's screen.
"""

import argparse
import asyncio
import json
import logging
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Standard screen resolution for iQOO / Vivo (1260x2800)
SCREEN_WIDTH = 1260
SCREEN_HEIGHT = 2800

SERIAL = os.getenv("ANDROID_SERIAL", "localhost:5555")


def ensure_pointer_indicator() -> None:
    """Ensure Android's native visual touch pointer indicator is active."""
    try:
        subprocess.run(
            ["adb", "-s", SERIAL, "shell", "settings", "put", "system", "show_touches", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
    except Exception:
        pass


def point_at_coordinates(x: int, y: int, duration_ms: int = 1000) -> None:
    """Draw a glowing visual pointer dot at exact (x, y) coordinates."""
    ensure_pointer_indicator()
    x = max(10, min(SCREEN_WIDTH - 10, int(x)))
    y = max(10, min(SCREEN_HEIGHT - 10, int(y)))
    
    # Micro-swipe to keep touch circle glowing on screen for duration
    subprocess.run(
        ["adb", "-s", SERIAL, "shell", "input", "swipe", str(x), str(y), str(x), str(y + 2), str(duration_ms)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=duration_ms / 1000.0 + 2.0,
    )


def circle_around_coordinates(x: int, y: int, radius: int = 60, steps: int = 12) -> None:
    """Draw a smooth visual circular highlight around (x, y)."""
    ensure_pointer_indicator()
    x = max(radius + 10, min(SCREEN_WIDTH - radius - 10, int(x)))
    y = max(radius + 10, min(SCREEN_HEIGHT - radius - 10, int(y)))

    # Compute circular points
    points = []
    for i in range(steps + 1):
        angle = (2 * math.pi * i) / steps
        px = int(x + radius * math.cos(angle))
        py = int(y + radius * math.sin(angle))
        points.append((px, py))

    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        subprocess.run(
            ["adb", "-s", SERIAL, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), "40"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.0,
        )


async def locate_and_point_target(target_description: str) -> dict:
    """Use Gemini Vision to find 2D bounding box of target, then visually point to it on screen."""
    from app.ai.vision.live_screen import live_screen_service

    screen_bytes = await live_screen_service.capture_screen_bytes(force_refresh=True)
    if not screen_bytes:
        return {"success": False, "error": "Could not capture screen frame."}

    prompt = (
        f"Locate the UI element or content described as: '{target_description}'. "
        "Return ONLY a JSON object with the bounding box in format: "
        "{\"box_2d\": [ymin, xmin, ymax, xmax], \"label\": \"name\"} where coordinates are normalized 0-1000."
    )

    result = await live_screen_service.inspect_live_screen(user_question=prompt)
    desc = result.get("description", "")

    # Parse box_2d
    box_match = re.search(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", desc)
    if box_match:
        ymin = int(box_match.group(1))
        xmin = int(box_match.group(2))
        ymax = int(box_match.group(3))
        xmax = int(box_match.group(4))

        center_x = int(((xmin + xmax) / 2) * (SCREEN_WIDTH / 1000.0))
        center_y = int(((ymin + ymax) / 2) * (SCREEN_HEIGHT / 1000.0))

        # Visually point on screen
        point_at_coordinates(center_x, center_y, duration_ms=1200)

        return {
            "success": True,
            "target": target_description,
            "coordinates": {"x": center_x, "y": center_y},
            "box": [ymin, xmin, ymax, xmax],
        }

    # Fallback: Point to center of screen
    point_at_coordinates(630, 1400, duration_ms=800)
    return {
        "success": False,
        "error": "Could not parse exact coordinates. Pointed to screen center as fallback.",
        "coordinates": {"x": 630, "y": 1400},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Live Screen Visual Pointer")
    parser.add_argument("--point", nargs=2, type=int, metavar=("X", "Y"), help="Point at (X, Y) coordinates")
    parser.add_argument("--circle", nargs=2, type=int, metavar=("X", "Y"), help="Draw circle around (X, Y)")
    parser.add_argument("--duration", type=int, default=1000, help="Duration in milliseconds")
    parser.add_argument("--target", "-t", type=str, default="", help="Element name/description to find and point at")
    parser.add_argument("--toast", type=str, default="", help="Optional toast text to show while pointing")
    args = parser.parse_args()

    ensure_pointer_indicator()

    if args.toast:
        subprocess.run(["termux-toast", args.toast], stderr=subprocess.DEVNULL)

    if args.point:
        x, y = args.point
        point_at_coordinates(x, y, duration_ms=args.duration)
        print(f"🎯 Pointed at ({x}, {y}) for {args.duration}ms")
        return 0

    if args.circle:
        x, y = args.circle
        circle_around_coordinates(x, y)
        print(f"⭕ Circled around ({x}, {y})")
        return 0

    if args.target:
        res = asyncio.run(locate_and_point_target(args.target))
        print(json.dumps(res, indent=2))
        return 0 if res.get("success") else 1

    # Default demo: Point at top, middle, and bottom
    point_at_coordinates(630, 700, 500)
    time.sleep(0.1)
    point_at_coordinates(630, 1400, 800)
    print("🎯 Pointed at screen center (630, 1400)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
