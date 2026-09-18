"""Normalized error taxonomy for Jenna AI providers."""

from typing import Any


class AIError(Exception):
    """Base exception for all AI provider and model failures."""
    def __init__(self, message: str, provider: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.details = details or {}


class AIProviderUnavailableError(AIError):
    """Raised when a requested provider is not configured or lacks credentials."""
    pass


class AIAuthenticationError(AIError):
    """Raised when provider credentials/API keys are invalid or unauthorized."""
    pass


class AIRateLimitError(AIError):
    """Raised when provider rate limits, concurrency ceilings, or quotas are reached."""
    pass


class AITimeoutError(AIError):
    """Raised when an AI provider call exceeds configured timeout limits."""
    pass


class AIInvalidRequestError(AIError):
    """Raised when a prompt, context length, or parameters violate provider constraints."""
    pass


class AIServiceError(AIError):
    """Raised when an upstream provider encounters an internal 5xx error."""
    pass
