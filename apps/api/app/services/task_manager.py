"""Background Task Daemon & Process Manager for Jenna & Antigravity.

Enables asynchronous task dispatching, live log streaming, STDIN pipe injection,
and full lifecycle management (list, status, kill) without blocking agent loops.
"""

from dataclasses import dataclass, field
import datetime
import json
import logging
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any, Optional

logger = logging.getLogger("jenna.task_manager")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TASKS_DIR = WORKSPACE_ROOT / ".system_generated" / "tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class BackgroundTask:
    task_id: str
    command: str
    tool_summary: str
    tool_action: str
    cwd: str
    start_time: str
    pid: Optional[int] = None
    status: str = "RUNNING"  # RUNNING, DONE, FAILED, KILLED
    exit_code: Optional[int] = None
    log_file: str = ""
    process: Optional[subprocess.Popen] = field(default=None, repr=False)


class TaskManager:
    """Manages long-running asynchronous processes and background tasks."""

    def __init__(self) -> None:
        self.tasks: dict[str, BackgroundTask] = {}
        self.registry_file = TASKS_DIR / "tasks_registry.json"
        self._load_registry()

    def _load_registry(self) -> None:
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                for tid, item in data.items():
                    # Check if process is still running
                    status = item.get("status", "DONE")
                    pid = item.get("pid")
                    if pid and status == "RUNNING":
                        try:
                            os.kill(pid, 0)
                        except OSError:
                            status = "DONE"
                    self.tasks[tid] = BackgroundTask(
                        task_id=tid,
                        command=item["command"],
                        tool_summary=item.get("tool_summary", "Background Command"),
                        tool_action=item.get("tool_action", "Running command"),
                        cwd=item.get("cwd", str(WORKSPACE_ROOT)),
                        start_time=item.get("start_time", ""),
                        pid=pid,
                        status=status,
                        exit_code=item.get("exit_code"),
                        log_file=item.get("log_file", ""),
                    )
            except Exception as exc:
                logger.warning(f"Failed to load task registry: {exc}")

    def _save_registry(self) -> None:
        try:
            data = {}
            for tid, t in self.tasks.items():
                data[tid] = {
                    "task_id": t.task_id,
                    "command": t.command,
                    "tool_summary": t.tool_summary,
                    "tool_action": t.tool_action,
                    "cwd": t.cwd,
                    "start_time": t.start_time,
                    "pid": t.pid,
                    "status": t.status,
                    "exit_code": t.exit_code,
                    "log_file": t.log_file,
                }
            self.registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to save task registry: {exc}")

    def launch_task(
        self,
        command: str,
        tool_summary: str = "Background Task",
        tool_action: str = "Running command",
        cwd: Optional[str] = None,
        wait_ms_before_async: int = 5000,
    ) -> dict[str, Any]:
        """Launch command. If it finishes within wait_ms_before_async, return synchronously.
        Otherwise, detach to background task and return task tracking info."""
        task_id = f"task-{int(time.time() * 1000) % 1000000}"
        log_path = TASKS_DIR / f"{task_id}.log"
        work_dir = Path(cwd).resolve() if cwd else WORKSPACE_ROOT

        log_file_handle = open(log_path, "w", encoding="utf-8")

        start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=str(work_dir),
            stdout=log_file_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

        task = BackgroundTask(
            task_id=task_id,
            command=command,
            tool_summary=tool_summary,
            tool_action=tool_action,
            cwd=str(work_dir),
            start_time=start_iso,
            pid=proc.pid,
            status="RUNNING",
            log_file=str(log_path),
            process=proc,
        )
        self.tasks[task_id] = task
        self._save_registry()

        # Wait synchronously up to wait_ms_before_async
        wait_sec = min(wait_ms_before_async / 1000.0, 10.0)
        start_wait = time.monotonic()
        while time.monotonic() - start_wait < wait_sec:
            ret = proc.poll()
            if ret is not None:
                task.status = "DONE" if ret == 0 else "FAILED"
                task.exit_code = ret
                log_file_handle.close()
                self._save_registry()
                output = log_path.read_text(encoding="utf-8", errors="replace")
                return {
                    "is_async": False,
                    "task_id": task_id,
                    "exit_code": ret,
                    "output": output,
                    "success": ret == 0,
                }
            time.sleep(0.05)

        # Still running -> Detach to background!
        logger.info(f"Task {task_id} exceeded wait threshold, running in background (PID: {proc.pid})")
        return {
            "is_async": True,
            "task_id": task_id,
            "pid": proc.pid,
            "status": "RUNNING",
            "log_file": str(log_path),
            "message": f"Command dispatched to background as task '{task_id}'. Monitor logs via manage_task.",
        }

    def list_tasks(self) -> list[dict[str, Any]]:
        """List all tracked background tasks."""
        self._check_tasks()
        res = []
        for t in self.tasks.values():
            res.append({
                "taskId": t.task_id,
                "toolSummary": t.tool_summary,
                "toolAction": t.tool_action,
                "command": t.command,
                "pid": t.pid,
                "status": t.status,
                "startTime": t.start_time,
                "logUri": t.log_file,
            })
        return res

    def get_status(self, task_id: str) -> dict[str, Any]:
        """Get live status and recent log snippet of a task."""
        self._check_tasks()
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found", "found": False}

        log_content = ""
        log_path = Path(task.log_file)
        if log_path.exists():
            try:
                text = log_path.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()
                log_content = "\n".join(lines[-40:])  # last 40 lines
            except Exception as e:
                log_content = f"Error reading log: {e}"

        return {
            "found": True,
            "taskId": task.task_id,
            "status": task.status,
            "pid": task.pid,
            "exit_code": task.exit_code,
            "logUri": task.log_file,
            "recent_output": log_content,
        }

    def kill_task(self, task_id: str) -> dict[str, Any]:
        """Terminate a running task."""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found", "success": False}

        if task.status != "RUNNING":
            return {"message": f"Task '{task_id}' is already {task.status}", "success": True}

        if task.pid:
            try:
                os.killpg(os.getpgid(task.pid), signal.SIGTERM)
                time.sleep(0.3)
                try:
                    os.killpg(os.getpgid(task.pid), signal.SIGKILL)
                except OSError:
                    pass
            except OSError:
                try:
                    os.kill(task.pid, signal.SIGKILL)
                except OSError:
                    pass

        task.status = "KILLED"
        self._save_registry()
        return {"message": f"Task '{task_id}' (PID: {task.pid}) terminated successfully.", "success": True}

    def send_input(self, task_id: str, input_str: str) -> dict[str, Any]:
        """Send STDIN input to a running task."""
        task = self.tasks.get(task_id)
        if not task or not task.process:
            return {"error": f"Task '{task_id}' is not actively running with open stdin pipe", "success": False}

        try:
            if task.process.stdin:
                task.process.stdin.write(input_str + "\n")
                task.process.stdin.flush()
                return {"message": f"Input sent to task '{task_id}'", "success": True}
        except Exception as exc:
            return {"error": f"Failed to send input: {exc}", "success": False}

        return {"error": "Stdin pipe unavailable", "success": False}

    async def start_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        wait_ms: int = 5000,
        tool_summary: str = "Background Command",
        tool_action: str = "Running command",
    ) -> dict[str, Any]:
        """Async wrapper around launch_task for AntigravityAgent integration."""
        import asyncio
        return await asyncio.to_thread(
            self.launch_task,
            command=command,
            cwd=cwd,
            tool_summary=tool_summary,
            tool_action=tool_action,
            wait_ms_before_async=wait_ms,
        )

    def _check_tasks(self) -> None:
        """Poll running processes to update their status."""
        for task in list(self.tasks.values()):
            if task.status == "RUNNING" and task.pid:
                try:
                    if task.process:
                        ret = task.process.poll()
                        if ret is not None:
                            task.status = "DONE" if ret == 0 else "FAILED"
                            task.exit_code = ret
                    else:
                        os.kill(task.pid, 0)
                except OSError:
                    task.status = "DONE"
        self._save_registry()


task_manager = TaskManager()
