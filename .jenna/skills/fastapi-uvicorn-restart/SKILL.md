---
name: fastapi-uvicorn-restart
description: Procedure for safely terminating and restarting FastAPI uvicorn daemon on Termux
version: 1.0.0
tags: ["fastapi", "uvicorn", "termux", "daemon"]
created_at: 2026-09-16T19:50:28.490792+00:00
author: Jenna AI
---

# fastapi-uvicorn-restart

1. Check running PID: pgrep -f uvicorn
2. Terminate PID cleanly: kill -15 <PID>
3. Relaunch in background: PYTHONPATH=. python3 -m uvicorn app.main:app --port 8000 --host 0.0.0.0
4. Verify /api/v1/health responds HTTP 200
