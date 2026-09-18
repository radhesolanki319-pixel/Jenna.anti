#!/usr/bin/env python3
"""Autonomous Real-Time Live Screen Vision Inspector for Jenna AI & Antigravity.

Usage:
    python3 scripts/inspect_live_screen.py [--prompt "What is on screen?"] [--save /path/to/snap.png] [--json]
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add apps/api to path so imports work cleanly
API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.ai.vision.live_screen import live_screen_service


async def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect live screen using ADB & Gemini Multimodal Vision")
    parser.add_argument("--prompt", "-p", default="", help="Custom query or question about the screen")
    parser.add_argument("--save", "-s", default=None, help="Save snapshot image to path")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.save:
        saved_path = await live_screen_service.save_snapshot(args.save)
        if saved_path:
            print(f"📸 Screen snapshot saved to: {saved_path}")
        else:
            print(f"❌ Failed to save snapshot to: {args.save}")

    result = await live_screen_service.inspect_live_screen(user_question=args.prompt)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("success") else 1

    if not result.get("success"):
        print(f"❌ Screen Vision Error: {result.get('error')}")
        return 1

    meta = result.get("metadata", {})
    focused_pkg = meta.get("focused_package", "Unknown")
    is_floating = meta.get("is_floating_window_active", False)

    print("═══════════════════════════════════════════════════")
    print("👁️  JENNA REAL-TIME LIVE SCREEN VISION")
    print("═══════════════════════════════════════════════════")
    print(f"📱 Active Package : {focused_pkg}")
    print(f"🪟 Small Window   : {'Active (mode=vivofreeform)' if is_floating else 'Standard Fullscreen'}")
    print("───────────────────────────────────────────────────")
    print(f"📝 Visual Analysis:\n{result.get('description', 'No description generated.')}")
    print("───────────────────────────────────────────────────")

    texts = result.get("extracted_text", [])
    if texts:
        print("🔍 Extracted Key Screen Elements:")
        for t in texts[:8]:
            print(f"  • {t}")
    print("═══════════════════════════════════════════════════")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
