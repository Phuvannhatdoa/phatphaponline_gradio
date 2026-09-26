#!/usr/bin/env python3
"""
ETL Script: Build Place Vietnamese Name Mapping
Maps Chinese place names (name_zh) to Vietnamese names using lexicon/dictionary data.
Updates places.name_vi field in SQLite (NO changes to raw data).
"""

import sqlite3
import os
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'data' / 'lineage.db'
DICT_DIR = BASE_DIR / 'data' / 'dictionaries' / 'tudien'

def get_db():
    return sqlite3.connect(DB_PATH)

def build_mapping():
    """Main ETL: Map Chinese place names to Vietnamese using dictionaries."""
    print("=== PLACE VIETNAMESE NAME MAPPING ETL ===")
    
    conn = get_db()
    try:
        # Get all places with name_zh but empty name_vi
        places = conn.execute("""
            SELECT id, name_zh, name_vi FROM places 
            WHERE (name_vi IS NULL OR name_vi = '') AND name_zh != ''
        """).fetchall()
        
        print(f"Found {len(places)} places needing Vietnamese names")
        
        # Try to load from lexicon table (has Vietnamese definitions)
        print("Loading lexicon entries...")
        lexicon_entries = conn.execute("""
            SELECT term, definition FROM lexicon 
            WHERE definition LIKE '%chùa%' OR definition LIKE '%tự%' OR definition LIKE '%núi%'
            LIMIT 50000
        """).fetchall()
        
        print(f"Loaded {len(lexicon_entries)} relevant lexicon entries")
        
        updated = 0
        skipped = 0
        
        for place in places:
            place_id, name_zh, name_vi = place
            
            if name_vi:
                continue
            
            vi_name = None
            
            # Search in lexicon definitions
            for lex_term, lex_def in lexicon_entries:
                if name_zh in lex_def:
                    # Try to extract Vietnamese name from context
                    # Pattern: "chùa Thiếu Lâm" or "Thiếu Lâm Tự"
                    vi_matches = re.findall(r'([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,3})\s*(?:\([^)]+\)|:|,)', lex_def[:500])
                    if vi_matches:
                        vi_name = vi_matches[0].strip()
                        break
            
            # Common known mappings
            if not vi_name:
                known = {
                    '少林寺': 'Thiếu Lâm Tự',
                    '少林宮': 'Thiếu Lâm Cung',
                    '嵩山': 'Tung Sơn',
                    '少林': 'Thiếu Lâm',
                }
                vi_name = known.get(name_zh)
            
            if vi_name:
                conn.execute("UPDATE places SET name_vi = ? WHERE id = ?", (vi_name, place_id))
                updated += 1
                if updated % 10 == 0:
                    print(f"Updated {updated} places...")
                    conn.commit()
            else:
                skipped += 1
        
        conn.commit()
        print(f"\n=== SUMMARY ===")
        print(f"Updated: {updated} places")
        print(f"Skipped (no match): {skipped} places")
        
        # Show sample results
        print(f"\n=== SAMPLE RESULTS ===")
        sample = conn.execute("SELECT id, name_zh, name_vi FROM places WHERE name_vi != '' LIMIT 10").fetchall()
        for row in sample:
            print(f"  {row[0]}: {row[1]} → {row[2]}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    build_mapping()
