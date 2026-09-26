#!/usr/bin/env python3
"""
Dictionary Merger - Merge Buddhist dictionaries with priority
Priority: HanLam > PhoThong > ThamKhao

Usage: python merger.py
Output: data/dict/merged.json
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/tudien")
OUTPUT_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dict")

PRIORITY = {
    "han_lam": 3,
    "pho_thong": 2,
    "tham_khao": 1
}

def get_source_from_path(filepath):
    """Determine source from path"""
    path_lower = str(filepath).lower()
    if "han_lam" in path_lower:
        return "HanLam"
    elif "pho_thong" in path_lower:
        return "PhoThong"
    elif "tham_khao" in path_lower:
        return "ThamKhao"
    return None

def get_priority(source):
    """Get priority value"""
    return PRIORITY.get(source.lower(), 0)

def parse_stardict_file(filepath):
    """Parse StarDict format: Line1=term, Line2=definition"""
    entries = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            term = None
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if not term:
                    term = line
                else:
                    entries[term] = {"definition": line}
                    term = None
    except Exception as e:
        print(f"[MERGER] Error reading {filepath}: {e}")
    return entries

def merge():
    """Merge all dictionaries with priority"""
    merged = {}
    sources_found = set()
    
    if not BASE_DIR.exists():
        print(f"[MERGER] Base dir not found: {BASE_DIR}")
        return merged
    
    for subdir in BASE_DIR.iterdir():
        if not subdir.is_dir():
            continue
        
        source = get_source_from_path(subdir)
        if not source:
            continue
        
        priority = get_priority(source)
        sources_found.add(source)
        print(f"[MERGER] Processing: {subdir.name} (priority={priority})")
        
        for dict_file in subdir.glob("*.txt"):
            print(f"[MERGER]   - {dict_file.name}")
            entries = parse_stardict_file(dict_file)
            
            for term, data in entries.items():
                if not term:
                    continue
                if term in merged:
                    existing_priority = merged[term].get("_priority", 0)
                    if priority > existing_priority:
                        merged[term] = {
                            "definition": data["definition"],
                            "source": source,
                            "_priority": priority
                        }
                else:
                    merged[term] = {
                        "definition": data["definition"],
                        "source": source,
                        "_priority": priority
                    }
    
    for term in merged:
        merged[term].pop("_priority", None)
    
    print(f"[MERGER] Sources found: {sources_found}")
    return merged

def main():
    """Main entry point"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("[MERGER] Starting merge...")
    merged = merge()
    
    output_file = OUTPUT_DIR / "merged.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"[MERGER] Done! Total entries: {len(merged)}")
    print(f"[MERGER] Output: {output_file}")
    return merged

if __name__ == "__main__":
    main()