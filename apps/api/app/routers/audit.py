"""Audit Explorer API Router.

Provides secure, user-scoped querying and statistics for audit events.
Strictly ensures no secrets, tokens, or credentials are leaked.
"""

import uuid
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import Role
from app.models.users import User
from app.repositories.audit_repo import AuditEventRepository
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Explorer"])


class AuditEventResponse(BaseModel):
    """Schema representing an audit trail event."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    event_type: str
    action: str
    success: bool
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)



class AuditStatsResponse(BaseModel):
    """Aggregated statistics for audit events."""

    total_events: int
    successful_events: int
    failed_events: int


@router.get("/events", response_model=list[AuditEventResponse], summary="List audit events")
async def list_audit_events(
    event_type: str | None = Query(default=None, description="Filter by event type"),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditEventResponse]:
    """Retrieve audit trail logs.

    Non-admin users can strictly only see events associated with their own user account.
    Admin users can query events across the system.
    """
    repo = AuditEventRepository(db)
    user_filter = None if current_user.role == Role.ADMIN.value else current_user.id
    events = await repo.list_filtered(
        user_id=user_filter,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    return [AuditEventResponse.model_validate(e) for e in events]


@router.get("/stats", response_model=AuditStatsResponse, summary="Get audit statistics")
async def get_audit_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditStatsResponse:
    """Get aggregated event counts and success rates."""
    repo = AuditEventRepository(db)
    user_filter = None if current_user.role == Role.ADMIN.value else current_user.id
    stats = await repo.get_stats(user_id=user_filter)
    return AuditStatsResponse(**stats)
