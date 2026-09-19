#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Jenna AI — WhatsApp Cloud Session Exporter
# Generates base64 string of authenticated session for 1-click cloud restore
# ==============================================================================

WORKSPACE="/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna"
SESSION_DIR="$WORKSPACE/whatsapp/session"
OUTPUT_FILE="$WORKSPACE/whatsapp_cloud_session.b64"

if [ ! -d "$SESSION_DIR" ]; then
    echo "❌ Error: Session directory not found at $SESSION_DIR"
    exit 1
fi

echo "📦 Compressing WhatsApp authenticated session..."
tar -czf - -C "$WORKSPACE/whatsapp" session | base64 -w 0 > "$OUTPUT_FILE"

FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
echo "✅ Session exported successfully!"
echo "📁 Saved to: $OUTPUT_FILE ($FILE_SIZE bytes)"
echo ""
echo "📋 To use on Render / Koyeb / Hugging Face:"
echo "1. Open your Cloud Dashboard -> Environment Variables"
echo "2. Add Key:   WHATSAPP_SESSION_B64"
echo "3. Add Value: (Copy the contents of $OUTPUT_FILE)"
echo ""
echo "Your cloud container will automatically auto-restore WhatsApp without scanning any QR code!"
