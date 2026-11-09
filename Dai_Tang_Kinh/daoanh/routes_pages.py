"""Route nhom pages: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""
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
from core import ADMIN_DIR, BASE_DIR, DASHBOARD_DIR, DATA_DIR, SQLITE_DB, TTL_MASTER_DIR, TTL_OLD_DIR, app



# Static file serving for admin frontend
@app.route('/daoanh/admin/')
def admin_index():
    return send_from_directory(ADMIN_DIR, 'placevn.html')



# Serve login page at /daoanh/login.html
@app.route('/daoanh/login.html')
def admin_login():
    return send_from_directory(ADMIN_DIR, 'login.html')



@app.route('/daoanh/admin/<path:path>')
def admin_static(path):
    return send_from_directory(ADMIN_DIR, path)



@app.route('/dashboard/<path:path>')
@app.route('/daoanh/dashboard/<path:path>')
def dashboard_static(path):
    return send_from_directory(DASHBOARD_DIR, path)



@app.route('/dashboard/')
@app.route('/daoanh/dashboard/')
def dashboard_index():
    return send_from_directory(DASHBOARD_DIR, 'dashboard_process.html')



@app.route('/daoanh/admin/search_all/')
@app.route('/daoanh/admin/search_all.html')
def search_all_page():
    resp = make_response(send_from_directory(ADMIN_DIR, 'search_all.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp



@app.route('/daoanh/admin/person.html')
def admin_person_page():
    resp = make_response(send_from_directory(ADMIN_DIR, 'person.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp



@app.route('/daoanh/admin/place_update.html')
def admin_place_update():
    return send_from_directory(ADMIN_DIR, 'place_update.html')




@app.route('/daoanh/api/admin/cbeta/dashboard-data')
def api_cbeta_dashboard_data():
    """GET /daoanh/api/admin/cbeta/dashboard-data — T52a stats for admin dashboard."""
    try:
        conn = get_db_connection()
        catalog_total = conn.execute('SELECT COUNT(*) FROM cbeta_catalog_vn').fetchone()[0]
        series_rows = conn.execute(
            'SELECT series, COUNT(*) as n FROM cbeta_catalog_vn GROUP BY series ORDER BY n DESC'
        ).fetchall()
        dynasty_rows = conn.execute(
            'SELECT dynasty_vi, COUNT(*) as n FROM cbeta_catalog_vn WHERE dynasty_vi IS NOT NULL GROUP BY dynasty_vi ORDER BY n DESC LIMIT 10'
        ).fetchall()
        passages_total = conn.execute('SELECT COUNT(*) FROM passage').fetchone()[0]
        passages_translated = conn.execute(
            'SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL AND vi_text != ""'
        ).fetchone()[0]
        entity_links = conn.execute('SELECT COUNT(*) FROM passage_entity').fetchone()[0]
        sat_count = conn.execute('SELECT COUNT(*) FROM sat_crossref').fetchone()[0]
        toh_count = conn.execute('SELECT COUNT(*) FROM toh_cbeta_crossref').fetchone()[0] if True else 0
        fuzzy_total = conn.execute('SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy').fetchone()[0]
        fuzzy_approved = conn.execute('SELECT COUNT(*) FROM catalog_mapping WHERE status="approved"').fetchone()[0]
        place_stats = conn.execute('SELECT COUNT(*) FROM cbeta_place_mention_stats').fetchone()[0]
        top_places = conn.execute(
            'SELECT place_id, mention_count, vi_name FROM cbeta_place_mention_stats ORDER BY mention_count DESC LIMIT 10'
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "catalog": {
                "total": catalog_total,
                "series": {r['series'] or 'unknown': r['n'] for r in series_rows}
            },
            "import": {
                "passages_total": passages_total,
                "passages_translated": passages_translated,
                "translation_pct": round(passages_translated / passages_total * 100, 1) if passages_total else 0
            },
            "entity": {
                "links_total": entity_links,
                "places_with_stats": place_stats,
                "top_places": [dict(r) for r in top_places]
            },
            "crossref": {
                "sat": sat_count,
                "sat_pct": round(sat_count / catalog_total * 100, 1),
                "toh": toh_count,
                "toh_pct": round(toh_count / catalog_total * 100, 1)
            },
            "fuzzy": {
                "total": fuzzy_total,
                "approved": fuzzy_approved,
                "approval_pct": round(fuzzy_approved / fuzzy_total * 100, 1) if fuzzy_total else 0
            },
            "dynasty_distribution": [{"dynasty": r['dynasty_vi'], "count": r['n']} for r in dynasty_rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/api/dashboard/stats', methods=['GET'])
@app.route('/daoanh/api/dashboard/stats', methods=['GET'])
@app.route('/api/admin/dashboard/stats', methods=['GET'])
@app.route('/daoanh/api/admin/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    """GET /api/dashboard/stats (và alias /api/admin/dashboard/stats) - Get all stats for dashboard"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        
        # DILA total
        dila_total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        
        # Marcus stats
        marcus_edges = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        marcus_monks = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT teacher_id as monk_id FROM marcus_networks
                UNION
                SELECT student_id as monk_id FROM marcus_networks
            )
        """).fetchone()[0]
        marcus_in_dila = conn.execute("""
            SELECT COUNT(DISTINCT m.monk_id) FROM (
                SELECT teacher_id as monk_id FROM marcus_networks
                UNION
                SELECT student_id as monk_id FROM marcus_networks
            ) m
            JOIN people p ON m.monk_id = p.id
        """).fetchone()[0]
        
        # Name Vi Map stats
        namevi_total = conn.execute("SELECT COUNT(*) FROM name_vi_map").fetchone()[0]
        namevi_with_dila = conn.execute("SELECT COUNT(*) FROM name_vi_map WHERE dila_id IS NOT NULL").fetchone()[0]
        namevi_with_marcus = conn.execute("SELECT COUNT(*) FROM name_vi_map WHERE marcus_ids IS NOT NULL").fetchone()[0]
        
        # TTL stats
        ttl_queue = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')]) if os.path.exists(TTL_OLD_DIR) else 0
        ttl_master = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')]) if os.path.exists(TTL_MASTER_DIR) else 0
        
        # Place VN review stats (vn_name_status from namevi_map_places)
        namevi_places_reviewed = conn.execute("SELECT COUNT(*) FROM namevi_map_places WHERE vn_name_status='reviewed'").fetchone()[0]
        namevi_places_auto = conn.execute("SELECT COUNT(*) FROM namevi_map_places WHERE vn_name_status='auto'").fetchone()[0]
        namevi_places_total = conn.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
        
        conn.close()
        
        coverage_marcus = round(marcus_in_dila / dila_total * 100, 1) if dila_total > 0 else 0
        coverage_namevi = round(namevi_total / dila_total * 100, 1) if dila_total > 0 else 0
        
        return jsonify({
            'dila_total': dila_total,
            'marcus_edges': marcus_edges,
            'marcus_monks': marcus_monks,
            'marcus_in_dila': marcus_in_dila,
            'marcus_coverage': coverage_marcus,
            'namevi_total': namevi_total,
            'namevi_with_dila': namevi_with_dila,
            'namevi_with_marcus': namevi_with_marcus,
            'namevi_coverage': coverage_namevi,
            'ttl_queue': ttl_queue,
            'ttl_master': ttl_master,
            'namevi_reviewed': namevi_places_reviewed,
            'namevi_auto': namevi_places_auto,
            'namevi_places_total': namevi_places_total
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/daoanh/api/progress/dashboard', methods=['GET'])
def api_progress_dashboard():
    """GET /daoanh/api/progress/dashboard - Dashboard Process Tracker (docs ↔ code).
    Đọc data/progress_data.json (sinh bởi scripts/build_progress_data.py).
    Truyền ?regenerate=1 để chạy lại script sinh dữ liệu mới."""
    progress_json = os.path.join(DATA_DIR, 'progress_data.json')
    regenerate = request.args.get('regenerate') in ('1', 'true', 'yes')

    if regenerate or not os.path.isfile(progress_json):
        script_path = os.path.join(BASE_DIR, 'scripts', 'build_progress_data.py')
        try:
            import subprocess
            run = subprocess.run([_sys.executable, script_path], cwd=BASE_DIR,
                                 capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=60)
            if run.returncode != 0:
                return jsonify({'success': False, 'error': run.stderr[-500:] or 'Script lỗi'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'Không chạy được script: {e}'}), 500

    if not os.path.isfile(progress_json):
        return jsonify({'success': False, 'error': 'progress_data.json chưa được tạo'}), 500

    try:
        with open(progress_json, encoding='utf-8') as f:
            data = json.load(f)
        data['regenerated'] = regenerate
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/compliance/dashboard', methods=['GET'])
def api_compliance_dashboard():
    """GET /daoanh/api/compliance/dashboard - Compliance Meter (SCHEMA_DESIGN M7.2).
    Đọc data/design_compliance.json (sinh bởi scripts/verify_design_compliance.py, read-only).
    Truyền ?regenerate=1 để chạy lại script sinh dữ liệu mới.
    Cổng hai tầng: exit 1 = có contract fail (coverage gap vẫn exit 0). Khi JSON mới
    đọc được thì luôn 200 kèm báo cáo; chỉ 500 khi script crash / không ghi được JSON."""
    compliance_json = os.path.join(DATA_DIR, 'design_compliance.json')
    regenerate = request.args.get('regenerate') in ('1', 'true', 'yes')

    if regenerate or not os.path.isfile(compliance_json):
        script_path = os.path.join(BASE_DIR, 'scripts', 'verify_design_compliance.py')
        started = time.time()
        try:
            import subprocess
            run = subprocess.run([_sys.executable, script_path], cwd=BASE_DIR,
                                 capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=60)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Không chạy được script: {e}'}), 500
        # rc 0 = đạt; rc 1 = có contract fail (báo cáo vẫn được ghi) → KHÔNG phải lỗi server.
        # rc khác 0/1, hoặc không có JSON mới (mtime cũ hơn lúc chạy) = script lỗi thật.
        if (run.returncode not in (0, 1) or not os.path.isfile(compliance_json)
                or os.path.getmtime(compliance_json) < started):
            return jsonify({'success': False, 'error': (run.stderr or '')[-500:] or 'Script lỗi',
                            'returncode': run.returncode}), 500

    if not os.path.isfile(compliance_json):
        return jsonify({'success': False, 'error': 'design_compliance.json chưa được tạo'}), 500

    try:
        with open(compliance_json, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # Khoá cũ giữ nguyên; chỉ THÊM các khoá gate mới.
    metrics = data.get('metrics') or []
    failed = [m for m in metrics if m.get('status') == 'fail']
    data['regenerated'] = regenerate
    data['has_failures'] = bool(failed)
    data['contract_failures'] = [m.get('id') for m in failed if m.get('gate_class') == 'contract']
    data['coverage_gaps'] = [m.get('id') for m in failed if m.get('gate_class') == 'coverage']
    data['gate_policy'] = data.get('gate_policy') or (data.get('summary') or {}).get('gate_policy')
    return jsonify(data)




@app.route('/daoanh/admin/bio-review')
def admin_bio_review_page():
    from flask import send_from_directory
    return send_from_directory(ADMIN_DIR, 'bio-review.html')
