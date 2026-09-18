"""Android Context Ingestion, Notification Sanitization, and Privacy Controls."""

import re
from datetime import datetime, timezone
from app.ai.android.types import AndroidContextPayload, AndroidNotificationItem

# Regex patterns for sensitive content in notifications
OTP_PATTERN = re.compile(r"\b\d{4,8}\b(?=.*(?:otp|code|pin|verification|password))", re.IGNORECASE)
CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
PASSWORD_KEYWORD = re.compile(r"(password|passcode|secret|api[-_]?key)[:=]\s*\S+", re.IGNORECASE)


def sanitize_notification_text(text: str) -> str:
    """Scrub financial OTPs, card numbers, and credentials from notification text."""
    sanitized = text
    # Scrub explicit password patterns
    sanitized = PASSWORD_KEYWORD.sub(r"\1: [REDACTED]", sanitized)
    # Scrub credit/debit card numbers
    sanitized = CARD_PATTERN.sub("[CARD_REDACTED]", sanitized)
    # Scrub OTPs if associated with verification keywords
    if any(k in text.lower() for k in ["otp", "code", "pin", "verify", "verification"]):
        sanitized = re.sub(r"\b\d{4,8}\b", "[OTP_REDACTED]", sanitized)
    return sanitized


class AndroidContextManager:
    """Maintains sanitized device context and enforces privacy boundaries."""

    def __init__(self):
        # device_id -> AndroidContextPayload
        self._latest_context: dict[str, AndroidContextPayload] = {}

    def ingest_context(self, payload: AndroidContextPayload) -> AndroidContextPayload:
        """Process and sanitize incoming context telemetry."""
        sanitized_notifications: list[AndroidNotificationItem] = []
        for notif in payload.notifications:
            clean_title = sanitize_notification_text(notif.title)
            clean_text = sanitize_notification_text(notif.text)
            sanitized_notifications.append(
                AndroidNotificationItem(
                    notification_id=notif.notification_id,
                    package_name=notif.package_name,
                    title=clean_title,
                    text=clean_text,
                    posted_at=notif.posted_at,
                    is_clearable=notif.is_clearable,
                )
            )

        sanitized_payload = AndroidContextPayload(
            device_id=payload.device_id,
            foreground_app=payload.foreground_app,
            screen_width=payload.screen_width,
            screen_height=payload.screen_height,
            battery_level=payload.battery_level,
            is_charging=payload.is_charging,
            network_type=payload.network_type,
            notifications=sanitized_notifications,
            timestamp=datetime.now(timezone.utc),
        )

        self._latest_context[payload.device_id] = sanitized_payload
        return sanitized_payload

    def get_latest_context(self, device_id: str) -> AndroidContextPayload | None:
        """Retrieve most recent sanitized context for a device."""
        return self._latest_context.get(device_id)


# Global singleton instance
android_context_manager = AndroidContextManager()
