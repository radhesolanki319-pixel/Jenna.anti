import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sessions import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository handling Session database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Session, session)

    async def create_session(
        self,
        user_id: uuid.UUID,
        token_hash: str | None = None,
        expires_at: datetime | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """Create a new user session storing hashed token."""
        now = datetime.now(timezone.utc)
        target_token_hash = token_hash or uuid.uuid4().hex
        target_expires_at = expires_at or (now + timedelta(days=7))
        return await self.create(
            user_id=user_id,
            token_hash=target_token_hash,
            expires_at=target_expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=False,
        )

    async def get_valid_session(self, token_hash: str, current_time: datetime) -> Session | None:
        """Fetch an active, unexpired, non-revoked session including the user relation."""
        query = (
            select(Session)
            .options(selectinload(Session.user))
            .where(
                Session.token_hash == token_hash,
                Session.is_revoked.is_(False),
                Session.expires_at > current_time,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_session(self, token_hash: str) -> bool:
        """Revoke a specific session."""
        stmt = (
            update(Session)
            .where(Session.token_hash == token_hash)
            .values(is_revoked=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount > 0)  # type: ignore

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all active sessions for a user."""
        stmt = (
            update(Session)
            .where(Session.user_id == user_id, Session.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore

    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Session]:
        """Fetch all sessions belonging to a specific user."""
        query = (
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_expired(self, current_time: datetime) -> int:
        """Delete all expired sessions from database."""
        stmt = delete(Session).where(Session.expires_at < current_time)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore
