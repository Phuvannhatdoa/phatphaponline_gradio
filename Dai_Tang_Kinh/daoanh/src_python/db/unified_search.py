#!/usr/bin/env python3
"""
Unified Search Function
Search across: monks (people, entity_monks), places, works (canon_catalog)
Input: Vietnamese or Chinese text
Output: All matching results (max 10 per category)
"""

import sqlite3
import re

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
MAX_RESULTS = 10

def is_chinese(text):
    """Check if text contains Chinese characters"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def normalize_search(text):
    """Normalize text for search"""
    # Remove special chars, lowercase
    return text.lower().strip()

def search_monks(query, max_results=MAX_RESULTS):
    """Search monks in DILA (people) and entity_monks"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    results = []
    query_norm = normalize_search(query)
    is_zh = is_chinese(query)
    
    # Note: name_vi column actually contains Chinese names (swapped during import)
    # So name_zh = actual VI names, name_vi = actual ZH names  
    if is_zh:
        # Search in Chinese names (priority to name_vi which has ZH)
        cursor = conn.execute("""
            SELECT id, name_vi, name_zh, 'dila' as source
            FROM people 
            WHERE name_vi LIKE ?
            ORDER BY LENGTH(name_vi)
            LIMIT ?
        """, (f'%{query}%', max_results))
        
        for row in cursor:
            results.append({
                'id': row[0],
                'name_zh': row[1],  # This is actually ZH
                'name_vi': row[2],  # This is actually VI
                'source': row[3],
                'type': 'monk'
            })
        
        # Also search entity_monks
        cursor = conn.execute("""
            SELECT name, definition, source, 'startdict' as src
            FROM entity_monks
            WHERE name LIKE ?
            LIMIT ?
        """, (f'%{query}%', max_results))
        
        for row in cursor:
            results.append({
                'name': row[0],
                'definition': row[1][:100],
                'source': row[2],
                'type': 'monk'
            })
    else:
        # Vietnamese search - but name_zh column has VI names
        cursor = conn.execute("""
            SELECT id, name_vi, name_zh, 'dila' as source
            FROM people 
            WHERE name_zh LIKE ? OR name_vi LIKE ?
            ORDER BY name_zh
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', max_results))
        
        for row in cursor:
            results.append({
                'id': row[0],
                'name_vi': row[2],  # name_zh has VI
                'name_zh': row[1],  # name_vi has ZH
                'source': row[3],
                'type': 'monk'
            })
        
        # Also search entity_monks (StarDict)
        cursor = conn.execute("""
            SELECT name, definition, source, 'startdict' as src
            FROM entity_monks
            WHERE name LIKE ?
            LIMIT ?
        """, (f'%{query}%', max_results))
        
        for row in cursor:
            results.append({
                'name': row[0],
                'definition': row[1][:100],
                'source': row[2],
                'type': 'monk'
            })
    
    conn.close()
    return results[:max_results]

def search_works(query, max_results=MAX_RESULTS):
    """Search works in canon_catalog"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    results = []
    query_norm = normalize_search(query)
    is_zh = is_chinese(query)
    
    if is_zh:
        cursor = conn.execute("""
            SELECT work_id, title_zh, title_vi, author_vi, era_vi, author_dila_id
            FROM canon_catalog
            WHERE title_zh LIKE ? OR author_zh LIKE ?
            ORDER BY title_zh
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', max_results))
    else:
        cursor = conn.execute("""
            SELECT work_id, title_vi, title_zh, author_vi, era_vi, author_dila_id
            FROM canon_catalog
            WHERE title_vi LIKE ? OR author_vi LIKE ? OR era_vi LIKE ? OR title_search LIKE ?
            ORDER BY title_vi
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query_norm}%', max_results))
    
    for row in cursor:
        results.append({
            'id': row[0],
            'title_vi': row[1],
            'title_zh': row[2],
            'author': row[3],
            'era': row[4],
            'author_dila_id': row[5],
            'type': 'work'
        })
    
    conn.close()
    return results[:max_results]

def search_places(query, max_results=MAX_RESULTS):
    """Search places/temples"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    results = []
    query_norm = normalize_search(query)
    is_zh = is_chinese(query)
    
    # places_dila now has 17 columns with full data
    if True:
        cursor = conn.execute("""
            SELECT id, name, name_zh, name_en, name_san, name_jpn, district, note, note_category, 
                   geo_lat, geo_long, 'dila_place' as source
            FROM places_dila
            WHERE name LIKE ? OR name_zh LIKE ? OR name_en LIKE ? OR district LIKE ? OR note LIKE ?
            ORDER BY name
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', max_results))
        
        for row in cursor:
            # Truncate note to 200 chars for search results
            note_short = (row[7] or '')[:200]
            
            results.append({
                'id': row[0],
                'name': row[1] or '',
                'name_zh': row[2],
                'name_en': row[3],
                'name_san': row[4],
                'name_jpn': row[5],
                'district': row[6],
                'note': note_short,
                'note_category': row[8],
                'geo_lat': row[9],
                'geo_long': row[10],
                'source': row[11],
                'type': 'place'
            })
    
    conn.close()
    return results[:max_results]

def unified_search(query):
    """
    Main unified search function
    Returns all matching results from monks, places, works
    """
    if not query or len(query.strip()) < 2:
        return {'error': 'Query too short'}
    
    return {
        'query': query,
        'monks': search_monks(query),
        'places': search_places(query),
        'works': search_works(query),
        'total': 0  # Will be calculated
    }

def test_search():
    """Test the search function"""
    test_queries = [
        'An Thế',      # VI - monk name
        'Ca Diếp',    # VI - work name
        'Hậu Hán',    # VI - era
        '安世高',      # ZH - monk name
        '迦葉',        # ZH - work name
    ]
    
    print("=" * 60)
    print("Testing Unified Search")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n--- Search: '{query}' ---")
        results = unified_search(query)
        
        print(f"  👤 Monks: {len(results.get('monks', []))}")
        for m in results.get('monks', [])[:3]:
            print(f"      - {m.get('name_vi') or m.get('name') or m.get('name_zh')} ({m.get('id', '')})")
        
        print(f"  📚 Works: {len(results.get('works', []))}")
        for w in results.get('works', [])[:3]:
            print(f"      - {w.get('title_vi')} - {w.get('author')}")
        
        print(f"  📍 Places: {len(results.get('places', []))}")
        for p in results.get('places', [])[:3]:
            print(f"      - {p.get('name_vi') or p.get('name_zh')}")

if __name__ == '__main__':
    test_search()