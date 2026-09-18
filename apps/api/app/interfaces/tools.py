"""Future Domain Interface: ToolExecutor

Defines the contract for tool discovery, validation, MCP protocol, and execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ToolParameter:
    """Specification of a single parameter accepted by a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolDefinition:
    """Schema defining a tool callable by Jenna agents or workflows."""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    category: str = "general"
    requires_permission: str | None = None
    is_sensitive: bool = False


@dataclass
class ToolResult:
    """Structured result returned by a tool execution."""
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ToolExecutor(ABC):
    """Abstract interface contract for tool discovery and execution."""

    @abstractmethod
    def discover_tools(self) -> list[ToolDefinition]:
        """List all available tools registered with the platform."""
        pass

    @abstractmethod
    def validate_call(self, tool_name: str, parameters: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate whether parameter arguments adhere to the tool's schema."""
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: str | None = None,
        permissions: set[str] | None = None,
    ) -> ToolResult:
        """Execute tool with permission checking and structured output."""
        pass
