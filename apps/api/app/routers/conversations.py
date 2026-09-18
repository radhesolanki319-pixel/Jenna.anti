"""Conversation API Router: Thread management, multi-turn reasoning, and SSE streaming."""

import json
import logging
from typing import AsyncIterator, Sequence
import uuid
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import AppException
from app.models.users import User
from app.routers.ai import _map_ai_error
from app.services.auth_service import get_current_user
from app.schemas.conversations import (
    ConversationCreate,
    ConversationDetailRead,
    ConversationRead,
    ConversationUpdate,
    MessageRead,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.conversation_service import ConversationService

logger = logging.getLogger("jenna.conversations_router")

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Dependency injector for ConversationService."""
    return ConversationService(session=db)


@router.get(
    "",
    response_model=list[ConversationRead],
    summary="List user conversations",
    description="Returns a paginated list of conversations belonging to the authenticated user.",
)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> Sequence[ConversationRead]:
    return await service.list_conversations(user_id=current_user.id, limit=limit, offset=offset)


@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Initializes a new conversation thread for the authenticated user.",
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationRead:
    return await service.create_conversation(user_id=current_user.id, title=payload.title)


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailRead,
    summary="Get conversation details and messages",
    description="Fetches a conversation and its messages with strict user ownership validation.",
)
async def get_conversation_detail(
    conversation_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationDetailRead:
    conv = await service.get_conversation(conversation_id=conversation_id, user_id=current_user.id)
    messages = await service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return ConversationDetailRead(
        conversation=ConversationRead.model_validate(conv),
        messages=[MessageRead.model_validate(m) for m in messages],
        total_messages=len(messages),
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationRead,
    summary="Update conversation title",
    description="Updates the title of an existing conversation owned by the authenticated user.",
)
async def update_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationRead:
    return await service.update_title(
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=payload.title,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation",
    description="Deletes a conversation and cascades message deletion.",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    await service.delete_conversation(conversation_id=conversation_id, user_id=current_user.id)
    return {"status": "ok", "message": f"Conversation '{conversation_id}' deleted."}


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageRead],
    summary="List conversation messages",
    description="Returns messages from a specific conversation in chronological order.",
)
async def list_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> list[MessageRead]:
    messages = await service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return [MessageRead.model_validate(m) for m in messages]


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    summary="Send message (synchronous reasoning)",
    description="Executes the full reasoning pipeline and returns the complete assistant response.",
)
async def send_message(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> SendMessageResponse:
    try:
        user_msg, assistant_msg, task_type, provider, model, latency_ms = await service.send_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=payload.content,
            model_override=payload.model,
            provider_override=payload.provider,
            web_search=payload.web_search,
            deep_research=payload.deep_research,
            attachments=payload.attachments,
            personal_intelligence=payload.personal_intelligence,
            persona=payload.persona,
        )
        return SendMessageResponse(
            user_message=MessageRead.model_validate(user_msg),
            assistant_message=MessageRead.model_validate(assistant_msg),
            task_type=task_type,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
        )
    except AppException:
        raise
    except Exception as exc:
        raise _map_ai_error(exc)


@router.post(
    "/{conversation_id}/stream",
    summary="Send message and stream assistant response (SSE)",
    description="Executes the reasoning pipeline, streaming tokens as SSE deltas and saving the response upon completion.",
)
async def stream_message(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> StreamingResponse:
    # Ensure user owns conversation before opening stream
    await service.get_conversation(conversation_id=conversation_id, user_id=current_user.id)

    async def sse_generator() -> AsyncIterator[str]:
        try:
            async for event in service.stream_message(
                conversation_id=conversation_id,
                user_id=current_user.id,
                content=payload.content,
                model_override=payload.model,
                provider_override=payload.provider,
                web_search=payload.web_search,
                deep_research=payload.deep_research,
                attachments=payload.attachments,
                personal_intelligence=payload.personal_intelligence,
                persona=payload.persona,
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as exc:
            err_event = {
                "type": "stream.error",
                "conversation_id": str(conversation_id),
                "error_code": type(exc).__name__,
                "message": str(exc),
            }
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
