#!/usr/bin/env python3
"""
Extract Vietnamese-Chinese mappings - simplified
Process each file separately to avoid memory issues
"""

import os
import re
import json

DICT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dictionaries"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/dictionary_mappings.json"

def extract_from_docx_simple(filepath):
    """Simple extraction - read raw text only"""
    mappings = []
    
    try:
        # Use simple text extraction
        import subprocess
        result = subprocess.run(
            ['python3', '-c', '''
from docx import Document
import sys
doc = Document(sys.argv[1])
for para in doc.paragraphs:
    print(para.text)
''', filepath],
            capture_output=True, text=True, timeout=30
        )
        
        filename = os.path.basename(filepath)
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Vietnamese → Chinese
            match = re.match(r'([A-Za-zÀ-ỹ\s]{2,30})\s+([一-龥]{2,10})', line)
            if match:
                vi = match.group(1).strip()
                zh = match.group(2).strip()
                mappings.append({'vietnamese': vi, 'chinese': zh, 'source': filename})
                continue
            
            # Chinese → Vietnamese
            match = re.match(r'([一-龥]{2,10})\s+([A-Za-zÀ-ỹ\s]{2,30})', line)
            if match:
                zh = match.group(1).strip()
                vi = match.group(2).strip()
                mappings.append({'vietnamese': vi, 'chinese': zh, 'source': filename})
    
    except Exception as e:
        print(f"   ⚠️ {os.path.basename(filepath)}: {e}")
    
    return mappings

def main():
    print("📚 Extracting dictionary mappings...")
    
    all_mappings = []
    
    # Priority files first
    priority = [
        'Tu Dien Phat Hoc Dao Uyen.docx',
        'Phat Quang Tu Dien - HT Quang Do.docx',
        'Tu Dien Han Viet - Nguyen Quoc Hung.docx',
        'Tu Dien Thien Tong Han Viet - Han Man - Thong Thien.docx'
    ]
    
    for filename in priority:
        filepath = os.path.join(DICT_DIR, filename)
        if os.path.exists(filepath):
            print(f"   Processing: {filename}")
            mappings = extract_from_docx_simple(filepath)
            print(f"      Found {len(mappings)}")
            all_mappings.extend(mappings)
    
    # Save progress
    seen = set()
    unique_mappings = []
    for m in all_mappings:
        key = (m['vietnamese'].lower(), m['chinese'])
        if key not in seen:
            seen.add(key)
            unique_mappings.append(m)
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'mappings': unique_mappings, 'count': len(unique_mappings)}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Extracted {len(unique_mappings)} unique mappings")
    print(f"💾 Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
