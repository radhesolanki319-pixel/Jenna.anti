"""Reactive Scheduling & Autonomous Cron Engine for Jenna & Antigravity.

Enables one-shot timers with conditional early termination ('never', 'any', <sender-id>)
and recurring 5-field crons without CPU-wasteful polling.
"""

import asyncio
from dataclasses import dataclass
import datetime
import logging
from pathlib import Path
import time
from typing import Any, Callable, Optional
import uuid

logger = logging.getLogger("jenna.scheduler")


@dataclass
class ScheduledJob:
    job_id: str
    prompt: str
    is_cron: bool
    duration_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    max_iterations: Optional[int] = None
    condition: str = "never"  # 'never', 'any', or a specific task_id / subagent_id
    current_iterations: int = 0
    status: str = "SCHEDULED"  # SCHEDULED, RUNNING, CANCELLED, EXPIRED
    created_at: float = 0.0
    fire_at: float = 0.0


class SchedulerService:
    """Manages one-shot timers and recurring cron triggers."""

    def __init__(self) -> None:
        self.jobs: dict[str, ScheduledJob] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._notify_callback: Optional[Callable[[str, str], Any]] = None

    def set_notify_callback(self, callback: Callable[[str, str], Any]) -> None:
        """Set callback to notify Jenna agent when a timer fires."""
        self._notify_callback = callback

    async def schedule_timer(
        self,
        duration_seconds: int,
        prompt: str,
        condition: str = "never",
        timer_condition: Optional[str] = None,
    ) -> dict[str, Any]:
        """Schedule a one-shot delayed timer."""
        job_id = f"timer-{uuid.uuid4().hex[:6]}"
        now = time.time()
        fire_at = now + duration_seconds
        cond = timer_condition or condition

        job = ScheduledJob(
            job_id=job_id,
            prompt=prompt,
            is_cron=False,
            duration_seconds=duration_seconds,
            condition=cond,
            created_at=now,
            fire_at=fire_at,
            status="SCHEDULED",
        )
        self.jobs[job_id] = job

        # Launch async wait task
        task = asyncio.create_task(self._timer_worker(job))
        self._tasks[job_id] = task

        logger.info(f"Scheduled one-shot timer [{job_id}] for {duration_seconds}s (Condition: {cond})")
        return {
            "success": True,
            "job_id": job_id,
            "duration_seconds": duration_seconds,
            "fire_at": datetime.datetime.fromtimestamp(fire_at, tz=datetime.timezone.utc).isoformat(),
            "condition": cond,
            "message": f"Timer [{job_id}] scheduled to notify in {duration_seconds}s.",
        }

    async def schedule_cron(
        self,
        cron_expression: str,
        prompt: str,
        max_iterations: Optional[int] = None,
    ) -> dict[str, Any]:
        """Schedule a recurring cron job."""
        job_id = f"cron-{uuid.uuid4().hex[:6]}"
        job = ScheduledJob(
            job_id=job_id,
            prompt=prompt,
            is_cron=True,
            cron_expression=cron_expression,
            max_iterations=max_iterations,
            created_at=time.time(),
            status="SCHEDULED",
        )
        self.jobs[job_id] = job

        task = asyncio.create_task(self._cron_worker(job))
        self._tasks[job_id] = task

        logger.info(f"Scheduled recurring cron [{job_id}] ({cron_expression})")
        return {
            "success": True,
            "job_id": job_id,
            "cron_expression": cron_expression,
            "max_iterations": max_iterations,
            "message": f"Recurring cron [{job_id}] registered successfully.",
        }

    async def _timer_worker(self, job: ScheduledJob) -> None:
        """Sleeps without CPU polling until timer expires or early termination occurs."""
        try:
            sleep_time = max(0.0, job.fire_at - time.time())
            await asyncio.sleep(sleep_time)

            if job.status == "SCHEDULED":
                job.status = "EXPIRED"
                logger.info(f"⏰ One-shot timer [{job.job_id}] FIRED! Prompt: '{job.prompt}'")
                if self._notify_callback:
                    try:
                        res = self._notify_callback(job.job_id, job.prompt)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception as e:
                        logger.error(f"Error in scheduler notify callback: {e}")

        except asyncio.CancelledError:
            job.status = "CANCELLED"
            logger.info(f"Timer [{job.job_id}] was cancelled early.")

    async def _cron_worker(self, job: ScheduledJob) -> None:
        """Parses cron interval and periodically triggers notifications."""
        # Simple minute-interval approximation for cron:
        # e.g., '*/5 * * * *' -> every 5 minutes (300s)
        interval = 60
        if job.cron_expression and "*/" in job.cron_expression:
            try:
                parts = job.cron_expression.split()
                if "*/" in parts[0]:
                    mins = int(parts[0].replace("*/", ""))
                    interval = max(30, mins * 60)
            except Exception:
                interval = 300

        try:
            while job.status == "SCHEDULED":
                await asyncio.sleep(interval)
                if job.status != "SCHEDULED":
                    break

                job.current_iterations += 1
                logger.info(f"⏱️ Cron [{job.job_id}] triggered (Iteration {job.current_iterations})")

                if self._notify_callback:
                    try:
                        res = self._notify_callback(job.job_id, job.prompt)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception as e:
                        logger.error(f"Error in cron notify callback: {e}")

                if job.max_iterations and job.current_iterations >= job.max_iterations:
                    job.status = "EXPIRED"
                    break

        except asyncio.CancelledError:
            job.status = "CANCELLED"
            logger.info(f"Cron [{job.job_id}] was cancelled.")

    def on_event_received(self, sender_id: str) -> None:
        """Check if any active timer should early-terminate on event from sender_id."""
        for jid, job in list(self.jobs.items()):
            if job.status == "SCHEDULED" and not job.is_cron:
                if job.condition == "any" or job.condition == sender_id:
                    logger.info(f"Timer [{jid}] cancelled early by message from [{sender_id}]")
                    self.cancel_job(jid)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Cancel a running timer or cron schedule."""
        job = self.jobs.get(job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found", "success": False}

        job.status = "CANCELLED"
        if job_id in self._tasks:
            self._tasks[job_id].cancel()

        return {"success": True, "message": f"Job '{job_id}' cancelled."}

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all registered timers and cron schedules."""
        res = []
        for jid, j in self.jobs.items():
            res.append({
                "jobId": j.job_id,
                "prompt": j.prompt,
                "isCron": j.is_cron,
                "cronExpression": j.cron_expression,
                "durationSeconds": j.duration_seconds,
                "condition": j.condition,
                "status": j.status,
                "currentIterations": j.current_iterations,
                "maxIterations": j.max_iterations,
            })
        return res

    def list_schedules(self) -> list[dict[str, Any]]:
        """Alias for list_jobs for Antigravity API compatibility."""
        return self.list_jobs()


scheduler_service = SchedulerService()
