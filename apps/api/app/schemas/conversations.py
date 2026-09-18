"""Pydantic schemas for Conversation and Message API contracts."""

from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, Field

from app.ai.types import TaskType


class ConversationCreate(BaseModel):
    """Payload to initialize a new conversation thread."""

    title: str = Field(default="New Conversation", max_length=255)


class ConversationUpdate(BaseModel):
    """Payload to update conversation metadata (e.g. rename title)."""

    title: str = Field(min_length=1, max_length=255)


class MessageRead(BaseModel):
    """Representation of a persisted message in a conversation."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    model: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ConversationRead(BaseModel):
    """Metadata summary of a conversation thread."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailRead(BaseModel):
    """Detailed conversation payload including recent messages."""

    conversation: ConversationRead
    messages: list[MessageRead]
    total_messages: int


class SendMessageRequest(BaseModel):
    """Payload for submitting a user message to an active conversation thread."""

    content: str = Field(min_length=1, description="User prompt text")
    model: str | None = Field(default=None, description="Optional model override")
    provider: str | None = Field(default=None, description="Optional provider override")
    web_search: bool = Field(default=False, description="Enable live web search augmentation")
    deep_research: bool = Field(default=False, description="Enable multi-step deep research synthesis")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="Attached file payloads")
    personal_intelligence: bool = Field(default=True, description="Enable long-term personal memory recall")
    persona: str | None = Field(default=None, description="Optional active persona system style")



class SendMessageResponse(BaseModel):
    """Complete response returned from synchronous message reasoning."""

    user_message: MessageRead
    assistant_message: MessageRead
    task_type: TaskType
    provider: str
    model: str
    latency_ms: float
