"""Base interface for embedding providers."""

from abc import ABC, abstractmethod


class EmbeddingError(Exception):
    """Base exception for embedding generation failures."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(message)
        self.provider = provider


class EmbeddingProviderUnavailableError(EmbeddingError):
    """Raised when an embedding provider is not configured or unreachable."""
    pass


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding models (Gemini, OpenAI, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the underlying embedding model."""
        raise NotImplementedError

    @abstractmethod
    def get_dimensions(self) -> int:
        """Return vector dimension length."""
        raise NotImplementedError

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for a single text string."""
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of text strings."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Validate whether provider API key is present and service is accessible."""
        raise NotImplementedError
