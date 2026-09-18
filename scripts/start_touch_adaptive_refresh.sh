#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Jenna Dynamic Touch-Adaptive 144Hz / 60Hz Governor Launcher
# ==============================================================================

WORKSPACE="/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna"
LOGS="$WORKSPACE/logs"
mkdir -p "$LOGS"

# Stop existing instance if running
pkill -f "touch_adaptive_refresh_daemon.py" 2>/dev/null || true
sleep 0.5

echo "⚡ Starting Touch-Adaptive Refresh Rate Governor (144Hz Touch / 60Hz Idle)..."
nohup python3 -u "$WORKSPACE/scripts/touch_adaptive_refresh_daemon.py" > "$LOGS/touch_refresh.log" 2>&1 &
echo $! > "$LOGS/touch_refresh.pid"

sleep 1
if pgrep -f "touch_adaptive_refresh_daemon.py" >/dev/null 2>&1; then
    echo "✅ Touch-Adaptive Refresh Governor is LIVE! (PID: $(pgrep -f "touch_adaptive_refresh_daemon.py"))"
    echo "  - Screen Touch: 144.0 Hz INSTANT BOOST"
    echo "  - Finger Lift:  60.0 Hz AUTO DROP"
else
    echo "❌ Failed to start touch adaptive refresh governor. Check $LOGS/touch_refresh.log"
fi
