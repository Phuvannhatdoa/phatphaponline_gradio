#!/usr/bin/env python3
"""Extract entities from lexicon: temples, monks, works"""

import sqlite3, re
from collections import defaultdict

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'

def extract_entities():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Create entity tables
    conn.execute("DROP TABLE IF EXISTS entity_temples")
    conn.execute("DROP TABLE IF EXISTS entity_monks")
    conn.execute("DROP TABLE IF EXISTS entity_works")
    
    conn.execute("""
    CREATE TABLE entity_temples (
        id INTEGER PRIMARY KEY,
        name TEXT,
        definition TEXT,
        source TEXT,
        entity_type TEXT DEFAULT 'temple'
    )""")
    
    conn.execute("""
    CREATE TABLE entity_monks (
        id INTEGER PRIMARY KEY,
        name TEXT,
        definition TEXT,
        source TEXT,
        entity_type TEXT DEFAULT 'monk'
    )""")
    
    conn.execute("""
    CREATE TABLE entity_works (
        id INTEGER PRIMARY KEY,
        title TEXT,
        definition TEXT,
        source TEXT,
        entity_type TEXT DEFAULT 'work'
    )""")
    conn.commit()
    
    # Temple keywords
    temple_kw = ['chùa', 'tự', 'viện', 'tổ đình', 'đạo tràng', 'quần am']
    
    # Monk keywords  
    monk_kw = ['thích', 'hòa thượng', 'thiền sư', 'thượng tọa', 'đại đức', 'ni sư', 'pháp sư', 'cư sĩ']
    
    # Work keywords
    work_kw = ['kinh', 'truyện', 'luận', 'tắng', 'bài', 'phú', 'sách', 'luật', 'kệ']
    
    temple_count = monk_count = work_count = 0
    
    # Get all terms from lexicon
    cursor = conn.execute("SELECT term, definition, source FROM lexicon")
    
    for term, definition, source in cursor:
        if not term or not definition:
            continue
        
        term_lower = term.lower()
        is_temple = any(kw in term_lower for kw in temple_kw)
        is_monk = any(kw in term_lower for kw in monk_kw)
        is_work = any(kw in term_lower for kw in work_kw) and ('phật giáo' in definition.lower() or 'đức phật' in definition.lower())
        
        if is_temple:
            try:
                conn.execute(
                    "INSERT INTO entity_temples (name, definition, source) VALUES (?, ?, ?)",
                    (term, definition[:500], source)
                )
                temple_count += 1
            except:
                pass
        elif is_monk:
            try:
                conn.execute(
                    "INSERT INTO entity_monks (name, definition, source) VALUES (?, ?, ?)",
                    (term, definition[:500], source)
                )
                monk_count += 1
            except:
                pass
        elif is_work:
            try:
                conn.execute(
                    "INSERT INTO entity_works (title, definition, source) VALUES (?, ?, ?)",
                    (term, definition[:500], source)
                )
                work_count += 1
            except:
                pass
    
    conn.commit()
    
    print(f"✅ Extracted entities:")
    print(f"  - Temples: {temple_count}")
    print(f"  - Monks: {monk_count}")
    print(f"  - Works: {work_count}")
    
    conn.close()

if __name__ == '__main__':
    extract_entities()