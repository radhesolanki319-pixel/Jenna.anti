"""Repository for AI token usage and latency tracking."""

import uuid
from typing import Any, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage import AIUsageLog
from app.repositories.base import BaseRepository


class AIUsageRepository(BaseRepository[AIUsageLog]):
    """Repository handling AIUsageLog database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AIUsageLog, session)

    async def log_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        user_id: uuid.UUID | None = None,
        request_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AIUsageLog:
        """Record an AI request usage telemetry row."""
        return await self.create(
            user_id=user_id,
            request_id=request_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens or (prompt_tokens + completion_tokens),
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
        )

    async def get_summary_for_user(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Aggregate total token usage and call count for a specific user."""
        query = select(
            func.count(AIUsageLog.id).label("total_requests"),
            func.coalesce(func.sum(AIUsageLog.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(AIUsageLog.completion_tokens), 0).label("completion_tokens"),
            func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.avg(AIUsageLog.latency_ms), 0.0).label("avg_latency_ms"),
        ).where(AIUsageLog.user_id == user_id)

        result = await self.session.execute(query)
        row = result.one()
        return {
            "total_requests": row.total_requests,
            "prompt_tokens": int(row.prompt_tokens),
            "completion_tokens": int(row.completion_tokens),
            "total_tokens": int(row.total_tokens),
            "avg_latency_ms": round(float(row.avg_latency_ms), 2),
        }

    async def list_recent(self, user_id: uuid.UUID | None = None, limit: int = 50) -> Sequence[AIUsageLog]:
        """Fetch the most recent usage records."""
        query = select(AIUsageLog).order_by(AIUsageLog.created_at.desc()).limit(limit)
        if user_id is not None:
            query = query.where(AIUsageLog.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
