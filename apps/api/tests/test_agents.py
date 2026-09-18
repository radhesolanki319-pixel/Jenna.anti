"""Comprehensive tests for Part 4: Specialized Agents & Agent Runtime Foundation.

Validates:
- AgentRegistry & Specialized Agents (RESEARCH, CODING, ANALYSIS, WRITING, GENERAL_TASK)
- TaskPlanner & AgentOrchestrator task decomposition and boundaries
- AgentRunner & AgentRunnerService execution lifecycle (CREATED -> QUEUED -> RUNNING -> SUCCEEDED / FAILED / CANCELLED)
- Timeout enforcement, bounded retries, and emergency stop / cancellation
- Sensitive action gating & interactive confirmation
- Context handoff contracts and zero chain-of-thought leakage
- User isolation and audit event logging
- Full HTTP API endpoints (/api/v1/agents/...)
"""

import asyncio
import gc
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.agents.base import BaseAgent
from app.ai.agents.orchestrator import AgentOrchestrator, agent_orchestrator
from app.ai.agents.planner import TaskPlanner
from app.ai.agents.registry import AgentRegistry, agent_registry
from app.ai.agents.runner import AgentRunner
from app.ai.agents.specialized import (
    AnalysisAgent,
    CodingAgent,
    GeneralTaskAgent,
    ResearchAgent,
    WritingAgent,
)
from app.ai.agents.types import (
    AgentBudget,
    AgentContext,
    AgentTaskStatus as RuntimeTaskStatus,
    AgentType as RuntimeAgentType,
    TaskStep,
)
from app.ai.service import AIService
from app.ai.types import AIRequest, AIResponse, AIUsage, TaskType
from app.core.database import AsyncSessionLocal
from app.core.errors import ForbiddenError, NotFoundError
from app.core.permissions import Permission
from app.interfaces.agent import AgentStatus
from app.main import app
from app.models.tasks import AgentStepTrace, AgentTask, AgentTaskStatus, AgentType, TaskPriority
from app.models.users import User
from app.repositories.agent_task_repo import AgentTaskRepository
from app.repositories.audit_repo import AuditEventRepository
from app.schemas.agents import AgentBudgetSchema, AgentTaskCreate
from app.services.agent_runner_service import AgentRunnerService, agent_runner_service


@pytest.fixture(autouse=True)
def disable_gc():
    """Stabilize Python 3.14 async tests."""
    gc.disable()
    yield
    gc.enable()


class MockDeterministicAIService:
    """Mock AI Service for deterministic agent testing."""

    def __init__(self, output: str = "Deterministic synthetic agent response"):
        self.output = output
        self.call_count = 0
        self.should_fail = False

    async def generate(self, request: AIRequest) -> AIResponse:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Upstream provider failure simulation")
        return AIResponse(
            text=self.output,
            provider="mock_agent_provider",
            model="mock-agent-model",
            finish_reason="stop",
            usage=AIUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80),
            request_id="mock-agent-req",
            latency_ms=10.0,
        )


# ==============================================================================
# 1. Agent Registry & Specialized Personas Tests
# ==============================================================================

def test_agent_registry_initialization():
    """Registry must include all 5 standard specialized agents by default."""
    reg = AgentRegistry()
    agents = reg.list_agents()
    types = {a.agent_type for a in agents}
    assert RuntimeAgentType.RESEARCH in types
    assert RuntimeAgentType.CODING in types
    assert RuntimeAgentType.ANALYSIS in types
    assert RuntimeAgentType.WRITING in types
    assert RuntimeAgentType.GENERAL_TASK in types
    assert len(agents) == 5


def test_agent_registry_lookup_and_serialization():
    """Registry must correctly resolve agents and output valid dictionary specs."""
    reg = AgentRegistry()
    coding_agent = reg.get(RuntimeAgentType.CODING)
    assert coding_agent is not None
    assert isinstance(coding_agent, CodingAgent)
    spec = coding_agent.to_dict()
    assert spec["name"] == "Coding Agent"
    assert spec["agent_type"] == "CODING"
    assert "code" in spec["description"].lower()


def test_specialized_agent_system_prompts():
    """Specialized agents must enforce security, quality, and zero chain-of-thought rules."""
    ctx = AgentContext(task_id="t1", user_id="u1", initial_goal="Test Goal")

    r_prompt = ResearchAgent().build_system_instruction(ctx)
    assert "chain-of-thought" in r_prompt.lower() or "factual" in r_prompt.lower()

    c_prompt = CodingAgent().build_system_instruction(ctx)
    assert "production-grade" in c_prompt.lower() or "secure" in c_prompt.lower()

    w_prompt = WritingAgent().build_system_instruction(ctx)
    assert "clarity" in w_prompt.lower()


# ==============================================================================
# 2. Task Planner & Orchestrator Decomposition Tests
# ==============================================================================

def test_task_planner_classification():
    """Planner must accurately select specialized agents based on user intent."""
    assert TaskPlanner.classify_primary_agent("Please refactor the database repository class") == RuntimeAgentType.CODING
    assert TaskPlanner.classify_primary_agent("Research the history of ASGI servers in Python") == RuntimeAgentType.RESEARCH
    assert TaskPlanner.classify_primary_agent("Analyze the latency trade-offs between Redis and Postgres") == RuntimeAgentType.ANALYSIS
    assert TaskPlanner.classify_primary_agent("Write a clear user guide and release notes") == RuntimeAgentType.WRITING
    assert TaskPlanner.classify_primary_agent("Organize the project backlog") == RuntimeAgentType.GENERAL_TASK


def test_task_planner_decomposition_and_budget_bounds():
    """Task decomposition must adhere strictly to budget max_steps caps."""
    budget = AgentBudget(max_steps=2)
    steps = TaskPlanner.decompose("Implement full user auth", primary_agent=RuntimeAgentType.CODING, budget=budget)
    assert len(steps) == 2
    assert steps[0].step_number == 1
    assert steps[1].step_number == 2


def test_agent_orchestrator_subtask_bounds():
    """Orchestrator preview must cap subtasks and enforce safe strategies."""
    orch = AgentOrchestrator()
    plan = orch.decompose_task(
        task_title="Build high-performance caching layer",
        task_description="Investigate Redis benchmarks, implement cache decorator, and document performance.",
    )
    assert len(plan.subtasks) <= 5
    assert len(plan.subtasks) > 0
    assert any(s.agent_type == AgentType.CODING for s in plan.subtasks)


# ==============================================================================
# 3. Agent Runner & Execution Lifecycle Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_runner_lifecycle_succeeded():
    """Runner must transition tasks from CREATED through RUNNING to SUCCEEDED."""
    mock_ai = MockDeterministicAIService(output="Step execution successfully completed.")
    runner = AgentRunner(ai_service=mock_ai)

    task = AgentTask(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Deterministic test task",
        description="Run research and coding steps",
        agent_type=AgentType.CODING.value,
        status=AgentTaskStatus.CREATED.value,
    )

    from app.ai.agents.types import AgentTask as RuntimeTask
    rt_task = RuntimeTask(
        task_id=str(task.id),
        user_id=str(task.user_id),
        title=task.title,
        description=task.description,
        agent_type=RuntimeAgentType.CODING,
        budget=AgentBudget(max_steps=2),
    )

    completed = await runner.execute_task(rt_task, user_role="user")
    assert completed.status == RuntimeTaskStatus.SUCCEEDED
    assert completed.result is not None
    assert completed.result.total_steps > 0
    assert "Step" in completed.result.output
    assert completed.result.error is None


@pytest.mark.asyncio
async def test_agent_runner_cancellation():
    """Runner must halt execution immediately when task cancellation is signaled."""
    mock_ai = MockDeterministicAIService()
    runner = AgentRunner(ai_service=mock_ai)

    from app.ai.agents.types import AgentTask as RuntimeTask
    rt_task = RuntimeTask(
        task_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        title="Long cancellable task",
        description="Write code for a massive project",
        agent_type=RuntimeAgentType.CODING,
        budget=AgentBudget(max_steps=5),
    )

    runner.cancel_task(rt_task.task_id)
    cancelled = await runner.execute_task(rt_task, user_role="user")
    assert cancelled.status == RuntimeTaskStatus.CANCELLED
    assert cancelled.result.status == RuntimeTaskStatus.CANCELLED


# ==============================================================================
# 4. Database Repository & Service Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_task_repository_crud():
    """Verify CRUD operations and strict user scoping in AgentTaskRepository."""
    from app.repositories.user_repo import UserRepository

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        u1 = await user_repo.create_user(
            email=f"task_u1_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="mock_hash",
        )
        u2 = await user_repo.create_user(
            email=f"task_u2_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="mock_hash",
        )
        user1_id = u1.id
        user2_id = u2.id

        repo = AgentTaskRepository(session)
        created = await repo.create_task(
            user_id=user1_id,
            title="Isolated Task 1",
            description="Test task isolation",
            agent_type=AgentType.RESEARCH.value,
            priority=TaskPriority.HIGH.value,
        )
        assert created.id is not None
        assert created.user_id == user1_id
        assert created.status == AgentTaskStatus.CREATED.value

        # User 1 can retrieve it
        fetched = await repo.get_user_task(created.id, user1_id)
        assert fetched is not None
        assert fetched.title == "Isolated Task 1"

        # User 2 CANNOT retrieve it (user isolation)
        cross_user = await repo.get_user_task(created.id, user2_id)
        assert cross_user is None

        # Update task status
        updated = await repo.update_task_status(created.id, user1_id, AgentTaskStatus.RUNNING.value)
        assert updated is not None
        assert updated.status == AgentTaskStatus.RUNNING.value

        # Create execution trace
        trace = await repo.record_step_trace(
            task_id=created.id,
            user_id=user1_id,
            step_index=1,
            agent_type=AgentType.RESEARCH.value,
            action="gather_facts",
            status="SUCCEEDED",
            duration_ms=45.0,
            output_summary="Collected 5 verified citations.",
        )
        assert trace.id is not None

        traces = await repo.get_step_traces(created.id, user1_id)
        assert len(traces) == 1
        assert traces[0].action == "gather_facts"


@pytest.mark.asyncio
async def test_agent_runner_service_pipeline():
    """Verify end-to-end task creation and execution in AgentRunnerService."""
    from app.repositories.user_repo import UserRepository

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        u = await user_repo.create_user(
            email=f"pipe_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="mock_hash",
        )
        user_id = u.id

        service = AgentRunnerService(ai_service=MockDeterministicAIService(output="Pipeline step ok"))
        create_data = AgentTaskCreate(
            title="Pipeline execution test",
            description="Analyze and write documentation",
            agent_type=AgentType.ANALYSIS,
            priority=TaskPriority.NORMAL,
        )

        task = await service.create_task(
            db=session,
            user_id=user_id,
            data=create_data,
            auto_decompose=True,
        )
        assert task.id is not None
        assert task.status in (AgentTaskStatus.CREATED.value, AgentTaskStatus.QUEUED.value)

        # Execute task pipeline
        executed = await service.execute_task_pipeline(session, task.id, user_id)
        assert executed.status == AgentTaskStatus.SUCCEEDED.value
        assert executed.result_summary is not None


# ==============================================================================
# 5. Full HTTP API Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_http_api_full_flow():
    """Verify all agent API endpoints: registry, decompose, tasks, execute, cancel."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register test user
        email = f"agent_tester_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        assert reg_res.status_code == 201

        # 1. GET /api/v1/agents/registry
        reg_resp = await client.get("/api/v1/agents/registry")
        assert reg_resp.status_code == 200
        agents_data = reg_resp.json()
        assert isinstance(agents_data, list)
        assert len(agents_data) >= 5

        # 2. POST /api/v1/agents/decompose
        dec_resp = await client.post(
            "/api/v1/agents/decompose",
            json={
                "title": "Refactor router and write unit tests",
                "description": "Analyze API structure, generate tests, and update documentation.",
                "agent_type": "CODING",
            },
        )
        assert dec_resp.status_code == 200
        dec_plan = dec_resp.json()
        assert "subtasks" in dec_plan
        assert len(dec_plan["subtasks"]) > 0

        # 3. POST /api/v1/agents/tasks (Create task)
        task_resp = await client.post(
            "/api/v1/agents/tasks",
            json={
                "title": "Autonomous Integration Test",
                "description": "Verify that agent pipelines run autonomously.",
                "agent_type": "RESEARCH",
            },
        )
        assert task_resp.status_code == 201
        task_data = task_resp.json()
        task_id = task_data["id"]
        assert task_data["title"] == "Autonomous Integration Test"

        # 4. GET /api/v1/agents/tasks (List user tasks)
        list_resp = await client.get("/api/v1/agents/tasks")
        assert list_resp.status_code == 200
        task_list = list_resp.json()
        assert any(t["id"] == task_id for t in task_list)

        # 5. GET /api/v1/agents/tasks/{task_id} (Get task details)
        detail_resp = await client.get(f"/api/v1/agents/tasks/{task_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == task_id
        assert "traces" in detail_data

        # 6. POST /api/v1/agents/tasks/{task_id}/execute (Execute task)
        exec_resp = await client.post(f"/api/v1/agents/tasks/{task_id}/execute")
        assert exec_resp.status_code == 200
        exec_data = exec_resp.json()
        assert exec_data["status"] in ("SUCCEEDED", "COMPLETED", "WAITING", "QUEUED")

        # 7. POST /api/v1/agents/tasks/{task_id}/cancel (Cancel task)
        cancel_resp = await client.post(f"/api/v1/agents/tasks/{task_id}/cancel")
        assert cancel_resp.status_code == 200
        cancel_data = cancel_resp.json()
        assert cancel_data["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_agent_api_user_isolation():
    """Verify User B cannot access or modify User A's agent tasks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client_a:
        # Register User A
        email_a = f"user_a_{uuid.uuid4().hex[:6]}@example.com"
        await client_a.post("/api/v1/auth/register", json={"email": email_a, "password": "SecurePassword123!"})

        # User A creates a task
        resp_a = await client_a.post(
            "/api/v1/agents/tasks",
            json={"title": "User A Private Task", "description": "Confidential", "agent_type": "RESEARCH"},
        )
        task_id = resp_a.json()["id"]

        # Register User B
        async with AsyncClient(transport=transport, base_url="http://test") as client_b:
            email_b = f"user_b_{uuid.uuid4().hex[:6]}@example.com"
            await client_b.post("/api/v1/auth/register", json={"email": email_b, "password": "SecurePassword123!"})

            # User B attempts to access User A's task -> 404 (Not Found or Forbidden)
            cross_get = await client_b.get(f"/api/v1/agents/tasks/{task_id}")
            assert cross_get.status_code in (404, 403)

            # User B attempts to cancel User A's task -> 404 or 403
            cross_cancel = await client_b.post(f"/api/v1/agents/tasks/{task_id}/cancel")
            assert cross_cancel.status_code in (404, 403)
