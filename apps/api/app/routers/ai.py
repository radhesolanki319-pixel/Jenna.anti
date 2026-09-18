"""Authenticated AI endpoints for completion, streaming, model routing, and usage."""

import json
from typing import Any, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.errors import (
    AIAuthenticationError,
    AIError,
    AIInvalidRequestError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from app.ai.service import AIService, get_ai_service
from app.ai.types import AIModelMetadata, AIRequest, AIResponse
from app.core.database import get_db
from app.models.users import User
from app.repositories.ai_usage_repo import AIUsageRepository
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Core"])


def _map_ai_error(exc: Exception) -> HTTPException:
    """Translate domain AI errors into structured HTTP status codes."""
    if isinstance(exc, AIProviderUnavailableError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "AI_UNAVAILABLE", "message": exc.message, "provider": exc.provider},
        )
    if isinstance(exc, AIAuthenticationError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "AI_AUTH_FAILED", "message": exc.message, "provider": exc.provider},
        )
    if isinstance(exc, AIRateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "AI_RATE_LIMIT", "message": exc.message, "provider": exc.provider},
        )
    if isinstance(exc, AITimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "AI_TIMEOUT", "message": exc.message, "provider": exc.provider},
        )
    if isinstance(exc, AIInvalidRequestError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "AI_INVALID_REQUEST", "message": exc.message, "provider": exc.provider},
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"code": "AI_ERROR", "message": str(exc)},
    )


@router.post(
    "/generate",
    response_model=AIResponse,
    summary="Generate AI completion",
    description="Synchronously executes an AI prompt through the model router with automatic fallback.",
)
async def generate_completion(
    request: AIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> AIResponse:
    try:
        return await ai_service.generate(request=request, user_id=current_user.id, db=db)
    except Exception as exc:
        raise _map_ai_error(exc)


@router.post(
    "/stream",
    summary="Stream AI completion (SSE)",
    description="Streams completion tokens as Server-Sent Events with standard lifecycle events.",
)
async def stream_completion(
    request: AIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> StreamingResponse:
    async def sse_generator() -> AsyncIterator[str]:
        try:
            async for event in ai_service.stream(request=request, user_id=current_user.id, db=db):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            err_event = {
                "type": "stream.error",
                "request_id": request.request_id,
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


@router.get(
    "/models",
    response_model=list[AIModelMetadata],
    summary="List supported AI models",
    description="Returns all registered models, their capabilities, and current provider availability.",
)
async def list_models(
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
) -> list[AIModelMetadata]:
    return ai_service.get_models()


@router.get(
    "/status",
    summary="Get AI routing status",
    description="Returns availability state of providers, configured defaults, and model catalogs.",
)
async def get_ai_status(
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
) -> dict[str, Any]:
    return ai_service.get_status()


@router.get(
    "/usage",
    summary="Get current user's AI token usage",
    description="Aggregated token consumption metrics and recent request log entries.",
)
async def get_ai_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    usage_repo = AIUsageRepository(db)
    summary = await usage_repo.get_summary_for_user(current_user.id)
    recent = await usage_repo.list_recent(user_id=current_user.id, limit=10)
    return {
        "summary": summary,
        "recent_requests": [
            {
                "id": str(r.id),
                "request_id": r.request_id,
                "provider": r.provider,
                "model": r.model,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "created_at": r.created_at.isoformat(),
            }
            for r in recent
        ],
    }
