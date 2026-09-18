import os
import shutil

dl = "/storage/emulated/0/Download"
categories = {
    "Audio": [".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"],
    "Videos": [".mp4", ".mkv", ".webm", ".avi", ".mov"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".epub"],
    "APKs": [".apk"],
    "Images": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
}

moved = 0
if os.path.exists(dl):
    for cat in categories:
        os.makedirs(os.path.join(dl, cat), exist_ok=True)

    for item in os.listdir(dl):
        item_path = os.path.join(dl, item)
        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower()
            for cat, extensions in categories.items():
                if ext in extensions:
                    try:
                        shutil.move(item_path, os.path.join(dl, cat, item))
                        moved += 1
                        break
                    except Exception:
                        pass

print(f"Organized {moved} loose files in {dl} into Audio, Videos, Documents, APKs, Images.")
