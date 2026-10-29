# -*- coding: utf-8 -*-
"""
Build Complete Courses Database for Jingjing English Lab
Generates app/courses_database.json with courses covering ALL 13 categories,
including Kokoro IPA phonetics and syntactic grammar chunk tagging.
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
ch15_drills[2].append(("Give me a hand.", "帮我一下。"))

used_oral = set()
for idx, (title, kws) in enumerate(CH15_TOPICS):
    for en, zh in oral_pairs:
        if en == "Give me a hand.":
            continue
        if any(kw in zh for kw in kws):
            if (en, zh) not in used_oral:
                ch15_drills[idx].append((en, zh))
                used_oral.add((en, zh))

all_extra_pairs = [p for p in oral_pairs if p not in used_oral] + [(d['english'], d['chinese']) for d in db_drills]

for idx in range(15):
    while len(ch15_drills[idx]) < 60 and all_extra_pairs:
        p = all_extra_pairs.pop(0)
        ch15_drills[idx].append(p)
    ch15_drills[idx] = ch15_drills[idx][:60]

print("[3/5] Constructing Full Curriculum Covering ALL 13 Categories...")

def make_drill_obj(drill_id, course_id, chapter_id, chapter_title, en, zh, idx):
    chunks = tag_syntax_chunks(en)
    ipa = get_ipa(en)
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

def build_course(cid, title, sub_title, categories, tag, tag_style, view_count, grad, icon, ch_titles, sents_per_ch, pool, desc):
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
        "category": categories[0] if categories else "日常实用",
        "category_name": categories[0] if categories else "日常实用",
        "categories": categories,
        "tag": tag,
        "tag_style": tag_style,
        "view_count": view_count,
        "chapter_count": len(chs),
        "sentence_count": total_sents,
        "cover_gradient": grad,
        "icon": icon,
        "description": desc,
        "chapters": chs
    }

courses = []

# ==================== 1. 零基础日常口语表达900句 (零基础 + 日常实用) ====================
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
    "category": "零基础",
    "category_name": "零基础",
    "categories": ["全部", "零基础", "日常实用"],
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

# ==================== 2. 英语高频口语短句1000句 (日常实用 + 综合提升) ====================
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
spoken_pool = [p for p in oral_pairs if p not in used_oral]
if len(spoken_pool) < 1000:
    spoken_pool += [(d['english'], d['chinese']) for d in db_drills]

courses.append(build_course(
    "spoken_1000", "英语高频口语短句1000句", "1000 High-Frequency Spoken Sentences",
    ["全部", "日常实用", "综合提升"], "用户共享", "cyan", 8210,
    "linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)", "translate",
    CH20_TITLES, 50, spoken_pool[:1000], "涵盖20个高频生活交流情境，高密度精读研习，提升英语语感和瞬时反应力。"
))

# ==================== 3 & 4. 精选720组核心英文句型 (综合提升 + 分级阅读) ====================
senior_drills = [d for d in db_drills if d.get('category') in {'senior', 'cet', 'ielts'}]
c3_titles = [
    "第一单元：时态综合运用 · Comprehensive Tenses",
    "第二单元：形容词比较级与最高级 · Comparisons",
    "第三单元：被动语态核心结构 · Passive Voice",
    "第四单元：动名词与不定式 · Gerunds and Infinitives",
    "第五单元：宾语从句句型 · Object Clauses",
    "第六单元：状语从句句型 · Adverbial Clauses"
]
courses.append(build_course(
    "pattern_720_up", "精选720组核心英文句型 少儿六上段", "720 Core Patterns - Grade 6A",
    ["全部", "综合提升", "分级阅读"], "用户共享", "orange", 8200,
    "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", "books",
    c3_titles, 60, senior_drills[:360], "小初衔接核心语法，聚焦时态、被动语态与复合句深度解析。"
))

c4_titles = [
    "第一单元：定语从句入门 · Attributive Clauses",
    "第二单元：条件状语从句 (If条件句) · Conditionals",
    "第三单元：过去完成时精析 · Past Perfect Tense",
    "第四单元：情态动词进阶运用 · Advanced Modals",
    "第五单元：虚拟语气基础与愿望表达 · Subjunctive Basics",
    "第六单元：综合阅读与长难句突破 · Complex Structures"
]
courses.append(build_course(
    "pattern_720_down", "精选720组核心英文句型 少儿六下段", "720 Core Patterns - Grade 6B",
    ["全部", "综合提升", "分级阅读"], "用户共享", "orange", 8116,
    "linear-gradient(135deg, #f97316 0%, #ea580c 100%)", "graduation-cap",
    c4_titles, 60, senior_drills[360:720] if len(senior_drills) >= 720 else senior_drills[:360],
    "小初高频进阶句式，掌握定语从句与条件句地道语感。"
))

# ==================== 5 & 6. 精选600组核心英文句型 (综合提升 + 分级阅读) ====================
junior_drills = [d for d in db_drills if d.get('category') in {'junior', 'primary'}]
c5_titles = [
    "第一单元：一般现在时与频度副词 · Present Simple",
    "第二单元：现在进行时态句型 · Present Continuous",
    "第三单元：There be 句型深度精通 · There be Patterns",
    "第四单元：一般疑问句与特殊疑问句 · Question Patterns",
    "第五单元：情态动词 Can / May / Must · Modal Verbs"
]
courses.append(build_course(
    "pattern_600_up", "精选600组核心英文句型 少儿五上段", "600 Core Patterns - Grade 5A",
    ["全部", "综合提升", "分级阅读"], "用户共享", "blue", 8010,
    "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)", "tree-structure",
    c5_titles, 60, junior_drills[:300], "五年级核心语法与常用交际短语精练。"
))

c6_titles = [
    "第一单元：一般过去时规则与不规则动词 · Past Simple",
    "第二单元：一般将来时 will / be going to · Future Simple",
    "第三单元：祈使句与日常礼貌请求 · Imperatives",
    "第四单元：感官动词与系表结构 · Linking Verbs",
    "第五单元：方位介词与地点状语 · Prepositions of Place"
]
courses.append(build_course(
    "pattern_600_down", "精选600组核心英文句型 少儿五下段", "600 Core Patterns - Grade 5B",
    ["全部", "综合提升", "分级阅读"], "用户共享", "indigo", 8005,
    "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)", "compass",
    c6_titles, 60, junior_drills[300:600] if len(junior_drills) >= 600 else junior_drills[:300],
    "过去时与将来时实战，方位介词与常用祈使表达。"
))

# ==================== 7 & 8. 精选450组核心英文句型 (综合提升 + 分级阅读) ====================
c7_titles = [
    "第一单元：自我介绍与问候句型 · Self Introduction",
    "第二单元：家庭成员与称谓表达 · Family Members",
    "第三单元：学校课室与文具物品 · School Supplies",
    "第四单元：身体部位与服饰打扮 · Body and Clothes",
    "第五单元：日常爱好与体育运动 · Sports and Hobbies"
]
courses.append(build_course(
    "pattern_450_up", "精选450组核心英文句型 少儿四上段", "450 Core Patterns - Grade 4A",
    ["全部", "综合提升", "分级阅读"], "用户共享", "teal", 7980,
    "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)", "user-circle",
    c7_titles, 45, db_drills[:225], "四年级基础核心句型，涵盖日常自我介绍、文具与喜好。"
))

c8_titles = [
    "第一单元：食物餐饮与最爱美食 · Food and Drinks",
    "第二单元：动物乐园与宠物特性 · Animals and Pets",
    "第三单元：时间表达与日程时刻 · Telling Time",
    "第四单元：天气冷暖与四季变换 · Seasons and Weather",
    "第五单元：城市地点与交通方式 · Places and Transport"
]
courses.append(build_course(
    "pattern_450_down", "精选450组核心英文句型 少儿四下段", "450 Core Patterns - Grade 4B",
    ["全部", "综合提升", "分级阅读"], "用户共享", "teal", 7940,
    "linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)", "sun",
    c8_titles, 45, db_drills[225:450], "美食餐饮、时间日程与城市交通高频表达。"
))

# ==================== 9 & 10. 精选300组核心英文句型 (零基础 + 分级阅读) ====================
c9_titles = [
    "第一单元：问候称呼与告别 · Greetings & Names",
    "第二单元：常见颜色与文具辨识 · Colors & Objects",
    "第三单元：数字与简易问答 · Numbers & Counting"
]
courses.append(build_course(
    "pattern_300_up", "精选300组核心英文句型 少儿三上段", "300 Core Patterns - Grade 3A",
    ["全部", "零基础", "分级阅读"], "用户共享", "pink", 7890,
    "linear-gradient(135deg, #ec4899 0%, #db2777 100%)", "palette",
    c9_titles, 50, db_drills[450:600], "三年级启蒙，简单问候、颜色与基础数字表达。"
))

c10_titles = [
    "第一单元：农场小动物与叫声 · Farm Animals",
    "第二单元：可口水果与食物喜好 · Fruits & Likes",
    "第三单元：玩具与物品归属 · Toys & Belongings"
]
courses.append(build_course(
    "pattern_300_down", "精选300组核心英文句型 少儿三下段", "300 Core Patterns - Grade 3B",
    ["全部", "零基础", "分级阅读"], "用户共享", "rose", 7850,
    "linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)", "balloon",
    c10_titles, 50, db_drills[600:750], "趣味动物、可口水果与玩具归属日常表达。"
))

# ==================== 11. 零基础学英语 (零基础 + 分级阅读) ====================
zero_starter_drills = [
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
    ("I like eating red apples.", "我喜欢吃红苹果。"),
    ("The banana is sweet and soft.", "香蕉又甜又软。"),
    ("The orange is rich in vitamin C.", "橙子富含维生素C。"),
    ("Watermelon is my favorite fruit.", "西瓜是我最喜欢的水果。"),
    ("The strawberry is very delicious.", "草莓非常美味。"),
    ("Do you want some grapes?", "你想来点葡萄吗？"),
    ("The peach smells so good.", "桃子闻起来真香。"),
    ("I love sweet mangoes.", "我喜爱香甜的芒果。"),
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
courses.append(build_course(
    "zero_starter", "零基础学英语 (认识动物、星期、水果...)", "English for Beginners - Vocabulary & Short Sentences",
    ["全部", "零基础", "分级阅读"], "精选推荐", "emerald", 8020,
    "linear-gradient(135deg, #10b981 0%, #84cc16 100%)", "sparkle",
    c11_titles, 6, zero_starter_drills, "超萌动物、美味水果与星期日历启蒙短句。"
))

# ==================== 12. 26个英文字母与发音自然拼读 (零基础 + 分级阅读) ====================
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
courses.append(build_course(
    "alphabet_phonics", "26个英文字母与发音自然拼读", "26 English Letters & Phonics",
    ["全部", "零基础", "分级阅读"], "官方推荐", "violet", 8150,
    "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)", "text-a-underline",
    c12_titles, 9, alphabet_drills, "26个字母发音口型与基础自然拼读规则。"
))

# ==================== 13. 商务英语 (商务英语 + 行业英语) ====================
office_drills = [d for d in db_drills if d.get('category') == 'office']
if len(office_drills) < 120:
    office_drills += [(p['english'], p['chinese']) for p in db_drills if p.get('category') in {'senior', 'cet'}]
c13_titles = [
    "第一单元：商务初次会面与接待 · Business Greetings & Reception",
    "第二单元：外贸业务询盘与报价 · Inquiries and Quotations",
    "第三单元：商务合同与交付条款 · Contracts and Delivery",
    "第四单元：跨国会议与远程沟通 · Meetings and Remote Calls"
]
courses.append(build_course(
    "business_300", "国际职场与商务英语高频核心表达", "International Business English in Practice",
    ["全部", "商务英语", "行业英语"], "职场精选", "sky", 8190,
    "linear-gradient(135deg, #0284c7 0%, #2563eb 100%)", "briefcase",
    c13_titles, 30, office_drills[:120], "涵盖商务接待、商务谈判、询盘报价与跨国远程会议高频句型。"
))

# ==================== 14. 认证备考 (认证备考 + 综合提升) ====================
ielts_drills = [d for d in db_drills if d.get('category') == 'ielts']
c14_titles = [
    "第一单元：雅思Part 1 个人生活与爱好 · Personal Profile",
    "第二单元：雅思Part 2 经历与事件描述 · Experience & Events",
    "第三单元：雅思Part 3 深度论证与社会议题 · In-depth Debate",
    "第四单元：高分地道习语与学术连接词 · Academic Linkers"
]
courses.append(build_course(
    "ielts_200", "雅思口语高频题库与高分表达精析", "IELTS Speaking Masterclass - Band 7+ Expressions",
    ["全部", "认证备考", "综合提升"], "考试必备", "emerald", 8230,
    "linear-gradient(135deg, #059669 0%, #0d9488 100%)", "certificate",
    c14_titles, 50, ielts_drills[:200], "针对雅思与托福口语评分标准，强化逻辑连贯词与地道地貌表达。"
))

# ==================== 15. 大学英语四六级备考 (认证备考 + 综合提升) ====================
cet_drills = [d for d in db_drills if d.get('category') == 'cet']
c15_titles = [
    "第一单元：四六级听力高频设空句式 · Listening Comprehension",
    "第二单元：常考图表与数据分析表达 · Data and Graphs",
    "第三单元：写作高分转折与因果从句 · Transitional Structures",
    "第四单元：长篇阅读长难句结构拆解 · Reading Breakdown"
]
courses.append(build_course(
    "cet_300", "大学英语四六级口语与写作核心句式", "CET-4/6 Key Expressions & Sentence Patterns",
    ["全部", "认证备考", "综合提升"], "高分必备", "indigo", 8140,
    "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)", "book-bookmark",
    c15_titles, 60, cet_drills[:240], "四六级听力设空、写作闪光从句与口语问答核心表达。"
))

# ==================== 16. 娱乐影音 (娱乐影音 + 日常实用 + 其他) ====================
smalltalk_drills = [d for d in db_drills if d.get('category') == 'smalltalk'] + [d for d in db_drills if d.get('category') == 'cafe']
c16_titles = [
    "第一单元：经典美剧高频口语俚语 · Popular American TV Slang",
    "第二单元：电影地道台词与幽默对白 · Movie Dialogue & Wit",
    "第三单元：日常生活吐槽与网络流行语 · Daily Chitchat & Trends",
    "第四单元：朋友聚会派对破冰互动 · Party Games & Banter"
]
courses.append(build_course(
    "entertainment_slang", "经典美剧俚语与地道影视对白精选", "American TV Slang & Movie Dialogue Expressions",
    ["全部", "娱乐影音", "日常实用", "其他"], "潮流精选", "purple", 8280,
    "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)", "film-slate",
    c16_titles, 30, smalltalk_drills[:120], "脱口秀、美剧与电影中常出现的鲜活口语俚语与地道表达。"
))

# ==================== 17. 中国文化 (中国文化 + 日常实用) ====================
chinese_culture_drills = [
    ("The Spring Festival is the most important festival in China.", "春节是中国最重要的传统节日。"),
    ("We have dumplings and paste Spring Festival couplets.", "我们吃饺子并贴春联。"),
    ("The Mid-Autumn Festival is a time for family reunion.", "中秋节是家人团聚的时刻。"),
    ("Dragon boat racing is held during the Dragon Boat Festival.", "端午节期间会举行赛龙舟比赛。"),
    ("Chinese tea culture has a history of thousands of years.", "中国茶文化拥有数千年的悠久历史。"),
    ("Tofu and Peking duck are world-famous Chinese dishes.", "豆腐和北京烤鸭是闻名世界的中国美食。"),
    ("The Great Wall is one of the wonders of the world.", "长城是世界奇迹之一。"),
    ("Traditional Chinese paper-cutting is a beautiful folk art.", "中国传统剪纸是一门优美的民间艺术。"),
    ("Chinese calligraphy reflects the beauty of rhythm and balance.", "中国书法体现了韵律与平衡之美。"),
    ("Tai Chi is an ancient martial art for both health and peace.", "太极拳是强身健体、修身养性的古老武术。"),
    ("Hotpot brings friends and family together warmly.", "火锅让家人朋友温暖地聚在一起。"),
    ("Red lanterns are hung to welcome good luck and happiness.", "挂红灯笼寓意迎福迎祥、幸福美满。"),
    ("Tang poetry represents the golden age of Chinese literature.", "唐诗代表了中国文学的黄金时代。"),
    ("The Silk Road connected ancient trade and civilization.", "丝绸之路连接了古代商贸与东西方文明。"),
    ("Chopsticks have been used in China for over three thousand years.", "筷子在中国已有三千多年的使用历史。"),
    ("The Lantern Festival marks the end of the Spring Festival.", "元宵节标志着春节庆祝活动的圆满结束。")
]
c17_titles = [
    "第一单元：中华传统节日与风俗民俗 · Traditional Festivals",
    "第二单元：中华地道美食与茶艺文化 · Food & Tea Culture",
    "第三单元：古代名胜古迹与丝路文明 · Heritage & Landmarks",
    "第四单元：传统艺术、书法与太极拳 · Martial Arts & Crafts"
]
courses.append(build_course(
    "chinese_culture", "用英语讲中国故事与传统文化精选", "Telling Chinese Stories & Cultural Heritage in English",
    ["全部", "中国文化", "日常实用"], "国风精选", "red", 8170,
    "linear-gradient(135deg, #dc2626 0%, #f97316 100%)", "sparkle",
    c17_titles, 4, chinese_culture_drills, "春节、中秋、茶文化与传统名胜古迹地道英文表达。"
))

# ==================== 18. 行业英语 (行业英语 + 商务英语) ====================
tech_drills = [
    ("We need to deploy the latest release to production tonight.", "我们今晚需要将最新版本部署到生产环境。"),
    ("Please create a pull request before merging into main.", "合并到主分支之前请先创建 Pull Request。"),
    ("The system architecture supports horizontal auto-scaling.", "系统架构支持水平自动化弹性扩缩容。"),
    ("Let's hold a quick daily standup meeting at ten.", "我们十点钟开一个简短的每日站立会。"),
    ("We observed high CPU usage and memory leakage in the cluster.", "我们在集群中观察到了高CPU占用和内存泄露。"),
    ("The API latency decreased significantly after Redis caching.", "引入 Redis 缓存后接口延迟显著降低。"),
    ("We follow agile methodology with two-week development sprints.", "我们遵循敏捷开发流程，采用两周一个迭代周期。"),
    ("Please document the API endpoints using Swagger or Postman.", "请使用 Swagger 或 Postman 规范书写接口文档。"),
    ("Database replication ensures high availability and disaster recovery.", "数据库副本机制保障了高可用性与灾备容灾能力。"),
    ("Our team focuses on cloud-native infrastructure on Kubernetes.", "我们团队专注于 Kubernetes 上的云原生基础设施。"),
    ("Code reviews help maintain high software quality and clean code.", "代码评审有助于维护高质量的软件标准与整洁代码。"),
    ("Let's analyze user feedback to optimize the next product release.", "让我们分析用户反馈以优化下一轮产品发布。")
]
c18_titles = [
    "第一单元：敏捷研发与日常站会交流 · Agile and Daily Standups",
    "第二单元：系统架构与云原生运维 · Architecture & Cloud",
    "第三单元：接口联调与线上排错 · API Integration & Debugging",
    "第四单元：产品迭代与用户体验优化 · Product Iterations & UX"
]
courses.append(build_course(
    "tech_industry", "互联网技术研发与IT职场高频英语", "IT & Software Engineering Workplace English",
    ["全部", "行业英语", "商务英语"], "极客精选", "cyan", 8260,
    "linear-gradient(135deg, #0891b2 0%, #0284c7 100%)", "cpu",
    c18_titles, 3, tech_drills, "覆盖代码评审、敏捷站会、架构设计与线上故障排查地道术语与表达。"
))

# ==================== 19. 文学读物 (文学读物 + 综合提升) ====================
lit_drills = [
    ("It is a truth universally acknowledged that a single man must be in want of a wife.", "凡是有钱的单身汉，总想娶位太太，这是一条举世公认的真理。"),
    ("To be or not to be, that is the question.", "生存还是毁灭，这是一个值得深思的问题。"),
    ("All animals are equal, but some animals are more equal than others.", "所有动物生来平等，但有些动物比其他动物更平等。"),
    ("The only way out of the labyrinth of suffering is to forgive.", "走出痛苦迷宫的唯一出路是选择宽恕。"),
    ("Not all those who wander are lost.", "徘徊漫步的人并不都是迷惘者。"),
    ("Whatever our souls are made of, his and mine are the same.", "无论我们的灵魂由什么做成，他的和我的都是完全一样的。"),
    ("So we beat on, boats against the current, borne back ceaselessly into the past.", "于是我们逆水行舟，奋力向前，直至被不断推回往昔的岁月。"),
    ("The flower that blooms in adversity is the most rare and beautiful of all.", "逆境中绽放的花朵，是所有花朵中最珍贵、最美丽的。"),
    ("Stay hungry, stay foolish.", "求知若饥，虚心若愚。"),
    ("In the middle of difficulty lies opportunity.", "在困难与挑战的中心，往往孕育着崭新的机遇。"),
    ("The best preparation for tomorrow is doing your best today.", "对明天最好的准备，就是把今天做到极致。"),
    ("Happiness can be found even in the darkest of times, if one only remembers to turn on the light.", "即使在最黑暗的时刻也能找到快乐，只要有人记得点亮光明。")
]
c19_titles = [
    "第一单元：世界文学名著金句诵读 · Famous Literary Quotes",
    "第二单元：经典英美散文哲思篇章 · Reflective Essays",
    "第三单元：英文经典诗歌韵律精读 · Classic English Poems",
    "第四单元：名家小说长难句语法剖析 · Complex Literary Sentences"
]
courses.append(build_course(
    "literature_classics", "世界经典名著名篇晨读与长难句精析", "Masterpieces of English Literature & Deep Reading",
    ["全部", "文学读物", "综合提升"], "经典必读", "amber", 8160,
    "linear-gradient(135deg, #d97706 0%, #b45309 100%)", "book-open",
    c19_titles, 3, lit_drills, "莎士比亚、简·奥斯汀与海明威名篇精选，提升深层次英语语感。"
))

# ==================== 20. 英文演讲 (英文演讲 + 综合提升) ====================
speech_drills = [
    ("Today I want to share with you three stories from my life.", "今天我想和大家分享我人生中的三个故事。"),
    ("Have you ever wondered why some people achieve extraordinary things?", "你是否曾经思考过，为什么有些人能成就非凡的事业？"),
    ("The true measure of courage is not the absence of fear, but the triumph over it.", "勇气的真正衡量标准不是没有恐惧，而是战胜恐惧。"),
    ("We must become the change that we wish to see in the world.", "我们必须成为我们希望在世界上看到的改变。"),
    ("Let me begin with a question that changed the way I think about education.", "请允许我从一个彻底改变了我对教育思考方式的问题开始。"),
    ("The future belongs to those who believe in the beauty of their dreams.", "未来属于那些相信自己梦想之美好的人。"),
    ("When you change the way you look at things, the things you look at change.", "当你改变看事物的角度，你所看到的事物也会随之改变。"),
    ("Every great journey starts with a single step into the unknown.", "每一段伟大的旅程，都始于迈向未知世界的第一步。"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "成功不是终点，失败不是终结：唯有继续前行的勇气才是最重要的。"),
    ("Thank you for your time, and let us build a brighter tomorrow together.", "感谢大家的宝贵时间，让我们携手共建更美好的明天。"),
    ("Believe in your unique voice, because the world is waiting to hear it.", "请坚信你独特的声音，因为全世界都在静候聆听。"),
    ("Knowledge without action is merely potential power.", "没有行动的知识，仅仅只是潜在的力量。")
]
c20_titles = [
    "第一单元：演讲开场白抓人技巧 · Engaging Opening Hooks",
    "第二单元：观点论据与故事共鸣 · Storytelling & Perspectives",
    "第三单元：修辞排比与演讲节奏 · Rhetorical Rhythm & Cadence",
    "第四单元：强有力总结与号召呼吁 · Powerful Call to Action"
]
courses.append(build_course(
    "ted_speech", "TED高分演讲核心启发句型与表达技巧", "TED Talks Speaking & Presentation Mastery",
    ["全部", "英文演讲", "综合提升"], "演讲高分", "rose", 8295,
    "linear-gradient(135deg, #e11d48 0%, #be123c 100%)", "microphone-stage",
    c20_titles, 3, speech_drills, "掌握公众演讲开场破冰、排比论证、故事叙述与情绪唤起核心技巧。"
))

# ==================== 21. 其他 (其他 + 日常实用) ====================
proverb_drills = [
    ("Kill two birds with one stone.", "一举两得（一石二鸟）。"),
    ("Speak of the devil and he shall appear.", "说曹操，曹操到。"),
    ("Practice makes perfect.", "熟能生巧。"),
    ("Action speaks louder than words.", "行胜于言（事实胜于雄辩）。"),
    ("Every cloud has a silver lining.", "黑暗中总有一丝曙光（否极泰来）。"),
    ("When in Rome, do as the Romans do.", "入乡随俗。"),
    ("Better late than never.", "迟做总比不做好。"),
    ("Don't put all your eggs in one basket.", "不要把鸡蛋放在同一个篮子里（分散风险）。"),
    ("A journey of a thousand miles begins with a single step.", "千里之行，始于足下。"),
    ("Rome was not built in a day.", "伟业非一日之功（罗马不是一天建成的）。"),
    ("Two heads are better than one.", "三个臭皮匠，顶个诸葛亮。"),
    ("Where there is a will, there is a way.", "有志者事竟成。")
]
c21_titles = [
    "第一单元：地道英语谚语与民间智慧 · Proverbs & Folk Wisdom",
    "第二单元：生活常用习惯用语 · Everyday Idioms",
    "第三单元：中英对照哲理名句 · Philosophical Sayings"
]
courses.append(build_course(
    "proverbs_idioms", "地道经典英语谚语与常用成语精粹", "Timeless English Proverbs and Common Idioms",
    ["全部", "其他", "日常实用"], "生活智慧", "slate", 8120,
    "linear-gradient(135deg, #475569 0%, #334155 100%)", "lightbulb",
    c21_titles, 4, proverb_drills, "日常口语与地道写作中画龙点睛的常用谚语与惯用表达。"
))

print(f"[4/5] Generated {len(courses)} courses total.")
category_counts = {}
for c in courses:
    for cat in c.get('categories', []):
        category_counts[cat] = category_counts.get(cat, 0) + 1
print("Courses distribution per category:")
for cat, count in category_counts.items():
    print(f"  - {cat}: {count} courses")

print(f"[5/5] Saving to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)

file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"Done! Database generated successfully ({file_size_mb:.2f} MB).")
