# -*- coding: utf-8 -*-
"""
静静学习系统 - 成人高阶英语自习题库 (Jingjing English Lab)
Adult-Oriented English Drill Bank & Conversation Scenarios.

Coverage:
1. 日常社交 (Daily Social)       —— 咖啡餐饮 / 周末闲聊 / 购物生活
2. 职场沟通 (Workplace)          —— 会议 / 邮件 / 敏捷协作
3. 出行出境 (Travel & Customs)   —— 机场值机 / 海关 / 酒店 / 问路
4. 语法攻坚 (Grammar)            —— 从句 / 时态 / 语态 / 高阶替换
5. 自定义精选 (Custom)           —— 由用户粘贴课文动态生成

All copy is strictly adult-oriented: no childish labels, no infantile terms.
"""

import os
import json
import re

# ---------------------------------------------------------------------------
# 口语对练场景 (Adult Conversation Scenarios)
# 前端依据 id 匹配场景卡片；结构保持不变（id/title/subtitle/icon/badge/
# partner_name/partner_avatar/prompt_context/initial_message）。
# ---------------------------------------------------------------------------
SCENARIOS = [
    {
        "id": "office",
        "title": "职场会议",
        "subtitle": "Workplace Meeting & Standup",
        "icon": "briefcase",
        "badge": "职场沟通",
        "partner_name": "James · 资深项目经理",
        "partner_avatar": "J",
        "prompt_context": "You are James, a thoughtful senior project manager at an international company. You and 静静 (Jingjing) are doing a quick sync on deliverables, timelines and collaborative ideas. Be professional yet warm, encouraging and solution-oriented. Keep replies to 1-2 conversational sentences and end with a natural follow-up question.",
        "initial_message": "Morning 静静, thanks for hopping on this quick sync. What's the top priority on your plate today?",
    },
    {
        "id": "cafe",
        "title": "咖啡馆点餐",
        "subtitle": "At the Coffee Shop",
        "icon": "coffee",
        "badge": "日常社交",
        "partner_name": "Emma · 咖啡师",
        "partner_avatar": "E",
        "prompt_context": "You are Emma, a warm and efficient barista at Brew & Co. The user is 静静 (Jingjing), an adult practicing natural conversational English. Help her order coffee and pastries, ask about cup size, milk choice (oat / almond / whole), iced or hot, and sweetness. Keep it sunny and welcoming, 1-2 sentences with a follow-up question.",
        "initial_message": "Hey 静静, welcome in! What can I get started for you today?",
    },
    {
        "id": "travel",
        "title": "机场与海关",
        "subtitle": "Airport & Customs",
        "icon": "airplane",
        "badge": "出行出境",
        "partner_name": "Alex · 地勤与海关",
        "partner_avatar": "A",
        "prompt_context": "You are Alex, a polite airport ground-staff and customs officer assisting 静静 (Jingjing) with check-in, boarding passes, window or aisle seats, baggage drop and immigration questions. Speak clearly, professionally and warmly in standard international English, 1-2 sentences with a natural question.",
        "initial_message": "Good day! May I see your passport and boarding pass, please?",
    },
    {
        "id": "smalltalk",
        "title": "周末闲聊",
        "subtitle": "Weekend Small Talk",
        "icon": "chat-circle-dots",
        "badge": "日常社交",
        "partner_name": "Sarah · 好友",
        "partner_avatar": "S",
        "prompt_context": "You are Sarah, a warm, caring and funny close friend chatting with 静静 (Jingjing). Talk about weekend plans, shows, food, shopping finds and work-life balance. Use authentic conversational fillers (Totally!, No way!, I know right?). Keep it 1-2 sentences with a light follow-up question.",
        "initial_message": "Hey 静静, great to see you! How's your weekend been so far?",
    },
    {
        "id": "freetalk",
        "title": "专属导师 Ava",
        "subtitle": "Dedicated Tutor",
        "icon": "sparkle",
        "badge": "私教研习",
        "partner_name": "Ava · 首席专属私教",
        "partner_avatar": "A",
        "prompt_context": "You are Ava, 静静 (Jingjing)'s dedicated senior English mentor. Discuss any topic she likes: learning strategy, films, music, travel, career and everyday reflections. Be insightful, elegant and warm; gently correct any awkward phrasing and offer natural native alternatives. Keep replies concise (1-2 sentences) and end with an inviting question.",
        "initial_message": "Hi 静静, I'm Ava, your dedicated English mentor. What's on your mind today?",
    },
]

# ---------------------------------------------------------------------------
# 题库加载 + 成人化标签映射
# 保留 drills_database.json 原始数据不动，仅在加载时把旧的 K12 分类/标签
# 统一映射为成年人五大类，并清洗 breakdown / cultural_tip 中的儿童化措辞。
# ---------------------------------------------------------------------------
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drills_database.json")

# 旧分类 -> 新分类
_CATEGORY_MAP = {
    "primary": "grammar",
    "junior": "grammar",
    "senior": "grammar",
    "cet": "grammar",
    "ielts": "grammar",
    "cafe": "daily",
    "smalltalk": "daily",
    "shopping": "daily",
    "office": "workplace",
    "travel": "travel",
    "custom": "custom",
}

# 新分类 -> 中文名
_CATEGORY_NAMES = {
    "grammar": "语法攻坚",
    "daily": "日常社交",
    "workplace": "职场沟通",
    "travel": "出行出境",
    "custom": "自定义精选",
}

# level_tag 前缀清洗（按顺序匹配，命中即替换前缀）
_LEVEL_TAG_FIXES = [
    (re.compile(r'^小学\s*PEP\s*·\s*'), '基础语法 · '),
    (re.compile(r'^小学[一二三四五六]年级\s*·\s*'), '基础语法 · '),
    (re.compile(r'^中考(拔高考点|核心考点|核心)\s*·\s*'), '核心语法 · '),
    (re.compile(r'^高考进阶\s*·\s*'), '高阶语法 · '),
    (re.compile(r'^四六级必背\s*·\s*'), '学术语法 · '),
    (re.compile(r'^雅思托福\s*·\s*'), '高阶表达 · '),
]

# 中文题干中仅需清洗“考场”类应试名词（保留句义，去 K12 标记）
_CHINESE_SCRUB = [
    ("中考考场", "考场"),
    ("高考考场", "考场"),
    ("中考", "考试"),
    ("高考", "考试"),
]

# breakdown / cultural_tip / level_tag 中的儿童化措辞清洗（长词优先）
_TEXT_SCRUB = [
    ("小学核心语法点", "基础语法要点"),
    ("小学语法分水岭", "基础语法分水岭"),
    ("小学必考", "基础高频考点"),
    ("小学核心", "基础核心"),
    ("小学", "基础"),
    ("中考核心铁律", "核心铁律"),
    ("中考易错雷区", "核心易错点"),
    ("中考经典搭配", "核心经典搭配"),
    ("中考高频句型", "核心高频句型"),
    ("中考黄金考点", "核心黄金考点"),
    ("中考拔高考点", "核心进阶考点"),
    ("中考核心考点", "核心考点"),
    ("中考必考", "核心高频考点"),
    ("中考", "核心"),
    ("高考进阶", "高阶语法"),
    ("高考", "高阶"),
    ("四六级必背", "学术语法"),
    ("四六级", "学术"),
    ("雅思托福", "高阶表达"),
    ("雅思", "高阶"),
    ("托福", "高阶"),
    ("初中", "进阶"),
]


def _scrub_text(text: str) -> str:
    if not text:
        return text
    for old, new in _TEXT_SCRUB:
        if old in text:
            text = text.replace(old, new)
    return text


def _fix_level_tag(tag: str) -> str:
    if not tag:
        return tag
    for pattern, replacement in _LEVEL_TAG_FIXES:
        if pattern.search(tag):
            return pattern.sub(replacement, tag, count=1)
    return tag


def _adultify(drill: dict) -> dict:
    """把一条原始题库映射为面向成年人的标签与措辞。"""
    result = dict(drill)
    old_cat = result.get("category", "")
    new_cat = _CATEGORY_MAP.get(old_cat, old_cat or "grammar")
    result["category"] = new_cat
    result["category_name"] = _CATEGORY_NAMES.get(new_cat, result.get("category_name", ""))
    result["level_tag"] = _scrub_text(_fix_level_tag(result.get("level_tag", "")))
    if result.get("breakdown"):
        result["breakdown"] = _scrub_text(result["breakdown"])
    if result.get("cultural_tip"):
        result["cultural_tip"] = _scrub_text(result["cultural_tip"])
    if result.get("chinese"):
        for old, new in _CHINESE_SCRUB:
            result["chinese"] = result["chinese"].replace(old, new)
    return result


def _load_drills():
    if os.path.exists(_DB_PATH):
        try:
            with open(_DB_PATH, "r", encoding="utf-8") as _f:
                raw = json.load(_f)
            if isinstance(raw, list):
                return [_adultify(d) for d in raw]
        except Exception as _e:  # noqa: BLE001
            print(f"[DataBank] Failed to load drills_database.json: {_e}")

    # 极简兜底（正常情况下不会触发，JSON 题库始终存在）
    return [
        {
            "id": "fallback_1",
            "category": "grammar",
            "category_name": "语法攻坚",
            "level_tag": "核心语法 · 定语从句",
            "chinese": "这就是昨天在会议上提出这个建议的那位同事。",
            "english": "This is the colleague who proposed the idea at yesterday's meeting.",
            "tokens": ["This is the colleague", "who proposed the idea", "at yesterday's meeting."],
            "breakdown": "This is the colleague [主干句] + who [关系代词指人] + proposed the idea [定语从句谓语与宾语] + at yesterday's meeting [时间地点状语]",
            "cultural_tip": "先行词为人且在从句中作主语时，关系代词用 who 或 that。",
        },
    ]


SENTENCE_DRILLS = _load_drills()
