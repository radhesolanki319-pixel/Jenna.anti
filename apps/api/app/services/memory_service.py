"""Memory business logic service coordinating embeddings, storage, semantic retrieval, lifecycle, and extraction."""

from datetime import datetime, timezone
import logging
from typing import Any, Sequence
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import BaseEmbeddingProvider, EmbeddingError, EmbeddingProviderUnavailableError
from app.ai.embeddings.registry import get_embedding_provider
from app.ai.memory.deduplication import ComparisonRelation, MemoryDeduplicator
from app.ai.memory.extractor import MemoryExtractor
from app.ai.memory.lifecycle import MemoryLifecycleManager
from app.ai.memory.policy import MemoryPolicy
from app.ai.memory.privacy import PrivacyFilter
from app.ai.memory.relevance import DEFAULT_WEIGHTS, RelevanceScorer, ScoringWeights
from app.ai.memory.working_memory import WorkingMemoryManager, working_memory_manager
from app.core.errors import NotFoundError
from app.models.memory import Memory, MemorySource, MemoryStatus, MemoryType
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import (
    CandidateAction,
    FeedbackType,
    MemoryCandidate,
    SensitivityClassification,
)

logger = logging.getLogger("jenna.services.memory")


class MemorySearchResultItem:
    """Represents a matched memory item with similarity and relevance score breakdown."""

    def __init__(
        self,
        memory: Memory,
        score: float,
        breakdown: dict[str, float],
    ) -> None:
        self.memory = memory
        self.score = score
        self.breakdown = breakdown

        # Pre-capture all attributes so serialization does not trigger ORM expiration reloads
        self.id = memory.id
        self.memory_id = memory.id
        self.user_id = memory.user_id
        self.conversation_id = memory.conversation_id
        self.superseded_by_id = memory.superseded_by_id
        self.status = memory.status
        self.memory_type = memory.memory_type
        self.content = memory.content
        self.summary = memory.summary
        self.importance = memory.importance
        self.confidence = memory.confidence
        self.source = memory.source
        self.metadata_ = memory.metadata_
        self.metadata = memory.metadata_
        self.has_embedding = bool(memory.embedding is not None)
        self.archived_at = memory.archived_at
        self.last_accessed_at = memory.last_accessed_at
        self.created_at = memory.created_at
        self.updated_at = memory.updated_at


class MemoryService:
    """Coordinates memory persistence, semantic vector search, deduplication, and extraction."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: BaseEmbeddingProvider | None = None,
        working_memory: WorkingMemoryManager | None = None,
    ) -> None:
        self.session = session
        self.repo = MemoryRepository(session)
        self._embedding_provider = embedding_provider
        self.working_memory = working_memory or working_memory_manager

    def get_embedding_provider(self) -> BaseEmbeddingProvider | None:
        """Lazily resolve embedding provider."""
        if self._embedding_provider is not None:
            return self._embedding_provider
        try:
            self._embedding_provider = get_embedding_provider()
            return self._embedding_provider
        except Exception as exc:
            logger.debug("Embedding provider not available: %s", exc)
            return None

    async def _safe_embed(self, text: str) -> list[float] | None:
        """Attempt to embed text; returns None if provider is unconfigured or fails."""
        provider = self.get_embedding_provider()
        if not provider:
            return None
        try:
            return await provider.embed_text(text)
        except (EmbeddingProviderUnavailableError, EmbeddingError) as exc:
            logger.warning("Embedding generation skipped: %s", exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error during embedding generation: %s", exc)
            return None

    async def create_memory(
        self,
        user_id: uuid.UUID,
        content: str,
        memory_type: str = MemoryType.FACT.value,
        summary: str | None = None,
        importance: float = 0.5,
        confidence: float = 0.8,
        source: str = MemorySource.MANUAL.value,
        status: str = MemoryStatus.ACTIVE.value,
        conversation_id: uuid.UUID | None = None,
        superseded_by_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Memory:
        """Create and embed a new persistent memory record with privacy validation."""
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")

        # Privacy gate: Reject sensitive credentials
        privacy_res = PrivacyFilter.check_text(content)
        if privacy_res.is_sensitive:
            if privacy_res.classification in (
                SensitivityClassification.SENSITIVE_CREDENTIAL,
                SensitivityClassification.HIGH_RISK,
            ):
                raise ValueError("Security Policy: Cannot store credentials, API keys, or private secrets.")

        # Compute vector embedding if provider is available
        embed_text = f"{summary}\n{content}".strip() if summary else content
        embedding = await self._safe_embed(embed_text)

        mem = await self.repo.create_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            summary=summary,
            importance=importance,
            confidence=confidence,
            source=source,
            status=status,
            conversation_id=conversation_id,
            superseded_by_id=superseded_by_id,
            metadata=metadata or {},
            embedding=embedding,
        )
        await self.session.commit()
        return mem

    async def get_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory:
        """Retrieve memory with strict user isolation."""
        mem = await self.repo.get_memory(memory_id=memory_id, user_id=user_id)
        if not mem:
            raise NotFoundError(message=f"Memory '{memory_id}' not found.")
        return mem

    async def list_memories(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        min_importance: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Memory], int]:
        """List user memories with filtering."""
        return await self.repo.list_memories(
            user_id=user_id,
            memory_type=memory_type,
            status=status,
            search=search,
            min_importance=min_importance,
            limit=limit,
            offset=offset,
        )

    async def update_memory(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str | None = None,
        summary: str | None = None,
        memory_type: str | None = None,
        status: str | None = None,
        superseded_by_id: uuid.UUID | None = None,
        importance: float | None = None,
        confidence: float | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Memory:
        """Update existing memory, re-embedding if content changes."""
        existing = await self.get_memory(memory_id=memory_id, user_id=user_id)

        new_embedding: list[float] | None = None
        if content is not None:
            privacy_res = PrivacyFilter.check_text(content)
            if privacy_res.is_sensitive:
                raise ValueError("Security Policy: Cannot store credentials or secrets.")

        if content is not None or summary is not None:
            effective_content = content if content is not None else existing.content
            effective_summary = summary if summary is not None else existing.summary
            text_to_embed = f"{effective_summary}\n{effective_content}".strip() if effective_summary else effective_content
            new_embedding = await self._safe_embed(text_to_embed)

        updated = await self.repo.update_memory(
            memory_id=memory_id,
            user_id=user_id,
            content=content,
            summary=summary,
            memory_type=memory_type,
            status=status,
            superseded_by_id=superseded_by_id,
            importance=importance,
            confidence=confidence,
            source=source,
            metadata=metadata,
            embedding=new_embedding if new_embedding is not None else None,
        )
        if not updated:
            raise NotFoundError(message=f"Memory '{memory_id}' not found.")
        await self.session.commit()
        return updated

    async def delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft-delete memory record."""
        deleted = await self.repo.soft_delete_memory(memory_id=memory_id, user_id=user_id)
        if not deleted:
            raise NotFoundError(message=f"Memory '{memory_id}' not found.")
        await self.session.commit()

    async def archive_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory:
        """Archive a memory."""
        mem = await self.repo.archive_memory(memory_id=memory_id, user_id=user_id)
        if not mem:
            raise NotFoundError(message=f"Memory '{memory_id}' not found.")
        await self.session.commit()
        return mem

    async def restore_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory:
        """Restore an archived or superseded memory to ACTIVE."""
        mem = await self.repo.restore_memory(memory_id=memory_id, user_id=user_id)
        if not mem:
            raise NotFoundError(message=f"Memory '{memory_id}' not found.")
        await self.session.commit()
        return mem

    async def apply_feedback(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        feedback_type: FeedbackType,
        comment: str | None = None,
        updated_content: str | None = None,
    ) -> Memory:
        """Apply user feedback to adjust memory importance, confidence, or lifecycle state."""
        mem = await self.get_memory(memory_id=memory_id, user_id=user_id)

        # Record feedback in metadata
        current_meta = dict(mem.metadata_ or {})
        history = list(current_meta.get("feedback_history", []))
        history.append({
            "feedback_type": feedback_type.value,
            "comment": comment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        current_meta["feedback_history"] = history

        if feedback_type == FeedbackType.USEFUL:
            new_conf = min(1.0, mem.confidence + 0.1)
            new_imp = min(1.0, mem.importance + 0.1)
            return await self.update_memory(
                memory_id=memory_id,
                user_id=user_id,
                confidence=new_conf,
                importance=new_imp,
                metadata=current_meta,
            )
        elif feedback_type == FeedbackType.INCORRECT:
            new_conf = max(0.0, mem.confidence - 0.4)
            if new_conf < 0.2:
                await self.delete_memory(memory_id=memory_id, user_id=user_id)
                mem.status = MemoryStatus.DELETED.value
                return mem
            return await self.update_memory(
                memory_id=memory_id,
                user_id=user_id,
                confidence=new_conf,
                metadata=current_meta,
            )
        elif feedback_type == FeedbackType.OUTDATED:
            archived = await self.archive_memory(memory_id=memory_id, user_id=user_id)
            archived.metadata_ = current_meta
            await self.session.commit()
            return archived
        elif feedback_type == FeedbackType.FORGET:
            await self.delete_memory(memory_id=memory_id, user_id=user_id)
            mem.status = MemoryStatus.DELETED.value
            return mem
        elif feedback_type == FeedbackType.EDIT:
            if not updated_content or not updated_content.strip():
                raise ValueError("Updated content required for EDIT feedback.")
            return await self.update_memory(
                memory_id=memory_id,
                user_id=user_id,
                content=updated_content.strip(),
                metadata=current_meta,
            )

        return mem

    async def search_semantic(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
        threshold: float = 0.35,
        memory_types: list[str] | None = None,
        statuses: list[str] | None = None,
        weights: ScoringWeights = DEFAULT_WEIGHTS,
    ) -> list[MemorySearchResultItem]:
        """Perform semantic vector similarity search with compound relevance scoring."""
        query = query.strip()
        if not query:
            return []

        provider = self.get_embedding_provider()
        if not provider:
            logger.warning("Cannot perform semantic search: No embedding provider configured.")
            return []

        try:
            query_embedding = await provider.embed_text(query)
        except Exception as exc:
            logger.error("Failed to embed search query: %s", exc)
            return []

        # Retrieve top raw vector candidates
        candidates = await self.repo.search_vector_similarity(
            user_id=user_id,
            query_embedding=query_embedding,
            limit=limit * 3,
            memory_types=memory_types,
            statuses=statuses or [MemoryStatus.ACTIVE.value],
        )

        now = datetime.now(timezone.utc)
        scored_results: list[MemorySearchResultItem] = []
        accessed_ids: list[uuid.UUID] = []

        for mem, similarity in candidates:
            score, breakdown = RelevanceScorer.compute_score(
                similarity=similarity,
                importance=mem.importance,
                confidence=mem.confidence,
                timestamp=mem.last_accessed_at or mem.created_at,
                weights=weights,
                reference_time=now,
            )
            if score >= threshold:
                scored_results.append(
                    MemorySearchResultItem(
                        memory=mem,
                        score=score,
                        breakdown=breakdown,
                    )
                )

        scored_results.sort(key=lambda r: r.score, reverse=True)
        top_results = scored_results[:limit]

        for r in top_results:
            accessed_ids.append(r.memory.id)
            r.memory.last_accessed_at = now
        if accessed_ids:
            await self.repo.touch_accessed(accessed_ids, user_id=user_id)
            await self.session.flush()

        return top_results

    async def extract_candidates(
        self,
        user_id: uuid.UUID,
        content: str,
        conversation_id: uuid.UUID | None = None,
    ) -> list[MemoryCandidate]:
        """Extract memory candidates and compare against user's existing memories."""
        raw_candidates = MemoryExtractor.extract_candidates(content, conversation_id=conversation_id)
        if not raw_candidates:
            return []

        # Fetch user's active memories for deduplication
        existing_memories, _ = await self.repo.list_memories(
            user_id=user_id,
            status=MemoryStatus.ACTIVE.value,
            limit=100,
        )

        final_candidates: list[MemoryCandidate] = []
        for cand in raw_candidates:
            if cand.suggested_action == CandidateAction.IGNORE:
                final_candidates.append(cand)
                continue

            dedup_res = MemoryDeduplicator.compare_with_existing(
                candidate_content=cand.content,
                candidate_type=cand.memory_type,
                existing_memories=existing_memories,
            )

            if dedup_res.relation == ComparisonRelation.DUPLICATE:
                cand.suggested_action = CandidateAction.IGNORE
                cand.reason = f"Duplicate of existing memory ({dedup_res.reason})"
            elif dedup_res.relation == ComparisonRelation.CONFLICT:
                cand.suggested_action = CandidateAction.SUPERSEDE
                cand.supersedes_id = dedup_res.matched_memory_id
                cand.reason = dedup_res.reason

            final_candidates.append(cand)

        return final_candidates

    async def confirm_candidate(
        self,
        user_id: uuid.UUID,
        candidate: MemoryCandidate,
        confirm: bool = True,
    ) -> Memory | None:
        """User confirms or rejects saving an extracted memory candidate."""
        if not confirm:
            return None

        # If candidate supersedes an existing memory, mark existing as superseded
        if candidate.supersedes_id:
            try:
                old_mem = await self.repo.get_memory(candidate.supersedes_id, user_id=user_id)
                if old_mem and old_mem.status == MemoryStatus.ACTIVE.value:
                    old_mem.status = MemoryStatus.SUPERSEDED.value
                    self.session.add(old_mem)
            except Exception as exc:
                logger.warning("Failed to supersede old memory %s: %s", candidate.supersedes_id, exc)

        new_mem = await self.create_memory(
            user_id=user_id,
            content=candidate.content,
            memory_type=candidate.memory_type,
            importance=candidate.importance,
            confidence=candidate.confidence,
            source=candidate.source,
            status=MemoryStatus.ACTIVE.value,
            conversation_id=candidate.conversation_id,
            metadata={
                "extraction_reason": candidate.reason,
                "supersedes_id": str(candidate.supersedes_id) if candidate.supersedes_id else None,
            },
        )

        if candidate.supersedes_id:
            try:
                old_mem = await self.repo.get_memory(candidate.supersedes_id, user_id=user_id)
                if old_mem:
                    old_mem.superseded_by_id = new_mem.id
                    self.session.add(old_mem)
                    await self.session.commit()
            except Exception:
                pass

        return new_mem

    async def process_conversation_memories(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str,
        assistant_response: str | None = None,
    ) -> list[Memory]:
        """Automatic memory extraction and persistence pipeline for conversation turns.

        Runs asynchronously/safely without failing the main conversation.
        """
        created: list[Memory] = []
        try:
            candidates = await self.extract_candidates(
                user_id=user_id,
                content=user_message,
                conversation_id=conversation_id,
            )

            for cand in candidates:
                if cand.suggested_action in (CandidateAction.STORE, CandidateAction.SUPERSEDE):
                    mem = await self.confirm_candidate(
                        user_id=user_id,
                        candidate=cand,
                        confirm=True,
                    )
                    if mem:
                        created.append(mem)
        except Exception as exc:
            logger.error("Error in automatic memory pipeline: %s", exc)

        return created

    async def get_relevant_context(
        self,
        user_id: uuid.UUID,
        query: str,
        conversation_id: uuid.UUID | None = None,
        limit: int = 5,
    ) -> list[str]:
        """Retrieve contextual memory snippets formatted safely as data."""
        snippets: list[str] = []

        # 1. Fetch short-term working memory
        working_items = await self.working_memory.list_items(
            user_id=str(user_id),
            conversation_id=str(conversation_id) if conversation_id else None,
        )
        if working_items:
            for k, val in working_items.items():
                snippets.append(f"[Working Memory] {k}: {val}")

        # 2. Semantic search across active long-term memories
        results = await self.search_semantic(
            user_id=user_id,
            query=query,
            limit=limit,
            threshold=0.35,
            statuses=[MemoryStatus.ACTIVE.value],
        )
        for res in results:
            mem = res.memory
            type_tag = f"[{mem.memory_type}]"
            content_part = mem.summary or mem.content
            snippets.append(f"{type_tag} {content_part}")

        return snippets
