"""OpenAI Embedding Provider implementation."""

import logging
from typing import Any
from app.ai.embeddings.base import BaseEmbeddingProvider, EmbeddingError, EmbeddingProviderUnavailableError
from app.core.config import settings

logger = logging.getLogger("jenna.ai.embeddings.openai")


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Generates dense vector embeddings using OpenAI models (e.g. text-embedding-3-small)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int = 768,
    ) -> None:
        self._api_key = api_key or settings.openai_api_key
        self._model = model or "text-embedding-3-small"
        self._dimensions = dimensions
        self._client: Any = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def get_dimensions(self) -> int:
        return self._dimensions

    def _get_client(self) -> Any:
        if not self._api_key:
            raise EmbeddingProviderUnavailableError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in environment.",
                provider=self.provider_name,
            )
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except Exception as exc:
                raise EmbeddingError(f"Failed to initialize OpenAI client: {exc}", provider=self.provider_name) from exc
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single string."""
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text.", provider=self.provider_name)

        client = self._get_client()
        try:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "input": text,
            }
            # text-embedding-3 models support dimension truncation
            if "3-" in self._model:
                kwargs["dimensions"] = self._dimensions

            response = await client.embeddings.create(**kwargs)
            if response.data and len(response.data) > 0:
                return response.data[0].embedding
            raise EmbeddingError("No embeddings returned from OpenAI", provider=self.provider_name)
        except EmbeddingError:
            raise
        except Exception as exc:
            logger.error("OpenAI embedding request failed: %s", exc)
            raise EmbeddingError(f"OpenAI embedding error: {exc}", provider=self.provider_name) from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings."""
        if not texts:
            return []

        client = self._get_client()
        try:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "input": texts,
            }
            if "3-" in self._model:
                kwargs["dimensions"] = self._dimensions

            response = await client.embeddings.create(**kwargs)
            if response.data:
                # Sort by index to ensure order matches input
                sorted_data = sorted(response.data, key=lambda d: d.index)
                return [d.embedding for d in sorted_data]
            raise EmbeddingError("No embeddings returned from OpenAI batch", provider=self.provider_name)
        except EmbeddingError:
            raise
        except Exception as exc:
            logger.error("OpenAI batch embedding request failed: %s", exc)
            raise EmbeddingError(f"OpenAI batch embedding error: {exc}", provider=self.provider_name) from exc

    async def health_check(self) -> bool:
        """Check if OpenAI provider is configured."""
        return bool(self._api_key and self._api_key.strip())
