#!/usr/bin/env python3
"""
Marcus SNA Database Schema - SQLite
Unified Networks + Conflicts + Resolutions

Usage: python marcus_db_schema.py
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"


def create_schema():
    """Create SQLite database schema"""
    print("=" * 60)
    print("🪷 MARCUS SNA DATABASE SCHEMA")
    print("=" * 60)
    
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # 1. Unified Networks Table
    # All relationships from Marcus, DILA, or Admin go here
    print("\n📋 Creating unified networks table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monk_id TEXT NOT NULL,
            related_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            source_origin TEXT NOT NULL CHECK(source_origin IN ('Marcus', 'DILA', 'Admin')),
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(monk_id, related_id, source_origin)
        )
    """)
    
    # Index for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_networks_monk_id ON networks(monk_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_networks_source ON networks(source_origin)
    """)
    
    # 2. Conflicts Table
    # Only records where DILA != Marcus
    print("📋 Creating conflicts table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monk_id TEXT NOT NULL,
            monk_name TEXT,
            source_origin TEXT DEFAULT 'MARCUS',
            conflict_type TEXT DEFAULT 'lineage',
            only_dila_teachers TEXT,
            only_marcus_teachers TEXT,
            only_dila_students TEXT,
            only_marcus_students TEXT,
            dila_count INTEGER DEFAULT 0,
            marcus_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'resolved', 'ignored')),
            admin_choice TEXT,
            resolution_timestamp TEXT,
            resolution_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conflicts_monk ON conflicts(monk_id)
    """)
    
    # 3. Resolutions Log (for auditing)
    print("📋 Creating resolutions log table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resolutions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conflict_id INTEGER NOT NULL,
            monk_id TEXT NOT NULL,
            chosen_source TEXT NOT NULL,
            previous_source TEXT,
            notes TEXT,
            resolved_by TEXT DEFAULT 'admin',
            resolved_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conflict_id) REFERENCES conflicts(id)
        )
    """)
    
    # 4. DILA Person Reference (read-only for joining)
    print("📋 Creating dila_reference table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dila_reference (
            id TEXT PRIMARY KEY,
            name_vi TEXT,
            name_zh TEXT,
            name_ja TEXT,
            name_en TEXT,
            dynasty TEXT,
            bio TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Marcus Node Reference
    print("📋 Creating marcus_reference table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marcus_reference (
            node_id TEXT PRIMARY KEY,
            label TEXT,
            label_vi TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 6. Person Provenance Tracking
    print("📋 Creating person_refs table...")
    cursor.execute("""
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_refs_person ON person_refs(person_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_refs_source ON person_refs(source_name)")
    
    conn.commit()
    
    # Verify tables
    print("\n✅ Database created successfully!")
    print(f"   Location: {DB_FILE}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\n📦 Tables created:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   - {table[0]}: {count} rows")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ SCHEMA COMPLETE")
    print("=" * 60)
    
    return DB_FILE


def load_dila_reference():
    """Load DILA person data into reference table"""
    print("\n📋 Loading DILA reference data...")
    
    DILA_FILE = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_person" / "Buddhist_Studies_Person_Authority.xml"
    
    if not DILA_FILE.exists():
        print(f"⚠️ DILA file not found: {DILA_FILE}")
        return
    
    import xml.etree.ElementTree as ET
    
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    tree = ET.parse(DILA_FILE)
    root = tree.getroot()
    persons = root.findall('.//tei:person', ns)
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    inserted = 0
    for person in persons[:1000]:  # First 1000 for demo
        person_id = person.get('{http://www.w3.org/XML/1998/namespace}id')
        if not person_id:
            continue
        
        name_zh = ""
        name_ja = ""
        name_en = ""
        dynasty = ""
        bio = ""
        
        for persName in person.findall('tei:persName', ns):
            lang = persName.get('{http://www.w3.org/XML/1998/namespace}lang', '')
            if persName.text:
                if 'zho' in lang:
                    name_zh = persName.text
                elif 'jpn' in lang or 'ja' in lang:
                    name_ja = persName.text
                elif 'eng' in lang or 'en' in lang:
                    name_en = persName.text
        
        for note in person.findall('tei:note', ns):
            note_type = note.get('type', '')
            if note_type == 'dynasty' and note.text:
                dynasty = note.text
            elif note_type == 'concise' and note.text:
                bio = note.text[:500]
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO dila_reference (id, name_zh, name_ja, name_en, dynasty, bio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (person_id, name_zh, name_ja, name_en, dynasty, bio))
            inserted += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"   ✅ Inserted {inserted} DILA reference records")
    conn.close()


if __name__ == "__main__":
    create_schema()
    load_dila_reference()