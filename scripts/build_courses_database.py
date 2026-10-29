# -*- coding: utf-8 -*-
"""
Build Complete Courses Database for Jingjing English Lab
Generates app/courses_database.json with 12 flagship courses, chapters,
IPA phonetics from Kokoro Tokenizer, and syntactic grammar chunk tagging.
"""
import os
import sys
import re
import json
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH_DIR = "/Users/chen/.gemini/antigravity/brain/0d6a0092-a514-44af-8786-418dce36997f/scratch"
OUTPUT_FILE = os.path.join(BASE_DIR, "app", "courses_database.json")

print("[1/5] Initializing Kokoro Tokenizer for offline IPA phonetics...")
try:
    from kokoro_onnx.tokenizer import Tokenizer
    tok = Tokenizer()
except Exception as e:
    print(f"[Warning] Kokoro tokenizer failed: {e}. Fallback enabled.")
    tok = None

def get_ipa(text: str) -> str:
    if not tok:
        return ""
    try:
        raw = tok.phonemize(text).strip()
        raw = re.sub(r'[.?!,;:"]+$', '', raw).strip()
        return f"/{raw}/" if raw else ""
    except Exception:
        return ""

PRONOUNS_SUBJ = {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those', 'there', 'who', 'what', 'which', 'someone', 'everyone', 'nobody', 'anybody'}
BE_VERBS = {'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
MODALS = {'can', 'could', 'may', 'might', 'must', 'should', 'would', 'will', 'shall', 'ought', 'do', 'does', 'did', 'have', 'has', 'had'}
PREPS = {'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by', 'about', 'under', 'over', 'into', 'after', 'before', 'through', 'between', 'during', 'without'}

def tag_syntax_chunks(en: str):
    clean = re.sub(r'[?.!,;:\'\"]+$', '', en).strip()
    words = clean.split()
    if not words:
        return []

    first_lower = words[0].lower()
    if first_lower in {'give', 'show', 'tell', 'send', 'pass', 'bring', 'lend', 'buy'} and len(words) >= 3 and words[1].lower() in {'me', 'him', 'her', 'us', 'them', 'you'}:
        v_part = f"{words[0]} {words[1]}"
        obj_part = ' '.join(words[2:])
        return [
            {'text': v_part, 'role': '谓语', 'color': 'purple', 'ipa': get_ipa(v_part)},
            {'text': obj_part, 'role': '宾语', 'color': 'blue', 'ipa': get_ipa(obj_part)}
        ]

    if first_lower == 'thank' and len(words) >= 2 and words[1].lower() == 'you':
        if len(words) > 2:
            return [
                {'text': 'Thank you', 'role': '谓宾短语', 'color': 'purple', 'ipa': get_ipa('Thank you')},
                {'text': ' '.join(words[2:]), 'role': '状语', 'color': 'emerald', 'ipa': get_ipa(' '.join(words[2:]))}
            ]
        return [{'text': 'Thank you', 'role': '常用口语', 'color': 'purple', 'ipa': get_ipa('Thank you')}]

    chunks = []
    if first_lower in MODALS or first_lower in BE_VERBS:
        if len(words) >= 2 and words[1].lower() in PRONOUNS_SUBJ:
            c_text = f"{words[0]} {words[1]}"
            chunks.append({'text': c_text, 'role': '疑问主谓', 'color': 'rose', 'ipa': get_ipa(c_text)})
            rem = words[2:]
        else:
            chunks.append({'text': words[0], 'role': '助动词', 'color': 'rose', 'ipa': get_ipa(words[0])})
            rem = words[1:]
    elif first_lower in PRONOUNS_SUBJ or words[0].lower() in {'the', 'a', 'an', 'my', 'your', 'his', 'her', 'our', 'their'}:
        if words[0].lower() in {'the', 'a', 'an', 'my', 'your', 'his', 'her', 'our', 'their'} and len(words) >= 2:
            c_text = f"{words[0]} {words[1]}"
            chunks.append({'text': c_text, 'role': '主语', 'color': 'rose', 'ipa': get_ipa(c_text)})
            rem = words[2:]
        else:
            chunks.append({'text': words[0], 'role': '主语', 'color': 'rose', 'ipa': get_ipa(words[0])})
            rem = words[1:]
    else:
        rem = words

    if rem:
        adv_idx = -1
        for i, w in enumerate(rem):
            if i > 0 and w.lower() in PREPS:
                adv_idx = i
                break

        if adv_idx != -1 and adv_idx < len(rem):
            vp_obj = rem[:adv_idx]
            adv = rem[adv_idx:]
            if len(vp_obj) >= 2 and not chunks:
                c1 = ' '.join(vp_obj[:2])
                chunks.append({'text': c1, 'role': '核心谓语', 'color': 'purple', 'ipa': get_ipa(c1)})
                if len(vp_obj) > 2:
                    c2 = ' '.join(vp_obj[2:])
                    chunks.append({'text': c2, 'role': '宾语', 'color': 'blue', 'ipa': get_ipa(c2)})
            elif vp_obj:
                c_vp = ' '.join(vp_obj)
                chunks.append({'text': c_vp, 'role': '谓宾结构', 'color': 'purple', 'ipa': get_ipa(c_vp)})
            c_adv = ' '.join(adv)
            chunks.append({'text': c_adv, 'role': '状语短语', 'color': 'emerald', 'ipa': get_ipa(c_adv)})
        else:
            if len(rem) <= 2:
                role = '表语' if chunks and chunks[0]['text'].lower() in BE_VERBS else '谓语'
                c = ' '.join(rem)
                chunks.append({'text': c, 'role': role, 'color': 'purple', 'ipa': get_ipa(c)})
            else:
                chunks.append({'text': rem[0], 'role': '谓语动词', 'color': 'purple', 'ipa': get_ipa(rem[0])})
                c_obj = ' '.join(rem[1:])
                chunks.append({'text': c_obj, 'role': '宾语/表语', 'color': 'blue', 'ipa': get_ipa(c_obj)})

    return chunks

print("[2/5] Loading open-source sentence datasets...")
# 1. 英语口语8000句
hucaixue_file = os.path.join(SCRATCH_DIR, "hucaixue_8000", "英语口语8000句-简版")
oral_pairs = []
if os.path.exists(hucaixue_file):
    with open(hucaixue_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            m = re.match(r'^([A-Za-z0-9\s,\'’\"\-?!.]+)\s*[（(]([^）)]+)[）)]\s*$', line)
            if m:
                en = m.group(1).strip()
                zh = m.group(2).strip()
                if len(en.split()) >= 2 and len(en) > 3:
                    oral_pairs.append((en, zh))
print(f"Loaded {len(oral_pairs)} pairs from 英语口语8000句")

# 2. drills_database.json
drills_file = os.path.join(BASE_DIR, "app", "drills_database.json")
db_drills = []
if os.path.exists(drills_file):
    with open(drills_file, "r", encoding="utf-8") as f:
        db_drills = json.load(f)
print(f"Loaded {len(db_drills)} sentences from drills_database.json")

# Build 15 topic buckets for 《零基础日常口语表达900句》
CH15_TOPICS = [
    ("一、问候与道别 · Greetings and Farewells", ['早晨好', '早上好', '你好', '再见', '明天见', '回见', '晚安', '见到你', '走好', '回头见', '告别', '保重', '喂', '欢迎']),
    ("二、感谢与致歉 · Thanks and Apologies", ['谢谢', '感谢', '多谢', '不客气', '对不起', '抱歉', '原谅', '不好意思', '借光', '打扰', '惭愧']),
    ("三、请求与指令 · Requests and Imperatives", ['帮我', '帮忙', '请', '快点', '关掉', '打开', '给我', '听着', '拿来', '注意', '递给', '锁门', '坐下', '站起来', '别动']),
    ("四、同意与反对 · Agreement and Disagreement", ['好的', '当然', '同意', '行', '对', '赞成', '没问题', '反对', '不行', '不同意', '不是', '不对', '无法', '拒绝', '错']),
    ("五、疑问与咨询 · Questions and Inquiries", ['吗', '呢', '什么', '谁', '哪', '几点', '多少', '怎么', '为什么', '何', '如何', '真吗', '哪里', '是吧']),
    ("六、感受与情绪 · Feelings and Emotions", ['累', '困', '困倦', '高兴', '开心', '伤心', '难过', '难受', '生气', '害怕', '紧张', '激动', '舒服', '痛', '不适', '遗憾', '厌烦']),
    ("七、饮食与就餐 · Dining and Eating", ['吃', '喝', '饭', '餐', '饿', '饱', '咖啡', '茶', '菜', '酒', '水', '点心', '买单', '味道', '尝', '面包', '汤', '早饭', '晚饭']),
    ("八、出行与交通 · Travel and Transportation", ['走', '车', '路', '站', '地铁', '公交', '出租', '机场', '飞机', '票', '去哪', '转弯', '到站', '迟到', '赶', '行李', '旅途']),
    ("九、购物与消费 · Shopping and Spending", ['买', '卖', '钱', '元', '贵', '便宜', '折', '商场', '店', '衣服', '穿', '试', '付', '现金', '刷卡', '找钱', '退货', '价格']),
    ("十、工作与学习 · Work and Study", ['工作', '上班', '下班', '开会', '学', '读', '书', '课', '业', '考', '公司', '做', '计划', '完成', '忙', '老板', '同事', '项目']),
    ("十一、夸赞与鼓励 · Praise and Encouragement", ['棒', '好极', '真棒', '精彩', '漂亮', '优秀', '加油', '努力', '干得好', '鼓励', '夸', '厉害', '佩服', '赞', '聪明', '帅', '酷']),
    ("十二、时间与天气 · Time and Weather", ['天气', '雨', '雪', '风', '晴', '热', '冷', '暖', '度', '云', '天', '几点', '点钟', '分', '时间', '表', '早', '晚', '季节']),
    ("十三、社交与闲聊 · Social Chat and Small Talk", ['聊', '朋友', '周末', '聚', '玩', '空', '最近', '久', '闲', '怎么样', '过得', '约', '见面', '电影', '兴趣', '爱好']),
    ("十四、建议与提醒 · Suggestions and Reminders", ['建议', '最好', '别', '不要', '记得', '提醒', '小心', '留神', '劝', '应该', '务必', '千万', '警告', '注意', '提防']),
    ("十五、祝愿与祝福 · Wishes and Blessings", ['祝', '愿', '幸', '福', '快乐', '平安', '顺利', '如意', '梦', '梦见', '保重', '恭喜', '贺', '健康', '长寿', '干杯'])
]

ch15_drills = {i: [] for i in range(15)}
# Inject exact Give me a hand into chapter 3 (index 2)
ch15_drills[2].append(("Give me a hand.", "帮我一下。"))

# Classify oral pairs
used_oral = set()
for idx, (title, kws) in enumerate(CH15_TOPICS):
    for en, zh in oral_pairs:
        if en == "Give me a hand.":
            continue
        if any(kw in zh for kw in kws):
            if (en, zh) not in used_oral:
                ch15_drills[idx].append((en, zh))
                used_oral.add((en, zh))

# Fill up to 60 per chapter from extra pairs or drills_database
all_extra_pairs = [p for p in oral_pairs if p not in used_oral] + [(d['english'], d['chinese']) for d in db_drills]

for idx in range(15):
    while len(ch15_drills[idx]) < 60 and all_extra_pairs:
        p = all_extra_pairs.pop(0)
        ch15_drills[idx].append(p)
    ch15_drills[idx] = ch15_drills[idx][:60]
    print(f"Chapter {idx+1} ({CH15_TOPICS[idx][0].split(' · ')[0]}): {len(ch15_drills[idx])} sentences")

print("[3/5] Constructing 12 Flagship Courses...")

def make_drill_obj(drill_id, course_id, chapter_id, chapter_title, en, zh, idx):
    chunks = tag_syntax_chunks(en)
    ipa = get_ipa(en)
    # clean words for underline slot typing
    words = [w.strip(',.?!;:\'"') for w in en.split() if w.strip(',.?!;:\'"')]
    tokens = [c['text'] for c in chunks] if chunks else words
    breakdown = " + ".join([f"{c['text']} [{c['role']}]" for c in chunks])
    return {
        "id": drill_id,
        "course_id": course_id,
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "index": idx,
        "english": en,
        "chinese": zh,
        "ipa": ipa,
        "chunks": chunks,
        "tokens": tokens,
        "words": words,
        "breakdown": breakdown,
        "cultural_tip": f"地道表达提示：熟练掌握“{en}”，注意重音与连读连贯度。"
    }

courses = []

# ==================== Course 1: 零基础日常口语表达900句 ====================
c1_chapters = []
total_c1_drills = 0
for idx, (title, _) in enumerate(CH15_TOPICS):
    ch_id = f"ch_{idx+1:02d}"
    sents = ch15_drills[idx]
    c_drills = []
    for s_idx, (en, zh) in enumerate(sents):
        d_id = f"oral900_{ch_id}_{s_idx+1:03d}"
        c_drills.append(make_drill_obj(d_id, "oral_900", ch_id, title, en, zh, s_idx + 1))
    total_c1_drills += len(c_drills)
    c1_chapters.append({
        "id": ch_id,
        "title": title,
        "chapter_num": idx + 1,
        "drill_count": len(c_drills),
        "status": "recent" if idx == 2 else ("completed" if idx < 2 else "unstarted"),
        "duration_seconds": 1060 if idx == 0 else (1034 if idx == 1 else (60 if idx == 2 else 0)),
        "completed_count": 1 if idx < 2 else 0,
        "drills": c_drills
    })

courses.append({
    "id": "oral_900",
    "title": "零基础日常口语表达900句",
    "english_title": "900 Essential Spoken English Expressions",
    "category": "zero",
    "category_name": "零基础",
    "tag": "精选爆款",
    "tag_style": "mint",
    "view_count": 8220,
    "chapter_count": 15,
    "sentence_count": total_c1_drills,
    "cover_gradient": "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
    "icon": "chat-circle-text",
    "description": "涵盖问候、感谢、请求等15大日常生活核心高频交际场景，零基础开口说地道口语。",
    "chapters": c1_chapters
})

# ==================== Course 2: 英语高频口语短句1000句 ====================
c2_chapters = []
spoken_pool = [p for p in oral_pairs if p not in used_oral]
if len(spoken_pool) < 1000:
    spoken_pool += [(d['english'], d['chinese']) for d in db_drills]

CH20_TITLES = [
    "一、初次相识与寒暄 · Meeting and Small Talk",
    "二、居家日常起居 · Daily Life at Home",
    "三、外出就餐点菜 · Dining at Restaurants",
    "四、购物试衣结账 · Shopping and Checkout",
    "五、城市出行问路 · Transportation and Directions",
    "六、旅行酒店住宿 · Travel and Hotels",
    "七、电话信息沟通 · Calls and Messages",
    "八、时间与日程安排 · Time and Scheduling",
    "九、天气与季节气候 · Weather and Seasons",
    "十、情绪喜怒哀乐 · Feelings and Moods",
    "十一、兴趣爱好娱乐 · Hobbies and Entertainment",
    "十二、健康就医看病 · Health and Medical",
    "十三、职场办公交流 · Workplace English",
    "十四、求助与表达建议 · Requests and Advice",
    "十五、表达观点态度 · Opinions and Attitudes",
    "十六、赞扬致谢鼓励 · Compliments and Thanks",
    "十七、抱歉原谅解围 · Apologies and Excuses",
    "十八、节假日与庆祝 · Holidays and Celebrations",
    "十九、数字金额计量 · Numbers and Prices",
    "二十、地道谚语表达 · Slang and Idioms"
]

total_c2_drills = 0
for idx, title in enumerate(CH20_TITLES):
    ch_id = f"ch_{idx+1:02d}"
    sents = spoken_pool[idx*50 : (idx+1)*50]
    c_drills = []
    for s_idx, (en, zh) in enumerate(sents):
        d_id = f"spoken1000_{ch_id}_{s_idx+1:03d}"
        c_drills.append(make_drill_obj(d_id, "spoken_1000", ch_id, title, en, zh, s_idx + 1))
    total_c2_drills += len(c_drills)
    c2_chapters.append({
        "id": ch_id,
        "title": title,
        "chapter_num": idx + 1,
        "drill_count": len(c_drills),
        "status": "unstarted",
        "duration_seconds": 0,
        "completed_count": 0,
        "drills": c_drills
    })

courses.append({
    "id": "spoken_1000",
    "title": "英语高频口语短句1000句",
    "english_title": "1000 High-Frequency Spoken Sentences",
    "category": "daily",
    "category_name": "日常实用",
    "tag": "用户共享",
    "tag_style": "cyan",
    "view_count": 8210,
    "chapter_count": 20,
    "sentence_count": total_c2_drills,
    "cover_gradient": "linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)",
    "icon": "translate",
    "description": "涵盖20个高频生活交流情境，高密度精读研习，提升英语语感和瞬时反应力。",
    "chapters": c2_chapters
})

# ==================== Helper for Pattern Courses (720/600/450/300) ====================
def build_pattern_course(cid, title, sub_title, cat, cat_name, tag, view_count, grad, icon, ch_titles, sents_per_ch, pool):
    chs = []
    total_sents = 0
    for idx, c_title in enumerate(ch_titles):
        ch_id = f"ch_{idx+1:02d}"
        sents = pool[idx*sents_per_ch : (idx+1)*sents_per_ch]
        c_drills = []
        for s_idx, p in enumerate(sents):
            en, zh = p if isinstance(p, tuple) else (p['english'], p['chinese'])
            d_id = f"{cid}_{ch_id}_{s_idx+1:03d}"
            c_drills.append(make_drill_obj(d_id, cid, ch_id, c_title, en, zh, s_idx + 1))
        total_sents += len(c_drills)
        chs.append({
            "id": ch_id,
            "title": c_title,
            "chapter_num": idx + 1,
            "drill_count": len(c_drills),
            "status": "unstarted",
            "duration_seconds": 0,
            "completed_count": 0,
            "drills": c_drills
        })
    return {
        "id": cid,
        "title": title,
        "english_title": sub_title,
        "category": cat,
        "category_name": cat_name,
        "tag": tag,
        "tag_style": "orange" if "720" in cid else "blue",
        "view_count": view_count,
        "chapter_count": len(chs),
        "sentence_count": total_sents,
        "cover_gradient": grad,
        "icon": icon,
        "description": f"{title} · 精选句型模块化研习，夯实语法骨架与口语流利度。",
        "chapters": chs
    }

# 3. 精选720组核心英文句型 少儿六上段
senior_drills = [d for d in db_drills if d.get('category') in {'senior', 'cet', 'ielts'}]
c3_titles = [
    "第一单元：时态综合运用 · Comprehensive Tenses",
    "第二单元：形容词比较级与最高级 · Comparisons",
    "第三单元：被动语态核心结构 · Passive Voice",
    "第四单元：动名词与不定式 · Gerunds and Infinitives",
    "第五单元：宾语从句句型 · Object Clauses",
    "第六单元：状语从句句型 · Adverbial Clauses"
]
courses.append(build_pattern_course(
    "pattern_720_up", "精选720组核心英文句型 少儿六上段", "720 Core Patterns - Grade 6A",
    "comprehensive", "综合提升", "用户共享", 8200, "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
    "books", c3_titles, 60, senior_drills[:360]
))

# 4. 精选720组核心英文句型 少儿六下段
c4_titles = [
    "第一单元：定语从句入门 · Attributive Clauses",
    "第二单元：条件状语从句 (If条件句) · Conditionals",
    "第三单元：过去完成时精析 · Past Perfect Tense",
    "第四单元：情态动词进阶运用 · Advanced Modals",
    "第五单元：虚拟语气基础与愿望表达 · Subjunctive Basics",
    "第六单元：综合阅读与长难句突破 · Complex Structures"
]
courses.append(build_pattern_course(
    "pattern_720_down", "精选720组核心英文句型 少儿六下段", "720 Core Patterns - Grade 6B",
    "comprehensive", "综合提升", "用户共享", 8116, "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
    "graduation-cap", c4_titles, 60, senior_drills[360:720] if len(senior_drills) >= 720 else senior_drills[:360]
))

# 5. 精选600组核心英文句型 少儿五上段
junior_drills = [d for d in db_drills if d.get('category') in {'junior', 'primary'}]
c5_titles = [
    "第一单元：一般现在时与频度副词 · Present Simple",
    "第二单元：现在进行时态句型 · Present Continuous",
    "第三单元：There be 句型深度精通 · There be Patterns",
    "第四单元：一般疑问句与特殊疑问句 · Question Patterns",
    "第五单元：情态动词 Can / May / Must · Modal Verbs"
]
courses.append(build_pattern_course(
    "pattern_600_up", "精选600组核心英文句型 少儿五上段", "600 Core Patterns - Grade 5A",
    "comprehensive", "综合提升", "用户共享", 8010, "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
    "tree-structure", c5_titles, 60, junior_drills[:300]
))

# 6. 精选600组核心英文句型 少儿五下段
c6_titles = [
    "第一单元：一般过去时规则与不规则动词 · Past Simple",
    "第二单元：一般将来时 will / be going to · Future Simple",
    "第三单元：祈使句与日常礼貌请求 · Imperatives",
    "第四单元：感官动词与系表结构 · Linking Verbs",
    "第五单元：方位介词与地点状语 · Prepositions of Place"
]
courses.append(build_pattern_course(
    "pattern_600_down", "精选600组核心英文句型 少儿五下段", "600 Core Patterns - Grade 5B",
    "comprehensive", "综合提升", "用户共享", 8005, "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
    "compass", c6_titles, 60, junior_drills[300:600] if len(junior_drills) >= 600 else junior_drills[:300]
))

# 7. 精选450组核心英文句型 少儿四上段
primary_drills = [d for d in db_drills if d.get('category') == 'primary']
c7_titles = [
    "第一单元：自我介绍与问候句型 · Self Introduction",
    "第二单元：家庭成员与称谓表达 · Family Members",
    "第三单元：学校课室与文具物品 · School Supplies",
    "第四单元：身体部位与服饰打扮 · Body and Clothes",
    "第五单元：日常爱好与体育运动 · Sports and Hobbies"
]
courses.append(build_pattern_course(
    "pattern_450_up", "精选450组核心英文句型 少儿四上段", "450 Core Patterns - Grade 4A",
    "comprehensive", "综合提升", "用户共享", 7980, "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
    "user-circle", c7_titles, 45, primary_drills[:225] if len(primary_drills) >= 225 else db_drills[:225]
))

# 8. 精选450组核心英文句型 少儿四下段
c8_titles = [
    "第一单元：食物餐饮与最爱美食 · Food and Drinks",
    "第二单元：动物乐园与宠物特性 · Animals and Pets",
    "第三单元：时间表达与日程时刻 · Telling Time",
    "第四单元：天气冷暖与四季变换 · Seasons and Weather",
    "第五单元：城市地点与交通方式 · Places and Transport"
]
courses.append(build_pattern_course(
    "pattern_450_down", "精选450组核心英文句型 少儿四下段", "450 Core Patterns - Grade 4B",
    "comprehensive", "综合提升", "用户共享", 7940, "linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)",
    "sun", c8_titles, 45, db_drills[225:450]
))

# 9. 精选300组核心英文句型 少儿三上段
c9_titles = [
    "第一单元：问候称呼与告别 · Greetings & Names",
    "第二单元：常见颜色与文具辨识 · Colors & Objects",
    "第三单元：数字与简易问答 · Numbers & Counting"
]
courses.append(build_pattern_course(
    "pattern_300_up", "精选300组核心英文句型 少儿三上段", "300 Core Patterns - Grade 3A",
    "zero", "零基础", "用户共享", 7890, "linear-gradient(135deg, #ec4899 0%, #db2777 100%)",
    "palette", c9_titles, 50, db_drills[450:600]
))

# 10. 精选300组核心英文句型 少儿三下段
c10_titles = [
    "第一单元：农场小动物与叫声 · Farm Animals",
    "第二单元：可口水果与食物喜好 · Fruits & Likes",
    "第三单元：玩具与物品归属 · Toys & Belongings"
]
courses.append(build_pattern_course(
    "pattern_300_down", "精选300组核心英文句型 少儿三下段", "300 Core Patterns - Grade 3B",
    "zero", "零基础", "用户共享", 7850, "linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)",
    "balloon", c10_titles, 50, db_drills[600:750]
))

# 11. 零基础学英语 (认识动物、星期、水果...)
zero_starter_drills = [
    # 动物
    ("The cat is sleeping on the chair.", "小猫正在椅子上睡觉。"),
    ("The dog is playing with a ball.", "小狗正在玩球。"),
    ("The bird is singing in the tree.", "小鸟正在树上唱歌。"),
    ("The rabbit has long ears.", "兔子有一对长耳朵。"),
    ("The panda likes eating bamboo.", "大熊猫喜欢吃竹子。"),
    ("The monkey is climbing a tree.", "猴子正在爬树。"),
    ("The elephant is very big.", "大象非常巨大。"),
    ("The lion is the king of beasts.", "狮子是万兽之王。"),
    ("The fish swims in the water.", "鱼儿在水里游。"),
    ("The duck is swimming in the pond.", "鸭子在池塘里游泳。"),
    ("The bear is catching fish.", "熊正在抓鱼。"),
    ("The horse runs very fast.", "马跑得非常快。"),
    # 水果
    ("I like eating red apples.", "我喜欢吃红苹果。"),
    ("The banana is sweet and soft.", "香蕉又甜又软。"),
    ("The orange is rich in vitamin C.", "橙子富含维生素C。"),
    ("Watermelon is my favorite fruit.", "西瓜是我最喜欢的水果。"),
    ("The strawberry is very delicious.", "草莓非常美味。"),
    ("Do you want some grapes?", "你想来点葡萄吗？"),
    ("The peach smells so good.", "桃子闻起来真香。"),
    ("I love sweet mangoes.", "我喜爱香甜的芒果。"),
    # 星期与时间
    ("Today is Monday.", "今天是星期一。"),
    ("We have English class on Tuesday.", "我们星期二有英语课。"),
    ("Wednesday is the middle of the week.", "星期三是一周的中间。"),
    ("I go swimming on Thursday.", "我星期四去游泳。"),
    ("Friday is my favorite day.", "星期五是我最喜欢的一天。"),
    ("Saturday is great for a picnic.", "星期六非常适合去野餐。"),
    ("Sunday is a relaxing day.", "星期天是放松的一天。"),
    ("What day is it today?", "今天星期几？")
]

c11_titles = [
    "第一单元：动物乐园 · Animal Friends",
    "第二单元：缤纷水果 · Delicious Fruits",
    "第三单元：日历与星期 · Days of the Week",
    "第四单元：基础数字与色彩 · Numbers & Colors",
    "第五单元：日常生活用品 · Daily Objects"
]
courses.append(build_pattern_course(
    "zero_starter", "零基础学英语 (认识动物、星期、水果...)", "English for Beginners - Vocabulary & Short Sentences",
    "zero", "零基础", "用户共享", 8020, "linear-gradient(135deg, #10b981 0%, #84cc16 100%)",
    "sparkle", c11_titles, 6, zero_starter_drills
))

# 12. 26个英文字母与发音自然拼读
alphabet_drills = [
    ("A is for Apple.", "A代表苹果。"),
    ("B is for Book.", "B代表书本。"),
    ("C is for Cat.", "C代表猫咪。"),
    ("D is for Dog.", "D代表小狗。"),
    ("E is for Elephant.", "E代表大象。"),
    ("F is for Fish.", "F代表小鱼。"),
    ("G is for Girl.", "G代表女孩。"),
    ("H is for House.", "H代表房屋。"),
    ("I is for Ice cream.", "I代表冰淇淋。"),
    ("J is for Juice.", "J代表果汁。"),
    ("K is for Kite.", "K代表风筝。"),
    ("L is for Lion.", "L代表狮子。"),
    ("M is for Moon.", "M代表月亮。"),
    ("N is for Nose.", "N代表鼻子。"),
    ("O is for Orange.", "O代表橙子。"),
    ("P is for Pen.", "P代表钢笔。"),
    ("Q is for Queen.", "Q代表女王。"),
    ("R is for Rabbit.", "R代表兔子。"),
    ("S is for Sun.", "S代表太阳。"),
    ("T is for Tree.", "T代表大树。"),
    ("U is for Umbrella.", "U代表雨伞。"),
    ("V is for Violin.", "V代表小提琴。"),
    ("W is for Water.", "W代表水。"),
    ("X is for X-ray.", "X代表X光。"),
    ("Y is for Yellow.", "Y代表黄色。"),
    ("Z is for Zebra.", "Z代表斑马。")
]

c12_titles = [
    "第一单元：字母发音与单词自然拼读 (A - I) · Letters A to I",
    "第二单元：字母发音与单词自然拼读 (J - R) · Letters J to R",
    "第三单元：字母发音与单词自然拼读 (S - Z) · Letters S to Z"
]
courses.append(build_pattern_course(
    "alphabet_phonics", "26个英文字母与发音自然拼读", "26 English Letters & Phonics",
    "zero", "零基础", "用户共享", 8150, "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
    "text-a-underline", c12_titles, 9, alphabet_drills
))

print(f"[4/5] Generated {len(courses)} courses total.")
total_sentences_all = sum(c['sentence_count'] for c in courses)
print(f"Total sentences across all courses: {total_sentences_all}")

print(f"[5/5] Saving to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)

file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"Done! Database generated successfully ({file_size_mb:.2f} MB).")
