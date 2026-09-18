#!/usr/bin/env python3
"""Dexter Autonomous Screen Actions & Input Controller.

Enables Dexter and Jenna to autonomously:
- Type text into focused fields on Android screen (`input text`)
- Search and hit enter in YouTube / Chrome / Apps (`keyevent 66`)
- Scroll and swipe reels / feeds (`input swipe`)
- Tap anywhere on screen (`input tap`)
- Control hardware navigation keys (Back, Home, Enter, Search)
"""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import urllib.parse

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = WORKSPACE_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
BUBBLE_FILE = LOGS_DIR / "dexter_bubble.txt"

_CACHED_SERIAL: str | None = None

def get_adb_serial() -> str | None:
    """Auto-detect and cache active ADB device serial."""
    global _CACHED_SERIAL
    if _CACHED_SERIAL:
        return _CACHED_SERIAL
    env_serial = os.getenv("ANDROID_SERIAL")
    if env_serial:
        _CACHED_SERIAL = env_serial
        return _CACHED_SERIAL
    try:
        out = subprocess.check_output(["adb", "devices"], text=True, timeout=1.5)
        for line in out.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                _CACHED_SERIAL = parts[0]
                return _CACHED_SERIAL
    except Exception:
        pass
    _CACHED_SERIAL = "emulator-5554"
    return _CACHED_SERIAL


def run_adb(cmd_args: list[str], timeout: float = 2.0) -> bool:
    """Execute ADB shell command on active device with minimum latency."""
    serial = get_adb_serial()
    base = ["adb"]
    if serial:
        base += ["-s", serial]
    base += ["shell"] + cmd_args
    try:
        res = subprocess.run(base, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return res.returncode == 0
    except Exception as exc:
        print(f"ADB Error: {exc}", file=sys.stderr)
        return False


def update_bubble(text: str, speak: bool = False) -> None:
    """Notify Dexter floating pet bubble with zero delay."""
    try:
        BUBBLE_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass
    if speak:
        try:
            subprocess.Popen(["termux-tts-speak", text], stderr=subprocess.DEVNULL)
        except Exception:
            pass


def type_text(text: str, hit_enter: bool = False) -> bool:
    """Autonomously type text into active focused screen input."""
    if not text:
        return False

    update_bubble(f"Typing: {text[:25]}... ⌨️", speak=False)

    # ADB input text treats %s as space, and certain chars need escaping
    # Replace space with %s
    safe_chars = []
    for ch in text:
        if ch == " ":
            safe_chars.append("%s")
        elif ch in "&<>|;()$`'\"\\":
            safe_chars.append(f"\\{ch}")
        else:
            safe_chars.append(ch)
    
    encoded = "".join(safe_chars)
    success = run_adb(["input", "text", encoded])

    if hit_enter and success:
        time.sleep(0.05)
        run_adb(["input", "keyevent", "66"])
        update_bubble("Done! 🔍", speak=False)

    return success


def press_key(key_name: str) -> bool:
    """Send Android keyevent."""
    KEY_MAP = {
        "enter": "66",
        "search": "84",
        "back": "4",
        "home": "3",
        "tab": "61",
        "space": "62",
        "delete": "67",
        "backspace": "67",
        "volume_up": "24",
        "volume_down": "25",
    }
    code = KEY_MAP.get(key_name.lower().strip(), key_name)
    update_bubble(f"Key: {key_name} ⌨️", speak=False)
    return run_adb(["input", "keyevent", code])


def tap(x: int, y: int) -> bool:
    """Tap at screen coordinates."""
    update_bubble(f"Tapping ({x}, {y}) 👆", speak=False)
    return run_adb(["input", "tap", str(x), str(y)])


def swipe(direction: str = "up") -> bool:
    """Swipe screen (for reels, feeds, scrolling)."""
    # 1260x2800 display coordinates
    d = direction.lower().strip()
    if d == "up" or d == "next":
        update_bubble("Next reel! 📱", speak=False)
        return run_adb(["input", "swipe", "630", "2000", "630", "600", "250"])
    elif d == "down" or d == "prev":
        update_bubble("Previous! 📱", speak=False)
        return run_adb(["input", "swipe", "630", "600", "630", "2000", "250"])
    elif d == "left":
        return run_adb(["input", "swipe", "1000", "1400", "200", "1400", "250"])
    elif d == "right":
        return run_adb(["input", "swipe", "200", "1400", "1000", "1400", "250"])
    return False


def search_youtube(query: str) -> bool:
    """Autonomously search on YouTube and hit search."""
    update_bubble(f"Searching: {query} 🔍", speak=True)
    
    # Try typing into search bar and pressing enter
    success = type_text(query, hit_enter=True)
    if not success:
        # Fallback to direct URL intent
        enc = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={enc}"
        run_adb(["am", "start", "-a", "android.intent.action.VIEW", "-d", url])
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Dexter Screen Action Automation")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # Type command
    p_type = subparsers.add_parser("type", help="Type text on screen")
    p_type.add_argument("text", help="Text to type")
    p_type.add_argument("--enter", action="store_true", help="Press Enter after typing")

    # Search command
    p_search = subparsers.add_parser("search", help="Search YouTube/App")
    p_search.add_argument("query", help="Query string")

    # Key command
    p_key = subparsers.add_parser("key", help="Send key event (enter, back, home, etc.)")
    p_key.add_argument("name", help="Key name or keycode")

    # Tap command
    p_tap = subparsers.add_parser("tap", help="Tap coordinates")
    p_tap.add_argument("x", type=int, help="X coordinate")
    p_tap.add_argument("y", type=int, help="Y coordinate")

    # Swipe command
    p_swipe = subparsers.add_parser("swipe", help="Swipe screen")
    p_swipe.add_argument("direction", nargs="?", default="up", choices=["up", "down", "left", "right", "next", "prev"])

    args = parser.parse_args()

    if args.action == "type":
        ok = type_text(args.text, hit_enter=args.enter)
        print("Success" if ok else "Failed")
        return 0 if ok else 1
    elif args.action == "search":
        ok = search_youtube(args.query)
        print("Success" if ok else "Failed")
        return 0 if ok else 1
    elif args.action == "key":
        ok = press_key(args.name)
        print("Success" if ok else "Failed")
        return 0 if ok else 1
    elif args.action == "tap":
        ok = tap(args.x, args.y)
        print("Success" if ok else "Failed")
        return 0 if ok else 1
    elif args.action == "swipe":
        ok = swipe(args.direction)
        print("Success" if ok else "Failed")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
