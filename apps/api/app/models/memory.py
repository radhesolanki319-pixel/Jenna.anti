"""Memory models for persistent semantic and episodic vector memory."""

import enum
import uuid
from datetime import datetime
from typing import Any
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


class MemoryType(str, enum.Enum):
    """Categorization for long-term and working memories."""

    FACT = "FACT"
    PREFERENCE = "PREFERENCE"
    PERSONAL_CONTEXT = "PERSONAL_CONTEXT"
    INSTRUCTION = "INSTRUCTION"
    CONVERSATION_SUMMARY = "CONVERSATION_SUMMARY"
    TASK_CONTEXT = "TASK_CONTEXT"
    TEMPORARY = "TEMPORARY"


class MemoryStatus(str, enum.Enum):
    """Lifecycle status of a memory record."""

    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class MemorySource(str, enum.Enum):
    """Origin source of a memory record."""

    USER_EXPLICIT = "USER_EXPLICIT"
    USER_CONVERSATION = "USER_CONVERSATION"
    SYSTEM = "SYSTEM"
    IMPORTED = "IMPORTED"
    MANUAL = "MANUAL"


class Memory(Base):
    """Represents an individual persistent long-term or contextual memory."""

    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("memories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MemoryStatus.ACTIVE.value,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MemoryType.FACT.value,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    importance: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
    )  # Range [0.0 - 1.0]
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.8,
        nullable=False,
    )  # Range [0.0 - 1.0]
    source: Mapped[str] = mapped_column(
        String(64),
        default=MemorySource.MANUAL.value,
        nullable=False,
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="memories")
    conversation = relationship("Conversation", backref="memories")
    superseded_by = relationship("Memory", remote_side=[id], backref="superseded_memories")

    __table_args__ = (
        Index("ix_memories_user_type", "user_id", "memory_type"),
        Index("ix_memories_user_status", "user_id", "status"),
        Index("ix_memories_user_type_status", "user_id", "memory_type", "status"),
        Index("ix_memories_user_created", "user_id", "created_at"),
        Index("ix_memories_user_accessed", "user_id", "last_accessed_at"),
        Index(
            "ix_memories_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

