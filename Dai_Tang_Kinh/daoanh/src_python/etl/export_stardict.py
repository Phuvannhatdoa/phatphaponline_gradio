#!/usr/bin/env python3
"""
StarDict Exporter
Xuất lexicon đã hợp nhất ra định dạng StarDict (daoanh_dict.txt)
Định dạng: term\tdefinition
"""

import sqlite3
import json
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
OUTPUT_FILE = BASE_DIR / "data" / "dict" / "daoanh_dict.txt"


def export_stardict():
    """Export lexicon to StarDict format"""
    print("\n📤 Exporting to StarDict format...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, definition, entity_type, source, priority
        FROM lexicon
        WHERE term IS NOT NULL AND term != ''
        ORDER BY priority, term
    """)
    rows = cursor.fetchall()
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    exported = 0
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for term, definition, etype, source, priority in rows:
            if not definition:
                definition = ""
            
            definition = definition.strip()
            
            if etype:
                definition = f"[{etype}] {definition}"
            
            if source:
                definition = f"{definition} ★Nguồn: {source}"
            
            line = f"{term}\t{definition}\n"
            f.write(line)
            exported += 1
    
    conn.close()
    
    print(f"   ✅ Exported {exported} terms to {OUTPUT_FILE}")
    return exported


def export_with_entity_tags():
    """Export với entity type tags riêng"""
    print("\n📤 Exporting with entity tags...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, definition, entity_type, source, priority
        FROM lexicon
        WHERE entity_type IN ('ĐỊA DANH', 'TU SĨ')
        ORDER BY entity_type, priority, term
    """)
    rows = cursor.fetchall()
    
    entities_output = BASE_DIR / "data" / "dict" / "daoanh_entities.txt"
    
    with open(entities_output, 'w', encoding='utf-8') as f:
        for term, definition, etype, source, priority in rows:
            if not definition:
                definition = ""
            
            definition = definition.strip()
            tag = f"@{etype}"
            line = f"{term}\t{tag} {definition}\n"
            f.write(line)
    
    conn.close()
    
    print(f"   ✅ Exported to {entities_output}")
    return len(rows)


def get_export_stats():
    """Get export statistics"""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM lexicon")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lexicon WHERE entity_type = 'ĐỊA DANH'")
    dia_danh = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lexicon WHERE entity_type = 'TU SĨ'")
    tu_si = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lexicon WHERE entity_type IS NULL OR entity_type = ''")
    other = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'ĐỊA DANH': dia_danh,
        'TU SĨ': tu_si,
        'OTHER': other
    }


if __name__ == "__main__":
    print("🚀 StarDict Exporter")
    print("=" * 40)
    
    stats = get_export_stats()
    print(f"\n📊 Lexicon Statistics:")
    print(f"   Total: {stats['total']}")
    print(f"   ĐỊA DANH: {stats['ĐỊA DANH']}")
    print(f"   TU SĨ: {stats['TU SĨ']}")
    print(f"   OTHER: {stats['OTHER']}")
    
    export_stardict()
    export_with_entity_tags()
    
    print("\n✅ StarDict Export Complete")
    
    print(f"\n📁 Output files:")
    print(f"   {OUTPUT_FILE}")
    print(f"   {BASE_DIR / 'data' / 'dict' / 'daoanh_entities.txt'}")