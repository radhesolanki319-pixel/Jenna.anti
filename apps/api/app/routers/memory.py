"""Memory API Router: CRUD, semantic search, working memory, extraction, lifecycle, and feedback."""

import logging
from typing import Any
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.users import User
from app.schemas.memory import (
    MemoryActionResponse,
    MemoryCandidate,
    MemoryConfirmRequest,
    MemoryCreateRequest,
    MemoryExtractRequest,
    MemoryExtractResponse,
    MemoryFeedbackRequest,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResultItemResponse,
    MemoryUpdateRequest,
    WorkingMemoryResponse,
    WorkingMemorySetRequest,
)
from app.services.auth_service import get_current_user
from app.services.memory_service import MemoryService

logger = logging.getLogger("jenna.memory_router")

router = APIRouter(prefix="/memory", tags=["memory"])


def get_memory_service(db: AsyncSession = Depends(get_db)) -> MemoryService:
    """Dependency provider for MemoryService."""
    return MemoryService(session=db)


@router.post(
    "",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new memory",
    description="Creates a persistent memory with automatic semantic vector embedding generation and privacy gate.",
)
async def create_memory(
    payload: MemoryCreateRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    mem = await service.create_memory(
        user_id=current_user.id,
        content=payload.content,
        memory_type=payload.memory_type.value,
        summary=payload.summary,
        importance=payload.importance,
        confidence=payload.confidence,
        source=payload.source,
        status=payload.status.value,
        conversation_id=payload.conversation_id,
        metadata=payload.metadata,
    )
    return MemoryResponse.from_model(mem)


@router.get(
    "",
    response_model=MemoryListResponse,
    summary="List memories",
    description="Retrieve paginated memories with optional type, status, search query, and importance filters.",
)
async def list_memories(
    memory_type: str | None = Query(default=None, description="Filter by memory type"),
    status: str | None = Query(default=None, description="Filter by status (ACTIVE, ARCHIVED, SUPERSEDED, ALL)"),
    search: str | None = Query(default=None, description="Search term in content or summary"),
    min_importance: float | None = Query(default=None, ge=0.0, le=1.0, description="Minimum importance filter"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryListResponse:
    items, total = await service.list_memories(
        user_id=current_user.id,
        memory_type=memory_type,
        status=status,
        search=search,
        min_importance=min_importance,
        limit=limit,
        offset=offset,
    )
    return MemoryListResponse(
        items=[MemoryResponse.from_model(m) for m in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/search",
    response_model=MemorySearchResponse,
    summary="Semantic vector search",
    description="Search memories semantically using vector embeddings and compound relevance scoring.",
)
async def search_memories(
    payload: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemorySearchResponse:
    results = await service.search_semantic(
        user_id=current_user.id,
        query=payload.query,
        limit=payload.limit,
        threshold=payload.threshold,
        memory_types=payload.memory_types,
        statuses=payload.statuses,
    )
    response_items = [
        MemorySearchResultItemResponse(
            memory=MemoryResponse.from_model(r),
            score=r.score,
            breakdown=r.breakdown,
        )
        for r in results
    ]
    return MemorySearchResponse(
        query=payload.query,
        results=response_items,
        count=len(response_items),
    )


@router.post(
    "/extract",
    response_model=MemoryExtractResponse,
    summary="Extract candidate memories",
    description="Extract candidate memories from content with privacy filter and deduplication check without persisting.",
)
async def extract_memories(
    payload: MemoryExtractRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryExtractResponse:
    candidates = await service.extract_candidates(
        user_id=current_user.id,
        content=payload.content,
        conversation_id=payload.conversation_id,
    )
    return MemoryExtractResponse(
        candidates=candidates,
        count=len(candidates),
    )


@router.post(
    "/confirm",
    response_model=MemoryActionResponse,
    summary="Confirm candidate memory",
    description="Save or reject an extracted memory candidate.",
)
async def confirm_memory(
    payload: MemoryConfirmRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryActionResponse:
    mem = await service.confirm_candidate(
        user_id=current_user.id,
        candidate=payload.candidate,
        confirm=payload.confirm,
    )
    if mem:
        return MemoryActionResponse(
            status="confirmed",
            message="Memory successfully stored.",
            memory=MemoryResponse.from_model(mem),
        )
    return MemoryActionResponse(
        status="rejected",
        message="Candidate memory was discarded.",
        memory=None,
    )


@router.get(
    "/working",
    response_model=WorkingMemoryResponse,
    summary="Get working memory",
    description="List active short-term working memory items for the user.",
)
async def get_working_memory(
    conversation_id: str | None = Query(default=None, description="Optional conversation scope"),
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> WorkingMemoryResponse:
    items = await service.working_memory.list_items(
        user_id=str(current_user.id),
        conversation_id=conversation_id,
    )
    return WorkingMemoryResponse(items=items)


@router.post(
    "/working",
    response_model=dict[str, Any],
    summary="Set working memory item",
    description="Store an ephemeral item in short-term working memory with TTL.",
)
async def set_working_memory(
    payload: WorkingMemorySetRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, Any]:
    await service.working_memory.set_item(
        user_id=str(current_user.id),
        key=payload.key,
        value=payload.value,
        ttl_seconds=payload.ttl_seconds,
        conversation_id=payload.conversation_id,
    )
    return {"status": "ok", "key": payload.key}


@router.delete(
    "/working",
    response_model=dict[str, Any],
    summary="Clear working memory",
    description="Clear ephemeral short-term working memory for user scope.",
)
async def clear_working_memory(
    conversation_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, Any]:
    await service.working_memory.clear(
        user_id=str(current_user.id),
        conversation_id=conversation_id,
    )
    return {"status": "cleared"}


@router.post(
    "/{memory_id}/archive",
    response_model=MemoryActionResponse,
    summary="Archive a memory",
    description="Transition memory lifecycle state to ARCHIVED.",
)
async def archive_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryActionResponse:
    mem = await service.archive_memory(memory_id=memory_id, user_id=current_user.id)
    return MemoryActionResponse(
        status="archived",
        message="Memory successfully archived.",
        memory=MemoryResponse.from_model(mem),
    )


@router.post(
    "/{memory_id}/restore",
    response_model=MemoryActionResponse,
    summary="Restore an archived or superseded memory",
    description="Transition memory lifecycle state back to ACTIVE.",
)
async def restore_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryActionResponse:
    mem = await service.restore_memory(memory_id=memory_id, user_id=current_user.id)
    return MemoryActionResponse(
        status="restored",
        message="Memory successfully restored to ACTIVE.",
        memory=MemoryResponse.from_model(mem),
    )


@router.post(
    "/{memory_id}/feedback",
    response_model=MemoryActionResponse,
    summary="Submit memory feedback",
    description="Provide feedback (USEFUL, INCORRECT, OUTDATED, FORGET, EDIT) to update memory state.",
)
async def memory_feedback(
    memory_id: uuid.UUID,
    payload: MemoryFeedbackRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryActionResponse:
    mem = await service.apply_feedback(
        memory_id=memory_id,
        user_id=current_user.id,
        feedback_type=payload.feedback_type,
        comment=payload.comment,
        updated_content=payload.updated_content,
    )
    return MemoryActionResponse(
        status="feedback_applied",
        message=f"Feedback '{payload.feedback_type.value}' successfully processed.",
        memory=MemoryResponse.from_model(mem) if mem.status != "DELETED" else None,
    )


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Get a single memory",
    description="Fetch a specific memory item by its UUID ensuring user isolation.",
)
async def get_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    mem = await service.get_memory(memory_id=memory_id, user_id=current_user.id)
    return MemoryResponse.from_model(mem)


@router.patch(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Update a memory",
    description="Update memory content, importance, or metadata.",
)
async def update_memory(
    memory_id: uuid.UUID,
    payload: MemoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    mem = await service.update_memory(
        memory_id=memory_id,
        user_id=current_user.id,
        content=payload.content,
        summary=payload.summary,
        memory_type=payload.memory_type.value if payload.memory_type else None,
        status=payload.status.value if payload.status else None,
        superseded_by_id=payload.superseded_by_id,
        importance=payload.importance,
        confidence=payload.confidence,
        source=payload.source,
        metadata=payload.metadata,
    )
    return MemoryResponse.from_model(mem)


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
    description="Soft-delete a memory record preventing future retrieval.",
)
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> None:
    await service.delete_memory(memory_id=memory_id, user_id=current_user.id)
