"""Centralized Tool Registry for Jenna AI Platform."""

from typing import Any, Callable, Coroutine

from app.ai.tools.builtin.calculator import CALCULATOR_TOOL, calculate
from app.ai.tools.builtin.filesystem import (
    FILESYSTEM_LIST_TOOL,
    FILESYSTEM_READ_TOOL,
    FILESYSTEM_WRITE_TOOL,
    list_directory,
    read_file,
    write_file,
)
from app.ai.tools.builtin.generators import (
    BLENDER_VALIDATOR_TOOL,
    LATEX_VALIDATOR_TOOL,
    SPREADSHEET_VALIDATOR_TOOL,
    validate_blender_script,
    validate_latex_source,
    validate_spreadsheet_formula,
)
from app.ai.tools.builtin.system import SYSTEM_INFO_TOOL, get_system_telemetry
from app.ai.tools.types import (
    ResearchRequest,
    ToolCategory,
    ToolDefinitionSchema,
)
from app.ai.tools.web.researcher import ResearchPipeline, WEB_RESEARCH_TOOL
from app.core.permissions import Permission



class ToolRegistry:
    """Central registry maintaining tool definitions, schemas, and execution handlers."""

    def __init__(self):
        self._tools: dict[str, ToolDefinitionSchema] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._research_pipeline = ResearchPipeline()

        # Register default builtin tools
        self._register_default_builtins()

    def _register_default_builtins(self) -> None:
        """Register core standard tools into registry."""
        # 1. Calculator
        self.register_tool(
            CALCULATOR_TOOL,
            lambda params: calculate(params.get("expression", "")),
        )

        # 2. Filesystem Read
        self.register_tool(
            FILESYSTEM_READ_TOOL,
            lambda params: read_file(
                path=params.get("path", ""),
                start_line=params.get("start_line"),
                end_line=params.get("end_line"),
            ),
        )

        # 3. Filesystem List
        self.register_tool(
            FILESYSTEM_LIST_TOOL,
            lambda params: list_directory(
                path=params.get("path", "."),
                max_entries=params.get("max_entries", 100),
            ),
        )

        # 4. Filesystem Write (Sensitive)
        self.register_tool(
            FILESYSTEM_WRITE_TOOL,
            lambda params: write_file(
                path=params.get("path", ""),
                content=params.get("content", ""),
                overwrite=params.get("overwrite", False),
            ),
        )

        # 5. System Telemetry
        self.register_tool(
            SYSTEM_INFO_TOOL,
            lambda params: get_system_telemetry(),
        )

        # 6. Web Research
        self.register_tool(
            WEB_RESEARCH_TOOL,
            self._handle_web_research,
        )

        # 7. GPT-6 Astra: Blender bpy Validator
        self.register_tool(
            BLENDER_VALIDATOR_TOOL,
            lambda params: validate_blender_script(params.get("script", "")),
        )

        # 8. GPT-6 Astra: LaTeX Architecture Validator
        self.register_tool(
            LATEX_VALIDATOR_TOOL,
            lambda params: validate_latex_source(params.get("latex_code", "")),
        )

        # 9. GPT-6 Astra: Dynamic Spreadsheet Formula Validator
        self.register_tool(
            SPREADSHEET_VALIDATOR_TOOL,
            lambda params: validate_spreadsheet_formula(params.get("formula", "")),
        )


    async def _handle_web_research(self, params: dict[str, Any]) -> dict[str, Any]:
        """Asynchronous handler for web research tool."""
        req = ResearchRequest(
            query=params.get("query", ""),
            max_sources=params.get("max_sources", 4),
        )
        res = await self._research_pipeline.execute_research(req)
        return res.model_dump()

    def register_tool(
        self,
        definition: ToolDefinitionSchema,
        handler: Callable[..., Any],
    ) -> None:
        """Register a tool with its schema definition and execution callable."""
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def get_tool(self, name: str) -> ToolDefinitionSchema | None:
        """Retrieve tool schema definition by name."""
        return self._tools.get(name)

    def get_handler(self, name: str) -> Callable[..., Any] | None:
        """Retrieve execution callable by tool name."""
        return self._handlers.get(name)

    def list_tools(
        self,
        category: ToolCategory | None = None,
        permission_filter: set[Permission] | None = None,
    ) -> list[ToolDefinitionSchema]:
        """List registered tools optionally filtered by category and permissions."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if permission_filter is not None:
            tools = [
                t for t in tools
                if t.requires_permission is None or t.requires_permission in permission_filter
            ]
        return tools

    def validate_call(self, tool_name: str, parameters: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate whether provided arguments satisfy the tool's schema."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found in registry"

        param_defs = {p.name: p for p in tool.parameters}

        # Check for missing required parameters
        for p in tool.parameters:
            if p.required and p.name not in parameters:
                return False, f"Missing required parameter '{p.name}' for tool '{tool_name}'"

        # Check types for provided parameters
        for k, v in parameters.items():
            if k not in param_defs:
                # Disallow unexpected parameters
                return False, f"Unexpected parameter '{k}' provided to tool '{tool_name}'"

            p_def = param_defs[k]
            if v is not None:
                if p_def.type == "string" and not isinstance(v, str):
                    return False, f"Parameter '{k}' must be a string, got {type(v).__name__}"
                elif p_def.type == "integer" and (not isinstance(v, int) or isinstance(v, bool)):
                    return False, f"Parameter '{k}' must be an integer, got {type(v).__name__}"
                elif p_def.type == "number" and (not isinstance(v, (int, float)) or isinstance(v, bool)):
                    return False, f"Parameter '{k}' must be a number, got {type(v).__name__}"
                elif p_def.type == "boolean" and not isinstance(v, bool):
                    return False, f"Parameter '{k}' must be a boolean, got {type(v).__name__}"
                elif p_def.type == "array" and not isinstance(v, list):
                    return False, f"Parameter '{k}' must be an array, got {type(v).__name__}"
                elif p_def.type == "object" and not isinstance(v, dict):
                    return False, f"Parameter '{k}' must be an object/dict, got {type(v).__name__}"

                if p_def.enum_values and str(v) not in p_def.enum_values:
                    return False, f"Parameter '{k}' value '{v}' not in permitted choices: {p_def.enum_values}"

        return True, None

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Export tool definitions in OpenAI Function Calling standard format."""
        openai_tools = []
        for tool in self._tools.values():
            properties = {}
            required = []
            for p in tool.parameters:
                properties[p.name] = {
                    "type": p.type,
                    "description": p.description,
                }
                if p.enum_values:
                    properties[p.name]["enum"] = p.enum_values
                if p.required:
                    required.append(p.name)

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            })
        return openai_tools


# Global singleton registry
default_tool_registry = ToolRegistry()
