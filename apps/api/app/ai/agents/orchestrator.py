"""Multi-Agent Orchestration, Task Decomposition, and Context Handoff Engine."""

import logging
import re
import time
from typing import Any, Optional
import uuid

from app.ai.agents.registry import agent_registry
from app.models.tasks import AgentTask, AgentTaskStatus, AgentType, TaskPriority
from app.schemas.agents import (
    AgentBudgetSchema,
    AgentDecompositionPlan,
    AgentDecompositionSubtask,
    ContextHandoffSchema,
)

logger = logging.getLogger("jenna.agents.orchestrator")

# Safeguard caps to prevent runaway agent loops
MAX_DECOMPOSITION_DEPTH = 3
MAX_SUBTASKS_PER_PLAN = 5
MAX_EXECUTION_STEPS_CAP = 30


class AgentOrchestrator:
    """Coordinates task decomposition, agent selection, context handoffs, and execution boundaries."""

    def __init__(self) -> None:
        self.registry = agent_registry

    def select_agent(self, task_description: str, suggested_type: str | None = None) -> AgentType:
        """Heuristically or explicitly selects the most appropriate specialized agent."""
        if suggested_type:
            try:
                return AgentType(suggested_type)
            except ValueError:
                pass

        desc_lower = task_description.lower()

        # Code keywords
        if any(kw in desc_lower for kw in ["code", "refactor", "bug", "implement", "python", "typescript", "function", "class", "api endpoint"]):
            return AgentType.CODING

        # Research keywords
        if any(kw in desc_lower for kw in ["research", "investigate", "find out", "compare options", "literature", "history of"]):
            return AgentType.RESEARCH

        # Analysis keywords
        if any(kw in desc_lower for kw in ["analyze", "evaluate", "trade-off", "benchmark", "risk assessment", "audit"]):
            return AgentType.ANALYSIS

        # Writing keywords
        if any(kw in desc_lower for kw in ["document", "write", "summary", "draft", "release notes", "guide", "readme"]):
            return AgentType.WRITING

        return AgentType.GENERAL_TASK

    def decompose_task(
        self,
        task_title: str,
        task_description: str,
        current_depth: int = 0,
    ) -> AgentDecompositionPlan:
        """Decomposes a complex objective into bounded, sequential specialized subtasks.
        
        Enforces MAX_DECOMPOSITION_DEPTH and MAX_SUBTASKS_PER_PLAN safeguards.
        """
        if current_depth >= MAX_DECOMPOSITION_DEPTH:
            # Depth limit reached: produce single leaf task
            assigned = self.select_agent(task_description)
            return AgentDecompositionPlan(
                original_task=task_title,
                strategy="Leaf task execution (depth limit reached)",
                subtasks=[
                    AgentDecompositionSubtask(
                        title=task_title,
                        description=task_description,
                        agent_type=assigned,
                        order=1,
                    )
                ],
            )

        full_text = f"{task_title} {task_description}".lower()
        subtasks: list[AgentDecompositionSubtask] = []

        # Complex feature build pattern: Research -> Architecture/Coding -> Documentation
        is_feature_build = any(kw in full_text for kw in ["build", "create", "implement", "develop", "system"]) and len(full_text) > 40
        is_research_and_write = any(kw in full_text for kw in ["research and write", "investigate and document"])

        if is_feature_build:
            subtasks = [
                AgentDecompositionSubtask(
                    title=f"Analysis & Requirements: {task_title}",
                    description=f"Analyze requirements, dependencies, and constraints for: {task_description}",
                    agent_type=AgentType.ANALYSIS,
                    order=1,
                ),
                AgentDecompositionSubtask(
                    title=f"Implementation: {task_title}",
                    description=f"Produce core implementation and tests for: {task_description}",
                    agent_type=AgentType.CODING,
                    order=2,
                ),
                AgentDecompositionSubtask(
                    title=f"Documentation & Handoff: {task_title}",
                    description=f"Draft technical documentation and usage summary for: {task_description}",
                    agent_type=AgentType.WRITING,
                    order=3,
                ),
            ]
            strategy = "Three-phase pipeline: Analysis -> Implementation -> Documentation"
        elif is_research_and_write:
            subtasks = [
                AgentDecompositionSubtask(
                    title=f"Topic Research: {task_title}",
                    description=f"Gather core findings and technical facts regarding: {task_description}",
                    agent_type=AgentType.RESEARCH,
                    order=1,
                ),
                AgentDecompositionSubtask(
                    title=f"Synthesis Report: {task_title}",
                    description=f"Synthesize structured report and guidance based on research.",
                    agent_type=AgentType.WRITING,
                    order=2,
                ),
            ]
            strategy = "Two-phase pipeline: Research -> Synthesis"
        else:
            # Single task
            assigned = self.select_agent(task_description)
            subtasks = [
                AgentDecompositionSubtask(
                    title=task_title,
                    description=task_description,
                    agent_type=assigned,
                    order=1,
                )
            ]
            strategy = f"Direct execution by specialized agent {assigned.value}"

        # Bound subtasks count
        subtasks = subtasks[:MAX_SUBTASKS_PER_PLAN]

        return AgentDecompositionPlan(
            original_task=task_title,
            strategy=strategy,
            subtasks=subtasks,
        )

    def build_context_handoff(
        self,
        source_agent: str,
        task_summary: str,
        artifacts: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Packages clean inter-agent context without exposing chain-of-thought."""
        schema = ContextHandoffSchema(
            source_agent=source_agent,
            task_summary=task_summary.strip(),
            artifacts=artifacts or [],
            metadata=metadata or {},
        )
        return schema.model_dump()

    def check_sensitive_action(self, action_name: str, payload: dict[str, Any]) -> tuple[bool, str | None]:
        """Detects if an agent action involves sensitive operations requiring user confirmation."""
        sensitive_patterns = [
            (r"delete|destroy|drop|purge|truncate", "Data deletion or destruction requires user confirmation"),
            (r"grant|elevate|admin|sudo", "Privilege elevation requires user confirmation"),
            (r"api_key|secret|credential|token|password", "Accessing or handling secrets requires user confirmation"),
            (r"deploy|publish|release", "Production deployment or external publishing requires confirmation"),
        ]

        target_text = f"{action_name} {str(payload)}".lower()
        for pattern, reason in sensitive_patterns:
            if re.search(pattern, target_text):
                return True, reason

        return False, None


# Global singleton instance
agent_orchestrator = AgentOrchestrator()
