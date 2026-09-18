#!/data/data/com.termux/files/usr/bin/bash
# Direct Hardware Bypass Charging Controller for iQOO Neo 10 (Snapdragon 8 Gen 4)
# Automated trigger via Game Assistant (com.vivo.gamecube) UI coordinator

DEVICE="emulator-5554"

current_flag=$(adb -s "$DEVICE" shell getprop persist.vivo.game_bypass_charge_flag 2>/dev/null | tr -d '\r')
target="${1:-toggle}"

echo "⚡ [Bypass Charging Controller - iQOO Neo 10]"
echo "Current State: persist.vivo.game_bypass_charge_flag = $current_flag"

if [ "$target" = "on" ] && [ "$current_flag" = "1" ]; then
    echo "✅ Bypass Charging is ALREADY ON!"
    exit 0
fi

if [ "$target" = "off" ] && [ "$current_flag" = "0" ]; then
    echo "✅ Bypass Charging is ALREADY OFF!"
    exit 0
fi

# Ensure Game Mode context is recognized by GameCube
adb -s "$DEVICE" shell settings put system is_game_mode 1
adb -s "$DEVICE" shell settings put system current_game_package com.pubg.imobile

# Swipe open Game Assistant sidebar handle from left edge
adb -s "$DEVICE" shell input swipe 0 350 400 350 200
sleep 0.6

# Tap Bypass Charging toggle (Exact verified coordinates: X=485, Y=1085)
adb -s "$DEVICE" shell input tap 485 1085
sleep 0.8

new_flag=$(adb -s "$DEVICE" shell getprop persist.vivo.game_bypass_charge_flag 2>/dev/null | tr -d '\r')
echo "New State: persist.vivo.game_bypass_charge_flag = $new_flag"

if [ "$new_flag" = "1" ]; then
    echo "🟢 Hardware Bypass Charging ACTIVATED! Power flows directly to motherboard."
else
    echo "⚪ Bypass Charging state toggled to: $new_flag"
fi
