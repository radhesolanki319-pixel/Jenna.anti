"""Comprehensive unit and integration tests for Memory Foundation & Semantic Retrieval."""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import BaseEmbeddingProvider, EmbeddingError, EmbeddingProviderUnavailableError
from app.ai.embeddings.gemini_embedding import GeminiEmbeddingProvider
from app.ai.embeddings.openai_embedding import OpenAIEmbeddingProvider
from app.ai.embeddings.registry import get_embedding_provider
from app.ai.memory.relevance import DEFAULT_WEIGHTS, RelevanceScorer, ScoringWeights
from app.ai.memory.working_memory import WorkingMemoryManager
from app.main import app
from app.models.memory import Memory, MemoryType
from app.models.users import User
from app.repositories.memory_repo import MemoryRepository
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService
from app.services.memory_service import MemoryService


class MockDeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic embedding provider for fast, reliable unit testing."""

    def __init__(self, dimensions: int = 768) -> None:
        self._dimensions = dimensions

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-embedding-v1"

    def get_dimensions(self) -> int:
        return self._dimensions

    def _generate_vector(self, text: str) -> list[float]:
        # Generate normalized deterministic vector from text hash
        vec = [0.0] * self._dimensions
        h = hash(text) % 1000
        # Set distinct non-zero coordinates
        idx = abs(h) % self._dimensions
        vec[idx] = 1.0
        return vec

    async def embed_text(self, text: str) -> list[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(t) for t in texts]

    async def health_check(self) -> bool:
        return True


# ============================================================================
# 1. Relevance Scoring Tests
# ============================================================================

def test_relevance_scorer_recency_decay():
    """Verify exponential recency decay with 7-day half life."""
    now = datetime.now(timezone.utc)

    # 0 days elapsed -> 1.0
    score_0 = RelevanceScorer.calculate_recency(now, reference_time=now, half_life_days=7.0)
    assert pytest.approx(score_0, 0.01) == 1.0

    # 7 days elapsed -> 0.5
    seven_days_ago = now - timedelta(days=7)
    score_7 = RelevanceScorer.calculate_recency(seven_days_ago, reference_time=now, half_life_days=7.0)
    assert pytest.approx(score_7, 0.01) == 0.5

    # 14 days elapsed -> 0.25
    fourteen_days_ago = now - timedelta(days=14)
    score_14 = RelevanceScorer.calculate_recency(fourteen_days_ago, reference_time=now, half_life_days=7.0)
    assert pytest.approx(score_14, 0.01) == 0.25


def test_relevance_scorer_compound_calculation():
    """Verify formula: compound_score = w_s*sim + w_i*imp + w_r*rec + w_c*conf."""
    now = datetime.now(timezone.utc)
    weights = ScoringWeights(similarity=0.5, importance=0.2, recency=0.2, confidence=0.1)

    # Perfect match at t=0: sim=1.0, imp=1.0, rec=1.0, conf=1.0 -> 1.0
    score, breakdown = RelevanceScorer.compute_score(
        similarity=1.0,
        importance=1.0,
        confidence=1.0,
        timestamp=now,
        weights=weights,
        reference_time=now,
    )
    assert pytest.approx(score, 0.001) == 1.0
    assert breakdown["similarity"] == 1.0
    assert breakdown["compound_score"] == 1.0

    # Partial score
    score_part, breakdown_part = RelevanceScorer.compute_score(
        similarity=0.8,
        importance=0.6,
        confidence=0.9,
        timestamp=now,  # recency = 1.0
        weights=weights,
        reference_time=now,
    )
    # Expected: 0.5*0.8 + 0.2*0.6 + 0.2*1.0 + 0.1*0.9 = 0.40 + 0.12 + 0.20 + 0.09 = 0.81
    assert pytest.approx(score_part, 0.01) == 0.81


# ============================================================================
# 2. Embedding Provider & Registry Tests
# ============================================================================

def test_embedding_provider_registry():
    """Check registry returns correct provider classes."""
    gemini = get_embedding_provider("gemini")
    assert isinstance(gemini, GeminiEmbeddingProvider)
    assert gemini.provider_name == "gemini"

    openai = get_embedding_provider("openai")
    assert isinstance(openai, OpenAIEmbeddingProvider)
    assert openai.provider_name == "openai"

    with pytest.raises(EmbeddingError):
        get_embedding_provider("unsupported_provider_xyz")


@pytest.mark.asyncio
async def test_embedding_provider_unconfigured_behavior():
    """Ensure unconfigured providers raise EmbeddingProviderUnavailableError without fake data."""
    gemini = GeminiEmbeddingProvider(api_key=None)
    gemini._api_key = None
    with pytest.raises(EmbeddingProviderUnavailableError):
        await gemini.embed_text("test")

    openai = OpenAIEmbeddingProvider(api_key=None)
    openai._api_key = None
    with pytest.raises(EmbeddingProviderUnavailableError):
        await openai.embed_text("test")


# ============================================================================
# 3. Short-Term Working Memory Tests
# ============================================================================

@pytest.mark.asyncio
async def test_working_memory_manager():
    """Test setting, getting, listing, and deleting working memory items."""
    wm = WorkingMemoryManager()
    user_id = str(uuid.uuid4())
    conv_id = str(uuid.uuid4())

    # Global user scope
    await wm.set_item(user_id=user_id, key="current_topic", value="Machine Learning")
    val = await wm.get_item(user_id=user_id, key="current_topic")
    assert val == "Machine Learning"

    # Conversation-specific scope
    await wm.set_item(user_id=user_id, key="draft_code", value="print('hello')", conversation_id=conv_id)
    conv_val = await wm.get_item(user_id=user_id, key="draft_code", conversation_id=conv_id)
    assert conv_val == "print('hello')"

    # Check listing
    items = await wm.list_items(user_id=user_id)
    assert "current_topic" in items

    # Clear
    await wm.clear(user_id=user_id)
    cleared_val = await wm.get_item(user_id=user_id, key="current_topic")
    assert cleared_val is None


# ============================================================================
# 4. Database CRUD & User Isolation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_memory_repository_crud_and_isolation():
    """Verify memory persistence and strict user isolation."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        # Create User A and User B
        email_a = f"mem_a_{uuid.uuid4().hex[:8]}@example.com"
        email_b = f"mem_b_{uuid.uuid4().hex[:8]}@example.com"
        user_a, _, _ = await auth_service.register(RegisterRequest(email=email_a, password="SecurePassword123!"))
        user_b, _, _ = await auth_service.register(RegisterRequest(email=email_b, password="SecurePassword123!"))
        await session.commit()

        repo = MemoryRepository(session)

        # 1. User A creates a memory
        mem_a = await repo.create_memory(
            user_id=user_a.id,
            memory_type=MemoryType.PREFERENCE.value,
            content="User prefers Python over TypeScript for backend development.",
            summary="Prefers Python for backend",
            importance=0.9,
            confidence=0.95,
        )
        await session.commit()
        assert mem_a.id is not None
        assert mem_a.user_id == user_a.id

        # 2. Strict isolation: User B cannot retrieve User A's memory
        mem_b_view = await repo.get_memory(memory_id=mem_a.id, user_id=user_b.id)
        assert mem_b_view is None

        # 3. User B list is empty
        items_b, total_b = await repo.list_memories(user_id=user_b.id)
        assert total_b == 0
        assert len(items_b) == 0

        # 4. User A list contains memory
        items_a, total_a = await repo.list_memories(user_id=user_a.id)
        assert total_a == 1
        assert items_a[0].id == mem_a.id

        # 5. User A updates memory
        updated_a = await repo.update_memory(
            memory_id=mem_a.id,
            user_id=user_a.id,
            importance=0.95,
            summary="Updated preference",
        )
        await session.commit()
        assert updated_a is not None
        assert updated_a.importance == 0.95
        assert updated_a.summary == "Updated preference"

        # 6. User B cannot update User A's memory
        updated_b = await repo.update_memory(
            memory_id=mem_a.id,
            user_id=user_b.id,
            importance=0.1,
        )
        assert updated_b is None

        # 7. User B cannot delete User A's memory
        del_b = await repo.delete_memory(memory_id=mem_a.id, user_id=user_b.id)
        assert del_b is False

        # 8. User A deletes memory
        del_a = await repo.delete_memory(memory_id=mem_a.id, user_id=user_a.id)
        await session.commit()
        assert del_a is True

        post_del = await repo.get_memory(memory_id=mem_a.id, user_id=user_a.id)
        assert post_del is None


# ============================================================================
# 5. Semantic Vector Search & Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_memory_service_semantic_search():
    """Verify semantic search retrieves relevant memories with deterministic embeddings."""
    from app.core.database import AsyncSessionLocal

    mock_provider = MockDeterministicEmbeddingProvider(dimensions=768)

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        email = f"mem_sem_{uuid.uuid4().hex[:8]}@example.com"
        user, _, _ = await auth_service.register(RegisterRequest(email=email, password="SecurePassword123!"))
        await session.commit()

        service = MemoryService(session=session, embedding_provider=mock_provider)

        # Create two distinct memories
        mem1 = await service.create_memory(
            user_id=user.id,
            content="Alice's favorite coffee is a flat white with oat milk.",
            memory_type=MemoryType.PREFERENCE.value,
            importance=0.8,
        )
        mem2 = await service.create_memory(
            user_id=user.id,
            content="The project server is located in Frankfurt datacenter zone B.",
            memory_type=MemoryType.FACT.value,
            importance=0.6,
        )

        assert mem1.embedding is not None
        assert mem2.embedding is not None

        # Search for exact coffee match
        results = await service.search_semantic(
            user_id=user.id,
            query="Alice's favorite coffee is a flat white with oat milk.",
            limit=5,
            threshold=0.3,
        )

        assert len(results) > 0
        top_match = results[0]
        assert top_match.memory.id == mem1.id
        assert top_match.score > 0.6
        assert "similarity" in top_match.breakdown
        assert "importance" in top_match.breakdown
        assert "recency" in top_match.breakdown

        # Context retrieval helper
        context_snippets = await service.get_relevant_context(
            user_id=user.id,
            query="Alice's favorite coffee is a flat white with oat milk.",
            limit=2,
        )
        assert len(context_snippets) > 0
        assert any("flat white" in s for s in context_snippets)


# ============================================================================
# 6. Memory REST API Endpoints Tests
# ============================================================================

@pytest.mark.asyncio
async def test_memory_api_full_flow():
    """Test full HTTP API lifecycle: create, get, list, search, patch, delete, working memory."""
    from app.core.database import AsyncSessionLocal

    mock_provider = MockDeterministicEmbeddingProvider(dimensions=768)

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        email = f"mem_api_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"
        user, _, _ = await auth_service.register(RegisterRequest(email=email, password=password))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 200

        # Override embedding provider in MemoryService dependency for tests
        from app.routers.memory import get_memory_service
        def override_service(db: AsyncSession = pytest.importorskip("fastapi").Depends(pytest.importorskip("app.core.database").get_db)):
            return MemoryService(session=db, embedding_provider=mock_provider)

        app.dependency_overrides[get_memory_service] = override_service

        try:
            # 1. Create memory
            create_payload = {
                "content": "User prefers dark theme across all applications.",
                "memory_type": "PREFERENCE",
                "summary": "Dark theme preference",
                "importance": 0.85,
                "confidence": 0.95,
            }
            res_create = await client.post("/api/v1/memory", json=create_payload)
            assert res_create.status_code == 201
            created_data = res_create.json()
            mem_id = created_data["id"]
            assert created_data["content"] == create_payload["content"]
            assert created_data["importance"] == 0.85
            assert created_data["has_embedding"] is True

            # 2. Get memory
            res_get = await client.get(f"/api/v1/memory/{mem_id}")
            assert res_get.status_code == 200
            assert res_get.json()["id"] == mem_id

            # 3. List memories
            res_list = await client.get("/api/v1/memory")
            assert res_list.status_code == 200
            list_data = res_list.json()
            assert list_data["total"] >= 1
            assert any(item["id"] == mem_id for item in list_data["items"])

            # 4. Search memories
            res_search = await client.post(
                "/api/v1/memory/search",
                json={
                    "query": "User prefers dark theme across all applications.",
                    "limit": 5,
                    "threshold": 0.2,
                },
            )
            assert res_search.status_code == 200
            search_data = res_search.json()
            assert search_data["count"] >= 1
            assert search_data["results"][0]["memory"]["id"] == mem_id

            # 5. Patch memory
            res_patch = await client.patch(
                f"/api/v1/memory/{mem_id}",
                json={"importance": 0.99, "summary": "Strong dark theme preference"},
            )
            assert res_patch.status_code == 200
            assert res_patch.json()["importance"] == 0.99
            assert res_patch.json()["summary"] == "Strong dark theme preference"

            # 6. Working memory operations
            res_wm_set = await client.post(
                "/api/v1/memory/working",
                json={"key": "active_tool", "value": "calculator", "ttl_seconds": 3600},
            )
            assert res_wm_set.status_code == 200

            res_wm_get = await client.get("/api/v1/memory/working")
            assert res_wm_get.status_code == 200
            assert res_wm_get.json()["items"].get("active_tool") == "calculator"

            res_wm_clear = await client.delete("/api/v1/memory/working")
            assert res_wm_clear.status_code == 200

            # 7. Delete memory
            res_del = await client.delete(f"/api/v1/memory/{mem_id}")
            assert res_del.status_code == 204

            # Verify 404 on deleted item
            res_get_deleted = await client.get(f"/api/v1/memory/{mem_id}")
            assert res_get_deleted.status_code == 404

        finally:
            app.dependency_overrides.pop(get_memory_service, None)
