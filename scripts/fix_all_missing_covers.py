# -*- coding: utf-8 -*-
import os
import shutil
import urllib.request
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSES_DIR = os.path.join(BASE_DIR, "static", "images", "courses")
DB_PATH = os.path.join(BASE_DIR, "app", "courses_database.json")

# 1. Map existing mismatched files
RENAME_MAP = {
    "nce_vol1.jpg": "nce_book1.jpg",
    "nce_vol2.jpg": "nce_book2.jpg",
    "nce_vol3.jpg": "nce_book3.jpg",
    "nce_vol4.jpg": "nce_book4.jpg",
    "oral_8000_home.jpg": "oral8000_home.jpg",
    "oral_8000_social.jpg": "oral8000_social.jpg",
    "oral_8000_dining.jpg": "oral8000_dining.jpg",
    "oral_8000_travel.jpg": "oral8000_traffic.jpg",
    "oral_8000_shopping.jpg": "oral8000_shopping.jpg",
    "oral_8000_emotion.jpg": "oral8000_emotions.jpg",
    "oral_8000_health.jpg": "oral8000_medical.jpg",
    "oral_8000_romance.jpg": "oral8000_romance.jpg",
    "oral_8000_workplace.jpg": "biz_workplace.jpg"
}

for src_name, dst_name in RENAME_MAP.items():
    src_path = os.path.join(COURSES_DIR, src_name)
    dst_path = os.path.join(COURSES_DIR, dst_name)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f"Copied {src_name} -> {dst_name}")

# 2. Download missing specific images
NEW_DOWNLOADS = {
    "spoken_1000.jpg": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&auto=format&fit=crop&q=80", # young people talking
    "pattern_720_up.jpg": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&auto=format&fit=crop&q=80", # kids study classroom
    "pattern_720_down.jpg": "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=600&auto=format&fit=crop&q=80", # library learning
    "pattern_600_down.jpg": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=600&auto=format&fit=crop&q=80", # desk learning apple
    "pattern_450_down.jpg": "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=600&auto=format&fit=crop&q=80", # child smiling drawing
    "pattern_300_down.jpg": "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=600&auto=format&fit=crop&q=80"  # colorful blocks
}

for filename, url in NEW_DOWNLOADS.items():
    target = os.path.join(COURSES_DIR, filename)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            with open(target, "wb") as f:
                f.write(data)
        print(f"Downloaded {filename} ({len(data)} bytes)")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

# 3. Verify every single course in database
with open(DB_PATH, "r", encoding="utf-8") as f:
    courses = json.load(f)

for c in courses:
    cid = c["id"]
    expected_file = os.path.join(COURSES_DIR, f"{cid}.jpg")
    if not os.path.exists(expected_file) or os.path.getsize(expected_file) < 500:
        print(f"[Warning] Course {cid} still missing cover! Fallback copying...")
        shutil.copy2(os.path.join(COURSES_DIR, "oral_900.jpg"), expected_file)
    c["cover_image"] = f"/static/images/courses/{cid}.jpg"

with open(DB_PATH, "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)

print("Updated app/courses_database.json!")
