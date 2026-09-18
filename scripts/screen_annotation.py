#!/usr/bin/env python3
"""Screen Annotation CLI Tool for Jenna AI.

Usage:
  python3 scripts/screen_annotation.py --target "search bar"
  python3 scripts/screen_annotation.py --box 100 200 400 800 --label "Login Button"
  python3 scripts/screen_annotation.py --spotlight 630 1400
  python3 scripts/screen_annotation.py --circle 630 1400 --radius 90
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.ai.vision.annotation_service import annotation_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Live Screen Visual Annotation & Bounding Box Tool")
    parser.add_argument("--target", "-t", type=str, help="Name or description of element to find and annotate")
    parser.add_argument("--box", nargs=4, type=int, metavar=("YMIN", "XMIN", "YMAX", "XMAX"), help="Normalized 0-1000 box coordinates")
    parser.add_argument("--label", "-l", type=str, default="", help="Label text to display via toast")
    parser.add_argument("--spotlight", nargs=2, type=int, metavar=("X", "Y"), help="Pulse a spotlight at (X, Y)")
    parser.add_argument("--circle", nargs=2, type=int, metavar=("X", "Y"), help="Draw circular highlight at (X, Y)")
    parser.add_argument("--radius", type=int, default=70, help="Circle radius in pixels")
    parser.add_argument("--duration", type=int, default=1200, help="Duration in milliseconds")
    args = parser.parse_args()

    if args.spotlight:
        x, y = args.spotlight
        annotation_service.draw_spotlight(x, y, duration_ms=args.duration)
        print(f"🎯 Spotlight drawn at ({x}, {y})")
        return 0

    if args.circle:
        x, y = args.circle
        annotation_service.draw_circular_highlight(x, y, radius=args.radius)
        print(f"⭕ Circle drawn around ({x}, {y}) with radius {args.radius}")
        return 0

    if args.box:
        box = args.box
        res = annotation_service.draw_bounding_box(box, label=args.label, duration_ms=args.duration)
        print(json.dumps(res, indent=2))
        return 0

    if args.target:
        print(f"🔍 Detecting and annotating '{args.target}' on screen...")
        res = asyncio.run(annotation_service.detect_and_annotate(args.target, auto_draw=True, duration_ms=args.duration))
        print(json.dumps(res, indent=2))
        return 0 if res.get("success") else 1

    # Demo: highlight center
    w, h = annotation_service.get_display_size()
    cx, cy = w // 2, h // 2
    annotation_service.draw_spotlight(cx, cy, duration_ms=1000)
    print(f"🎯 Display size {w}x{h}. Demo spotlight pulsed at screen center ({cx}, {cy}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
