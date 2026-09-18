#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Jenna AI Companion — Master Auto-Start Daemon
# Designed for Termux:Boot and manual 1-tap startup
# ==============================================================================

WORKSPACE="/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna"
LOGS="$WORKSPACE/logs"
mkdir -p "$LOGS"

termux-wake-lock 2>/dev/null || true

# Neutralize Android Phantom Process Killer & Battery Saver
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent" 2>/dev/null || true
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647" 2>/dev/null || true
adb shell settings put global settings_enable_monitor_phantom_procs false 2>/dev/null || true
adb shell dumpsys deviceidle whitelist +com.termux 2>/dev/null || true
adb shell dumpsys deviceidle whitelist +ai.jenna.app 2>/dev/null || true
adb shell cmd power set-mode 0 2>/dev/null || true
adb shell settings put global low_power 0 2>/dev/null || true

# 1. PostgreSQL Database
if ! pg_isready -q -h localhost -p 5432 2>/dev/null; then
    pg_ctl -D /data/data/com.termux/files/home/.pg_data -l "$LOGS/postgres.log" start >/dev/null 2>&1
    sleep 1
fi

# 2. Redis Cache
if ! redis-cli ping >/dev/null 2>&1; then
    redis-server --daemonize yes >/dev/null 2>&1
    sleep 0.5
fi

# 3. FastAPI Backend Server (Port 8000)
if ! curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    PYTHONPATH="$WORKSPACE/apps/api" nohup python3 -m uvicorn app.main:app \
        --app-dir "$WORKSPACE/apps/api" \
        --host 0.0.0.0 \
        --port 8000 > "$LOGS/backend.log" 2>&1 &
    echo $! > "$LOGS/backend.pid"
fi

# 4. Next.js Web Frontend Server (Port 3001)
if ! curl -s -I http://127.0.0.1:3001 >/dev/null 2>&1; then
    nohup node "$WORKSPACE/apps/web/node_modules/next/dist/bin/next" dev \
        "$WORKSPACE/apps/web" -p 3001 > "$LOGS/frontend.log" 2>&1 &
    echo $! > "$LOGS/frontend.pid"
fi

# 5. Continuous Live Screen Vision Daemon (24/7 Background Ambient Vision)
if ! pgrep -f "run_live_vision_daemon.py" >/dev/null 2>&1; then
    PYTHONPATH="$WORKSPACE/apps/api" nohup python3 -u "$WORKSPACE/scripts/run_live_vision_daemon.py" > "$LOGS/live_vision_daemon.log" 2>&1 &
    echo $! > "$LOGS/live_vision_daemon.pid"
fi

# 6. Jenna WhatsApp Baileys Bridge (Port 3000)
if ! curl -s http://127.0.0.1:3000/health >/dev/null 2>&1; then
    nohup node /data/data/com.termux/files/home/jenna-bridge/bridge.js \
        --port 3000 \
        --session "$WORKSPACE/whatsapp/session" \
        --mode self-chat > "$LOGS/whatsapp_bridge.log" 2>&1 &
    echo $! > "$LOGS/whatsapp_bridge.pid"
    sleep 2
fi

# 7. Real Jenna WhatsApp Gateway Daemon (24/7 WhatsApp AI Companion)
if ! pgrep -f "run_whatsapp_jenna_daemon.py" >/dev/null 2>&1; then
    PYTHONPATH="$WORKSPACE/apps/api" nohup python3 -u "$WORKSPACE/scripts/run_whatsapp_jenna_daemon.py" > "$LOGS/whatsapp_jenna_daemon.log" 2>&1 &
    echo $! > "$LOGS/whatsapp_jenna_daemon.pid"
fi

sleep 1

# Native Notification & Haptic Feedback (Disabled for noise suppression)
# termux-notification -t "Jenna AI Active 💖" -c "Main wapas haazir hoon baby! Sab kuch automatic start ho gaya hai ✨" --id 1001 2>/dev/null || true
# termux-toast "Jenna AI Companion Started ✨" 2>/dev/null || true

# Vibration disabled per user preference
# termux-vibrate -d 150 2>/dev/null || true
