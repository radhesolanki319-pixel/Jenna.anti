"""Schemas for memory CRUD, semantic search, working memory, lifecycle, and extraction."""

from datetime import datetime
import enum
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.memory import MemorySource, MemoryStatus, MemoryType


class SensitivityClassification(str, enum.Enum):
    """Sensitivity classification for privacy protection."""

    SAFE = "SAFE"
    SENSITIVE_CREDENTIAL = "SENSITIVE_CREDENTIAL"
    SENSITIVE_PERSONAL = "SENSITIVE_PERSONAL"
    HIGH_RISK = "HIGH_RISK"


class CandidateAction(str, enum.Enum):
    """Suggested policy action for an extracted candidate memory."""

    STORE = "STORE"
    SUPERSEDE = "SUPERSEDE"
    CONFIRM = "CONFIRM"
    IGNORE = "IGNORE"


class FeedbackType(str, enum.Enum):
    """User feedback options for memory management."""

    USEFUL = "USEFUL"
    INCORRECT = "INCORRECT"
    OUTDATED = "OUTDATED"
    FORGET = "FORGET"
    EDIT = "EDIT"


class MemoryCreateRequest(BaseModel):
    """Payload for creating a new memory."""

    content: str = Field(..., min_length=1, max_length=50000, description="Memory text content")
    memory_type: MemoryType = Field(default=MemoryType.FACT, description="Category of memory")
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE, description="Lifecycle status")
    summary: str | None = Field(default=None, max_length=1000, description="Optional brief summary")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance weight [0.0 - 1.0]")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Extraction confidence [0.0 - 1.0]")
    source: str = Field(default=MemorySource.MANUAL.value, max_length=64, description="Origin source")
    conversation_id: uuid.UUID | None = Field(default=None, description="Optional associated conversation")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata payload")


class MemoryUpdateRequest(BaseModel):
    """Payload for updating an existing memory."""

    content: str | None = Field(default=None, min_length=1, max_length=50000)
    summary: str | None = Field(default=None, max_length=1000)
    memory_type: MemoryType | None = None
    status: MemoryStatus | None = None
    superseded_by_id: uuid.UUID | None = None
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] | None = None


class MemoryResponse(BaseModel):
    """Serialized memory record returned to client."""

    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    superseded_by_id: uuid.UUID | None = None
    status: str
    memory_type: str
    content: str
    summary: str | None = None
    importance: float
    confidence: float
    source: str
    metadata: dict[str, Any]
    has_embedding: bool
    archived_at: datetime | None = None
    last_accessed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, mem: Any) -> "MemoryResponse":
        meta = getattr(mem, "metadata_", None)
        if not isinstance(meta, dict):
            raw_meta = getattr(mem, "metadata", None)
            meta = raw_meta if isinstance(raw_meta, dict) else {}

        return cls(
            id=getattr(mem, "id", getattr(mem, "memory_id", None)),
            user_id=getattr(mem, "user_id", None),
            conversation_id=getattr(mem, "conversation_id", None),
            superseded_by_id=getattr(mem, "superseded_by_id", None),
            status=getattr(mem, "status", MemoryStatus.ACTIVE.value),
            memory_type=getattr(mem, "memory_type", MemoryType.FACT.value),
            content=getattr(mem, "content", ""),
            summary=getattr(mem, "summary", None),
            importance=getattr(mem, "importance", 0.5),
            confidence=getattr(mem, "confidence", 0.8),
            source=getattr(mem, "source", MemorySource.MANUAL.value),
            metadata=meta,
            has_embedding=getattr(mem, "has_embedding", bool(getattr(mem, "embedding", None) is not None)),
            archived_at=getattr(mem, "archived_at", None),
            last_accessed_at=getattr(mem, "last_accessed_at", datetime.now()),
            created_at=getattr(mem, "created_at", datetime.now()),
            updated_at=getattr(mem, "updated_at", datetime.now()),
        )


class MemoryListResponse(BaseModel):
    """Paginated list of memories."""

    items: list[MemoryResponse]
    total: int
    limit: int
    offset: int


class MemorySearchRequest(BaseModel):
    """Payload for semantic similarity memory search."""

    query: str = Field(..., min_length=1, max_length=5000, description="Natural language search query")
    limit: int = Field(default=5, ge=1, le=50, description="Max memory items to return")
    threshold: float = Field(default=0.35, ge=0.0, le=1.0, description="Minimum relevance threshold")
    memory_types: list[str] | None = Field(default=None, description="Filter to specific memory types")
    statuses: list[str] | None = Field(default=None, description="Filter to specific statuses (default ACTIVE)")


class MemorySearchResultItemResponse(BaseModel):
    """Matched memory item with compound score and breakdown."""

    memory: MemoryResponse
    score: float
    breakdown: dict[str, float]


class MemorySearchResponse(BaseModel):
    """Response payload for semantic search."""

    query: str
    results: list[MemorySearchResultItemResponse]
    count: int


class WorkingMemorySetRequest(BaseModel):
    """Payload for setting an ephemeral working memory item."""

    key: str = Field(..., min_length=1, max_length=128)
    value: Any
    ttl_seconds: int = Field(default=86400, ge=1, le=2592000)  # Up to 30 days
    conversation_id: str | None = None


class WorkingMemoryResponse(BaseModel):
    """Current working memory dictionary."""

    items: dict[str, Any]


class MemoryCandidate(BaseModel):
    """Extracted memory candidate before persistence."""

    content: str = Field(..., min_length=1, max_length=5000)
    memory_type: str = Field(default=MemoryType.FACT.value)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    reason: str = Field(default="", max_length=500)
    source: str = Field(default=MemorySource.USER_CONVERSATION.value)
    sensitivity: SensitivityClassification = Field(default=SensitivityClassification.SAFE)
    suggested_action: CandidateAction = Field(default=CandidateAction.STORE)
    supersedes_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None


class MemoryExtractRequest(BaseModel):
    """Request to extract candidate memories from a text or conversation turn."""

    content: str = Field(..., min_length=1, max_length=20000, description="Text or conversation snippet to analyze")
    conversation_id: uuid.UUID | None = None


class MemoryExtractResponse(BaseModel):
    """Extracted candidate memories list."""

    candidates: list[MemoryCandidate]
    count: int


class MemoryConfirmRequest(BaseModel):
    """User confirmation payload for candidate or suggested memory."""

    candidate: MemoryCandidate
    confirm: bool = Field(default=True, description="True to save as ACTIVE memory, False to reject")


class MemoryFeedbackRequest(BaseModel):
    """User feedback for a specific memory record."""

    feedback_type: FeedbackType
    comment: str | None = Field(default=None, max_length=1000)
    updated_content: str | None = Field(default=None, max_length=5000)


class MemoryActionResponse(BaseModel):
    """General action response for memory operations (archive, restore, feedback)."""

    status: str
    message: str
    memory: MemoryResponse | None = None
