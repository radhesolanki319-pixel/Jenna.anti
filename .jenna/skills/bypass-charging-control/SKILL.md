---
name: bypass-charging-control
description: Governance and verification of Vivo/iQOO direct hardware Bypass Charging.
version: 1.0.0
tags: ["hardware", "charging", "vivo", "battery"]
created_at: 2026-09-16T19:46:15.249000+00:00
author: Jenna AI (Hermes Engine)
---

# Bypass Charging Control

To manage and check Bypass Charging on iQOO Neo 9 Pro (Snapdragon 8 Gen 2):
1. Check current charge level and charging current: `dumpsys battery`
2. Verify thermal temperature (maintain under 38.5°C for optimal gaming)
3. Check battery saver state: `cmd battery set low_power 0`
4. Guide the user to activate Monster Mode / Game Space sidebar for full hardware bypass lock.
