#!/usr/bin/env python3
"""
Fuzzy Matcher - Match DILA places with dictionary entries
Using Levenshtein distance

Usage: python matcher.py
Input: data/dict/normalized.json, data/places.json
Output: data/dict/match_queue.json
"""

import json
from pathlib import Path
from difflib import SequenceMatcher

INPUT_DICT = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict/normalized.json")
INPUT_PLACES = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places.json")
OUTPUT_QUEUE = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict/match_queue.json")

THRESHOLD = 85

def normalize_string(s):
    """Remove special chars, lowercase"""
    if not s:
        return ""
    s = s.lower().strip()
    s = s.replace(',', ' ').replace('.', ' ')
    s = ' '.join(s.split())
    return s

def fuzzy_ratio(s1, s2):
    """Calculate fuzzy match ratio"""
    if not s1 or not s2:
        return 0
    return int(SequenceMatcher(None, normalize_string(s1), normalize_string(s2)).ratio() * 100)

def match():
    """Match places with dictionary"""
    if not INPUT_DICT.exists():
        print(f"[MATCHER] Dict not found: {INPUT_DICT}")
        return []
    
    print(f"[MATCHER] Loading dictionary...")
    with open(INPUT_DICT, 'r', encoding='utf-8') as f:
        dict_data = json.load(f)
    
    places = []
    if INPUT_PLACES.exists():
        print(f"[MATCHER] Loading places...")
        with open(INPUT_PLACES, 'r', encoding='utf-8') as f:
            places_data = json.load(f)
            places = places_data.get('places', [])
    
    print(f"[MATCHER] Matching {len(places)} places with {len(dict_data)} dictionary entries...")
    
    matches = []
    for place in places:
        place_name = place.get('nameVietnamese') or place.get('nameChinese') or ''
        if not place_name:
            continue
        
        best_match = None
        best_score = 0
        
        for term, info in dict_data.items():
            score = fuzzy_ratio(place_name, term)
            if score >= THRESHOLD and score > best_score:
                best_score = score
                best_match = {
                    "term": term,
                    "definition": info.get("definition", ""),
                    "source": info.get("source", ""),
                    "score": score
                }
        
        if best_match:
            matches.append({
                "place_id": place.get('id', ''),
                "place_name": place_name,
                "dict_term": best_match["term"],
                "definition": best_match["definition"],
                "source": best_match["source"],
                "score": best_match["score"],
                "status": "pending"
            })
    
    print(f"[MATCHER] Found {len(matches)} matches (threshold {THRESHOLD}%)")
    return matches

def main():
    """Main entry point"""
    matches = match()
    
    with open(OUTPUT_QUEUE, 'w', encoding='utf-8') as f:
        json.dump({"matches": matches, "total": len(matches)}, f, ensure_ascii=False, indent=2)
    
    print(f"[MATCHER] Saved to: {OUTPUT_QUEUE}")
    return matches

if __name__ == "__main__":
    main()