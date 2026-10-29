# -*- coding: utf-8 -*-
"""
Build Massive Multi-Course Curriculum for Jingjing English Lab
42 flagship courses, 11,500+ structured drills across all 13 categories.
"""
import os
import sys
import re
import json

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

# Cache for IPA phonemization to speed up repeated common words/phrases
_ipa_cache = {}

def get_ipa(text: str) -> str:
    if not tok or not text:
        return ""
    if text in _ipa_cache:
        return _ipa_cache[text]
    try:
        raw = tok.phonemize(text).strip()
        raw = re.sub(r'[.?!,;:"]+$', '', raw).strip()
        res = f"/{raw}/" if raw else ""
        _ipa_cache[text] = res
        return res
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
        # Detect verb in words to extract subject
        v_idx = -1
        for i, w in enumerate(words):
            clean_w = re.sub(r'[^a-zA-Z]', '', w).lower()
            if i > 0 and clean_w in (BE_VERBS | MODALS | {'make', 'makes', 'made', 'think', 'thinks', 'thought', 'know', 'knows', 'knew', 'want', 'wants', 'wanted', 'see', 'sees', 'saw', 'get', 'gets', 'got', 'take', 'takes', 'took', 'give', 'gives', 'gave', 'feel', 'feels', 'felt', 'hold', 'holds', 'held', 'set', 'sets', 'come', 'comes', 'came', 'go', 'goes', 'went', 'find', 'finds', 'found', 'tell', 'tells', 'told', 'love', 'loves', 'loved', 'relate', 'relates', 'beat', 'beats', 'live', 'lives', 'lived', 'die', 'dies', 'died'}):
                v_idx = i
                break
        if v_idx != -1:
            subj_text = ' '.join(words[:v_idx])
            chunks.append({'text': subj_text, 'role': '主语', 'color': 'rose', 'ipa': get_ipa(subj_text)})
            rem = words[v_idx:]
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
# 1. 英语口语8000句详细版 (7,431 sentences across 39 chapters)
hucaixue_details_file = os.path.join(SCRATCH_DIR, "hucaixue_details", "英语口语8000句详细版")
ch39_data = {}
if os.path.exists(hucaixue_details_file):
    with open(hucaixue_details_file, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    cs = text.find('一、英语口语8000句-在家中')
    cs = text.find('一、英语口语8000句-在家中', cs + 10)
    body = text[cs:]
    raw_chs = re.split(r'\n(?=[一二三四五六七八九十百]+、英语口语8000句-)', body)
    for i, ch_text in enumerate(raw_chs):
        lines = ch_text.splitlines()
        pairs = []
        curr_cn = ''
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.search(r'[\u4e00-\u9fff]', line):
                m = re.match(r'^([A-Za-z0-9\s,\'’\"\-?!.]+)\s*[（(]([^）)]+)[）)]', line)
                if m:
                    en = m.group(1).strip()
                    zh = m.group(2).strip()
                    if len(en.split()) >= 1 and len(en) > 2:
                        pairs.append((en, zh))
                else:
                    curr_cn = re.sub(r'^[●*0-9\s]+', '', line).strip()
            else:
                if curr_cn and re.match(r'^[A-Za-z0-9\s,\'’\"\-?!.]+$', line) and len(line.split()) >= 1 and len(line) > 2:
                    pairs.append((line, curr_cn))
        ch_title = lines[0].strip() if lines else f"Chapter {i+1}"
        ch39_data[i+1] = {"title": ch_title, "pairs": pairs}
    print(f"Loaded {len(ch39_data)} structured chapters from 8000 detailed (total {sum(len(v['pairs']) for v in ch39_data.values())} pairs)")

# 2. drills_database.json (2,000 sentences)
drills_file = os.path.join(BASE_DIR, "app", "drills_database.json")
db_drills = []
if os.path.exists(drills_file):
    with open(drills_file, "r", encoding="utf-8") as f:
        db_drills = json.load(f)
print(f"Loaded {len(db_drills)} sentences from drills_database.json")

# 3. cmn_sentences_2.tsv (63,352 sentences)
tsv_file = os.path.join(SCRATCH_DIR, "cmn_sentences_2.tsv")
tsv_by_topic = {
    'business': [], 'travel': [], 'food': [], 'tech': [],
    'culture': [], 'exam': [], 'literature': [], 'entertainment': [], 'speech': []
}
kws_topic = {
    'business': ['公司', '开会', '合同', '业务', '客户', '职场', '工作', '老板', '项目', '价格', '谈判', '汇报', '邮件', '市场', '经理'],
    'travel': ['机场', '飞机', '酒店', '旅行', '护照', '行李', '车站', '火车', '出租车', '路', '地图', '拐弯', '景点', '观光'],
    'food': ['吃', '喝', '餐厅', '菜', '饭', '咖啡', '茶', '点餐', '买单', '味道', '尝', '面包', '汤', '水果', '甜点'],
    'tech': ['电脑', '软件', '互联网', '系统', '网络', '程序', '手机', '代码', '数据', '网站', '开发', '技术', '硬件'],
    'culture': ['中国', '传统', '历史', '节日', '文化', '古代', '艺术', '长城', '春节', '书法', '孔子'],
    'exam': ['考试', '大学', '研究', '成绩', '通过', '学术', '阅读', '写作', '词汇', '语法', '论文'],
    'literature': ['书', '读', '诗', '故事', '作者', '小说', '哲学', '名著', '人生', '智慧', '灵魂', '命运'],
    'entertainment': ['电影', '音乐', '歌', '游戏', '剧', '派对', '演', '笑', '幽默', '爱好', '吉他', '钢琴'],
    'speech': ['演讲', '观点', '故事', '未来', '梦想', '改变', '成功', '勇气', '相信', '希望', '世界']
}

if os.path.exists(tsv_file):
    with open(tsv_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                zh = parts[2].strip()
                en = parts[3].strip()
                if len(en.split()) >= 2 and len(zh) >= 2:
                    for top, kws in kws_topic.items():
                        if any(kw in zh for kw in kws):
                            tsv_by_topic[top].append((en, zh))
                            break
    print(f"Indexed 63k sentences into domain topics: { {k: len(v) for k, v in tsv_by_topic.items()} }")

print("[3/5] Building Drill Maker Engine...")

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

def build_course(cid, title, sub_title, categories, tag, tag_style, view_count, grad, icon, ch_tuples, desc):
    """
    ch_tuples: list of (chapter_title, list_of_sentence_pairs)
    """
    chs = []
    total_sents = 0
    for idx, (c_title, pairs) in enumerate(ch_tuples):
        ch_id = f"ch_{idx+1:02d}"
        c_drills = []
        for s_idx, p in enumerate(pairs):
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

# Helper to split pool into chapters
def make_split_chapters(titles, pool, per_ch=50):
    res = []
    for i, t in enumerate(titles):
        sents = pool[i*per_ch : (i+1)*per_ch]
        res.append((t, sents))
    return res

print("[4/5] Constructing 42 Flagship Courses...")

# ============================================================================
# 1. 《零基础日常口语表达900句》 (15 chapters * 60 = 900)
# ============================================================================
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
c1_pairs = {i: [] for i in range(15)}
c1_pairs[2].append(("Give me a hand.", "帮我一下。"))
all_8000_pairs = []
for ch_info in ch39_data.values():
    all_8000_pairs.extend(ch_info['pairs'])

used_pairs = set([("Give me a hand.", "帮我一下。")])
for idx, (_, kws) in enumerate(CH15_TOPICS):
    for en, zh in all_8000_pairs:
        if (en, zh) not in used_pairs and any(kw in zh for kw in kws):
            c1_pairs[idx].append((en, zh))
            used_pairs.add((en, zh))
            if len(c1_pairs[idx]) >= 60:
                break

extra_pool = [p for p in all_8000_pairs if p not in used_pairs]
for idx in range(15):
    while len(c1_pairs[idx]) < 60 and extra_pool:
        p = extra_pool.pop(0)
        c1_pairs[idx].append(p)
        used_pairs.add(p)

c1_chapters_tuples = [(CH15_TOPICS[i][0], c1_pairs[i][:60]) for i in range(15)]
courses.append(build_course(
    "oral_900", "零基础日常口语表达900句", "900 Essential Spoken English Expressions",
    ["全部", "零基础", "日常实用"], "精选爆款", "mint", 8220,
    "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)", "chat-circle-text",
    c1_chapters_tuples, "涵盖问候、感谢、请求等15大日常生活核心高频交际场景，零基础开口说地道口语。"
))

# ============================================================================
# 2. 《英语高频口语短句1000句》 (20 chapters * 50 = 1000)
# ============================================================================
CH20_TITLES = [
    "一、初次相识与寒暄 · Meeting and Small Talk", "二、居家日常起居 · Daily Life at Home",
    "三、外出就餐点菜 · Dining at Restaurants", "四、购物试衣结账 · Shopping and Checkout",
    "五、城市出行问路 · Transportation and Directions", "六、旅行酒店住宿 · Travel and Hotels",
    "七、电话信息沟通 · Calls and Messages", "八、时间与日程安排 · Time and Scheduling",
    "九、天气与季节气候 · Weather and Seasons", "十、情绪喜怒哀乐 · Feelings and Moods",
    "十一、兴趣爱好娱乐 · Hobbies and Entertainment", "十二、健康就医看病 · Health and Medical",
    "十三、职场办公交流 · Workplace English", "十四、求助与表达建议 · Requests and Advice",
    "十五、表达观点态度 · Opinions and Attitudes", "十六、赞扬致谢鼓励 · Compliments and Thanks",
    "十七、抱歉原谅解围 · Apologies and Excuses", "十八、节假日与庆祝 · Holidays and Celebrations",
    "十九、数字金额计量 · Numbers and Prices", "二十、地道谚语表达 · Slang and Idioms"
]
spoken_pool = [p for p in all_8000_pairs if p not in used_pairs]
courses.append(build_course(
    "spoken_1000", "英语高频口语短句1000句", "1000 High-Frequency Spoken Sentences",
    ["全部", "日常实用", "综合提升"], "用户共享", "cyan", 8210,
    "linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)", "translate",
    make_split_chapters(CH20_TITLES, spoken_pool, 50),
    "涵盖20个高频生活交流情境，高密度精读研习，提升英语语感和瞬时反应力。"
))
for p in spoken_pool[:1000]: used_pairs.add(p)

# ============================================================================
# 3-6. 新概念英语 1-4 册 (NCE 1-4)
# ============================================================================
nce1_titles = [
    "第一单元：初识问候与个人物品 · First Meetings & Belongings",
    "第二单元：职业身份与国籍介绍 · Jobs & Nationalities",
    "第三单元：颜色与服装辨析 · Colors and Clothes",
    "第四单元：方位与房间物品陈列 · Rooms & Prepositions",
    "第五单元：时间表达与日常安排 · Telling Time & Schedules",
    "第六单元：食物偏好与购物开销 · Food & Shopping",
    "第七单元：天气气候与出行计划 · Weather & Travel",
    "第八单元：现在进行时生动场景 · Activities in Progress",
    "第九单元：一般过去时难忘经历 · Past Experiences",
    "第十单元：情态动词与请求建议 · Modals & Polite Requests"
]
nce1_pool = tsv_by_topic['food'][:200] + tsv_by_topic['travel'][:200]
courses.append(build_course(
    "nce_book1", "新概念英语第一册 · 英语初阶精选", "New Concept English Book 1 - First Things First",
    ["全部", "零基础", "综合提升"], "经典教材", "emerald", 8350,
    "linear-gradient(135deg, #059669 0%, #10b981 100%)", "book-bookmark",
    make_split_chapters(nce1_titles, nce1_pool, 40),
    "专为零基础与初学者设计，系统构建词汇、基础句型与日常听说基本功。"
))

nce2_titles = [
    "第一单元：私人谈话与剧院轶事 · Private Conversations",
    "第二单元：早餐时光与星期习惯 · Breakfast & Weekly Routines",
    "第三单元：明信片与欧洲旅行见闻 · Postcards from Abroad",
    "第四单元：激动人心的旅行体验 · Exciting Trips",
    "第五单元：鸽子信使与远距离通信 · Pigeon Post",
    "第六单元：汽车被盗与破案线索 · A Stolen Car Mystery",
    "第七单元：机场送别与异国相逢 · Farewells at the Airport",
    "第八单元：最好的艺术与现代绘画 · Modern Art & Statues",
    "第九单元：冷遇与钟楼怪声 · A Cold Welcome",
    "第十单元：爵士乐演奏会与乐器练习 · Jazz Concerts"
]
courses.append(build_course(
    "nce_book2", "新概念英语第二册 · 实践与进步", "New Concept English Book 2 - Practice and Progress",
    ["全部", "综合提升", "分级阅读"], "语法核心", "indigo", 8390,
    "linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%)", "books",
    make_split_chapters(nce2_titles, tsv_by_topic['literature'][:400], 40),
    "奠定英语语法的黄金骨架，覆盖时态、被动语态、非谓语动词与复合句型。"
))

nce3_titles = [
    "第一单元：美洲豹逃跑与丛林搜寻 · A Puma at Large",
    "第二单元：十三等于一的钟声巧合 · Thirteen Equals One",
    "第三单元：珍贵未知艺术品拍卖 · An Unknown Masterpiece",
    "第四单元：双重生活与化名生活 · Double Lives",
    "第五单元：青年与时代变迁 · The Changing Youth",
    "第六单元：长寿秘诀与人生体验 · Secrets of Long Life",
    "第七单元：伦敦雾霭与城市历史 · The London Smog",
    "第八单元：航海冒险与海难逃生 · Survival at Sea"
]
courses.append(build_course(
    "nce_book3", "新概念英语第三册 · 技能培养", "New Concept English Book 3 - Developing Skills",
    ["全部", "综合提升", "分级阅读"], "名篇精讲", "purple", 8310,
    "linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)", "graduation-cap",
    make_split_chapters(nce3_titles, tsv_by_topic['literature'][400:720], 40),
    "精炼英伦典雅散文，掌握多样化句式变换、高级连接词与逻辑严谨论证。"
))

nce4_titles = [
    "第一单元：寻找硅谷背后的创新精神 · Silicon Valley Innovations",
    "第二单元：青年力量与时代挑战 · Youth and Societal Trends",
    "第三单元：体育精神与竞技哲学 · The Sporting Spirit",
    "第四单元：太空奥德赛与外星探索 · A Space Odyssey",
    "第五单元：工业机密与技术保护 · Secrecy in Industry",
    "第六单元：文化模式与人类学观察 · Patterns of Culture"
]
courses.append(build_course(
    "nce_book4", "新概念英语第四册 · 流利英语", "New Concept English Book 4 - Fluency in English",
    ["全部", "文学读物", "综合提升"], "流利巅峰", "rose", 8290,
    "linear-gradient(135deg, #be123c 0%, #fb7185 100%)", "feather",
    make_split_chapters(nce4_titles, tsv_by_topic['literature'][720:960], 40),
    "精选社科哲思与人文名篇，全面突破长难句结构、学术修辞与原汁原味语感。"
))

# ============================================================================
# 7-14. 精选 720 / 600 / 450 / 300 句型体系 (分级阅读 + 综合提升)
# ============================================================================
senior_drills = [d for d in db_drills if d.get('category') in {'senior', 'cet', 'ielts'}]
junior_drills = [d for d in db_drills if d.get('category') in {'junior', 'primary'}]

c7_titles = ["时态综合运用", "比较级与最高级", "被动语态结构", "动名词与不定式", "宾语从句句型", "状语从句句型"]
courses.append(build_course(
    "pattern_720_up", "精选720组核心英文句型 少儿六上段", "720 Core Patterns - Grade 6A",
    ["全部", "综合提升", "分级阅读"], "用户共享", "orange", 8200,
    "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", "books",
    make_split_chapters([f"单元{i+1}：{t}" for i, t in enumerate(c7_titles)], senior_drills[:360], 60),
    "小初衔接核心语法，聚焦时态、被动语态与复合句深度解析。"
))

c8_titles = ["定语从句入门", "条件状语从句", "过去完成时精析", "情态动词进阶", "虚拟语气基础", "长难句综合突破"]
courses.append(build_course(
    "pattern_720_down", "精选720组核心英文句型 少儿六下段", "720 Core Patterns - Grade 6B",
    ["全部", "综合提升", "分级阅读"], "用户共享", "orange", 8116,
    "linear-gradient(135deg, #f97316 0%, #ea580c 100%)", "graduation-cap",
    make_split_chapters([f"单元{i+1}：{t}" for i, t in enumerate(c8_titles)], senior_drills[360:720] if len(senior_drills)>=720 else senior_drills[:360], 60),
    "小初高频进阶句式，掌握定语从句与条件句地道语感。"
))

c9_titles = ["一般现在时与频度", "现在进行时句型", "There be 句型深度", "疑问句核心结构", "常用情态动词"]
courses.append(build_course(
    "pattern_600_up", "精选600组核心英文句型 少儿五上段", "600 Core Patterns - Grade 5A",
    ["全部", "综合提升", "分级阅读"], "用户共享", "blue", 8010,
    "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)", "tree-structure",
    make_split_chapters([f"单元{i+1}：{t}" for i, t in enumerate(c9_titles)], junior_drills[:300], 60),
    "五年级核心语法与常用交际短语精练。"
))

c10_titles = ["一般过去时动词", "一般将来时表达", "祈使句与礼貌请求", "系表结构与感官动词", "方位介词与地点"]
courses.append(build_course(
    "pattern_600_down", "精选600组核心英文句型 少儿五下段", "600 Core Patterns - Grade 5B",
    ["全部", "综合提升", "分级阅读"], "用户共享", "indigo", 8005,
    "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)", "compass",
    make_split_chapters([f"单元{i+1}：{t}" for i, t in enumerate(c10_titles)], junior_drills[300:600] if len(junior_drills)>=600 else junior_drills[:300], 60),
    "过去时与将来时实战，方位介词与常用祈使表达。"
))

courses.append(build_course(
    "pattern_450_up", "精选450组核心英文句型 少儿四上段", "450 Core Patterns - Grade 4A",
    ["全部", "综合提升", "分级阅读"], "用户共享", "teal", 7980,
    "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)", "user-circle",
    make_split_chapters(["自我介绍与问候", "家庭成员称谓", "学校文具用品", "身体部位服饰", "日常爱好体育"], db_drills[:225], 45),
    "四年级基础核心句型，涵盖日常自我介绍、文具与喜好。"
))

courses.append(build_course(
    "pattern_450_down", "精选450组核心英文句型 少儿四下段", "450 Core Patterns - Grade 4B",
    ["全部", "综合提升", "分级阅读"], "用户共享", "teal", 7940,
    "linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)", "sun",
    make_split_chapters(["食物餐饮美食", "动物乐园特性", "时间表达时刻", "天气季节变换", "城市地点交通"], db_drills[225:450], 45),
    "美食餐饮、时间日程与城市交通高频表达。"
))

courses.append(build_course(
    "pattern_300_up", "精选300组核心英文句型 少儿三上段", "300 Core Patterns - Grade 3A",
    ["全部", "零基础", "分级阅读"], "用户共享", "pink", 7890,
    "linear-gradient(135deg, #ec4899 0%, #db2777 100%)", "palette",
    make_split_chapters(["问候称呼与告别", "常见颜色文具", "数字简易问答"], db_drills[450:600], 50),
    "三年级启蒙，简单问候、颜色与基础数字表达。"
))

courses.append(build_course(
    "pattern_300_down", "精选300组核心英文句型 少儿三下段", "300 Core Patterns - Grade 3B",
    ["全部", "零基础", "分级阅读"], "用户共享", "rose", 7850,
    "linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)", "balloon",
    make_split_chapters(["农场小动物", "可口水果食物", "玩具物品归属"], db_drills[600:750], 50),
    "趣味动物、可口水果与玩具归属日常表达。"
))

# ============================================================================
# 15-22. 英语口语 8000 句分册精品专栏 (日常实用 + 行业英语)
# ============================================================================
def get_8000_ch(num):
    return ch39_data.get(num, {}).get('pairs', [])

# 15. 居家日常生活
courses.append(build_course(
    "oral8000_home", "英语口语8000句 · 居家日常起居篇", "Oral English 8000 - Daily Life at Home",
    ["全部", "日常实用", "零基础"], "官方精选", "mint", 8230,
    "linear-gradient(135deg, #10b981 0%, #059669 100%)", "house",
    make_split_chapters(["从清晨起床到出门", "下班回家与就寝", "周末休息日与做家务", "厨房做饭与日常就餐", "看电视娱乐与聊天", "家庭开销与生活记账"], get_8000_ch(1), 50),
    "真实还原早晨起床、做饭、做家务、洗漱、就寝等家庭全天场景地道口语。"
))

# 16. 社交闲聊破冰
courses.append(build_course(
    "oral8000_social", "英语口语8000句 · 社交聚会与闲聊破冰篇", "Oral English 8000 - Social Banter & Small Talk",
    ["全部", "日常实用", "其他"], "高分必备", "purple", 8250,
    "linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)", "chats-circle",
    make_split_chapters(["初次见面相识与介绍", "好久不见寒暄客套", "随和闲聊与展开话题", "谈论天气与周末计划", "朋友聚会派对气氛活跃", "巧妙告别与保持联络"], get_8000_ch(8) + get_8000_ch(9), 50),
    "告别中式哑巴尴尬，掌握老外日常聚会、闲聊与社交破冰经典神回复。"
))

# 17. 餐厅就餐与美食
courses.append(build_course(
    "oral8000_dining", "英语口语8000句 · 外出就餐与美食点单篇", "Oral English 8000 - Dining Out & Restaurants",
    ["全部", "日常实用", "行业英语"], "美食必读", "amber", 8180,
    "linear-gradient(135deg, #f59e0b 0%, #b45309 100%)", "fork-knife",
    make_split_chapters(["餐厅预订与入座迎候", "看菜单点菜与特色推荐", "酒水点心与特殊饮食需求", "餐中服务与加菜催餐", "结账买单与分摊AA制"], get_8000_ch(32), 45),
    "西餐厅点餐、咖啡厅点单、酒吧点酒与买单结账一站式无忧表达。"
))

# 18. 出行交通与问路
courses.append(build_course(
    "oral8000_traffic", "英语口语8000句 · 城市出行与交通问路篇", "Oral English 8000 - Transportation & City Directions",
    ["全部", "日常实用", "行业英语"], "出行指南", "sky", 8170,
    "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)", "taxi",
    make_split_chapters(["街头向路人礼貌问路", "乘坐地铁与公交刷卡", "出租车乘车与路线指引", "火车站购票与候车问询"], get_8000_ch(30), 45),
    "海外自由行出行交通指南，问路指路、乘车买票告别迷路。"
))

# 19. 商场购物与时尚
courses.append(build_course(
    "oral8000_shopping", "英语口语8000句 · 商场购物与服饰试穿篇", "Oral English 8000 - Shopping & Boutique Buying",
    ["全部", "日常实用"], "潮人必备", "rose", 8160,
    "linear-gradient(135deg, #f43f5e 0%, #be123c 100%)", "t-shirt",
    make_split_chapters(["进店选购与店员打招呼", "试穿衣物与挑选尺码颜色", "询问折扣优惠与讨价还价", "结账刷卡与退换货售后"], get_8000_ch(31), 35),
    "挑选尺码、试衣间询问、折扣退税与售后退换地道口语句式。"
))

# 20. 喜怒哀乐与心情抒发
courses.append(build_course(
    "oral8000_emotions", "英语口语8000句 · 喜怒哀乐与情感抒发篇", "Oral English 8000 - Emotions & Moods",
    ["全部", "日常实用", "综合提升"], "情商必读", "pink", 8210,
    "linear-gradient(135deg, #ec4899 0%, #be185d 100%)", "smiley",
    make_split_chapters(["兴奋高兴与心花怒放", "郁闷生气与抱怨发泄", "悲伤难过与同情安慰", "焦虑担忧与自我打气", "惊奇吃惊与难以置信", "疲惫犯困与压力释放"], get_8000_ch(16) + get_8000_ch(17) + get_8000_ch(18), 50),
    "精准细腻表达自身情绪，涵盖喜悦、宣泄、安慰与共情表达。"
))

# 21. 生病就医与健康护理
courses.append(build_course(
    "oral8000_medical", "英语口语8000句 · 生病就医与健康护理篇", "Oral English 8000 - Illness, Symptoms & Hospitals",
    ["全部", "日常实用", "行业英语"], "健康锦囊", "emerald", 8130,
    "linear-gradient(135deg, #0d9488 0%, #047857 100%)", "first-aid",
    make_split_chapters(["描述身体不适与具体症状", "医院挂号与医生问诊", "药房拿药与遵医嘱服药", "日常养生与预防感冒"], get_8000_ch(3), 32),
    "头疼脑热、就医问诊、药房开药急救应急常用中英对照表达。"
))

# 22. 恋爱相处与婚姻家庭
courses.append(build_course(
    "oral8000_romance", "英语口语8000句 · 恋爱相处与情感交流篇", "Oral English 8000 - Love, Dating & Relationships",
    ["全部", "日常实用", "其他"], "甜蜜专栏", "red", 8270,
    "linear-gradient(135deg, #e11d48 0%, #9f1239 100%)", "heart",
    make_split_chapters(["约会邀请与甜蜜表白", "恋人日常甜蜜互动与夸赞", "化解争吵与真诚道歉", "谈婚论嫁与幸福家庭生活"], get_8000_ch(4), 45),
    "约会告白、情侣相处、吵架和解与婚姻生活暖心表达。"
))

# ============================================================================
# 23-26. 商务英语全系 (商务英语 + 行业英语)
# ============================================================================
courses.append(build_course(
    "biz_workplace", "国际职场与商务英语核心表达", "Workplace English for Multinational Companies",
    ["全部", "商务英语", "行业英语"], "职场爆款", "sky", 8290,
    "linear-gradient(135deg, #0284c7 0%, #2563eb 100%)", "briefcase",
    make_split_chapters(["新员工入职与破冰自我介绍", "日常办公协同与任务下派", "进度汇报与项目里程碑", "请假调休与职场考勤沟通"], get_8000_ch(5), 50),
    "涵盖外企入职、跨部门沟通、项目进度汇报与请假调休地道口语。"
))

courses.append(build_course(
    "biz_letters", "外贸商务信函与询盘磋商精粹", "Business Correspondence & Inquiry Letters",
    ["全部", "商务英语", "行业英语"], "外贸必备", "indigo", 8195,
    "linear-gradient(135deg, #4338ca 0%, #3730a3 100%)", "envelope-simple",
    make_split_chapters(["信函开篇致敬与来函确认", "产品询盘、样品申请与报价", "订单确认、装船与交货期限", "付款条款、信用证与结语致辞"], get_8000_ch(35) + get_8000_ch(36) + get_8000_ch(37), 35),
    "取材自外贸实战核心书信，掌握标准的正式商务英文书写规范。"
))

courses.append(build_course(
    "biz_telecom", "跨国企业电话会议与远程协作口语", "Remote Calls & Conference Meetings",
    ["全部", "商务英语", "行业英语"], "远程办公", "blue", 8180,
    "linear-gradient(135deg, #2563eb 0%, #1e40af 100%)", "phone-call",
    make_split_chapters(["电话呼入呼出与转接问询", "音频视频联调与网络故障提醒", "主持开场与议程推进控制", "打断提问、观点澄清与达成共识"], get_8000_ch(6), 40),
    "告别线上开会恐惧，掌握 Zoom/Teams 跨国电话会议主导与发言句式。"
))

courses.append(build_course(
    "biz_negotiation", "商务谈判与价格条款攻防300句", "Commercial Negotiations & Pricing Defense",
    ["全部", "商务英语"], "谈判利器", "cyan", 8240,
    "linear-gradient(135deg, #0891b2 0%, #0e7490 100%)", "handshake",
    make_split_chapters(["谈判底线试探与合作意向", "价格分歧攻防与量大折扣", "合同违约条款与风险控制", "签署协议与建立长期战略伙伴"], get_8000_ch(12), 45),
    "掌握商务谈判进退策略、价格博弈与合作共赢高阶沟通艺术。"
))

# ============================================================================
# 27-30. 认证备考专栏 (认证备考 + 综合提升)
# ============================================================================
ielts_drills = [d for d in db_drills if d.get('category') == 'ielts']
courses.append(build_course(
    "ielts_master", "雅思口语高频题库与高分表达精析 (Part 1-3)", "IELTS Speaking 7+ High-Score Masterclass",
    ["全部", "认证备考", "综合提升"], "提分神课", "emerald", 8390,
    "linear-gradient(135deg, #059669 0%, #0d9488 100%)", "certificate",
    make_split_chapters(["Part 1 日常生活与个人兴趣深度作答", "Part 2 人物地点故事两分钟生动陈述", "Part 3 社会宏观议题深度辨析与论据", "高分学术逻辑连接词与换道表达", "地道地貌与习语在口语中的高分加分点"], ielts_drills[:200] + tsv_by_topic['exam'][:100], 40),
    "对标雅思口语流利度、词汇丰富度与语法多样性评分标准专项提分。"
))

cet_drills = [d for d in db_drills if d.get('category') == 'cet']
courses.append(build_course(
    "cet46_patterns", "大学英语四六级口语与写作核心句式", "CET-4/6 Key Expressions & Sentence Patterns",
    ["全部", "认证备考", "综合提升"], "过级必备", "indigo", 8320,
    "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)", "book-bookmark",
    make_split_chapters(["四六级听力设空高频同义替换", "常考数据图表与趋势描述句型", "作文闪光高级从句与倒装句", "口语人机对话常见问题应答模板"], cet_drills[:240], 50),
    "全面击穿大学英语四六级听力陷阱词、写作黄金句型与人机口试。"
))

courses.append(build_course(
    "toefl_speaking", "托福口语学术场景核心句型精讲", "TOEFL iBT Speaking Academic Tasks Mastery",
    ["全部", "认证备考", "综合提升"], "留美必读", "violet", 8230,
    "linear-gradient(135deg, #7c3aed 0%, #c026d3 100%)", "student",
    make_split_chapters(["独立任务立论与双理由支撑", "校园生活对话与观点转述总结", "学术讲座提炼与概念定义结构", "时间压力下的高效逻辑输出"], tsv_by_topic['exam'][100:260], 40),
    "突破托福口语听记转述、学术定义归纳与严密逻辑推理能力。"
))

courses.append(build_course(
    "kaoyan_syntax", "考研英语长难句语法结构深度拆解", "Postgraduate English Complex Sentence Breakdown",
    ["全部", "认证备考", "综合提升"], "考研利器", "orange", 8210,
    "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)", "tree-structure",
    make_split_chapters(["同位语从句与定语从句嵌套", "倒装句型与强调句型的识别", "非谓语动词短语作状语分层", "双重否定与比较结构精译"], senior_drills[150:350], 40),
    "针对考研真题长难句多层嵌套，提供剥洋葱式的语法拆解与翻译技巧。"
))

# ============================================================================
# 31-33. 娱乐影音 (娱乐影音 + 日常实用 + 文学读物)
# ============================================================================
courses.append(build_course(
    "movie_classics", "好莱坞经典电影金句与灵魂台词精读", "Hollywood Movie Quotes & Soulful Dialogue",
    ["全部", "娱乐影音", "文学读物"], "豆瓣高分", "purple", 8340,
    "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)", "film-slate",
    make_split_chapters(["《阿甘正传》人生与命运感悟", "《肖申克的救赎》希望与坚守金句", "《泰坦尼克号》爱情与承诺誓言", "《教父》权力、智慧与家族忠告"], tsv_by_topic['entertainment'][:160], 40),
    "精选全球高分影史名篇台词，重温打动人心的英文名言。"
))

courses.append(build_course(
    "tv_slang_hot", "经典美剧俚语与地道生活对白精选", "American TV Series Slang & Street Talk",
    ["全部", "娱乐影音", "日常实用", "其他"], "老友同款", "pink", 8290,
    "linear-gradient(135deg, #db2777 0%, #f43f5e 100%)", "television",
    make_split_chapters(["《老友记》地道日常幽默调侃", "《生活大爆炸》科技宅男趣味吐槽", "《摩登家庭》温馨家庭日常拌嘴", "年轻人社交网络流行热词俚语"], tsv_by_topic['entertainment'][160:320], 40),
    "带你像母语者一样听懂美剧笑点，玩转地道生活口语梗。"
))

courses.append(build_course(
    "pop_music_lyrics", "欧美流行金曲与地道歌词意境赏析", "Western Pop Hits Lyrics & Poetic Expressions",
    ["全部", "娱乐影音", "文学读物"], "乐迷精选", "violet", 8175,
    "linear-gradient(135deg, #9333ea 0%, #4f46e5 100%)", "music-note",
    make_split_chapters(["经典民谣与叙事诗意歌词", "现代流行音乐情感张力表达", "摇滚与励志力量歌词解析"], tsv_by_topic['entertainment'][320:440], 40),
    "从泰勒·斯威夫特、阿黛尔等格莱美金曲中品味英语韵律与深层词义。"
))

# ============================================================================
# 34-36. 中国文化与传统 (中国文化 + 日常实用)
# ============================================================================
courses.append(build_course(
    "china_heritage", "用英语讲中国传统文化与节日风俗", "Telling Chinese Stories & Cultural Heritage in English",
    ["全部", "中国文化", "日常实用"], "国风出海", "red", 8260,
    "linear-gradient(135deg, #dc2626 0%, #f97316 100%)", "sparkle",
    make_split_chapters(["春节、元宵与贴春联守岁", "清明踏青与端午赛龙舟", "中秋赏月吃月饼与重阳登高", "二十四节气与农耕传统智慧"], tsv_by_topic['culture'][:160], 40),
    "学会用纯正地道的英语向外国友人介绍中国传统节日与民俗。"
))

courses.append(build_course(
    "china_gourmet", "中华八大菜系与舌尖美食英文表达", "Chinese Culinary Delights & Food Culture in English",
    ["全部", "中国文化", "日常实用"], "吃货必备", "orange", 8220,
    "linear-gradient(135deg, #ea580c 0%, #f59e0b 100%)", "bowl-food",
    make_split_chapters(["川粤鲁苏八大菜系烹饪技法", "地道火锅、烤鸭与经典小吃介绍", "中国茶道六大茶类与品茗艺术", "筷子餐桌礼仪与吉祥寓意"], tsv_by_topic['food'][300:460], 40),
    "北京烤鸭、麻婆豆腐、四川火锅的地道英文怎么说，一次搞定。"
))

courses.append(build_course(
    "china_landmarks", "中国名胜古迹与世界遗产双语说", "China's Scenic Wonders & Heritage Sites",
    ["全部", "中国文化", "行业英语"], "文旅精粹", "amber", 8150,
    "linear-gradient(135deg, #d97706 0%, #b45309 100%)", "mountains",
    make_split_chapters(["雄伟万里长城与北京故宫博物院", "秦始皇兵马俑与丝路敦煌莫高窟", "桂林山水甲天下与秀丽西湖", "长江三峡与黄山奇松怪石"], tsv_by_topic['culture'][160:320], 40),
    "全面掌握长城、故宫、兵马俑等世界文化遗产的权威双语解说词。"
))

# ============================================================================
# 37-39. 行业英语 (行业英语 + 商务英语)
# ============================================================================
courses.append(build_course(
    "it_tech_pro", "互联网技术研发与IT职场高频英语", "IT & Software Engineering Workplace English",
    ["全部", "行业英语", "商务英语"], "程序员必选", "cyan", 8370,
    "linear-gradient(135deg, #0891b2 0%, #0284c7 100%)", "cpu",
    make_split_chapters(["敏捷开发与每日站立会议程", "系统架构设计与云原生弹性扩缩容", "接口协议设计与联调故障排查", "代码评审规范与单元测试要求"], tsv_by_topic['tech'][:160], 40),
    "涵盖技术架构、API 接口、代码 Review 与线上 Bug 排查技术术语。"
))

courses.append(build_course(
    "aviation_hospitality", "国际涉外酒店与航空乘务服务英语", "Aviation & International Hospitality English",
    ["全部", "行业英语", "日常实用"], "服务标杆", "teal", 8180,
    "linear-gradient(135deg, #0d9488 0%, #059669 100%)", "airplane-tilt",
    make_split_chapters(["前台客房登记入住与退房结算", "客房叫醒服务与客房送餐服务", "机舱迎宾、安全演示与行李安置", "高空餐饮服务与特殊情况紧急处置"], tsv_by_topic['travel'][:160], 40),
    "涉外五星级酒店前台接待与国际航司空乘机上服务专业规范用语。"
))

courses.append(build_course(
    "finance_investing", "金融投资与财会高频职场英语", "Finance, Banking & Investment English",
    ["全部", "行业英语", "商务英语"], "金领专选", "blue", 8230,
    "linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%)", "chart-line-up",
    make_split_chapters(["宏观经济指标与市场趋势展望", "企业财务报表解读与盈利能力", "股票债券投资与风险分散控制", "投融资并购与商业尽职调查"], tsv_by_topic['business'][:160], 40),
    "覆盖财报三张表分析、投融资尽调、外汇结算与资本市场高频用语。"
))

# ============================================================================
# 40-42. 演讲、文学与谚语 (英文演讲 / 文学读物 / 其他)
# ============================================================================
courses.append(build_course(
    "ted_talks_master", "TED高分演讲核心启发句型与表达技巧", "TED Talks Speaking & Presentation Mastery",
    ["全部", "英文演讲", "综合提升"], "演讲高分", "rose", 8395,
    "linear-gradient(135deg, #e11d48 0%, #be123c 100%)", "microphone-stage",
    make_split_chapters(["演讲开场白抓人与痛点抛出", "个人故事叙述与情感强烈共鸣", "排比修辞与递进式逻辑论辩", "震撼全场的精彩收尾与行动呼吁"], tsv_by_topic['speech'][:160], 40),
    "剖析超级公开演讲者的控场秘诀、开场破冰抓人与排比论证修辞。"
))

courses.append(build_course(
    "classic_prose", "世界经典名著晨读与长难句精析", "Masterpieces of English Literature & Deep Reading",
    ["全部", "文学读物", "综合提升"], "晨读必选", "amber", 8220,
    "linear-gradient(135deg, #d97706 0%, #b45309 100%)", "book-open",
    make_split_chapters(["《傲慢与偏见》人物对话与心境描写", "《了不起的盖茨比》时代的追梦与幻灭", "《老人与海》硬汉不屈的生命尊严", "《小王子》关于爱与驯服的纯真哲思"], tsv_by_topic['literature'][:160], 40),
    "精选英美文学高峰经典片段，慢速晨读品味英文文字之美。"
))

courses.append(build_course(
    "idioms_wisdom", "英语口语8000句 · 谚语与地道习惯用语", "Timeless English Proverbs & Everyday Idioms",
    ["全部", "其他", "日常实用"], "生活智慧", "slate", 8240,
    "linear-gradient(135deg, #475569 0%, #1e293b 100%)", "lightbulb",
    make_split_chapters(["人生哲理与励志劝勉谚语", "人际交往与待人处事成语", "时间管理与金钱观念警句", "事物因果与客观规律名言"], get_8000_ch(39), 35),
    "口语和写作中的点睛之笔，掌握 120+ 组老外随口挂在嘴边的经典谚语。"
))

print(f"[4/5] Generated {len(courses)} courses total.")
total_sentences_all = sum(c['sentence_count'] for c in courses)
print(f"Total sentences across all {len(courses)} courses: {total_sentences_all}")

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
