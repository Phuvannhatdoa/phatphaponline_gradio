#!/usr/bin/env python3
"""
Import DILA Person Authority → people table
Source: authority_person/Buddhist_Studies_Person_Authority.xml
Action: INSERT NEW - no duplicate
"""

import os
import sqlite3
import xml.etree.ElementTree as ET
import re
from datetime import datetime

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
XML_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml'

def main():
    print(f"Loading: {XML_FILE}")
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    list_person = root.find('.//tei:listPerson', ns)
    persons = list_person.findall('tei:person', ns)
    total = len(persons)
    print(f"Found {total} persons")

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Create backup
    conn.execute("DROP TABLE IF EXISTS people_backup")
    conn.execute("ALTER TABLE people RENAME TO people_backup")
    
    # Create fresh table
    conn.execute("""
    CREATE TABLE people (
        id TEXT PRIMARY KEY,
        name_zh TEXT,
        name_vi TEXT,
        name_en TEXT,
        name_ja TEXT,
        sect TEXT,
        dynasty TEXT,
        birth_year INTEGER,
        death_year INTEGER,
        bio TEXT,
        source_origin TEXT DEFAULT 'DILA',
        latin_source TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
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
    conn.commit()
    
    inserted = 0
    for i, person in enumerate(persons):
        pid = person.get('{http://www.w3.org/XML/1998/namespace}id')
        if not pid:
            continue
        
        names = person.findall('tei:persName', ns)
        name_zh = name_vi = name_en = name_ja = ''
        for name in names:
            lang = name.get('{http://www.w3.org/XML/1998/namespace}lang')
            text = name.text or ''
            if lang == 'zho-Hant':
                name_zh = text
            elif lang == 'vie':
                name_vi = text
            elif lang == 'eng':
                name_en = text
            elif lang == 'jpn':
                name_ja = text
            for alt in name:
                if alt.text and not name_zh:
                    name_zh = alt.text
        if not name_zh:
            continue
        
        notes = person.findall('tei:note', ns)
        dynasty = bio = ''
        for note in notes:
            if note.get('type') == 'dynasty':
                dynasty = (note.text or '').strip()
            elif note.get('type') == 'concise':
                bio = (note.text or '').strip()
        
        birth_year = death_year = None
        years = re.findall(r'(\d{4})', bio)
        if len(years) >= 2:
            y1, y2 = int(years[0]), int(years[1])
            if y1 < 2026 and y2 < 2026:
                birth_year, death_year = y1, y2
        
        sect = ''
        for note in notes:
            if note.get('type') == 'monk' and note.text and '是' in note.text:
                sect = 'Thiền Tông'
        
        # Insert with latin_source provenance
        latin_src = 'DILA' if name_en else None
        conn.execute("""
        INSERT INTO people (id, name_zh, name_vi, name_en, name_ja, sect, dynasty, birth_year, death_year, latin_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, name_zh, name_vi, name_en, name_ja, sect, dynasty, birth_year, death_year, latin_src))
        if name_en:
            conn.execute("""
            INSERT INTO person_refs (person_id, source_name, ref_type, value, note)
            VALUES (?, ?, ?, ?, ?)
            """, (pid, 'DILA', 'latin_name', name_en, f'Imported from DILA Person Authority XML'))
        inserted += 1
        
        if (i + 1) % 5000 == 0:
            conn.commit()
            print(f"  {i+1}/{total}...")

    conn.commit()
    
    count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    print(f"Inserted {count} records")
    
    # Drop backup
    conn.execute("DROP TABLE IF EXISTS people_backup")
    conn.commit()
    
    print(f"Done! Final: {count}")
    conn.close()

if __name__ == '__main__':
    main()