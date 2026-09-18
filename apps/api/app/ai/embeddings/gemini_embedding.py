"""Google Gemini Embedding Provider implementation."""

import logging
from typing import Any
from app.ai.embeddings.base import BaseEmbeddingProvider, EmbeddingError, EmbeddingProviderUnavailableError
from app.core.config import settings

logger = logging.getLogger("jenna.ai.embeddings.gemini")


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Generates dense vector embeddings using Google Gemini models (e.g. text-embedding-004)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int = 768,
    ) -> None:
        self._api_key = api_key or settings.effective_google_api_key
        self._model = model or settings.embedding_model or "text-embedding-004"
        self._dimensions = dimensions
        self._client: Any = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def get_dimensions(self) -> int:
        return self._dimensions

    def _get_client(self) -> Any:
        if not self._api_key:
            raise EmbeddingProviderUnavailableError(
                "Gemini API key is not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY in environment.",
                provider=self.provider_name,
            )
        if self._client is None:
            try:
                from google.genai import Client
                self._client = Client(api_key=self._api_key)
            except Exception as exc:
                raise EmbeddingError(f"Failed to initialize Gemini client: {exc}", provider=self.provider_name) from exc
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single string."""
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text.", provider=self.provider_name)

        client = self._get_client()
        try:
            response = await client.aio.models.embed_content(
                model=self._model,
                contents=text,
            )
            if hasattr(response, "embeddings") and response.embeddings:
                values = response.embeddings[0].values
                return list(values[:self._dimensions]) if values else []
            elif hasattr(response, "embedding") and response.embedding:
                values = response.embedding.values
                return list(values[:self._dimensions]) if values else []
            else:
                raise EmbeddingError("Unexpected response format from Gemini embeddings API", provider=self.provider_name)
        except EmbeddingError:
            raise
        except Exception as exc:
            logger.error("Gemini embedding request failed: %s", exc)
            raise EmbeddingError(f"Gemini embedding error: {exc}", provider=self.provider_name) from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings."""
        if not texts:
            return []

        client = self._get_client()
        try:
            response = await client.aio.models.embed_content(
                model=self._model,
                contents=texts,
            )
            results: list[list[float]] = []
            if hasattr(response, "embeddings") and response.embeddings:
                for emb in response.embeddings:
                    vals = emb.values if hasattr(emb, "values") else []
                    results.append(list(vals[:self._dimensions]))
                return results
            raise EmbeddingError("Unexpected batch response format from Gemini embeddings API", provider=self.provider_name)
        except EmbeddingError:
            raise
        except Exception as exc:
            logger.error("Gemini batch embedding request failed: %s", exc)
            raise EmbeddingError(f"Gemini batch embedding error: {exc}", provider=self.provider_name) from exc

    async def health_check(self) -> bool:
        """Check if Gemini provider is configured."""
        return bool(self._api_key and self._api_key.strip())
