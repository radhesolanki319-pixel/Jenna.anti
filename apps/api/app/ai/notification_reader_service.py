"""Smart Notification Reader Service for Jenna AI.

Reads active Android notifications via termux-notification-list, filters
important apps (WhatsApp, Telegram, Gmail, SMS, Phone), formats them in
Hindi/Hinglish, speaks via termux-tts-speak, and drafts Gemini replies.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("jenna.ai.notification_reader")

# ── Package → friendly name mapping ──────────────────────────────────────────
_APP_LABELS: dict[str, str] = {
    "com.whatsapp": "WhatsApp",
    "com.whatsapp.w4b": "WhatsApp Business",
    "org.telegram.messenger": "Telegram",
    "org.telegram.messenger.web": "Telegram",
    "com.google.android.gm": "Gmail",
    "com.android.mms": "SMS",
    "com.android.messaging": "SMS",
    "com.google.android.apps.messaging": "Messages",
    "com.samsung.android.messaging": "Samsung Messages",
    "com.android.phone": "Phone",
    "com.google.android.dialer": "Phone",
    "com.samsung.android.incallui": "Phone",
    "com.miui.incallui": "Phone",
    "com.vivo.incallui": "Phone",
    "com.instagram.android": "Instagram",
    "com.facebook.katana": "Facebook",
    "com.facebook.orca": "Messenger",
    "com.twitter.android": "Twitter",
    "com.linkedin.android": "LinkedIn",
    "com.snapchat.android": "Snapchat",
    "com.discord": "Discord",
    "com.slack": "Slack",
}

# Packages considered "important" — worth reading aloud
_IMPORTANT_PACKAGES: set[str] = {
    "com.whatsapp",
    "com.whatsapp.w4b",
    "org.telegram.messenger",
    "org.telegram.messenger.web",
    "com.google.android.gm",
    "com.android.mms",
    "com.android.messaging",
    "com.google.android.apps.messaging",
    "com.samsung.android.messaging",
    "com.android.phone",
    "com.google.android.dialer",
    "com.samsung.android.incallui",
    "com.miui.incallui",
    "com.vivo.incallui",
}


def get_app_label(package: str) -> str:
    """Map a package name to a human-friendly app name."""
    if not package:
        return "Unknown App"
    # Try exact match first
    label = _APP_LABELS.get(package)
    if label:
        return label
    # Fallback: extract last component
    parts = package.split(".")
    return parts[-1].replace("_", " ").title() if parts else package


class NotificationReaderService:
    """Reads, filters, speaks, and drafts replies for Android notifications."""

    def __init__(self) -> None:
        # Dedup cache: set of notification fingerprint hashes already processed
        self._seen: set[str] = set()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _fingerprint(self, notif: dict[str, Any]) -> str:
        """Create a stable hash for a notification to detect duplicates."""
        key = "|".join([
            str(notif.get("packageName", "")),
            str(notif.get("title", "")),
            str(notif.get("content", "")),
        ])
        return hashlib.sha256(key.encode()).hexdigest()

    def _fetch_notifications(self) -> list[dict[str, Any]]:
        """Run termux-notification-list and return parsed JSON array."""
        try:
            result = subprocess.run(
                ["termux-notification-list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10.0,
            )
            if result.returncode != 0:
                logger.warning(
                    "termux-notification-list failed: %s", result.stderr.strip()
                )
                return []
            raw = result.stdout.strip()
            if not raw:
                return []
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            logger.warning("Could not parse notification JSON: %s", exc)
            return []
        except FileNotFoundError:
            logger.warning("termux-notification-list not found; is Termux:API installed?")
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error fetching notifications: %s", exc)
            return []

    def _is_important(self, notif: dict[str, Any]) -> bool:
        """Return True if the notification should be read aloud."""
        pkg = notif.get("packageName", "")
        return pkg in _IMPORTANT_PACKAGES

    def _format_spoken_text(self, notif: dict[str, Any]) -> str:
        """Format notification as natural Hindi/Hinglish speech text."""
        app = get_app_label(notif.get("packageName", ""))
        title = notif.get("title", "").strip()
        content = notif.get("content", "").strip()

        pkg = notif.get("packageName", "")

        # Phone call (special handling)
        if "phone" in pkg.lower() or "incallui" in pkg.lower() or "dialer" in pkg.lower():
            caller = title or content or "koi"
            return f"{caller} ka phone aa raha hai"

        # Compose spoken line
        parts: list[str] = []
        if app:
            parts.append(f"{app} pe")
        if title and title.lower() not in ("null", "none", ""):
            parts.append(f"{title} ka message hai")
        if content and content.lower() not in ("null", "none", ""):
            parts.append(f": {content}")

        spoken = " ".join(parts) if parts else "ek naya notification hai"
        return spoken

    def _speak(self, text: str) -> None:
        """Speak text using termux-tts-speak (fire-and-forget subprocess)."""
        try:
            subprocess.run(
                ["termux-tts-speak", text],
                timeout=30.0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            logger.warning("termux-tts-speak not found; skipping TTS.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("TTS speak failed: %s", exc)

    # ── Public API ────────────────────────────────────────────────────────────

    async def read_new_notifications(
        self, speak: bool = True
    ) -> list[dict[str, Any]]:
        """Read all active notifications, filter important ones, speak new ones.

        Args:
            speak: Whether to call termux-tts-speak for each new notification.

        Returns:
            List of dicts with keys: app, title, text, spoken_text, reply_draft.
        """
        raw_list: list[dict[str, Any]] = await asyncio.to_thread(
            self._fetch_notifications
        )

        results: list[dict[str, Any]] = []

        for notif in raw_list:
            if not self._is_important(notif):
                continue

            fp = self._fingerprint(notif)
            is_new = fp not in self._seen

            spoken_text = self._format_spoken_text(notif)
            entry: dict[str, Any] = {
                "app": get_app_label(notif.get("packageName", "")),
                "package": notif.get("packageName", ""),
                "title": notif.get("title", ""),
                "text": notif.get("content", ""),
                "spoken_text": spoken_text,
                "reply_draft": "",
                "is_new": is_new,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            if is_new:
                self._seen.add(fp)
                if speak:
                    await asyncio.to_thread(self._speak, spoken_text)

            results.append(entry)

        return results

    async def list_all_notifications(self) -> list[dict[str, Any]]:
        """List all active notifications (important ones only), no speaking.

        Returns the same structure as read_new_notifications but never speaks.
        """
        raw_list: list[dict[str, Any]] = await asyncio.to_thread(
            self._fetch_notifications
        )
        results: list[dict[str, Any]] = []
        for notif in raw_list:
            if not self._is_important(notif):
                continue
            fp = self._fingerprint(notif)
            entry: dict[str, Any] = {
                "app": get_app_label(notif.get("packageName", "")),
                "package": notif.get("packageName", ""),
                "title": notif.get("title", ""),
                "text": notif.get("content", ""),
                "spoken_text": self._format_spoken_text(notif),
                "reply_draft": "",
                "is_new": fp not in self._seen,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            results.append(entry)
        return results

    async def draft_reply(self, notification: dict[str, Any]) -> str:
        """Use Gemini to draft a short, contextual reply for a notification.

        Args:
            notification: A notification dict (as returned by read_new_notifications).

        Returns:
            A suggested reply string, or empty string on failure.
        """
        try:
            from app.core.config import settings  # lazy import

            app = notification.get("app", "")
            title = notification.get("title", "")
            text = notification.get("text", "")

            prompt = (
                f"You are Jenna AI helping to draft a short reply.\n"
                f"App: {app}\n"
                f"From: {title}\n"
                f"Message: {text}\n\n"
                "Draft a short, friendly reply in the same language as the message "
                "(Hindi, Hinglish, or English). Keep it under 2 sentences. "
                "Only output the reply text, nothing else."
            )

            try:
                from google import genai  # type: ignore[import-untyped]
                from google.genai import types as gtypes  # type: ignore[import-untyped]
            except ImportError:
                logger.warning("google-genai not installed; skipping reply draft.")
                return ""

            api_key = settings.effective_google_api_key
            if not api_key:
                return ""

            client = genai.Client(api_key=api_key)

            def _call() -> str:
                for model in [
                    "gemini-flash-lite-latest",
                    "gemini-2.0-flash",
                    "gemini-1.5-flash",
                ]:
                    try:
                        resp = client.models.generate_content(
                            model=model,
                            contents=[gtypes.Part.from_text(text=prompt)],
                        )
                        return (resp.text or "").strip()
                    except Exception as me:
                        logger.warning("Model %s failed for reply draft: %s", model, me)
                return ""

            return await asyncio.to_thread(_call)

        except Exception as exc:  # noqa: BLE001
            logger.error("draft_reply failed: %s", exc)
            return ""

    def reset_cache(self) -> None:
        """Clear the dedup cache so all notifications will be treated as new."""
        self._seen.clear()


# Global singleton
notification_reader_service = NotificationReaderService()
