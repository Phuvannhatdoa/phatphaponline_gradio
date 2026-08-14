#!/usr/bin/env python3
"""
Multi-Dict Merger v10
- Overlay Strategy: ThamKhao (3) → PhoThong (2) → HanLam (1)
- Giữ tất cả entries, đánh dấu nguồn
- Entity Auto-Tagging: Chùa/Tu sĩ
- FTS5 Full-text Search
- NFC Normalization
"""

import sqlite3
import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
MERGED_JSON = BASE_DIR / "data" / "dict" / "merged.json"

DICT_GROUPS = {
    3: BASE_DIR / "data" / "dictionaries" / "tudien" / "tham_khao",
    2: BASE_DIR / "data" / "dictionaries" / "tudien" / "pho_thong",
    1: BASE_DIR / "data" / "dictionaries" / "tudien" / "han_lam",
}

EXTRA_DICTS = BASE_DIR / "data" / "dictionaries"

TUDIEN_EXTRA = BASE_DIR / "data" / "dictionaries" / "tudien"

PLACE_KEYWORDS = ['chùa', 'tự', 'viện', 'tổ đình', 'tịnh xá', 'bảo tự', 'pháp viện', 'ton']
MONK_KEYWORDS = ['hòa thượng', 'thượng tọa', 'đại đức', 'thiền sư', 'pháp sư', 'tăng trưởng', 'tăng chủng']

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ python-docx not available, .docx files will be skipped")


def nfc(text):
    """Unicode NFC Normalization"""
    if not text:
        return ""
    return unicodedata.normalize('NFC', text)


def remove_accents(text):
    """Remove Vietnamese accents for search"""
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def parse_term_line(line):
    """Parse term line: remove ● prefix, extra whitespace"""
    line = line.strip()
    if line.startswith('●'):
        line = line[1:].strip()
    return line.strip()


def detect_entity(term, definition):
    """Auto-detect entity type: ĐỊA DANH or TU SĨ"""
    text = f"{term} {definition or ''}".lower()
    
    for kw in MONK_KEYWORDS:
        if kw in text:
            return "TU SĨ"
    
    for kw in PLACE_KEYWORDS:
        if kw in text:
            return "ĐỊA DANH"
    
    return ""


def create_schema():
    """Create SQLite schema with FTS5"""
    print("\n📋 Creating schema...")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS lexicon")
    cursor.execute("""
        CREATE TABLE lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            normalized TEXT NOT NULL,
            definition TEXT,
            source TEXT NOT NULL,
            priority INTEGER CHECK(priority IN (1,2,3)),
            entity_type TEXT,
            lang TEXT DEFAULT 'vi',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term, source)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_priority ON lexicon(priority)")
    cursor.execute("CREATE INDEX idx_entity ON lexicon(entity_type)")
    cursor.execute("CREATE INDEX idx_normalized ON lexicon(normalized)")
    cursor.execute("CREATE INDEX idx_source ON lexicon(source)")
    
    cursor.execute("DROP TABLE IF EXISTS lexicon_fts")
    cursor.execute("""
        CREATE VIRTUAL TABLE lexicon_fts USING fts5(
            term, definition, content=lexicon, content_rowid=id
        )
    """)
    
    conn.commit()
    print("   ✅ Schema created with FTS5")
    return conn


def load_txt_file(filepath, source, priority):
    """Load entries from a .txt file (StarDict format)"""
    entries = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]
    except Exception as e:
        print(f"   ⚠️ Error reading {filepath}: {e}")
        return entries
    
    i = 0
    while i < len(lines) - 1:
        term_line = lines[i].strip()
        defn_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        
        if not term_line:
            i += 1
            continue
        
        term = parse_term_line(term_line)
        
        if not term or len(term) < 2:
            i += 1
            continue
        
        definition = parse_term_line(defn_line) if defn_line else ""
        
        entity_type = detect_entity(term, definition)
        
        entries.append({
            'term': nfc(term),
            'normalized': nfc(remove_accents(term)),
            'definition': nfc(definition)[:2000],
            'source': source,
            'priority': priority,
            'entity_type': entity_type
        })
        
        i += 2
    
    return entries


def load_docx_file(filepath, source, priority):
    """Load entries from a .docx file (Phap Quang format)"""
    entries = []
    
    if not DOCX_AVAILABLE:
        return entries
    
    try:
        doc = docx.Document(filepath)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
    except Exception as e:
        print(f"   ⚠️ Error reading {filepath}: {e}")
        return entries
    
    lines = full_text
    i = 0
    while i < len(lines) - 1:
        term_line = lines[i].strip()
        
        if not term_line or len(term_line) < 2:
            i += 1
            continue
        
        term = parse_term_line(term_line)
        
        defn_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        definition = parse_term_line(defn_line) if defn_line else ""
        
        entity_type = detect_entity(term, definition)
        
        entries.append({
            'term': nfc(term),
            'normalized': nfc(remove_accents(term)),
            'definition': nfc(definition)[:2000],
            'source': source,
            'priority': priority,
            'entity_type': entity_type
        })
        
        i += 2
    
    return entries


def scan_extra_dicts():
    """Scan extra .docx and .txt files in /dictionaries/"""
    if not EXTRA_DICTS.exists():
        return []
    
    all_entries = []
    all_files = list(EXTRA_DICTS.glob("*.txt")) + list(EXTRA_DICTS.glob("*.docx"))
    
    print(f"\n📂 Loading Extra Dicts ({len(all_files)} files)...")
    
    for filepath in all_files:
        if filepath.suffix == '.txt':
            entries = load_txt_file(filepath, filepath.stem, 3)
        elif filepath.suffix == '.docx':
            entries = load_docx_file(filepath, filepath.stem, 3)
        else:
            continue
        
        if entries:
            all_entries.extend(entries)
            print(f"   ✅ {filepath.name}: {len(entries)} entries")
    
    return all_entries


def scan_dict_group(priority):
    """Scan all .txt and .docx files in a dict group"""
    group_path = DICT_GROUPS.get(priority)
    if not group_path or not group_path.exists():
        print(f"   ⚠️ Path not found: {group_path}")
        return []
    
    files = list(group_path.rglob("*.txt")) + list(group_path.rglob("*.docx"))
    
    group_name = {3: "ThamKhao", 2: "PhoThong", 1: "HanLam"}[priority]
    print(f"\n📂 Loading {group_name} (priority {priority})...")
    print(f"   Found {len(files)} files (.txt + .docx)")
    
    all_entries = []
    for filepath in files:
        if filepath.suffix == '.txt':
            entries = load_txt_file(filepath, filepath.stem, priority)
        else:
            entries = load_docx_file(filepath, filepath.stem, priority)
        
        if entries:
            all_entries.extend(entries)
            print(f"   ✅ {filepath.name}: {len(entries)} entries")
    
    return all_entries


def merge_dicts():
    """Main merge function"""
    print("=" * 60)
    print("🚀 Multi-Dict Merger v10")
    print("=" * 60)
    
    conn = create_schema()
    cursor = conn.cursor()
    
    merged = []
    stats = {1: 0, 2: 0, 3: 0}
    
    for priority in [3, 2, 1]:
        entries = scan_dict_group(priority)
        
        for entry in entries:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO lexicon 
                    (term, normalized, definition, source, priority, entity_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry['term'],
                    entry['normalized'],
                    entry['definition'],
                    entry['source'],
                    entry['priority'],
                    entry['entity_type']
                ))
                
                if cursor.rowcount > 0:
                    merged.append(entry)
                    stats[priority] += 1
                    
            except Exception as e:
                pass
        
        conn.commit()
        print(f"   📊 Added {stats[priority]} new entries from priority {priority}")
    
    extra_entries = scan_extra_dicts()
    for entry in extra_entries:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO lexicon 
                (term, normalized, definition, source, priority, entity_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry['term'],
                entry['normalized'],
                entry['definition'],
                entry['source'],
                entry['priority'],
                entry['entity_type']
            ))
            if cursor.rowcount > 0:
                merged.append(entry)
        except:
            pass
    conn.commit()
    
    cursor.execute("""
        INSERT INTO lexicon_fts(rowid, term, definition)
        SELECT id, term, definition FROM lexicon
    """)
    conn.commit()
    
    total = sum(stats.values())
    print(f"\n📊 Total merged: {total} entries")
    print(f"   ThamKhao (P3): {stats[3]}")
    print(f"   PhoThong (P2): {stats[2]}")
    print(f"   HanLam  (P1): {stats[1]}")
    
    cursor.execute("SELECT entity_type, COUNT(*) FROM lexicon WHERE entity_type != '' GROUP BY entity_type")
    entity_stats = cursor.fetchall()
    print(f"\n📊 Entity Distribution:")
    for etype, cnt in entity_stats:
        print(f"   {etype}: {cnt}")
    
    conn.close()
    
    with open(MERGED_JSON, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved to {MERGED_JSON}")
    
    return merged


def search_fts(query, limit=10):
    """FTS5 search"""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT lexicon.term, lexicon.definition, lexicon.entity_type, lexicon_fts.rank
        FROM lexicon_fts
        JOIN lexicon ON lexicon_fts.rowid = lexicon.id
        WHERE lexicon_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'term': row[0],
            'definition': row[1][:200],
            'entity_type': row[2],
            'rank': row[3]
        })
    
    conn.close()
    return results


if __name__ == "__main__":
    merge_dicts()
    
    print("\n🧪 FTS5 Test:")
    results = search_fts("chùa*", 5)
    for r in results:
        print(f"   → {r['term']} [{r['entity_type']}]")
    
    print("\n✅ Multi-Dict Merger Complete")
