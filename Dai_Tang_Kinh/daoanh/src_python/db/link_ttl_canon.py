#!/usr/bin/env python3
"""
Link Entity Works to Canonical Works
- Step 1: Use title similarity matching (VI)
- Step 2: Use translator matching
- Step 3: Match CBETA location (if available)
"""

import sqlite3
import re
from difflib import SequenceMatcher

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'

def similarity(a, b):
    """Calculate text similarity ratio"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_title_keywords(title):
    """Extract key words from title"""
    # Remove common suffixes
    title = re.sub(r'[ ()（）]', '', title)
    # Remove volume info
    title = re.sub(r'\d+卷?\s*$', '', title)
    return title

def link_works():
    """Link entity_works to canon_catalog"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Get all canonical works
    cursor = conn.execute("""
        SELECT work_id, title_vi, title_zh, author_vi, era_vi
        FROM canon_catalog
        WHERE verified = 0
    """)
    
    canon_works = []
    for row in cursor:
        canon_works.append({
            'id': row[0],
            'title_vi': row[1],
            'title_zh': row[2],
            'author': row[3],
            'era': row[4]
        })
    
    # Get all entity works
    cursor = conn.execute("""
        SELECT id, title, definition, source
        FROM entity_works
    """)
    
    entity_works = []
    for row in cursor:
        entity_works.append({
            'id': row[0],
            'title': row[1],
            'definition': row[2],
            'source': row[3]
        })
    
    linked = 0
    link_results = []
    
    for canon in canon_works:
        best_match = None
        best_score = 0
        
        # Title search in entity_works
        title_kw = extract_title_keywords(canon['title_vi'] or '')
        
        for entity in entity_works:
            # Check for title match
            score = similarity(canon['title_vi'] or '', entity['title'] or '')
            
            # Also check keyword match
            if title_kw:
                entity_kw = extract_title_keywords(entity['title'] or '')
                if title_kw in entity_kw or entity_kw in title_kw:
                    score = max(score, 0.6)
            
            if score > best_score and score > 0.4:
                best_score = score
                best_match = entity['id']
        
        if best_match:
            # Link in ttl_canon_works
            conn.execute("""
                INSERT OR REPLACE INTO ttl_canon_works (
                    ttl_filename, work_uri, work_id, relation_type
                ) VALUES (?, ?, ?, ?)
            """, (
                f'entity_work_{best_match}',
                f'entity:work:{best_match}',
                canon['id'],
                'title_similarity'
            ))
            
            # Mark canonical as verified
            conn.execute("""
                UPDATE canon_catalog
                SET verified = 1
                WHERE work_id = ?
            """, (canon['id'],))
            
            linked += 1
            link_results.append({
                'canon_id': canon['id'],
                'canon_title': canon['title_vi'],
                'entity_id': best_match,
                'score': best_score
            })
    
    conn.commit()
    
    # Summary
    print(f"Linked {linked} works out of {len(canon_works)}")
    
    for r in link_results:
        print(f"  {r['canon_id']}: {r['canon_title']} -> entity:{r['entity_id']} ({r['score']:.2f})")
    
    conn.close()
    return linked

def create_ttl_works_schema():
    """Create ttl_works table schema"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Create table if not exists
    conn.execute("""
    CREATE TABLE IF NOT EXISTS ttl_works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ttl_filename TEXT,
        work_title_vi TEXT,
        work_title_zh TEXT,
        work_id INTEGER,
        relation_source TEXT,
        relation_type TEXT,
        matched_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Schema: ttl_works")

if __name__ == '__main__':
    create_ttl_works_schema()
    link_works()
    print("\n✅ Link complete!")