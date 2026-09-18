"""ModelRouter for intelligent provider and model selection based on task, capability, and availability."""

from typing import Any
from app.ai.errors import AIInvalidRequestError, AIProviderUnavailableError
from app.ai.providers.base import BaseAIProvider
from app.ai.types import AIModelMetadata, ModelCapability, TaskType
from app.core.config import settings


class ModelRouter:
    """Routes AI completion requests to optimal providers and models."""

    def __init__(self, providers: list[BaseAIProvider] | None = None) -> None:
        self._providers: dict[str, BaseAIProvider] = {}
        if providers:
            for p in providers:
                self.register_provider(p)

    def register_provider(self, provider: BaseAIProvider) -> None:
        """Register a provider adapter."""
        self._providers[provider.name.lower()] = provider

    def get_provider(self, name: str | None = None) -> BaseAIProvider:
        """Fetch requested provider or select primary/fallback configured provider."""
        # 1. If explicit provider requested
        if name:
            p_name = name.lower()
            if p_name not in self._providers:
                raise AIProviderUnavailableError(
                    message=f"AI Provider '{name}' is not registered.",
                    provider=name,
                )
            prov = self._providers[p_name]
            if not prov.is_available:
                raise AIProviderUnavailableError(
                    message=f"Requested AI Provider '{name}' is unconfigured (missing API credentials).",
                    provider=name,
                )
            return prov

        # 2. Try default configured provider
        default_name = settings.ai_provider.lower()
        if default_name in self._providers and self._providers[default_name].is_available:
            return self._providers[default_name]

        # 3. Fallback to any registered and available provider
        for prov in self._providers.values():
            if prov.is_available:
                return prov

        # 4. No provider is available
        available_list = [p.name for p in self._providers.values() if p.is_available]
        registered_list = list(self._providers.keys())
        raise AIProviderUnavailableError(
            message=(
                f"No AI Providers are configured with valid credentials. "
                f"Configured default is '{settings.ai_provider}'. "
                f"Registered providers: {registered_list}. "
                f"Available: {available_list}. Please set GOOGLE_API_KEY or OPENAI_API_KEY."
            ),
            provider=settings.ai_provider,
        )

    def route(
        self,
        task_type: TaskType = TaskType.CHAT,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
    ) -> tuple[BaseAIProvider, str]:
        """Select optimal provider and model based on task, preference, and availability."""
        # Validate task capabilities
        if task_type == TaskType.VISION:
            raise AIInvalidRequestError(
                message="Task 'VISION' is not supported in Part 2 Phase 1 foundation.",
            )
        if task_type == TaskType.TOOL_USE:
            raise AIInvalidRequestError(
                message="Task 'TOOL_USE' is not supported in Part 2 Phase 1 foundation.",
            )

        # 1. If model is explicitly specified, determine which provider owns it if provider is omitted
        if preferred_model and not preferred_provider:
            for p in self._providers.values():
                if p.get_model_info(preferred_model):
                    preferred_provider = p.name
                    break

        provider = self.get_provider(preferred_provider)

        # 2. If explicit model requested and belongs to provider, verify availability
        if preferred_model:
            model_info = provider.get_model_info(preferred_model)
            if model_info:
                return provider, model_info.model_id
            # If model name not in static catalog, pass through to provider directly
            return provider, preferred_model

        # 3. Task-based model selection
        models = provider.list_models()
        for m in models:
            if task_type in m.default_for_tasks:
                return provider, m.model_id

        # 4. Fallback to provider's first available model or default
        if models:
            return provider, models[0].model_id

        return provider, settings.ai_model

    def list_all_models(self) -> list[AIModelMetadata]:
        """Aggregate models across all registered providers."""
        all_models: list[AIModelMetadata] = []
        for p in self._providers.values():
            all_models.extend(p.list_models())
        return all_models

    def get_status(self) -> dict[str, Any]:
        """Telemetry status of all registered providers and models."""
        providers_status = {}
        for name, p in self._providers.items():
            providers_status[name] = {
                "available": p.is_available,
                "models": [m.model_id for m in p.list_models()],
            }
        return {
            "default_provider": settings.ai_provider,
            "default_model": settings.ai_model,
            "providers": providers_status,
        }
