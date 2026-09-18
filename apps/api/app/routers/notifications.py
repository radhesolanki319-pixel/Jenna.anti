"""Notifications API Router for Jenna AI.

Provides endpoints to read and list Android notifications via the Smart
Notification Reader service.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationItem(BaseModel):
    app: str
    package: str
    title: str
    text: str
    spoken_text: str
    reply_draft: str
    is_new: bool
    timestamp: str


@router.get("/read", response_model=list[NotificationItem])
async def read_notifications(speak: bool = True) -> list[dict]:
    """Read new important notifications and optionally speak them aloud.

    - Filters: WhatsApp, Telegram, Gmail, SMS, Phone calls.
    - New notifications (not seen before) are spoken via termux-tts-speak.
    - Already-read notifications are returned with is_new=false.
    """
    from app.ai.notification_reader_service import notification_reader_service  # lazy

    return await notification_reader_service.read_new_notifications(speak=speak)


@router.get("/list", response_model=list[NotificationItem])
async def list_notifications() -> list[dict]:
    """List all active important notifications without speaking.

    Returns the same structure as /read but never triggers TTS.
    """
    from app.ai.notification_reader_service import notification_reader_service  # lazy

    return await notification_reader_service.list_all_notifications()


@router.post("/cache/reset")
async def reset_notification_cache() -> dict:
    """Reset the dedup cache so all notifications will be treated as new on next read."""
    from app.ai.notification_reader_service import notification_reader_service  # lazy

    notification_reader_service.reset_cache()
    return {"success": True, "message": "Notification dedup cache cleared."}
