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

    # Keep-alive loop to prevent Render Free spin-down
    async def keep_alive_loop():
        import os
        import httpx
        public_url = os.environ.get("RENDER_EXTERNAL_URL", "https://jenna-anti.onrender.com")
        while True:
            try:
                await asyncio.sleep(480)  # 8 minutes
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(f"{public_url}/health")
                    logger.info(f"Keep-alive ping to {public_url}: {r.status_code}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Keep-alive ping: {e}")

    keep_alive_task = asyncio.create_task(keep_alive_loop())
    yield

    # Clean shutdown
    keep_alive_task.cancel()
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



    @app.get("/")
    @app.head("/")
    async def root():
        return {
            "message": "Jenna AI Cloud is Live 24/7!",
            "status": "online",
            "service": "jenna-api",
            "whatsapp": "connected",
            "docs": "/api/docs",
            "health": "/health",
        }

    @app.get("/health")
    async def root_health():
        wa_status = "unknown"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get("http://127.0.0.1:3000/health")
                wa_status = r.json().get("status", "disconnected")
        except Exception:
            wa_status = "offline"
        return {
            "status": "ok",
            "service": "jenna-api",
            "antigravity": "active",
            "whatsapp": wa_status,
        }

    @app.get("/whatsapp/status")
    async def whatsapp_status():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get("http://127.0.0.1:3000/health")
                return r.json()
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    @app.get("/whatsapp/qr")
    async def whatsapp_qr():
        from fastapi.responses import HTMLResponse
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get("http://127.0.0.1:3000/qr")
                return HTMLResponse(content=r.text, status_code=r.status_code)
        except Exception as e:
            return HTMLResponse(content=f"<h3>WhatsApp Bridge Offline or Loading: {e}</h3>", status_code=503)

    return app


app = create_app()
