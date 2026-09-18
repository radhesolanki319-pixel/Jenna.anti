"""Repository for managing Conversation database entities."""

import uuid
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversations import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Data access layer for conversations with strict user scoping."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Conversation, session)

    async def get_user_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation | None:
        """Fetch a conversation ensuring strict user ownership isolation."""
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_user_conversations(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Conversation]:
        """Fetch paginated conversations for a user ordered by most recently updated."""
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create a new conversation thread owned by the user."""
        return await self.create(
            user_id=user_id,
            title=title.strip() or "New Conversation",
        )

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
    ) -> Conversation | None:
        """Update conversation title if owned by the user."""
        conv = await self.get_user_conversation(conversation_id, user_id)
        if not conv:
            return None
        conv.title = title.strip() or "Untitled Conversation"
        conv.updated_at = datetime.now(timezone.utc)
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    async def touch(self, conversation_id: uuid.UUID) -> None:
        """Update updated_at timestamp when a new message is appended."""
        conv = await self.get_by_id(conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            self.session.add(conv)
            await self.session.flush()

    async def delete_user_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a conversation if owned by the user, cascading messages."""
        conv = await self.get_user_conversation(conversation_id, user_id)
        if not conv:
            return False
        await self.delete(conv)
        return True
