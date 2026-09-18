#!/data/data/com.termux/files/usr/bin/bash
# Jenna AI — Safe Shutdown Script for Termux / Linux

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "  🛑 Stopping Jenna AI Services...                "
echo "=================================================="

# Stop Frontend
if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "  Stopping Next.js frontend (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
    fi
    rm -f "$PROJECT_ROOT/logs/frontend.pid"
fi
pkill -f "next-server" 2>/dev/null || true

# Stop Backend
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "  Stopping FastAPI backend (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
    fi
    rm -f "$PROJECT_ROOT/logs/backend.pid"
fi
pkill -f "uvicorn app.main:app" 2>/dev/null || true

echo "  ✅ Jenna AI services stopped cleanly."
echo "=================================================="
