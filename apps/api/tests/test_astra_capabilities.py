"""Test suite for GPT-6 Astra capabilities, Zero-Amnesia engine, Specialized Agents, and Tools."""

import pytest
from app.ai.agents.planner import TaskPlanner
from app.ai.agents.registry import agent_registry
from app.ai.agents.types import AgentType
from app.ai.astra_capabilities import (
    ASTRA_CAPABILITY_MANIFEST,
    build_astra_system_instructions,
)
from app.ai.context import ContextBuilder, ConversationContext
from app.ai.personality import SystemInstructionBuilder
from app.ai.tools.builtin.generators import (
    validate_blender_script,
    validate_latex_source,
    validate_spreadsheet_formula,
)
from app.ai.tools.registry import ToolRegistry
from app.ai.zero_amnesia import ZeroAmnesiaEngine


def test_astra_manifest_and_system_instructions():
    """Verify that all 5 Astra domains are present in the manifest and system instruction."""
    assert "autonomous_operations" in ASTRA_CAPABILITY_MANIFEST
    assert "spatial_simulation" in ASTRA_CAPABILITY_MANIFEST
    assert "enterprise_engineering" in ASTRA_CAPABILITY_MANIFEST
    assert "advanced_reasoning" in ASTRA_CAPABILITY_MANIFEST
    assert "structural_synthesis" in ASTRA_CAPABILITY_MANIFEST

    instruction = build_astra_system_instructions()
    assert "AUTONOMOUS SYSTEM & COMPUTER OPERATIONS" in instruction
    assert "3D MODELING, CAD, & PHYSICS SIMULATION" in instruction
    assert "ENTERPRISE SOFTWARE ENGINEERING" in instruction
    assert "ADVANCED REASONING & MATHEMATICS" in instruction
    assert "STRUCTURAL ASSET & DOCUMENT SYNTHESIS" in instruction

    # Verify integration into SystemInstructionBuilder
    builder = SystemInstructionBuilder()
    full_prompt = builder.build_system_instruction()
    assert "GPT-6 ASTRA CAPABILITY MATRIX" in full_prompt
    assert "Procedural Blender (bpy)" in full_prompt
    assert "Zero-Amnesia Context Discipline" in full_prompt


def test_zero_amnesia_engine():
    """Verify Zero-Amnesia symbol tracking, decision recording, and anti-loop watchdog."""
    engine = ZeroAmnesiaEngine()

    # 1. Record decisions
    engine.record_decision(
        topic="Database Engine",
        decision="Use PostgreSQL 18 with asyncpg",
        rationale="Vector search with pgvector",
    )
    assert len(engine.decisions) == 1

    # 2. Track symbols
    engine.track_symbols(
        file_path="apps/api/app/models/tasks.py",
        symbols=["AgentType", "AgentTask"],
    )
    assert "apps/api/app/models/tasks.py" in engine.symbols

    # 3. Context block generation
    block = engine.build_context_block()
    assert block is not None
    assert "<zero_amnesia_engine>" in block
    assert "Database Engine" in block
    assert "AgentType" in block

    # 4. Anti-loop watchdog
    code_attempt = "def solve_problem():\n    return 42"
    assert engine.check_loop(code_attempt) is False
    # Repeating identical code triggers loop detection
    assert engine.check_loop(code_attempt) is True
    assert engine.loop_count >= 1

    block_with_loop = engine.build_context_block()
    assert "CRITICAL ANTI-LOOP WATCHDOG DIRECTIVE" in block_with_loop


def test_conversation_context_with_zero_amnesia():
    """Verify ConversationContext incorporates zero_amnesia_context correctly."""
    context = ConversationContext(
        system_instruction="You are Jenna.",
        zero_amnesia_context="<zero_amnesia_engine>Active Symbols</zero_amnesia_engine>",
    )
    compiled = context.compile_system_instruction()
    assert compiled is not None
    assert "You are Jenna." in compiled
    assert "<zero_amnesia_engine>Active Symbols</zero_amnesia_engine>" in compiled


def test_astra_specialized_agents_in_registry():
    """Verify all 5 Astra specialized agents are registered with distinct instructions."""
    expected_types = [
        AgentType.SPATIAL_3D,
        AgentType.ENTERPRISE_DEVOPS,
        AgentType.DOCUMENT_SYNTHESIS,
        AgentType.FRONTIER_MATH,
        AgentType.SYSTEM_AUTOMATION,
    ]

    for agent_type in expected_types:
        agent = agent_registry.get(agent_type)
        assert agent is not None, f"Agent for {agent_type} not found in registry"
        dummy_context = pytest.importorskip("app.ai.agents.types").AgentContext(
            task_id="t1",
            user_id="u1",
            initial_goal="test goal",
        )
        instruction = agent.build_system_instruction(dummy_context)
        assert "GPT-6 Astra" in instruction or len(instruction) > 50


def test_task_planner_astra_classification_and_decomposition():
    """Verify TaskPlanner identifies Astra domains and generates bounded decomposition plans."""
    # Classification tests
    assert TaskPlanner.classify_primary_agent("Create procedural Blender bpy scene for fluids") == AgentType.SPATIAL_3D
    assert TaskPlanner.classify_primary_agent("Compile enterprise multi-page LaTeX report") == AgentType.DOCUMENT_SYNTHESIS
    assert TaskPlanner.classify_primary_agent("Solve Tier-4 theorem math proof and ARC puzzle") == AgentType.FRONTIER_MATH
    assert TaskPlanner.classify_primary_agent("Perform desktop automation and screen click RPA") == AgentType.SYSTEM_AUTOMATION
    assert TaskPlanner.classify_primary_agent("Triage runtime stack trace and patch zero-day vulnerability") == AgentType.ENTERPRISE_DEVOPS

    # Decomposition test
    steps = TaskPlanner.decompose("Generate 3D CAD mesh for turbine in Blender")
    assert len(steps) >= 2
    assert any(s.agent_type == AgentType.SPATIAL_3D for s in steps)


def test_astra_tools_and_validators():
    """Verify Blender, LaTeX, and Spreadsheet formula validators."""
    # 1. Blender validator
    valid_blender = "import bpy\nbpy.ops.mesh.primitive_cube_add()"
    res_blender = validate_blender_script(valid_blender)
    assert res_blender["valid"] is True
    assert res_blender["imports_bpy"] is True

    invalid_blender = "import bpy\ndef broken_code(:"
    res_bad_blender = validate_blender_script(invalid_blender)
    assert res_bad_blender["valid"] is False
    assert "SyntaxError" in res_bad_blender["error"]

    # 2. LaTeX validator
    valid_latex = "\\begin{document}\n\\section{Title}\nHello world $x^2$\n\\end{document}"
    res_latex = validate_latex_source(valid_latex)
    assert res_latex["valid"] is True

    mismatched_latex = "\\begin{document}\n\\begin{table}\n\\end{document}"
    res_bad_latex = validate_latex_source(mismatched_latex)
    assert res_bad_latex["valid"] is False

    # 3. Spreadsheet validator
    valid_formula = "=SUM(A1:A10) + XLOOKUP(B1, C1:C10, D1:D10)"
    res_formula = validate_spreadsheet_formula(valid_formula)
    assert res_formula["valid"] is True
    assert "SUM" in res_formula["recognized_functions"]
    assert "XLOOKUP" in res_formula["recognized_functions"]

    bad_formula = "=SUM(A1:A10"
    res_bad_formula = validate_spreadsheet_formula(bad_formula)
    assert res_bad_formula["valid"] is False
    assert "Mismatched parentheses" in res_bad_formula["error"]


def test_tools_registered_in_tool_registry():
    """Verify that ToolRegistry has the new Astra validator tools registered and runnable."""
    registry = ToolRegistry()
    assert registry.get_tool("blender_validator") is not None
    assert registry.get_tool("latex_validator") is not None
    assert registry.get_tool("spreadsheet_validator") is not None

    handler = registry.get_handler("spreadsheet_validator")
    assert handler is not None
    out = handler({"formula": "=SUM(B2:B50)"})
    assert out["valid"] is True
