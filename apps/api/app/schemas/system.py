from pydantic import BaseModel, Field


class SystemInfoResponse(BaseModel):
    """System information response for telemetry and diagnostics."""
    service: str = Field(default="jenna-api")
    name: str = Field(default="Jenna Personal AI Platform")
    version: str = Field(default="0.2.0")
    phase: str = Field(default="Phase 2 — Backend Core + Database")
    environment: str
    status: str = Field(default="running")
    timestamp: str
    uptime_seconds: float
    dependencies: dict[str, str] = Field(
        default_factory=dict,
        description="Key infrastructure dependencies and their observed status",
    )
