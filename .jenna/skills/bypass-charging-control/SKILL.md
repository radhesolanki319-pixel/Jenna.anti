---
name: bypass-charging-control
description: Governance and verification of Vivo/iQOO direct hardware Bypass Charging.
version: 1.0.0
tags: ["hardware", "charging", "vivo", "battery"]
created_at: 2026-09-16T19:46:15.249000+00:00
author: Jenna AI (Hermes Engine)
---

# Bypass Charging Control

Governance and verification of Vivo/iQOO direct hardware Bypass Charging on iQOO Neo 10 (Snapdragon 8 Gen 4 / `sun` architecture, OriginOS / FuntouchOS 15).

## Hardware & Kernel Architecture
- **Target Flag:** `persist.vivo.game_bypass_charge_flag` (1 = Active, 0 = Inactive)
- **Kernel Node:** `/sys/class/cms_class/game_bypass_charge_flag` (managed by `init.rc`)
- **System Controller:** `com.vivo.gamecube` (Ultra Game Mode / Game Assistant)
- **Charger Requirement:** Official 120W FlashCharge AC adapter connected (`adapter power: 120`)

## Instant Control via Script
Run the automated toggle script from Termux:
```bash
bash /storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/scripts/toggle_bypass_charging.sh on
bash /storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/scripts/toggle_bypass_charging.sh off
```

## Verification
1. Verify property state:
   ```bash
   adb -s emulator-5554 shell getprop persist.vivo.game_bypass_charge_flag
   ```
2. Verify battery telemetry:
   ```bash
   adb -s emulator-5554 shell dumpsys battery
   termux-battery-status
   ```
   When active, the battery icon displays a yellow bypass bolt, and charging current drops to 0 mA / trickle float as the motherboard draws power directly from the 120W adapter.

