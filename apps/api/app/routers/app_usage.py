"""App Usage Intelligence API Router.

Provides endpoints for Android app usage tracking, digital wellbeing
summaries, and background tracking control.

Prefix: /api/v1/app-usage
Tag:    Usage Intelligence
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

try:
    from app.ai.usage_intelligence_service import get_usage_intelligence_service
except ImportError as _e:
    get_usage_intelligence_service = None  # type: ignore[assignment]
    logging.getLogger(__name__).warning("UsageIntelligenceService unavailable: %s", _e)

router = APIRouter(prefix="/app-usage", tags=["Usage Intelligence"])

logger = logging.getLogger(__name__)


def _svc():
    """Return the service singleton or raise 503."""
    if get_usage_intelligence_service is None:
        raise HTTPException(503, "UsageIntelligenceService is not available.")
    return get_usage_intelligence_service()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/today",
    summary="Today's app usage summary",
    response_model=None,
)
async def get_today_summary() -> dict[str, Any]:
    """Return today's Android app usage summary including top apps and warnings.

    Response fields:
    - **total_screen_time_min** — total tracked screen time today in minutes
    - **top_apps** — list of `{package, label, minutes, percentage}`
    - **warnings_issued** — wellbeing warnings that fired today
    - **as_of** — ISO timestamp of when this data was generated
    """
    try:
        return _svc().get_today_summary()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get today's summary: %s", exc)
        raise HTTPException(500, f"Failed to get usage summary: {exc}") from exc


@router.get(
    "/history",
    summary="Session history",
    response_model=None,
)
async def get_session_history(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to return"),
) -> list[dict[str, Any]]:
    """Return individual app session records for the last *hours* hours.

    Each record contains `package`, `label`, `start_time`, `end_time`, and `duration_sec`.
    """
    try:
        return _svc().get_session_history(hours=hours)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get session history: %s", exc)
        raise HTTPException(500, f"Failed to get session history: {exc}") from exc


@router.post(
    "/tracking/start",
    summary="Start background app usage tracking",
    status_code=200,
)
async def start_tracking() -> dict[str, str]:
    """Start the background ADB polling loop (every 60 seconds)."""
    try:
        _svc().start_tracking()
        return {"status": "ok", "message": "App usage tracking started."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to start tracking: %s", exc)
        raise HTTPException(500, f"Failed to start tracking: {exc}") from exc


@router.post(
    "/tracking/stop",
    summary="Stop background app usage tracking",
    status_code=200,
)
async def stop_tracking() -> dict[str, str]:
    """Stop the background ADB polling loop and flush any open session."""
    try:
        _svc().stop_tracking()
        return {"status": "ok", "message": "App usage tracking stopped."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to stop tracking: %s", exc)
        raise HTTPException(500, f"Failed to stop tracking: {exc}") from exc
