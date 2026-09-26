#!/usr/bin/env python3
"""
Create SQLite Schema - Buddhist Central Database
DILA Authority Layer (Priority 1)
"""
import sqlite3
import os
from datetime import datetime

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
SQLITE_DIR = os.path.join(DATA_DIR, "sqlite")
BACKUP_DIR = os.path.join(SQLITE_DIR, "backup")

def create_schema(db_path):
    """Create comprehensive SQLite schema"""
    
    # Ensure directories exist
    os.makedirs(SQLITE_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # =====================
    # A. AUTHORITY LAYER
    # =====================
    
    # People table (DILA authority)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_vi TEXT,
            name_en TEXT,
            lineage TEXT,
            dynasty TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            dila_id TEXT,
            wiki_url TEXT,
            biography TEXT,
            sources TEXT,
            works TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Indexes for people
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_people_name_zh ON people(name_zh)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_people_name_vi ON people(name_vi)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_people_lineage ON people(lineage)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_people_dynasty ON people(dynasty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_people_dila_id ON people(dila_id)')
    
    # Places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_vi TEXT,
            name_en TEXT,
            lat REAL,
            lng REAL,
            country TEXT,
            province TEXT,
            source TEXT,
            dila_place_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_places_name_zh ON places(name_zh)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_places_country ON places(country)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_places_gps ON places(lat, lng)')
    
    # Networks table (Teacher/Disciple + Social connections)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            weight INTEGER DEFAULT 10,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people(id),
            FOREIGN KEY (target_id) REFERENCES people(id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_networks_person ON networks(person_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_networks_target ON networks(target_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_networks_relation ON networks(relation_type)')
    
    # Time periods table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_periods (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_en TEXT,
            start_year INTEGER,
            end_year INTEGER,
            era TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_years ON time_periods(start_year, end_year)')
    
    # =====================
    # B. CANON LAYER
    # =====================
    
    # Canons catalog
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS canons_catalog (
            text_id TEXT PRIMARY KEY,
            title_zh TEXT,
            title_en TEXT,
            author_id TEXT,
            author_name TEXT,
            canon_type TEXT,
            volume TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES people(id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_canons_title ON canons_catalog(title_zh)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_canons_author ON canons_catalog(author_id)')
    
    # Text mapping cross-reference
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS text_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taisho_id TEXT,
            cbeta_id TEXT,
            linhson_id TEXT,
            source TEXT
        )
    ''')
    
    # =====================
    # C. LEXICON LAYER
    # =====================
    
    # Lexicon/Dictionary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            definition TEXT,
            priority INTEGER DEFAULT 3,
            source TEXT,
            language TEXT DEFAULT 'zh',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lexicon_term ON lexicon(term)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lexicon_priority ON lexicon(priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lexicon_source ON lexicon(source)')
    
    # =====================
    # METADATA
    # =====================
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert schema version
    cursor.execute('''
        INSERT OR REPLACE INTO metadata (key, value, updated_at)
        VALUES (?, ?, ?)
    ''', ('schema_version', '1.0', datetime.utcnow().isoformat()))
    
    conn.commit()
    
    # Get table list
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cursor.fetchall()]
    
    conn.close()
    
    return tables

def main():
    db_path = os.path.join(SQLITE_DIR, "buddhist_db.sqlite")
    
    print("🗄️  Creating SQLite schema...")
    tables = create_schema(db_path)
    
    print(f"✅ Database created: {db_path}")
    print(f"   Tables: {len(tables)}")
    for t in tables:
        print(f"   - {t}")
    
    # Get size
    size = os.path.getsize(db_path)
    print(f"\n📊 Database size: {size:,} bytes ({size/1024/1024:.2f} MB)")

if __name__ == "__main__":
    main()