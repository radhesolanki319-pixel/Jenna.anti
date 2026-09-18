"""Comprehensive test suite for Part 2 Phase 1:
AI Core, Provider Layer, Model Router, Retries, Timeouts, Streaming, and Auth.
"""

import asyncio
import uuid
import pytest
from typing import AsyncIterator
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from app.ai.context import ConversationContext
from app.ai.errors import (
    AIAuthenticationError,
    AIError,
    AIInvalidRequestError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.router import ModelRouter
from app.ai.service import AIService
from app.ai.types import (
    AIModelMetadata,
    AIRequest,
    AIResponse,
    AIStreamChunk,
    AIUsage,
    ChatMessage,
    ModelCapability,
    TaskType,
)
from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.ai_usage import AIUsageLog
from app.repositories.ai_usage_repo import AIUsageRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService


# ==============================================================================
# 1. Mock Provider for Deterministic Testing
# ==============================================================================

class MockProvider(BaseAIProvider):
    def __init__(
        self,
        name: str = "mock_provider",
        available: bool = True,
        response_text: str = "Mock response",
        fail_times: int = 0,
        fail_exception: Exception | None = None,
        delay_seconds: float = 0.0,
    ):
        self._name = name
        self._available = available
        self.response_text = response_text
        self.fail_times = fail_times
        self.failed_count = 0
        self.fail_exception = fail_exception or AIServiceError("Mock upstream failure", provider=name)
        self.delay_seconds = delay_seconds
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(self, request: AIRequest) -> AIResponse:
        self.call_count += 1
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.failed_count < self.fail_times:
            self.failed_count += 1
            raise self.fail_exception

        return AIResponse(
            text=self.response_text,
            provider=self.name,
            model=request.model or "mock-model",
            finish_reason="stop",
            usage=AIUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            request_id=request.request_id,
            latency_ms=25.0,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        self.call_count += 1
        if self.failed_count < self.fail_times:
            self.failed_count += 1
            raise self.fail_exception

        words = self.response_text.split()
        for idx, w in enumerate(words):
            yield AIStreamChunk(delta=w + " ", index=idx)
        yield AIStreamChunk(
            delta="",
            index=len(words),
            finish_reason="stop",
            usage=AIUsage(prompt_tokens=10, completion_tokens=len(words), total_tokens=10 + len(words)),
        )

    def list_models(self) -> list[AIModelMetadata]:
        return [
            AIModelMetadata(
                model_id="mock-model",
                provider=self.name,
                display_name="Mock Model",
                context_window=4096,
                capabilities={ModelCapability.STREAMING},
                default_for_tasks={TaskType.CHAT, TaskType.CODING},
                is_available=self.is_available,
            ),
            AIModelMetadata(
                model_id="mock-reasoner",
                provider=self.name,
                display_name="Mock Reasoner",
                context_window=8192,
                capabilities={ModelCapability.STREAMING},
                default_for_tasks={TaskType.REASONING},
                is_available=self.is_available,
            ),
        ]

    def get_model_info(self, model_id: str) -> AIModelMetadata | None:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return None

    async def health_check(self) -> bool:
        return self.is_available


# ==============================================================================
# 2. Provider Configuration & Availability Tests
# ==============================================================================

def test_gemini_provider_unconfigured_availability():
    p = GeminiProvider(api_key="")
    assert p.is_available is False
    assert p.name == "gemini"
    models = p.list_models()
    assert len(models) > 0
    assert all(m.is_available is False for m in models)


def test_openai_provider_unconfigured_availability():
    p = OpenAIProvider(api_key="")
    assert p.is_available is False
    assert p.name == "openai"
    models = p.list_models()
    assert len(models) > 0
    assert all(m.is_available is False for m in models)


@pytest.mark.asyncio
async def test_unavailable_provider_raises_error():
    p = MockProvider(name="unavail", available=False)
    router = ModelRouter([p])
    service = AIService(router=router)

    req = AIRequest(messages=[ChatMessage(role="user", content="hello")])
    with pytest.raises(AIProviderUnavailableError) as exc_info:
        await service.generate(req)
    assert "unconfigured" in str(exc_info.value).lower() or "no ai providers" in str(exc_info.value).lower()


# ==============================================================================
# 3. ModelRouter & Task Routing Tests
# ==============================================================================

def test_model_router_task_selection():
    p1 = MockProvider(name="mock_p1", available=True)
    router = ModelRouter([p1])

    # Route CHAT task
    prov, model = router.route(task_type=TaskType.CHAT)
    assert prov.name == "mock_p1"
    assert model == "mock-model"

    # Route REASONING task
    prov, model = router.route(task_type=TaskType.REASONING)
    assert prov.name == "mock_p1"
    assert model == "mock-reasoner"

    # Route explicit model override
    prov, model = router.route(preferred_model="custom-override-model")
    assert model == "custom-override-model"


def test_model_router_rejects_unsupported_tasks():
    p1 = MockProvider(name="mock_p1", available=True)
    router = ModelRouter([p1])

    with pytest.raises(AIInvalidRequestError) as exc_info:
        router.route(task_type=TaskType.VISION)
    assert "not supported" in str(exc_info.value)

    with pytest.raises(AIInvalidRequestError) as exc_info:
        router.route(task_type=TaskType.TOOL_USE)
    assert "not supported" in str(exc_info.value)


def test_model_router_fallback_to_available_provider():
    p_offline = MockProvider(name="gemini", available=False)
    p_online = MockProvider(name="openai", available=True)
    router = ModelRouter([p_offline, p_online])

    # Default configured is gemini, but it's offline -> fallback to openai
    prov = router.get_provider()
    assert prov.name == "openai"


# ==============================================================================
# 4. AIService Retries, Timeouts, and Errors
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_service_retries_transient_failures():
    # Fails twice with rate limit, succeeds on 3rd attempt
    mock_p = MockProvider(
        name="retry_p",
        available=True,
        fail_times=2,
        fail_exception=AIRateLimitError("Rate limited", provider="retry_p"),
    )
    router = ModelRouter([mock_p])
    service = AIService(router=router)

    req = AIRequest(messages=[ChatMessage(role="user", content="test")])
    res = await service.generate(req)
    assert res.text == "Mock response"
    assert mock_p.call_count == 3  # 1 initial + 2 retries


@pytest.mark.asyncio
async def test_ai_service_does_not_retry_auth_errors():
    mock_p = MockProvider(
        name="auth_p",
        available=True,
        fail_times=2,
        fail_exception=AIAuthenticationError("Bad API key", provider="auth_p"),
    )
    router = ModelRouter([mock_p])
    service = AIService(router=router)

    req = AIRequest(messages=[ChatMessage(role="user", content="test")])
    with pytest.raises(AIAuthenticationError):
        await service.generate(req)
    assert mock_p.call_count == 1  # Fails immediately without retry


@pytest.mark.asyncio
async def test_ai_service_timeout_handling():
    from app.core.config import settings
    # Provider hangs longer than timeout limit
    mock_p = MockProvider(name="slow_p", available=True, delay_seconds=1.0)
    router = ModelRouter([mock_p])
    service = AIService(router=router)

    with patch.object(settings, "ai_request_timeout_seconds", 0.05):
        with patch.object(settings, "ai_max_retries", 1):
            req = AIRequest(messages=[ChatMessage(role="user", content="test")])
            with pytest.raises((AITimeoutError, AIServiceError)):
                await service.generate(req)


# ==============================================================================
# 5. Streaming Protocol Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_streaming_lifecycle_events():
    mock_p = MockProvider(name="stream_p", available=True, response_text="Hello world Jenna")
    router = ModelRouter([mock_p])
    service = AIService(router=router)

    req = AIRequest(messages=[ChatMessage(role="user", content="stream me")])
    events = []
    async for event in service.stream(req):
        events.append(event)

    assert len(events) >= 3
    # 1. stream.started
    assert events[0]["type"] == "stream.started"
    assert events[0]["provider"] == "stream_p"

    # 2. stream.delta
    deltas = [e for e in events if e["type"] == "stream.delta"]
    assert len(deltas) == 3
    assert deltas[0]["delta"] == "Hello "
    assert deltas[1]["delta"] == "world "
    assert deltas[2]["delta"] == "Jenna "

    # 3. stream.completed
    completed = [e for e in events if e["type"] == "stream.completed"][0]
    assert completed["full_text"] == "Hello world Jenna "
    assert completed["usage"]["total_tokens"] > 0


@pytest.mark.asyncio
async def test_ai_streaming_error_event():
    mock_p = MockProvider(
        name="stream_err_p",
        available=True,
        fail_times=1,
        fail_exception=AIServiceError("Stream connection broke"),
    )
    router = ModelRouter([mock_p])
    service = AIService(router=router)

    req = AIRequest(messages=[ChatMessage(role="user", content="fail stream")])
    events = []
    async for event in service.stream(req):
        events.append(event)

    err_events = [e for e in events if e["type"] == "stream.error"]
    assert len(err_events) == 1
    assert "Stream connection broke" in err_events[0]["message"]


# ==============================================================================
# 6. Usage Tracking & DB Logging Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_usage_logging_in_database():
    async with AsyncSessionLocal() as session:
        # Create test user
        user_repo = UserRepository(session)
        user = await user_repo.create_user(email=f"ai_user_{uuid.uuid4().hex[:6]}@example.com")
        await session.commit()

        mock_p = MockProvider(name="usage_p", available=True, response_text="Usage tracked test")
        router = ModelRouter([mock_p])
        service = AIService(router=router)

        req = AIRequest(messages=[ChatMessage(role="user", content="ping")])
        res = await service.generate(req, user_id=user.id, db=session)
        assert res.usage.total_tokens == 15

        # Check repository aggregation
        usage_repo = AIUsageRepository(session)
        summary = await usage_repo.get_summary_for_user(user.id)
        assert summary["total_requests"] == 1
        assert summary["total_tokens"] == 15
        assert summary["prompt_tokens"] == 10
        assert summary["completion_tokens"] == 5

        # Clean up
        recent = await usage_repo.list_recent(user_id=user.id)
        for log in recent:
            await usage_repo.delete(log)
        await user_repo.delete(user)
        await session.commit()


# ==============================================================================
# 7. Authenticated AI Endpoints Tests (REST)
# ==============================================================================

@pytest.mark.asyncio
async def test_ai_generate_endpoint_requires_authentication():
    with TestClient(app) as client:
        # Request without session cookie -> 401
        resp = client.post(
            "/api/v1/ai/generate",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ai_generate_endpoint_authenticated_flow():
    from httpx import ASGITransport, AsyncClient
    from app.ai.service import get_ai_service

    mock_p = MockProvider(name="mock_endpoint", available=True, response_text="Endpoint success")
    test_service = AIService(router=ModelRouter([mock_p]))

    app.dependency_overrides[get_ai_service] = lambda: test_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg_resp = await client.post(
                "/api/v1/auth/register",
                json={"email": f"ai_auth_{uuid.uuid4().hex[:6]}@example.com", "password": "SecurePassword123!"},
            )
            assert reg_resp.status_code == 201

            resp = await client.post(
                "/api/v1/ai/generate",
                json={
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "temperature": 0.5,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["text"] == "Endpoint success"
            assert data["provider"] == "mock_endpoint"
            assert data["usage"]["total_tokens"] > 0
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


@pytest.mark.asyncio
async def test_ai_models_and_status_endpoints():
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": f"ai_stat_{uuid.uuid4().hex[:6]}@example.com", "password": "SecurePassword123!"},
        )
        assert reg_resp.status_code == 201

        # GET /api/v1/ai/models
        res_models = await client.get("/api/v1/ai/models")
        assert res_models.status_code == 200
        models_data = res_models.json()
        assert isinstance(models_data, list)
        assert len(models_data) > 0

        # GET /api/v1/ai/status
        res_status = await client.get("/api/v1/ai/status")
        assert res_status.status_code == 200
        status_data = res_status.json()
        assert "default_provider" in status_data
        assert "providers" in status_data



# ==============================================================================
# 8. WebSocket AI Streaming Integration
# ==============================================================================

def test_websocket_ai_streaming_integration():
    mock_p = MockProvider(name="ws_ai", available=True, response_text="WebSocket AI output")
    test_service = AIService(router=ModelRouter([mock_p]))

    with patch("app.ai.service.get_ai_service", return_value=test_service):
        with TestClient(app) as client:
            with client.websocket_connect("/api/v1/ws") as ws:
                # 1. Initial handshake
                init = ws.receive_json()
                assert init["type"] == "connection_established"

                # 2. Send ai.generate message
                ws.send_json({
                    "type": "ai.generate",
                    "payload": {
                        "messages": [{"role": "user", "content": "test over websocket"}],
                    },
                })

                # 3. Receive stream.started
                event_start = ws.receive_json()
                assert event_start["type"] == "stream.started"
                assert event_start["provider"] == "ws_ai"

                # 4. Receive deltas
                deltas = []
                while True:
                    evt = ws.receive_json()
                    if evt["type"] == "stream.delta":
                        deltas.append(evt["delta"])
                    elif evt["type"] == "stream.completed":
                        assert "".join(deltas) == "WebSocket AI output "
                        break


# ==============================================================================
# 9. Real Provider Smoke Test (Conditional on Environment Key)
# ==============================================================================

@pytest.mark.asyncio
async def test_real_gemini_provider_smoke_test_if_key_available():
    """Performs real minimal API call if GOOGLE_API_KEY / GEMINI_API_KEY is configured."""
    from app.core.config import settings
    api_key = settings.effective_google_api_key

    if not api_key:
        pytest.skip("No real GOOGLE_API_KEY/GEMINI_API_KEY configured; skipping live smoke test.")

    provider = GeminiProvider(api_key=api_key)
    assert provider.is_available is True

    req = AIRequest(
        messages=[ChatMessage(role="user", content="Reply with exactly 'OK' and nothing else.")],
        max_tokens=100,
        temperature=0.0,
    )
    try:
        res = await provider.generate(req)
        assert res is not None
        assert len(res.text.strip()) > 0
        assert res.provider == "gemini"
        assert res.usage.total_tokens > 0
    except (AIAuthenticationError, AIServiceError, AIRateLimitError):
        pytest.skip("Environment key was present but rejected as invalid/expired, rate limited, or connection failed upstream.")
