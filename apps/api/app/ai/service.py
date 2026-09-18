"""AI Service: Orchestrates ModelRouter, provider calls, retries, fallbacks, and usage tracking."""

import asyncio
import logging
import time
import uuid
from typing import Any, AsyncIterator
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
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.router import ModelRouter
from app.ai.types import (
    AIModelMetadata,
    AIRequest,
    AIResponse,
    AIStreamChunk,
    AIUsage,
    TaskType,
)
from app.core.config import settings
from app.repositories.ai_usage_repo import AIUsageRepository
from app.repositories.audit_repo import AuditEventRepository

logger = logging.getLogger("jenna.ai")


class AIService:
    """Core AI brain service for Jenna."""

    def __init__(self, router: ModelRouter | None = None) -> None:
        if router is None:
            gemini = GeminiProvider()
            openai = OpenAIProvider()
            self.router = ModelRouter(providers=[gemini, openai])
        else:
            self.router = router

    def get_models(self) -> list[AIModelMetadata]:
        """List all supported models across providers."""
        return self.router.list_all_models()

    def get_status(self) -> dict[str, Any]:
        """Status and availability of AI routing subsystem."""
        return self.router.get_status()

    async def _execute_with_retry(
        self,
        provider: BaseAIProvider,
        request: AIRequest,
    ) -> AIResponse:
        """Execute non-streaming generation with exponential backoff retries and timeout."""
        max_retries = settings.ai_max_retries
        last_exc: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                async with asyncio.timeout(settings.ai_request_timeout_seconds):
                    return await provider.generate(request)
            except asyncio.TimeoutError:
                last_exc = AITimeoutError(
                    message=f"Request to provider '{provider.name}' timed out after {settings.ai_request_timeout_seconds}s.",
                    provider=provider.name,
                )
                if attempt < max_retries:
                    backoff = 0.5 * (2 ** attempt)
                    await asyncio.sleep(backoff)
                else:
                    break
            except (AIAuthenticationError, AIInvalidRequestError):
                # Never retry client / auth errors
                raise
            except (AIRateLimitError, AITimeoutError, AIServiceError) as exc:
                last_exc = exc
                if attempt < max_retries:
                    backoff = 0.5 * (2 ** attempt)
                    logger.warning(
                        "AI generation failed on %s (attempt %d/%d). Retrying in %.2fs. Error: %s",
                        provider.name,
                        attempt + 1,
                        max_retries,
                        backoff,
                        str(exc),
                    )
                    await asyncio.sleep(backoff)
                else:
                    break

        if last_exc:
            raise last_exc
        raise AIServiceError("Execution failed without explicit error.", provider=provider.name)

    async def generate(
        self,
        request: AIRequest,
        user_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> AIResponse:
        """Route and execute a non-streaming AI completion request."""
        # 1. Resolve optimal provider & model
        provider, model = self.router.route(
            task_type=request.task_type,
            preferred_provider=request.provider,
            preferred_model=request.model,
        )
        resolved_req = request.model_copy(update={"model": model, "provider": provider.name})

        start_time = time.monotonic()
        try:
            response = await self._execute_with_retry(provider, resolved_req)
            success = True
            error_msg = None
        except Exception as exc:
            success = False
            error_msg = str(exc)
            latency_ms = (time.monotonic() - start_time) * 1000.0

            # Log failed usage
            if db is not None:
                try:
                    usage_repo = AIUsageRepository(db)
                    await usage_repo.log_usage(
                        provider=provider.name,
                        model=model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0,
                        latency_ms=round(latency_ms, 2),
                        user_id=user_id,
                        request_id=request.request_id,
                        success=False,
                        error_message=error_msg,
                    )
                    await db.commit()
                except Exception as log_err:
                    logger.error("Failed to record failed AI usage: %s", log_err)
            raise

        # 2. Record usage metrics
        if db is not None:
            try:
                usage_repo = AIUsageRepository(db)
                await usage_repo.log_usage(
                    provider=response.provider,
                    model=response.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    latency_ms=response.latency_ms,
                    user_id=user_id,
                    request_id=response.request_id,
                    success=True,
                )
                audit_repo = AuditEventRepository(db)
                await audit_repo.log_event(
                    event_type="ai",
                    action="generate",
                    success=True,
                    user_id=user_id,
                    request_id=response.request_id,
                    metadata={
                        "provider": response.provider,
                        "model": response.model,
                        "total_tokens": response.usage.total_tokens,
                        "latency_ms": response.latency_ms,
                    },
                )
                await db.commit()
            except Exception as log_err:
                logger.error("Failed to record AI usage log: %s", log_err)

        return response

    async def stream(
        self,
        request: AIRequest,
        user_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream response tokens emitting standard streaming lifecycle events."""
        req_id = request.request_id or str(uuid.uuid4())
        start_time = time.monotonic()

        # 1. Route provider and model
        try:
            provider, model = self.router.route(
                task_type=request.task_type,
                preferred_provider=request.provider,
                preferred_model=request.model,
            )
            resolved_req = request.model_copy(update={"model": model, "provider": provider.name, "request_id": req_id})
        except Exception as exc:
            yield {
                "type": "stream.error",
                "request_id": req_id,
                "error_code": "ROUTING_ERROR",
                "message": str(exc),
            }
            return

        # 2. Emit stream.started
        yield {
            "type": "stream.started",
            "request_id": req_id,
            "provider": provider.name,
            "model": model,
        }

        full_text_accum = []
        finish_reason = "stop"
        final_usage = AIUsage()
        success = True
        error_msg = None

        try:
            async for chunk in provider.stream(resolved_req):
                if chunk.delta:
                    full_text_accum.append(chunk.delta)
                    yield {
                        "type": "stream.delta",
                        "request_id": req_id,
                        "delta": chunk.delta,
                        "index": chunk.index,
                    }
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                if chunk.usage:
                    final_usage = chunk.usage

        except Exception as exc:
            success = False
            error_msg = str(exc)
            yield {
                "type": "stream.error",
                "request_id": req_id,
                "error_code": type(exc).__name__,
                "message": str(exc),
            }

        latency_ms = (time.monotonic() - start_time) * 1000.0
        full_text = "".join(full_text_accum)

        # Approximate completion tokens if not returned by stream
        if final_usage.total_tokens == 0:
            final_usage.completion_tokens = max(1, len(full_text) // 4)
            final_usage.total_tokens = final_usage.prompt_tokens + final_usage.completion_tokens

        if success:
            yield {
                "type": "stream.completed",
                "request_id": req_id,
                "finish_reason": finish_reason,
                "usage": final_usage.model_dump(),
                "latency_ms": round(latency_ms, 2),
                "full_text": full_text,
            }

        # 3. Log usage
        if db is not None:
            try:
                usage_repo = AIUsageRepository(db)
                await usage_repo.log_usage(
                    provider=provider.name,
                    model=model,
                    prompt_tokens=final_usage.prompt_tokens,
                    completion_tokens=final_usage.completion_tokens,
                    total_tokens=final_usage.total_tokens,
                    latency_ms=round(latency_ms, 2),
                    user_id=user_id,
                    request_id=req_id,
                    success=success,
                    error_message=error_msg,
                )
                await db.commit()
            except Exception as log_err:
                logger.error("Failed to record streaming AI usage: %s", log_err)


_global_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    """Singleton getter for the platform AI service."""
    global _global_ai_service
    if _global_ai_service is None:
        _global_ai_service = AIService()
    return _global_ai_service
