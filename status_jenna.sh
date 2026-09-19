#!/data/data/com.termux/files/usr/bin/bash
# Jenna AI — Status Checker Script for Termux / Linux

echo "=================================================="
echo "  📊 Jenna AI Platform Status                     "
echo "=================================================="

# PostgreSQL
if pg_isready -h 127.0.0.1 -p 5432 -q >/dev/null 2>&1; then
    echo "  🐘 PostgreSQL:   🟢 RUNNING (Port 5432)"
else
    echo "  🐘 PostgreSQL:   🔴 STOPPED"
fi

# Redis
if redis-cli ping >/dev/null 2>&1; then
    echo "  ⚡ Redis:        🟢 RUNNING (Port 6379, PONG)"
else
    echo "  ⚡ Redis:        🔴 STOPPED"
fi

# Backend
if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "  🚀 Backend API:  🟢 RUNNING (http://localhost:8000)"
else
    echo "  🚀 Backend API:  🔴 STOPPED"
fi

# Frontend Web
if curl -s -I http://127.0.0.1:3001 >/dev/null 2>&1; then
    echo "  🌐 Frontend Web: 🟢 RUNNING (http://localhost:3001)"
else
    echo "  🌐 Frontend Web: ⚪ IDLE (Ready on Port 3001)"
fi

# WhatsApp Bridge
if curl -s http://127.0.0.1:3000/health >/dev/null 2>&1; then
    echo "  📱 WA Bridge:    🟢 CONNECTED (Port 3000)"
else
    echo "  📱 WA Bridge:    🔴 STOPPED"
fi

# WhatsApp Daemon
if pgrep -f "run_whatsapp_jenna_daemon.py" >/dev/null 2>&1; then
    echo "  💬 WA Daemon:    🟢 ACTIVE (Autonomous Antigravity Agent)"
else
    echo "  💬 WA Daemon:    🔴 STOPPED"
fi

# Proactive Sentinel
if pgrep -f "run_proactive_companion.py" >/dev/null 2>&1; then
    echo "  🛡️ Proactive:    🟢 ACTIVE (Thermal, Battery & State Sentinel)"
else
    echo "  🛡️ Proactive:    🔴 STOPPED"
fi

# Zero-Amnesia Disk Memory
CONV_COUNT=$(ls -1 /storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/data/conversations/*.json 2>/dev/null | wc -l)
echo "  🧠 Zero-Amnesia: 🟢 ACTIVE ($CONV_COUNT User Logs Persisted on Disk)"

# Touch-Adaptive 144Hz / 60Hz Governor
if pgrep -f "touch_adaptive_refresh_daemon.py" >/dev/null 2>&1; then
    echo "  ⚡ 144Hz Touch:  🟢 ACTIVE (Touch: 144Hz | Idle: 60Hz)"
else
    echo "  ⚡ 144Hz Touch:  🔴 STOPPED"
fi

# Live Vision Daemon
if pgrep -f "run_live_vision_daemon.py" >/dev/null 2>&1; then
    echo "  👁️ Live Vision:  🟢 ACTIVE (Continuous Screen Watcher)"
else
    echo "  👁️ Live Vision:  🔴 STOPPED"
fi

# Dexter Screen Pet
if pgrep -f "dexter_screen_pet.py" >/dev/null 2>&1; then
    echo "  🐾 Dexter Pet:   🟢 LIVING ON SCREEN (Transparent Overlay)"
else
    echo "  🐾 Dexter Pet:   🔴 STOPPED"
fi

echo "=================================================="
