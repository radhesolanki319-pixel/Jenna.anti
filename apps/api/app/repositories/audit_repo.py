import uuid
from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import sanitize_audit_metadata
from app.models.audit_events import AuditEvent
from app.repositories.base import BaseRepository


class AuditEventRepository(BaseRepository[AuditEvent]):
    """Repository handling AuditEvent database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditEvent, session)

    async def log_event(
        self,
        event_type: str,
        action: str = "EXECUTE",
        success: bool = True,
        user_id: uuid.UUID | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> AuditEvent:
        """Record an audit event with sanitized metadata."""
        meta = dict(metadata or {})
        if resource_type:
            meta["resource_type"] = resource_type
        if resource_id:
            meta["resource_id"] = resource_id
        sanitized_metadata = sanitize_audit_metadata(meta)
        return await self.create(
            event_type=event_type,
            action=action,
            success=success,
            user_id=user_id,
            request_id=request_id,
            metadata_json=sanitized_metadata,
        )

    async def list_recent(self, limit: int = 50) -> Sequence[AuditEvent]:
        """Fetch the most recent audit events."""
        query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_user(self, user_id: uuid.UUID, limit: int = 50) -> Sequence[AuditEvent]:
        """Fetch audit events associated with a specific user."""
        query = (
            select(AuditEvent)
            .where(AuditEvent.user_id == user_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_filtered(
        self,
        user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[AuditEvent]:
        """Fetch filtered audit events with pagination."""
        query = select(AuditEvent)
        if user_id is not None:
            query = query.where(AuditEvent.user_id == user_id)
        if event_type:
            query = query.where(AuditEvent.event_type == event_type)
        query = query.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_stats(self, user_id: uuid.UUID | None = None) -> dict[str, Any]:
        """Compute aggregated audit statistics."""
        from sqlalchemy import func
        total_q = select(func.count(AuditEvent.id))
        success_q = select(func.count(AuditEvent.id)).where(AuditEvent.success == True)
        if user_id is not None:
            total_q = total_q.where(AuditEvent.user_id == user_id)
            success_q = success_q.where(AuditEvent.user_id == user_id)

        total_res = await self.session.execute(total_q)
        success_res = await self.session.execute(success_q)
        total = total_res.scalar_one() or 0
        success_count = success_res.scalar_one() or 0

        return {
            "total_events": total,
            "successful_events": success_count,
            "failed_events": max(0, total - success_count),
        }

