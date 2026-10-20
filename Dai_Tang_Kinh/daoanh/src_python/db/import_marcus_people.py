#!/usr/bin/env python3
"""
Import Marcus B. person data → people table
Fills name_en from marcus_reference where missing, records provenance.

Usage: python import_marcus_people.py
"""

import sqlite3
import re

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'

def main():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    # 1. latin_source column if missing
    try:
        conn.execute("ALTER TABLE people ADD COLUMN latin_source TEXT")
        print("✅ Added latin_source column to people")
    except Exception:
        print("ℹ️ latin_source column already exists")

    # 2. person_refs table if missing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS person_refs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            ref_type TEXT,
            value TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_person_refs_person ON person_refs(person_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_person_refs_source ON person_refs(source_name)")
    print("✅ Ensured person_refs table")

    # 3. Match dila_reference → people by ID, fill name_en where empty
    dila_rows = conn.execute(
        "SELECT id, name_en FROM dila_reference WHERE name_en IS NOT NULL AND name_en != ''"
    ).fetchall()

    updated = 0
    for row in dila_rows:
        person = conn.execute(
            "SELECT id, name_en, latin_source FROM people WHERE id = ?",
            (row['id'],)
        ).fetchone()
        if not person:
            continue
        if person['name_en'] and person['name_en'].strip():
            continue

        conn.execute(
            "UPDATE people SET name_en = ?, latin_source = 'marcus' WHERE id = ?",
            (row['name_en'], row['id'])
        )
        conn.execute("""
            INSERT INTO person_refs (person_id, source_name, ref_type, value, note)
            VALUES (?, ?, ?, ?, ?)
        """, (row['id'], 'marcus', 'latin_name', row['name_en'],
              'Filled from dila_reference (marcus-sourced name_en)'))
        updated += 1

    conn.commit()

    total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    total_refs = conn.execute("SELECT COUNT(*) FROM person_refs").fetchone()[0]
    with_latin = conn.execute("SELECT COUNT(*) FROM people WHERE latin_source IS NOT NULL").fetchone()[0]
    conn.close()

    print(f"\n📊 Stats:")
    print(f"   People: {total_people}")
    print(f"   Latin names filled from Marcus: {updated}")
    print(f"   People with latin_source: {with_latin}")
    print(f"   person_refs rows: {total_refs}")

if __name__ == '__main__':
    main()
