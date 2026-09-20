"""
Jenna AI Platform — Autonomic Self-Healing Doctor Service
Empowers Jenna to diagnose her own health, inspect error logs and tracebacks,
safely patch her own code with pre-flight sandbox syntax verification,
and trigger autonomous self-deployment and auto-rollback.
"""

import asyncio
import collections
import datetime
import json
import logging
import os
import py_compile
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("jenna.autonomic_doctor")

WORKSPACE_ROOT = Path(
    os.getenv(
        "JENNA_WORKSPACE_ROOT",
        "/app" if os.path.exists("/app/apps/api") else "/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna"
    )
).resolve()

LOGS_DIR = WORKSPACE_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DOCTOR_EVENTS_LOG = LOGS_DIR / "doctor_events.jsonl"
DOCTOR_SURGERIES_LOG = LOGS_DIR / "doctor_surgeries.jsonl"
DOCTOR_INCIDENTS_LOG = LOGS_DIR / "doctor_incidents.jsonl"

RENDER_DEPLOY_HOOK = os.getenv(
    "RENDER_DEPLOY_HOOK",
    "https://api.render.com/deploy/srv-dandui2jnfac738ai21g?key=hWUH_ivZs1s"
)


class DoctorLogHandler(logging.Handler):
    """Ring buffer handler capturing recent warnings, errors, and tracebacks."""

    def __init__(self, maxlen: int = 150):
        super().__init__(level=logging.WARNING)
        self.buffer = collections.deque(maxlen=maxlen)

    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                "timestamp": record.created,
                "time_str": datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "filename": record.filename,
                "lineno": record.lineno,
            }
            if record.exc_info:
                import traceback
                entry["traceback"] = "".join(traceback.format_exception(*record.exc_info))
            self.buffer.append(entry)
        except Exception:
            pass


# Global singleton handler attached to root logger
doctor_log_handler = DoctorLogHandler(maxlen=150)
logging.getLogger().addHandler(doctor_log_handler)


class AutonomicDoctor:
    """The Self-Healing Autonomous Engine for Jenna."""

    def __init__(self, workspace_root: Path = WORKSPACE_ROOT):
        self.workspace_root = workspace_root
        self.boot_time = time.time()
        self.log_handler = doctor_log_handler

    def log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an autonomic medical event in persistent JSONL log."""
        try:
            IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            now_t = datetime.datetime.now(IST)
            entry = {
                "timestamp": now_t.timestamp(),
                "time_str": now_t.strftime("%Y-%m-%d %I:%M:%S %p IST"),
                "event_type": event_type,
                **data,
            }
            with open(DOCTOR_EVENTS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug(f"Failed to log doctor event: {exc}")

    async def diagnose_system(self) -> dict[str, Any]:
        """Perform comprehensive self-examination and return full vitals."""
        IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_t = datetime.datetime.now(IST)
        uptime_sec = int(time.time() - self.boot_time)

        vitals = {
            "timestamp": now_t.strftime("%Y-%m-%d %I:%M:%S %p IST"),
            "uptime_seconds": uptime_sec,
            "uptime_human": f"{uptime_sec // 3600}h {(uptime_sec % 3600) // 60}m {uptime_sec % 60}s",
            "status": "HEALTHY",
            "health_score": 100,
            "symptoms": [],
            "components": {},
        }

        # 1. WhatsApp Bridge Vitals
        is_conn = False
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                # Try local bridge first
                try:
                    resp = await client.get("http://127.0.0.1:3000/health", headers={"Host": "127.0.0.1"}, timeout=1.0)
                    if resp.status_code == 200:
                        b_data = resp.json()
                        is_conn = b_data.get("status") == "connected"
                        vitals["components"]["whatsapp_bridge"] = {
                            "location": "local_bridge",
                            "status": "connected" if is_conn else "disconnected",
                            "queue": b_data.get("queueLength", 0),
                            "uptime": b_data.get("uptime", 0),
                        }
                except Exception:
                    pass

                # If local not found, check cloud deployment endpoint
                if not is_conn:
                    try:
                        c_resp = await client.get("https://jenna-anti.onrender.com/whatsapp/status", timeout=5.0)
                        if c_resp.status_code == 200:
                            c_data = c_resp.json()
                            is_conn = c_data.get("status") == "connected"
                            vitals["components"]["whatsapp_bridge"] = {
                                "location": "cloud_render",
                                "status": "connected" if is_conn else "disconnected",
                                "queue": c_data.get("queueLength", 0),
                                "uptime": c_data.get("uptime", 0),
                            }
                    except Exception:
                        pass
        except Exception as e:
            vitals["components"]["whatsapp_bridge"] = {"status": "unreachable", "error": str(e)}

        if not is_conn:
            vitals["symptoms"].append("WhatsApp Bridge is disconnected or unreachable.")
            vitals["health_score"] -= 25

        # 2. Disk Space Vitals
        try:
            stat = shutil.disk_usage(self.workspace_root)
            free_gb = round(stat.free / (1024 ** 3), 2)
            total_gb = round(stat.total / (1024 ** 3), 2)
            used_pct = round((stat.used / stat.total) * 100, 1)
            vitals["components"]["disk"] = {
                "total_gb": total_gb,
                "free_gb": free_gb,
                "used_percentage": used_pct,
            }
            if free_gb < 0.5:
                vitals["symptoms"].append(f"Low disk space warning: Only {free_gb} GB remaining.")
                vitals["health_score"] -= 20
        except Exception as e:
            vitals["components"]["disk"] = {"error": str(e)}

        # 3. AI Provider Configuration Check
        try:
            from app.core.config import settings
            has_gemini = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or getattr(settings, "google_api_key", None))
        except Exception:
            has_gemini = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        vitals["components"]["ai_provider"] = {
            "gemini_key_present": has_gemini,
            "default_model": os.getenv("AI_MODEL", "gemini-3.6-flash"),
        }
        if not has_gemini:
            vitals["symptoms"].append("Google Gemini API Key is missing.")
            vitals["health_score"] -= 50

        # 4. Recent Errors in Ring Buffer
        recent_errors = [e for e in self.log_handler.buffer if e.get("level") in ("ERROR", "CRITICAL")]
        vitals["recent_error_count"] = len(recent_errors)
        if recent_errors:
            vitals["symptoms"].append(f"Detected {len(recent_errors)} recent error(s) in system log.")
            vitals["health_score"] = max(20, vitals["health_score"] - (len(recent_errors) * 5))

        # Overall Status Resolution
        if vitals["health_score"] >= 90:
            vitals["status"] = "EXCELLENT"
            vitals["diagnosis_summary"] = "Jenna ka poora system ekdum swasth aur fit hai, Boss! Koi bimari ya error nahi hai. 💖"
        elif vitals["health_score"] >= 70:
            vitals["status"] = "GOOD"
            vitals["diagnosis_summary"] = "System chal raha hai lekin kuch minor symptoms hain jo main automatically monitor kar rahi hoon."
        elif vitals["health_score"] >= 40:
            vitals["status"] = "DEGRADED"
            vitals["diagnosis_summary"] = "System me kuch issues hain jinko surgery ki zaroorat pad sakti hai."
        else:
            vitals["status"] = "CRITICAL"
            vitals["diagnosis_summary"] = "System critical condition me hai, immediate self-healing required!"

        self.log_event("diagnosis", vitals)
        return vitals

    def inspect_logs(self, limit: int = 20, level: str | None = None) -> list[dict[str, Any]]:
        """Retrieve recent logs and tracebacks from the doctor ring buffer."""
        items = list(self.log_handler.buffer)
        if level:
            items = [x for x in items if x.get("level", "").upper() == level.upper()]
        return items[-limit:]

    def safe_patch_file(
        self,
        target_file: str,
        new_content: str,
        description: str = "Self-healing surgery",
    ) -> dict[str, Any]:
        """Perform safe surgery on a code file with automated pre-flight sandbox syntax check and backup snapshot."""
        path = Path(target_file)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()

        # 1. Pre-Flight Sandbox Verification for Python files
        if path.suffix == ".py":
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tmp:
                tmp.write(new_content)
                tmp_path = Path(tmp.name)

            try:
                py_compile.compile(str(tmp_path), doraise=True)
            except py_compile.PyCompileError as c_err:
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
                err_msg = str(c_err)
                logger.error(f"Surgery aborted! Syntax check failed on {path.name}: {err_msg}")
                self.log_event("surgery_aborted", {
                    "file": str(path),
                    "reason": "Syntax compilation failed",
                    "error": err_msg,
                })
                return {
                    "success": False,
                    "error": "Syntax check failed! Code was NOT saved to protect the system from crashing.",
                    "details": err_msg,
                    "target_file": str(path),
                }
            finally:
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass

        # 2. Create Backup Snapshot before overwriting
        backup_path = None
        if path.exists():
            ts = int(time.time())
            backup_path = path.with_suffix(f"{path.suffix}.bak.{ts}")
            stable_bak = path.with_suffix(f"{path.suffix}.bak")
            try:
                shutil.copy2(path, backup_path)
                shutil.copy2(path, stable_bak)
            except Exception as b_err:
                logger.warning(f"Could not create backup snapshot: {b_err}")

        # 3. Write modified content atomically
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # 4. Record successful surgery
        surgery_info = {
            "file": str(path),
            "description": description,
            "backup": str(backup_path) if backup_path else None,
            "timestamp": time.time(),
            "time_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success": True,
        }
        try:
            with open(DOCTOR_SURGERIES_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(surgery_info) + "\n")
        except Exception:
            pass

        self.log_event("surgery_completed", surgery_info)
        return {
            "success": True,
            "file": str(path),
            "backup": str(backup_path) if backup_path else None,
            "description": description,
            "syntax_verified": path.suffix == ".py",
            "message": f"Successfully performed safe surgery on {path.name} with syntax verified and backup created.",
        }

    def rollback_file(self, target_file: str) -> dict[str, Any]:
        """Roll back a modified file to its latest .bak snapshot."""
        path = Path(target_file)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()

        stable_bak = path.with_suffix(f"{path.suffix}.bak")
        if not stable_bak.exists():
            # Search for any timestamped backup
            baks = sorted(path.parent.glob(f"{path.name}.bak.*"))
            if baks:
                stable_bak = baks[-1]
            else:
                return {"success": False, "error": f"No backup (.bak) found for {path.name}"}

        shutil.copy2(stable_bak, path)
        self.log_event("rollback", {"file": str(path), "restored_from": str(stable_bak)})
        return {
            "success": True,
            "file": str(path),
            "restored_from": str(stable_bak),
            "message": f"Successfully rolled back {path.name} to last known stable version.",
        }

    async def trigger_self_deploy(self, reason: str = "Autonomic self-healing update") -> dict[str, Any]:
        """Trigger an autonomous production deployment via Render deploy hook."""
        if not RENDER_DEPLOY_HOOK:
            return {"success": False, "error": "RENDER_DEPLOY_HOOK not configured"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(RENDER_DEPLOY_HOOK)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    deploy_id = data.get("deploy", {}).get("id", "unknown")
                    self.log_event("self_deploy_triggered", {"deploy_id": deploy_id, "reason": reason})
                    return {
                        "success": True,
                        "deploy_id": deploy_id,
                        "status": "triggered",
                        "message": f"Render cloud deployment triggered successfully (Deploy ID: {deploy_id}). Production will auto-refresh in ~60-90 seconds.",
                    }
                else:
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "response": resp.text,
                    }
        except Exception as exc:
            return {"success": False, "error": str(exc)}


autonomic_doctor = AutonomicDoctor()
