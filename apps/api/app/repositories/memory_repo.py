"""Repository for user-isolated memory persistence, lifecycle management, and vector similarity search."""

from datetime import datetime, timezone
from typing import Any, Sequence
import uuid
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, MemorySource, MemoryStatus, MemoryType


class MemoryRepository:
    """Handles CRUD, lifecycle transitions, and vector similarity retrieval for persistent memories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_memory(
        self,
        user_id: uuid.UUID,
        memory_type: str,
        content: str,
        summary: str | None = None,
        importance: float = 0.5,
        confidence: float = 0.8,
        source: str = MemorySource.MANUAL.value,
        status: str = MemoryStatus.ACTIVE.value,
        conversation_id: uuid.UUID | None = None,
        superseded_by_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
        archived_at: datetime | None = None,
    ) -> Memory:
        """Create and persist a new user memory."""
        mem = Memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            summary=summary,
            importance=max(0.0, min(1.0, float(importance))),
            confidence=max(0.0, min(1.0, float(confidence))),
            source=source,
            status=status,
            conversation_id=conversation_id,
            superseded_by_id=superseded_by_id,
            archived_at=archived_at,
            metadata_=metadata or {},
            embedding=embedding,
            last_accessed_at=datetime.now(timezone.utc),
        )
        self.session.add(mem)
        await self.session.flush()
        return mem

    async def get_memory(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Memory | None:
        """Fetch memory ensuring strict user ownership isolation and excluding deleted by default."""
        stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(Memory.status != MemoryStatus.DELETED.value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_memories(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        min_importance: float | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> tuple[Sequence[Memory], int]:
        """Fetch paginated memories with optional type, status, search, and importance filters."""
        stmt = select(Memory).where(Memory.user_id == user_id)
        count_stmt = select(func.count()).select_from(Memory).where(Memory.user_id == user_id)

        # Status filtering
        if not include_deleted:
            stmt = stmt.where(Memory.status != MemoryStatus.DELETED.value)
            count_stmt = count_stmt.where(Memory.status != MemoryStatus.DELETED.value)

        if status and status.upper() != "ALL":
            stmt = stmt.where(Memory.status == status.upper())
            count_stmt = count_stmt.where(Memory.status == status.upper())

        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
            count_stmt = count_stmt.where(Memory.memory_type == memory_type)

        if search and search.strip():
            term = f"%{search.strip()}%"
            filter_expr = Memory.content.ilike(term) | Memory.summary.ilike(term)
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        if min_importance is not None:
            stmt = stmt.where(Memory.importance >= min_importance)
            count_stmt = count_stmt.where(Memory.importance >= min_importance)

        stmt = stmt.order_by(Memory.created_at.desc()).limit(limit).offset(offset)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        items_res = await self.session.execute(stmt)
        items = items_res.scalars().all()

        return items, total

    async def update_memory(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str | None = None,
        summary: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        superseded_by_id: uuid.UUID | None = None,
        importance: float | None = None,
        confidence: float | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
        archived_at: datetime | None = None,
    ) -> Memory | None:
        """Update existing memory record preserving user isolation."""
        mem = await self.get_memory(memory_id=memory_id, user_id=user_id, include_deleted=True)
        if not mem:
            return None

        if content is not None:
            mem.content = content
        if summary is not None:
            mem.summary = summary
        if memory_type is not None:
            mem.memory_type = memory_type
        if status is not None:
            mem.status = status
        if superseded_by_id is not None:
            mem.superseded_by_id = superseded_by_id
        if importance is not None:
            mem.importance = max(0.0, min(1.0, float(importance)))
        if confidence is not None:
            mem.confidence = max(0.0, min(1.0, float(confidence)))
        if source is not None:
            mem.source = source
        if metadata is not None:
            mem.metadata_ = metadata
        if embedding is not None:
            mem.embedding = embedding
        if archived_at is not None:
            mem.archived_at = archived_at

        mem.updated_at = datetime.now(timezone.utc)
        self.session.add(mem)
        await self.session.flush()
        return mem

    async def archive_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory | None:
        """Archive a memory record."""
        mem = await self.get_memory(memory_id=memory_id, user_id=user_id)
        if not mem:
            return None
        mem.status = MemoryStatus.ARCHIVED.value
        mem.archived_at = datetime.now(timezone.utc)
        mem.updated_at = datetime.now(timezone.utc)
        self.session.add(mem)
        await self.session.flush()
        return mem

    async def restore_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory | None:
        """Restore an archived or superseded memory back to ACTIVE."""
        mem = await self.get_memory(memory_id=memory_id, user_id=user_id)
        if not mem:
            return None
        mem.status = MemoryStatus.ACTIVE.value
        mem.archived_at = None
        mem.superseded_by_id = None
        mem.updated_at = datetime.now(timezone.utc)
        self.session.add(mem)
        await self.session.flush()
        return mem

    async def soft_delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Mark memory as DELETED preserving audit trail while preventing retrieval."""
        mem = await self.get_memory(memory_id=memory_id, user_id=user_id)
        if not mem:
            return False
        mem.status = MemoryStatus.DELETED.value
        mem.updated_at = datetime.now(timezone.utc)
        self.session.add(mem)
        await self.session.flush()
        return True

    async def delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Soft-delete memory record ensuring strict user isolation."""
        return await self.soft_delete_memory(memory_id=memory_id, user_id=user_id)

    async def touch_accessed(self, memory_ids: list[uuid.UUID], user_id: uuid.UUID) -> None:
        """Batch update last_accessed_at timestamp."""
        if not memory_ids:
            return
        stmt = (
            update(Memory)
            .where(Memory.id.in_(memory_ids), Memory.user_id == user_id)
            .values(last_accessed_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False)
        )
        await self.session.execute(stmt)

    async def search_vector_similarity(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 10,
        memory_types: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> list[tuple[Memory, float]]:
        """Perform vector cosine similarity search in pgvector.

        Only retrieves non-deleted memories, defaulting strictly to ACTIVE status.
        """
        active_statuses = statuses or [MemoryStatus.ACTIVE.value]
        distance_expr = Memory.embedding.cosine_distance(query_embedding)
        stmt = (
            select(Memory, distance_expr.label("distance"))
            .where(Memory.user_id == user_id)
            .where(Memory.embedding.is_not(None))
            .where(Memory.status.in_(active_statuses))
        )
        if memory_types:
            stmt = stmt.where(Memory.memory_type.in_(memory_types))

        stmt = stmt.order_by(distance_expr.asc()).limit(limit)

        result = await self.session.execute(stmt)
        rows = result.all()

        scored: list[tuple[Memory, float]] = []
        for mem, dist in rows:
            sim = max(0.0, min(1.0, 1.0 - float(dist if dist is not None else 1.0)))
            scored.append((mem, sim))

        return scored
