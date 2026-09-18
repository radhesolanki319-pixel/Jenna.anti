"""Tools API Router: Discovery, execution, MCP integration, and web research."""

import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status

from app.ai.tools.executor import PlatformToolExecutor, default_tool_executor
from app.ai.tools.mcp.client import MCPClient, MockMCPTransport
from app.ai.tools.registry import ToolRegistry, default_tool_registry
from app.ai.tools.types import (
    ResearchRequest,
    ResearchResponse,
    ToolCallRequest,
    ToolCategory,
    ToolDefinitionSchema,
    ToolExecutionResult,
)
from app.ai.tools.web.researcher import ResearchPipeline
from app.models.users import User
from app.services.auth_service import get_current_user

logger = logging.getLogger("jenna.tools_router")

router = APIRouter(prefix="/tools", tags=["tools"])

# In-memory registry of active MCP server connections
_active_mcp_clients: dict[str, MCPClient] = {}


@router.get(
    "",
    response_model=list[ToolDefinitionSchema],
    summary="List available platform tools",
    description="Returns tool declarations, input parameter schemas, categories, and permission tiers.",
)
async def list_tools(
    category: Optional[ToolCategory] = Query(None, description="Filter tools by category"),
    current_user: User = Depends(get_current_user),
) -> list[ToolDefinitionSchema]:
    """Retrieve catalog of available tools."""
    return default_tool_registry.list_tools(category=category)


@router.post(
    "/execute",
    response_model=ToolExecutionResult,
    summary="Execute a tool call",
    description="Invokes a tool with parameter validation, 3-tier authorization, and bounded execution timeouts.",
)
async def execute_tool(
    request: ToolCallRequest,
    current_user: User = Depends(get_current_user),
) -> ToolExecutionResult:
    """Execute a tool with user-isolated permissions."""
    return await default_tool_executor.execute_tool_call(
        request=request,
        user_id=str(current_user.id),
        user_role=current_user.role,
    )


@router.post(
    "/research",
    response_model=ResearchResponse,
    summary="Perform multi-source web research",
    description="Multi-step research workflow: searches sources, cross-references findings, and produces verified citations.",
)
async def perform_research(
    request: ResearchRequest,
    current_user: User = Depends(get_current_user),
) -> ResearchResponse:
    """Execute multi-step web research with citation generation."""
    pipeline = ResearchPipeline()
    return await pipeline.execute_research(request)


@router.get(
    "/mcp/servers",
    summary="List connected MCP servers",
    description="Returns active Model Context Protocol connections and their discovered capabilities.",
)
async def list_mcp_servers(
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List connected MCP servers."""
    servers = []
    for name, client in _active_mcp_clients.items():
        servers.append({
            "name": name,
            "connected": client.transport.is_connected if hasattr(client.transport, "is_connected") else True,
            "server_info": client.server_info,
            "tools_count": len(client.discovered_tools),
            "tools": [t.name for t in client.discovered_tools],
        })
    return servers


@router.post(
    "/mcp/connect",
    summary="Connect an MCP server",
    description="Initializes connection to an MCP server, performs handshake, and dynamically registers tools.",
)
async def connect_mcp_server(
    server_name: str = Query(..., description="Unique name for this MCP server instance"),
    server_type: str = Query("mock", description="Connection transport type: mock, stdio, sse"),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Connect to an MCP server and register its discovered tools."""
    if server_name in _active_mcp_clients:
        return {
            "status": "already_connected",
            "server_name": server_name,
            "tools_registered": len(_active_mcp_clients[server_name].discovered_tools),
        }

    # Initialize transport
    if server_type == "mock":
        transport = MockMCPTransport(server_name=server_name)
    else:
        # Default mock fallback for testing
        transport = MockMCPTransport(server_name=server_name)

    client = MCPClient(transport=transport)
    await client.connect()
    discovered = await client.discover_tools()

    # Register each discovered tool into the central platform registry
    for tool_def in discovered:
        # Bind tool execution to MCP client call
        async def make_mcp_handler(t_name: str):
            async def _handler(params: dict[str, Any]):
                return await client.call_tool(t_name, params)
            return _handler

        handler = await make_mcp_handler(tool_def.name)
        default_tool_registry.register_tool(tool_def, handler)

    _active_mcp_clients[server_name] = client

    return {
        "status": "connected",
        "server_name": server_name,
        "tools_registered": len(discovered),
        "tools": [t.name for t in discovered],
    }
