#!/usr/bin/env python3
"""
Extract Vietnamese-Chinese place name mappings from Buddhist dictionaries
For enriching DILA/CBETA place data with Vietnamese names
"""

import os
import re
import json
import zipfile
import subprocess
from pathlib import Path

DICT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dictionaries"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/dictionary_mappings.json"

def extract_from_docx(filepath):
    """Extract text from .docx file"""
    mappings = []
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '-c', '''
from docx import Document
import sys
doc = Document(sys.argv[1])
for para in doc.paragraphs:
    print(para.text)
''' , filepath],
            capture_output=True, text=True, timeout=60
        )
        
        filename = os.path.basename(filepath)
        mappings.extend(parse_text_to_mappings(result.stdout, filename))
        
    except Exception as e:
        print(f"Error extracting {filepath}: {e}")
    
    return mappings

def extract_from_doc(filepath):
    """Extract text from .doc file (try antiword or catdoc)"""
    mappings = []
    filename = os.path.basename(filepath)
    
    # Try using antiword
    try:
        result = subprocess.run(
            ['antiword', filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            mappings.extend(parse_text_to_mappings(result.stdout, filename))
            return mappings
    except:
        pass
    
    # Try catdoc
    try:
        result = subprocess.run(
            ['catdoc', filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            mappings.extend(parse_text_to_mappings(result.stdout, filename))
            return mappings
    except:
        pass
    
    return mappings

def parse_text_to_mappings(text, source):
    """Parse text to find Vietnamese-Chinese mappings"""
    mappings = []
    
    # Common temple name patterns
    # Pattern 1: "Chùa X" / "X Temple" - Vietnamese name followed by Chinese
    # Pattern 2: "Tên Việt - Tên Hán" or "Tên Việt: Tên Hán"
    
    for line in text.split('\n'):
        line = line.strip()
        if len(line) < 3:
            continue
        
        # Pattern: Vietnamese (Vietnamese) - Chinese
        # Example: "Thiếu Lâm Tự (少林寺)" or "Thiếu Lâm Tự - 少林寺"
        match = re.search(r'([A-Za-zÀ-ỹ\s\.\-\,]+)[\(\-\:]+\s*([一-龥]+)', line)
        if match:
            vi = match.group(1).strip()
            zh = match.group(2).strip()
            if len(vi) > 2 and len(zh) > 1:
                mappings.append({
                    'vietnamese': vi,
                    'chinese': zh,
                    'source': source
                })
                continue
        
        # Pattern: Chinese (Vietnamese)
        # Example: "少林寺 (Thiếu Lâm Tự)"
        match = re.search(r'([一-龥]+)\s*\(([A-Za-zÀ-ỹ\s\.\-\,]+)\)', line)
        if match:
            zh = match.group(1).strip()
            vi = match.group(2).strip()
            if len(vi) > 2 and len(zh) > 1:
                mappings.append({
                    'vietnamese': vi,
                    'chinese': zh,
                    'source': source
                })
                continue
        
        # Pattern: "Vietnamese: Chinese"
        # Example: "Thiếu Lâm Tự: 少林寺"
        match = re.search(r'([A-Za-zÀ-ỹ\s\.\-\,]+?)[\:\-]\s*([一-龥]{2,15})', line)
        if match:
            vi = match.group(1).strip()
            zh = match.group(2).strip()
            if len(vi) > 2 and len(zh) > 1:
                mappings.append({
                    'vietnamese': vi,
                    'chinese': zh,
                    'source': source
                })
    
    return mappings

def find_temple_keywords(line):
    """Check if line contains temple/monastery keywords"""
    keywords = ['chùa', 'tự', 'tịnh', 'am', 'động', 'quán', 'trai', 'viện', 'tang']
    return any(k in line.lower() for k in keywords)

def main():
    print("🔍 Extracting dictionary mappings...")
    
    all_mappings = []
    dict_files = list(Path(DICT_DIR).glob('*.doc*'))
    
    for filepath in dict_files:
        print(f"  Processing: {filepath.name}")
        
        if filepath.suffix == '.docx':
            mappings = extract_from_docx(str(filepath))
        elif filepath.suffix == '.doc':
            mappings = extract_from_doc(str(filepath))
        else:
            continue
        
        # Filter to only temple-related entries
        temple_mappings = [m for m in mappings if find_temple_keywords(m.get('vietnamese', ''))]
        
        print(f"    Found {len(temple_mappings)} temple entries")
        all_mappings.extend(temple_mappings)
    
    # Deduplicate
    seen = set()
    unique_mappings = []
    for m in all_mappings:
        key = (m['vietnamese'].lower(), m['chinese'])
        if key not in seen:
            seen.add(key)
            unique_mappings.append(m)
    
    # Save
    output = {
        "mappings": unique_mappings,
        "count": len(unique_mappings),
        "sources": list(set(m['source'] for m in unique_mappings))
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Extracted {len(unique_mappings)} unique mappings")
    print(f"Output: {OUTPUT_JSON}")
    
    # Show sample
    print("\nSample mappings:")
    for m in unique_mappings[:10]:
        print(f"  {m['vietnamese']} ↔ {m['chinese']}")

if __name__ == "__main__":
    main()