"""Screen Narrator Service — Jenna AI Live Screen Narration.

Jenna captures the phone screen, understands what's visible, and narrates it
aloud in a natural, warm, conversational Hindi/English voice — like a loving
companion describing the world to you.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import logging
import os
import subprocess
from typing import Any

from app.ai.vision.gemini_vision_provider import GeminiVisionProvider
from app.ai.vision.live_screen import live_screen_service

logger = logging.getLogger("jenna.vision.screen_narrator")

# Natural narration prompt — conversational, warm, not robotic
_NARRATION_PROMPT = (
    "Tu ek caring AI companion hai jiska naam Jenna hai. "
    "Tu apne user ki phone screen dekh rahi hai aur usse naturally batana chahti hai kya dikh raha hai. "
    "Screen pe jo kuch bhi visible hai usse ek dost ki tarah describe kar — "
    "simple, pyaari, aur conversational Hindi-English (Hinglish) mein. "
    "Bilkul robotic ya boring mat bolna. Max 2-3 short sentences mein bata. "
    "Example style: 'Teri YouTube khuli hai, koi recipe video chal rahi hai. "
    "Bahut yummy lag raha hai!' "
    "Abhi screen pe kya dikh raha hai woh bata:"
)


class ScreenNarratorService:
    """Narrates the live phone screen via Gemini Vision and Termux TTS."""

    def __init__(self, serial: str = "localhost:5555") -> None:
        self.serial = os.getenv("ANDROID_SERIAL", serial)
        self.provider = GeminiVisionProvider()

        self._last_screen_hash: str | None = None
        self._auto_task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._running: bool = False

    # ------------------------------------------------------------------
    # Core narration
    # ------------------------------------------------------------------

    async def narrate_once(self) -> dict[str, Any]:
        """Capture screen, ask Gemini for narration, speak it aloud.

        Returns:
            dict with keys: text, spoken, skipped (dedup), error
        """
        screen_bytes = await live_screen_service.capture_screen_bytes(force_refresh=True)
        if not screen_bytes:
            return {
                "text": "",
                "spoken": False,
                "skipped": False,
                "error": "Screen capture unavailable — ADB se screenshot nahi mila.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # --- Smart dedup: skip if screen hasn't changed ---
        current_hash = hashlib.md5(screen_bytes).hexdigest()  # noqa: S324
        if current_hash == self._last_screen_hash:
            logger.debug("Screen unchanged — narration skipped (dedup).")
            return {
                "text": "",
                "spoken": False,
                "skipped": True,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        self._last_screen_hash = current_hash

        # --- Send to Gemini Vision ---
        narration_text = ""
        try:
            res = await self.provider.analyze_screen(
                screen_data=screen_bytes,
                mime_type="image/png",
                detect_ui_elements=False,
                prompt=_NARRATION_PROMPT,
            )
            narration_text = (res.description or "").strip()
        except Exception as exc:
            logger.error(f"Gemini narration failed: {exc}")
            return {
                "text": "",
                "spoken": False,
                "skipped": False,
                "error": f"Gemini Vision error: {exc}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        if not narration_text:
            return {
                "text": "",
                "spoken": False,
                "skipped": False,
                "error": "Gemini returned empty narration.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # --- Speak aloud via Termux TTS ---
        spoken = await self._speak(narration_text)

        return {
            "text": narration_text,
            "spoken": spoken,
            "skipped": False,
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Auto narration loop
    # ------------------------------------------------------------------

    async def start_auto_narration(self, interval_sec: float = 10.0) -> dict[str, Any]:
        """Start a background loop that narrates the screen every `interval_sec` seconds.

        If already running, returns current status without starting another loop.
        """
        if self._running and self._auto_task and not self._auto_task.done():
            return {
                "status": "already_running",
                "interval_sec": interval_sec,
                "message": "Auto narration pehle se chal rahi hai, Jenna screen dekh rahi hai!",
            }

        self._running = True
        self._auto_task = asyncio.create_task(
            self._narration_loop(interval_sec), name="jenna_screen_narrator"
        )
        logger.info(f"Auto screen narration started (interval={interval_sec}s)")
        return {
            "status": "started",
            "interval_sec": interval_sec,
            "message": f"Theek hai! Main ab har {interval_sec} seconds mein screen dekh ke bataungi.",
        }

    async def stop_auto_narration(self) -> dict[str, Any]:
        """Stop the background narration loop gracefully."""
        self._running = False
        if self._auto_task and not self._auto_task.done():
            self._auto_task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(self._auto_task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        self._auto_task = None
        logger.info("Auto screen narration stopped.")
        return {
            "status": "stopped",
            "message": "Okay, main ab screen narration band karti hoon. Rest le lo!",
        }

    def is_running(self) -> bool:
        """Return True if the auto narration loop is active."""
        return self._running and bool(
            self._auto_task and not self._auto_task.done()
        )

    async def _narration_loop(self, interval_sec: float) -> None:
        """Internal background coroutine for periodic narration."""
        while self._running:
            try:
                result = await self.narrate_once()
                if result.get("error"):
                    logger.warning(f"Narration loop error: {result['error']}")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Unexpected narration loop error: {exc}")
            try:
                await asyncio.sleep(interval_sec)
            except asyncio.CancelledError:
                break

    # ------------------------------------------------------------------
    # TTS helper
    # ------------------------------------------------------------------

    async def _speak(self, text: str) -> bool:
        """Speak text via termux-tts-speak on the phone speaker.

        Returns True if TTS succeeded, False otherwise (text still returned).
        """
        def _do_speak() -> bool:
            try:
                proc = subprocess.run(
                    ["termux-tts-speak", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                )
                return proc.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as exc:
                logger.debug(f"TTS non-fatal skip: {exc}")
                return False

        return await asyncio.to_thread(_do_speak)


# Singleton
screen_narrator_service = ScreenNarratorService()
