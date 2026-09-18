"""Clipboard Intelligence Service — Jenna AI Smart Clipboard Enhancement.

Jenna reads your clipboard, understands what kind of content it is, and
uses Gemini to fix grammar, improve writing, translate Hindi<->English,
or fix code bugs — then optionally writes back to clipboard automatically.
"""

import asyncio
from datetime import datetime, timezone
import logging
import os
import re
import subprocess
from typing import Any

from app.ai.vision.gemini_vision_provider import GeminiVisionProvider

logger = logging.getLogger("jenna.clipboard_intelligence")

# Content-type detection patterns
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

# Smart enhancement prompt
_ENHANCEMENT_PROMPT_TEMPLATE = """Tu ek caring AI assistant hai jiska naam Jenna hai.
User ke clipboard mein yeh content hai:

---
{content}
---

Content type: {content_type}

Iske basis pe ek perfect enhanced version banana:
- Agar yeh code hai: bugs fix kar, formatting improve kar, aur brief comment add kar.
- Agar Hindi text hai: grammar sahi kar, natural aur fluent banao, spelling theek karo.
- Agar English text hai: grammar, clarity, aur tone improve karo — professional but warm.
- Agar mixed Hindi-English (Hinglish) hai: natural aur expressive banao.
- Agar URL hai: as-is return kar with a brief one-line description of what it likely is.
- Agar phone number hai: properly format karo (Indian format preferred).

Sirf enhanced content return karo, koi explanation nahi, koi extra text nahi.
Bas seedha improved version likho:"""


class ClipboardIntelligenceService:
    """Smart clipboard reader, enhancer, and writer using Gemini AI."""

    def __init__(self) -> None:
        self.provider = GeminiVisionProvider()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_content_type(self, text: str) -> str:
        """Detect the type of clipboard content.

        Returns one of: code | hindi_text | english_text | url | phone_number | mixed
        """
        if not text or not text.strip():
            return "empty"

        stripped = text.strip()

        # URL
        if _URL_PATTERN.search(stripped) and "\n" not in stripped:
            return "url"

        # Phone number
        if _PHONE_PATTERN.match(stripped):
            return "phone_number"

        # Code
        if _CODE_PATTERNS.search(stripped):
            return "code"

        # Hindi check
        has_hindi = bool(_HINDI_PATTERN.search(stripped))
        has_english = bool(re.search(r"[a-zA-Z]{3,}", stripped))

        if has_hindi and has_english:
            return "mixed"
        if has_hindi:
            return "hindi_text"
        return "english_text"

    async def enhance_clipboard(
        self, auto_copy_back: bool = True
    ) -> dict[str, Any]:
        """Read clipboard, enhance content with Gemini, optionally write back.

        Args:
            auto_copy_back: If True, write enhanced content back to clipboard.

        Returns:
            dict with keys: original, enhanced, content_type, copied_back, toast_shown, error
        """
        # --- Read clipboard ---
        original = await self._read_clipboard()
        if original is None:
            return {
                "original": "",
                "enhanced": "",
                "content_type": "empty",
                "copied_back": False,
                "toast_shown": False,
                "error": "Clipboard khaali hai ya termux-clipboard-get kaam nahi kar raha.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        original_stripped = original.strip()
        if not original_stripped:
            return {
                "original": original,
                "enhanced": "",
                "content_type": "empty",
                "copied_back": False,
                "toast_shown": False,
                "error": "Clipboard mein koi content nahi mila.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        content_type = self.detect_content_type(original_stripped)

        # --- Enhance with Gemini ---
        enhanced = ""
        try:
            prompt = _ENHANCEMENT_PROMPT_TEMPLATE.format(
                content=original_stripped, content_type=content_type
            )
            # Use text-only via analyze_image with a 1x1 transparent pixel workaround
            # Actually we use a direct Gemini text call via the provider's underlying client
            enhanced = await self._call_gemini_text(prompt, original_stripped)
        except Exception as exc:
            logger.error(f"Gemini clipboard enhancement failed: {exc}")
            return {
                "original": original_stripped,
                "enhanced": "",
                "content_type": content_type,
                "copied_back": False,
                "toast_shown": False,
                "error": f"Gemini error: {exc}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        if not enhanced:
            enhanced = original_stripped  # Fallback to original

        # --- Auto copy back ---
        copied_back = False
        if auto_copy_back:
            copied_back = await self._write_clipboard(enhanced)

        # --- Toast notification ---
        toast_shown = False
        preview = enhanced[:60] + ("…" if len(enhanced) > 60 else "")
        toast_shown = await self._show_toast(f"Jenna: {preview}")

        return {
            "original": original_stripped,
            "enhanced": enhanced,
            "content_type": content_type,
            "copied_back": copied_back,
            "toast_shown": toast_shown,
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_gemini_text(self, prompt: str, fallback: str) -> str:
        """Call Gemini with a text-only prompt using the provider's client."""

        def _do_call() -> str:
            client = self.provider._client  # noqa: SLF001
            if not client:
                logger.warning("Gemini client not available — returning original.")
                return fallback

            for model in [
                "gemini-flash-lite-latest",
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-1.5-flash",
            ]:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    return (response.text or "").strip()
                except Exception as me:
                    logger.warning(f"Gemini text model {model} failed: {me}")
            return fallback

        return await asyncio.to_thread(_do_call)

    async def _read_clipboard(self) -> str | None:
        """Read clipboard content via termux-clipboard-get."""

        def _do_read() -> str | None:
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
                logger.warning(
                    f"termux-clipboard-get failed (code={proc.returncode}): "
                    f"{proc.stderr.strip()}"
                )
                return None
            except FileNotFoundError:
                logger.warning("termux-clipboard-get not found — Termux API missing?")
                return None
            except subprocess.TimeoutExpired:
                logger.warning("termux-clipboard-get timed out.")
                return None
            except Exception as exc:
                logger.error(f"Clipboard read error: {exc}")
                return None

        return await asyncio.to_thread(_do_read)

    async def _write_clipboard(self, text: str) -> bool:
        """Write text back to clipboard via termux-clipboard-set."""

        def _do_write() -> bool:
            try:
                proc = subprocess.run(
                    ["termux-clipboard-set", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=5.0,
                )
                if proc.returncode != 0:
                    logger.warning(
                        f"termux-clipboard-set failed: "
                        f"{proc.stderr.decode(errors='replace').strip()}"
                    )
                    return False
                return True
            except FileNotFoundError:
                logger.warning("termux-clipboard-set not found.")
                return False
            except subprocess.TimeoutExpired:
                logger.warning("termux-clipboard-set timed out.")
                return False
            except Exception as exc:
                logger.error(f"Clipboard write error: {exc}")
                return False

        return await asyncio.to_thread(_do_write)

    async def _show_toast(self, message: str) -> bool:
        """Show a toast notification via termux-toast."""

        def _do_toast() -> bool:
            try:
                proc = subprocess.run(
                    ["termux-toast", "-s", message],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=5.0,
                )
                return proc.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                return False

        return await asyncio.to_thread(_do_toast)


# Singleton
clipboard_intelligence_service = ClipboardIntelligenceService()
