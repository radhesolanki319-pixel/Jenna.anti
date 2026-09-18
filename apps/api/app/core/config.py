from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Jenna AI"
    service_name: str = "jenna-api"
    app_version: str = "0.2.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_secret: str = Field(default="change-me-in-production", alias="APP_SECRET")
    session_secret: str = Field(default="change-me-in-production", alias="SESSION_SECRET")
    debug: bool = True
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://jenna:jenna_secret@localhost:5432/jenna_db",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="CORS_ORIGINS",
    )

    # AI Providers & Model Routing
    ai_provider: str = Field(default="gemini", alias="AI_PROVIDER")
    ai_model: str = Field(default="gemini-3.6-flash", alias="AI_MODEL")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    ai_request_timeout_seconds: float = Field(default=30.0, alias="AI_REQUEST_TIMEOUT_SECONDS")
    ai_max_retries: int = Field(default=2, alias="AI_MAX_RETRIES")

    # Embeddings & Vector Memory
    embedding_provider: str = Field(default="gemini", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="gemini-embedding-001", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")

    @property
    def effective_google_api_key(self) -> str | None:
        """Return GOOGLE_API_KEY or fallback to GEMINI_API_KEY if present."""
        import os
        return self.google_api_key or os.environ.get("GEMINI_API_KEY")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.is_production:
            if self.app_secret in ("change-me-in-production", "change-me-to-a-random-secret") or len(self.app_secret) < 16:
                raise ValueError("In production mode, APP_SECRET must be set to a secure string with at least 16 characters.")
            if self.session_secret in ("change-me-in-production", "change-me-to-a-random-secret") or len(self.session_secret) < 16:
                raise ValueError("In production mode, SESSION_SECRET must be set to a secure string with at least 16 characters.")
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
