#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_name_vi_map.py - ETL Script để tạo bảng name_vi_map
Mục tiêu: Map Vietnamese names từ Stardict với DILA và Marcus IDs

Usage:
    python build_name_vi_map.py [--dry-run] [--verbose]

Author: Agent Build (2026-04-27)
Task: feat-name-vi-map-etl
"""

import os, re, sqlite3, sys
from datetime import datetime

# Configuration
BASE_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"
DB_PATH = os.path.join(BASE_DIR, "data", "lineage.db")
STARDICT_PATH = os.path.join(BASE_DIR, "data", "dict", "daoanh_entities.txt")
LOG_PATH = os.path.join(BASE_DIR, "logs", "name_vi_map_etl.log")

class ETLError(Exception):
    pass

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    print(log_line)
    if os.path.exists(os.path.dirname(LOG_PATH)):
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

def parse_stardict_entries(filepath):
    """Parse stardict file và extract monk entries với Vietnamese names"""
    entries = []
    pattern = re.compile(r'^([A-ZÀ-ỹ][^\t]*?)\t@TU SĨ (.+)', re.UNICODE)
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in lines:
        m = pattern.match(line)
        if not m:
            continue
            
        vi_name = m.group(1).strip()
        bio = m.group(2)
        
        # Skip entries starting with number/dash/parentheses
        if re.match(r'^[0-9（.(]', vi_name):
            continue
            
        # Check Vietnamese name has real diacritics
        if not re.search(r'[àáạảãâăấậầẩẫẵóỏọỏôốộồổỗếểệễềìíịỉĩùúủụữưứừựữỳýỵỷỹđ]', vi_name):
            continue
        
        entry = {
            'name_vi': vi_name,
            'bio': bio,
            'name_zh': None,
            'birth_year': None,
            'death_year': None
        }
        
        # Extract years pattern: YYYY-YYYY hoặc YYYY-?
        years_match = re.search(r'\[([0-9?]+)[)-]([0-9?]+)\]', bio)
        if years_match:
            try:
                entry['birth_year'] = int(years_match.group(1)) if years_match.group(1).isdigit() else None
                entry['death_year'] = int(years_match.group(2)) if years_match.group(2).isdigit() else None
            except ValueError:
                pass
        
        # Extract CJK names from bio - focus on person names (2-4 chars typical)
        # Priority: extract names before 師 (monk master) or other patterns
        cjk_names = set()
        
        # Pattern 1: Names before 師 (e.g., "慧能師", "鑑堂一師")
        master_pattern = re.findall(r'[\u4e00-\u9fff]{2,4}師', bio)
        for name in master_pattern:
            cjk_names.add(name.replace('師', ''))
        
        # Pattern 2: Names in parentheses directly (e.g., "(慧能)" or "（慧能）")
        paren_pattern = re.findall(r'[\(\（][\u4e00-\u9fff]{2,4}[\)\）]', bio)
        for name in paren_pattern:
            cjk_names.add(name[1:-1])
        
        # Pattern 3: Generic CJK 2-4 char sequences (filter out common words)
        common_words = {'公司', '寺廟', '法師', '和尚', '菩薩', '如來', '佛教', '經文', '經書'}
        generic_cjk = re.findall(r'[\u4e00-\u9fff]{2,4}', bio)
        for name in generic_cjk:
            if name not in common_words:
                cjk_names.add(name)
        
        entry['cjk_candidates'] = list(cjk_names)
        
        entries.append(entry)
    
    log(f"Parsed {len(entries)} valid monk entries from stardict")
    return entries

def load_dila_monk_names(conn):
    """Load DILA monk names for matching"""
    query = """
        SELECT id, name_zh, birth_year, death_year 
        FROM people 
        WHERE name_zh IS NOT NULL AND name_zh != ''
    """
    monks = {}
    cursor = conn.execute(query)
    for row in cursor.fetchall():
        dila_id, name_zh, birth, death = row
        if name_zh:
            # Key: name_zh + years for exact matching
            key = f"{name_zh}|{birth}|{death}"
            monks[key] = {
                'dila_id': dila_id,
                'name_zh': name_zh,
                'birth_year': birth,
                'death_year': death
            }
    log(f"Loaded {len(monks)} DILA monks with Chinese names")
    return monks

def load_marcus_monks(conn):
    """Load Marcus monks for matching"""
    query = """
        SELECT DISTINCT teacher_id, teacher_label FROM marcus_networks 
        WHERE teacher_label IS NOT NULL AND teacher_label != ''
        UNION
        SELECT DISTINCT student_id, student_label FROM marcus_networks 
        WHERE student_label IS NOT NULL AND student_label != ''
    """
    monk_ids = {}  # name_zh -> set of IDs
    
    cursor = conn.execute(query)
    for row in cursor.fetchall():
        monk_id, label = row
        if label:
            if label not in monk_ids:
                monk_ids[label] = set()
            monk_ids[label].add(monk_id)
    
    log(f"Loaded {len(monk_ids)} unique Marcus monk labels")
    return monk_ids

def match_entries_to_dila(entry, dila_monks):
    """Match stardict entry to DILA using name_zh + years"""
    if not entry['cjk_candidates']:
        return None
    
    # Try exact match with years first
    for cjk in entry['cjk_candidates']:
        # Key with years
        key = f"{cjk}|{entry['birth_year']}|{entry['death_year']}"
        if key in dila_monks:
            return dila_monks[key]['dila_id']
        
        # Key without years
        key_no_years = f"{cjk}|None|None"
        if key_no_years in dila_monks:
            return dila_monks[key_no_years]['dila_id']
    
    return None

def match_entries_to_marcus(entry, marcus_monks):
    """Match stardict entry to Marcus using Chinese name"""
    if not entry['cjk_candidates']:
        return []
    
    matched_ids = set()
    for cjk in entry['cjk_candidates']:
        if cjk in marcus_monks:
            matched_ids.update(marcus_monks[cjk])
    
    return list(matched_ids) if matched_ids else []

def create_table(conn):
    """Create name_vi_map table"""
    conn.execute("DROP TABLE IF EXISTS name_vi_map")
    conn.execute("""
        CREATE TABLE name_vi_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT NOT NULL,
            name_zh TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            bio_snippet TEXT,
            dila_id TEXT,
            marcus_ids TEXT,
            source TEXT DEFAULT 'daoanh_dict',
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name_vi, name_zh)
        )
    """)
    conn.execute("CREATE INDEX idx_name_zh ON name_vi_map(name_zh)")
    conn.execute("CREATE INDEX idx_name_vi ON name_vi_map(name_vi)")
    conn.execute("CREATE INDEX idx_dila_id ON name_vi_map(dila_id)")
    conn.commit()
    log("Created name_vi_map table")

def insert_mapping(conn, entry, dila_id, marcus_ids):
    """Insert a single mapping into name_vi_map"""
    marcus_ids_str = ",".join(marcus_ids) if marcus_ids else None
    
    try:
        conn.execute("""
            INSERT OR IGNORE INTO name_vi_map 
            (name_vi, name_zh, birth_year, death_year, bio_snippet, dila_id, marcus_ids, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry['name_vi'],
            entry['cjk_candidates'][0] if entry['cjk_candidates'] else None,
            entry['birth_year'],
            entry['death_year'],
            entry['bio'][:500] if entry['bio'] else None,  # Truncate bio to 500 chars
            dila_id,
            marcus_ids_str,
            1.0 if dila_id or marcus_ids else 0.5
        ))
    except sqlite3.IntegrityError as e:
        log(f"Duplicate entry: {entry['name_vi']} - {e}", "WARN")

def run_etl(dry_run=False, verbose=False):
    """Main ETL execution"""
    log("="*60)
    log("Starting ETL: build_name_vi_map")
    log("="*60)
    
    start_time = datetime.now()
    
    # Connect to database
    if not os.path.exists(DB_PATH):
        raise ETLError(f"Database not found: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Step 1: Parse stardict
        log("Step 1: Parsing stardict entries...")
        entries = parse_stardict_entries(STARDICT_PATH)
        
        # Step 2: Load DILA monks
        log("Step 2: Loading DILA monks...")
        dila_monks = load_dila_monk_names(conn)
        
        # Step 3: Load Marcus monks
        log("Step 3: Loading Marcus monks...")
        marcus_monks = load_marcus_monks(conn)
        
        if dry_run:
            log("DRY RUN MODE - Skipping database operations")
            log(f"Sample entries: {entries[:5]}")
            return
        
        # Step 4: Create table
        log("Step 4: Creating name_vi_map table...")
        create_table(conn)
        
        # Step 5: Process entries
        log("Step 5: Processing entries and inserting mappings...")
        dila_matches = 0
        marcus_matches = 0
        both_matches = 0
        
        for entry in entries:
            dila_id = match_entries_to_dila(entry, dila_monks)
            marcus_ids = match_entries_to_marcus(entry, marcus_monks)
            
            if dila_id:
                dila_matches += 1
            if marcus_ids:
                marcus_matches += 1
            if dila_id and marcus_ids:
                both_matches += 1
            
            insert_mapping(conn, entry, dila_id, marcus_ids)
        
        conn.commit()
        
        # Step 6: Summary
        total = conn.execute("SELECT COUNT(*) FROM name_vi_map").fetchone()[0]
        with_dila = conn.execute("SELECT COUNT(*) FROM name_vi_map WHERE dila_id IS NOT NULL").fetchone()[0]
        with_marcus = conn.execute("SELECT COUNT(*) FROM name_vi_map WHERE marcus_ids IS NOT NULL").fetchone()[0]
        
        log("="*60)
        log("ETL COMPLETE - SUMMARY")
        log("="*60)
        log(f"Total entries in name_vi_map: {total}")
        log(f"Matches with DILA: {dila_matches} ({dila_matches*100/len(entries):.1f}%)")
        log(f"Matches with Marcus: {marcus_matches} ({marcus_matches*100/len(entries):.1f}%)")
        log(f"Matches with both: {both_matches}")
        log(f"Entries processed: {len(entries)}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        log(f"Execution time: {elapsed:.2f} seconds")
        log("="*60)
        
        return {
            'total': total,
            'dila_matches': dila_matches,
            'marcus_matches': marcus_matches,
            'both_matches': both_matches,
            'elapsed': elapsed
        }
        
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build name_vi_map table")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    try:
        result = run_etl(dry_run=args.dry_run, verbose=args.verbose)
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    except ETLError as e:
        log(f"ETL Error: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected Error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)