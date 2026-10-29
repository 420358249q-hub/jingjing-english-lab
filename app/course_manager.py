# -*- coding: utf-8 -*-
"""
Course Manager for Jingjing English Lab
Loads courses database, serves courses, chapters, and drill data.
"""
import os
import json
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSES_DB_PATH = os.path.join(BASE_DIR, "app", "courses_database.json")

_courses_cache: Optional[List[Dict[str, Any]]] = None
_courses_mtime: float = 0.0
_courses_summary_cache: Optional[List[Dict[str, Any]]] = None
_course_detail_cache: Dict[str, Dict[str, Any]] = {}
_chapter_drills_cache: Dict[str, Dict[str, Any]] = {}

def load_courses() -> List[Dict[str, Any]]:
    global _courses_cache, _courses_mtime, _courses_summary_cache, _course_detail_cache, _chapter_drills_cache
    if not os.path.exists(COURSES_DB_PATH):
        return []
    
    current_mtime = os.path.getmtime(COURSES_DB_PATH)
    if _courses_cache is not None and current_mtime == _courses_mtime:
        return _courses_cache
    
    try:
        with open(COURSES_DB_PATH, "r", encoding="utf-8") as f:
            raw_courses = json.load(f)
            _courses_cache = raw_courses
            _courses_mtime = current_mtime

            # Pre-compute and index in memory for O(1) 0ms retrieval
            summary = []
            detail_map = {}
            chapter_map = {}

            for c in raw_courses:
                cid = c["id"]
                summary.append({
                    "id": cid,
                    "title": c["title"],
                    "english_title": c["english_title"],
                    "category": c["category"],
                    "category_name": c["category_name"],
                    "categories": c.get("categories", [c.get("category", "日常实用")]),
                    "tag": c.get("tag", "精选推荐"),
                    "tag_style": c.get("tag_style", "mint"),
                    "view_count": c.get("view_count", 8000),
                    "chapter_count": len(c.get("chapters", [])),
                    "sentence_count": c.get("sentence_count", 0),
                    "cover_gradient": c.get("cover_gradient", "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)"),
                    "cover_image": c.get("cover_image", f"/static/images/courses/{cid}.jpg"),
                    "cdn_cover_image": c.get("cdn_cover_image", ""),
                    "icon": c.get("icon", "chat-circle-text"),
                    "description": c.get("description", "")
                })

                chapters_summary = []
                for ch in c.get("chapters", []):
                    chid = ch["id"]
                    chapters_summary.append({
                        "id": chid,
                        "title": ch["title"],
                        "chapter_num": ch["chapter_num"],
                        "drill_count": ch.get("drill_count", len(ch.get("drills", []))),
                        "status": ch.get("status", "unstarted"),
                        "duration_seconds": ch.get("duration_seconds", 0),
                        "completed_count": ch.get("completed_count", 0)
                    })
                    chapter_map[f"{cid}:{chid}"] = {
                        "course_id": cid,
                        "course_title": c["title"],
                        "chapter_id": chid,
                        "chapter_title": ch["title"],
                        "chapter_num": ch["chapter_num"],
                        "drill_count": len(ch.get("drills", [])),
                        "drills": ch.get("drills", [])
                    }

                detail_map[cid] = {
                    "id": cid,
                    "title": c["title"],
                    "english_title": c["english_title"],
                    "category": c["category"],
                    "category_name": c["category_name"],
                    "tag": c.get("tag", "精选推荐"),
                    "view_count": c.get("view_count", 8000),
                    "chapter_count": len(c.get("chapters", [])),
                    "sentence_count": c.get("sentence_count", 0),
                    "cover_gradient": c.get("cover_gradient", ""),
                    "cover_image": c.get("cover_image", f"/static/images/courses/{cid}.jpg"),
                    "cdn_cover_image": c.get("cdn_cover_image", ""),
                    "icon": c.get("icon", "chat-circle-text"),
                    "description": c.get("description", ""),
                    "chapters": chapters_summary
                }

            _courses_summary_cache = summary
            _course_detail_cache = detail_map
            _chapter_drills_cache = chapter_map
            return _courses_cache
    except Exception as e:
        print(f"[CourseManager Error] Failed to load courses: {e}")
        return _courses_cache or []

def get_courses_summary() -> List[Dict[str, Any]]:
    load_courses()
    return _courses_summary_cache or []

def get_course_detail(course_id: str) -> Optional[Dict[str, Any]]:
    load_courses()
    return _course_detail_cache.get(course_id)

def get_chapter_drills(course_id: str, chapter_id: str) -> Optional[Dict[str, Any]]:
    load_courses()
    return _chapter_drills_cache.get(f"{course_id}:{chapter_id}")
