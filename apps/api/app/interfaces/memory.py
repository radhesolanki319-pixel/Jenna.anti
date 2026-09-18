"""Future Domain Interface: MemoryProvider

Defines the contract for episodic, working, and semantic vector memory.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class MemoryRecord:
    """Individual memory item stored in the memory system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    user_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemorySearchResult:
    """Result of a semantic search query with relevance score."""
    record: MemoryRecord
    score: float  # Cosine similarity score [0.0 - 1.0]


class MemoryProvider(ABC):
    """Abstract interface contract for Jenna's persistent long-term and working memory."""

    @abstractmethod
    async def store(
        self,
        key: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> MemoryRecord:
        """Store a new memory item."""
        pass

    @abstractmethod
    async def retrieve(self, memory_id: str) -> MemoryRecord | None:
        """Fetch memory item by its unique ID."""
        pass

    @abstractmethod
    async def update(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """Update existing memory content and metadata."""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item."""
        pass

    @abstractmethod
    async def search_semantic(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        user_id: str | None = None,
    ) -> list[MemorySearchResult]:
        """Perform vector embedding similarity search across stored memories."""
        pass
