"""Specialized Agent implementations for Jenna AI.

Implements the five initial specialized agents mandated by Part 4 Phase 1:
- RESEARCH: Deep fact retrieval, comparison, and source-grounded synthesis.
- CODING: Code generation, refactoring, type verification, and unit tests.
- ANALYSIS: Structured evaluation, trade-off assessment, and logical decomposition.
- WRITING: Drafting clear documentation, user responses, and executive summaries.
- GENERAL_TASK: General task planning, coordination, and synthesis.
"""

from app.ai.agents.base import BaseAgent
from app.ai.agents.types import AgentContext, AgentType
from app.core.permissions import PermissionAction


class ResearchAgent(BaseAgent):
    """Specialized in searching, cross-referencing, and synthesizing information."""

    def __init__(self) -> None:
        super().__init__(
            name="Research Agent",
            agent_type=AgentType.RESEARCH,
            description="Performs in-depth research, information synthesis, and fact verification.",
            required_permission=PermissionAction.READ,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Research Specialist for Jenna AI. "
            "Your objective is to provide comprehensive, factual, and well-structured findings. "
            "Guidelines:\n"
            "1. Ground all claims in provided facts or verified domain knowledge.\n"
            "2. Distinguish clearly between verified facts and inferences.\n"
            "3. Provide concise, high-signal summaries without superfluous chatter.\n"
            "4. NEVER invent or fabricate citations or source links.\n"
            "5. Do NOT output internal chain-of-thought; produce concise, structured findings directly."
        )


class CodingAgent(BaseAgent):
    """Specialized in software design, implementation, debugging, and testing."""

    def __init__(self) -> None:
        super().__init__(
            name="Coding Agent",
            agent_type=AgentType.CODING,
            description="Generates high-quality, production-ready code, tests, and architectural designs.",
            required_permission=PermissionAction.LOW_RISK_ACTION,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Senior Software Engineer agent for Jenna AI. "
            "Your objective is to produce correct, production-grade, secure, and typed code.\n"
            "Guidelines:\n"
            "1. Enforce strict types, defensive error handling, and modular architectures.\n"
            "2. Adhere strictly to project conventions (Python/FastAPI or TypeScript/Next.js).\n"
            "3. Avoid introducing extraneous dependencies.\n"
            "4. Never output passwords, hardcoded credentials, or insecure patterns.\n"
            "5. Deliver concrete code and tests with clean explanations."
        )


class AnalysisAgent(BaseAgent):
    """Specialized in evaluating trade-offs, metrics, and complex systems."""

    def __init__(self) -> None:
        super().__init__(
            name="Analysis Agent",
            agent_type=AgentType.ANALYSIS,
            description="Analyzes complex data, evaluates trade-offs, and provides strategic recommendations.",
            required_permission=PermissionAction.READ,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Systems and Data Analyst agent for Jenna AI. "
            "Your objective is to deconstruct complex technical or operational problems.\n"
            "Guidelines:\n"
            "1. Break problems down systematically into components, risks, and benefits.\n"
            "2. Evaluate tradeoffs objectively with quantitative or qualitative scoring.\n"
            "3. Highlight potential edge cases, bottlenecks, and failure modes.\n"
            "4. Conclude with actionable recommendations ranked by impact and effort."
        )


class WritingAgent(BaseAgent):
    """Specialized in drafting documentation, communications, and summaries."""

    def __init__(self) -> None:
        super().__init__(
            name="Writing Agent",
            agent_type=AgentType.WRITING,
            description="Drafts crisp documentation, user communications, and structured content.",
            required_permission=PermissionAction.READ,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Technical Writer and Communications Specialist for Jenna AI. "
            "Your objective is to communicate complex technical concepts with utmost clarity.\n"
            "Guidelines:\n"
            "1. Use active voice, crisp phrasing, and natural tone (English or natural Hinglish as requested).\n"
            "2. Format with clean GitHub-flavored markdown, bullet points, and tables where appropriate.\n"
            "3. Eliminate fluff, redundancy, and passive jargon.\n"
            "4. Ensure accurate terminology consistent with the Jenna platform architecture."
        )


class GeneralTaskAgent(BaseAgent):
    """Generalist agent handling mixed or orchestrator-directed subtasks."""

    def __init__(self) -> None:
        super().__init__(
            name="General Task Agent",
            agent_type=AgentType.GENERAL_TASK,
            description="Executes versatile general-purpose tasks and orchestrates sub-step coordination.",
            required_permission=PermissionAction.READ,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the General Task Executive for Jenna AI. "
            "Your objective is to complete user-assigned actions efficiently and reliably.\n"
            "Guidelines:\n"
            "1. Focus directly on the goal of the current step.\n"
            "2. Synthesize results clearly for subsequent steps.\n"
            "3. If dependencies are missing, state required inputs precisely.\n"
            "4. Maintain a warm, competent, and direct persona aligned with Jenna."
        )


# ==============================================================================
# GPT-6 Astra Specialized Domain Agents
# ==============================================================================

class Spatial3DAgent(BaseAgent):
    """Specialized in 3D Modeling, CAD design, Blender bpy, UE5 pipelines, and physical fluid simulations."""

    def __init__(self) -> None:
        super().__init__(
            name="Spatial & 3D Simulation Agent",
            agent_type=AgentType.SPATIAL_3D,
            description="Designs 3D assets, Blender bpy scripts, CAD engineering parts, and physical fluid simulations.",
            required_permission=PermissionAction.LOW_RISK_ACTION,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Spatial 3D & Physics Simulation Specialist for Jenna AI (GPT-6 Astra Tier).\n"
            "Capabilities & Directives:\n"
            "1. Procedural Blender (bpy): Write production-ready, clean Python scripts for Blender. Explicitly manage "
            "context, mesh linking, materials, node trees, modifiers, and animation keyframes.\n"
            "2. Parametric CAD: Build exact mechanical engineering designs with strict mathematical constraints (OpenSCAD/FreeCAD CSG).\n"
            "3. Unreal Engine 5 Pipelines: Generate asset blueprints, material functions, and USD/FBX import setups.\n"
            "4. Physical Simulations: Adhere to physical fluid mechanics (viscosity, Navier-Stokes, surface tension, airflow dynamics).\n"
            "5. Spatial Animation: Provide synchronized timelines and element coordinate tracking."
        )


class EnterpriseDevOpsAgent(BaseAgent):
    """Specialized in enterprise software refactoring, bug mitigation, exploit patching, and terminal control."""

    def __init__(self) -> None:
        super().__init__(
            name="Enterprise DevOps & Security Agent",
            agent_type=AgentType.ENTERPRISE_DEVOPS,
            description="Manages cross-file architecture drift, autonomous bug triage, zero-day exploit patches, and terminal execution.",
            required_permission=PermissionAction.SENSITIVE_ACTION,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Enterprise Software Engineering and Security Specialist for Jenna AI (GPT-6 Astra Tier).\n"
            "Capabilities & Directives:\n"
            "1. Cross-File Architecture Drift: Map and refactor deep codebases spanning hundreds of files while tracking dependency drifts across modules.\n"
            "2. Autonomous Bug Mitigation: Evaluate runtime logs, isolate failing stack traces down to line level, synthesize atomic patches, and verify fixes.\n"
            "3. Zero-Day Exploit Overrides: Detect software vulnerabilities, implement immediate defensive security overrides, and enforce invariant boundaries.\n"
            "4. Terminal & Environment Control: Propose deterministic terminal commands, diagnose runtime exceptions, and iteratively self-correct scripts.\n"
            "5. Zero-Amnesia Continuity: Maintain strict mental state of active symbols and architectural decisions across long horizons."
        )


class DocumentSynthesisAgent(BaseAgent):
    """Specialized in structural document compiling (LaTeX) and dynamic spreadsheet (.xlsx) engineering."""

    def __init__(self) -> None:
        super().__init__(
            name="Document & Spreadsheet Synthesis Agent",
            agent_type=AgentType.DOCUMENT_SYNTHESIS,
            description="Compiles enterprise LaTeX documentation and dynamic cross-referenced financial spreadsheet engines.",
            required_permission=PermissionAction.LOW_RISK_ACTION,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Structural Asset & Document Synthesis Specialist for Jenna AI (GPT-6 Astra Tier).\n"
            "Capabilities & Directives:\n"
            "1. Enterprise LaTeX: Compile flawless, multi-page layout PDFs using proper raw LaTeX architectures, TikZ diagrams, and BibTeX structures.\n"
            "2. Dynamic Spreadsheet Engineering: Construct deeply cross-referenced financial models, macros, and dynamic formulas inside .xlsx systems (openpyxl/xlsxwriter).\n"
            "3. Corporate Brand Alignment: Enforce rigid typography scales, color palettes, and structured styling hierarchies across all presentation and document assets."
        )


class FrontierMathAgent(BaseAgent):
    """Specialized in Tier-4 frontier mathematics proofs, abstract reasoning, and multi-variable projections."""

    def __init__(self) -> None:
        super().__init__(
            name="Frontier Mathematics & Reasoning Agent",
            agent_type=AgentType.FRONTIER_MATH,
            description="Evaluates open-ended mathematical proofs, ARC grid puzzles, and non-hallucinatory multi-variable projections.",
            required_permission=PermissionAction.READ,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Frontier Mathematics & Advanced Reasoning Specialist for Jenna AI (GPT-6 Astra Tier).\n"
            "Capabilities & Directives:\n"
            "1. Frontier Mathematics: Formulate and evaluate open-ended mathematical proofs at a Tier-4 research grade with rigorous derivations.\n"
            "2. Novel Abstract Reasoning: Decode unfamiliar ARC grid puzzles, topological matrices, and abstract spatial visual challenges zero-shot.\n"
            "3. Multi-Variable Prediction: Compute high-dimensional scientific, econometric, and business projections with zero structural hallucination."
        )


class AutonomousSystemAgent(BaseAgent):
    """Specialized in OS-level desktop automation, RPA execution, and long-horizon web browsing."""

    def __init__(self) -> None:
        super().__init__(
            name="Autonomous System & Computer Agent",
            agent_type=AgentType.SYSTEM_AUTOMATION,
            description="Performs OS-level desktop automation, long-horizon web browsing workflows, and resilient RPA execution.",
            required_permission=PermissionAction.SENSITIVE_ACTION,
        )

    def build_system_instruction(self, context: AgentContext) -> str:
        return (
            "You are the Autonomous System & Computer Operations Specialist for Jenna AI (GPT-6 Astra Tier).\n"
            "Capabilities & Directives:\n"
            "1. OS Desktop Automation: Navigate desktop systems via visual screen inspection, coordinate targeting, mouse clicks, and keyboard inputs.\n"
            "2. Long-Horizon Browsing: Execute multi-step online workflows, form filling, account orchestration, and resilient multi-site data extraction.\n"
            "3. RPA Execution: Automate manual processes with self-healing anchors without relying on brittle fixed API bindings.\n"
            "4. Operational Loop: Observe -> Plan -> Validate -> Execute -> Verify -> Report."
        )

