#!/data/data/com.termux/files/usr/bin/bash
# Jenna AI — Master Startup Script for Termux / Linux

set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "  🚀 Starting Jenna AI Platform on Termux         "
echo "=================================================="

# 0. Neutralize Android Phantom Process Killer & Battery Saver
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent" 2>/dev/null || true
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647" 2>/dev/null || true
adb shell settings put global settings_enable_monitor_phantom_procs false 2>/dev/null || true
adb shell dumpsys deviceidle whitelist +com.termux 2>/dev/null || true
adb shell dumpsys deviceidle whitelist +ai.jenna.app 2>/dev/null || true
adb shell cmd power set-mode 0 2>/dev/null || true
adb shell settings put global low_power 0 2>/dev/null || true

# 1. Start PostgreSQL if not accepting connections
if ! pg_isready -q >/dev/null 2>&1; then
    echo "📦 Starting PostgreSQL..."
    pg_ctl -D "/data/data/com.termux/files/home/.pg_data" start || true
    sleep 2
fi

if pg_isready -q >/dev/null 2>&1; then
    echo "  ✅ PostgreSQL is running and ready."
else
    echo "  ⚠️ PostgreSQL failed to start. Check pg_ctl status."
fi

# 2. Start Redis if not responding to ping
if ! redis-cli ping >/dev/null 2>&1; then
    echo "📦 Starting Redis server..."
    redis-server --daemonize yes
    sleep 1
fi

if redis-cli ping >/dev/null 2>&1; then
    echo "  ✅ Redis is running (PONG)."
else
    echo "  ⚠️ Redis failed to start."
fi

mkdir -p "$PROJECT_ROOT/logs"

# 3. Check if Backend is already running on port 8000
if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "  ✅ Backend is already running on port 8000."
else
    echo "🚀 Starting FastAPI Backend on http://0.0.0.0:8000..."
    unset GOOGLE_GEMINI_BASE_URL
    setsid env PYTHONPATH="$PROJECT_ROOT/apps/api" python3 -m uvicorn app.main:app --app-dir "$PROJECT_ROOT/apps/api" --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/logs/backend.pid"
    echo "  Backend PID: $BACKEND_PID (logs at logs/backend.log)"
fi

# Wait for backend readiness
for i in {1..10}; do
    if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
        echo "  ✅ Backend is healthy and responding."
        break
    fi
    sleep 1
done

# 4. Check if Frontend is already running on port 3000
if curl -s http://127.0.0.1:3000 >/dev/null 2>&1; then
    echo "  ✅ Frontend is already running on port 3000."
else
    echo "🚀 Starting Next.js Frontend on http://0.0.0.0:3000..."
    cd "$PROJECT_ROOT/apps/web"
    setsid npm run dev -- -p 3000 -H 0.0.0.0 > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_ROOT/logs/frontend.pid"
    echo "  Frontend PID: $FRONTEND_PID (logs at logs/frontend.log)"
    cd "$PROJECT_ROOT"
fi

# Wait for frontend readiness
for i in {1..10}; do
    if curl -s http://127.0.0.1:3000 >/dev/null 2>&1; then
        echo "  ✅ Frontend is healthy and responding."
        break
    fi
    sleep 1
done

# 5. Continuous Live Screen Vision Daemon (24/7 Background Ambient Vision)
if ! pgrep -f "run_live_vision_daemon.py" >/dev/null 2>&1; then
    echo "👁️ Starting Continuous Live Screen Vision Daemon..."
    setsid env PYTHONPATH="$PROJECT_ROOT/apps/api" python3 -u "$PROJECT_ROOT/scripts/run_live_vision_daemon.py" > "$PROJECT_ROOT/logs/live_vision_daemon.log" 2>&1 &
    VISION_PID=$!
    echo $VISION_PID > "$PROJECT_ROOT/logs/live_vision_daemon.pid"
    echo "  Vision Daemon PID: $VISION_PID (logs at logs/live_vision_daemon.log)"
else
    echo "  ✅ Live Screen Vision Daemon is already active."
fi

# 6. Dexter Screen Pet Native Overlay
if ! pgrep -f "dexter_screen_pet.py" >/dev/null 2>&1; then
    echo "🐾 Starting Dexter Screen Pet Overlay..."
    setsid python3 "$PROJECT_ROOT/scripts/dexter_screen_pet.py" --run --x 480 --y 500 > "$PROJECT_ROOT/logs/dexter_pet.log" 2>&1 &
    DEXTER_PID=$!
    echo $DEXTER_PID > "$PROJECT_ROOT/logs/dexter_pet.pid"
    echo "  Dexter Pet PID: $DEXTER_PID (logs at logs/dexter_pet.log)"
else
    echo "  ✅ Dexter Screen Pet is already active on screen."
fi

echo ""
echo "=================================================="
echo "  🎉 JENNA AI IS NOW LIVE AND READY!             "
echo "=================================================="
echo ""
echo "  🌐 Web Dashboard:      http://localhost:3000"
echo "  🔌 API Documentation:  http://localhost:8000/docs"
echo "  📋 System Health:       http://localhost:3000/health"
echo "  💬 Chat with Jenna:    http://localhost:3000/chat"
echo "  🎙️ Voice Studio:       http://localhost:3000/voice"
echo "  🛠️ Tools & Research:   http://localhost:3000/tools"
echo "  📱 Android & Devices:  http://localhost:3000/devices"
echo "  ⚖️ Human Approvals:    http://localhost:3000/approvals"
echo ""
echo "  To view logs: tail -f logs/backend.log"
echo "  To check status: ./status_jenna.sh"
echo "  To stop: ./stop_jenna.sh"
echo "=================================================="
