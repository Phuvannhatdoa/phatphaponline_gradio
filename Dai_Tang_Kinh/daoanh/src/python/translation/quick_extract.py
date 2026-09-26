#!/usr/bin/env python3
"""Quick extraction from Phat Quang Tu Dien - focus on temples only"""

import os
import re
import json

DICT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dictionaries/Phat Quang Tu Dien - HT Quang Do.docx"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/dictionary_mappings.json"

def extract_temples():
    mappings = []
    
    try:
        from docx import Document
        doc = Document(DICT_FILE)
        
        print(f"Processing: Phat Quang Tu Dien")
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text or len(text) < 5:
                continue
            
            # Skip if too short
            if len(text) > 200:
                continue
            
            # Pattern: "Vietnamese - Chinese" or "Vietnamese (Chinese)"
            # Example: "Thiếu Lâm Tự - 少林寺" or "Thiếu Lâm Tự (少林寺)"
            match = re.search(r'([A-Za-zÀ-ỹ\s\.\-\,]+)[\(\-\:]+\s*([一-龥]+)', text)
            if match:
                vi = match.group(1).strip()
                zh = match.group(2).strip()
                if 2 < len(vi) < 50 and 2 < len(zh) < 15:
                    mappings.append({
                        'vietnamese': vi,
                        'chinese': zh,
                        'source': 'Phat Quang Tu Dien'
                    })
                    continue
            
            # Reverse pattern: "Chinese (Vietnamese)"
            match = re.search(r'([一-龥]+)\s*\(([A-Za-zÀ-ỹ\s\.\-\,]+)\)', text)
            if match:
                zh = match.group(1).strip()
                vi = match.group(2).strip()
                if 2 < len(vi) < 50 and 2 < len(zh) < 15:
                    mappings.append({
                        'vietnamese': vi,
                        'chinese': zh,
                        'source': 'Phat Quang Tu Dien'
                    })
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    return mappings

# Quick test with single file
mappings = extract_temples()
print(f"Found {len(mappings)} temple mappings")

# Deduplicate
seen = set()
unique = []
for m in mappings:
    key = (m['vietnamese'].lower(), m['chinese'])
    if key not in seen:
        seen.add(key)
        unique.append(m)

print(f"Unique: {len(unique)}")

# Save
output = {
    "mappings": unique,
    "count": len(unique),
    "sources": ["Phat Quang Tu Dien"]
}

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved to: {OUTPUT_JSON}")
print("\nSample:")
for m in unique[:15]:
    print(f"  {m['vietnamese']} ↔ {m['chinese']}")