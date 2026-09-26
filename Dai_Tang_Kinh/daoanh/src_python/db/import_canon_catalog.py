#!/usr/bin/env python3
"""
Import Mục Lục Đại Chánh Tân Tu vào SQLite
Data source: .doc file parsing / manual entry pattern
Schema: canon_catalog table
"""

import os
import sqlite3
import re
from datetime import datetime

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
DOC_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/muc_luc_dtk/5-Muc-Luc-Dai-Chanh-Tan-Tu-Dai-Tang-Kinh-Nguyen-Minh-Tien-Soan.doc'

def create_schema():
    """Create canon_catalog table"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Drop if exists
    conn.execute("DROP TABLE IF EXISTS canon_catalog")
    conn.execute("DROP TABLE IF EXISTS canon_author_mapping")
    conn.execute("DROP TABLE IF EXISTS ttl_canon_works")
    
    # Create canon_catalog table
    conn.execute("""
    CREATE TABLE canon_catalog (
        work_id INTEGER PRIMARY KEY AUTOINCREMENT,
        -- Title fields
        title_vi TEXT,                    -- Ca Diếp Kết Kinh (Vietnamese)
        title_zh TEXT,                   -- 迦葉結經 (Chinese full)
        title_search TEXT,              -- ca diep ket kinh (normalized for search)
        
        -- Author/Translator
        author_vi TEXT,                  -- An Thế Cao
        author_zh TEXT,                -- 安世高
        author_dila_id TEXT,            -- A000xxx (link to people)
        author_role TEXT DEFAULT 'translator',  -- 'translator', 'author', 'compiler'
        
        -- Era/Time
        era_vi TEXT,                     -- Hậu Hán (Vietnamese)
        era_zh TEXT,                   -- 後漢 (Chinese)
        year_start INTEGER,             -- Start year (e.g., 25)
        year_end INTEGER,               -- End year
        
        -- Location (CBETA reference)
        cbeta_id TEXT,                 -- Sh.2027
        location_text TEXT,             -- Q.49, Tr.4, Sh.2027
        volume INTEGER,                -- 1 quyển
        
        -- Source tracking
        source TEXT DEFAULT 'MucLucDaiChanh',
        verified INTEGER DEFAULT 0,
        search_rank INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Index for search
    conn.execute("CREATE INDEX idx_canon_title ON canon_catalog(title_search)")
    conn.execute("CREATE INDEX idx_canon_author ON canon_catalog(author_vi)")
    conn.execute("CREATE INDEX idx_canon_era ON canon_catalog(era_vi)")
    
    # Create author mapping table
    conn.execute("""
    CREATE TABLE canon_author_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_id INTEGER,
        author_name_vi TEXT,
        author_name_zh TEXT,
        author_dila_id TEXT,
        author_marcus_id TEXT,
        author_role TEXT,
        verified_source TEXT,
        created_at TEXT
    )
    """)
    
    # Create TTL works linking table
    conn.execute("""
    CREATE TABLE ttl_canon_works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ttl_filename TEXT,
        work_uri TEXT,
        work_id INTEGER,
        relation_type TEXT,
        created_at TEXT
    )
    """)
    
    conn.commit()
    print("✅ Schema created: canon_catalog, canon_author_mapping, ttl_canon_works")
    conn.close()

def parse_sample_data():
    """Show expected 5-line format from the doc"""
    print("\n=== Expected Data Format ===")
    print("Each work has 5 lines with information:")
    print("""
Line 1: Tên kinh sách (1 quyển)
Line 2: Niên đại (Hậu Hán)
Line 3: Tên dịch giả (An Thế Cao dịch)
Line 4: Số thứ tự, trang và số hiệu (Q. 49, Tr. 4, Sh. 2027)
Line 5: Tên tiếng Hoa đầy đủ (迦葉結經 (一卷) (後漢 安世高譯))

Example parsed:
{
    "title_vi": "Ca Diếp Kết Kinh",
    "era_vi": "Hậu Hán", 
    "author_vi": "An Thế Cao",
    "location_text": "Q. 49, Tr. 4, Sh. 2027",
    "title_zh": "迦葉結經 (一卷) (後漢 安世高譯)"
}
""")

def add_sample_data():
    """Add sample data to test"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Sample works (from user examples)
    sample_works = [
        {
            "title_vi": "Ca Diếp Kết Kinh",
            "title_zh": "迦葉結經 (一卷) (後漢 安世高譯)",
            "era_vi": "Hậu Hán",
            "era_zh": "後漢",
            "author_vi": "An Thế Cao",
            "author_zh": "安世高",
            "location_text": "Q. 49, Tr. 4, Sh. 2027",
            "volume": 1
        },
        {
            "title_vi": "Ca Diếp Phó Phật Bát Niết Bàn Kinh",
            "title_zh": "迦葉赴佛般涅槃經 (一卷) (東晉竺曇無蘭譯)",
            "era_vi": "Đông Tấn",
            "era_zh": "東晉", 
            "author_vi": "Trúc Đàm Vô Lan",
            "author_zh": "竺曇無蘭",
            "location_text": "Q.12, Tr. 1115, Sh. 393",
            "volume": 1
        }
    ]
    
    for work in sample_works:
        # Normalize for search
        title_search = work['title_vi'].lower().replace(' ', '')
        
        conn.execute("""
            INSERT INTO canon_catalog (
                title_vi, title_zh, title_search,
                era_vi, era_zh,
                author_vi, author_zh,
                location_text, volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            work['title_vi'],
            work['title_zh'],
            title_search,
            work['era_vi'],
            work['era_zh'],
            work['author_vi'],
            work['author_zh'],
            work['location_text'],
            work['volume']
        ))
    
    conn.commit()
    
    # Verify
    count = conn.execute("SELECT COUNT(*) FROM canon_catalog").fetchone()[0]
    print(f"✅ Added {count} sample works")
    
    # Show data
    cursor = conn.execute("SELECT work_id, title_vi, author_vi, era_vi FROM canon_catalog")
    for row in cursor:
        print(f"  {row[0]}: {row[1]} - {row[2]} ({row[3]})")
    
    conn.close()

def link_translators_to_dila():
    """Link translators to DILA people table"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Get all translators
    cursor = conn.execute("""
        SELECT DISTINCT author_vi, author_zh 
        FROM canon_catalog 
        WHERE author_vi IS NOT NULL
    """)
    
    linked = 0
    for author_vi, author_zh in cursor:
        if not author_vi:
            continue
        
        # Search in DILA people
        search_patterns = [
            f"%{author_vi}%",
            f"%{author_zh}%" if author_zh else None
        ]
        
        dila_id = None
        for pattern in search_patterns:
            if not pattern:
                continue
            row = conn.execute("""
                SELECT id, name_zh FROM people 
                WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 1
            """, (pattern, pattern)).fetchone()
            
            if row:
                dila_id = row[0]
                break
        
        if dila_id:
            conn.execute("""
                UPDATE canon_catalog 
                SET author_dila_id = ?, verified = 1
                WHERE author_vi = ?
            """, (dila_id, author_vi))
            linked += 1
            print(f"  ✅ {author_vi} -> {dila_id}")
    
    conn.commit()
    print(f"\n✅ Linked {linked} translators to DILA")
    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Import Mục Lục Đại Chánh Tân Tu")
    print("=" * 60)
    
    # Step 1: Create schema
    create_schema()
    
    # Step 2: Show expected format
    parse_sample_data()
    
    # Step 3: Add sample data
    add_sample_data()
    
    # Step 4: Link translators to DILA
    link_translators_to_dila()
    
    print("\n✅ Import complete!")
    print("\nNOTE: Due to .doc format issues, please:")
    print("1. Convert .doc to text/CSV manually, OR")
    print("2. Use admin panel to add works, OR")
    print("3. Provide data in JSON/CSV format")