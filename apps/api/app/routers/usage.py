"""Usage and Cost Visibility API Router.

Tracks LLM token consumption, latency benchmarks, estimated costs, and daily rate quotas.
"""

import uuid
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.users import User
from app.repositories.ai_usage_repo import AIUsageRepository
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/usage", tags=["Usage & Cost Visibility"])

DEFAULT_DAILY_QUOTA = 150_000  # 150k tokens / day default allocation


class UsageSummaryResponse(BaseModel):
    """Consolidated token usage, latency, and cost telemetry."""

    total_requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    avg_latency_ms: float
    estimated_cost_usd: float
    daily_quota_tokens: int
    quota_remaining_tokens: int
    quota_percent_used: float


class UsageLogEntry(BaseModel):
    """Telemetry item for an individual AI provider request."""

    id: uuid.UUID
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    success: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



@router.get("/summary", response_model=UsageSummaryResponse, summary="Get token and cost summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageSummaryResponse:
    """Calculates aggregated token usage and estimated costs for the user."""
    repo = AIUsageRepository(db)
    summary = await repo.get_summary_for_user(current_user.id)

    prompt = summary["prompt_tokens"]
    comp = summary["completion_tokens"]
    total = summary["total_tokens"]

    # Blended estimate: ~$0.50 per 1M prompt tokens, ~$1.50 per 1M completion tokens
    cost_usd = round((prompt * 0.0000005) + (comp * 0.0000015), 5)
    remaining = max(0, DEFAULT_DAILY_QUOTA - total)
    pct_used = min(100.0, round((total / DEFAULT_DAILY_QUOTA) * 100, 1))

    return UsageSummaryResponse(
        total_requests=summary["total_requests"],
        prompt_tokens=prompt,
        completion_tokens=comp,
        total_tokens=total,
        avg_latency_ms=summary["avg_latency_ms"],
        estimated_cost_usd=cost_usd,
        daily_quota_tokens=DEFAULT_DAILY_QUOTA,
        quota_remaining_tokens=remaining,
        quota_percent_used=pct_used,
    )


@router.get("/logs", response_model=list[UsageLogEntry], summary="Recent usage logs")
async def get_recent_usage_logs(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UsageLogEntry]:
    """List recent AI generation telemetry records."""
    repo = AIUsageRepository(db)
    logs = await repo.list_recent(user_id=current_user.id, limit=limit)
    return [UsageLogEntry.model_validate(log) for log in logs]
