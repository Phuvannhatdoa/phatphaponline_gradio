#!/usr/bin/env python3
"""
Export data from SQLite to JSON for admin interface
"""

import sqlite3
import json
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
OUTPUT_DIR = BASE_DIR / "data" / "indexed"


def export_people():
    """Export people for admin"""
    print("\n📤 Exporting people...")
    conn = sqlite3.connect(str(DB_FILE))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name_zh, name_vi, sect, dynasty, bio
        FROM people
        ORDER BY id
        LIMIT 50000
    """)
    
    people = []
    for row in cur.fetchall():
        people.append({
            'id': row[0],
            'name_zh': row[1] or '',
            'name_vi': row[2] or '',
            'sect': row[3] or '',
            'dynasty': row[4] or '',
            'bio': row[5] or ''
        })
    
    conn.close()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / 'people_admin.json', 'w', encoding='utf-8') as f:
        json.dump(people, f, ensure_ascii=False)
    
    print(f"   ✅ Exported {len(people)} people")
    return len(people)


def export_places():
    """Export places with GPS for admin"""
    print("\n📤 Exporting places...")
    conn = sqlite3.connect(str(DB_FILE))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name_zh, province, gps_lat, gps_long
        FROM places
        WHERE gps_lat IS NOT NULL
        ORDER BY province
        LIMIT 50000
    """)
    
    places = []
    for row in cur.fetchall():
        places.append({
            'name': row[0] or '',
            'province': row[1] or '',
            'lat': row[2],
            'lng': row[3]
        })
    
    conn.close()
    
    with open(OUTPUT_DIR / 'places_admin.json', 'w', encoding='utf-8') as f:
        json.dump(places, f, ensure_ascii=False)
    
    print(f"   ✅ Exported {len(places)} places with GPS")
    return len(places)


def export_stats():
    """Export stats for admin"""
    conn = sqlite3.connect(str(DB_FILE))
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM people")
    people = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM places WHERE gps_lat IS NOT NULL")
    places = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lexicon")
    lexicon = cur.fetchone()[0]
    
    conn.close()
    
    stats = {
        'people': people,
        'places_gps': places,
        'lexicon': lexicon,
        'updated': '2026-04-22'
    }
    
    with open(OUTPUT_DIR / 'stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False)
    
    print(f"\n📊 Stats: {stats}")
    return stats


if __name__ == "__main__":
    print("=" * 50)
    print("Export data for admin")
    print("=" * 50)
    
    export_people()
    export_places()
    export_stats()
    
    print("\n✅ Export complete")
    print(f"Output: {OUTPUT_DIR}")