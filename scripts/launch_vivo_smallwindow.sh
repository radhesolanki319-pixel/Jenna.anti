#!/data/data/com.termux/files/usr/bin/bash
# Autonomous Vivo Funtouch OS 15 Small Window Trigger
# Created for Jenna AI Companion
set -e

APP="${1:-youtube}"
URL="${2:-}"
SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
if [ -z "$SERIAL" ]; then
    adb connect 127.0.0.1:5555 >/dev/null 2>&1 || true
    SERIAL="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
fi
ADB_CMD="adb ${SERIAL:+-s $SERIAL}"

launch_slot() {
    local y_coord="$1"
    $ADB_CMD shell "input swipe 5 480 200 480 600 && sleep 0.25 && input tap 155 $y_coord"
}

launch_custom_pkg() {
    local pkg="$1"
    local original="com.whatsapp,0;com.google.android.youtube,0;com.vivo.notes,0;com.google.android.apps.messaging,0;com.vivo.gallery,0;com.google.android.googlequicksearchbox,0;com.android.chrome,0"
    $ADB_CMD shell "settings put system upslide_quick_launch_apps_overseas '${pkg},0;${original}'"
    sleep 0.2
    $ADB_CMD shell "input swipe 5 480 200 480 600 && sleep 0.25 && input tap 155 410"
    sleep 0.8
    # restore standard list
    $ADB_CMD shell "settings put system upslide_quick_launch_apps_overseas '${original}'"
}

case "$APP" in
    youtube)
        launch_slot 650
        if [ -n "$URL" ]; then
            sleep 1.2
            $ADB_CMD shell "am start -a android.intent.action.VIEW -d '$URL'" >/dev/null 2>&1 || true
        fi
        echo "YouTube launched in Vivo Small Window"
        ;;
    whatsapp)
        launch_slot 410
        echo "WhatsApp launched in Vivo Small Window"
        ;;
    notes)
        launch_slot 880
        echo "Notes launched in Vivo Small Window"
        ;;
    messages|sms)
        launch_slot 1120
        echo "Messages launched in Vivo Small Window"
        ;;
    gallery|albums|photos)
        launch_slot 1360
        echo "Gallery launched in Vivo Small Window"
        ;;
    google|search)
        launch_slot 1600
        echo "Google Search launched in Vivo Small Window"
        ;;
    chrome|browser)
        launch_slot 1840
        if [ -n "$URL" ]; then
            sleep 1.2
            $ADB_CMD shell "am start -n com.android.chrome/com.google.android.apps.chrome.Main -d '$URL'" >/dev/null 2>&1 || $ADB_CMD shell "am start -a android.intent.action.VIEW -d '$URL'" >/dev/null 2>&1 || true
        fi
        echo "Chrome launched in Vivo Small Window"
        ;;
    calculator)
        launch_custom_pkg "com.vivo.calculator"
        echo "Calculator launched in Vivo Small Window"
        ;;
    telegram)
        launch_custom_pkg "org.telegram.messenger"
        echo "Telegram launched in Vivo Small Window"
        ;;
    instagram)
        launch_custom_pkg "com.instagram.android"
        echo "Instagram launched in Vivo Small Window"
        ;;
    spotify)
        launch_custom_pkg "com.spotify.music"
        echo "Spotify launched in Vivo Small Window"
        ;;
    *)
        # Generic package or unknown app
        launch_custom_pkg "$APP"
        echo "Application $APP launched in Vivo Small Window"
        ;;
esac
