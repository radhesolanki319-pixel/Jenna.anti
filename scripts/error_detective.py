#!/usr/bin/env python3
"""CLI: Live Error Detective for Jenna AI.

Usage:
    python3 scripts/error_detective.py              # scan once for errors
    python3 scripts/error_detective.py --watch      # continuous watch every 5s
    python3 scripts/error_detective.py --interval 3 # custom interval in seconds
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

_SEVERITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
}


def _print_result(result: dict) -> None:
    """Pretty-print a single scan result."""
    has_error = result.get("has_error", False)
    severity = result.get("severity", "low")
    emoji = _SEVERITY_EMOJI.get(severity, "⚪")
    ts = result.get("timestamp", "")

    print(f"\n{emoji} Error Detective Scan — {ts}")
    print(f"   Has Error   : {has_error}")
    if has_error:
        print(f"   Type        : {result.get('error_type', 'unknown')}")
        print(f"   Severity    : {severity.upper()}")
        print(f"   Message     : {result.get('error_message', '')}")
        print(f"   Suggested   : {result.get('suggested_fix', '')}")
    else:
        print("   ✅ No errors detected on screen.")
    print()


async def _run_once(args: argparse.Namespace) -> None:
    from app.ai.vision.error_detective_service import error_detective_service

    print("🔍 Scanning screen for errors...")
    result = await error_detective_service.scan_for_errors()
    _print_result(result)

    if args.json:
        print("--- JSON Output ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))


async def _run_watch(interval: float) -> None:
    from app.ai.vision.error_detective_service import error_detective_service

    print(f"👁️  Starting continuous error watch (interval={interval}s).")
    print("   Press Ctrl+C to stop.\n")

    scan_count = 0
    try:
        while True:
            scan_count += 1
            print(f"[Scan #{scan_count}]", end=" ", flush=True)
            result = await error_detective_service.scan_for_errors()
            _print_result(result)
            await asyncio.sleep(interval)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n⛔ Watch stopped after {scan_count} scan(s).")


async def _main(args: argparse.Namespace) -> None:
    if args.watch:
        await _run_watch(interval=args.interval)
    else:
        await _run_once(args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jenna AI — Live Error Detective",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously watch for errors instead of scanning once",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Interval in seconds between scans in watch mode (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also print raw JSON output (one-shot mode only)",
    )
    args = parser.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
