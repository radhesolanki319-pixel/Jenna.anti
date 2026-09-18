#!/usr/bin/env python3
"""CLI: Smart Notification Reader for Jenna AI.

Usage:
    python3 scripts/notification_reader.py           # read and speak new notifications
    python3 scripts/notification_reader.py --list    # list all, don't speak
    python3 scripts/notification_reader.py --reply   # draft replies too
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Allow running from project root
_ROOT = Path(__file__).resolve().parent.parent
_API_SRC = _ROOT / "apps" / "api"
if str(_API_SRC) not in sys.path:
    sys.path.insert(0, str(_API_SRC))


async def _main(args: argparse.Namespace) -> None:
    from app.ai.notification_reader_service import notification_reader_service

    if args.list:
        notifications = await notification_reader_service.list_all_notifications()
        print(f"\n📋 All active important notifications ({len(notifications)} found):\n")
        if not notifications:
            print("  (none)")
        for i, n in enumerate(notifications, 1):
            tag = " [NEW]" if n.get("is_new") else ""
            print(f"  {i}. [{n['app']}]{tag} {n['title']}: {n['text']}")
        print()
        return

    # Default: read new notifications (and speak unless --no-speak)
    speak = not getattr(args, "no_speak", False)
    print(f"\n🔔 Reading new notifications (speak={speak})...\n")
    notifications = await notification_reader_service.read_new_notifications(
        speak=speak
    )

    if not notifications:
        print("  No important notifications found.")
    else:
        print(f"  Found {len(notifications)} important notification(s):\n")

    for i, n in enumerate(notifications, 1):
        tag = " ✦" if n.get("is_new") else " (seen)"
        print(f"  {i}. [{n['app']}]{tag}")
        print(f"     From   : {n['title']}")
        print(f"     Message: {n['text']}")
        print(f"     Spoken : {n['spoken_text']}")

        if args.reply and n.get("is_new"):
            print("     Drafting reply...", end="", flush=True)
            draft = await notification_reader_service.draft_reply(n)
            n["reply_draft"] = draft
            print(f"\r     Reply  : {draft or '(no suggestion)'}")

        print()

    if args.json:
        print("\n--- JSON Output ---")
        print(json.dumps(notifications, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jenna AI — Smart Notification Reader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all important notifications without speaking",
    )
    parser.add_argument(
        "--reply",
        action="store_true",
        help="Draft Gemini reply suggestions for new notifications",
    )
    parser.add_argument(
        "--no-speak",
        action="store_true",
        dest="no_speak",
        help="Suppress TTS (useful for testing)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also print raw JSON output at the end",
    )
    args = parser.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
