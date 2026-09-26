#!/usr/bin/env python3
"""
Dictionary Normalizer - Clean text + Unicode NFC

Usage: python normalizer.py
Input: data/dict/merged.json
Output: data/dict/normalized.json
"""

import json
import unicodedata
import re
from pathlib import Path

INPUT_FILE = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict/merged.json")
OUTPUT_FILE = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict/normalized.json")

def normalize_text(text):
    """Normalize text: trim, NFC, remove special chars"""
    if not text:
        return ""
    text = text.strip()
    text = unicodedata.normalize('NFC', text)
    return text

def normalize():
    """Normalize all entries"""
    if not INPUT_FILE.exists():
        print(f"[NORMALIZER] Input not found: {INPUT_FILE}")
        return {}
    
    print(f"[NORMALIZER] Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        merged = json.load(f)
    
    print(f"[NORMALIZER] Normalizing {len(merged)} entries...")
    normalized = {}
    
    for term, data in merged.items():
        norm_term = normalize_text(term)
        norm_def = normalize_text(data.get("definition", ""))
        
        normalized[term] = {
            "definition": norm_def,
            "source": data.get("source", "unknown"),
            "normalized": norm_term.lower()
        }
    
    return normalized

def main():
    """Main entry point"""
    normalized = normalize()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    
    print(f"[NORMALIZER] Done! Entries: {len(normalized)}")
    print(f"[NORMALIZER] Output: {OUTPUT_FILE}")
    return normalized

if __name__ == "__main__":
    main()