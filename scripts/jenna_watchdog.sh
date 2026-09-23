#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Jenna God Mode Watchdog — Keeps bridge + backend alive 24/7
# Run this once — it auto-restarts everything if they crash
# ==============================================================================

WORKSPACE="/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna"
LOGS="$WORKSPACE/logs"
mkdir -p "$LOGS"

echo "🔥 Jenna God Mode Watchdog started"

while true; do

    # 1. Backend check + restart
    if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "$(date): Backend down — restarting..."
        PYTHONPATH="$WORKSPACE/apps/api" nohup python3 -m uvicorn app.main:app \
            --app-dir "$WORKSPACE/apps/api" \
            --host 0.0.0.0 --port 8000 \
            > "$LOGS/backend.log" 2>&1 &
        sleep 8
    fi

    # 2. God Mode Bridge check + restart
    if ! pgrep -f "phone_bridge_client.py" > /dev/null 2>&1; then
        echo "$(date): God Mode Bridge down — restarting..."
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            BRIDGE_URL="ws://127.0.0.1:8000/device/bridge"
        else
            BRIDGE_URL="wss://jenna-anti.onrender.com/device/bridge"
        fi
        JENNA_BRIDGE_WS_URL="$BRIDGE_URL" setsid python3 -u \
            "$WORKSPACE/scripts/phone_bridge_client.py" \
            </dev/null >> "$LOGS/god_mode_bridge.log" 2>&1 &
        sleep 3
    fi

    # Check every 30 seconds
    sleep 30

done
