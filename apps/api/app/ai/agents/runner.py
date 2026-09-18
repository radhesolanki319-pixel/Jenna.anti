"""Agent Runner executing autonomous multi-step tasks with strict safety gates,
bounded budgets, timeouts, permission checks, and audit logging.
"""

import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import Any
import uuid

from app.ai.agents.planner import TaskPlanner
from app.ai.agents.registry import AgentRegistry, agent_registry
from app.ai.agents.types import (
    AgentBudget,
    AgentContext,
    AgentHandoff,
    AgentTask,
    AgentTaskStatus,
    AgentType,
    TaskResult,
    TaskStep,
)
from app.ai.context import MemoryContextProvider
from app.services.memory_service import MemoryService
from app.ai.service import get_ai_service
from app.core.permissions import Permission
from app.interfaces.permissions import AuthorizationDecision
from app.services.permission_service import DefaultPermissionService

logger = logging.getLogger("jenna.agents.runner")


class AgentRunner:
    """Orchestrates autonomous task execution across registered specialized agents."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        permission_service: DefaultPermissionService | None = None,
        ai_service: Any = None,
    ) -> None:
        self.registry = registry or agent_registry
        self.permission_service = permission_service or DefaultPermissionService()
        self._ai_service = ai_service
        self._cancellation_events: dict[str, asyncio.Event] = {}

    @property
    def ai_service(self) -> Any:
        if self._ai_service is None:
            self._ai_service = get_ai_service()
        return self._ai_service

    def cancel_task(self, task_id: str) -> bool:
        """Signal cancellation for an active or queued task."""
        if task_id not in self._cancellation_events:
            self._cancellation_events[task_id] = asyncio.Event()
        self._cancellation_events[task_id].set()
        return True

    async def execute_task(
        self,
        task: AgentTask,
        user_role: str = "user",
        session: Any = None,
    ) -> AgentTask:
        cancel_event = self._cancellation_events.get(task.task_id) or asyncio.Event()
        self._cancellation_events[task.task_id] = cancel_event

        start_time = time.monotonic()
        task.status = AgentTaskStatus.RUNNING
        task.updated_at = datetime.now(timezone.utc)

        # 1. Decompose into steps if not already populated
        if not task.steps:
            task.steps = TaskPlanner.decompose(
                goal=task.description,
                primary_agent=task.agent_type,
                budget=task.budget,
            )

        # 2. Retrieve long-term cognitive memory context for user
        memory_str = None
        if session:
            try:
                mem_provider = MemoryContextProvider(memory_service=MemoryService(session=session))
                snippets = await mem_provider.provide_context(
                    user_id=task.user_id,
                    query=f"{task.title} {task.description}",
                )
                if snippets:
                    memory_str = "\n".join(snippets)
            except Exception as exc:
                logger.warning("Failed to retrieve memory context for agent task: %s", exc)

        agent_context = AgentContext(
            task_id=task.task_id,
            user_id=task.user_id,
            initial_goal=task.description,
            memory_context=memory_str,
            working_memory={},
            step_history=[],
            artifacts=[],
        )

        total_tokens_consumed = 0
        execution_error: str | None = None
        current_agent_type: AgentType | None = None

        try:
            async with asyncio.timeout(task.budget.timeout_seconds):
                for step in task.steps:
                    # Check cancellation
                    if cancel_event.is_set():
                        task.status = AgentTaskStatus.CANCELLED
                        step.status = AgentTaskStatus.CANCELLED
                        step.error = "Task cancelled by user request."
                        execution_error = "Task was cancelled before completion."
                        break

                    # Resolve specialized agent
                    agent = self.registry.get(step.agent_type)
                    if not agent:
                        step.status = AgentTaskStatus.FAILED
                        step.error = f"Agent type '{step.agent_type.value}' is not registered."
                        task.status = AgentTaskStatus.FAILED
                        execution_error = step.error
                        break

                    # Verify 3-tier permission
                    required_perm = (
                        Permission.EXECUTE
                        if step.agent_type == AgentType.CODING
                        else Permission.READ
                    )
                    eval_res = self.permission_service.evaluate_action(
                        role=user_role,
                        required_permission=required_perm,
                        is_sensitive=False,
                        context={"user_id": task.user_id, "task_id": task.task_id},
                    )

                    if eval_res.decision == AuthorizationDecision.DENIED:
                        step.status = AgentTaskStatus.FAILED
                        step.error = f"Permission denied: {eval_res.reason}"
                        task.status = AgentTaskStatus.FAILED
                        execution_error = step.error
                        break
                    elif eval_res.decision == AuthorizationDecision.REQUIRES_CONFIRMATION:
                        step.status = AgentTaskStatus.WAITING
                        task.status = AgentTaskStatus.WAITING
                        execution_error = f"Step #{step.step_number} requires user confirmation."
                        break

                    # Record context handoff if agent changed
                    if current_agent_type and current_agent_type != step.agent_type:
                        handoff = AgentHandoff(
                            from_agent=current_agent_type,
                            to_agent=step.agent_type,
                            reason=f"Transitioning to step #{step.step_number}",
                            context_summary=agent_context.step_history[-1].output_summary or "",
                            artifacts=agent_context.artifacts,
                        )
                        agent_context.artifacts.append({"handoff": handoff.model_dump()})

                    current_agent_type = step.agent_type

                    # Bounded retry execution loop (max 2 retries)
                    max_retries = 2
                    step_success = False
                    for attempt in range(max_retries + 1):
                        if cancel_event.is_set():
                            break
                        executed_step = await agent.execute_step(
                            step=step,
                            context=agent_context,
                            ai_service=self.ai_service,
                        )
                        if executed_step.status == AgentTaskStatus.SUCCEEDED:
                            step_success = True
                            # Estimated token increment
                            total_tokens_consumed += len((executed_step.output_summary or "").split()) * 2
                            break
                        elif attempt < max_retries:
                            await asyncio.sleep(0.1)

                    if not step_success:
                        task.status = AgentTaskStatus.FAILED
                        execution_error = step.error or f"Step #{step.step_number} failed after retries."
                        break

                    agent_context.step_history.append(step)

                    # Check token budget
                    if total_tokens_consumed > task.budget.max_tokens:
                        task.status = AgentTaskStatus.FAILED
                        execution_error = f"Exceeded token budget limit of {task.budget.max_tokens} tokens."
                        break

        except asyncio.TimeoutError:
            task.status = AgentTaskStatus.FAILED
            execution_error = f"Task timed out after {task.budget.timeout_seconds}s."
        except Exception as exc:
            task.status = AgentTaskStatus.FAILED
            execution_error = f"Unexpected agent execution error: {str(exc)}"
        finally:
            self._cancellation_events.pop(task.task_id, None)

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        if task.status not in (AgentTaskStatus.FAILED, AgentTaskStatus.CANCELLED, AgentTaskStatus.WAITING):
            task.status = AgentTaskStatus.SUCCEEDED

        # Synthesize final output without exposing internal chain-of-thought
        succeeded_steps = [s for s in task.steps if s.status == AgentTaskStatus.SUCCEEDED]
        final_summary = ""
        if succeeded_steps:
            final_summary = "\n\n".join(
                f"### Step {s.step_number}: {s.description}\n{s.output_summary}"
                for s in succeeded_steps
            )
        elif execution_error:
            final_summary = f"Task stopped: {execution_error}"

        task.result = TaskResult(
            task_id=task.task_id,
            status=task.status,
            summary=f"Execution completed with status '{task.status.value}' across {len(succeeded_steps)}/{len(task.steps)} steps.",
            output=final_summary,
            artifacts=agent_context.artifacts,
            total_steps=len(succeeded_steps),
            total_tokens=total_tokens_consumed,
            latency_ms=round(elapsed_ms, 2),
            error=execution_error,
        )
        task.updated_at = datetime.now(timezone.utc)
        return task


# Global singleton runner
agent_runner = AgentRunner()
