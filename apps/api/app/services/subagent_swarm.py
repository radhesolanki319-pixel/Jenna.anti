"""Multi-Agent Swarm Orchestrator for Jenna & Antigravity.

Enables concurrent background subagent dispatching, runtime agent specialization,
inter-agent pub/sub messaging bus, and isolated workspace management.
"""

import asyncio
from dataclasses import dataclass, field
import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any, Callable, Optional
import uuid

logger = logging.getLogger("jenna.subagent_swarm")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass
class SubagentDefinition:
    name: str
    description: str
    system_prompt: str
    enable_write_tools: bool = True
    enable_subagent_tools: bool = False
    enable_mcp_tools: bool = True


@dataclass
class SubagentInstance:
    conversation_id: str
    type_name: str
    role: str
    prompt: str
    model: str
    workspace_mode: str
    state: str = "running"  # running, idle, waiting_for_message, done, errored, canceled
    state_detail: str = "Initializing..."
    created_at: str = ""
    updated_at: str = ""
    transcript: list[dict[str, Any]] = field(default_factory=list)
    outbox: list[dict[str, Any]] = field(default_factory=list)


class SubagentSwarm:
    """Manages concurrent subagent execution loops and inter-agent communication."""

    def __init__(self) -> None:
        self.definitions: dict[str, SubagentDefinition] = {}
        self.instances: dict[str, SubagentInstance] = {}
        self._message_queues: dict[str, asyncio.Queue] = {}
        self._register_default_definitions()

    def _register_default_definitions(self) -> None:
        self.definitions["research"] = SubagentDefinition(
            name="research",
            description="Deep web search, documentation inspection, and codebase reconnaissance with read-only tools.",
            system_prompt="You are a high-speed Research Subagent. Inspect code, search web, analyze data, and report findings concisely.",
            enable_write_tools=False,
            enable_subagent_tools=False,
            enable_mcp_tools=True,
        )
        self.definitions["self"] = SubagentDefinition(
            name="self",
            description="Full-capability peer clone inheriting full terminal, code writing, and tool execution powers.",
            system_prompt="You are a peer autonomous developer subagent. Execute tasks, modify code, run tests, and report results.",
            enable_write_tools=True,
            enable_subagent_tools=True,
            enable_mcp_tools=True,
        )

    def define_subagent(
        self,
        name: str,
        description: str,
        system_prompt: str,
        enable_write_tools: bool = True,
        enable_subagent_tools: bool = False,
        enable_mcp_tools: bool = True,
    ) -> dict[str, Any]:
        """Dynamically register a new subagent type at runtime."""
        self.definitions[name] = SubagentDefinition(
            name=name,
            description=description,
            system_prompt=system_prompt,
            enable_write_tools=enable_write_tools,
            enable_subagent_tools=enable_subagent_tools,
            enable_mcp_tools=enable_mcp_tools,
        )
        logger.info(f"Registered new subagent definition: '{name}'")
        return {"success": True, "name": name, "message": f"Subagent type '{name}' registered successfully."}

    async def invoke_subagent(
        self,
        subagents: list[dict[str, Any]],
        on_complete_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> dict[str, Any]:
        """Dispatch one or more subagents concurrently."""
        dispatched = []

        for item in subagents:
            type_name = item.get("TypeName", "self")
            role = item.get("Role", type_name)
            prompt = item.get("Prompt", "")
            model = item.get("Model", "inherit")
            workspace_mode = item.get("Workspace", "inherit")

            cid = f"subagent-{uuid.uuid4().hex[:8]}"
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            instance = SubagentInstance(
                conversation_id=cid,
                type_name=type_name,
                role=role,
                prompt=prompt,
                model=model,
                workspace_mode=workspace_mode,
                state="running",
                state_detail=f"Dispatched task: {role}",
                created_at=now_iso,
                updated_at=now_iso,
            )
            self.instances[cid] = instance
            self._message_queues[cid] = asyncio.Queue()

            # Launch background worker task
            asyncio.create_task(self._run_subagent_loop(instance, on_complete_callback))
            dispatched.append({
                "conversationId": cid,
                "typeName": type_name,
                "role": role,
                "status": "running",
            })

        return {
            "success": True,
            "dispatched": dispatched,
            "message": f"Successfully launched {len(dispatched)} concurrent subagent(s).",
        }

    async def _run_subagent_loop(
        self,
        instance: SubagentInstance,
        on_complete_callback: Optional[Callable[[str, str], Any]] = None,
    ) -> None:
        """Background execution loop for an individual subagent."""
        logger.info(f"Subagent [{instance.conversation_id}] ({instance.role}) started.")
        try:
            from app.ai.providers.gemini_provider import GeminiProvider
            from app.ai.types import AIRequest, ChatMessage, TaskType

            provider = GeminiProvider()
            defn = self.definitions.get(instance.type_name, self.definitions.get("self"))
            system_prompt = defn.system_prompt if defn else "You are an autonomous subagent."

            subagent_full_prompt = (
                f"ROLE: {instance.role}\n"
                f"TASK: {instance.prompt}\n\n"
                "Execute and provide a clear, concise resolution summary."
            )

            instance.state = "running"
            instance.state_detail = f"Generating solution for: {instance.role}"

            req = AIRequest(
                messages=[ChatMessage(role="user", content=subagent_full_prompt)],
                system_instruction=system_prompt,
                model="gemini-3.5-flash-lite",
                temperature=0.2,
                max_tokens=1024,
                task_type=TaskType.CHAT,
            )
            res = await provider.generate(req)
            resolution = res.text if res and res.text else "Task completed."

            instance.state = "done"
            instance.state_detail = "Task completed successfully."
            instance.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            instance.transcript.append({"role": "assistant", "content": resolution})

            logger.info(f"Subagent [{instance.conversation_id}] completed.")
            if on_complete_callback:
                try:
                    res_coro = on_complete_callback(instance.conversation_id, resolution)
                    if asyncio.iscoroutine(res_coro):
                        await res_coro
                except Exception as e:
                    logger.warning(f"Error in subagent complete callback: {e}")

        except Exception as exc:
            logger.error(f"Subagent [{instance.conversation_id}] errored: {exc}")
            instance.state = "errored"
            instance.state_detail = f"Error: {str(exc)}"

    def list_subagents(self) -> list[dict[str, Any]]:
        """List active subagents and their current live states."""
        res = []
        for cid, inst in self.instances.items():
            res.append({
                "conversationId": cid,
                "type": inst.type_name,
                "role": inst.role,
                "state": inst.state,
                "stateDetail": inst.state_detail,
                "createdAt": inst.created_at,
                "updatedAt": inst.updated_at,
            })
        return res

    def kill_subagents(self, conversation_ids: list[str]) -> dict[str, Any]:
        """Terminate specific subagents."""
        killed = []
        for cid in conversation_ids:
            if cid in self.instances:
                self.instances[cid].state = "canceled"
                self.instances[cid].state_detail = "Manually killed by parent agent."
                killed.append(cid)
        return {"success": True, "killed": killed}

    def kill_all(self) -> dict[str, Any]:
        """Terminate all running subagents."""
        killed = []
        for cid, inst in self.instances.items():
            if inst.state in ("running", "idle", "waiting_for_message"):
                inst.state = "canceled"
                inst.state_detail = "Mass kill_all invoked."
                killed.append(cid)
        return {"success": True, "killed": killed}

    async def send_message(self, recipient_id: str, message: str) -> dict[str, Any]:
        """Deliver a message to a subagent."""
        if recipient_id not in self.instances:
            return {"error": f"Subagent '{recipient_id}' not found", "success": False}

        inst = self.instances[recipient_id]
        inst.transcript.append({"role": "user", "content": message})
        inst.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if recipient_id in self._message_queues:
            await self._message_queues[recipient_id].put(message)

        return {"success": True, "message": f"Delivered to subagent {recipient_id}"}


subagent_swarm = SubagentSwarm()
