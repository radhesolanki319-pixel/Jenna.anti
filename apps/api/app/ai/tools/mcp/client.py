"""Model Context Protocol (MCP) Client Abstraction with Mock and Transport Support."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from app.ai.tools.mcp.protocol import (
    MCP_PROTOCOL_VERSION,
    JsonRpcRequest,
    JsonRpcResponse,
    MCPCallToolResult,
    MCPInitializeResult,
    MCPToolSchema,
)
from app.ai.tools.types import (
    ToolCategory,
    ToolDefinitionSchema,
    ToolParameterSchema,
)

logger = logging.getLogger("jenna.mcp")


class MCPTransport(ABC):
    """Abstract communication channel to an external MCP server."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish channel to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    async def send_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Send JSON-RPC request and await response."""
        pass


class MockMCPTransport(MCPTransport):
    """Deterministic in-memory mock MCP transport for testing."""

    def __init__(self, server_name: str = "MockMCPTestServer", mock_tools: list[MCPToolSchema] | None = None):
        self.server_name = server_name
        self.is_connected = False
        self._tools = mock_tools or [
            MCPToolSchema(
                name="mock_weather_lookup",
                description="Get weather condition for a city.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "Name of the target city"},
                    },
                    "required": ["city"],
                },
            ),
            MCPToolSchema(
                name="mock_git_status",
                description="Retrieve clean git status of a repository.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Path to local git repo"},
                    },
                    "required": ["repo_path"],
                },
            ),
        ]
        self._tool_handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "mock_weather_lookup": lambda params: {
                "city": params.get("city"),
                "temperature_c": 22.5,
                "condition": "Partly Cloudy",
                "humidity": 65,
            },
            "mock_git_status": lambda params: {
                "branch": "main",
                "clean": True,
                "ahead": 0,
                "behind": 0,
            },
        }

    async def connect(self) -> None:
        self.is_connected = True

    async def disconnect(self) -> None:
        self.is_connected = False

    def register_tool(self, schema: MCPToolSchema, handler: Callable[[dict[str, Any]], Any]) -> None:
        self._tools.append(schema)
        self._tool_handlers[schema.name] = handler

    async def send_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        if not self.is_connected:
            return JsonRpcResponse(
                id=request.id,
                error={"code": -32000, "message": "Transport not connected"},
            )

        if request.method == "initialize":
            init_res = MCPInitializeResult(
                protocolVersion=MCP_PROTOCOL_VERSION,
                capabilities={"tools": {"listChanged": True}},
                serverInfo={"name": self.server_name, "version": "1.0.0"},
            )
            return JsonRpcResponse(id=request.id, result=init_res.model_dump())

        elif request.method == "tools/list":
            tools_list = [t.model_dump() for t in self._tools]
            return JsonRpcResponse(id=request.id, result={"tools": tools_list})

        elif request.method == "tools/call":
            params = request.params or {}
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if tool_name not in self._tool_handlers:
                return JsonRpcResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Method/Tool '{tool_name}' not found"},
                )

            try:
                handler = self._tool_handlers[tool_name]
                out = handler(tool_args)
                result = MCPCallToolResult(
                    content=[{"type": "text", "text": json.dumps(out)}],
                    isError=False,
                )
                return JsonRpcResponse(id=request.id, result=result.model_dump())
            except Exception as exc:
                result = MCPCallToolResult(
                    content=[{"type": "text", "text": str(exc)}],
                    isError=True,
                )
                return JsonRpcResponse(id=request.id, result=result.model_dump())

        return JsonRpcResponse(
            id=request.id,
            error={"code": -32601, "message": f"Unknown method: {request.method}"},
        )


class MCPClient:
    """Client for interacting with Model Context Protocol (MCP) servers."""

    def __init__(self, transport: MCPTransport, client_name: str = "JennaMCPClient"):
        self.transport = transport
        self.client_name = client_name
        self.server_info: dict[str, Any] = {}
        self.server_capabilities: dict[str, Any] = {}
        self.discovered_tools: list[ToolDefinitionSchema] = []
        self._request_counter = 0

    def _next_id(self) -> int:
        self._request_counter += 1
        return self._request_counter

    async def connect(self) -> None:
        """Connect to MCP server and complete the initialization handshake."""
        await self.transport.connect()
        req = JsonRpcRequest(
            id=self._next_id(),
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": self.client_name, "version": "0.1.0"},
            },
        )
        res = await self.transport.send_request(req)
        if res.error:
            raise ConnectionError(f"MCP initialization failed: {res.error.get('message')}")

        result_data = res.result or {}
        self.server_info = result_data.get("serverInfo", {})
        self.server_capabilities = result_data.get("capabilities", {})

    async def disconnect(self) -> None:
        """Close connection."""
        await self.transport.disconnect()

    async def discover_tools(self) -> list[ToolDefinitionSchema]:
        """Fetch remote tool declarations from the MCP server and map them to Jenna schemas."""
        req = JsonRpcRequest(
            id=self._next_id(),
            method="tools/list",
            params={},
        )
        res = await self.transport.send_request(req)
        if res.error:
            raise RuntimeError(f"MCP tools/list failed: {res.error.get('message')}")

        tools_data = (res.result or {}).get("tools", [])
        mapped_tools: list[ToolDefinitionSchema] = []

        for raw_tool in tools_data:
            name = raw_tool.get("name", "")
            description = raw_tool.get("description", "")
            input_schema = raw_tool.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            required_keys = set(input_schema.get("required", []))

            parameters: list[ToolParameterSchema] = []
            for param_name, prop in properties.items():
                parameters.append(
                    ToolParameterSchema(
                        name=param_name,
                        type=prop.get("type", "string"),
                        description=prop.get("description", ""),
                        required=param_name in required_keys,
                        default=prop.get("default"),
                        enum_values=prop.get("enum"),
                    )
                )

            tool_def = ToolDefinitionSchema(
                name=f"mcp_{name}",
                description=description or f"MCP tool: {name}",
                category=ToolCategory.MCP,
                parameters=parameters,
                requires_permission=None,
                is_sensitive=False,
                timeout_seconds=30.0,
            )
            mapped_tools.append(tool_def)

        self.discovered_tools = mapped_tools
        return mapped_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
        """Execute a remote tool call via MCP tools/call."""
        clean_name = tool_name.removeprefix("mcp_")
        req = JsonRpcRequest(
            id=self._next_id(),
            method="tools/call",
            params={"name": clean_name, "arguments": arguments},
        )
        res = await asyncio.wait_for(self.transport.send_request(req), timeout=timeout)
        if res.error:
            raise RuntimeError(f"MCP tools/call returned error: {res.error.get('message')}")

        result_data = res.result or {}
        is_error = result_data.get("isError", False)
        content = result_data.get("content", [])

        # Extract text payloads
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        combined_text = "\n".join(texts)

        if is_error:
            raise RuntimeError(f"Tool execution failed on MCP server: {combined_text}")

        try:
            parsed = json.loads(combined_text)
            return parsed
        except (json.JSONDecodeError, TypeError):
            return {"output": combined_text}
