"""Structured AI Request, Response, Usage, and Model types for Jenna AI."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Task classifications used by the ModelRouter to pick optimal models."""
    CHAT = "CHAT"
    REASONING = "REASONING"
    CODING = "CODING"
    ANALYSIS = "ANALYSIS"
    RESEARCH = "RESEARCH"          # Information synthesis & future search
    TOOL_REQUEST = "TOOL_REQUEST"  # Action & device commands (future MCP/tools)
    VISION = "VISION"              # Reserved for future phases
    TOOL_USE = "TOOL_USE"          # Alias/reserved for tool execution


class ModelCapability(str, Enum):
    """Specific capabilities supported by a given model."""
    STREAMING = "STREAMING"
    VISION = "VISION"
    TOOL_USE = "TOOL_USE"
    JSON_OUTPUT = "JSON_OUTPUT"
    SYSTEM_INSTRUCTION = "SYSTEM_INSTRUCTION"


class ChatMessage(BaseModel):
    """Single message in a conversational exchange."""
    role: str = Field(description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(description="Textual message content")

    model_config = {"extra": "ignore"}


class AIUsage(BaseModel):
    """Token consumption and usage metrics."""
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class AIRequest(BaseModel):
    """Normalized cross-provider AI completion request."""
    messages: list[ChatMessage] = Field(description="Sequential chat history ending in user prompt")
    system_instruction: str | None = Field(default=None, description="Optional system persona or instruction")
    model: str | None = Field(default=None, description="Specific model override or None for automatic routing")
    provider: str | None = Field(default=None, description="Specific provider override (e.g. 'gemini', 'openai')")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    task_type: TaskType = Field(default=TaskType.CHAT)
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    model_config = {"extra": "ignore"}


class AIResponse(BaseModel):
    """Normalized cross-provider AI completion response."""
    text: str = Field(description="Generated assistant text")
    provider: str = Field(description="Provider that fulfilled the request (e.g. 'gemini', 'openai')")
    model: str = Field(description="Model identifier that produced the completion")
    finish_reason: str = Field(default="stop")
    usage: AIUsage = Field(default_factory=AIUsage)
    request_id: str
    latency_ms: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "ignore"}


class AIStreamChunk(BaseModel):
    """Single token or delta emitted during a streaming completion."""
    delta: str = Field(default="")
    index: int = Field(default=0)
    finish_reason: str | None = None
    usage: AIUsage | None = None


class AIModelMetadata(BaseModel):
    """Descriptive metadata and capability specification for a model."""
    model_id: str
    provider: str
    display_name: str
    context_window: int
    capabilities: set[ModelCapability] = Field(default_factory=set)
    default_for_tasks: set[TaskType] = Field(default_factory=set)
    is_available: bool = True
