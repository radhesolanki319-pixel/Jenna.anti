"""Comprehensive tests for Part 2 Phase 2: Jenna Conversation Engine, Personality, and Reasoning Pipeline."""

import json
import uuid
from typing import AsyncIterator
import pytest
from unittest.mock import patch
from httpx import ASGITransport, AsyncClient

from app.ai.classifier import TaskClassifier
from app.ai.context import ContextBuilder
from app.ai.personality import SystemInstructionBuilder
from app.ai.providers.base import BaseAIProvider
from app.ai.router import ModelRouter
from app.ai.service import AIService
from app.ai.types import (
    AIModelMetadata,
    AIRequest,
    AIResponse,
    AIStreamChunk,
    AIUsage,
    ModelCapability,
    TaskType,
)
from app.ai.validator import ResponseValidator
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.main import app
from app.models.conversations import Message
from app.models.users import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.user_repo import UserRepository
from app.schemas.personality import PersonalitySettings
from app.services.auth_service import get_current_user
from app.services.conversation_service import ConversationService


# ==============================================================================
# Mock Provider for Deterministic Testing
# ==============================================================================

class MockConversationProvider(BaseAIProvider):
    """Deterministic mock provider for conversational testing."""

    def __init__(
        self,
        name: str = "mock_chat",
        response_text: str = "Hello! I am Jenna, your personal AI.",
    ) -> None:
        self._name = name
        self.response_text = response_text
        self.received_requests: list[AIRequest] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True

    def list_models(self) -> list[AIModelMetadata]:
        return [
            AIModelMetadata(
                model_id="mock-chat-model",
                provider=self.name,
                display_name="Mock Chat Model",
                context_window=32768,
                capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION},
                default_for_tasks={
                    TaskType.CHAT,
                    TaskType.REASONING,
                    TaskType.CODING,
                    TaskType.ANALYSIS,
                    TaskType.RESEARCH,
                    TaskType.TOOL_REQUEST,
                },
            )
        ]

    def get_model_info(self, model_name: str) -> AIModelMetadata | None:
        models = self.list_models()
        return models[0] if model_name in (models[0].model_id, "default") else None

    async def generate(self, request: AIRequest) -> AIResponse:
        self.received_requests.append(request)
        return AIResponse(
            text=self.response_text,
            provider=self.name,
            model="mock-chat-model",
            finish_reason="stop",
            usage=AIUsage(prompt_tokens=15, completion_tokens=10, total_tokens=25),
            request_id=request.request_id,
            latency_ms=120.0,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        self.received_requests.append(request)
        words = self.response_text.split(" ")
        for idx, word in enumerate(words):
            yield AIStreamChunk(delta=word + " ", index=idx)
        yield AIStreamChunk(
            finish_reason="stop",
            usage=AIUsage(prompt_tokens=15, completion_tokens=len(words), total_tokens=15 + len(words)),
        )


# ==============================================================================
# 1. Personality & System Instruction Tests
# ==============================================================================

def test_personality_system_instruction_builder():
    # Default settings
    builder = SystemInstructionBuilder()
    prompt = builder.build_system_instruction()

    assert "CORE OPERATIONAL PRINCIPLES:" in prompt
    assert "ASSISTANT IDENTITY:" in prompt
    assert "Jenna" in prompt
    assert "LINGUISTIC CAPABILITIES & ADAPTATION (HINDI / HINGLISH / ENGLISH):" in prompt
    assert "kal mujhe yaad dilana" in prompt
    assert "mujhe ye code samjha do" in prompt
    assert "Never pretend to be a biological human" in prompt

    # Custom personality
    custom_settings = PersonalitySettings(
        assistant_name="Jenna Pro",
        personality_style="playful",
        formality="casual",
        preferred_language="hinglish",
        humor_level="witty",
        verbosity="concise",
    )
    custom_builder = SystemInstructionBuilder(custom_settings)
    custom_prompt = custom_builder.build_system_instruction()

    assert "Jenna Pro" in custom_prompt
    assert "delightfully witty" in custom_prompt or "playful" in custom_prompt.lower()
    assert "LANGUAGE OVERRIDE: User explicitly prefers Hinglish" in custom_prompt


def test_system_instruction_with_extension_hooks():
    builder = SystemInstructionBuilder()
    prompt = builder.build_system_instruction(
        memory_context=["User is building a personal AI named Jenna", "User prefers dark mode"],
        tool_instructions=["weather_tool: checks weather for cities"],
        extra_context={"device_mode": "desktop"},
    )

    assert "RETRIEVED MEMORY CONTEXT:" in prompt
    assert "User is building a personal AI named Jenna" in prompt
    assert "AVAILABLE TOOL INSTRUCTIONS:" in prompt
    assert "weather_tool: checks weather for cities" in prompt
    assert "ADDITIONAL CONTEXT:" in prompt
    assert "device_mode: desktop" in prompt


# ==============================================================================
# 2. Task Classification & Language Detection Tests
# ==============================================================================

def test_task_classification():
    # Coding
    assert TaskClassifier.classify_task("mujhe ye code samjha do please") == TaskType.CODING
    assert TaskClassifier.classify_task("def calculate_fibonacci(n: int) -> int:") == TaskType.CODING
    assert TaskClassifier.classify_task("How do I fix this TypeScript type error?") == TaskType.CODING

    # Reasoning
    assert TaskClassifier.classify_task("Why does async I/O scale better than multi-threading?") == TaskType.REASONING
    assert TaskClassifier.classify_task("Solve this logic puzzle step by step") == TaskType.REASONING

    # Tool Request
    assert TaskClassifier.classify_task("kal mujhe yaad dilana to submit report") == TaskType.TOOL_REQUEST
    assert TaskClassifier.classify_task("remind me tomorrow morning at 9am") == TaskType.TOOL_REQUEST
    assert TaskClassifier.classify_task("ye file check karo") == TaskType.TOOL_REQUEST

    # Research
    assert TaskClassifier.classify_task("research the history of quantum computing algorithms") == TaskType.RESEARCH

    # Analysis
    assert TaskClassifier.classify_task("analyze and compare PostgreSQL with MySQL performance") == TaskType.ANALYSIS

    # Chat
    assert TaskClassifier.classify_task("Hey Jenna, how are you doing today?") == TaskType.CHAT
    assert TaskClassifier.classify_task("Namaste! Aaj ka din kaisa hai?") == TaskType.CHAT


def test_language_detection():
    # Hindi Devanagari
    assert TaskClassifier.detect_language("नमस्ते, आप कैसे हैं?") == "hi"

    # Hinglish
    assert TaskClassifier.detect_language("kya haal hai bhai?") == "hinglish"
    assert TaskClassifier.detect_language("kal mujhe yaad dilana to check files") == "hinglish"
    assert TaskClassifier.detect_language("mujhe ye code samjha do") == "hinglish"

    # English
    assert TaskClassifier.detect_language("Can you explain how the event loop works?") == "en"
    assert TaskClassifier.detect_language("What is the capital of France?") == "en"


# ==============================================================================
# 3. Context Builder & Window Trimming Tests
# ==============================================================================

def test_context_builder_trimming():
    builder = ContextBuilder(max_messages=5, max_estimated_chars=1000)

    # Create dummy messages
    dummy_msgs = [
        Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message turn number {i}",
        )
        for i in range(12)
    ]

    context = builder.build_from_db_messages(
        db_messages=dummy_msgs,
        system_instruction="System prompt",
    )

    # Should keep only the last 5 messages
    assert len(context.messages) == 5
    assert context.messages[0].content == "Message turn number 7"
    assert context.messages[-1].content == "Message turn number 11"
    assert context.system_instruction == "System prompt"


# ==============================================================================
# 4. Response Validation Tests
# ==============================================================================

def test_response_validator():
    # Valid response
    valid_text = "Here is an explanation of async/await in Python: It runs on an event loop without blocking threads."
    is_valid, err = ResponseValidator.validate(valid_text)
    assert is_valid is True
    assert err is None

    # Empty response
    is_valid, err = ResponseValidator.validate("   ")
    assert is_valid is False
    assert "empty" in err.lower()

    # Repeated sentences loop
    repetitive_text = "This is a broken loop. " * 8
    is_valid, err = ResponseValidator.validate(repetitive_text)
    assert is_valid is False
    assert "repetition" in err.lower()

    # Sanitization
    dirty = "Hello world!\n\n\n\n\nHow are you?   "
    clean = ResponseValidator.sanitize(dirty)
    assert clean == "Hello world!\n\nHow are you?"


# ==============================================================================
# 5. Database Repositories & User Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_conversation_repositories_and_isolation():
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        # Create valid users in DB to satisfy foreign keys
        user1 = await user_repo.create_user(
            email=f"conv_user1_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=hash_password("Password123!"),
            role="user",
        )
        user2 = await user_repo.create_user(
            email=f"conv_user2_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=hash_password("Password123!"),
            role="user",
        )
        await session.commit()

        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        # 1. Create conversation for user 1
        conv1 = await conv_repo.create_conversation(user_id=user1.id, title="User 1 Conversation")
        await session.commit()
        assert conv1.title == "User 1 Conversation"
        assert conv1.user_id == user1.id

        # 2. Add messages to conv1
        msg1 = await msg_repo.create_message(
            conversation_id=conv1.id,
            role="user",
            content="Hello from User 1",
        )
        await session.commit()
        msg2 = await msg_repo.create_message(
            conversation_id=conv1.id,
            role="assistant",
            content="Hi User 1! How can I assist?",
            model="gemini-2.5-flash",
            provider="gemini",
        )
        await session.commit()

        messages = await msg_repo.list_conversation_messages(conv1.id)
        assert len(messages) == 2
        assert messages[0].content == "Hello from User 1"
        assert messages[1].role == "assistant"

        # 3. User isolation: User 2 cannot access user 1's conversation
        user2_access = await conv_repo.get_user_conversation(conversation_id=conv1.id, user_id=user2.id)
        assert user2_access is None

        # User 2 cannot delete user 1's conversation
        delete_success = await conv_repo.delete_user_conversation(conversation_id=conv1.id, user_id=user2.id)
        assert delete_success is False

        # User 1 CAN access and delete
        user1_access = await conv_repo.get_user_conversation(conversation_id=conv1.id, user_id=user1.id)
        assert user1_access is not None
        assert user1_access.id == conv1.id


# ==============================================================================
# 6. Conversation Service Multi-turn Reasoning Pipeline Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_conversation_service_reasoning_flow():
    mock_p = MockConversationProvider(
        name="test_jenna",
        response_text="Bilkul! Main aapki madad karne ke liye taiyaar hoon.",
    )
    test_ai_service = AIService(router=ModelRouter([mock_p]))

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.create_user(
            email=f"conv_flow_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=hash_password("Password123!"),
            role="user",
        )
        await session.commit()

        conv_service = ConversationService(session=session, ai_service=test_ai_service)

        # 1. Create conversation
        conv = await conv_service.create_conversation(user_id=user.id, title="New Conversation")

        # 2. Send initial message in Hinglish
        user_msg, asst_msg, task_type, provider, model, latency_ms = await conv_service.send_message(
            conversation_id=conv.id,
            user_id=user.id,
            content="mujhe ye code samjha do",
        )

        assert user_msg.role == "user"
        assert asst_msg.role == "assistant"
        assert asst_msg.content == "Bilkul! Main aapki madad karne ke liye taiyaar hoon."
        assert task_type == TaskType.CODING
        assert provider == "test_jenna"

        # Verify auto-title generation from initial prompt
        updated_conv = await conv_service.get_conversation(conv.id, user.id)
        assert updated_conv.title == "mujhe ye code samjha do"

        # 3. Send turn 2 (Multi-turn verification)
        user_msg2, asst_msg2, task_type2, _, _, _ = await conv_service.send_message(
            conversation_id=conv.id,
            user_id=user.id,
            content="Explain in more detail",
        )

        # Check that provider received both turns in context
        last_req = mock_p.received_requests[-1]
        assert len(last_req.messages) >= 3
        roles = [m.role for m in last_req.messages]
        assert roles == ["user", "assistant", "user"]


# ==============================================================================
# 7. FastAPI Conversation REST Endpoints Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_conversation_api_full_flow():
    transport = ASGITransport(app=app)
    mock_p = MockConversationProvider(
        name="api_mock_ai",
        response_text="Here is your requested solution.",
    )
    test_ai_service = AIService(router=ModelRouter([mock_p]))

    with patch("app.services.conversation_service.get_ai_service", return_value=test_ai_service):
        with patch("app.ai.service.get_ai_service", return_value=test_ai_service):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # 1. Register a user to get real cookie session
                email = f"chat_api_{uuid.uuid4().hex[:6]}@jenna.ai"
                reg_res = await client.post(
                    "/api/v1/auth/register",
                    json={"email": email, "password": "SecurePassword123!"},
                )
                assert reg_res.status_code == 201

                # 2. Create conversation
                res = await client.post("/api/v1/conversations", json={"title": "Test Chat API"})
                assert res.status_code == 201
                conv_data = res.json()
                conv_id = conv_data["id"]
                assert conv_data["title"] == "Test Chat API"

                # 3. List conversations
                list_res = await client.get("/api/v1/conversations")
                assert list_res.status_code == 200
                conv_list = list_res.json()
                assert any(c["id"] == conv_id for c in conv_list)

                # 4. Send message via POST /conversations/{id}/messages
                msg_res = await client.post(
                    f"/api/v1/conversations/{conv_id}/messages",
                    json={"content": "Can you design a clean architecture for me?"},
                )
                assert msg_res.status_code == 200
                msg_json = msg_res.json()
                assert msg_json["user_message"]["content"] == "Can you design a clean architecture for me?"
                assert msg_json["assistant_message"]["content"] == "Here is your requested solution."
                assert msg_json["provider"] == "api_mock_ai"

                # 5. Stream message via POST /conversations/{id}/stream (SSE)
                stream_res = await client.post(
                    f"/api/v1/conversations/{conv_id}/stream",
                    json={"content": "Stream this response please"},
                )
                assert stream_res.status_code == 200
                lines = stream_res.text.strip().split("\n\n")
                events = []
                for line in lines:
                    if line.startswith("data:"):
                        events.append(json.loads(line[5:].strip()))

                event_types = [e["type"] for e in events]
                assert "stream.started" in event_types
                assert "stream.delta" in event_types
                assert "stream.completed" in event_types

                # 6. Fetch conversation detail with messages
                detail_res = await client.get(f"/api/v1/conversations/{conv_id}")
                assert detail_res.status_code == 200
                detail_json = detail_res.json()
                assert detail_json["total_messages"] >= 4

                # 7. Update conversation title
                patch_res = await client.patch(
                    f"/api/v1/conversations/{conv_id}",
                    json={"title": "Renamed Architecture Discussion"},
                )
                assert patch_res.status_code == 200
                assert patch_res.json()["title"] == "Renamed Architecture Discussion"

                # 8. Personality settings endpoint
                settings_res = await client.get("/api/v1/settings/personality")
                assert settings_res.status_code == 200
                settings_json = settings_res.json()
                assert settings_json["settings"]["assistant_name"] == "Jenna"

                put_settings_res = await client.put(
                    "/api/v1/settings/personality",
                    json={
                        "assistant_name": "Jenna AI",
                        "personality_style": "warm",
                        "response_style": "conversational",
                        "preferred_language": "hinglish",
                        "preferred_locale": "en-IN",
                        "verbosity": "detailed",
                        "formality": "casual",
                        "humor_level": "subtle",
                    },
                )
                assert put_settings_res.status_code == 200
                assert put_settings_res.json()["settings"]["assistant_name"] == "Jenna AI"
                assert put_settings_res.json()["settings"]["preferred_language"] == "hinglish"

                # 9. Delete conversation
                del_res = await client.delete(f"/api/v1/conversations/{conv_id}")
                assert del_res.status_code == 200

                # 10. Verify 404 after deletion
                verify_del = await client.get(f"/api/v1/conversations/{conv_id}")
                assert verify_del.status_code == 404


@pytest.mark.asyncio
async def test_conversation_api_user_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client1:
        # User 1 registers and creates a conversation
        email1 = f"user1_{uuid.uuid4().hex[:6]}@jenna.ai"
        r1 = await client1.post("/api/v1/auth/register", json={"email": email1, "password": "Password123!"})
        assert r1.status_code == 201

        conv_res = await client1.post("/api/v1/conversations", json={"title": "User 1 Private Thread"})
        assert conv_res.status_code == 201
        conv_id = conv_res.json()["id"]

    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        # User 2 registers
        email2 = f"user2_{uuid.uuid4().hex[:6]}@jenna.ai"
        r2 = await client2.post("/api/v1/auth/register", json={"email": email2, "password": "Password123!"})
        assert r2.status_code == 201

        # User 2 attempts to read User 1's conversation -> 404
        get_res = await client2.get(f"/api/v1/conversations/{conv_id}")
        assert get_res.status_code == 404

        # User 2 attempts to send message to User 1's conversation -> 404
        msg_res = await client2.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "Malicious intrusion attempt"},
        )
        assert msg_res.status_code == 404

        # User 2 attempts to delete User 1's conversation -> 404
        del_res = await client2.delete(f"/api/v1/conversations/{conv_id}")
        assert del_res.status_code == 404
