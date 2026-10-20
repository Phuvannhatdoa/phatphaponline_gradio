#!/usr/bin/env python3
"""
Comprehensive Master SQLite Schema v2
All Authority Tables + Kinh điển + Lexicon

Schema:
- A. Authority Layer: people, places, networks, time_periods, conflicts
- B. Kinh điển: canons_catalog, text_mapping  
- C. Lexicon: lexicon (22 dictionaries)

Usage: python comprehensive_schema.py
"""

import sqlite3
import os
import json
import re
from pathlib import Path
from datetime import datetime
import unicodedata

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"

# Data source paths
DILA_PLACE_FILE = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_place" / "Buddhist_Studies_Place_Authority.xml"
DILA_PERSON_FILE = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_person" / "Buddhist_Studies_Person_Authority.xml"
STARDICT_FILE = BASE_DIR / "data" / "dict" / "merged.json"


def nfc_normalize(text):
    """Unicode NFC normalization"""
    if not text:
        return ""
    return unicodedata.normalize('NFC', text)


def remove_accents(text):
    """Remove Vietnamese accents for normalized field"""
    if not text:
        return ""
    replacements = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
    }
    result = []
    for c in text.lower():
        result.append(replacements.get(c, c))
    return ''.join(result)


def create_comprehensive_schema():
    """Create all SQLite tables"""
    print("=" * 60)
    print("🪷 COMPREHENSIVE MASTER SCHEMA v2")
    print("=" * 60)
    
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # ==================== A. AUTHORITY LAYER ====================
    
    # A.1 people - People from DILA Authority + sect (tông phái)
    print("\n📋 Creating people table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
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
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_sect ON people(sect)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_dynasty ON people(dynasty)")
    
    # A.2 places - Temples from DILA Place Authority + GPS
    print("📋 Creating places table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_vi TEXT,
            name_en TEXT,
            location TEXT,
            gps_lat REAL,
            gps_long REAL,
            address TEXT,
            province TEXT,
            country TEXT DEFAULT 'Vietnam',
            place_type TEXT,
            source_origin TEXT DEFAULT 'DILA',
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_province ON places(province)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_type ON places(place_type)")
    
    # A.3 networks - Relationships (Thầy/Trò, Đồng môn) with weight
    print("📋 Creating networks table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monk_id TEXT NOT NULL,
            related_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            entity_type TEXT,
            source_origin TEXT NOT NULL CHECK(source_origin IN ('Marcus', 'DILA', 'Admin')),
            weight INTEGER DEFAULT 1 CHECK(weight IN (1, 2, 3)),
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(monk_id, related_id, source_origin)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_networks_monk ON networks(monk_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_networks_source ON networks(source_origin)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_networks_rel ON networks(relation_type)")
    
    # A.4 time_periods - Historical periods
    print("📋 Creating time_periods table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_periods (
            id TEXT PRIMARY KEY,
            period_name TEXT NOT NULL,
            period_name_zh TEXT,
            period_name_vi TEXT,
            start_year INTEGER,
            end_year INTEGER,
            era_name TEXT,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_periods_name ON time_periods(period_name)")
    
    # A.5 conflicts - Lineage conflicts (DILA vs Marcus)
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_monk ON conflicts(monk_id)")
    
    # ==================== B. KINH ĐIỂN LAYER ====================
    
    # B.1 canons_catalog - Multi-canon catalog (Taisho, CBETA, etc)
    print("📋 Creating canons_catalog table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canons_catalog (
            id TEXT PRIMARY KEY,
            canon_name TEXT NOT NULL,
            canon_code TEXT NOT NULL,
            volume TEXT,
            title_zh TEXT,
            title_vi TEXT,
            title_en TEXT,
            author TEXT,
            year INTEGER,
            pages TEXT,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_canons_name ON canons_catalog(canon_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_canons_code ON canons_catalog(canon_code)")
    
    # B.2 text_mapping - Cross-reference between canons
    print("📋 Creating text_mapping table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS text_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            canon TEXT NOT NULL,
            mapping_type TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_id, target_id, canon)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mapping_source ON text_mapping(source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mapping_target ON text_mapping(target_id)")
    
    # ==================== C. LEXICON LAYER ====================
    
    # C.1 lexicon - StarDict academic hub (22 dictionaries)
    print("📋 Creating lexicon table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            normalized TEXT NOT NULL,
            definition TEXT,
            source TEXT NOT NULL,
            priority INTEGER DEFAULT 3 CHECK(priority IN (1, 2, 3)),
            entity_type TEXT,
            lang TEXT DEFAULT 'vi',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term, source)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_term ON lexicon(term)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_normalized ON lexicon(normalized)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_source ON lexicon(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_priority ON lexicon(priority)")
    
    # Additional auxiliary tables
    print("📋 Creating resolutions_log table...")
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
    
    conn.commit()
    
    # Verify tables
    print("\n✅ Schema created successfully!")
    print(f"   Database: {DB_FILE}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\n📦 Tables created:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   - {table[0]}: {count} rows")
    
    conn.close()
    
    return DB_FILE


def load_places_from_dila():
    """Load places from DILA Place Authority XML"""
    print("\n📋 Loading DILA Place data...")
    
    if not DILA_PLACE_FILE.exists():
        print(f"⚠️ DILA Place file not found: {DILA_PLACE_FILE}")
        return
    
    import xml.etree.ElementTree as ET
    
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    tree = ET.parse(DILA_PLACE_FILE)
    root = tree.getroot()
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    places = root.findall('.//tei:place', ns)
    print(f"   Found {len(places)} places")
    
    inserted = 0
    for place in places[:5000]:  # First 5000 for demo
        place_id = place.get('{http://www.w3.org/XML/1998/namespace}id')
        if not place_id:
            continue
        
        name_zh = ""
        name_vi = ""
        location = ""
        province = ""
        
        for placeName in place.findall('tei:placeName', ns):
            if placeName.text:
                lang = placeName.get('{http://www.w3.org/XML/1998/namespace}lang', '')
                if 'zho' in lang:
                    name_zh = placeName.text
                elif 'eng' in lang or 'en' in lang:
                    name_en = placeName.text
        
        # Get location info
        for note in place.findall('tei:note', ns):
            note_type = note.get('type', '')
            if note_type == 'location' and note.text:
                location = note.text[:200]
            elif note_type == 'province' and note.text:
                province = note.text
        
        # Get coordinates (if available)
        lat = None
        long = None
        for geo in place.findall('tei:geo', ns):
            if geo.text:
                coords = geo.text.split()
                if len(coords) >= 2:
                    try:
                        lat = float(coords[0])
                        long = float(coords[1])
                    except:
                        pass
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO places (id, name_zh, name_vi, location, province, gps_lat, gps_long)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (place_id, name_zh, name_vi, location, province, lat, long))
            inserted += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"   ✅ Inserted {inserted} places")
    conn.close()


def load_lexicon_from_stardict():
    """Load lexicon from StarDict merged.json"""
    print("\n📋 Loading StarDict lexicon...")
    
    if not STARDICT_FILE.exists():
        print(f"⚠️ StarDict file not found: {STARDICT_FILE}")
        return
    
    with open(STARDICT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    print(f"   Found {len(data)} terms")
    
    # Priority mapping for common dictionaries
    priority_map = {
        'HanLam': 1,  # Hàn Lâm
        'PhatQuang': 1,
        'Vuon': 2,  # Phổ Thông
        'Trieu': 2,
        'Bien': 3,  # Tham Khảo
    }
    
    inserted = 0
    for term, value in list(data.items())[:5000]:  # First 5000 for demo
        if not term:
            continue
        
        # Get definition
        definition = ""
        source = "Unknown"
        priority = 3
        
        if isinstance(value, dict):
            definition = value.get('definition', '')[:500]
            source = value.get('source', 'Unknown')
            priority = priority_map.get(source, 3)
        
        # Normalize
        normalized = remove_accents(term)
        
        # Entity type detection
        entity_type = ""
        lower_term = term.lower()
        if 'chùa' in lower_term or 'tự' in lower_term:
            entity_type = 'chua'
        elif 'tịnh xá' in lower_term:
            entity_type = 'tinhxa'
        elif 'thiền viện' in lower_term:
            entity_type = 'thienvien'
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO lexicon (term, normalized, definition, source, priority, entity_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (term, normalized, definition, source, priority, entity_type))
            inserted += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"   ✅ Inserted {inserted} lexicon terms")
    conn.close()


if __name__ == "__main__":
    create_comprehensive_schema()
    load_places_from_dila()
    load_lexicon_from_stardict()
    print("\n" + "=" * 60)
    print("✅ COMPREHENSIVE SCHEMA COMPLETE")
    print("=" * 60)