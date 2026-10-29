# -*- coding: utf-8 -*-
"""
NLP Chunker & Sentence Processor for WaXueShe Mini
Splits sentences into natural grammatical tokens and builds structured breakdowns.
"""
import re

PREPS = {'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by', 'about', 'under', 'over', 'into', 'after', 'before', 'through', 'between'}
CONJS = {'and', 'but', 'or', 'so', 'because', 'although', 'if', 'when', 'while', 'that', 'which', 'who', 'where', 'as', 'since', 'though'}

def chunk_sentence(sentence: str):
    """
    Split an English sentence into 2-5 syntactic chunks (tokens) for puzzle assembly.
    """
    words = sentence.strip().split()
    if not words:
        return []
    if len(words) <= 2:
        return words
    if len(words) <= 4:
        if len(words) == 3:
            return [words[0] + ' ' + words[1], words[2]]
        elif len(words) == 4:
            return [words[0] + ' ' + words[1], words[2] + ' ' + words[3]]
        else:
            return words
    
    chunks = []
    current = [words[0]]
    for i in range(1, len(words)):
        w_lower = words[i].lower().strip(',.?!;:\'\"')
        has_comma = words[i-1].endswith(',')
        is_split_word = w_lower in PREPS or w_lower in CONJS
        
        # Split conditions: comma, or prep/conj with sufficient remaining words, or current chunk already has 3 words
        if has_comma or (len(current) >= 2 and is_split_word and len(words) - i >= 2) or (len(current) >= 3 and len(words) - i >= 2):
            chunks.append(' '.join(current))
            current = [words[i]]
        else:
            current.append(words[i])
    if current:
        chunks.append(' '.join(current))
    
    while len(chunks) > 5:
        chunks[-2] = chunks[-2] + ' ' + chunks[-1]
        chunks.pop()
    return chunks

def generate_breakdown(en: str, zh: str = "") -> str:
    """
    Generate grammar component breakdown.
    """
    words = en.strip().split()
    if len(words) <= 3:
        return f"{words[0]} [主谓结构] + {' '.join(words[1:])} [宾语/表语成分]"
    return f"{words[0]} [主语/句首提示] + {' '.join(words[1:3])} [核心动词/谓语短语] + {' '.join(words[3:])} [宾语与状语补充]"

def split_raw_text_into_sentences(text: str):
    """
    Parse multiline or paragraph text into separate candidate sentences.
    Supports English + Chinese on same line or pure English paragraphs.
    """
    lines = text.strip().splitlines()
    candidates = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line contains both English and Chinese
        # e.g., "The early bird catches the worm. 早起的鸟儿有虫吃。"
        # or "Practice makes perfect (熟能生巧)"
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', line))
        
        if has_chinese:
            # Try to separate English and Chinese
            match = re.search(r'([A-Za-z0-9\s,\'’\"\-?!.]+)([\u4e00-\u9fff\s，。！？（）()]+)', line)
            if match and len(match.group(1).split()) >= 3:
                en = match.group(1).strip()
                zh = match.group(2).strip().strip('()（）')
                candidates.append((en, zh))
                continue
                
        # Pure English or sentence splitting by punctuation
        # Split by . ! ? while preserving punctuation
        sentences = re.split(r'(?<=[.!?])\s+', line)
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            # If still has Chinese mixed at end
            m_cn = re.search(r'[\u4e00-\u9fff]', s)
            if m_cn:
                parts = re.split(r'(?<=[\u4e00-\u9fff])\s+|(?<=[.!?])\s+(?=[\u4e00-\u9fff])', s)
                if len(parts) >= 2:
                    en_part = [p for p in parts if re.search(r'[a-zA-Z]{2,}', p)]
                    zh_part = [p for p in parts if re.search(r'[\u4e00-\u9fff]', p)]
                    if en_part and zh_part:
                        candidates.append((' '.join(en_part).strip(), ' '.join(zh_part).strip()))
                        continue
            
            # Pure English sentence
            words = s.split()
            if len(words) >= 3:
                candidates.append((s, ""))
                
    return candidates
