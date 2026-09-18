from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Status of an individual dependent service."""
    name: str
    status: str  # healthy | unhealthy
    detail: str | None = None


class HealthResponse(BaseModel):
    """Overall structured health check response."""
    status: str = Field(description="ok | degraded | unhealthy")
    service: str = Field(default="jenna-api", description="Service identifier")
    version: str
    phase: str
    timestamp: str
    services: list[ServiceStatus]


class LivenessResponse(BaseModel):
    """Simple liveness probe response."""
    status: str = Field(default="ok")
    service: str = Field(default="jenna-api")
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe response verifying critical dependencies."""
    status: str = Field(description="ok | not_ready")
    service: str = Field(default="jenna-api")
    ready: bool
    timestamp: str
    dependencies: list[ServiceStatus]
