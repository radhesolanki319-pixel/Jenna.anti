"""Embeddings package for semantic search and memory representation."""

from app.ai.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingError,
    EmbeddingProviderUnavailableError,
)
from app.ai.embeddings.gemini_embedding import GeminiEmbeddingProvider
from app.ai.embeddings.openai_embedding import OpenAIEmbeddingProvider
from app.ai.embeddings.registry import get_embedding_provider

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingError",
    "EmbeddingProviderUnavailableError",
    "GeminiEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "get_embedding_provider",
]
