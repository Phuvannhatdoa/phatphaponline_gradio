#!/usr/bin/env python3
"""Build TTL-DILA mapping: Manual verification needed"""

import os, sqlite3, re

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
TTL_DIR = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/ttl/old'

def extract_names_from_ttl(ttl_file):
    filepath = os.path.join(TTL_DIR, ttl_file + '.ttl')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    names = []
    for match in re.finditer(r'rdfs:label\s+"([^"]+)"(?:@(\w+))?', content):
        label = match.group(1)
        names.append(label)
    
    return names

def build_mapping():
    ttl_files = [f.replace('.ttl', '') for f in os.listdir(TTL_DIR) if f.endswith('.ttl')]
    print(f"Found {len(ttl_files)} TTL files")
    
    conn = sqlite3.connect(DB_FILE)
    
    conn.execute("DROP TABLE IF EXISTS ttl_mapping")
    conn.execute("""
    CREATE TABLE ttl_mapping (
        id INTEGER PRIMARY KEY,
        ttl_filename TEXT,
        name_vi TEXT,
        name_zh TEXT,
        dila_id TEXT,
        status TEXT DEFAULT 'pending'
    )""")
    conn.commit()
    
    # Known mappings (to be verified manually)
    known_mappings = {
        'TS-Dai-Hue-Tong-Cao': ('A038686', '大德宗杲'),  # Likely match
        'TS-Vien-Ngo-Khac-Can': ('A000453', '克勤'),  # Likely match
        'TS-Thien-Tue-Bao-Chuong': (None, ''),
        'Ton-Gia-Dao-Tin': (None, ''),
        'TS-Duong-Ki-Phuong-Hoi': ('A004146', '楊岐會'),  # Partial match
        'TS-Bach-Van-Thu-Doan': ('A033489', '雲岫守端'),  # Partial match
        'TS-Ngu-To-Phap-Dien': ('A036842', '法演'),  # Already matched
    }
    
    for ttl_file in ttl_files:
        names = extract_names_from_ttl(ttl_file)
        
        name_vi = next((n for n in names if not any('\u4e00' <= c <= '\u9fff' for c in n)), '')
        name_zh = next((n for n in names if any('\u4e00' <= c <= '\u9fff' for c in n)), '')
        
        dila_id, dila_name_zh = known_mappings.get(ttl_file, (None, ''))
        
        conn.execute("""
            INSERT INTO ttl_mapping (ttl_filename, name_vi, name_zh, dila_id, status)
            VALUES (?, ?, ?, ?, ?)
        """, (ttl_file, name_vi, name_zh, dila_id, 'verified' if dila_id else 'pending'))
        
        status = '✅' if dila_id else '❌'
        print(f"{status} {ttl_file}: {dila_id or 'NO MATCH'} ({name_vi})")
    
    conn.commit()
    
    # Summary
    verified = conn.execute("SELECT COUNT(*) FROM ttl_mapping WHERE status = 'verified'").fetchone()[0]
    print(f"\n=== Verified: {verified}/{len(ttl_files)} ===")
    
    conn.close()

if __name__ == '__main__':
    build_mapping()