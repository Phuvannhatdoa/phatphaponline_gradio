#!/usr/bin/env python3
"""
Import DILA Person Authority to SQLite - Simplified
"""

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
DILA_PERSON = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_person" / "Buddhist_Studies_Person_Authority.xml"


def import_all():
    print("=" * 60)
    print("🚀 DILA Person Authority Import")
    print("=" * 60)
    
    # Setup DB
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM people")
    conn.commit()
    
    # Parse XML
    print("\n📂 Parsing XML...")
    tree = ET.parse(DILA_PERSON)
    root = tree.getroot()
    
    # Remove namespace
    for elem in root.iter():
        if elem.tag.startswith('{'):
            elem.tag = elem.tag.split('}')[1]
    
    # Find all persons - use XPath
    persons = root.findall('.//listPerson/person')
    print(f"   Found {len(persons)} persons")
    
    # Insert
    print("\n📥 Importing...")
    inserted = 0
    for idx, p in enumerate(persons):
        raw_id = p.get('id') or p.get('n')
        pid = f"A{idx+1:06d}"
        
        # Get name
        name = ''
        for pn in p.findall('persName'):
            if pn.text:
                name = pn.text[:100]
                break
        
        if not name:
            continue
        
        try:
            cursor.execute("INSERT INTO people (id, name_zh) VALUES (?, ?)", (pid, name))
            inserted += 1
        except:
            pass
        
        if (idx + 1) % 10000 == 0:
            print(f"   Processed {idx+1}...")
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM people")
    total = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n✅ Import complete: {inserted} inserted (total: {total})")
    return inserted


if __name__ == "__main__":
    import_all()