#!/usr/bin/env python3
"""
D2: Fast StarDict Scanner - Simple version
"""

import os
import re
import json

INPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/raw/dictionaries"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/dictionary_places.json"

# Simple temple pattern
TEMPLE_RE = re.compile(r'^(Chùa|Tịnh\s*Xá|Thiền\s*Viện|Viện|Tự|Am|Trai|Quán|Cốc|Ngõ)\s+[\u00C0-\u1EF9\w\s]+', re.IGNORECASE)

def extract_han(s):
    m = re.search(r'[(【]([^)】]+)[)】]', s or '')
    return m.group(1) if m else None

def scan_quick():
    print("🚀 D2: Fast Scanner")
    print("=" * 40)
    
    txt_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.txt')]
    print(f"📂 {len(txt_files)} files")
    
    places = []
    for fname in txt_files:
        fpath = os.path.join(INPUT_DIR, fname)
        count = 0
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                # Simple tab split
                if '\t' not in line:
                    continue
                parts = line.split('\t', 1)
                if len(parts) < 2:
                    continue
                name, desc = parts[0].strip(), parts[1].strip()
                # Check temple pattern
                if TEMPLE_RE.match(name):
                    han = extract_han(name)
                    places.append({
                        'nameVi': name,
                        'nameHan': han,
                        'description': desc[:500],  # Limit length
                        'source': fname
                    })
                    count += 1
        print(f"  ✅ {fname}: {count}")
    
    # Dedupe - keep longest description
    print(f"\n🔄 Deduplicating {len(places)} items...")
    seen = {}
    for p in places:
        key = p['nameVi']
        if key not in seen:
            seen[key] = p
        else:
            if len(p['description']) > len(seen[key]['description']):
                seen[key] = p
    
    result = list(seen.values())
    print(f"✅ Unique: {len(result)}")
    
    # Save
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': result, 'count': len(result)}, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {OUTPUT_JSON}")
    
    return result

if __name__ == "__main__":
    scan_quick()