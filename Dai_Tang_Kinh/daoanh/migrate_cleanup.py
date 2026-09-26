#!/usr/bin/env python3
"""Migration script to clean up duplicate *_new tables and consolidate mapping tables.

- Renames `people_new` → `people_staging`
- Renames `places_new` → `places_staging`
- Merges `name_vi_map_places` into `namevi_map_places` (keeps richer table)
- Drops the now‑obsolete tables.

Run with:
    python3 migrate_cleanup.py
"""
import sqlite3
import sys
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

def exec_sql(conn, sql, params=()):
    try:
        conn.execute(sql, params)
    except Exception as e:
        print(f"SQL error: {e}\nStatement: {sql}\nParams: {params}")
        sys.exit(1)

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("--- Starting migration ---")
    # 1. Rename people_new -> people_staging (if exists)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='people_new'")
    if cur.fetchone():
        print("Renaming people_new → people_staging")
        exec_sql(conn, "ALTER TABLE people_new RENAME TO people_staging")
    else:
        print("people_new not present, skipping rename")
    # 2. Rename places_new -> places_staging (if exists)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='places_new'")
    if cur.fetchone():
        print("Renaming places_new → places_staging")
        exec_sql(conn, "ALTER TABLE places_new RENAME TO places_staging")
    else:
        print("places_new not present, skipping rename")
    # 3. Consolidate mapping tables
    # Ensure target table exists (keep the richer namevi_map_places)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='namevi_map_places'")
    if not cur.fetchone():
        print("Target mapping table namevi_map_places does not exist – aborting")
        sys.exit(1)
    # Migrate rows from name_vi_map_places if that table exists
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='name_vi_map_places'")
    if cur.fetchone():
        print("Migrating data from name_vi_map_places → namevi_map_places")
        # Insert only rows that do not already exist (unique on dila_id)
        exec_sql(conn, """
            INSERT OR IGNORE INTO namevi_map_places (dila_id, name_vi, name_zh, source, confidence)
            SELECT dila_id, name_vi, name_zh, source, confidence FROM name_vi_map_places;
        """)
        print("Dropping legacy table name_vi_map_places")
        exec_sql(conn, "DROP TABLE name_vi_map_places")
    else:
        print("Legacy mapping table name_vi_map_places not present, nothing to merge")
    conn.commit()
    conn.close()
    print("--- Migration completed successfully ---")

if __name__ == '__main__':
    main()
