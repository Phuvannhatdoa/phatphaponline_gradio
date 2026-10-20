import sqlite3
import sys

db_path = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='namevi_map_places'")
if cursor.fetchone():
    print("✅ Table namevi_map_places exists")
else:
    print("❌ Table NOT found, creating...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS namevi_map_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT,
            name_zh TEXT,
            dila_id TEXT UNIQUE,
            confidence REAL DEFAULT 0.5,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✅ Table created")

conn.close()
print("Done!")
