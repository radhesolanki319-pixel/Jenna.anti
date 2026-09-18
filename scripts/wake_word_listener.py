#!/usr/bin/env python3
"""Jenna Wake Word Listener.

Continuously listens for "Hey Jenna" (and variants) using either
termux-speech-to-text or a simple voice-activity-detection fallback.

Trigger phrases (case-insensitive):
  • hey jenna   • jenna   • hey jenu   • jenna sun   • sun jenna
  • any utterance ending in "jenna?"  or starting with "jenna,"

On detection:
  • vibrate 500 ms
  • toast "Jenna sun rahi hai! 💖"
  • POST to backend /api/v1/conversations/quick-listen  (best-effort)
  • OR speak: "Haan baby, batao!"

Usage:
    python3 scripts/wake_word_listener.py
    # Ctrl-C or SIGTERM to stop gracefully
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [wake-word] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("wake_word")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_URL = os.environ.get("JENNA_BACKEND_URL", "http://localhost:8000")
QUICK_LISTEN_URL = f"{BACKEND_URL}/api/v1/conversations/quick-listen"

WAKE_AUDIO_PATH = "/tmp/jenna_wake.wav"
RECORD_DURATION_SEC = 3
LOOP_SLEEP_SEC = 1
MIN_VOICE_BYTES = 5120  # 5 KB — simple VAD threshold

TRIGGER_PATTERNS = [
    r"\bhey\s+jenn?[au]\b",
    r"\bjenn?[au]\s+sun\b",
    r"\bsun\s+jenn?[au]\b",
    r"\bjenn?[au]\b",          # bare "jenna" / "jenu"
    r"\bjenn?[au]\?",          # ends with "jenna?"
    r"^jenn?[au]\s*,",         # starts with "jenna,"
]
_TRIGGER_RE = re.compile("|".join(TRIGGER_PATTERNS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# Graceful shutdown flag
# ---------------------------------------------------------------------------
_running = True


def _handle_signal(sig, frame) -> None:
    global _running
    logger.info("Received signal %d — shutting down.", sig)
    _running = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

# ---------------------------------------------------------------------------
# Termux utility helpers
# ---------------------------------------------------------------------------

def _has_cmd(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _vibrate(ms: int = 500) -> None:
    if _has_cmd("termux-vibrate"):
        subprocess.Popen(
            ["termux-vibrate", "-d", str(ms)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def _toast(msg: str) -> None:
    if _has_cmd("termux-toast"):
        subprocess.Popen(
            ["termux-toast", "-s", msg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    else:
        logger.info("[TOAST] %s", msg)


def _tts(msg: str) -> None:
    if _has_cmd("termux-tts-speak"):
        subprocess.Popen(
            ["termux-tts-speak", msg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    else:
        logger.info("[TTS] %s", msg)

# ---------------------------------------------------------------------------
# Backend call
# ---------------------------------------------------------------------------

def _notify_backend() -> None:
    """POST to the quick-listen endpoint (best effort, no crash on failure)."""
    try:
        import urllib.request
        import urllib.error
        data = json.dumps({"trigger": "wake_word", "source": "wake_word_listener"}).encode()
        req = urllib.request.Request(
            QUICK_LISTEN_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            logger.debug("Backend notified: %s", resp.status)
    except Exception as exc:
        logger.debug("Backend notification failed (non-fatal): %s", exc)

# ---------------------------------------------------------------------------
# On wake detection
# ---------------------------------------------------------------------------

def _on_wake_detected(transcript: Optional[str] = None) -> None:
    """Actions to run when the wake word is detected."""
    logger.info("🔔 Wake word detected! transcript=%r", transcript)
    _vibrate(500)
    _toast("Jenna sun rahi hai! 💖")
    _notify_backend()
    _tts("Haan baby, batao!")

# ---------------------------------------------------------------------------
# STT-based detection
# ---------------------------------------------------------------------------

def _record_and_transcribe_stt() -> Optional[str]:
    """Record 3 seconds and transcribe via termux-speech-to-text.

    Returns the transcript string, or None on failure.
    """
    try:
        result = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True,
            text=True,
            timeout=RECORD_DURATION_SEC + 5,
        )
        text = result.stdout.strip()
        if text:
            logger.debug("STT transcript: %r", text)
        return text or None
    except subprocess.TimeoutExpired:
        logger.debug("termux-speech-to-text timed out.")
    except Exception as exc:
        logger.debug("termux-speech-to-text error: %s", exc)
    return None


def _stt_loop() -> None:
    """Wake detection using termux-speech-to-text."""
    logger.info("Using termux-speech-to-text for wake word detection.")
    logger.info("Listening for wake words: hey jenna / jenna / hey jenu / jenna sun …")

    while _running:
        transcript = _record_and_transcribe_stt()
        if transcript and _TRIGGER_RE.search(transcript):
            _on_wake_detected(transcript)
        time.sleep(LOOP_SLEEP_SEC)

# ---------------------------------------------------------------------------
# VAD (voice activity detection) fallback
# ---------------------------------------------------------------------------

def _record_wav(path: str, duration: int) -> bool:
    """Record audio to WAV. Returns True if the file was created."""
    try:
        subprocess.run(
            ["termux-microphone-record", "-l", str(duration), "-f", path],
            timeout=duration + 5,
            capture_output=True,
        )
        return Path(path).exists()
    except subprocess.TimeoutExpired:
        logger.debug("termux-microphone-record timed out.")
    except FileNotFoundError:
        logger.warning("termux-microphone-record not found.")
    except Exception as exc:
        logger.debug("Recording error: %s", exc)
    return False


def _vad_loop() -> None:
    """Fallback: simple voice activity detection via file size."""
    logger.info(
        "termux-speech-to-text not available — using VAD fallback "
        "(file size > %d bytes = voice detected).", MIN_VOICE_BYTES
    )
    logger.info("On voice detected: toast + vibrate (no transcript matching).")

    while _running:
        audio_path = Path(WAKE_AUDIO_PATH)
        # Remove stale file
        if audio_path.exists():
            audio_path.unlink(missing_ok=True)

        ok = _record_wav(WAKE_AUDIO_PATH, RECORD_DURATION_SEC)
        if ok and audio_path.exists():
            size = audio_path.stat().st_size
            logger.debug("Recorded %s — size=%d bytes", WAKE_AUDIO_PATH, size)
            if size > MIN_VOICE_BYTES:
                logger.info("Voice activity detected (%d bytes).", size)
                _vibrate(400)
                _toast("Jenna sun rahi hai, Termux mein type karo! 💖")
                _notify_backend()
        else:
            logger.debug("No audio file produced, skipping.")

        time.sleep(LOOP_SLEEP_SEC)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("═══════════════════════════════════════")
    logger.info("  Jenna Wake Word Listener  🎙️")
    logger.info("  Backend: %s", BACKEND_URL)
    logger.info("═══════════════════════════════════════")

    if _has_cmd("termux-speech-to-text"):
        _stt_loop()
    elif _has_cmd("termux-microphone-record"):
        _vad_loop()
    else:
        logger.error(
            "Neither termux-speech-to-text nor termux-microphone-record is available.\n"
            "Install Termux:API and grant microphone permission, then retry."
        )
        sys.exit(1)

    logger.info("Wake word listener shut down cleanly.")


if __name__ == "__main__":
    main()
