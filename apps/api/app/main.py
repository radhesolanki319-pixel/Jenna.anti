import asyncio
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
    device_bridge,
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

    # Autonomic Doctor Background Watchdog Loop
    async def doctor_watchdog_loop():
        from app.services.autonomic_doctor import autonomic_doctor
        while True:
            try:
                await asyncio.sleep(60)  # Check every 60 seconds
                diag = await autonomic_doctor.diagnose_system()
                if diag.get("status") in ("DEGRADED", "CRITICAL"):
                    logger.warning(f"Autonomic Doctor Warning: {diag.get('diagnosis_summary')} (Score: {diag.get('health_score')})")
            except asyncio.CancelledError:
                break
            except Exception as d_err:
                logger.debug(f"Doctor watchdog check error: {d_err}")

    doctor_task = asyncio.create_task(doctor_watchdog_loop())
    keep_alive_task = asyncio.create_task(keep_alive_loop())
    yield

    # Clean shutdown
    doctor_task.cancel()
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
    app.include_router(device_bridge.router)



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

    @app.get("/doctor/diagnose")
    async def doctor_diagnose_endpoint():
        """Autonomic Doctor Vitals & Health Diagnosis."""
        from app.services.autonomic_doctor import autonomic_doctor
        return await autonomic_doctor.diagnose_system()

    @app.get("/doctor/logs")
    async def doctor_logs_endpoint(limit: int = 30, level: str | None = None):
        """Autonomic Doctor Recent Logs & Error Tracebacks."""
        from app.services.autonomic_doctor import autonomic_doctor
        logs = autonomic_doctor.inspect_logs(limit=limit, level=level)
        return {
            "count": len(logs),
            "logs": logs,
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

    @app.get("/whatsapp/groups")
    async def whatsapp_groups():
        """Retrieve all WhatsApp groups the bot is participating in."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get("http://127.0.0.1:3000/groups")
                return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/whatsapp/chats")
    async def whatsapp_live_chats(limit: int = 50):
        """Retrieve live WhatsApp chat history stored in Cloud container."""
        import json
        import os
        from pathlib import Path
        conv_dir = Path(os.getenv("JENNA_WORKSPACE_ROOT", "/app")) / "data" / "conversations"
        results = {}
        if conv_dir.exists():
            for f in conv_dir.glob("*.jsonl"):
                try:
                    lines = [json.loads(line) for line in f.read_text(encoding="utf-8").strip().split("\n") if line.strip()]
                    results[f.stem] = lines[-limit:]
                except Exception:
                    pass
            for f in conv_dir.glob("*.json"):
                if f.stem not in results:
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        if isinstance(data, list):
                            results[f.stem] = data[-limit:]
                    except Exception:
                        pass
        return {"total_threads": len(results), "conversations": results}

    @app.get("/whatsapp/live")
    async def whatsapp_live_viewer():
        """Web UI to view live WhatsApp chat messages."""
        from fastapi.responses import HTMLResponse
        data = await whatsapp_live_chats(limit=100)
        convs = data.get("conversations", {})
        html = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Jenna Live WhatsApp Chats</title>
<meta http-equiv="refresh" content="10">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
.header { max-width: 800px; margin: 0 auto 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; }
h1 { color: #38bdf8; margin: 0; font-size: 20px; }
.badge { background: #10b981; color: #0f172a; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 12px; }
.chat-box { max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 12px; }
.msg { padding: 12px 16px; border-radius: 12px; max-width: 75%; font-size: 14px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
.msg.user { align-self: flex-end; background: #0284c7; color: #fff; }
.msg.assistant { align-self: flex-start; background: #1e293b; color: #f1f5f9; border: 1px solid #334155; }
.meta { font-size: 11px; opacity: 0.7; margin-bottom: 4px; }
</style></head><body>
<div class="header"><h1>💬 Jenna Live WhatsApp Monitor</h1><span class="badge">LIVE (Auto-refresh 10s)</span></div>
<div class="chat-box">"""
        if not convs:
            html += "<p style='text-align:center;color:#64748b;'>No messages recorded in this container yet. Send a message on WhatsApp to start!</p>"
        else:
            import datetime
            IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            for user, msgs in convs.items():
                for m in msgs:
                    role = m.get("role", "user")
                    ts = m.get("timestamp")
                    if ts:
                        time_str = datetime.datetime.fromtimestamp(ts, tz=IST).strftime("%I:%M:%S %p IST")
                    else:
                        time_str = m.get("time_str", "")
                    content = m.get("content", "")
                    sender = "Boss 👑" if role == "user" else "Jenna 🤖"
                    html += f'<div class="msg {role}"><div class="meta">{sender} • {time_str}</div><div>{content}</div></div>'
        html += "</div></body></html>"
        return HTMLResponse(content=html)

    return app


app = create_app()
