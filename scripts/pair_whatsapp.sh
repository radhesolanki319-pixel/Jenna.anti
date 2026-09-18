#!/data/data/com.termux/files/usr/bin/bash
SESSION="/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/whatsapp/session"
mkdir -p "$SESSION"

PHONE="$1"
if [ -n "$PHONE" ]; then
    echo "🔗 Pairing Jenna AI with Phone Number: $PHONE"
    node /data/data/com.termux/files/home/jenna-bridge/bridge.js --pair-only --session "$SESSION" --phone "$PHONE"
else
    echo "📱 Pairing Jenna AI via QR Code"
    node /data/data/com.termux/files/home/jenna-bridge/bridge.js --pair-only --session "$SESSION"
fi
