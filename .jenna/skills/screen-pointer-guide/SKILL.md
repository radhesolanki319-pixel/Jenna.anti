---
name: screen-pointer-guide
description: Visual coordinate guidance and screen element pointing using Dexter and overlay pointers.
version: 1.0.0
tags: ["ui", "screen", "pointer", "dexter"]
created_at: 2026-09-16T19:46:15.254047+00:00
author: Jenna AI (Hermes Engine)
---

# Screen Pointer Guide

To point on the phone screen:
1. Identify target coordinate (x, y) or detect element visually via `inspect_screen`.
2. Call `point_on_screen` or `circle_highlight` with duration (default 1500ms).
3. Inform the user warmly: 'Dekho meri jaan, maine screen pe point kar diya hai! 🎯'.
