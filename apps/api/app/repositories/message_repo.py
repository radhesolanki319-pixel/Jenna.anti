"""Repository for managing Message database entities."""

import uuid
from typing import Any, Sequence
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversations import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Data access layer for conversation messages."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Message, session)

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        model: str | None = None,
        provider: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Create and persist a message in a conversation thread."""
        return await self.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            provider=provider,
            metadata_=metadata or {},
        )

    async def list_conversation_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Message]:
        """List messages in chronological order (oldest first)."""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(asc(Message.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 20,
    ) -> list[Message]:
        """Fetch the most recent N messages, returned in chronological order."""
        # Query newest first to grab the latest N, then reverse to chronological
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def count_messages(self, conversation_id: uuid.UUID) -> int:
        """Count total messages in a conversation."""
        query = select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
        result = await self.session.execute(query)
        return result.scalar_one() or 0
