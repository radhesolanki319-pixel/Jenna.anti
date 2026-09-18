"""Registry and factory for embedding providers."""

from app.ai.embeddings.base import BaseEmbeddingProvider, EmbeddingError
from app.ai.embeddings.gemini_embedding import GeminiEmbeddingProvider
from app.ai.embeddings.openai_embedding import OpenAIEmbeddingProvider
from app.core.config import settings

_PROVIDERS: dict[str, type[BaseEmbeddingProvider]] = {
    "gemini": GeminiEmbeddingProvider,
    "google": GeminiEmbeddingProvider,
    "openai": OpenAIEmbeddingProvider,
}


def get_embedding_provider(provider_name: str | None = None) -> BaseEmbeddingProvider:
    """Retrieve embedding provider based on configuration or explicit parameter."""
    name = (provider_name or settings.embedding_provider or "gemini").lower()
    provider_cls = _PROVIDERS.get(name)
    if not provider_cls:
        raise EmbeddingError(f"Unsupported embedding provider: '{name}'. Supported: {list(_PROVIDERS.keys())}")
    return provider_cls(dimensions=settings.embedding_dimensions)
