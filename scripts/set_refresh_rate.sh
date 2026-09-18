#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# iQOO Neo 10 Display Refresh Rate Governor (Snapdragon 8 Gen 4 / 60Hz - 144Hz)
# ==============================================================================

MODE="${1:-status}"
SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"

if [ -z "$SERIAL" ]; then
    echo "❌ Error: No ADB device connected. Connect wireless ADB first."
    exit 1
fi

case "$MODE" in
    144|144hz|ultra|gaming)
        adb -s "$SERIAL" shell settings put system peak_refresh_rate 144.0
        adb -s "$SERIAL" shell settings put system user_refresh_rate 144.0
        adb -s "$SERIAL" shell settings put system min_refresh_rate 144.0
        echo "⚡ Display Refresh Rate LOCKED to 144Hz (Ultra Gaming & High Velocity Mode)"
        ;;
    120|120hz|smooth)
        adb -s "$SERIAL" shell settings put system peak_refresh_rate 120.0
        adb -s "$SERIAL" shell settings put system user_refresh_rate 120.0
        adb -s "$SERIAL" shell settings put system min_refresh_rate 60.0
        echo "✨ Display Refresh Rate set to 120Hz (Adaptive Smooth Mode)"
        ;;
    60|60hz|battery|eco)
        adb -s "$SERIAL" shell settings put system peak_refresh_rate 60.0
        adb -s "$SERIAL" shell settings put system user_refresh_rate 60.0
        adb -s "$SERIAL" shell settings put system min_refresh_rate 60.0
        echo "🔋 Display Refresh Rate LOCKED to 60Hz (Ultra Battery Saver Mode)"
        ;;
    status|*)
        PEAK=$(adb -s "$SERIAL" shell settings get system peak_refresh_rate 2>/dev/null | tr -d '\r')
        USER=$(adb -s "$SERIAL" shell settings get system user_refresh_rate 2>/dev/null | tr -d '\r')
        MIN=$(adb -s "$SERIAL" shell settings get system min_refresh_rate 2>/dev/null | tr -d '\r')
        echo "📊 Display Refresh Rate Status on $SERIAL:"
        echo "  - Peak Rate:  ${PEAK:-unknown} Hz"
        echo "  - User Rate:  ${USER:-unknown} Hz"
        echo "  - Min Rate:   ${MIN:-unknown} Hz"
        ;;
esac
