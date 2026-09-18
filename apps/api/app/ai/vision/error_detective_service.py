"""Live Error Detective Service for Jenna AI.

Captures the live Android screen and uses Gemini Vision to detect errors,
crashes, ANR dialogs, tracebacks, build failures, and HTTP error pages.
Supports one-shot scanning and continuous background watching.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger("jenna.ai.vision.error_detective")

ErrorSeverity = Literal["low", "medium", "high", "critical"]

_DETECTION_PROMPT = """\
You are an expert Android/software Error Detective AI.

Analyze this screen capture and detect ANY of the following:
1. App crash dialog ("Unfortunately, <app> has stopped")
2. ANR dialog ("App is not responding")
3. Red error text or exception tracebacks
4. Build failure output (Gradle, Maven, npm, etc.)
5. HTTP 404 / 500 / 502 / 503 error pages
6. Permission denial messages
7. Force-close buttons or "Close app" prompts
8. Stack traces or logcat error output
9. Firebase / database / network error messages
10. Any other critical software error visible on screen

Respond ONLY with a valid JSON object (no markdown fences) with these fields:
{
  "has_error": true or false,
  "error_type": "crash|anr|traceback|build_failure|http_error|permission_denial|other|none",
  "error_message": "short description of the error visible, or empty string",
  "suggested_fix": "concise actionable suggestion to fix this, or empty string",
  "severity": "low|medium|high|critical"
}

If no error is detected, set has_error=false, error_type="none", severity="low".
"""

_ALERT_SEVERITIES: frozenset[str] = frozenset({"high", "critical"})


class ErrorDetectiveService:
    """Detects software errors on the live Android screen using Gemini Vision."""

    def __init__(self) -> None:
        self._watching: bool = False
        self._watch_task: asyncio.Task[None] | None = None

    # ── Core scan ─────────────────────────────────────────────────────────────

    async def scan_for_errors(self) -> dict[str, Any]:
        """Capture live screen and analyze for errors with Gemini Vision.

        Returns:
            Dict with keys: has_error, error_type, error_message,
            suggested_fix, severity, timestamp.
        """
        from app.ai.vision.live_screen import live_screen_service  # lazy
        from app.ai.vision.gemini_vision_provider import GeminiVisionProvider  # lazy

        screen_bytes = await live_screen_service.capture_screen_bytes(
            force_refresh=True
        )

        empty_result: dict[str, Any] = {
            "has_error": False,
            "error_type": "none",
            "error_message": "",
            "suggested_fix": "",
            "severity": "low",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not screen_bytes:
            logger.warning("Could not capture screen for error detection.")
            empty_result["error_message"] = "Screen capture unavailable."
            return empty_result

        provider = GeminiVisionProvider()

        try:
            result = await provider.analyze_screen(
                screen_data=screen_bytes,
                mime_type="image/png",
                detect_ui_elements=False,
                prompt=_DETECTION_PROMPT,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini Vision error detection failed: %s", exc)
            return empty_result

        raw_text = (result.description or "").strip()
        parsed = self._parse_response(raw_text)
        parsed["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Auto-alert for high/critical errors
        if parsed.get("has_error") and parsed.get("severity") in _ALERT_SEVERITIES:
            await self._auto_alert(parsed)

        return parsed

    # ── Continuous watcher ────────────────────────────────────────────────────

    async def watch_for_errors(self, interval_sec: float = 5.0) -> None:
        """Continuously scan for errors at `interval_sec` intervals.

        Runs until `stop_watching()` is called.  Each detected error is logged
        and triggers auto-alerts for high/critical severity.
        """
        self._watching = True
        logger.info(
            "ErrorDetective: starting continuous watch (interval=%.1fs)", interval_sec
        )
        while self._watching:
            try:
                result = await self.scan_for_errors()
                if result.get("has_error"):
                    logger.warning(
                        "ErrorDetective detected [%s] %s — %s",
                        result.get("severity"),
                        result.get("error_type"),
                        result.get("error_message"),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.error("ErrorDetective watch loop error: %s", exc)
            await asyncio.sleep(interval_sec)
        logger.info("ErrorDetective: watch loop stopped.")

    def start_watching(self, interval_sec: float = 5.0) -> bool:
        """Start the background watch coroutine.  Returns False if already running."""
        if self._watching and self._watch_task and not self._watch_task.done():
            return False
        self._watch_task = asyncio.ensure_future(
            self.watch_for_errors(interval_sec=interval_sec)
        )
        return True

    def stop_watching(self) -> bool:
        """Stop the continuous watch loop.  Returns False if not running."""
        if not self._watching:
            return False
        self._watching = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
        self._watch_task = None
        return True

    @property
    def is_watching(self) -> bool:
        """True if the background watcher is currently active."""
        return self._watching and (
            self._watch_task is not None and not self._watch_task.done()
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_response(self, text: str) -> dict[str, Any]:
        """Parse Gemini JSON response into a structured error dict."""
        import json
        import re

        default: dict[str, Any] = {
            "has_error": False,
            "error_type": "none",
            "error_message": "",
            "suggested_fix": "",
            "severity": "low",
        }

        if not text:
            return default

        # Strip markdown fences if present
        clean = re.sub(r"```[a-z]*\n?", "", text).strip()

        try:
            parsed = json.loads(clean)
            # Validate / normalise fields
            has_error = bool(parsed.get("has_error", False))
            severity = str(parsed.get("severity", "low")).lower()
            if severity not in ("low", "medium", "high", "critical"):
                severity = "low"
            return {
                "has_error": has_error,
                "error_type": str(parsed.get("error_type", "none")),
                "error_message": str(parsed.get("error_message", ""))[:500],
                "suggested_fix": str(parsed.get("suggested_fix", ""))[:500],
                "severity": severity,
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Could not parse error-detective JSON: %s — raw: %.200s", exc, text)
            # Heuristic fallback: check for error keywords
            lowered = text.lower()
            has_error = any(
                kw in lowered
                for kw in ("crash", "exception", "error", "anr", "stopped", "traceback", "failure")
            )
            return {
                "has_error": has_error,
                "error_type": "other" if has_error else "none",
                "error_message": text[:200] if has_error else "",
                "suggested_fix": "",
                "severity": "medium" if has_error else "low",
            }

    async def _auto_alert(self, result: dict[str, Any]) -> None:
        """Show toast notification and vibrate for high/critical errors."""
        severity = result.get("severity", "low")
        error_msg = result.get("error_message", "Error detected")
        toast_msg = f"[{severity.upper()}] {error_msg[:80]}"

        def _do_alerts() -> None:
            try:
                subprocess.run(
                    ["termux-toast", "-s", toast_msg],
                    timeout=5.0,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("termux-toast failed: %s", exc)
            # Vibration disabled per user preference

        await asyncio.to_thread(_do_alerts)


# Global singleton
error_detective_service = ErrorDetectiveService()
