"""Data types and schemas for Jenna Tools, MCP, and Web Research."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.core.permissions import Permission


class ToolCategory(str, Enum):
    """Categorical classification of tools."""
    GENERAL = "GENERAL"
    CALCULATOR = "CALCULATOR"
    FILESYSTEM = "FILESYSTEM"
    WEB = "WEB"
    SYSTEM = "SYSTEM"
    MCP = "MCP"


class ToolAuthorizationTier(str, Enum):
    """Evaluation tiers for tool invocation authorization."""
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"


class ToolParameterSchema(BaseModel):
    """Specification of a single parameter accepted by a tool."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(default="string", description="JSON schema type: string, number, integer, boolean, array, object")
    description: str = Field(default="", description="Description of what this argument controls")
    required: bool = Field(default=True, description="Whether this parameter is mandatory")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    enum_values: Optional[list[str]] = Field(default=None, description="Optional restricted choices")


class ToolDefinitionSchema(BaseModel):
    """Complete metadata and schema defining a callable tool."""
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Description provided to LLM router")
    category: ToolCategory = Field(default=ToolCategory.GENERAL)
    parameters: list[ToolParameterSchema] = Field(default_factory=list)
    requires_permission: Optional[Permission] = Field(default=None)
    is_sensitive: bool = Field(default=False, description="True if action mutates state or requires user confirmation")
    timeout_seconds: float = Field(default=30.0, ge=0.01, le=300.0)
    output_max_chars: int = Field(default=10000, ge=10, le=100000)


class ToolCallRequest(BaseModel):
    """Request payload for executing a tool."""
    tool_name: str = Field(..., min_length=1, max_length=100)
    parameters: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = Field(default=False, description="User confirmation flag for sensitive actions")


class ToolExecutionResult(BaseModel):
    """Outcome and artifacts produced by a tool execution."""
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    truncated: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requires_confirmation: bool = False
    confirmation_reason: Optional[str] = None


class WebSearchResult(BaseModel):
    """A single web search result source."""
    title: str
    url: str
    snippet: str
    domain: str = ""
    published_date: Optional[str] = None
    score: float = 0.0


class Citation(BaseModel):
    """Referenced source citation in synthesized research."""
    index: int
    title: str
    url: str
    snippet: str
    source_verified: bool = True


class ResearchRequest(BaseModel):
    """Input query for multi-step web research."""
    query: str = Field(..., min_length=3, max_length=500, description="The topic or question to research")
    max_sources: int = Field(default=4, ge=1, le=10)
    depth: str = Field(default="standard", description="standard or deep")


class ResearchResponse(BaseModel):
    """Synthesized research outcome with verified sources."""
    query: str
    synthesis: str
    sources_collected: int
    sources_read: int
    citations: list[Citation]
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
