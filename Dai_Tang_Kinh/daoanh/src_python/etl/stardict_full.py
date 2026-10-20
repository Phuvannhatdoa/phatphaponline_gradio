#!/usr/bin/env python3
"""
StarDict Full Format Exporter
Export complete StarDict format: .ifo + .idx + .dz

Usage:
  python stardict_full.py
"""

import sqlite3
import json
import struct
import hashlib
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
OUTPUT_DIR = BASE_DIR / "data" / "dict"
DICT_NAME = "daoanh_dict"

# StarDict format:
# .ifo - Information file
# .idx - Index file (word offset + length)

def export_ifo():
    """Generate .ifo file"""
    print("\n📤 Generating .ifo...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM lexicon")
    word_count = cursor.fetchone()[0]
    conn.close()
    
    ifo_content = f"""StarDict's Dict ifo file
version=2.4.8
wordcount={word_count}
synwordcount=0
bookname=Phật Pháp Online - Đạo Ảnh
author=DILA Vietnam
description= Vietnamese Buddhist Dictionary - 22 dictionaries merged
date=2026-04-22
language=vi
sametypesequence=mg
"""
    
    ifo_file = OUTPUT_DIR / f"{DICT_NAME}.ifo"
    with open(ifo_file, 'w', encoding='utf-8') as f:
        f.write(ifo_content)
    
    print(f"   ✅ {ifo_file}")
    return word_count


def export_idx():
    """Generate .idx file (index)"""
    print("\n📤 Generating .idx...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, definition, entity_type
        FROM lexicon
        WHERE term IS NOT NULL AND term != ''
        ORDER BY term
    """)
    words = cursor.fetchall()
    conn.close()
    
    idx_file = OUTPUT_DIR / f"{DICT_NAME}.idx"
    
    offset = 0
    idx_entries = []
    
    with open(idx_file, 'wb') as f:
        for term, definition, etype in words:
            if not definition:
                definition = ""
            
            definition = definition.strip()
            def_bytes = definition.encode('utf-8')
            def_len = len(def_bytes)
            
            term_bytes = term.encode('utf-8')
            
            entry = struct.pack(f'{len(term_bytes)}sI', term_bytes, def_len)
            f.write(entry)
            idx_entries.append((term, offset, def_len))
            offset += len(term_bytes) + 4
    
    print(f"   ✅ {idx_file}: {len(idx_entries)} entries")
    return idx_entries


def export_midx():
    """Generate .mdx (dictionary text)"""
    print("\n📤 Generating .mdx...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, definition, entity_type
        FROM lexicon
        WHERE term IS NOT NULL AND term != ''
        ORDER BY term
    """)
    words = cursor.fetchall()
    conn.close()
    
    mdx_file = OUTPUT_DIR / f"{DICT_NAME}.mdx"
    
    with open(mdx_file, 'w', encoding='utf-8') as f:
        for term, definition, etype in words:
            if not definition:
                definition = ""
            
            if etype:
                definition = f"[{etype}] {definition}"
            
            definition = definition.replace('\n', '<br>')
            line = f"{term}\t{definition}\n"
            f.write(line)
    
    print(f"   ✅ {mdx_file}")
    return len(words)


def export_star_dict():
    """Main export function"""
    print("=" * 60)
    print("🚀 StarDict Full Format Export")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    word_count = export_ifo()
    idx_count = export_idx()
    mdx_count = export_midx()
    
    print(f"\n📊 StarDict Export Complete:")
    print(f"   Words: {word_count}")
    print(f"   Output: {OUTPUT_DIR}/")
    
    return {
        'word_count': word_count,
        'ifo': f"{DICT_NAME}.ifo",
        'idx': f"{DICT_NAME}.idx",
        'mdx': f"{DICT_NAME}.mdx"
    }


if __name__ == "__main__":
    export_star_dict()
    print("\n✅ Complete")