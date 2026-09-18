#!/usr/bin/env python3
"""Jenna — App Usage Intelligence CLI.

Usage:
    python3 scripts/usage_intelligence.py              # show today's summary
    python3 scripts/usage_intelligence.py --hours 6   # session history (last 6 h)
    python3 scripts/usage_intelligence.py --start     # start tracking daemon
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — make sure we can import from apps/api/app
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_API_DIR = _REPO_ROOT / "apps" / "api"
sys.path.insert(0, str(_API_DIR))

try:
    from app.ai.usage_intelligence_service import UsageIntelligenceService
except ImportError as _e:
    print(f"[ERROR] Could not import UsageIntelligenceService: {_e}")
    print("Make sure you're running this from the project root and dependencies are installed.")
    sys.exit(1)

# DB path relative to repo root
_DB_PATH = _REPO_ROOT / "data" / "usage_intelligence.db"

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_minutes(minutes: float) -> str:
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def _bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _print_summary(svc: UsageIntelligenceService) -> None:
    data = svc.get_today_summary()
    total_min: float = data["total_screen_time_min"]
    top_apps: list[dict] = data["top_apps"]
    warnings: list[dict] = data["warnings_issued"]
    as_of: str = data["as_of"]

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║        📱  Jenna — Today's App Usage Summary         ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"  As of: {as_of}")
    print(f"  Total screen time: {_fmt_minutes(total_min)}")
    print()

    if not top_apps:
        print("  No app sessions recorded today.")
    else:
        print(f"  {'App':<30} {'Time':>7}  {'%':>5}  Bar")
        print("  " + "─" * 60)
        for app in top_apps:
            label = app["label"][:29]
            mins = _fmt_minutes(app["minutes"])
            pct = app["percentage"]
            bar = _bar(pct)
            print(f"  {label:<30} {mins:>7}  {pct:>4.1f}%  {bar}")

    print()
    if warnings:
        print(f"  ⚠️  Warnings issued today ({len(warnings)}):")
        for w in warnings:
            print(f"    • [{w['threshold']}] {w['package']} @ {w['issued_at']}")
    else:
        print("  ✅ No wellbeing warnings issued today.")
    print()


def _print_history(svc: UsageIntelligenceService, hours: int) -> None:
    sessions = svc.get_session_history(hours=hours)
    print()
    print(f"╔══════════════════════════════════════════════════════╗")
    print(f"║      📅  Session History — Last {hours}h               ║")
    print(f"╚══════════════════════════════════════════════════════╝")
    print()

    if not sessions:
        print("  No sessions found.")
    else:
        for s in sessions:
            dur = f"{s['duration_sec']:.0f}s" if s["duration_sec"] else "ongoing"
            label = s["label"][:25]
            print(f"  {s['start_time']}  {label:<25}  {dur}")
    print()


def _start_daemon(svc: UsageIntelligenceService) -> None:
    print("🔄 Starting app usage tracking daemon…")
    print("   Press Ctrl+C to stop.\n")
    svc.start_tracking()

    def _shutdown(sig, frame):
        print("\n⏹  Stopping tracking…")
        svc.stop_tracking()
        print("✅  Tracking stopped. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("✅  Tracking started! Polling every 60 seconds.")
    print("   Data saved to:", _DB_PATH)
    print()

    while True:
        time.sleep(10)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jenna App Usage Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=None,
        metavar="N",
        help="Show session history for the last N hours",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start the background usage tracking daemon",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output raw JSON instead of pretty tables",
    )
    args = parser.parse_args()

    svc = UsageIntelligenceService(db_path=_DB_PATH)

    if args.start:
        _start_daemon(svc)
    elif args.hours is not None:
        if args.output_json:
            print(json.dumps(svc.get_session_history(hours=args.hours), indent=2))
        else:
            _print_history(svc, args.hours)
    else:
        if args.output_json:
            print(json.dumps(svc.get_today_summary(), indent=2))
        else:
            _print_summary(svc)


if __name__ == "__main__":
    main()
