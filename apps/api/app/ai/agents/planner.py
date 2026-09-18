"""Task Planner and Orchestrator skeleton for decomposing agent goals into structured steps."""

import re
from typing import Any
import uuid

from app.ai.agents.types import (
    AgentBudget,
    AgentTaskStatus,
    AgentType,
    TaskStep,
)


class TaskPlanner:
    """Decomposes a user task or goal into bounded, typed execution steps."""

    @staticmethod
    def classify_primary_agent(goal: str) -> AgentType:
        """Heuristic classifier to determine primary agent for a goal."""
        text = goal.lower()
        # GPT-6 Astra Domains
        if any(w in text for w in ["blender", "bpy", "3d", "cad", "unreal", "ue5", "fluid simulation", "mesh", "spatial animation", "openscad"]):
            return AgentType.SPATIAL_3D
        if any(w in text for w in ["latex", "pdf compile", "spreadsheet", "xlsx", "excel", "financial model", "macro", "typography scale"]):
            return AgentType.DOCUMENT_SYNTHESIS
        if any(w in text for w in ["theorem", "proof", "tier-4", "math discovery", "arc puzzle", "abstract reasoning", "multi-variable projection"]):
            return AgentType.FRONTIER_MATH
        if any(w in text for w in ["desktop automation", "rpa", "browse website", "fill form", "screen click", "os-level"]):
            return AgentType.SYSTEM_AUTOMATION
        if any(w in text for w in ["exploit", "patch", "vulnerability", "zero-day", "stack trace", "devops", "terminal control", "architecture drift", "refactor deep"]):
            return AgentType.ENTERPRISE_DEVOPS

        # Standard Core Domains
        if any(w in text for w in ["research", "investigate", "find out", "source", "evidence"]):
            return AgentType.RESEARCH
        if any(w in text for w in ["analyze", "evaluate", "tradeoff", "trade-off", "benchmark", "pros and cons", "feasibility"]):
            return AgentType.ANALYSIS
        if any(w in text for w in ["write", "draft", "document", "documentation", "email", "summary", "post", "blog", "essay", "letter", "guide", "readme"]):
            return AgentType.WRITING
        if any(w in text for w in ["code", "function", "class", "script", "bug", "refactor", "test", "api", "backend", "frontend", "python", "typescript", "implement"]):
            return AgentType.CODING
        return AgentType.GENERAL_TASK

    @classmethod
    def decompose(
        cls,
        goal: str,
        primary_agent: AgentType | None = None,
        budget: AgentBudget | None = None,
    ) -> list[TaskStep]:
        """Decompose a high-level goal into an initial sequential execution plan."""
        max_steps = budget.max_steps if budget else 10
        agent = primary_agent or cls.classify_primary_agent(goal)

        steps: list[TaskStep] = []

        # Multi-phase decomposition based on agent type
        if agent == AgentType.SPATIAL_3D:
            raw_steps = [
                (AgentType.ANALYSIS, f"Analyze 3D/CAD constraints and physical specifications for: {goal}"),
                (AgentType.SPATIAL_3D, f"Generate procedural bpy scripts, CAD geometry, and simulation parameters for: {goal}"),
                (AgentType.WRITING, f"Document spatial coordinates, pipeline integration, and rendering guidelines for: {goal}"),
            ]
        elif agent == AgentType.ENTERPRISE_DEVOPS:
            raw_steps = [
                (AgentType.ANALYSIS, f"Isolate runtime error, stack trace, and module dependencies for: {goal}"),
                (AgentType.ENTERPRISE_DEVOPS, f"Synthesize atomic bug fix, patch vulnerabilities, or execute terminal commands for: {goal}"),
                (AgentType.CODING, f"Verify regression tests and architecture integrity for: {goal}"),
            ]
        elif agent == AgentType.DOCUMENT_SYNTHESIS:
            raw_steps = [
                (AgentType.ANALYSIS, f"Structure data schema, typographic layout, and formulas for: {goal}"),
                (AgentType.DOCUMENT_SYNTHESIS, f"Compile enterprise LaTeX PDF architecture or dynamic .xlsx workbook for: {goal}"),
                (AgentType.WRITING, f"Review brand alignment, typography hierarchy, and formula verification for: {goal}"),
            ]
        elif agent == AgentType.FRONTIER_MATH:
            raw_steps = [
                (AgentType.ANALYSIS, f"Establish axioms, state spaces, and formal mathematical boundaries for: {goal}"),
                (AgentType.FRONTIER_MATH, f"Derive rigorous proof steps, spatial transformations, or multi-variable models for: {goal}"),
                (AgentType.WRITING, f"Synthesize formal proof notation and sensitivity confidence intervals for: {goal}"),
            ]
        elif agent == AgentType.SYSTEM_AUTOMATION:
            raw_steps = [
                (AgentType.ANALYSIS, f"Plan UI interaction steps, targets, and permission safety checks for: {goal}"),
                (AgentType.SYSTEM_AUTOMATION, f"Execute OS navigation, browsing workflows, or RPA operations for: {goal}"),
                (AgentType.WRITING, f"Verify execution telemetry, state invariants, and output reports for: {goal}"),
            ]
        elif agent == AgentType.CODING:
            raw_steps = [
                (AgentType.ANALYSIS, f"Analyze specifications and requirements for: {goal}"),
                (AgentType.CODING, f"Implement core functionality and unit tests for: {goal}"),
                (AgentType.WRITING, f"Document usage and verification steps for: {goal}"),
            ]
        elif agent == AgentType.RESEARCH:
            raw_steps = [
                (AgentType.RESEARCH, f"Gather background data and key facts for: {goal}"),
                (AgentType.ANALYSIS, f"Evaluate findings, verify consistency, and synthesize conclusions for: {goal}"),
                (AgentType.WRITING, f"Formulate clear executive summary report for: {goal}"),
            ]
        elif agent == AgentType.ANALYSIS:
            raw_steps = [
                (AgentType.RESEARCH, f"Collect data points and context related to: {goal}"),
                (AgentType.ANALYSIS, f"Perform rigorous trade-off and metrics analysis for: {goal}"),
                (AgentType.WRITING, f"Deliver structured analytical breakdown and recommendations for: {goal}"),
            ]
        elif agent == AgentType.WRITING:
            raw_steps = [
                (AgentType.RESEARCH, f"Identify core themes and factual anchors for: {goal}"),
                (AgentType.WRITING, f"Draft and polish comprehensive content for: {goal}"),
            ]
        else:
            raw_steps = [
                (AgentType.GENERAL_TASK, f"Execute goal: {goal}"),
            ]


        # Truncate strictly to budget max_steps
        bounded_steps = raw_steps[:max_steps]

        for idx, (step_agent, desc) in enumerate(bounded_steps, start=1):
            steps.append(
                TaskStep(
                    step_id=str(uuid.uuid4()),
                    step_number=idx,
                    description=desc,
                    agent_type=step_agent,
                    status=AgentTaskStatus.CREATED,
                    input_context={"target_goal": goal},
                )
            )

        return steps
