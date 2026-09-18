#!/data/data/com.termux/files/usr/bin/bash
# start_wake_word.sh — Launch Jenna wake word listener as a background daemon.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/wake_word.log"
PID_FILE="$LOG_DIR/wake_word.pid"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    EXISTING_PID=$(cat "$PID_FILE")
    if kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "⚠️  Wake word listener is already running (PID: $EXISTING_PID)"
        echo "   Log: $LOG_FILE"
        echo "   To stop: kill $EXISTING_PID"
        exit 0
    else
        echo "Stale PID file found, removing."
        rm -f "$PID_FILE"
    fi
fi

echo "🎙️  Starting Jenna wake word listener…"
echo "   Log: $LOG_FILE"

nohup python3 -u "$PROJECT_ROOT/scripts/wake_word_listener.py" \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo "$PID" > "$PID_FILE"
echo "✅ Wake word listener started! PID: $PID"
echo "   Monitor: tail -f $LOG_FILE"
echo "   Stop:    kill $PID  (or: kill \$(cat $PID_FILE))"
