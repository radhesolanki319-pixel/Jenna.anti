"""OpenAI AI Provider implementation using the official openai SDK."""

import asyncio
import time
from typing import AsyncIterator

from app.ai.errors import (
    AIAuthenticationError,
    AIInvalidRequestError,
    AIProviderUnavailableError,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from app.ai.providers.base import BaseAIProvider
from app.ai.types import (
    AIModelMetadata,
    AIRequest,
    AIResponse,
    AIStreamChunk,
    AIUsage,
    ModelCapability,
    TaskType,
)
from app.core.config import settings

try:
    from openai import AsyncOpenAI
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


OPENAI_MODELS: list[AIModelMetadata] = [
    AIModelMetadata(
        model_id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        context_window=128000,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.REASONING, TaskType.CODING, TaskType.RESEARCH},
    ),
    AIModelMetadata(
        model_id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        context_window=128000,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.CHAT, TaskType.ANALYSIS, TaskType.TOOL_REQUEST},
    ),
    AIModelMetadata(
        model_id="o3-mini",
        provider="openai",
        display_name="o3 Mini",
        context_window=200000,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION},
        default_for_tasks=set(),
    ),
]


class OpenAIProvider(BaseAIProvider):
    """Adapter for OpenAI models via official openai SDK."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self._client: AsyncOpenAI | None = None
        if self._api_key and HAS_OPENAI:
            self._client = AsyncOpenAI(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key and HAS_OPENAI)

    def _ensure_available(self) -> None:
        if not self.is_available or not self._client:
            raise AIProviderUnavailableError(
                message="OpenAI provider is unavailable. Please configure OPENAI_API_KEY.",
                provider=self.name,
            )

    def _build_messages(self, request: AIRequest) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = []
        if request.system_instruction:
            msgs.append({"role": "system", "content": request.system_instruction})
        for m in request.messages:
            msgs.append({"role": m.role, "content": m.content})
        return msgs

    def _resolve_model(self, model: str | None) -> str:
        if model:
            return model
        return settings.ai_model if settings.ai_model.startswith("gpt") or settings.ai_model.startswith("o") else "gpt-4o-mini"

    async def generate(self, request: AIRequest) -> AIResponse:
        self._ensure_available()
        assert self._client is not None
        model = self._resolve_model(request.model)
        messages = self._build_messages(request)

        start_time = time.monotonic()
        try:
            async with asyncio.timeout(settings.ai_request_timeout_seconds):
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
        except asyncio.TimeoutError as exc:
            raise AITimeoutError(
                message=f"OpenAI request timed out after {settings.ai_request_timeout_seconds}s.",
                provider=self.name,
            ) from exc
        except openai.AuthenticationError as exc:
            raise AIAuthenticationError(message="Invalid OpenAI API Key.", provider=self.name) from exc
        except openai.RateLimitError as exc:
            raise AIRateLimitError(message="OpenAI rate limit or quota exceeded.", provider=self.name) from exc
        except openai.BadRequestError as exc:
            raise AIInvalidRequestError(message=f"OpenAI bad request: {str(exc)}", provider=self.name) from exc
        except openai.OpenAIError as exc:
            raise AIServiceError(message=f"OpenAI service error: {str(exc)}", provider=self.name) from exc
        except Exception as exc:
            raise AIServiceError(message=f"Unexpected OpenAI error: {str(exc)}", provider=self.name) from exc

        latency_ms = (time.monotonic() - start_time) * 1000.0

        choice = response.choices[0]
        text = choice.message.content or ""
        finish_reason = choice.finish_reason or "stop"

        usage = AIUsage()
        if response.usage:
            usage.prompt_tokens = response.usage.prompt_tokens
            usage.completion_tokens = response.usage.completion_tokens
            usage.total_tokens = response.usage.total_tokens

        return AIResponse(
            text=text,
            provider=self.name,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
            request_id=request.request_id,
            latency_ms=round(latency_ms, 2),
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        self._ensure_available()
        assert self._client is not None
        model = self._resolve_model(request.model)
        messages = self._build_messages(request)

        try:
            stream_resp = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
            index = 0
            accumulated_usage = AIUsage()
            async for chunk in stream_resp:
                delta_content = ""
                finish_reason = None
                if chunk.choices and len(chunk.choices) > 0:
                    delta_content = chunk.choices[0].delta.content or ""
                    finish_reason = chunk.choices[0].finish_reason

                if hasattr(chunk, "usage") and chunk.usage:
                    accumulated_usage.prompt_tokens = chunk.usage.prompt_tokens
                    accumulated_usage.completion_tokens = chunk.usage.completion_tokens
                    accumulated_usage.total_tokens = chunk.usage.total_tokens

                yield AIStreamChunk(
                    delta=delta_content,
                    index=index,
                    finish_reason=finish_reason,
                    usage=accumulated_usage if accumulated_usage.total_tokens > 0 else None,
                )
                index += 1

        except openai.AuthenticationError as exc:
            raise AIAuthenticationError(message="Invalid OpenAI API Key.", provider=self.name) from exc
        except openai.RateLimitError as exc:
            raise AIRateLimitError(message="OpenAI rate limit or quota exceeded.", provider=self.name) from exc
        except openai.OpenAIError as exc:
            raise AIServiceError(message=f"OpenAI streaming error: {str(exc)}", provider=self.name) from exc
        except Exception as exc:
            raise AIServiceError(message=f"Unexpected OpenAI streaming error: {str(exc)}", provider=self.name) from exc

    def list_models(self) -> list[AIModelMetadata]:
        is_avail = self.is_available
        return [
            m.model_copy(update={"is_available": is_avail})
            for m in OPENAI_MODELS
        ]

    def get_model_info(self, model_id: str) -> AIModelMetadata | None:
        for m in OPENAI_MODELS:
            if m.model_id == model_id:
                return m.model_copy(update={"is_available": self.is_available})
        return None

    async def health_check(self) -> bool:
        if not self.is_available:
            return False
        try:
            test_req = AIRequest(
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            res = await self.generate(test_req)
            return bool(res.text)
        except Exception:
            return False
