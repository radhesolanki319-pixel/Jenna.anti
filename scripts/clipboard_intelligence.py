#!/usr/bin/env python3
"""Jenna Clipboard Intelligence CLI — Smart Clipboard Enhancer.

Usage:
    python3 scripts/clipboard_intelligence.py           # enhance and copy back
    python3 scripts/clipboard_intelligence.py --no-copy # enhance only, show result
"""

import argparse
import asyncio
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_API_SRC = _PROJECT_ROOT / "apps" / "api"

for _path in [str(_PROJECT_ROOT), str(_API_SRC)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("clipboard_intelligence_cli")

# ---------------------------------------------------------------------------
# Standalone helpers (no backend dependency — works standalone)
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(
    r"^https?://|^www\.|\.com|\.org|\.net|\.in|\.io", re.IGNORECASE
)
_PHONE_PATTERN = re.compile(r"^[+]?[\d\s\-()]{7,15}$")
_CODE_PATTERNS = re.compile(
    r"def |class |import |function |const |var |let |<html|<!DOCTYPE|#include|"
    r"print\(|console\.log|public static|void main|SELECT |FROM |WHERE |INSERT ",
    re.IGNORECASE,
)
_HINDI_PATTERN = re.compile(r"[\u0900-\u097F]")


def detect_content_type(text: str) -> str:
    """Detect content type: code | hindi_text | english_text | url | phone_number | mixed."""
    if not text or not text.strip():
        return "empty"
    stripped = text.strip()
    if _URL_PATTERN.search(stripped) and "\n" not in stripped:
        return "url"
    if _PHONE_PATTERN.match(stripped):
        return "phone_number"
    if _CODE_PATTERNS.search(stripped):
        return "code"
    has_hindi = bool(_HINDI_PATTERN.search(stripped))
    has_english = bool(re.search(r"[a-zA-Z]{3,}", stripped))
    if has_hindi and has_english:
        return "mixed"
    if has_hindi:
        return "hindi_text"
    return "english_text"


def read_clipboard() -> str | None:
    """Read clipboard via termux-clipboard-get."""
    try:
        proc = subprocess.run(
            ["termux-clipboard-get"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5.0,
            text=True,
        )
        if proc.returncode == 0:
            return proc.stdout
        print(f"[!] termux-clipboard-get failed: {proc.stderr.strip()}")
        return None
    except FileNotFoundError:
        print("[!] termux-clipboard-get not found. Install Termux:API.")
        return None
    except subprocess.TimeoutExpired:
        print("[!] termux-clipboard-get timed out.")
        return None


def write_clipboard(text: str) -> bool:
    """Write text to clipboard via termux-clipboard-set."""
    try:
        proc = subprocess.run(
            ["termux-clipboard-set", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=5.0,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def show_toast(message: str) -> None:
    """Show a short toast notification."""
    try:
        subprocess.run(
            ["termux-toast", "-s", message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3.0,
        )
    except Exception:
        pass


def get_api_key() -> str | None:
    """Find Gemini/Google API key from environment or .env file."""
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key:
        return key
    env_file = _PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("GOOGLE_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def enhance_with_gemini(content: str, content_type: str, api_key: str) -> str:
    """Call Gemini to enhance the clipboard content."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = (
            f"Tu ek caring AI assistant hai jiska naam Jenna hai.\n"
            f"User ke clipboard mein yeh content hai:\n\n---\n{content}\n---\n\n"
            f"Content type: {content_type}\n\n"
            "Iske basis pe ek perfect enhanced version banana:\n"
            "- Agar yeh code hai: bugs fix kar, formatting improve kar, aur brief comment add kar.\n"
            "- Agar Hindi text hai: grammar sahi kar, natural aur fluent banao, spelling theek karo.\n"
            "- Agar English text hai: grammar, clarity, aur tone improve karo — professional but warm.\n"
            "- Agar mixed Hindi-English (Hinglish) hai: natural aur expressive banao.\n"
            "- Agar URL hai: as-is return kar.\n"
            "- Agar phone number hai: properly format karo.\n\n"
            "Sirf enhanced content return karo, koi explanation nahi:"
        )

        for model in ["gemini-flash-lite-latest", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                result = (response.text or "").strip()
                if result:
                    return result
            except Exception as me:
                logger.debug(f"Model {model} failed: {me}")

        return content  # Fallback to original

    except ImportError:
        print("[!] google-genai not installed — pip install google-genai")
        return content
    except Exception as exc:
        print(f"[!] Gemini error: {exc}")
        return content


async def run_enhancement(auto_copy_back: bool = True) -> None:
    """Main async runner for clipboard enhancement."""
    print("📋 Jenna Clipboard Intelligence\n")

    # Read clipboard
    original = read_clipboard()
    if original is None or not original.strip():
        print("❌ Clipboard khaali hai ya read nahi ho saka.")
        sys.exit(1)

    original = original.strip()
    content_type = detect_content_type(original)

    print(f"📌 Content type detected: {content_type}")
    print(f"📝 Original ({len(original)} chars):\n{original[:200]}{'...' if len(original) > 200 else ''}\n")

    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ GOOGLE_API_KEY nahi mili. .env file ya environment mein set karo.")
        sys.exit(1)

    # Enhance
    print("🤖 Gemini se enhancement ho rahi hai...")
    enhanced = await asyncio.to_thread(enhance_with_gemini, original, content_type, api_key)

    print(f"\n✨ Enhanced ({len(enhanced)} chars):\n{enhanced}\n")

    # Copy back
    if auto_copy_back:
        success = await asyncio.to_thread(write_clipboard, enhanced)
        if success:
            print("✅ Enhanced content clipboard mein copy ho gaya!")
            preview = enhanced[:60] + ("…" if len(enhanced) > 60 else "")
            await asyncio.to_thread(show_toast, f"Jenna: {preview}")
        else:
            print("⚠️  Clipboard write failed — enhanced text upar dikh raha hai.")
    else:
        print("ℹ️  --no-copy mode: clipboard update nahi hua.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jenna Clipboard Intelligence — smart clipboard enhancer!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        dest="no_copy",
        help="Show enhanced result but don't write back to clipboard",
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_enhancement(auto_copy_back=not args.no_copy))
    except KeyboardInterrupt:
        print("\nJenna: Theek hai, band karti hoon. Bye! 💕")
        sys.exit(0)


if __name__ == "__main__":
    main()
