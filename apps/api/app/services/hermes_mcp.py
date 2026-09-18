"""Hermes Bidirectional Model Context Protocol (MCP) Server for Jenna AI.

Implements Nous Research's Hermes Agent MCP standard:
Exposes all Jenna autonomous tools as an MCP-compliant server for bidirectional
interoperability with Cursor, Claude Desktop, and external agent ecosystems.
"""

import json
import logging
from typing import Any, Dict, List

from app.services.hermes_skills import hermes_skill_engine

logger = logging.getLogger("jenna.hermes_mcp")


class HermesMCPServer:
    """Model Context Protocol (MCP) Server specification provider and executor."""

    def __init__(self) -> None:
        self.server_name = "jenna-hermes-mcp"
        self.server_version = "1.0.0"

    def get_server_info(self) -> Dict[str, Any]:
        """Return MCP Server metadata."""
        return {
            "name": self.server_name,
            "version": self.server_version,
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
        }

    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """Return MCP-standard tool definitions."""
        return [
            {
                "name": "jenna_run_command",
                "description": "Execute bash commands in Termux Linux environment synchronously or in background",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The command line string to execute"},
                        "cwd": {"type": "string", "description": "Working directory path"},
                        "wait_ms": {"type": "integer", "description": "Wait time before detaching to background"},
                    },
                    "required": ["command"],
                },
            },
            {
                "name": "jenna_replace_file_content",
                "description": "Surgically replace exact contiguous code chunk within specified line bounds",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target file absolute path"},
                        "target_content": {"type": "string", "description": "Exact lines to be replaced"},
                        "replacement_content": {"type": "string", "description": "Replacement lines"},
                        "start_line": {"type": "integer", "description": "Start line bound"},
                        "end_line": {"type": "integer", "description": "End line bound"},
                    },
                    "required": ["path", "target_content", "replacement_content"],
                },
            },
            {
                "name": "jenna_learn_skill",
                "description": "Hermes closed-loop skill creation: save a reusable procedure into persistent skill library",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the skill in kebab-case"},
                        "description": {"type": "string", "description": "Brief description of skill purpose"},
                        "instructions": {"type": "string", "description": "Markdown instructions and procedure"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Search tags"},
                    },
                    "required": ["name", "description", "instructions"],
                },
            },
            {
                "name": "jenna_point_on_screen",
                "description": "Draw glowing touch pointer at exact (x, y) coordinates on user's Android screen",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X display coordinate in pixels"},
                        "y": {"type": "integer", "description": "Y display coordinate in pixels"},
                        "duration_ms": {"type": "integer", "description": "Pointer display duration in milliseconds"},
                    },
                    "required": ["x", "y"],
                },
            },
            {
                "name": "jenna_invoke_subagent",
                "description": "Dispatch parallel autonomous subagents into the multi-agent swarm",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "subagents": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "TypeName": {"type": "string"},
                                    "Role": {"type": "string"},
                                    "Prompt": {"type": "string"},
                                },
                                "required": ["TypeName", "Role", "Prompt"],
                            },
                        }
                    },
                    "required": ["subagents"],
                },
            },
        ]

    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call routed through standard MCP JSON-RPC protocol."""
        from app.services.antigravity_agent import antigravity_agent

        if tool_name == "jenna_run_command":
            res = await antigravity_agent.execute_tool("run_command", arguments)
        elif tool_name == "jenna_replace_file_content":
            res = await antigravity_agent.execute_tool("replace_file_content", arguments)
        elif tool_name == "jenna_learn_skill":
            res = hermes_skill_engine.create_skill(
                name=arguments.get("name", "custom-skill"),
                description=arguments.get("description", ""),
                instructions=arguments.get("instructions", ""),
                tags=arguments.get("tags", []),
            )
        elif tool_name == "jenna_point_on_screen":
            res = await antigravity_agent.execute_tool("point_on_screen", arguments)
        elif tool_name == "jenna_invoke_subagent":
            res = await antigravity_agent.execute_tool("invoke_subagent", arguments)
        else:
            return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

        return {"isError": not res.get("success", True), "content": [{"type": "text", "text": json.dumps(res, indent=2)}]}


hermes_mcp_server = HermesMCPServer()
