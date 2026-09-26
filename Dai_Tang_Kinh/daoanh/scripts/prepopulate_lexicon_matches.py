#!/usr/bin/env python3
"""
Pre-populate namevi_map_places with 100% lexicon matches to save API quota.
Run this script before starting Flask app.
"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
conn.row_factory = sqlite3.Row

# Find exact matches between places_pending.name_zh and lexicon.term
matches = conn.execute("""
    SELECT p.id, p.name_zh, l.term 
    FROM places_pending p
    INNER JOIN lexicon l ON p.name_zh = l.term
    WHERE p.id NOT IN (SELECT dila_id FROM namevi_map_places)
""").fetchall()

print(f"Found {len(matches)} exact matches. Pre-populating...")

for m in matches:
    conn.execute(
        "INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, source) VALUES (?, ?, ?, ?)",
        (m['id'], m['term'], m['name_zh'], 'lexicon-auto')
    )
    print(f"  ✓ {m['id']}: {m['name_zh']} → {m['term']}")

conn.commit()
conn.close()
print("✅ Pre-population complete!")
