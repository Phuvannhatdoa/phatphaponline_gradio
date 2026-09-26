#!/usr/bin/env python3
"""
Entity Extraction Engine
Gán nhãn ĐỊA DANH và TU SĨ cho lexicon và SQLite
"""

import sqlite3
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"

DIA_DANH_PATTERNS = [
    r'chùa\s+', r'\s+chùa$', r'^chùa\s',
    r'tự\s+', r'\s+tự$', r'^tự\s',
    r'viện\s+', r'\s+viện$', r'^viện\s',
    r'tổ\s+đình', r'đình\s+',
    r'đạo\s+tràng', r'tràng\s+',
    r'tịnh\s+xá', r'tịnh\s+viện',
    r'bảo\s+tự',
    r'pháp\s+viện',
    r'quyết\s+tâm',
    r'ton\s+', r'tō',
]

TU_SI_PATTERNS = [
    r'hòa\s+thượng', r'hòa-thượng',
    r'thượng\s+tọa', r'thượng-tọa',
    r'đại\s+đức', r'đại-đức',
    r'thiền\s+sư', r'thiền-sư',
    r'pháp\s+sư', r'pháp-sư',
    r'tăng\s+trưởng',
    r'tăng\s+chủng',
    r'hóa\s+chủ',
    r'đạo\s+chủ',
    r'bồ\s+tát',
    r'ngài\s+',
]

PLACE_TYPES = {
    'chùa': 'ĐỊA DANH',
    'tự': 'ĐỊA DANH',
    'viện': 'ĐỊA DANH',
    'tổ đình': 'ĐỊA DANH',
    'đạo tràng': 'ĐỊA DANH',
    'tịnh xá': 'ĐỊA DANH',
    'bảo tự': 'ĐỊA DANH',
    'pháp viện': 'ĐỊA DANH',
    'ton': 'ĐỊA DANH',
}

MONK_TITLES = {
    'hòa thượng': 'TU SĨ',
    'thượng tọa': 'TU SĨ',
    'đại đức': 'TU SĨ',
    'thiền sư': 'TU SĨ',
    'pháp sư': 'TU SĨ',
    'tăng trưởng': 'TU SĨ',
    'tăng chủng': 'TU SĨ',
    'hóa chủ': 'TU SĨ',
    'đạo chủ': 'TU SĨ',
}


def extract_entity_type(text):
    """Detect entity type từ text"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    for keyword, etype in PLACE_TYPES.items():
        if keyword in text_lower:
            return etype
    
    for keyword, etype in MONK_TITLES.items():
        if keyword in text_lower:
            return etype
    
    return None


def update_lexicon_entities():
    """Update entity_type cho lexicon table"""
    print("\n🔍 Updating lexicon entity types...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("SELECT term, definition FROM lexicon WHERE entity_type IS NULL OR entity_type = ''")
    rows = cursor.fetchall()
    
    updated = 0
    for term, definition in rows:
        combined = f"{term} {definition or ''}"
        etype = extract_entity_type(combined)
        
        if etype:
            cursor.execute("UPDATE lexicon SET entity_type = ? WHERE term = ?", (etype, term))
            updated += 1
    
    conn.commit()
    print(f"   ✅ Updated {updated} entity types")
    
    cursor.execute("SELECT entity_type, COUNT(*) as cnt FROM lexicon WHERE entity_type != '' GROUP BY entity_type")
    stats = cursor.fetchall()
    print("\n📊 Entity Statistics:")
    for etype, cnt in stats:
        print(f"   {etype}: {cnt}")
    
    conn.close()


def create_entity_index():
    """Create index cho entity search"""
    print("\n📋 Creating entity index...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_type ON lexicon(entity_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_normalized ON lexicon(normalized)
    """)
    
    conn.commit()
    conn.close()
    print("   ✅ Indexes created")


def export_entity_json():
    """Export entities to JSON"""
    print("\n💾 Exporting entity JSON...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, normalized, entity_type, source, priority
        FROM lexicon
        WHERE entity_type IN ('ĐỊA DANH', 'TU SĨ')
        ORDER BY entity_type, priority
    """)
    rows = cursor.fetchall()
    
    entities = {
        'ĐỊA DANH': [],
        'TU SĨ': []
    }
    
    for term, normalized, etype, source, priority in rows:
        entities[etype].append({
            'term': term,
            'normalized': normalized,
            'source': source,
            'priority': priority
        })
    
    out_file = BASE_DIR / "data" / "indexed" / "entities.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Exported to {out_file}")
    print(f"   ĐỊA DANH: {len(entities['ĐỊA DANH'])}")
    print(f"   TU SĨ: {len(entities['TU SĨ'])}")
    
    conn.close()


if __name__ == "__main__":
    update_lexicon_entities()
    create_entity_index()
    export_entity_json()
    print("\n✅ Entity Extraction Complete")