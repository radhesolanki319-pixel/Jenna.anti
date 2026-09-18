import os
import re
import urllib.parse
import requests

OUTPUT_DIR = "/storage/emulated/0/Download/TermuxWorkspace/projects/UPLOAD/UI_INSPIRATIONS"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

QUERIES = [
    ("ai_companion_mobile_app_ui_dribbble", "AI companion mobile app UI design dribbble"),
    ("futuristic_ai_assistant_dark_glassmorphism", "futuristic AI assistant app UI dark mode glassmorphism dribbble"),
    ("cyberpunk_mobile_app_interface", "cyberpunk mobile app UI design dribbble behance"),
    ("voice_ai_assistant_mobile_waveform", "voice AI assistant mobile UI waveform dribbble"),
    ("ai_chat_companion_mobile_screen", "AI chat companion mobile screen UI behance"),
    ("anime_ai_virtual_companion_mobile_ui", "virtual AI companion mobile app UI dribbble"),
    ("hud_ai_assistant_mobile_interface", "futuristic sci fi HUD mobile app UI design dribbble"),
]

def search_images(query, max_results=5):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/images/search?q={encoded}&form=HDRSC2"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        murls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', r.text)
        if not murls:
            murls = re.findall(r'\"murl\":\"(http[^\"]+)\"', r.text)
        
        valid = []
        for u in murls:
            # Clean up url
            u_clean = u.replace("\\/", "/")
            if any(u_clean.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                valid.append(u_clean)
            elif "jpg" in u_clean.lower() or "png" in u_clean.lower():
                valid.append(u_clean)
            if len(valid) >= max_results:
                break
        return valid
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return []

def download_image(url, filepath):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, stream=True)
        if r.status_code == 200 and len(r.content) > 15000: # at least 15KB
            with open(filepath, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        pass
    return False

def main():
    print(f"[*] Searching and collecting UI inspirations into {OUTPUT_DIR}...")
    downloaded_files = []
    
    count = 1
    for category_slug, query in QUERIES:
        print(f"[>] Searching: '{query}'")
        img_urls = search_images(query, max_results=6)
        cat_saved = 0
        for u in img_urls:
            ext = ".png" if ".png" in u.lower() else ".jpg"
            filename = f"ui_inspo_{count:02d}_{category_slug}{ext}"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if download_image(u, filepath):
                size_kb = os.path.getsize(filepath) // 1024
                print(f"    [+] Saved ({size_kb} KB): {filename}")
                downloaded_files.append((filename, query, u, size_kb))
                count += 1
                cat_saved += 1
                if cat_saved >= 3:
                    break

    print(f"\n[✓] Finished! Total UI inspiration images downloaded: {len(downloaded_files)}")

    # Write Catalog Markdown
    catalog_path = os.path.join(OUTPUT_DIR, "UI_COLLECTION_CATALOG.md")
    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write("# 🎨 Curated Web UI Inspirations for Jenna AI Companion\n\n")
        f.write("Real-world, top-tier mobile UI designs collected from Dribbble, Behance, and design repositories.\n\n")
        f.write("| Preview | File Name | Design Style & Query | Size |\n")
        f.write("|---|---|---|---|\n")
        for fn, q, u, sz in downloaded_files:
            f.write(f"| ![{fn}]({fn}) | `{fn}` | {q} | {sz} KB |\n")
    print(f"[✓] Created Catalog: {catalog_path}")

if __name__ == "__main__":
    main()
