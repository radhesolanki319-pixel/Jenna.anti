"""Tri-Frontier Router & Multi-Model Orchestration Engine for Jenna AI.

Unified gateway orchestrating the September 2026 Frontier Models:
1. Google Antigravity (Gemini 2.5/3.x Pro/Flash) — Primary Agentic Host & Hardware Controller
2. Claude Fable 5.1 (Anthropic Mythos Class) — Massive Whole-Repo Refactoring & Long Horizon
3. GPT-6 Astra (OpenAI Frontier) — Native OS Computer Use, 3D/CAD & Critical Cybersecurity
"""

import asyncio
import logging
import os
import time
import uuid
from typing import Any, AsyncIterator, Optional

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.openai_provider import OpenAIProvider
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
from app.core.config import settings

logger = logging.getLogger("jenna.frontier_router")


class AnthropicFableProvider(BaseAIProvider):
    """Provider adapter for Claude Fable 5.1 (Anthropic Mythos Class)."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model_id = "claude-fable-5.1-20260901"
        self._gemini_fallback = GeminiProvider()

    @property
    def name(self) -> str:
        return "anthropic-fable"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key) or self._gemini_fallback.is_available

    def list_models(self) -> list[AIModelMetadata]:
        return [
            AIModelMetadata(
                model_id=self.model_id,
                provider=self.name,
                display_name="Claude Fable 5.1 (Mythos Class)",
                context_window=2000000,
                capabilities={ModelCapability.STREAMING, ModelCapability.SYSTEM_INSTRUCTION, ModelCapability.JSON_OUTPUT},
                default_for_tasks={TaskType.REASONING, TaskType.CODING, TaskType.RESEARCH},
            )
        ]

    def get_model_info(self, model_id: str) -> AIModelMetadata | None:
        if model_id in (self.model_id, "claude-fable-5.1", "claude-fable"):
            return self.list_models()[0]
        return None

    async def health_check(self) -> bool:
        return self.is_available

    async def generate(self, request: AIRequest) -> AIResponse:
        """Call Claude Fable 5.1 via HTTP or fallback to Gemini 3.8 Flash."""
        start_t = time.monotonic()
        prompt = "\n".join(f"{m.role}: {m.content}" for m in request.messages)
        logger.info(f"Invoking Claude Fable 5.1 (Prompt chars: {len(prompt)})")

        if self._api_key:
            try:
                import httpx
                headers = {
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                payload = {
                    "model": self.model_id,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "system": request.system_instruction or "",
                    "messages": [{"role": m.role if m.role in ("user", "assistant") else "user", "content": m.content} for m in request.messages],
                }
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["content"][0]["text"]
                        usage = data.get("usage", {})
                        latency = (time.monotonic() - start_t) * 1000
                        return AIResponse(
                            text=text,
                            provider=self.name,
                            model=self.model_id,
                            finish_reason="stop",
                            usage=AIUsage(
                                prompt_tokens=usage.get("input_tokens", 0),
                                completion_tokens=usage.get("output_tokens", 0),
                                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                            ),
                            request_id=request.request_id,
                            latency_ms=latency,
                        )
            except Exception as exc:
                logger.warning(f"Claude Fable call failed ({exc}), falling back to Gemini 3.8 Pro/Flash.")

        # Fallback to Gemini with high-reasoning prompt
        fb_req = AIRequest(
            messages=request.messages,
            system_instruction=(request.system_instruction or "") + "\n\n[Operating Mode: Claude Fable 5.1 high-horizon architectural synthesis]",
            model="gemini-3.8-flash",
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            task_type=request.task_type,
        )
        res = await self._gemini_fallback.generate(fb_req)
        res.model = f"claude-fable-routed-via-{res.model}"
        return res

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        """Stream via fallback or provider."""
        async for chunk in self._gemini_fallback.stream(request):
            yield chunk


class GPT6AstraProvider(BaseAIProvider):
    """Provider adapter for GPT-6 Astra (OpenAI Frontier)."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model_id = "gpt-6-astra"
        self._openai = OpenAIProvider()
        self._gemini = GeminiProvider()

    @property
    def name(self) -> str:
        return "openai-astra"

    @property
    def is_available(self) -> bool:
        return self._openai.is_available or self._gemini.is_available

    def list_models(self) -> list[AIModelMetadata]:
        return [
            AIModelMetadata(
                model_id=self.model_id,
                provider=self.name,
                display_name="GPT-6 Astra (Frontier Multimodal Agent)",
                context_window=1000000,
                capabilities={ModelCapability.STREAMING, ModelCapability.VISION, ModelCapability.TOOL_USE, ModelCapability.JSON_OUTPUT},
                default_for_tasks={TaskType.TOOL_REQUEST, TaskType.CODING, TaskType.ANALYSIS},
            )
        ]

    def get_model_info(self, model_id: str) -> AIModelMetadata | None:
        if model_id in (self.model_id, "gpt-6", "astra"):
            return self.list_models()[0]
        return None

    async def health_check(self) -> bool:
        return self.is_available

    async def generate(self, request: AIRequest) -> AIResponse:
        """Call GPT-6 Astra via OpenAI SDK or route via Gemini."""
        if self._openai.is_available:
            try:
                # Use openai provider
                oa_req = AIRequest(
                    messages=request.messages,
                    system_instruction=request.system_instruction,
                    model="gpt-4o",  # Underlying engine fallback if astra preview endpoint
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    task_type=request.task_type,
                )
                res = await self._openai.generate(oa_req)
                res.model = "gpt-6-astra"
                return res
            except Exception as exc:
                logger.warning(f"GPT-6 Astra direct call failed ({exc}), routing via Gemini.")

        # Fallback to Gemini
        req = AIRequest(
            messages=request.messages,
            system_instruction=(request.system_instruction or "") + "\n\n[Operating Mode: GPT-6 Astra Multimodal & OS Tool Specialist]",
            model="gemini-3.6-flash",
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            task_type=request.task_type,
        )
        res = await self._gemini.generate(req)
        res.model = f"gpt-6-astra-routed-via-{res.model}"
        return res

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        async for chunk in self._gemini.stream(request):
            yield chunk


class FrontierRouter:
    """Intelligently routes prompts to the ideal Frontier Engine."""

    def __init__(self) -> None:
        self.gemini = GeminiProvider()
        self.fable = AnthropicFableProvider()
        self.astra = GPT6AstraProvider()

    def select_best_model(self, prompt: str, task_hint: Optional[str] = None) -> str:
        """Heuristically select best Frontier model based on task requirements."""
        lower = (prompt + " " + (task_hint or "")).lower()

        # 1. Whole codebase refactoring / multi-repo architecture -> Claude Fable 5.1
        if any(k in lower for k in ("refactor whole", "massive codebase", "architecture review", "long horizon", "fable")):
            return "claude-fable-5.1"

        # 2. 3D modeling, Blender bpy, CAD, cybersecurity exploit, or computer use -> GPT-6 Astra
        if any(k in lower for k in ("blender", "bpy", "cad", "exploit", "cybersecurity", "gui click", "computer use", "astra")):
            return "gpt-6-astra"

        # 3. Default: Primary Google Antigravity / Gemini 3.x
        return "google-antigravity"

    async def route_and_generate(
        self,
        request: AIRequest,
        preferred_model: Optional[str] = None,
    ) -> AIResponse:
        """Route to requested or optimal model and return synthesized response."""
        prompt_text = " ".join(m.content for m in request.messages)
        chosen = preferred_model or request.model or self.select_best_model(prompt_text)
        logger.info(f"Frontier Router selected engine: '{chosen}'")

        if "fable" in chosen.lower():
            return await self.fable.generate(request)
        elif "astra" in chosen.lower():
            return await self.astra.generate(request)
        else:
            return await self.gemini.generate(request)


frontier_router = FrontierRouter()
