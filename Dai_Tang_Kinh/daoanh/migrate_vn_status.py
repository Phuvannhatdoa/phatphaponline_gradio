"""Migration: Add vn_name_status column to namevi_map_places"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lineage.db')
conn = sqlite3.connect(DB_PATH)
try:
    conn.execute("ALTER TABLE namevi_map_places ADD COLUMN vn_name_status TEXT DEFAULT NULL")
    conn.commit()
    print("Added vn_name_status column to namevi_map_places")
except Exception as e:
    if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
        print("Column vn_name_status already exists")
    else:
        print(f"Error: {e}")
conn.close()
