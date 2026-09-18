"""Model Context Protocol (MCP) JSON-RPC 2.0 specifications and types."""

from dataclasses import dataclass, field
from typing import Any, Optional
from pydantic import BaseModel, Field

MCP_PROTOCOL_VERSION = "2024-11-05"


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 Request message."""
    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: Optional[dict[str, Any]] = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 Response message."""
    jsonrpc: str = "2.0"
    id: str | int
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None


class MCPToolSchema(BaseModel):
    """MCP standard tool definition object."""
    name: str
    description: str = ""
    inputSchema: dict[str, Any] = Field(default_factory=dict)


class MCPInitializeResult(BaseModel):
    """Server handshake capability response."""
    protocolVersion: str = MCP_PROTOCOL_VERSION
    capabilities: dict[str, Any] = Field(default_factory=dict)
    serverInfo: dict[str, Any] = Field(default_factory=dict)


class MCPCallToolResult(BaseModel):
    """Result returned by tools/call RPC."""
    content: list[dict[str, Any]] = Field(default_factory=list)
    isError: bool = False
