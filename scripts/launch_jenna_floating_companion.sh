#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# 🐱 Jenna Floating Screen Companion & Mascot Launcher
# Launches Jenna's interactive floating avatar (Dex Cat / Cyberpunk)
# directly into Android Freeform Multi-Window / Vivo Small Window mode!
# ==============================================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPANION_URL="http://localhost:3001/companion"
SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
if [ -z "$SERIAL" ]; then
    adb connect 127.0.0.1:5555 >/dev/null 2>&1 || true
    SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
fi

echo "=================================================="
echo "  🐱 Launching Jenna Floating Companion Avatar    "
echo "=================================================="

# Check if web server is reachable
if ! curl -s -I http://127.0.0.1:3001 >/dev/null 2>&1; then
    echo "⚠️ Web frontend not running on port 3001. Starting..."
    bash "$PROJECT_ROOT/scripts/start_all.sh"
    sleep 3
fi

echo "🚀 Opening Companion in Freeform / Small Window Mode..."

# Method 1: Launch via Android Intent in Freeform Windowing Mode (5)
adb -s "$SERIAL" shell "am start --windowingMode 5 -a android.intent.action.VIEW -d '$COMPANION_URL'" >/dev/null 2>&1 || true

# Method 2: Also trigger via Chrome direct component if available
adb -s "$SERIAL" shell "am start --windowingMode 5 -n com.android.chrome/com.google.android.apps.chrome.Main -d '$COMPANION_URL'" >/dev/null 2>&1 || true

# Toast notification for user (silenced for noise suppression)
# termux-toast -b "#ec4899" -c "#ffffff" "🐱 Jenna Copilot is living on your screen!" 2>/dev/null || true

echo "✅ Jenna Floating Companion launched at: $COMPANION_URL"
echo "Tip: You can drag, resize, or minimize it to a floating bubble on your phone screen!"
