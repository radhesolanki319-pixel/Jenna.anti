#!/usr/bin/env python3
"""Gaze Tracking CLI for Jenna AI.

Usage:
  python3 scripts/gaze_tracking.py
  python3 scripts/gaze_tracking.py --camera
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.ai.vision.gaze_tracking_service import gaze_tracking_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Live User Gaze & Focus Tracking Tool")
    parser.add_argument("--camera", "-c", action="store_true", help="Use front camera snapshot for high precision gaze vector")
    args = parser.parse_args()

    mode_name = "Front Camera Vision" if args.camera else "Low-Power Telemetry Heuristics"
    print(f"👁️ Tracking user gaze via {mode_name}...")

    res = asyncio.run(gaze_tracking_service.get_gaze_state(use_camera=args.camera))
    print(json.dumps(res, indent=2, ensure_ascii=False))

    zone = res.get("gaze_zone", "UNKNOWN")
    desc = res.get("focus_description", "")
    print(f"\n🎯 Estimated Gaze Zone: {zone}")
    print(f"💡 Focus Detail: {desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
