#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Jenna AI — Wireless ADB Pairing & Auto-Connect Helper
# Usage: ./scripts/pair_wireless_adb.sh <pair_port> <pairing_code> [connect_port]
# ==============================================================================

PAIR_PORT="$1"
CODE="$2"
CONNECT_PORT="${3:-$PAIR_PORT}"

if [ -z "$PAIR_PORT" ] || [ -z "$CODE" ]; then
    echo "Usage: $0 <pair_port> <pairing_code> [connect_port]"
    echo "Example: $0 38475 123456 41235"
    exit 1
fi

echo "🔗 Pairing with localhost:$PAIR_PORT using code $CODE..."
adb pair "localhost:$PAIR_PORT" "$CODE"

sleep 1

echo "🚀 Connecting to localhost:$CONNECT_PORT..."
adb connect "localhost:$CONNECT_PORT"

sleep 1
adb devices
