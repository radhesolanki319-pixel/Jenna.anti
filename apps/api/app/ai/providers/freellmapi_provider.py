"""FreeLLMAPI Multi-AI Fusion Provider for Jenna.

Integrates FreeLLMAPI (242+ models including Claude, Gemini, GPT, DeepSeek, GLM, Kimi)
via local OpenAI-compatible endpoint at http://localhost:3001/v1.
"""

import json
import logging
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import aiohttp

from app.ai.providers.base import BaseAIProvider
from app.ai.types import (
    AIModelMetadata,
    AIRequest,
    AIResponse,
    AIStreamChunk,
    AIUsage,
    ChatMessage,
    ModelCapability,
    TaskType,
)

logger = logging.getLogger("jenna.freellmapi_provider")

DEFAULT_BASE_URL = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")
DEFAULT_API_KEY = os.getenv("FREELLMAPI_API_KEY", "freellmapi-c7bf396fcf0351dbba9546933a8881054c627e6f78875206")
DEFAULT_MODEL = os.getenv("FREELLMAPI_MODEL", "auto")


class FreeLLMAPIFusionProvider(BaseAIProvider):
    """Provider adapter for FreeLLMAPI 242+ Model Multi-AI Fusion Engine."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key or DEFAULT_API_KEY
        self.default_model = default_model or DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "freellmapi-fusion"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.base_url)

    def list_models(self) -> List[AIModelMetadata]:
        return [
            AIModelMetadata(
                model_id="auto",
                provider=self.name,
                display_name="FreeLLMAPI Auto-Router (Best Available of 242 Models)",
                context_window=128000,
                capabilities={ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.STREAMING, ModelCapability.TOOL_USE},
                default_for_tasks={TaskType.CODING, TaskType.REASONING, TaskType.RESEARCH},
            ),
            AIModelMetadata(
                model_id="fusion",
                provider=self.name,
                display_name="FreeLLMAPI Multi-AI Fusion (Parallel Panel + Judge)",
                context_window=128000,
                capabilities={ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.STREAMING},
                default_for_tasks={TaskType.ANALYSIS, TaskType.REASONING},
            ),
        ]

    def get_model_info(self, model_id: str) -> Optional[AIModelMetadata]:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        return self.list_models()[0]

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=4.0),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def generate(self, request: AIRequest) -> AIResponse:
        """Call FreeLLMAPI completions endpoint with auto failover."""
        start_t = time.monotonic()
        target_model = request.model if request.model in ("auto", "fusion") else self.default_model

        messages_payload: List[Dict[str, str]] = []
        if request.system_instruction:
            messages_payload.append({"role": "system", "content": request.system_instruction})

        for m in request.messages:
            role = m.role if m.role in ("user", "assistant", "system") else "user"
            messages_payload.append({"role": role, "content": m.content})

        payload = {
            "model": target_model,
            "messages": messages_payload,
            "max_tokens": request.max_tokens or 2000,
            "temperature": request.temperature or 0.3,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=35.0),
            ) as resp:
                if resp.status != 200:
                    err_body = await resp.text()
                    raise RuntimeError(f"FreeLLMAPI HTTP {resp.status}: {err_body}")

                data = await resp.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content") or ""

                routed_via = data.get("_routed_via") or data.get("model") or target_model
                usage_dict = data.get("usage", {})
                latency = (time.monotonic() - start_t) * 1000

                return AIResponse(
                    text=content,
                    provider=self.name,
                    model=f"freellmapi-fused[{routed_via}]",
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage=AIUsage(
                        prompt_tokens=usage_dict.get("prompt_tokens", 0),
                        completion_tokens=usage_dict.get("completion_tokens", 0),
                        total_tokens=usage_dict.get("total_tokens", 0),
                    ),
                    request_id=request.request_id,
                    latency_ms=latency,
                )

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        """Simple non-streaming yield for robustness."""
        res = await self.generate(request)
        yield AIStreamChunk(delta=res.text, finish_reason=res.finish_reason)
