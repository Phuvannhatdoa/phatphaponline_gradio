#!/usr/bin/env python3
"""
API: Unified Search + Canon Details
Flask routes for /api/search, /api/canon/{id}, /api/monk/{id}, /api/place/{id}
"""

import sqlite3
import json
from flask import Flask, request, jsonify

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
app = Flask(__name__)
MAX_RESULTS = 10

def is_chinese(text):
    import re
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def normalize(text):
    return text.lower().strip()

@app.route('/api/search')
def api_search():
    """Unified search across monks, works, places"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'error': 'Query too short', 'min': 2})
    
    is_zh = is_chinese(q)
    q_like = f'%{q}%'
    results = {'monks': [], 'works': [], 'places': []}
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Search monks (people + entity_monks)
    if is_zh:
        cursor = conn.execute("""
            SELECT id, name_vi, name_zh, 'dila' as src
            FROM people 
            WHERE name_vi LIKE ?
            ORDER BY LENGTH(name_vi)
            LIMIT ?
        """, (q_like, MAX_RESULTS))
    else:
        # For VI: search both columns (name_vi has CH, name_zh has VI)
        cursor = conn.execute("""
            SELECT id, name_vi, name_zh, 'dila' as src
            FROM people 
            WHERE name_vi LIKE ? OR name_zh LIKE ?
            ORDER BY name_zh
            LIMIT ?
        """, (q_like, q_like, MAX_RESULTS))
    
    for row in cursor:
        results['monks'].append({
            'id': row[0],
            'name': row[1] or row[2] or 'N/A',
            'name_zh': row[1],
            'name_vi': row[2],
            'source': row[3]
        })
    
    # Search entity_monks (StarDict)
    cursor = conn.execute("""
        SELECT name, definition, source
        FROM entity_monks
        WHERE name LIKE ?
        LIMIT ?
    """, (q_like, MAX_RESULTS))
    
    for row in cursor:
        results['monks'].append({
            'name': row[0],
            'definition': row[1][:80],
            'source': row[2]
        })
    
    # Search works (canon_catalog)
    if is_zh:
        cursor = conn.execute("""
            SELECT work_id, title_zh, title_vi, author_vi, era_vi, author_dila_id
            FROM canon_catalog
            WHERE title_zh LIKE ? OR author_vi LIKE ?
            ORDER BY title_zh
            LIMIT ?
        """, (q_like, q_like, MAX_RESULTS))
    else:
        cursor = conn.execute("""
            SELECT work_id, title_vi, title_zh, author_vi, era_vi, author_dila_id
            FROM canon_catalog
            WHERE title_vi LIKE ? OR author_vi LIKE ? OR era_vi LIKE ?
            ORDER BY title_vi
            LIMIT ?
        """, (q_like, q_like, q_like, MAX_RESULTS))
    
    for row in cursor:
        results['works'].append({
            'id': row[0],
            'title': row[1] or row[2] or 'N/A',
            'title_vi': row[2],
            'author': row[3],
            'era': row[4],
            'author_dila_id': row[5]
        })
    
    # Search places (places_dila - now has 17 columns with full data)
    cursor = conn.execute("""
        SELECT id, name, name_zh, name_en, name_san, name_jpn, district, note, note_category, geo_lat, geo_long
        FROM places_dila
        WHERE name LIKE ? OR name_zh LIKE ? OR name_en LIKE ? OR district LIKE ?
        ORDER BY name
        LIMIT ?
    """, (q_like, q_like, q_like, q_like, MAX_RESULTS))
    
    for row in cursor:
        results['places'].append({
            'id': row[0],
            'name': row[1] or '',
            'name_zh': row[2],
            'name_en': row[3],
            'name_san': row[4],
            'name_jpn': row[5],
            'district': row[6],
            'note': (row[7] or '')[:200] + '...' if row[7] and len(row[7]) > 200 else row[7],
            'note_category': row[8],
            'geo_lat': row[9],
            'geo_long': row[10],
            'source': 'dila'
        })
    
    conn.close()
    
    # Calculate total
    results['total'] = len(results['monks']) + len(results['works']) + len(results['places'])
    results['query'] = q
    
    return jsonify(results)

@app.route('/api/canon/<int:work_id>')
def api_canon_details(work_id):
    """Get canonical work details"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    cursor = conn.execute("""
        SELECT work_id, title_vi, title_zh, author_vi, author_zh, era_vi, era_zh, 
               location_text, volume, author_dila_id, verified
        FROM canon_catalog
        WHERE work_id = ?
    """, (work_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Work not found'})
    
    result = {
        'id': row[0],
        'title_vi': row[1],
        'title_zh': row[2],
        'author': row[3],
        'author_zh': row[4],
        'era': row[5],
        'era_zh': row[6],
        'location': row[7],
        'volume': row[8],
        'author_dila_id': row[9],
        'verified': row[10]
    }
    
    # Get related TTL works
    cursor = conn.execute("""
        SELECT ttl_filename, work_uri, relation_type
        FROM ttl_canon_works
        WHERE work_id = ?
    """, (work_id,))
    
    result['ttl_related'] = [{'file': r[0], 'uri': r[1], 'rel': r[2]} for r in cursor]
    
    conn.close()
    return jsonify(result)

@app.route('/api/monk/<monk_id>')
def api_monk_details(monk_id):
    """Get monk details from DILA"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Remove prefix if exists
    monk_id = monk_id.replace('A', '')
    
    cursor = conn.execute("""
        SELECT id, name_vi, name_zh, name_en, sect, dynasty, birth_year, death_year, bio
        FROM people
        WHERE id = ? OR id = ?
    """, (f'A{monk_id}', monk_id))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Monk not found'})
    
    result = {
        'id': row[0],
        'name': row[1] or row[2] or 'N/A',
        'name_zh': row[1],
        'name_vi': row[2],
        'sect': row[4],
        'dynasty': row[5],
        'birth': row[6],
        'death': row[7],
        'bio': row[8][:500] if row[8] else None
    }
    
    # Get teacher
    cursor = conn.execute("""
        SELECT teacher_id
        FROM ttl_mapping
        WHERE monk_id = ?
    """, (row[0],))
    
    teacher = cursor.fetchone()
    if teacher:
        result['teacher_id'] = teacher[0]
    
    conn.close()
    return jsonify(result)

@app.route('/api/place/<place_id>')
def api_place_details(place_id):
    """Get place/temple details"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    cursor = conn.execute("""
        SELECT id, name, name_zh, name_en, name_san, name_jpn, name_peo, name_other,
               geo_lat, geo_long, district, note, note_category, listbibl
        FROM places_dila
        WHERE id = ?
    """, (place_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Place not found'})
    
    # Truncate note to 500 chars for display
    note = row[11] or ''
    note_display = note[:500] + '...' if len(note) > 500 else note
    
    result = {
        'id': row[0],
        'name': row[1] or '',
        'name_zh': row[2],
        'name_en': row[3],
        'name_san': row[4],
        'name_jpn': row[5],
        'name_peo': row[6],
        'name_other': row[7],
        'geo_lat': row[8],
        'geo_long': row[9],
        'district': row[10],
        'note': note_display,
        'note_full': note,
        'note_category': row[12],
        'listbibl': row[13]
    }
    
    conn.close()
    return jsonify(result)

@app.route('/api/works')
def api_works():
    """List all works with pagination"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    total = conn.execute("SELECT COUNT(*) FROM canon_catalog").fetchone()[0]
    
    cursor = conn.execute("""
        SELECT work_id, title_vi, title_zh, author_vi, era_vi
        FROM canon_catalog
        ORDER BY title_vi
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    
    works = []
    for row in cursor:
        works.append({
            'id': row[0],
            'title': row[1] or row[2],
            'title_vi': row[1],
            'author': row[2],
            'era': row[3]
        })
    
    conn.close()
    
    return jsonify({
        'works': works,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/eras')
def api_eras():
    """Get all eras"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    cursor = conn.execute("""
        SELECT era_vi, era_zh, COUNT(*) as count
        FROM canon_catalog
        WHERE era_vi IS NOT NULL
        GROUP BY era_vi
        ORDER BY count DESC
    """)
    
    eras = []
    for row in cursor:
        eras.append({
            'name': row[0],
            'name_zh': row[1],
            'count': row[2]
        })
    
    conn.close()
    return jsonify(eras)

if __name__ == '__main__':
    print("Starting API server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)