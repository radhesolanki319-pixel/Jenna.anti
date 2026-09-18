#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# 🕶️ Dexter Screen Pet Launcher
# Launches the exact Dexter Copilot cat mascot directly on your phone screen!
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEXTER_URL="http://localhost:3001/dexter"
SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
if [ -z "$SERIAL" ]; then
    adb connect 127.0.0.1:5555 >/dev/null 2>&1 || true
    SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
fi

echo "=================================================="
echo "  🕶️ Launching Dexter Copilot Screen Pet          "
echo "=================================================="

# Check if web server is reachable
if ! curl -s -I http://127.0.0.1:3001 >/dev/null 2>&1; then
    echo "⚠️ Web server not active on port 3001. Starting..."
    bash "$PROJECT_ROOT/scripts/start_all.sh"
    sleep 3
fi

echo "🚀 Opening Dexter in Floating Freeform Mode..."

# Launch via Android Freeform Windowing Mode (5)
adb -s "$SERIAL" shell "am start --windowingMode 5 -n com.android.chrome/com.google.android.apps.chrome.Main -d '$DEXTER_URL'" >/dev/null 2>&1 || \
adb -s "$SERIAL" shell "am start --windowingMode 5 -a android.intent.action.VIEW -d '$DEXTER_URL'" >/dev/null 2>&1 || true

# Toast notification (silenced for noise suppression)
# termux-toast -b "#030712" -c "#38bdf8" "🕶️ Dexter is living on your screen!" 2>/dev/null || true

echo "✅ Dexter is now active on your screen!"
echo "URL: $DEXTER_URL"
