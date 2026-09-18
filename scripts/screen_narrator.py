#!/usr/bin/env python3
"""Jenna Screen Narrator CLI — Live Screen Narration Tool.

Usage:
    python3 scripts/screen_narrator.py              # narrate once
    python3 scripts/screen_narrator.py --loop       # loop every 10 seconds
    python3 scripts/screen_narrator.py --interval 5 # loop every 5 seconds
"""

import argparse
import asyncio
import hashlib
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sure the project root and apps/api are on sys.path so app.* imports work
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_API_SRC = _PROJECT_ROOT / "apps" / "api"

for _path in [str(_PROJECT_ROOT), str(_API_SRC)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ---------------------------------------------------------------------------
# Set up logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("screen_narrator_cli")


def _capture_screen(serial: str = "localhost:5555") -> bytes | None:
    """Capture screen via ADB, return PNG bytes or None."""
    try:
        proc = subprocess.run(
            ["adb", "-s", serial, "exec-out", "screencap", "-p"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8.0,
        )
        if proc.returncode == 0 and len(proc.stdout) > 5000:
            return proc.stdout
        print(f"[!] ADB screencap failed (code={proc.returncode}, size={len(proc.stdout)})")
        return None
    except FileNotFoundError:
        print("[!] 'adb' not found. Please install Android Debug Bridge.")
        return None
    except subprocess.TimeoutExpired:
        print("[!] ADB screencap timed out.")
        return None
    except Exception as exc:
        print(f"[!] Screen capture error: {exc}")
        return None


def _get_narration(screen_bytes: bytes, api_key: str | None = None) -> str:
    """Send screenshot to Gemini and get narration text."""
    try:
        from google import genai
        from google.genai import types as gtypes

        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            # Try loading from .env
            env_file = _PROJECT_ROOT / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("GOOGLE_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

        if not key:
            return "[Gemini API key nahi mili — GOOGLE_API_KEY set karo]"

        client = genai.Client(api_key=key)
        image_part = gtypes.Part.from_bytes(data=screen_bytes, mime_type="image/png")

        narration_prompt = (
            "Tu ek caring AI companion hai jiska naam Jenna hai. "
            "Tu apne user ki phone screen dekh rahi hai aur usse naturally batana chahti hai kya dikh raha hai. "
            "Screen pe jo kuch bhi visible hai usse ek dost ki tarah describe kar — "
            "simple, pyaari, aur conversational Hindi-English (Hinglish) mein. "
            "Bilkul robotic ya boring mat bolna. Max 2-3 short sentences mein bata. "
            "Example style: 'Teri YouTube khuli hai, koi recipe video chal rahi hai. Bahut yummy lag raha hai!' "
            "Abhi screen pe kya dikh raha hai woh bata:"
        )

        for model in ["gemini-flash-lite-latest", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[image_part, narration_prompt],
                )
                return (response.text or "").strip()
            except Exception as me:
                logger.debug(f"Model {model} failed: {me}")
        return "[Gemini se narration nahi mili]"

    except ImportError:
        return "[google-genai library install nahi hai — pip install google-genai]"
    except Exception as exc:
        return f"[Gemini error: {exc}]"


def _speak(text: str) -> bool:
    """Speak text via termux-tts-speak."""
    try:
        proc = subprocess.run(
            ["termux-tts-speak", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=60.0,
        )
        return proc.returncode == 0
    except FileNotFoundError:
        print("[!] termux-tts-speak not found — TTS unavailable.")
        return False
    except subprocess.TimeoutExpired:
        print("[!] TTS timed out.")
        return False
    except Exception as exc:
        print(f"[!] TTS error: {exc}")
        return False


async def narrate_once_async(serial: str = "localhost:5555") -> dict:
    """Async narration runner."""
    screen_bytes = await asyncio.to_thread(_capture_screen, serial)
    if not screen_bytes:
        return {"text": "", "spoken": False, "error": "Screen capture failed"}

    narration = await asyncio.to_thread(_get_narration, screen_bytes)
    print(f"\n🎙️  Jenna: {narration}\n")

    spoken = await asyncio.to_thread(_speak, narration)
    if not spoken:
        print("   (TTS unavailable — text only)")

    return {"text": narration, "spoken": spoken, "error": None}


async def loop_narration(interval: float = 10.0, serial: str = "localhost:5555") -> None:
    """Loop narration every `interval` seconds with smart dedup."""
    print(f"🔄 Auto narration started — every {interval}s. Press Ctrl+C to stop.\n")
    last_hash: str | None = None

    while True:
        screen_bytes = await asyncio.to_thread(_capture_screen, serial)
        if screen_bytes:
            current_hash = hashlib.md5(screen_bytes).hexdigest()  # noqa: S324
            if current_hash == last_hash:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Screen unchanged — skipping narration.")
            else:
                last_hash = current_hash
                narration = await asyncio.to_thread(_get_narration, screen_bytes)
                ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
                print(f"[{ts}] 🎙️  Jenna: {narration}")
                await asyncio.to_thread(_speak, narration)
        else:
            print("[!] Screen capture failed — retrying next interval.")

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jenna Screen Narrator — aapki screen ko awaz deti hai!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop narration continuously (default interval: 10s)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        metavar="SECONDS",
        help="Narration loop interval in seconds (default: 10)",
    )
    parser.add_argument(
        "--serial",
        type=str,
        default=os.getenv("ANDROID_SERIAL", "localhost:5555"),
        metavar="SERIAL",
        help="ADB device serial (default: localhost:5555)",
    )

    args = parser.parse_args()

    try:
        if args.loop or args.interval != 10.0:
            asyncio.run(loop_narration(interval=args.interval, serial=args.serial))
        else:
            result = asyncio.run(narrate_once_async(serial=args.serial))
            if result.get("error"):
                print(f"Error: {result['error']}")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nJenna: Theek hai, band karti hoon narration. Phir milenge! 💕")
        sys.exit(0)


if __name__ == "__main__":
    main()
