"""Google Gemini AI Provider implementation using the official google-genai SDK."""

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
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError, ServerError
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False


GEMINI_MODELS: list[AIModelMetadata] = [
    AIModelMetadata(
        model_id="gemini-3.5-flash",
        provider="gemini",
        display_name="Gemini 3.5 Flash",
        context_window=1048576,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.CHAT, TaskType.ANALYSIS, TaskType.TOOL_REQUEST},
    ),
    AIModelMetadata(
        model_id="gemini-3.5-flash-lite",
        provider="gemini",
        display_name="Gemini 3.5 Flash-Lite",
        context_window=1048576,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.CHAT},
    ),
    AIModelMetadata(
        model_id="gemini-3.6-flash",
        provider="gemini",
        display_name="Gemini 3.6 Flash",
        context_window=1048576,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.ANALYSIS, TaskType.TOOL_REQUEST},
    ),
    AIModelMetadata(
        model_id="gemini-3.8-flash",
        provider="gemini",
        display_name="Gemini 3.8 Flash",
        context_window=1048576,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.REASONING, TaskType.CODING, TaskType.RESEARCH},
    ),
    AIModelMetadata(
        model_id="gemini-flash-lite-latest",
        provider="gemini",
        display_name="Gemini Flash-Lite Latest",
        context_window=1048576,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION},
        default_for_tasks=set(),
    ),
    AIModelMetadata(
        model_id="gemini-2.5-pro",
        provider="gemini",
        display_name="Gemini 2.5 Pro",
        context_window=2097152,
        capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
        default_for_tasks={TaskType.REASONING, TaskType.CODING, TaskType.RESEARCH},
    ),
]


class GeminiProvider(BaseAIProvider):
    """Adapter for Google Gemini models via google-genai SDK."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.effective_google_api_key
        self._client: genai.Client | None = None
        if self._api_key and HAS_GOOGLE_GENAI:
            self._client = genai.Client(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key and HAS_GOOGLE_GENAI)

    def _ensure_available(self) -> None:
        if not self.is_available or not self._client:
            raise AIProviderUnavailableError(
                message="Google Gemini provider is unavailable. Please configure GOOGLE_API_KEY or GEMINI_API_KEY.",
                provider=self.name,
            )

    def _build_contents_and_config(self, request: AIRequest) -> tuple[list[types.Content], types.GenerateContentConfig]:
        contents: list[types.Content] = []
        for msg in request.messages:
            role = "model" if msg.role.lower() in ("assistant", "model") else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            system_instruction=request.system_instruction if request.system_instruction else None,
        )
        return contents, config

    def _resolve_model(self, model: str | None) -> str:
        if model:
            if model in ("gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"):
                return "gemini-flash-lite-latest"
            if model in ("gemini-2.5-pro", "gemini-1.5-pro"):
                return "gemini-flash-lite-latest"
            return model
        return "gemini-flash-lite-latest"

    async def generate(self, request: AIRequest) -> AIResponse:
        self._ensure_available()
        assert self._client is not None
        initial_model = self._resolve_model(request.model)
        candidates = [initial_model]
        for fallback in ("gemini-flash-lite-latest", "gemini-3.5-flash-lite"):
            if fallback not in candidates:
                candidates.append(fallback)

        contents, config = self._build_contents_and_config(request)
        start_time = time.monotonic()
        response = None
        active_model = initial_model
        last_error: Exception | None = None

        for cand in candidates:
            try:
                active_model = cand
                async with asyncio.timeout(settings.ai_request_timeout_seconds):
                    response = await self._client.aio.models.generate_content(
                        model=cand,
                        contents=contents,
                        config=config,
                    )
                if response:
                    break
            except asyncio.TimeoutError as exc:
                last_error = exc
                break
            except (APIError, ClientError, ServerError) as exc:
                last_error = exc
                # If quota exhausted (429) or model deprecated (404), try next candidate
                status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if status_code in (429, 404, 503):
                    continue
                self._handle_genai_error(exc)
            except Exception as exc:
                last_error = exc
                break

        if not response:
            if isinstance(last_error, (APIError, ClientError, ServerError)):
                self._handle_genai_error(last_error)
            elif isinstance(last_error, asyncio.TimeoutError):
                raise AITimeoutError(
                    message=f"Gemini API request timed out after {settings.ai_request_timeout_seconds}s.",
                    provider=self.name,
                ) from last_error
            raise AIServiceError(message=f"Unexpected Gemini error: {str(last_error)}", provider=self.name) from last_error

        latency_ms = (time.monotonic() - start_time) * 1000.0

        usage = AIUsage()
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage.prompt_tokens = response.usage_metadata.prompt_token_count or 0
            usage.completion_tokens = response.usage_metadata.candidates_token_count or 0
            usage.total_tokens = response.usage_metadata.total_token_count or (usage.prompt_tokens + usage.completion_tokens)

        text = response.text or ""
        finish_reason = "stop"
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason = str(response.candidates[0].finish_reason).lower()

        return AIResponse(
            text=text,
            provider=self.name,
            model=active_model,
            finish_reason=finish_reason,
            usage=usage,
            request_id=request.request_id,
            latency_ms=round(latency_ms, 2),
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        self._ensure_available()
        assert self._client is not None
        initial_model = self._resolve_model(request.model)
        candidates = [initial_model]
        for fallback in ("gemini-flash-lite-latest", "gemini-3.5-flash-lite"):
            if fallback not in candidates:
                candidates.append(fallback)

        contents, config = self._build_contents_and_config(request)
        stream_iter = None
        first_chunk = None
        last_error: Exception | None = None

        for cand in candidates:
            try:
                response_stream = await self._client.aio.models.generate_content_stream(
                    model=cand,
                    contents=contents,
                    config=config,
                )
                it = response_stream.__aiter__()
                first_chunk = await it.__anext__()
                stream_iter = it
                break
            except StopAsyncIteration:
                stream_iter = None
                first_chunk = None
                break
            except (APIError, ClientError, ServerError) as exc:
                last_error = exc
                status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if status_code in (429, 404, 503):
                    continue
                self._handle_genai_error(exc)
            except Exception as exc:
                last_error = exc
                break

        if stream_iter is None and first_chunk is None and last_error:
            if isinstance(last_error, (APIError, ClientError, ServerError)):
                self._handle_genai_error(last_error)
            raise AIServiceError(message=f"Gemini streaming failure: {str(last_error)}", provider=self.name) from last_error

        try:
            index = 0
            accumulated_usage = AIUsage()

            if first_chunk:
                delta_text = first_chunk.text or ""
                if hasattr(first_chunk, "usage_metadata") and first_chunk.usage_metadata:
                    accumulated_usage.prompt_tokens = first_chunk.usage_metadata.prompt_token_count or accumulated_usage.prompt_tokens
                    accumulated_usage.completion_tokens = first_chunk.usage_metadata.candidates_token_count or accumulated_usage.completion_tokens
                    accumulated_usage.total_tokens = first_chunk.usage_metadata.total_token_count or (accumulated_usage.prompt_tokens + accumulated_usage.completion_tokens)

                yield AIStreamChunk(
                    delta=delta_text,
                    index=index,
                    usage=accumulated_usage if accumulated_usage.total_tokens > 0 else None,
                )
                index += 1

            if stream_iter:
                async for chunk in stream_iter:
                    delta_text = chunk.text or ""
                    if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                        accumulated_usage.prompt_tokens = chunk.usage_metadata.prompt_token_count or accumulated_usage.prompt_tokens
                        accumulated_usage.completion_tokens = chunk.usage_metadata.candidates_token_count or accumulated_usage.completion_tokens
                        accumulated_usage.total_tokens = chunk.usage_metadata.total_token_count or (accumulated_usage.prompt_tokens + accumulated_usage.completion_tokens)

                    yield AIStreamChunk(
                        delta=delta_text,
                        index=index,
                        usage=accumulated_usage if accumulated_usage.total_tokens > 0 else None,
                    )
                    index += 1

            yield AIStreamChunk(
                delta="",
                index=index,
                finish_reason="stop",
                usage=accumulated_usage if accumulated_usage.total_tokens > 0 else None,
            )
        except (APIError, ClientError, ServerError) as exc:
            self._handle_genai_error(exc)
        except Exception as exc:
            raise AIServiceError(message=f"Gemini streaming failure: {str(exc)}", provider=self.name) from exc

    def list_models(self) -> list[AIModelMetadata]:
        is_avail = self.is_available
        return [
            m.model_copy(update={"is_available": is_avail})
            for m in GEMINI_MODELS
        ]

    def get_model_info(self, model_id: str) -> AIModelMetadata | None:
        for m in GEMINI_MODELS:
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

    def _handle_genai_error(self, exc: Exception) -> None:
        err_msg = str(exc)
        code = getattr(exc, "code", None)
        if code in (401, 403) or "API_KEY_INVALID" in err_msg or "UNAUTHENTICATED" in err_msg:
            raise AIAuthenticationError(message="Invalid Google Gemini API Key.", provider=self.name) from exc
        if code == 429 or "RESOURCE_EXHAUSTED" in err_msg:
            raise AIRateLimitError(message="Gemini rate limit or quota exceeded.", provider=self.name) from exc
        if code == 400 or "INVALID_ARGUMENT" in err_msg:
            raise AIInvalidRequestError(message=f"Invalid request parameters: {err_msg}", provider=self.name) from exc
        raise AIServiceError(message=f"Gemini upstream service error: {err_msg}", provider=self.name) from exc
