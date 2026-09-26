#!/usr/bin/env python3
"""
Entity Extractor - Extract places (chùa/tự/tổ đình) and monks (hòa thượng/thiền sư)
from dictionary data

Usage: python extractor.py
Input: data/dict/normalized.json
Output: data/dict/entities.json
"""

import json
import re
from pathlib import Path

INPUT_FILE = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict/normalized.json")
OUTPUT_FILE = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict/entities.json")

PLACE_KEYWORDS = [
    r'chùa', r'tự', r'viện', r'tổ đình', r'đạo tràng', r'thảo viện',
    r'am', r'cốc', r'quán', r'tra viện', r'tịnh xá', r'tịnh viện',
    r'nĩa', r'bảo', r'điện', r'phương trượng'
]

MONK_KEYWORDS = [
    r'hòa thượng', r'thượng tọa', r'đại đức', r'thiền sư', r'pháp sư',
    r'cư sĩ', r'tăng', r'sa môn', r'hòa tăng', r'tổ sư',
    r'thầy', r'ngài', r'ngộ', r'đạo chủ'
]

def is_place(term):
    """Check if term is a Buddhist place"""
    term_lower = term.lower()
    for kw in PLACE_KEYWORDS:
        if re.search(kw, term_lower):
            return True
    return False

def is_monk(term):
    """Check if term is a monk/teacher"""
    term_lower = term.lower()
    for kw in MONK_KEYWORDS:
        if re.search(kw, term_lower):
            return True
    return False

def extract_type(term):
    """Determine entity type"""
    if is_place(term):
        if 'tổ đình' in term.lower():
            return "to_dinh"
        elif 'chùa' in term.lower():
            return "chua"
        elif 'tự' in term.lower():
            return "tu"
        elif 'viện' in term.lower():
            return "vien"
        elif 'am' in term.lower():
            return "am"
        return "place"
    elif is_monk(term):
        if 'hòa thượng' in term.lower():
            return "hoa_thuong"
        elif 'thượng tọa' in term.lower():
            return "thuong_toa"
        elif 'thiền sư' in term.lower():
            return "thien_su"
        elif 'pháp sư' in term.lower():
            return "phap_su"
        return "monk"
    return None

def extract():
    """Extract entities from dictionary"""
    if not INPUT_FILE.exists():
        print(f"[EXTRACTOR] Input not found: {INPUT_FILE}")
        return {"places": [], "monks": []}
    
    print(f"[EXTRACTOR] Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    places = []
    monks = []
    
    print(f"[EXTRACTOR] Extracting entities from {len(data)} entries...")
    
    for term, info in data.items():
        entity_type = extract_type(term)
        if not entity_type:
            continue
        
        entity = {
            "term": term,
            "type": entity_type,
            "definition": info.get("definition", ""),
            "source": info.get("source", ""),
            "normalized": info.get("normalized", "")
        }
        
        if entity_type in ["chua", "tu", "vien", "to_dinh", "am", "place"]:
            places.append(entity)
            if len(places) % 100 == 0:
                print(f"[EXTRACTOR]   Found {len(places)} places...")
        else:
            monks.append(entity)
            if len(monks) % 100 == 0:
                print(f"[EXTRACTOR]   Found {len(monks)} monks...")
    
    result = {
        "places": places,
        "monks": monks,
        "total_places": len(places),
        "total_monks": len(monks)
    }
    
    print(f"[EXTRACTOR] Total: {len(places)} places, {len(monks)} monks")
    return result

def main():
    """Main entry point"""
    result = extract()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"[EXTRACTOR] Saved to: {OUTPUT_FILE}")
    return result

if __name__ == "__main__":
    main()