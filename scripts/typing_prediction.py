#!/usr/bin/env python3
"""Typing Prediction CLI for Jenna AI.

Usage:
  python3 scripts/typing_prediction.py
  python3 scripts/typing_prediction.py --input "git com"
  python3 scripts/typing_prediction.py --copy
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.ai.vision.typing_prediction_service import typing_prediction_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Live Screen Typing Prediction Tool")
    parser.add_argument("--input", "-i", type=str, default="", help="Current partial text typed by user")
    parser.add_argument("--copy", "-c", action="store_true", help="Auto-copy top predicted completion to clipboard")
    args = parser.parse_args()

    print(f"🔮 Analyzing screen context & predicting next input...")
    res = asyncio.run(typing_prediction_service.predict_next_input(current_input=args.input, auto_clipboard=args.copy))
    print(json.dumps(res, indent=2, ensure_ascii=False))

    top = res.get("top_completion", "")
    if top:
        print(f"\n✨ Top Recommendation: {top}")
        if res.get("copied_to_clipboard"):
            print("📋 (Copied to clipboard!)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
