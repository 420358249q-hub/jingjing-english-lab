# -*- coding: utf-8 -*-
"""
Download curated, high-definition, lightweight Unsplash images for Jingjing English Lab.
Organized into:
1. static/images/courses/ (Course covers for all 42 courses)
2. static/images/scenes/ (Thematic scenario illustrations for Drill Workshop)
"""
import os
import urllib.request
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSES_DIR = os.path.join(BASE_DIR, "static", "images", "courses")
SCENES_DIR = os.path.join(BASE_DIR, "static", "images", "scenes")

os.makedirs(COURSES_DIR, exist_ok=True)
os.makedirs(SCENES_DIR, exist_ok=True)

# Curated image pool from Unsplash (w=600, q=80, ~25KB each, fast & crystal clear)
COURSE_IMAGE_URLS = {
    "oral_900": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600&auto=format&fit=crop&q=80", # morning coffee
    "oral_8000_home": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=600&auto=format&fit=crop&q=80", # cozy living room
    "oral_8000_social": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600&auto=format&fit=crop&q=80", # friends cafe
    "oral_8000_dining": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=80", # restaurant
    "oral_8000_travel": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=600&auto=format&fit=crop&q=80", # airplane runway
    "oral_8000_shopping": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&auto=format&fit=crop&q=80", # shopping street
    "oral_8000_emotion": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600&auto=format&fit=crop&q=80", # expressive lights
    "oral_8000_health": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=600&auto=format&fit=crop&q=80", # health tea herbal
    "oral_8000_romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=600&auto=format&fit=crop&q=80", # sunset romance
    "oral_8000_workplace": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=600&auto=format&fit=crop&q=80", # modern workplace
    "nce_vol1": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=600&auto=format&fit=crop&q=80", # British library books
    "nce_vol2": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=600&auto=format&fit=crop&q=80", # vintage London fountain pen
    "nce_vol3": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=600&auto=format&fit=crop&q=80", # university students
    "nce_vol4": "https://images.unsplash.com/photo-1507842229452-7729f2730d0d?w=600&auto=format&fit=crop&q=80", # classic library interior
    "senior_high_core": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=600&auto=format&fit=crop&q=80", # study desk lamp
    "senior_high_syntax": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&auto=format&fit=crop&q=80", # high school students
    "junior_high_found": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&auto=format&fit=crop&q=80", # colorful books classroom
    "junior_high_cloze": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=600&auto=format&fit=crop&q=80", # open book reading
    "primary_grade3": "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=600&auto=format&fit=crop&q=80", # colorful pencils
    "primary_grade4": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&auto=format&fit=crop&q=80", # kids classroom
    "primary_grade5": "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=600&auto=format&fit=crop&q=80", # school library
    "primary_grade6": "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=600&auto=format&fit=crop&q=80", # graduation young
    "pattern_600_up": "https://images.unsplash.com/photo-1456324504439-367cee3b3c32?w=600&auto=format&fit=crop&q=80", # mind map desk
    "pattern_450_up": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=600&auto=format&fit=crop&q=80", # school apple blocks
    "pattern_300_up": "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=600&auto=format&fit=crop&q=80", # child smiling drawing
    "pattern_200_up": "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=600&auto=format&fit=crop&q=80", # alphabet toys
    "biz_letters": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600&auto=format&fit=crop&q=80", # typing on laptop business
    "biz_telecom": "https://images.unsplash.com/photo-1588196749597-9ff075ee6b5b?w=600&auto=format&fit=crop&q=80", # zoom conference video
    "biz_negotiation": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=600&auto=format&fit=crop&q=80", # handshake business
    "ielts_master": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=600&auto=format&fit=crop&q=80", # London Big Ben
    "cet46_patterns": "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=600&auto=format&fit=crop&q=80", # college library
    "toefl_speaking": "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=600&auto=format&fit=crop&q=80", # New York Manhattan
    "kaoyan_syntax": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=600&auto=format&fit=crop&q=80", # night study books
    "movie_classics": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=600&auto=format&fit=crop&q=80", # vintage cinema projector
    "tv_slang_hot": "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=600&auto=format&fit=crop&q=80", # retro television neon
    "pop_music_lyrics": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop&q=80", # vinyl record guitar
    "china_heritage": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&auto=format&fit=crop&q=80", # Great Wall mountain
    "china_gourmet": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=600&auto=format&fit=crop&q=80", # dim sum tea food
    "china_landmarks": "https://images.unsplash.com/photo-1547981609-4b6bfe67ca0b?w=600&auto=format&fit=crop&q=80", # China pavilion sunset
    "it_tech_pro": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&auto=format&fit=crop&q=80", # code dual screen
    "aviation_hospitality": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&auto=format&fit=crop&q=80", # luxury hotel lobby
    "finance_investing": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&auto=format&fit=crop&q=80", # candlestick financial chart
    "ted_talks_master": "https://images.unsplash.com/photo-1475721027785-f74eccf877e2?w=600&auto=format&fit=crop&q=80", # TED stage red circle spotlight
    "classic_prose": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&auto=format&fit=crop&q=80", # book in golden sunshine
    "idioms_wisdom": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=600&auto=format&fit=crop&q=80" # vintage typewriter
}

SCENE_IMAGE_URLS = {
    # 电影名篇专属
    "scene_shawshank": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop&q=80", # stormy starry rain freedom
    "scene_forrest": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=800&auto=format&fit=crop&q=80", # park bench under tree
    "scene_titanic": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop&q=80", # vast ocean sunset
    "scene_godfather": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=800&auto=format&fit=crop&q=80", # dark noir luxury city
    "scene_cinema": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80", # vintage movie theater
    
    # 美剧与流行
    "scene_tv": "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=800&auto=format&fit=crop&q=80", # retro TV & neon
    "scene_friends": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&auto=format&fit=crop&q=80", # cozy coffee shop couch
    "scene_music": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop&q=80", # acoustic guitar / music notes
    
    # 演讲与文学
    "scene_ted": "https://images.unsplash.com/photo-1475721027785-f74eccf877e2?w=800&auto=format&fit=crop&q=80", # TED stage spotlight
    "scene_literature": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&auto=format&fit=crop&q=80", # open book in sun
    "scene_pride": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=800&auto=format&fit=crop&q=80", # misty countryside estate
    "scene_prince": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800&auto=format&fit=crop&q=80", # starry sky night galaxy
    
    # 日常与生活
    "scene_daily": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80", # cozy room morning
    "scene_dining": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&auto=format&fit=crop&q=80", # restaurant dining
    "scene_travel": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800&auto=format&fit=crop&q=80", # airport runway
    "scene_shopping": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800&auto=format&fit=crop&q=80", # shopping fashion
    "scene_health": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&auto=format&fit=crop&q=80", # health tea
    "scene_romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80", # romantic sunset
    
    # 商务与行业
    "scene_business": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=800&auto=format&fit=crop&q=80", # office laptop
    "scene_tech": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&auto=format&fit=crop&q=80", # code screens
    "scene_aviation": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&auto=format&fit=crop&q=80", # hotel & flying
    "scene_finance": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop&q=80", # stock chart
    
    # 备考与校园
    "scene_campus": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=800&auto=format&fit=crop&q=80", # college students
    "scene_library": "https://images.unsplash.com/photo-1507842229452-7729f2730d0d?w=800&auto=format&fit=crop&q=80", # library bookshelf
    "scene_exam": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800&auto=format&fit=crop&q=80", # desk study
    "scene_kids": "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=800&auto=format&fit=crop&q=80", # pencils & crayons
    
    # 文化与通用
    "scene_china": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800&auto=format&fit=crop&q=80", # Great Wall
    "scene_general": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&auto=format&fit=crop&q=80" # morning sunshine
}

def download_file(url, target_path):
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            with open(target_path, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def main():
    print(f"Downloading {len(COURSE_IMAGE_URLS)} course covers...")
    success_c = 0
    for cid, url in COURSE_IMAGE_URLS.items():
        dest = os.path.join(COURSES_DIR, f"{cid}.jpg")
        if download_file(url, dest):
            success_c += 1
            print(f"  [Course] {cid} -> {os.path.basename(dest)} ({os.path.getsize(dest)} bytes)")
        time.sleep(0.05)

    print(f"\nDownloading {len(SCENE_IMAGE_URLS)} workshop scene illustrations...")
    success_s = 0
    for sid, url in SCENE_IMAGE_URLS.items():
        dest = os.path.join(SCENES_DIR, f"{sid}.jpg")
        if download_file(url, dest):
            success_s += 1
            print(f"  [Scene] {sid} -> {os.path.basename(dest)} ({os.path.getsize(dest)} bytes)")
        time.sleep(0.05)

    print(f"\nAsset sync completed! Courses: {success_c}/{len(COURSE_IMAGE_URLS)}, Scenes: {success_s}/{len(SCENE_IMAGE_URLS)}")

    # Update app/courses_database.json with local cover_image paths
    db_path = os.path.join(BASE_DIR, "app", "courses_database.json")
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            courses = json.load(f)
        for c in courses:
            cid = c["id"]
            local_cover = f"/static/images/courses/{cid}.jpg"
            cdn_url = COURSE_IMAGE_URLS.get(cid, "")
            c["cover_image"] = local_cover
            c["cdn_cover_image"] = cdn_url
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print("Updated app/courses_database.json with cover_image attributes!")

if __name__ == "__main__":
    main()
