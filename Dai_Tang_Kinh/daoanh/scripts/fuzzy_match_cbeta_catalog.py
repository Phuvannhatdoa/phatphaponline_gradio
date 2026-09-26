"""
ETL: Fuzzy match place name_zh ↔ CBETA catalog title_zh using RapidFuzz.
Stores top-5 matches per unique name_zh in cbeta_catalog_place_fuzzy table.

Usage:
    python scripts/fuzzy_match_cbeta_catalog.py

Logic:
    1. Read all distinct Chinese place names from places table (36,848 unique)
    2. Read all catalog titles from cbeta_catalog_vn (3,122 records)
    3. For each place name, compute RapidFuzz partial_ratio against each catalog title
    4. Store top-5 matches with score >= 60 in cbeta_catalog_place_fuzzy table
    5. Expand to all place_ids sharing that name_zh
"""

import sys
import os
import sqlite3
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from rapidfuzz import fuzz, process
except ImportError:
    print("RapidFuzz not installed. Run: pip install rapidfuzz")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clean_title(title):
    """Strip author/dynasty metadata from catalog titles for better matching."""
    title = re.sub(r'[（(][^）)]*[）)]', '', title).strip()
    title = re.sub(r'\s+', '', title)
    return title

def has_chinese(s):
    return bool(re.search(r'[\u4e00-\u9fff]', s))

def main():
    conn = get_conn()
    
    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cbeta_catalog_place_fuzzy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT NOT NULL,
            name_zh TEXT NOT NULL,
            catalog_id TEXT NOT NULL,
            title_zh TEXT,
            title_vi TEXT,
            score INTEGER NOT NULL,
            rank INTEGER NOT NULL DEFAULT 1,
            UNIQUE(place_id, catalog_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fuzzy_place ON cbeta_catalog_place_fuzzy(place_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fuzzy_catalog ON cbeta_catalog_place_fuzzy(catalog_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fuzzy_score ON cbeta_catalog_place_fuzzy(score)")
    conn.commit()
    
    print("Reading place names...")
    rows = conn.execute(
        "SELECT DISTINCT name_zh FROM places WHERE name_zh IS NOT NULL AND name_zh != ''"
    ).fetchall()
    all_place_names = [r['name_zh'] for r in rows if has_chinese(r['name_zh'])]
    print(f"  Found {len(all_place_names)} distinct Chinese place names")
    
    print("Reading CBETA catalog...")
    cat_rows = conn.execute(
        "SELECT sh_number, title_zh, title_vi FROM cbeta_catalog_vn WHERE title_zh IS NOT NULL"
    ).fetchall()
    catalogs = [(r['sh_number'], r['title_zh'], r['title_vi'] or '') for r in cat_rows]
    print(f"  Found {len(catalogs)} catalog entries")
    
    catalog_titles = [clean_title(c[1]) for c in catalogs]
    
    # Pre-clear existing fuzzy matches
    conn.execute("DELETE FROM cbeta_catalog_place_fuzzy")
    conn.commit()
    
    inserted = 0
    start = time.time()
    
    for idx, place_name in enumerate(all_place_names):
        cleaned = clean_title(place_name)
        if len(cleaned) < 2:
            continue
        
        results = process.extract(
            cleaned,
            catalog_titles,
            scorer=fuzz.partial_ratio,
            score_cutoff=60,
            limit=5
        )
        
        if not results:
            continue
        
        # Find all place_ids for this name_zh
        place_rows = conn.execute(
            "SELECT id FROM places WHERE name_zh = ?", (place_name,)
        ).fetchall()
        place_ids = [r['id'] for r in place_rows]
        
        for rank, (title_clean, score, cat_idx) in enumerate(results, 1):
            cat_id, title_zh, title_vi = catalogs[cat_idx]
            for pid in place_ids:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO cbeta_catalog_place_fuzzy
                           (place_id, name_zh, catalog_id, title_zh, title_vi, score, rank)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (pid, place_name, cat_id, title_zh, title_vi, score, rank)
                    )
                    inserted += 1
                except Exception as e:
                    print(f"    Error inserting {pid}/{cat_id}: {e}")
        
        if (idx + 1) % 500 == 0:
            elapsed = time.time() - start
            rate = (idx + 1) / elapsed
            eta = (len(all_place_names) - idx - 1) / rate
            print(f"  [{idx+1}/{len(all_place_names)}] inserted={inserted} rate={rate:.0f}/s eta={eta:.0f}s")
            conn.commit()
    
    conn.commit()
    elapsed = time.time() - start
    print(f"\nDone! {inserted} fuzzy matches inserted in {elapsed:.1f}s")
    print(f"Rate: {len(all_place_names)/elapsed:.1f} names/s")
    
    count = conn.execute("SELECT COUNT(DISTINCT place_id) FROM cbeta_catalog_place_fuzzy").fetchone()[0]
    print(f"Places with fuzzy matches: {count}")
    
    conn.close()

if __name__ == '__main__':
    main()
