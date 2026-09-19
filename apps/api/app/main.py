from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.errors import register_exception_handlers
from app.core.logging import logger, setup_logging
from app.core.redis import redis_client
from app.middleware.request_id import RequestIdMiddleware
from app.routers import (
    agents,
    ai,
    android,
    antigravity,
    app_usage,
    approvals,
    audit,
    auth,
    conversations,
    devices,
    health,
    improvement,
    memory,
    notifications,
    production,
    settings as settings_router,
    system,
    tools,
    usage,
    vision,
    voice,
    websocket,
)





@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing startup and shutdown of infrastructure resources."""
    setup_logging()
    logger.info(
        f"Starting {settings.app_name} ({settings.service_name}) v{settings.app_version}",
        extra={
            "environment": settings.app_env,
            "log_level": settings.log_level,
            "version": settings.app_version,
        },
    )

    # Establish Redis connection abstraction
    await redis_client.connect()

    # Auto-initialize database tables for SQLite cloud storage
    if "sqlite" in settings.database_url.lower():
        try:
            import app.models  # noqa: F401
            from app.core.database import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("SQLite database schema initialized successfully.")
        except Exception as e:
            logger.warning(f"Note on SQLite schema init: {e}")

    yield

    # Clean shutdown
    logger.info("Shutting down API services and disconnecting clients...")
    await redis_client.disconnect()
    await engine.dispose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory configuring middleware, exception handlers, and API routers."""
    app = FastAPI(
        title="Jenna AI Platform API",
        description="Production-oriented Backend API for Jenna Personal AI Platform — Phase 2",
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Centralized exception handlers
    register_exception_handlers(app)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and access logging middleware
    app.add_middleware(RequestIdMiddleware)

    # API Version 1 Routers
    app.include_router(agents.router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
    app.include_router(android.router, prefix="/api/v1")
    app.include_router(antigravity.router, prefix="/api/v1")
    app.include_router(app_usage.router, prefix="/api/v1")
    app.include_router(approvals.router, prefix="/api/v1")
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(devices.router, prefix="/api/v1")
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(improvement.router, prefix="/api/v1")
    app.include_router(memory.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(production.router, prefix="/api/v1")

    app.include_router(settings_router.router, prefix="/api/v1")
    app.include_router(system.router, prefix="/api/v1")
    app.include_router(tools.router, prefix="/api/v1")
    app.include_router(usage.router, prefix="/api/v1")
    app.include_router(vision.router, prefix="/api/v1")
    app.include_router(voice.router, prefix="/api/v1")
    app.include_router(websocket.router, prefix="/api/v1")



    @app.get("/health")
    async def root_health():
        return {"status": "ok", "service": "jenna-api", "antigravity": "active", "whatsapp": "active"}

    return app


app = create_app()
