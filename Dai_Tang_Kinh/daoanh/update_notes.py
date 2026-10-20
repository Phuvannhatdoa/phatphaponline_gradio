#!/usr/bin/env python3
"""Update places_pending.note from places_dila.note"""
import sqlite3
import time

DB = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'

print("Starting note update...")
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")

# Get mappings
print("Fetching mappings from places_dila...")
mappings = conn.execute("""
    SELECT p.id, d.note 
    FROM places_pending p
    JOIN places_dila d ON p.name_zh = d.name_zh
    WHERE d.note IS NOT NULL
""").fetchall()

print(f"Found {len(mappings)} mappings to update")

# Update in batches
batch_size = 1000
updated = 0

for i in range(0, len(mappings), batch_size):
    batch = mappings[i:i+batch_size]
    for place_id, note in batch:
        conn.execute("UPDATE places_pending SET note = ? WHERE id = ?", (note, place_id))
    conn.commit()
    updated += len(batch)
    if updated % 5000 == 0:
        print(f"  Updated {updated}/{len(mappings)}...")

print(f"✅ Done! Updated {updated} records")
conn.close()
