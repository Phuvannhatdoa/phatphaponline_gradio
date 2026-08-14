"""
API Endpoints cho Admin TTL Rebuild
- /api/monk/{id}/lexicon: Lay tu dien tu lexicon table
- /api/monk/{id}/truoctac: Lay tac pham tu canon_catalog
- /api/save_ttl_v2: Save TTL moi vao /ontology/monks/TTL/
"""

import os
import sqlite3
import re
from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)

# Paths
BASE_DIR = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh'
SQLITE_DB = os.path.join(BASE_DIR, 'data', 'lineage.db')
TTL_NEW_DIR = os.path.join(BASE_DIR, 'ontology', 'monks', 'TTL')

def get_db():
    """Connect to SQLite database"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_dila_id_from_filename(filename):
    """Chuyen doi filename thanh DILA ID
    TS-Dai-Hue-Tong-Cao -> A038686
    """
    conn = get_db()
    try:
        # Clean filename - remove TS- and .ttl
        clean_name = filename.replace('TS-', '').replace('.ttl', '')
        
        # Try exact match in ttl_mapping
        row = conn.execute(
            "SELECT dila_id FROM ttl_mapping WHERE ttl_filename = ? OR ttl_filename LIKE ?",
            (filename, f'%{clean_name}%')
        ).fetchone()
        
        if row:
            return row[0]
        
        # Try name match - convert hyphen to spaces
        name_vi = clean_name.replace('-', ' ')
        row = conn.execute(
            "SELECT dila_id FROM ttl_mapping WHERE name_vi LIKE ?",
            (f'%{name_vi}%',)
        ).fetchone()
        
        if row:
            return row[0]
        
        # Return filename as-is if not found
        return clean_name
    finally:
        conn.close()

# ==================== NEW API ENDPOINTS ====================

@app.route('/api/monk/<dila_id>/lexicon', methods=['GET'])
def api_monk_lexicon(dila_id):
    """
    GET /api/monk/{id}/lexicon
    Lay cac entry trong lexicon table lien quan toi monk
    """
    conn = get_db()
    try:
        # Get monk name first
        monk = conn.execute(
            "SELECT name_vi, name_zh FROM people WHERE id = ?",
            (dila_id,)
        ).fetchone()
        
        if not monk:
            return jsonify({'error': 'Monk not found'}), 404
        
        name_vi = monk['name_vi'] or ''
        name_zh = monk['name_zh'] or ''
        
        # Search in lexicon by name
        results = []
        
        # Search by Vietnamese name
        if name_vi:
            # Remove special chars for search
            search_name = name_vi.replace(' ', '%')
            rows = conn.execute("""
                SELECT * FROM lexicon 
                WHERE term_vi LIKE ? OR term_zh LIKE ? OR definition LIKE ?
                LIMIT 50
            """, (f'%{search_name}%', f'%{search_name}%', f'%{search_name}%')).fetchall()
            
            for row in rows:
                results.append(dict(row))
        
        return jsonify({
            'dila_id': dila_id,
            'name_vi': name_vi,
            'name_zh': name_zh,
            'entries': results,
            'count': len(results)
        })
    finally:
        conn.close()

@app.route('/api/monk/<dila_id>/truoctac', methods=['GET'])
def api_monk_truoctac(dila_id):
    """
    GET /api/monk/{id}/truoctac
    Lay cac tac pham trong canon_catalog cua tac gia
    """
    conn = get_db()
    try:
        # Get monk info
        monk = conn.execute(
            "SELECT name_vi, name_zh FROM people WHERE id = ?",
            (dila_id,)
        ).fetchone()
        
        if not monk:
            return jsonify({'error': 'Monk not found'}), 404
        
        name_vi = monk['name_vi'] or ''
        name_zh = monk['name_zh'] or ''
        
        # Search works by author in canon_catalog
        rows = conn.execute("""
            SELECT * FROM canon_catalog 
            WHERE author_vi LIKE ? OR author_zh LIKE ?
            ORDER BY title_vi
        """, (f'%{name_vi}%', f'%{name_zh}%')).fetchall()
        
        works = []
        for row in rows:
            works.append({
                'work_id': row['work_id'],
                'title_vi': row['title_vi'],
                'title_zh': row['title_zh'],
                'era_vi': row['era_vi'],
                'year_start': row['year_start'],
                'year_end': row['year_end'],
                'location_text': row['location_text'],
                'cbeta_id': row['cbeta_id'],
                'volume': row['volume']
            })
        
        return jsonify({
            'dila_id': dila_id,
            'author_vi': name_vi,
            'author_zh': name_zh,
            'works': works,
            'count': len(works)
        })
    finally:
        conn.close()

@app.route('/api/monk/<dila_id>/vps_ttl', methods=['GET'])
def api_monk_vps_ttl(dila_id):
    """
    GET /api/monk/{id}/vps_ttl
    Lay noi dung TTL tu /data/ttl/old/
    """
    ttl_old_dir = os.path.join(BASE_DIR, 'data', 'ttl', 'old')
    
    # Search for TTL file
    ttl_file = None
    for f in os.listdir(ttl_old_dir):
        if dila_id.lower() in f.lower():
            ttl_file = os.path.join(ttl_old_dir, f)
            break
    
    if not ttl_file:
        return jsonify({'error': 'TTL file not found'}), 404
    
    with open(ttl_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract key info from TTL
    ttl_info = {
        'filename': os.path.basename(ttl_file),
        'content': content,
        'labels': re.findall(r'rdfs:label\s+"([^"]+)"@([a-z]{2})', content),
        'lineage': re.search(r'bkg:dharmaLineageName\s+"([^"]+)"', content),
        'biographicalNote': re.search(r'bkg:biographicalNote\s+"([^"]+)"', content),
        'authoredWorks': re.findall(r'<ex:work/([^>]+)>', content),
        'hasTeacher': re.findall(r'<ex:monk/([^>]+)>', content)
    }
    
    return jsonify({
        'dila_id': dila_id,
        'ttl_file': os.path.basename(ttl_file),
        'content': content,
        'works': ttl_info['authoredWorks'],
        'teachers': ttl_info['hasTeacher'],
        'lineage': ttl_info['lineage'].group(1) if ttl_info['lineage'] else None,
        'bio': ttl_info['biographicalNote'].group(1)[:500] if ttl_info['biographicalNote'] else None
    })

@app.route('/api/monk/<dila_id>/dila', methods=['GET'])
def api_monk_dila(dila_id):
    """
    GET /api/monk/{id}/dila
    Lay thong tin tu people table
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM people WHERE id = ?",
            (dila_id,)
        ).fetchone()
        
        if not row:
            return jsonify({'error': 'DILA person not found'}), 404
        
        return jsonify({
            'dila_id': dila_id,
            'data': dict(row)
        })
    finally:
        conn.close()

@app.route('/api/monk/<dila_id>/marcus', methods=['GET'])
def api_monk_marcus(dila_id):
    """
    GET /api/monk/{id}/marcus
    Lay thong tin tu marcus_networks table
    """
    conn = get_db()
    try:
        # Teachers
        teachers = [row[0] for row in conn.execute("""
            SELECT teacher_label FROM marcus_networks WHERE student_id = ?
        """, (dila_id,)).fetchall()]
        
        # Students
        students = [row[0] for row in conn.execute("""
            SELECT student_label FROM marcus_networks WHERE teacher_id = ?
        """, (dila_id,)).fetchall()]
        
        # Edge count
        edge_count = conn.execute("""
            SELECT COUNT(*) FROM marcus_networks 
            WHERE teacher_id = ? OR student_id = ?
        """, (dila_id, dila_id)).fetchone()[0]
        
        # Lineage from networks
        lineage_row = conn.execute("""
            SELECT n.related_label FROM networks n
            WHERE n.monk_id = ? AND n.relation_type = 'lineage'
            LIMIT 1
        """, (dila_id,)).fetchone()
        
        lineage = lineage_row[0] if lineage_row else None
        
        return jsonify({
            'dila_id': dila_id,
            'teachers': teachers,
            'students': students,
            'edges': edge_count,
            'lineage': lineage
        })
    finally:
        conn.close()

@app.route('/api/save_ttl_v2', methods=['POST'])
def api_save_ttl_v2():
    """
    POST /api/save_ttl_v2
    Save TTL moi vao /ontology/monks/TTL/
    """
    data = request.get_json()
    dila_id = data.get('id')
    ttl_content = data.get('ttl_content', '')
    filename = data.get('filename', f'{dila_id}.ttl')
    
    if not dila_id:
        return jsonify({'error': 'Missing id'}), 400
    
    if not ttl_content:
        return jsonify({'error': 'Missing ttl_content'}), 400
    
    # Ensure directory exists
    os.makedirs(TTL_NEW_DIR, exist_ok=True)
    
    # Save file - keep original filename
    filepath = os.path.join(TTL_NEW_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ttl_content)
    
    return jsonify({
        'success': True,
        'dila_id': dila_id,
        'filename': filename,
        'saved_to': f'/ontology/monks/TTL/{filename}'
    })

# Test endpoint
@app.route('/api/test_monk/<monk_id>', methods=['GET'])
def api_test_monk(monk_id):
    """
    GET /api/test_monk/{id}
    Test all endpoints for a monk - returns combined data
    """
    import requests
    
    results = {
        'monk_id': monk_id,
        'sources': {}
    }
    
    # Get DILA
    try:
        dila_resp = requests.get(f'http://localhost:5000/api/monk/{monk_id}/dila')
        results['sources']['dila'] = dila_resp.json() if dila_resp.status_code == 200 else {'error': dila_resp.status_code}
    except Exception as e:
        results['sources']['dila'] = {'error': str(e)}
    
    # Get Marcus
    try:
        marcus_resp = requests.get(f'http://localhost:5000/api/monk/{monk_id}/marcus')
        results['sources']['marcus'] = marcus_resp.json() if marcus_resp.status_code == 200 else {'error': marcus_resp.status_code}
    except Exception as e:
        results['sources']['marcus'] = {'error': str(e)}
    
    # Get VPS TTL
    try:
        vps_resp = requests.get(f'http://localhost:5000/api/monk/{monk_id}/vps_ttl')
        results['sources']['vps_ttl'] = vps_resp.json() if vps_resp.status_code == 200 else {'error': vps_resp.status_code}
    except Exception as e:
        results['sources']['vps_ttl'] = {'error': str(e)}
    
    # Get Lexicon
    try:
        lex_resp = requests.get(f'http://localhost:5000/api/monk/{monk_id}/lexicon')
        results['sources']['lexicon'] = lex_resp.json() if lex_resp.status_code == 200 else {'error': lex_resp.status_code}
    except Exception as e:
        results['sources']['lexicon'] = {'error': str(e)}
    
    # Get Truoc Tac
    try:
        tt_resp = requests.get(f'http://localhost:5000/api/monk/{monk_id}/truoctac')
        results['sources']['truoctac'] = tt_resp.json() if tt_resp.status_code == 200 else {'error': tt_resp.status_code}
    except Exception as e:
        results['sources']['truoctac'] = {'error': str(e)}
    
    return jsonify(results)

if __name__ == '__main__':
    os.makedirs(TTL_NEW_DIR, exist_ok=True)
    print(f"TTL New Directory: {TTL_NEW_DIR}")
    app.run(host='0.0.0.0', port=5001, debug=True)