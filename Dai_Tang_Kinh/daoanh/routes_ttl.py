"""Route nhom ttl: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""
from flask import Flask, jsonify, request, send_from_directory, Response, make_response
import sqlite3
import re
import unicodedata
import os
import json
import hashlib
from datetime import datetime
import requests
import urllib.parse
import shutil
import time
from flask_cors import CORS
import sys as _sys
from hanviet_normalization import normalize_text as hanviet_normalize, load_glossary as hanviet_load_glossary
from style_constitution import (  # noqa: E402
    source_hash as _t165_source_hash,
    select_rules as _t165_select_rules,
    style_lock as _t165_style_lock,
    build_style_prompt as _t165_build_style_prompt,
    constitution_hash as _t165_constitution_hash,
    glossary_hash as _t165_glossary_hash,
    invalidate_cache_for_rule as _t165_invalidate_cache_for_rule,
    invalidate_cache_all_semantic as _t165_invalidate_cache_all_semantic,
    lookup_cache as _t165_lookup_cache,
    write_cache as _t165_write_cache,
    log_prompt_metrics as _t165_log_prompt_metrics,
    is_rules_outdated as _t165_is_rules_outdated,
    persist_prompt_metrics as _t165_persist_prompt_metrics,
    PROMPT_METRICS_TABLE as _T165_PROMPT_METRICS_TABLE,
    PROMPT_FORMAT_VERSION as _T165_PROMPT_FORMAT_VERSION,
    extract_match_terms as _t165_extract_match_terms,
    is_trusted_translation as _t166_is_trusted,
    is_draft_translation as _t166_is_draft,
    identity_lock_policy as _t166_identity_lock_policy,
)
from canonical_lock import (  # noqa: E402
    post_check_translation as _t166_post_check_translation,
    # T165-P8.3: entity alignment pilot gate — reuse P8.1 contract
    build_entity_key_map as _p8_build_entity_key_map,
    build_entity_prompt_instruction as _p8_build_entity_prompt_instruction,
    parse_entity_xml as _p8_parse_entity_xml,
    check_entity_assertions as _p8_check_entity_assertions,
)
from vnpa_lookup import (  # noqa: E402
    VNPA_ORDER_BY as _t200_vnpa_order_by,
    lookup_by_dila as _t200_vnpa_lookup_by_dila,
    map_dila_to_name as _t200_vnpa_map_dila_to_name,
    has_duplicate_dila as _t200_vnpa_has_duplicate_dila,
)
from t265_routes import t265_bp
from db_core import get_db_connection
import re as _re86
import threading as _t148_threading
import xml.etree.ElementTree as _t148_ET
import threading as _t412_threading
import urllib.request as _urllib_req, urllib.parse as _urllib_parse
import subprocess as _t50_sp
import signal as _t50_sig
from api_ttl_profile_v2 import create_ttl_profile_blueprint
from api_ttl_anchor import create_ttl_anchor_blueprint
from core import BASE_DIR, TTL_ARCHIVE_DIR, TTL_MASTER_DIR, TTL_OLD_DIR, app, get_db, verify_session



@app.route('/api/get_ttl/<path:filename>', methods=['GET'])
def api_get_ttl(filename):
    """
    GET /api/get_ttl/<path:filename>
    Exact filename match - accepts TS-Dai-Hue-Tong-Cao.ttl format.
    Parses TTL and returns structured fields for UI.
    """
    # Prevent path traversal
    if '..' in filename or '/' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    if not filename.endswith('.ttl'):
        filename += '.ttl'
    
    content = ""
    source = ""
    
    # Check old directory
    old_path = os.path.join(TTL_OLD_DIR, filename)
    if os.path.exists(old_path):
        with open(old_path, 'r', encoding='utf-8') as f:
            content = f.read()
        source = 'old'
    
    # Check master directory
    if not content:
        master_path = os.path.join(TTL_MASTER_DIR, filename)
        if os.path.exists(master_path):
            with open(master_path, 'r', encoding='utf-8') as f:
                content = f.read()
            source = 'master'
    
    if not content:
        return jsonify({'error': 'File not found'}), 404
    
    # Parse TTL to extract structured fields
    name_vi_match = re.search(r'rdfs:label\s+"([^"]+)"@vi', content)
    name_vi = name_vi_match.group(1) if name_vi_match else ""
    
    name_zh_match = re.search(r'rdfs:label\s+"([^"]+)"@zh', content)
    name_zh = name_zh_match.group(1) if name_zh_match else name_vi
    
    # Extract birth/death years
    birth_match = re.search(r'crm:P4_has_time-span\s+"(\d{4})"', content)
    birth_year = birth_match.group(1) if birth_match else None
    
    # Extract lineage/sect
    lineage_match = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"', content)
    sect = lineage_match.group(1) if lineage_match else ""
    
    # Extract dynasty
    dynasty_match = re.search(r'bkg:dynasty\s+"([^"]+)"', content)
    dynasty = dynasty_match.group(1) if dynasty_match else ""
    
    # Extract biographical note
    bio_match = re.search(r'bkg:biographicalNote\s+"([^"]+)"', content)
    bio = bio_match.group(1)[:500] if bio_match else ""
    
    # Extract teachers and students from TTL (bkg:hasTeacher, bkg:hasDisciple)
    teachers = re.findall(r'bkg:hasTeacher\s+<ex:monk/([^>]+)>', content)
    students = re.findall(r'bkg:hasDisciple\s+<ex:monk/([^>]+)>', content)
    
    return jsonify({
        'filename': filename,
        'ttl_content': content,
        'content': content,
        'source': source,
        'id': filename.replace('.ttl', ''),
        'name_vi': name_vi,
        'name_zh': name_zh,
        'birth_year': birth_year,
        'death_year': None,
        'sect': sect,
        'dynasty': dynasty,
        'bio': bio,
        'vps_teachers': teachers,
        'vps_students': students
    })



@app.route('/api/save-ttl', methods=['POST'])
def api_save_ttl():
    """Save TTL content to master file"""
    data = request.get_json()
    dila_id = data.get('id')
    ttl_content = data.get('ttl_content', '')
    
    if not dila_id:
        return jsonify({'error': 'Missing id'}), 400
    
    # Strip TS- prefix
    if dila_id.startswith('TS-'):
        dila_id = dila_id[3:]
    
    # Save to master directory
    os.makedirs(TTL_MASTER_DIR, exist_ok=True)
    master_ttl_path = os.path.join(TTL_MASTER_DIR, f"TS-{dila_id}.ttl")
    with open(master_ttl_path, 'w', encoding='utf-8') as f:
        f.write(ttl_content)
    
    return jsonify({'success': True, 'dila_id': dila_id, 'file': f"/ontology/ttl/monks/TS-{dila_id}.ttl"})
    
    # Save to master_entities table (create if not exists)
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS master_entities (
                id TEXT PRIMARY KEY,
                name_vi TEXT,
                lineage_master TEXT,
                lineage_source TEXT,
                bio TEXT,
                resolved_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_by TEXT DEFAULT 'admin'
            )
        """)
        
        conn.execute("""
            INSERT OR REPLACE INTO master_entities (id, name_vi, lineage_master, lineage_source, bio)
            VALUES (?, ?, ?, ?, ?)
        """, (dila_id, name_vi, lineage_master, lineage_source, bio))
        conn.commit()
    finally:
        conn.close()
    
    # Generate master TTL file
    ttl_template = f"""@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix da: <http://daoanh.vn/ontology/> .

<ex:monk/{dila_id}> a bkg:Monk ;
    rdfs:label "{name_vi}"@vi ;
    da:dilaId "{dila_id}" ;
    bkg:dharmaLineageName "{lineage_master}"@vi ;
    bkg:biographicalNote """ + bio[:500].replace('"""', '\\"\\"\\"') + """@vi .

# Resolved: {datetime.now().isoformat()}
# Lineage source: {lineage_source}
"""
    
    # Save to master directory
    master_ttl_path = os.path.join(TTL_MASTER_DIR, f"{dila_id}.ttl")
    with open(master_ttl_path, 'w', encoding='utf-8') as f:
        f.write(ttl_template)
    
    # Move old file to archive
    old_file = os.path.join(TTL_OLD_DIR, f"{dila_id}.ttl")
    if not os.path.exists(old_file):
        for f in os.listdir(TTL_OLD_DIR):
            if dila_id.lower() in f.lower():
                old_file = os.path.join(TTL_OLD_DIR, f)
                break
    
    if os.path.exists(old_file):
        archive_path = os.path.join(TTL_ARCHIVE_DIR, f"{dila_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.ttl")
        os.rename(old_file, archive_path)
    
    return jsonify({
        'success': True,
        'dila_id': dila_id,
        'master_file': f"/data/ttl/master/{dila_id}.ttl"
    })



@app.route('/api/save_ttl_v2', methods=['POST'])
def api_save_ttl_v2():
    """POST /api/save_ttl_v2 - Save rebuilt TTL to /ontology/monks/TTL/"""
    data = request.get_json()
    monk_id = (data.get('id') or '').replace('TS-', '')
    ttl_content = data.get('ttl_content', '')
    filename = data.get('filename', f"{monk_id}.ttl")
    
    if not ttl_content:
        return jsonify({'success': False, 'error': 'No content'}), 400
    
    save_dir = os.path.join(BASE_DIR, 'ontology', 'monks', 'TTL')
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ttl_content)
        return jsonify({'success': True, 'saved_to': filepath})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/admin/ttl-etl/run', methods=['POST'])
@app.route('/daoanh/api/admin/ttl-etl/run', methods=['POST'])
def admin_ttl_etl_run():
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 403
    data = request.get_json() or {}
    apply_mode = bool(data.get('apply', False))
    try:
        import subprocess
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 't05_ttl_namevi_etl.py')
        cmd = ['python', script]
        if apply_mode:
            cmd.append('--apply')
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return jsonify({'ok': True, 'output': result.stdout, 'stderr': result.stderr, 'apply': apply_mode})
    except subprocess.TimeoutExpired:
        return jsonify({'ok': False, 'error': 'Script timeout sau 120s'}), 500
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/api/admin/ttl-local-names', methods=['GET'])
@app.route('/daoanh/api/admin/ttl-local-names', methods=['GET'])
def admin_ttl_local_names():
    """GET /daoanh/api/admin/ttl-local-names
    Trả map {dila_id: name_vi} từ TTL đã lưu trong DB (vn_person_authority + ttl_master).
    Dùng cho cột TTLLocal trong namevimap.html — load 1 lần, lookup client-side.
    Ưu tiên vn_person_authority; ttl_master chỉ fill các ID còn thiếu.
    """
    try:
        conn = get_db()
        result = {}
        try:
            # [T200] vòng `result[r[0]] = r[1]` để dòng sau đè dòng trước ⇒ với 33 nhóm
            # dila_id trùng thì tên thắng KHÔNG xác định. Helper dùng setdefault + ORDER BY.
            result = _t200_vnpa_map_dila_to_name(conn)
        except Exception:
            pass
        try:
            rows = conn.execute(
                "SELECT dila_id, name_vi FROM ttl_master "
                "WHERE dila_id IS NOT NULL AND name_vi IS NOT NULL AND name_vi != ''"
            ).fetchall()
            for r in rows:
                if r[0] not in result:
                    result[r[0]] = r[1]
        except Exception:
            pass
        return jsonify({'ok': True, 'map': result, 'total': len(result)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
