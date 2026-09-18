---
name: youtube-media-pipeline
description: Autonomous YouTube/Instagram audio and video downloader via yt-dlp with auto-delivery to user phone storage and WhatsApp.
version: 1.0.0
tags: ["youtube", "media", "download", "yt-dlp", "whatsapp"]
created_at: 2026-09-18T07:27:42.747445+00:00
author: Jenna AI
---

# youtube-media-pipeline

# YouTube & Media Download Skill
1. Use yt-dlp to download audio or video directly to /storage/emulated/0/Download/
   Command: yt-dlp -f 'ba' -x --audio-format mp3 -o '/storage/emulated/0/Download/%(title)s.%(ext)s' '<URL>'
   Or video: yt-dlp -f 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]' -o '/storage/emulated/0/Download/%(title)s.%(ext)s' '<URL>'
2. Once downloaded, notify the user or send media directly to WhatsApp via POST http://127.0.0.1:3000/send-media.
3. Clean up any partial or temporary files.

