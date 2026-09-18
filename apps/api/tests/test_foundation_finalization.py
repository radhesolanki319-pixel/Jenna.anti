"""Tests for Phase 5: Foundation Finalization, Future Domain Interfaces,
Domain Events, 3-Tier Permissions, and Audit Metadata Sanitization.
"""

import uuid
import pytest
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from app.core.database import AsyncSessionLocal
from app.core.permissions import Permission, Role
from app.core.security import sanitize_audit_metadata
from app.events import (
    DomainEvent,
    DomainEventType,
    AIResponseEvent,
    AgentStartedEvent,
    ToolRequestedEvent,
    MemoryCreatedEvent,
    DeviceEvent,
    TaskCreatedEvent,
    VoiceEvent,
    VisionEvent,
)
from app.interfaces import (
    AIProvider,
    AIGenerationResult,
    AIProviderMetadata,
    MemoryProvider,
    MemoryRecord,
    MemorySearchResult,
    AgentRunner,
    AgentRun,
    AgentStatus,
    AgentTaskResult,
    ToolExecutor,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    DeviceController,
    DeviceMetadata,
    DeviceStatus,
    DeviceType,
    DeviceCommandResult,
    VisionProvider,
    VisionAnalysisResult,
    CameraContext,
    BoundingBox,
    VoiceProvider,
    AudioTranscription,
    VoiceProfile,
    TaskScheduler,
    ScheduledTask,
    TaskStatus,
    PermissionService,
    AuthorizationDecision,
    PermissionEvaluationResult,
)
from app.services.permission_service import DefaultPermissionService, get_permission_service
from app.repositories.audit_repo import AuditEventRepository


# ==============================================================================
# 1. Future Domain Interfaces Tests
# ==============================================================================

class DummyAIProvider(AIProvider):
    async def generate_text(
        self,
        prompt: str,
        context: list[dict[str, str]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIGenerationResult:
        return AIGenerationResult(
            content="AI response",
            model="dummy-v1",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

    async def generate_stream(
        self,
        prompt: str,
        context: list[dict[str, str]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        yield "chunk"

    async def reason_multimodal(
        self,
        prompt: str,
        images: list[bytes | str],
        model: str | None = None,
        **kwargs: Any,
    ) -> AIGenerationResult:
        return AIGenerationResult(content="Multimodal response", model="dummy-v1")

    def get_metadata(self) -> AIProviderMetadata:
        return AIProviderMetadata(
            provider_name="dummy",
            model_name="dummy-v1",
            context_window=8192,
            supports_streaming=True,
            supports_multimodal=True,
        )


@pytest.mark.asyncio
async def test_ai_provider_interface():
    provider = DummyAIProvider()
    res = await provider.generate_text("Hello")
    assert res.content == "AI response"
    assert res.total_tokens == 15
    meta = provider.get_metadata()
    assert meta.provider_name == "dummy"


class DummyMemoryProvider(MemoryProvider):
    def __init__(self):
        self._storage: dict[str, MemoryRecord] = {}

    async def store(
        self,
        key: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> MemoryRecord:
        rec = MemoryRecord(id=str(uuid.uuid4()), key=key, content=content, metadata=metadata or {}, user_id=user_id)
        self._storage[rec.id] = rec
        return rec

    async def retrieve(self, memory_id: str) -> MemoryRecord | None:
        return self._storage.get(memory_id)

    async def update(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        rec = self._storage[memory_id]
        rec.content = content
        if metadata:
            rec.metadata = metadata
        return rec

    async def delete(self, memory_id: str) -> bool:
        return self._storage.pop(memory_id, None) is not None

    async def search_semantic(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        user_id: str | None = None,
    ) -> list[MemorySearchResult]:
        return [MemorySearchResult(record=r, score=0.95) for r in self._storage.values()][:limit]


@pytest.mark.asyncio
async def test_memory_provider_interface():
    mem = DummyMemoryProvider()
    record = await mem.store(key="city", content="User lives in Munich")
    assert record.content == "User lives in Munich"
    found = await mem.retrieve(record.id)
    assert found is not None
    assert found.content == "User lives in Munich"
    similar = await mem.search_semantic("Munich")
    assert len(similar) == 1
    assert similar[0].score == 0.95
    deleted = await mem.delete(record.id)
    assert deleted is True


class DummyAgentRunner(AgentRunner):
    async def create_run(
        self,
        agent_name: str,
        task: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> AgentRun:
        return AgentRun(run_id="run-123", agent_name=agent_name, task=task, user_id=user_id, status=AgentStatus.PENDING)

    async def execute_task(self, run_id: str) -> AgentTaskResult:
        return AgentTaskResult(run_id=run_id, status=AgentStatus.COMPLETED, output="Task succeeded")

    async def get_status(self, run_id: str) -> AgentRun:
        return AgentRun(run_id=run_id, status=AgentStatus.COMPLETED)

    async def cancel_run(self, run_id: str) -> bool:
        return True


@pytest.mark.asyncio
async def test_agent_runner_interface():
    runner = DummyAgentRunner()
    run = await runner.create_run(agent_name="planner", task="Organize calendar", user_id="u1")
    assert run.run_id == "run-123"
    status_run = await runner.get_status(run.run_id)
    assert status_run.status == AgentStatus.COMPLETED
    result = await runner.execute_task(run.run_id)
    assert result.status == AgentStatus.COMPLETED
    assert result.output == "Task succeeded"


class DummyToolExecutor(ToolExecutor):
    def discover_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="calculator",
                description="Calculates expressions",
                parameters=[ToolParameter(name="expr", type="string", description="expression")],
                requires_permission="EXECUTE",
            )
        ]

    def validate_call(self, tool_name: str, parameters: dict[str, Any]) -> tuple[bool, str | None]:
        return ("expr" in parameters, None)

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: str | None = None,
        permissions: set[str] | None = None,
    ) -> ToolResult:
        return ToolResult(tool_name=tool_name, success=True, data=42)


@pytest.mark.asyncio
async def test_tool_executor_interface():
    executor = DummyToolExecutor()
    tools = executor.discover_tools()
    assert len(tools) == 1
    assert tools[0].name == "calculator"
    valid, err = executor.validate_call("calculator", {"expr": "2+2"})
    assert valid is True
    res = await executor.execute_tool("calculator", {"expr": "2+2"})
    assert res.success is True
    assert res.data == 42


class DummyDeviceController(DeviceController):
    async def list_authorized_devices(self, user_id: str) -> list[DeviceMetadata]:
        return [
            DeviceMetadata(
                device_id="dev-android-01",
                device_type=DeviceType.ANDROID,
                name="Pixel 8 Pro",
                status=DeviceStatus.ONLINE,
                capabilities=["notifications", "screen_read"],
            )
        ]

    async def send_command(
        self,
        device_id: str,
        command: str,
        payload: dict[str, Any] | None = None,
    ) -> DeviceCommandResult:
        return DeviceCommandResult(device_id=device_id, command=command, success=True)

    async def receive_event(self, device_id: str, event_payload: dict[str, Any]) -> None:
        pass

    async def get_device_status(self, device_id: str) -> DeviceMetadata:
        return DeviceMetadata(
            device_id=device_id,
            name="Pixel 8 Pro",
            device_type=DeviceType.ANDROID,
            status=DeviceStatus.ONLINE,
        )


@pytest.mark.asyncio
async def test_device_controller_interface():
    controller = DummyDeviceController()
    devices = await controller.list_authorized_devices("u1")
    assert len(devices) == 1
    assert devices[0].device_type == DeviceType.ANDROID
    cmd = await controller.send_command("dev-android-01", "ping")
    assert cmd.success is True


class DummyVisionProvider(VisionProvider):
    async def analyze_image(
        self,
        image_data: bytes | str,
        prompt: str | None = None,
    ) -> VisionAnalysisResult:
        return VisionAnalysisResult(description="A clean desk setup")

    async def analyze_screen(
        self,
        screen_capture: bytes | str,
        detect_ui_elements: bool = True,
    ) -> VisionAnalysisResult:
        return VisionAnalysisResult(
            description="Screen with submit button",
            detected_elements=[BoundingBox(x=10.0, y=20.0, width=100.0, height=40.0, label="Submit")],
        )

    async def get_camera_context(self) -> CameraContext:
        return CameraContext(is_active=True, resolution="1920x1080", framerate=30)


@pytest.mark.asyncio
async def test_vision_provider_interface():
    vision = DummyVisionProvider()
    res = await vision.analyze_image(b"fake_bytes", "Describe")
    assert res.description == "A clean desk setup"
    screen = await vision.analyze_screen(b"fake_screen")
    assert len(screen.detected_elements) == 1
    assert screen.detected_elements[0].label == "Submit"


class DummyVoiceProvider(VoiceProvider):
    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> AudioTranscription:
        return AudioTranscription(text="Turn on living room light", language="en", confidence=0.98)

    async def stream_speech_to_text(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str | None = None,
    ) -> AsyncIterator[str]:
        yield "Turn on living room light"

    async def text_to_speech(
        self,
        text: str,
        voice_profile: VoiceProfile | None = None,
    ) -> bytes:
        return b"fake_wav_audio"

    async def stream_text_to_speech(
        self,
        text_stream: AsyncIterator[str],
        voice_profile: VoiceProfile | None = None,
    ) -> AsyncIterator[bytes]:
        yield b"chunk"


@pytest.mark.asyncio
async def test_voice_provider_interface():
    voice = DummyVoiceProvider()
    stt = await voice.speech_to_text(b"audio")
    assert stt.text == "Turn on living room light"
    assert stt.confidence == 0.98
    tts = await voice.text_to_speech("Hello")
    assert len(tts) > 0


class DummyTaskScheduler(TaskScheduler):
    async def schedule_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        run_at: datetime | None = None,
        cron_expression: str | None = None,
    ) -> ScheduledTask:
        return ScheduledTask(task_id="task-1", task_type=task_type, payload=payload, cron_expression=cron_expression, status=TaskStatus.SCHEDULED)

    async def cancel_task(self, task_id: str) -> bool:
        return True

    async def get_task_status(self, task_id: str) -> ScheduledTask | None:
        return ScheduledTask(task_id=task_id, status=TaskStatus.SCHEDULED)

    async def list_pending_tasks(self, limit: int = 50) -> list[ScheduledTask]:
        return [ScheduledTask(task_id="task-1", task_type="backup", status=TaskStatus.SCHEDULED)]


@pytest.mark.asyncio
async def test_task_scheduler_interface():
    sched = DummyTaskScheduler()
    t = await sched.schedule_task(task_type="daily_sync", payload={"backup": True}, cron_expression="0 2 * * *")
    assert t.task_type == "daily_sync"
    status_task = await sched.get_task_status(t.task_id)
    assert status_task is not None
    assert status_task.status == TaskStatus.SCHEDULED


# ==============================================================================
# 2. Domain Events Tests
# ==============================================================================

def test_domain_events_all_14_types():
    event_types = [
        DomainEventType.AI_REQUEST,
        DomainEventType.AI_RESPONSE,
        DomainEventType.AGENT_STARTED,
        DomainEventType.AGENT_COMPLETED,
        DomainEventType.TOOL_REQUESTED,
        DomainEventType.TOOL_COMPLETED,
        DomainEventType.MEMORY_CREATED,
        DomainEventType.MEMORY_RETRIEVED,
        DomainEventType.DEVICE_CONNECTED,
        DomainEventType.DEVICE_EVENT,
        DomainEventType.TASK_CREATED,
        DomainEventType.TASK_COMPLETED,
        DomainEventType.VOICE_EVENT,
        DomainEventType.VISION_EVENT,
    ]
    assert len(event_types) == 14

    for et in event_types:
        evt = DomainEvent(
            event_type=et,
            source="test",
            payload={"action": "verify", "type_str": et.value},
        )
        assert evt.event_id is not None
        assert evt.event_type == et
        assert isinstance(evt.timestamp, datetime)
        dumped = evt.model_dump()
        assert dumped["event_type"] == et.value


def test_specialized_domain_event_subclasses():
    ai_evt = AIResponseEvent(
        source="gemini_provider",
        payload={"model": "gemini-1.5-pro", "tokens": 42},
    )
    assert ai_evt.payload["tokens"] == 42
    assert ai_evt.event_type == DomainEventType.AI_RESPONSE

    tool_evt = ToolRequestedEvent(
        source="agent_loop",
        payload={"tool_name": "device_lock", "args": {"device_id": "phone-1"}},
    )
    assert tool_evt.payload["tool_name"] == "device_lock"
    assert tool_evt.event_type == DomainEventType.TOOL_REQUESTED

    mem_evt = MemoryCreatedEvent(
        source="memory_engine",
        payload={"memory_id": "mem-1", "type": "fact"},
    )
    assert mem_evt.payload["type"] == "fact"
    assert mem_evt.event_type == DomainEventType.MEMORY_CREATED


# ==============================================================================
# 3. 3-Tier Permission Evaluation Tests
# ==============================================================================

def test_permission_service_decisions():
    service = DefaultPermissionService()

    # 1. ALLOWED: standard user reading
    res_allowed = service.evaluate_action(role=Role.USER.value, required_permission=Permission.READ)
    assert res_allowed.decision == AuthorizationDecision.ALLOWED
    assert "authorized" in res_allowed.reason

    # 2. DENIED: readonly user trying to write
    res_denied = service.evaluate_action(role=Role.READONLY.value, required_permission=Permission.WRITE)
    assert res_denied.decision == AuthorizationDecision.DENIED
    assert "lacks required permission" in res_denied.reason

    # 3. REQUIRES_CONFIRMATION: sensitive action by admin without confirmation context
    res_confirm = service.evaluate_action(
        role=Role.ADMIN.value,
        required_permission=Permission.SENSITIVE_ACTION,
        is_sensitive=True,
        context={"action_name": "wipe_device"},
    )
    assert res_confirm.decision == AuthorizationDecision.REQUIRES_CONFIRMATION
    assert res_confirm.confirmation_prompt is not None
    assert "wipe_device" in res_confirm.confirmation_prompt

    # 4. ALLOWED: sensitive action by admin WITH confirmation context
    res_confirmed = service.evaluate_action(
        role=Role.ADMIN.value,
        required_permission=Permission.SENSITIVE_ACTION,
        is_sensitive=True,
        context={"action_name": "wipe_device", "confirmed": True},
    )
    assert res_confirmed.decision == AuthorizationDecision.ALLOWED

    # 5. Temporary permission grant test
    test_user_id = str(uuid.uuid4())
    # User normally has no DEVICE_CONTROL permission
    res_before = service.evaluate_action(
        role=Role.USER.value,
        required_permission=Permission.DEVICE_CONTROL,
        context={"user_id": test_user_id},
    )
    assert res_before.decision == AuthorizationDecision.DENIED

    # Grant temporary permission
    service.grant_temporary_permission(test_user_id, Permission.DEVICE_CONTROL, duration_seconds=60)
    res_after = service.evaluate_action(
        role=Role.USER.value,
        required_permission=Permission.DEVICE_CONTROL,
        context={"user_id": test_user_id},
    )
    assert res_after.decision == AuthorizationDecision.ALLOWED
    assert "temporary grant" in res_after.reason

    # Revoke temporary permission
    service.revoke_temporary_permission(test_user_id, Permission.DEVICE_CONTROL)
    res_revoked = service.evaluate_action(
        role=Role.USER.value,
        required_permission=Permission.DEVICE_CONTROL,
        context={"user_id": test_user_id},
    )
    assert res_revoked.decision == AuthorizationDecision.DENIED


# ==============================================================================
# 4. Audit Logging Metadata Sanitization Tests
# ==============================================================================

def test_sanitize_audit_metadata_recursive():
    raw_metadata = {
        "user_email": "admin@jenna.local",
        "action": "login",
        "credentials": {
            "password": "super-secret-password-123",
            "access_token": "bearer-token-xyz-888",
            "nested_list": [
                {"client_secret": "sensitive-oauth-secret", "public_id": "app-100"},
                "plain_string_in_list",
            ],
        },
        "session_cookie": "jenna_session=abcdef123456",
        "api_key": "live-api-key-999",
        "safe_data": {
            "ip_address": "127.0.0.1",
            "browser": "Chrome",
            "attempts": 1,
        },
    }

    sanitized = sanitize_audit_metadata(raw_metadata)

    # Verify sensitive fields are redacted
    assert sanitized["credentials"]["password"] == "[REDACTED]"
    assert sanitized["credentials"]["access_token"] == "[REDACTED]"
    assert sanitized["credentials"]["nested_list"][0]["client_secret"] == "[REDACTED]"
    assert sanitized["session_cookie"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"

    # Verify non-sensitive fields are intact
    assert sanitized["user_email"] == "admin@jenna.local"
    assert sanitized["action"] == "login"
    assert sanitized["credentials"]["nested_list"][0]["public_id"] == "app-100"
    assert sanitized["safe_data"]["ip_address"] == "127.0.0.1"
    assert sanitized["safe_data"]["attempts"] == 1


@pytest.mark.asyncio
async def test_audit_repo_sanitizes_on_log_event():
    async with AsyncSessionLocal() as session:
        repo = AuditEventRepository(session)
        sensitive_meta = {
            "password": "user_plain_password",
            "auth_token": "tok_xyz_123",
            "safe_info": "success",
        }
        event = await repo.log_event(
            event_type="auth",
            action="login_attempt",
            success=True,
            metadata=sensitive_meta,
        )
        await session.commit()

        # Query back the saved event
        saved = await repo.get_by_id(event.id)
        assert saved is not None
        assert saved.metadata_json["password"] == "[REDACTED]"
        assert saved.metadata_json["auth_token"] == "[REDACTED]"
        assert saved.metadata_json["safe_info"] == "success"

        # Cleanup
        await repo.delete(saved)
        await session.commit()
