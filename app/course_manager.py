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

def load_courses() -> List[Dict[str, Any]]:
    global _courses_cache, _courses_mtime
    if not os.path.exists(COURSES_DB_PATH):
        return []
    
    current_mtime = os.path.getmtime(COURSES_DB_PATH)
    if _courses_cache is not None and current_mtime == _courses_mtime:
        return _courses_cache
    
    try:
        with open(COURSES_DB_PATH, "r", encoding="utf-8") as f:
            _courses_cache = json.load(f)
            _courses_mtime = current_mtime
            return _courses_cache
    except Exception as e:
        print(f"[CourseManager Error] Failed to load courses: {e}")
        return _courses_cache or []

def get_courses_summary() -> List[Dict[str, Any]]:
    all_courses = load_courses()
    summary = []
    for c in all_courses:
        summary.append({
            "id": c["id"],
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
            "icon": c.get("icon", "chat-circle-text"),
            "description": c.get("description", "")
        })
    return summary

def get_course_detail(course_id: str) -> Optional[Dict[str, Any]]:
    all_courses = load_courses()
    for c in all_courses:
        if c["id"] == course_id:
            # Return course with chapter summaries (omit heavy nested drill array for fast response)
            chapters_summary = []
            for ch in c.get("chapters", []):
                chapters_summary.append({
                    "id": ch["id"],
                    "title": ch["title"],
                    "chapter_num": ch["chapter_num"],
                    "drill_count": ch.get("drill_count", len(ch.get("drills", []))),
                    "status": ch.get("status", "unstarted"),
                    "duration_seconds": ch.get("duration_seconds", 0),
                    "completed_count": ch.get("completed_count", 0)
                })
            return {
                "id": c["id"],
                "title": c["title"],
                "english_title": c["english_title"],
                "category": c["category"],
                "category_name": c["category_name"],
                "tag": c.get("tag", "精选推荐"),
                "view_count": c.get("view_count", 8000),
                "chapter_count": len(c.get("chapters", [])),
                "sentence_count": c.get("sentence_count", 0),
                "cover_gradient": c.get("cover_gradient", ""),
                "icon": c.get("icon", "chat-circle-text"),
                "description": c.get("description", ""),
                "chapters": chapters_summary
            }
    return None

def get_chapter_drills(course_id: str, chapter_id: str) -> Optional[Dict[str, Any]]:
    all_courses = load_courses()
    for c in all_courses:
        if c["id"] == course_id:
            for ch in c.get("chapters", []):
                if ch["id"] == chapter_id:
                    return {
                        "course_id": c["id"],
                        "course_title": c["title"],
                        "chapter_id": ch["id"],
                        "chapter_title": ch["title"],
                        "chapter_num": ch["chapter_num"],
                        "drill_count": len(ch.get("drills", [])),
                        "drills": ch.get("drills", [])
                    }
    return None
