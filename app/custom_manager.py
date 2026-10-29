# -*- coding: utf-8 -*-
"""
Custom Drills Manager for WaXueShe Mini
Allows users to paste any English text, textbook article, or dialogues,
automatically converting them into interactive sentence building drills.
"""
import os
import json
import time
import re
from typing import List, Dict, Any, Optional

from app.nlp_chunker import split_raw_text_into_sentences, chunk_sentence, generate_breakdown
from app.ollama_client import chat_with_ollama, select_best_model, get_installed_models

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_DB_PATH = os.path.join(BASE_DIR, "custom_drills.json")

def load_custom_drills() -> List[Dict[str, Any]]:
    if not os.path.exists(CUSTOM_DB_PATH):
        return []
    try:
        with open(CUSTOM_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[CustomManager] Error reading {CUSTOM_DB_PATH}: {e}")
        return []

def persist_custom_drills(drills: List[Dict[str, Any]]) -> bool:
    try:
        with open(CUSTOM_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(drills, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[CustomManager] Error writing {CUSTOM_DB_PATH}: {e}")
        return False

def translate_sentences_batch(sentences: List[str]) -> List[str]:
    """
    Translate English sentences to Simplified Chinese using Ollama in batch.
    """
    if not sentences:
        return []
    
    installed = get_installed_models()
    model = select_best_model(installed) if installed else None
    
    numbered = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])
    prompt = f"""You are an English-Chinese translation expert.
Translate the following English sentences into fluent, natural Simplified Chinese.
Output each numbered line with ONLY the Chinese translation (e.g. '1. ...'):
{numbered}"""

    try:
        res = chat_with_ollama(
            messages=[{"role": "user", "content": prompt}],
            model_name=model
        )
        reply = res.get("reply", "")
        translations = {}
        for line in reply.splitlines():
            line = line.strip()
            match = re.match(r'^(\d+)[\.\、\:\s]+(.+)$', line)
            if match:
                idx = int(match.group(1)) - 1
                translations[idx] = match.group(2).strip()
        
        result = []
        for i, s in enumerate(sentences):
            result.append(translations.get(i, ""))
        return result
    except Exception as e:
        print(f"[CustomManager] Translation batch error: {e}")
        return ["" for _ in sentences]

def generate_drills_from_text(raw_text: str, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse raw text, translate if needed, chunk syntax, and produce ready-to-play drills.
    """
    candidates = split_raw_text_into_sentences(raw_text)
    if not candidates:
        return []
    
    # Identify which need translation
    need_trans_indices = [i for i, (en, zh) in enumerate(candidates) if not zh]
    need_trans_texts = [candidates[i][0] for i in need_trans_indices]
    
    translated_texts = []
    if need_trans_texts:
        translated_texts = translate_sentences_batch(need_trans_texts)
    
    trans_map = dict(zip(need_trans_indices, translated_texts))
    
    tag_name = tag.strip() if tag and tag.strip() else "静静精选课文"
    generated = []
    
    timestamp = int(time.time() * 1000)
    for i, (en, zh) in enumerate(candidates):
        final_zh = zh if zh else trans_map.get(i, "")
        if not final_zh:
            final_zh = f"请朗读并拼写此课文原句"
            
        chunks = chunk_sentence(en)
        breakdown = generate_breakdown(en, final_zh)
        
        drill_obj = {
            "id": f"custom_{timestamp}_{i+1}",
            "category": "custom",
            "category_name": "自定义精选",
            "level_tag": f"{tag_name} · 第 {i+1} 句",
            "chinese": final_zh,
            "english": en,
            "tokens": chunks,
            "breakdown": breakdown,
            "cultural_tip": "静静专属课文精练：点击下方词块按语序拼接，可在答对后点击单词单独练发音。",
            "is_custom": True,
            "created_at": time.strftime("%Y-%m-%d %H:%M")
        }
        generated.append(drill_obj)
        
    return generated

def save_custom_drills(new_drills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = load_custom_drills()
    existing_en = {d.get("english", "").strip().lower() for d in existing}
    
    appended = []
    for d in new_drills:
        if d.get("english", "").strip().lower() not in existing_en:
            existing.append(d)
            appended.append(d)
            existing_en.add(d.get("english", "").strip().lower())
            
    persist_custom_drills(existing)
    return existing

def delete_single_custom_drill(drill_id: str) -> List[Dict[str, Any]]:
    existing = load_custom_drills()
    updated = [d for d in existing if d.get("id") != drill_id]
    persist_custom_drills(updated)
    return updated

def delete_all_custom_drills() -> bool:
    return persist_custom_drills([])
