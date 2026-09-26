#!/usr/bin/env python3
"""
Query APIs for Multi-Canon Database
Extended from query_apis.py
"""
import sqlite3
import json
import os

DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"

def get_person_works(person_id):
    """Get all works by a person (via DILA ID)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First get the dila_id
    cursor.execute("SELECT dila_id FROM people WHERE id = ? OR dila_id = ?", (person_id, person_id))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {'error': 'Person not found'}
    
    dila_id = row[0]
    
    # Get works from canon_mapping
    cursor.execute('''
        SELECT cm.work_id, cm.title, cm.canon_source, cm.volume, cm.page
        FROM canon_mapping cm
        WHERE cm.author_dila_id = ?
        ORDER BY cm.canon_source, cm.volume
    ''', (dila_id,))
    
    works = []
    for row in cursor.fetchall():
        works.append({
            'work_id': row[0],
            'title': row[1],
            'canon_source': row[2],
            'volume': row[3],
            'page': row[4]
        })
    
    conn.close()
    
    return {
        'person_id': person_id,
        'dila_id': dila_id,
        'total_works': len(works),
        'works': works
    }

def get_work_details(work_id):
    """Get details of a specific work"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get from canon_mapping
    cursor.execute('''
        SELECT cm.work_id, cm.title, cm.canon_source, cm.author_dila_id, cm.volume, cm.page,
               p.name_zh as author_name
        FROM canon_mapping cm
        LEFT JOIN people p ON cm.author_dila_id = p.dila_id
        WHERE cm.work_id = ?
    ''', (work_id,))
    
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {'error': 'Work not found'}
    
    # Get cross-canon mappings
    cursor.execute('''
        SELECT taisho_id, cbeta_id, linhson_id, source
        FROM text_mapping
        WHERE taisho_id = ? OR cbeta_id = ? OR linhson_id = ?
    ''', (work_id, work_id, work_id))
    
    mappings = []
    for m in cursor.fetchall():
        mappings.append({
            'taisho': m[0],
            'cbeta': m[1],
            'linhson': m[2],
            'source': m[3]
        })
    
    conn.close()
    
    return {
        'work_id': row[0],
        'title': row[1],
        'canon_source': row[2],
        'author_dila_id': row[3],
        'author_name': row[6],
        'volume': row[4],
        'page': row[5],
        'cross_mappings': mappings
    }

def search_works(query, limit=20):
    """Search works by title"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cm.work_id, cm.title, cm.canon_source, p.name_zh as author_name
        FROM canon_mapping cm
        LEFT JOIN people p ON cm.author_dila_id = p.dila_id
        WHERE cm.title LIKE ?
        LIMIT ?
    ''', (f'%{query}%', limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'work_id': row[0],
            'title': row[1],
            'canon_source': row[2],
            'author': row[3]
        })
    
    conn.close()
    return results

def get_canon_stats():
    """Get statistics for each canon"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    sources = ['CBETA', 'SAT', 'LINHSON', 'VINHLUC', 'CANLONG']
    
    for source in sources:
        cursor.execute("SELECT COUNT(*) FROM canon_mapping WHERE canon_source = ?", (source,))
        stats[source] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# Test queries
if __name__ == "__main__":
    print("📊 Canon Stats:")
    stats = get_canon_stats()
    for k, v in stats.items():
        print(f"   {k}: {v:,}")
    
    print("\n🔍 Search works '般若':")
    results = search_works('般若', 5)
    for r in results:
        print(f"   {r['work_id']}: {r['title']} ({r['canon_source']})")
    
    print("\n✅ Query APIs working!")