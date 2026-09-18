#!/usr/bin/env python3
"""Silence Intelligence Verification & Testing CLI for Jenna AI Voice.

Usage:
  python3 scripts/test_silence_intelligence.py --text "Jenna suno mujhe ek cheez batani thi aur..." --silence 1000
  python3 scripts/test_silence_intelligence.py --text "Jenna YouTube open karo?" --silence 700
"""

import argparse
import json
from pathlib import Path
import sys

API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.ai.voice.silence_intelligence import silence_intelligence_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Silence Intelligence & Turn-Taking Analyzer")
    parser.add_argument("--text", "-t", type=str, default="Jenna suno mujhe ek cheez batani thi aur...", help="Spoken utterance text")
    parser.add_argument("--silence", "-s", type=float, default=800.0, help="Silence elapsed in milliseconds")
    args = parser.parse_args()

    print(f"🎙️ Analyzing Silence Intelligence for utterance: '{args.text}' (Silence: {args.silence}ms)")
    res = silence_intelligence_service.analyze_silence(args.text, silence_duration_ms=args.silence)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    dec = res["decision"]
    if dec == "HOLD_TURN":
        print(f"\n✋ HOLD TURN: AI remains silent while user is thinking! (Wait {res['remaining_wait_ms']:.0f}ms)")
    elif dec == "SPEAK_NOW":
        print(f"\n🗣️ SPEAK NOW: User finished speaking! Jenna responds instantly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
