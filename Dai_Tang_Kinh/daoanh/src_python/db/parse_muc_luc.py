#!/usr/bin/env python3
"""
Extract canon works from Mục Lục Đại Chánh Tân Tu (.doc via catdoc)
Format: 5 lines per work
"""

import re
import sqlite3
import os

DOC_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/muc_luc_dtk/5-Muc-Luc-Dai-Chanh-Tan-Tu-Dai-Tang-Kinh-Nguyen-Minh-Tien-Soan.doc'
DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
TXT_FILE = '/tmp/muc_luc.txt'

def extract_and_parse():
    """Extract text from .doc and parse works"""
    
    # Extract .doc to text
    print("Extracting .doc to text...")
    os.system(f'catdoc "{DOC_FILE}" 2>/dev/null > "{TXT_FILE}"')
    
    # Read extracted text
    with open(TXT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    works = []
    i = 0
    current_work = {}
    
    print(f"Processing {len(lines)} lines...")
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect start of new work entry
        if line.startswith('● Tên kinh sách:'):
            # Save previous work if exists
            if current_work and 'title_vi' in current_work:
                works.append(current_work)
            
            # Parse title (remove ● Tên kinh sách: ")
            title = line.replace('● Tên kinh sách:', '').strip().strip('"')
            
            # Handle multi-line title
            if '(' in title and ')' not in title:
                # Title spans multiple lines
                while i + 1 < len(lines) and ')' not in lines[i + 1].strip():
                    i += 1
                    title += ' ' + lines[i].strip()
                title = title.rstrip('"')
            
            current_work = {'title_vi': title}
        
        elif line.startswith('● Thông tin niên đại:') or line.startswith('● Thông tin niên đại :'):
            era = line.replace('● Thông tin niên đại:', '').replace('● Thông tin niên đại :', '').strip().strip('"')
            current_work['era_vi'] = era
        
        elif line.startswith('● Tên dịch giả:') or line.startswith('● Tên dịch giả :'):
            author = line.replace('● Tên dịch giả:', '').replace('● Tên dịch giả :', '').strip().strip('"')
            current_work['author_vi'] = author
        
        elif line.startswith('● Số thứ tự, trang và số hiệu:') or line.startswith('● Số thứ tự, trang và số hiệu :'):
            location = line.replace('● Số thứ tự, trang và số hiệu:', '').replace('● Số thứ tự, trang và số hiệu :', '').strip().strip('"')
            current_work['location_text'] = location
        
        elif line.startswith('● Tên tiếng Hoa:') or line.startswith('● Tên tiếng Hoa :'):
            title_zh = line.replace('● Tên tiếng Hoa:', '').replace('● Tên tiếng Hoa :', '').strip().strip('"')
            current_work['title_zh'] = title_zh
        
        i += 1
    
    # Save last work
    if current_work and 'title_vi' in current_work:
        works.append(current_work)
    
    print(f"Extracted {len(works)} works")
    return works

def clean_work(work):
    """Clean work data"""
    cleaned = {}
    
    # Title VI
    title = work.get('title_vi', '') or ''
    title = re.sub(r'\s+', ' ', title).strip()
    # Extract volume info
    volume_match = re.search(r'(\d+)\s*quyển', title)
    volume = int(volume_match.group(1)) if volume_match else 1
    title = re.sub(r'\s*\(\d+\s*quyển[,-]?\s*\d*\)\s*', '', title).strip()
    title = re.sub(r'\s*\(\d+\s*quyển\)', '', title).strip()
    title = re.sub(r',\s*\d+-\d+\)', '', title).strip()  # Remove page range
    
    cleaned['title_vi'] = title
    cleaned['volume'] = volume
    
    # Era VI
    era = work.get('era_vi', '') or ''
    era_map = {
        'Hậu Hán': 'Hậu Hán',
        'Nguyên Ngụy': 'Nguyên Ngụy', 
        'Đường': 'Đường',
        'Tây Tấn': 'Tây Tấn',
        'Đông Tấn': 'Đông Tấn',
        'Nam Tề': 'Nam Tề',
        'Lương': 'Lương',
        'Trần': 'Trần',
        'Nguyên': 'Nguyên',
        'Minh': 'Minh',
        'Thanh': 'Thanh',
    }
    cleaned['era_vi'] = era_map.get(era, era)
    
    # Author VI
    author = work.get('author_vi', '') or ''
    author = author.replace(' dịch', '').replace(' biên', '').strip()
    cleaned['author_vi'] = author
    
    # Location
    location = work.get('location_text', '') or ''
    cleaned['location_text'] = location
    
    # Title ZH
    title_zh = work.get('title_zh', '') or ''
    title_zh = re.sub(r'\s+', ' ', title_zh).strip()
    cleaned['title_zh'] = title_zh
    
    return cleaned

def save_to_db(works):
    """Save works to SQLite"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Clear existing data
    conn.execute("DELETE FROM canon_catalog")
    conn.execute("DELETE FROM ttl_canon_works")
    
    inserted = 0
    for work in works:
        cleaned = clean_work(work)
        
        # Skip empty
        if not cleaned.get('title_vi'):
            continue
        
        # Title search
        title_search = cleaned['title_vi'].lower().replace(' ', '')
        
        conn.execute("""
            INSERT INTO canon_catalog (
                title_vi, title_zh, title_search,
                author_vi, era_vi,
                location_text, volume,
                source, verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cleaned['title_vi'],
            cleaned['title_zh'],
            title_search,
            cleaned['author_vi'],
            cleaned['era_vi'],
            cleaned['location_text'],
            cleaned['volume'],
            'MucLucDaiChanh',
            0
        ))
        inserted += 1
    
    conn.commit()
    
    # Count
    count = conn.execute("SELECT COUNT(*) FROM canon_catalog").fetchone()[0]
    
    # Show sample
    print(f"\n=== Sample Works (first 5) ===")
    cursor = conn.execute("SELECT work_id, title_vi, author_vi, era_vi FROM canon_catalog LIMIT 5")
    for row in cursor:
        print(f"  {row[0]}: {row[1]} - {row[2]} ({row[3]})")
    
    # Show era distribution
    print(f"\n=== Era Distribution ===")
    cursor = conn.execute("""
        SELECT era_vi, COUNT(*) as cnt 
        FROM canon_catalog 
        GROUP BY era_vi 
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in cursor:
        print(f"  {row[0]}: {row[1]}")
    
    # Show top translators
    print(f"\n=== Top Translators ===")
    cursor = conn.execute("""
        SELECT author_vi, COUNT(*) as cnt 
        FROM canon_catalog 
        WHERE author_vi IS NOT NULL AND author_vi != ''
        GROUP BY author_vi 
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in cursor:
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()
    print(f"\n✅ Saved {inserted} works to canon_catalog")
    return inserted

if __name__ == '__main__':
    print("=" * 60)
    print("Extract Works from Mục Lục Đại Chánh Tân Tu")
    print("=" * 60)
    
    works = extract_and_parse()
    count = save_to_db(works)
    
    print(f"\n✅ Complete! Total: {count} works imported")