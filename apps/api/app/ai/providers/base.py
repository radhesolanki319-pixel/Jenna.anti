"""Base contract for AI Providers in Jenna."""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from app.ai.types import AIModelMetadata, AIRequest, AIResponse, AIStreamChunk


class BaseAIProvider(ABC):
    """Abstract provider adapter interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider unique identifier (e.g. 'gemini', 'openai')."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if credentials and configuration allow API calls."""
        pass

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Execute a synchronous text generation call."""
        pass

    @abstractmethod
    def stream(self, request: AIRequest) -> AsyncIterator[AIStreamChunk]:
        """Stream response tokens asynchronously."""
        pass

    @abstractmethod
    def list_models(self) -> list[AIModelMetadata]:
        """Return list of models supported by this provider."""
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> AIModelMetadata | None:
        """Fetch metadata for a specific model ID."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify provider availability and basic connectivity."""
        pass
