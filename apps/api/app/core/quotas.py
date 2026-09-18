"""Quota and Rate Limiting Enforcement Engine (Part 11).

Tracks per-user request rates and daily token limits to prevent abuse and API cost overruns.
"""

import time
import uuid
from typing import NamedTuple
from app.core.errors import RateLimitError

DEFAULT_RPM_LIMIT = 60  # 60 requests per minute
DEFAULT_DAILY_TOKEN_LIMIT = 150_000  # 150k tokens per day


class QuotaCheckResult(NamedTuple):
    allowed: bool
    current_tokens: int
    remaining_tokens: int
    requests_last_minute: int


class QuotaManager:
    """In-memory sliding window rate limiter and daily quota tracker."""

    def __init__(self):
        # user_id -> list of request timestamps in current window
        self._request_timestamps: dict[str, list[float]] = {}
        # user_id -> daily token count
        self._daily_tokens: dict[str, int] = {}
        self._last_reset_day = time.strftime("%Y-%m-%d")

    def _check_day_reset(self) -> None:
        today = time.strftime("%Y-%m-%d")
        if today != self._last_reset_day:
            self._daily_tokens.clear()
            self._last_reset_day = today

    def record_and_check(
        self,
        user_id: uuid.UUID,
        estimated_tokens: int = 0,
        rpm_limit: int = DEFAULT_RPM_LIMIT,
        daily_limit: int = DEFAULT_DAILY_TOKEN_LIMIT,
    ) -> QuotaCheckResult:
        """Check sliding window rate limits and daily quota. Raises RateLimitError if exceeded."""
        self._check_day_reset()
        uid = str(user_id)
        now = time.time()

        # 1. Sliding window RPM check
        window_start = now - 60.0
        timestamps = [t for t in self._request_timestamps.get(uid, []) if t > window_start]
        if len(timestamps) >= rpm_limit:
            raise RateLimitError(
                message=f"Request rate limit exceeded. Max {rpm_limit} requests/min.",
                retry_after_seconds=int(60.0 - (now - timestamps[0])),
            )

        # 2. Daily token limit check
        used_tokens = self._daily_tokens.get(uid, 0)
        if used_tokens + estimated_tokens > daily_limit:
            raise RateLimitError(
                message=f"Daily token quota exceeded ({used_tokens}/{daily_limit}).",
                retry_after_seconds=3600,
            )

        # Record request
        timestamps.append(now)
        self._request_timestamps[uid] = timestamps
        self._daily_tokens[uid] = used_tokens + estimated_tokens

        remaining = max(0, daily_limit - (used_tokens + estimated_tokens))
        return QuotaCheckResult(
            allowed=True,
            current_tokens=used_tokens + estimated_tokens,
            remaining_tokens=remaining,
            requests_last_minute=len(timestamps),
        )

    def get_quota_status(self, user_id: uuid.UUID, daily_limit: int = DEFAULT_DAILY_TOKEN_LIMIT) -> dict:
        self._check_day_reset()
        uid = str(user_id)
        used = self._daily_tokens.get(uid, 0)
        return {
            "daily_limit_tokens": daily_limit,
            "used_tokens": used,
            "remaining_tokens": max(0, daily_limit - used),
            "quota_percent_used": min(100.0, round((used / daily_limit) * 100, 2)),
        }


quota_manager = QuotaManager()
