---
name: system-diagnostics
description: Comprehensive Android and Termux thermal, battery, memory, and process diagnostics.
version: 1.0.0
tags: ["android", "termux", "hardware", "diagnostics"]
created_at: 2026-09-16T19:46:15.245349+00:00
author: Jenna AI (Hermes Engine)
---

# System Diagnostics

To diagnose the device:
1. Check battery capacity, temp, and status: `termux-battery-status` or `dumpsys battery`
2. Check CPU frequency and thermal throttling in `/sys/class/thermal/`
3. Check memory pressure using `free -h` and `vmstat`
4. Check active Termux and background daemons using `ps aux | grep python`
Synthesize findings and present warm, actionable advice to the user.
