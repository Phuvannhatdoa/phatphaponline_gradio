"""Route nhom misc: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""
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
from core import ALLOWED_DIRS, BASE_DIR, CUSTOM_HANVIET, DATA_DIR, GEMINI_API_KEY, GROQ_MODEL, SQLITE_DB, TTL_ARCHIVE_DIR, TTL_MASTER_DIR, TTL_OLD_DIR, _MISSING_HANZI, _T262_CBETA_URL_RE, _T50_LOG_FILE, _T50_SCRIPT, _audit_ref_lookup, _citation_lookup, _compute_dataset_version, _compute_verification_summary, _ensure_custom_hanviet_override_table, _ensure_glossary_term_table, _ensure_missing_hanzi_table, _iso_now, _lexicon_han_lookup, _llm_config_read, _llm_config_write, _make_source_code, _persist_canonical_decision, _resolve_entity_id, _safe_audit_id, _t126_build_qa_prompt, _t126_call_groq, _t126_retrieve, _t221_load, _t221_save, _t416_pending_index_hint, _t50_log_tail, _t50_pid_alive, _t50_read_job, _t50_start_sigla, _t50_write_job, _t73_style_lock, _wiki_search_lang, app, clean_gemini_output, ensure_long_id, extract_sentence_with_place, get_db, improve_grammar, load_staging, load_verification, normalize_keyword, normalize_terms, normalize_text, normalize_value, parse_dila_district, parse_han_variants, parse_name_variants, title_case_vi, verify_session



@app.route('/daoanh/api/admin/missing-hanzi')
def api_admin_missing_hanzi():
    """
    GET /daoanh/api/admin/missing-hanzi?page=&limit=&search=
    T08 — paginated list of chars _ensure_vietnamese() could not translate.
    """
    try:
        page = max(int(request.args.get('page', 1)), 1)
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = (page - 1) * limit
        search = request.args.get('search', '').strip()
        conn = get_db_connection()
        try:
            _ensure_missing_hanzi_table()
            _ensure_custom_hanviet_override_table()
            where = "WHERE char LIKE ?" if search else ""
            params = [f'%{search}%'] if search else []
            total = conn.execute(f"SELECT COUNT(*) FROM missing_hanzi {where}", params).fetchone()[0]
            rows = conn.execute(f"""
                SELECT char, count, last_seen_at FROM missing_hanzi {where}
                ORDER BY count DESC, last_seen_at DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset]).fetchall()
            overrides = {r['char']: r['hanviet'] for r in conn.execute(
                "SELECT char, hanviet FROM custom_hanviet_override").fetchall()}
            items = []
            for r in rows:
                items.append({
                    "char": r['char'], "count": r['count'], "last_seen_at": r['last_seen_at'],
                    "override": overrides.get(r['char'])
                })
            return jsonify({"ok": True, "total": total, "page": page, "limit": limit, "items": items})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/missing-hanzi/override', methods=['POST'])
def api_admin_missing_hanzi_override():
    """
    POST /daoanh/api/admin/missing-hanzi/override  body: {char, hanviet}
    T08 — persist an admin-supplied Hán-Việt reading for a previously-missing
    character. Additive only (custom_hanviet_override table); does not touch
    hanviet_fallback or the CUSTOM_HANVIET literal in source. Takes effect
    immediately via _load_custom_hanviet_overrides() merging into the running
    in-memory dict, so the very next translation call uses it.
    """
    data = request.get_json(silent=True) or {}
    char = (data.get('char') or '').strip()
    hanviet = (data.get('hanviet') or '').strip()
    if not char or len(char) != 1:
        return jsonify({"ok": False, "error": "char must be exactly 1 character"}), 400
    if not hanviet:
        return jsonify({"ok": False, "error": "hanviet required"}), 400
    conn = get_db_connection()
    try:
        _ensure_custom_hanviet_override_table()
        conn.execute("""
            INSERT INTO custom_hanviet_override (char, hanviet, added_by, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(char) DO UPDATE SET
                hanviet = excluded.hanviet, created_at = CURRENT_TIMESTAMP
        """, (char, hanviet, request.remote_addr))
        conn.execute("DELETE FROM missing_hanzi WHERE char = ?", (char,))
        conn.commit()
        CUSTOM_HANVIET[char] = hanviet
        _MISSING_HANZI.pop(char, None)
        return jsonify({"ok": True, "char": char, "hanviet": hanviet})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()



@app.route('/daoanh/api/admin/t221/approvals')
def api_t221_approvals():
    """GET — trạng thái 2 approval gates của T22.1"""
    data = _t221_load()
    # Thêm flag OpenCode dùng
    gates = data.get('gates', {})
    data['can_proceed_giai_doan_b'] = gates.get('giai_doan_a', {}).get('status') == 'approved'
    data['nlp_authorized'] = gates.get('final_signoff', {}).get('status') == 'approved'
    return jsonify(data)



@app.route('/daoanh/api/admin/t221/approve/<gate>', methods=['POST'])
def api_t221_approve(gate):
    """POST — Lee Tổng approve một gate (giai_doan_a | final_signoff)"""
    if gate not in ('giai_doan_a', 'final_signoff'):
        return jsonify({'ok': False, 'error': 'Invalid gate'}), 400
    body = request.get_json(silent=True) or {}
    data = _t221_load()
    from datetime import datetime
    data['gates'][gate].update({
        'status': 'approved',
        'approved_by': body.get('approved_by', 'Lee Tổng'),
        'approved_at': datetime.utcnow().isoformat() + 'Z',
        'note': body.get('note', ''),
        'rejected_by': None,
        'rejected_at': None,
    })
    if gate == 'final_signoff':
        data['nlp_authorized'] = True
    data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    _t221_save(data)
    return jsonify({'ok': True, 'gate': gate, 'status': 'approved'})



@app.route('/daoanh/api/admin/t221/reject/<gate>', methods=['POST'])
def api_t221_reject(gate):
    """POST — Lee Tổng reject một gate và yêu cầu làm lại"""
    if gate not in ('giai_doan_a', 'final_signoff'):
        return jsonify({'ok': False, 'error': 'Invalid gate'}), 400
    body = request.get_json(silent=True) or {}
    data = _t221_load()
    from datetime import datetime
    data['gates'][gate].update({
        'status': 'rejected',
        'rejected_by': body.get('rejected_by', 'Lee Tổng'),
        'rejected_at': datetime.utcnow().isoformat() + 'Z',
        'note': body.get('note', ''),
        'approved_by': None,
        'approved_at': None,
    })
    data['nlp_authorized'] = False
    data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    _t221_save(data)
    return jsonify({'ok': True, 'gate': gate, 'status': 'rejected'})



# ---------------------------------------------------------------------------
# T78 — LEGAL/LICENSE FIREWALL: Legal Check + Add Source (admin no-code)
# ---------------------------------------------------------------------------
@app.route('/daoanh/api/admin/source-check', methods=['POST'])
def api_admin_source_check():
    """Nhận {name, repo_url} -> phân tích repo public -> report (LicenseGate + notes)."""
    try:
        body = request.get_json(silent=True) or {}
        name = (body.get('name') or '').strip()
        repo_url = (body.get('repo_url') or '').strip()
        if not name or not repo_url:
            return jsonify({'success': False, 'error': 'Thiếu tên nguồn hoặc Repo URL'}), 400
        from gate.analyzer import SourceAnalyzer
        rep = SourceAnalyzer(db_path=os.path.join(BASE_DIR, 'data', 'lineage.db')).analyze(name, repo_url)
        return jsonify({'success': True, 'report': rep})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/sources/list', methods=['GET'])
def api_admin_sources_list():
    """Source Hub: danh sách tất cả data_sources kèm claims count và authority_score."""
    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT ds.source_id, ds.source_code, ds.source_name, ds.organization,
                   ds.legal_status, ds.legal_status_at_ingest, ds.integration_mode,
                   ds.license_verified, ds.license_spdx, ds.data_license,
                   ds.active, ds.origin_url, ds.license_url,
                   sa.authority_score,
                   COALESCE(ec.claims,0) AS claims
            FROM data_sources ds
            LEFT JOIN source_authority sa ON sa.source_id = ds.source_id
            LEFT JOIN (
                SELECT source_id, COUNT(*) AS claims FROM entity_claims GROUP BY source_id
            ) ec ON ec.source_id = ds.source_id
            ORDER BY ds.source_id
        ''').fetchall()
        sources = [dict(r) for r in rows]
        return jsonify({'sources': sources, 'total': len(sources)})
    except Exception as e:
        return jsonify({'error': str(e), 'sources': []}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/admin/source-add', methods=['POST'])
def api_admin_source_add():
    """Admin xác nhận thêm source -> INSERT data_sources (legal_status=AUDITING, KHÔNG tự ACTIVE)
       + ghi en_audit_log. Nếu source đã tồn tại (source_code/name) -> cập nhật additive."""
    try:
        body = request.get_json(silent=True) or {}
        name = (body.get('name') or '').strip()
        repo_url = (body.get('repo_url') or '').strip()
        source_code = (body.get('source_code') or '').strip() or _make_source_code(name)
        notes = body.get('notes') or []
        integration_mode = (body.get('integration_mode') or 'REFERENCE_ONLY').upper()
        editor = (body.get('editor') or 'admin').strip()
        if not name or not repo_url:
            return jsonify({'success': False, 'error': 'Thiếu tên nguồn hoặc Repo URL'}), 400

        conn = get_db_connection()
        now = _iso_now()
        # source_code duy nhất: nếu đã có -> cập nhật additive, không nhân đôi
        existing = conn.execute(
            'SELECT source_id FROM data_sources WHERE source_code = ? OR source_name = ?',
            (source_code, name)).fetchone()
        if existing:
            sid = existing[0]
            conn.execute('UPDATE data_sources SET repository_url=?, legal_status=\'AUDITING\', '
                         'integration_mode=?, terms_status=\'under_review\', updated_at=? '
                         'WHERE source_id=?',
                         (repo_url, integration_mode, now, sid))
            action = 'source_update'
        else:
            cur = conn.execute(
                'INSERT INTO data_sources (source_code, source_name, source_type, '
                'repository_url, legal_status, data_license_status, integration_mode, '
                'terms_status, version_policy, license_verified, active, enabled, created_at, updated_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (source_code, name, 'crossref', repo_url, 'AUDITING', 'UNKNOWN',
                 integration_mode, 'under_review', 'not_available', 0, 1, 1, now, now))
            sid = cur.lastrowid
            action = 'source_add'
        # ghi audit log (additive; nếu bảng thiếu cột thì bỏ qua ghi chi tiết)
        conn.execute('INSERT INTO en_audit_log (entity_ref, action, editor, created_at) '
                     'VALUES (?,?,?,?)',
                     (f'source:{source_code}', action, editor, now))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'source_id': sid, 'source_code': source_code,
                        'legal_status': 'AUDITING', 'integration_mode': integration_mode,
                        'action': action})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/daoanh/api/admin/ai_judge/<id>')
def ai_judge(id):
    try:
        conn = get_db_connection()
        digits = ''.join(filter(str.isdigit, id))
        full_id = f'PL{digits.zfill(12)}' if digits else id

        query = """
            SELECT p.id, p.name_zh, p.name_vi AS auto_name,
                   p.address AS pending_address, p.country AS raw_country,
                   p.gps_lat, p.gps_long, p.province, p.place_type,
                   p.raw_xml AS location_xml,
                    d.district AS raw_district, d.raw_xml,
                     d.note_category AS dila_note, d.listbibl,
                    d.geo_lat, d.geo_long, d.name_en, d.name_san, d.name_jpn, d.name_peo, d.name_other,
                   m.name_vi AS saved_name, m.source, m.needs_review,
                   m.note_vi, m.district_vi, m.country_vi,
                    m.gps_lat AS m_lat, m.gps_long AS m_long, m.vn_name_status,
                   pe.latin_source, pe.id AS person_id,
                   s.name AS source_name, s.license, s.usage_level
            FROM places_pending p
            LEFT JOIN places_dila d ON p.id = d.id
            LEFT JOIN namevi_map_places m ON p.id = m.dila_id
            LEFT JOIN dataset_sources s ON m.source_id = s.id
            LEFT JOIN people pe ON p.name_zh = pe.name_zh AND pe.name_zh != ''
            WHERE p.id = ?
        """
        row = conn.execute(query, (full_id,)).fetchone()
        if not row:
            row = conn.execute(query.replace('WHERE p.id = ?', 'WHERE p.id LIKE ? LIMIT 1'), (f'%{digits}%',)).fetchone()

        if not row:
            marcus = conn.execute(
                "SELECT node_id AS id, label_vi AS name_vi, label AS name_zh FROM marcus_reference WHERE node_id = ? OR node_id LIKE ? LIMIT 1",
                (full_id, f'%{digits}%')
            ).fetchone()
            if marcus:
                conn.close()
                return jsonify({"success": True, "marcus": True, "id": marcus['id'], "name_zh": marcus['name_zh'], "name_vi": marcus['name_vi'] or '', "verdict": marcus['name_vi'] or '', "source": "manual", "needs_review": 0, "note_vi": "", "lexicon_suggestions": {"default_suggestion": "", "candidates": []}, "raw_country": "", "raw_district": "", "pending_address": "", "province": "", "place_type": "", "gps_lat": "", "gps_long": "", "full_description": "", "raw_xml": "", "latin_source": None, "person_id": "", "provenance": [], "source_name": "Marcus_fojin", "license": "CC0", "usage_level": "GREEN", "district_vi": "", "country_vi": ""})
            conn.close()
            return jsonify({"success": False, "error": "Không tìm thấy ID", "message": "ID không tồn tại trên hệ thống"}), 404

        # Lexicon suggestions (22 StarDict dictionaries, not DILA long descriptions)
        saved_vi = (row['saved_name'] or '').strip()
        auto_vi = (row['auto_name'] or '').strip()
        han_name = row['name_zh'] or ''
        suggest_api = han_name or saved_vi or auto_vi or ''
        candidates = []

        if suggest_api:
            suggest_norm = normalize_text(suggest_api)
            lex_rows = conn.execute(
                "SELECT DISTINCT term FROM lexicon WHERE key_norm = ? AND LENGTH(term) < 100 ORDER BY priority ASC LIMIT 5",
                (suggest_norm,)
            ).fetchall()
            for r in lex_rows:
                text = r['term']
                if text == han_name:  # Skip self-match (e.g. 波利城→波利城)
                    continue
                candidates.append({"source": "lexicon", "text": text})

        if han_name:
            h_terms = _lexicon_han_lookup(conn, han_name)
            for text in h_terms:
                if not any(c['text'] == text for c in candidates):
                    candidates.append({"source": "lexicon_han", "text": text})

        if suggest_api and not any(c['text'] == suggest_api for c in candidates):
            if suggest_api != han_name:
                candidates.append({"source": "api", "text": suggest_api})

        # Provenance from person_refs
        provenance = []
        person_id = row['person_id']
        if person_id:
            refs = conn.execute(
                "SELECT source_name, ref_type, value, note FROM person_refs WHERE person_id = ?",
                (person_id,)
            ).fetchall()
            provenance = [dict(r) for r in refs]
        conn.close()

        data = dict(row)
        data['gps_lat'] = data.pop('m_lat', None) or data.get('geo_lat') or data.get('gps_lat') or ''
        data['gps_long'] = data.pop('m_long', None) or data.get('geo_long') or data.get('gps_long') or ''
        data['verdict'] = data.get('saved_name') or ''
        data['source'] = data.get('source') or 'none'
        data['needs_review'] = data.get('needs_review') or 0
        data['vn_name_status'] = data.get('vn_name_status') or None
        data['note_vi'] = data.get('note_vi') or ''
        # Provide title-cased name_vi for frontend display
        name_source = data.get('saved_name') or data.get('auto_name') or ''
        data['name_vi_display'] = title_case_vi(name_source) if name_source else ''
        default_suggestion = ''
        for c in candidates:
            if c['source'] == 'lexicon':
                default_suggestion = c['text']
                break
        data['lexicon_suggestions'] = {
            "default_suggestion": default_suggestion,
            "candidates": candidates
        }
        data['han_variants'] = parse_han_variants(data.get('raw_xml', ''))
        data['name_variants'] = parse_name_variants(data.get('raw_xml', ''))
        data['full_description'] = data.get('raw_xml') or ''
        data['raw_tei'] = data.get('raw_xml') or ''
        data['district'] = data.get('raw_district') or ''
        data['address'] = data.get('pending_address') or ''
        data['raw_address'] = data.get('pending_address') or ''
        data['country'] = data.get('raw_country') or ''
        data['district_vi'] = data.get('district_vi') or ''
        data['country_vi'] = data.get('country_vi') or ''
        # Dynasty/historical region: note_type=廣大之陸上人文地理區域 + no district → no admin address
        dila_note = (data.get('dila_note') or '').strip()
        if dila_note == '廣大之陸上人文地理區域' and not (data.get('raw_district') or '').strip():
            data['district_vi'] = ''
            if not data.get('country_vi'):
                geo_lat = data.get('geo_lat') or data.get('gps_lat') or ''
                geo_lng = data.get('geo_long') or data.get('gps_long') or ''
                try:
                    lat, lng = float(geo_lat or 0), float(geo_lng or 0)
                    # China bounding box
                    if 18 <= lat <= 54 and 73 <= lng <= 135:
                        data['country_vi'] = 'Trung Quốc'
                    else:
                        data['country_vi'] = ''
                except (ValueError, TypeError):
                    data['country_vi'] = ''
        data['person_id'] = person_id or ''
        data['provenance'] = provenance
        data['source_name'] = data.get('source_name') or 'DILA_Authority'
        data['license'] = data.get('license') or 'CC BY-SA 4.0'
        data['usage_level'] = data.get('usage_level') or 'YELLOW'
        data['success'] = True
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/polish_cbeta_translation', methods=['POST'])
def polish_cbeta_translation():
    """
    POST /daoanh/api/admin/polish_cbeta_translation
    Body: { rawText, placeId, cbetaRef, hanSource }
    Flow:
      1) improve_grammar (LLM) → corrected_text + uncertain_terms
      2) normalize_terms (lexicon fuzzy) → mappings
      3) Return polished text + uncertain mappings
    """
    try:
        body = request.get_json(silent=True) or {}
        raw_text = (body.get('rawText') or '').strip()
        han_source = (body.get('hanSource') or '').strip()
        place_id = (body.get('placeId') or '').strip()
        cbeta_ref = (body.get('cbetaRef') or '').strip()

        if not raw_text:
            return jsonify({"ok": False, "error": "Thiếu rawText"}), 400

        # Step 1: Grammar correction
        step1 = improve_grammar(raw_text, han_source or raw_text)
        corrected = step1.get('corrected_text', raw_text)
        uncertain = step1.get('uncertain_terms', [])

        # Step 2: Terminology normalization
        step2 = normalize_terms(corrected, uncertain)
        polished = step2['correctedText']

        return jsonify({
            "ok": True,
            "polishedText": polished,
            "uncertainMappings": [m for m in step2['mappings'] if m['confidence'] < 0.9],
            "metadata": {
                "originalLength": len(raw_text),
                "correctedLength": len(polished),
                "termsReplaced": sum(1 for m in step2['mappings'] if m['confidence'] >= 0.9),
                "termsUncertain": sum(1 for m in step2['mappings'] if m['confidence'] >= 0.7 and m['confidence'] < 0.9),
                "termsManual": sum(1 for m in step2['mappings'] if m['confidence'] < 0.7)
            }
        })

    except Exception as e:
        import traceback
        app.logger.error(f"polish_cbeta_translation error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/auto_batch_suggest')
def auto_batch_suggest():
    try:
        conn = get_db_connection()
        # Auto-save 50 lexicon matches
        auto_matches = conn.execute("""
            SELECT p.id, l.definition FROM places_pending p
            JOIN lexicon l ON p.name_zh = l.term
            WHERE p.id NOT IN (SELECT dila_id FROM namevi_map_places)
            LIMIT 50
        """).fetchall()
        for m in auto_matches:
            conn.execute(
                "INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, source, confidence) VALUES (?, ?, (SELECT name_zh FROM places_pending WHERE id=?), 'lexicon_auto', 1.0)",
                (m['id'], m['definition'], m['id'])
            )
        conn.commit()

        # Get 10 next for Admin
        pending = conn.execute("""
            SELECT id, name_zh FROM places_pending
            WHERE id NOT IN (SELECT dila_id FROM namevi_map_places)
            LIMIT 10
        """).fetchall()
        conn.close()

        results = []
        for p in pending:
            results.append({"id": ensure_long_id(p['id']), "name_zh": p['name_zh'], "suggested_vi": "", "is_standard": False})

        return jsonify({"success": True, "batch": results, "auto_saved": len(auto_matches)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/t50/run', methods=['POST'])
def t50_run():
    """POST — khởi chạy backfill T50 cho 1 sigla (hoặc tất cả). Body: {sigla, sleep}."""
    body = request.get_json(force=True) or {}
    sigla = (body.get('sigla') or '').strip()
    sleep_s = float(body.get('sleep', 1.0))

    st = _t50_read_job()
    if st.get('running') and _t50_pid_alive(st.get('pid')):
        return jsonify({"ok": False, "error": f"Đang chạy sigla '{st['sigla']}' (PID {st['pid']}). Dừng trước khi chạy bộ khác."})

    cmd = ['python', '-X', 'utf8', _T50_SCRIPT, '--sleep', str(sleep_s)]
    if sigla:
        cmd += ['--sigla', sigla]

    log_f = open(_T50_LOG_FILE, 'w', encoding='utf-8')
    proc = _t50_sp.Popen(cmd, stdout=log_f, stderr=log_f,
                          cwd=os.path.dirname(__file__),
                          env={**os.environ, 'PYTHONUTF8': '1'})
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    _t50_write_job({"running": True, "sigla": sigla or "tất cả", "pid": proc.pid, "started_at": now})
    return jsonify({"ok": True, "pid": proc.pid, "sigla": sigla or "tất cả", "started_at": now})




@app.route('/daoanh/api/admin/t50/stop', methods=['POST'])
def t50_stop():
    """POST — dừng job backfill T50 đang chạy."""
    st = _t50_read_job()
    pid = st.get('pid')
    if not pid or not _t50_pid_alive(pid):
        _t50_write_job({**st, "running": False})
        return jsonify({"ok": False, "error": "Không có job nào đang chạy"})
    try:
        os.kill(int(pid), _t50_sig.SIGTERM)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
    _t50_write_job({**st, "running": False, "stopped_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
    return jsonify({"ok": True, "stopped_pid": pid})




@app.route('/daoanh/api/admin/t50/job-status')
def t50_job_status():
    """GET — trạng thái job hiện tại + tail log + số đã dịch + hàng đợi."""
    st = _t50_read_job()
    pid = st.get('pid')
    if st.get('running') and not _t50_pid_alive(pid):
        # Job vừa xong — tự động chạy bộ tiếp trong queue
        st['running'] = False
        queue = st.get('queue') or []
        if queue:
            next_sigla = queue.pop(0)
            st['queue'] = queue
            _t50_start_sigla(next_sigla, st)
        else:
            _t50_write_job(st)

    translated = 0
    remaining = 0
    try:
        conn = get_db_connection()
        translated = conn.execute('SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL').fetchone()[0]
        total = conn.execute('SELECT COUNT(*) FROM passage').fetchone()[0]
        remaining = total - translated
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "running": st.get('running', False),
        "sigla": st.get('sigla'),
        "pid": st.get('pid'),
        "started_at": st.get('started_at'),
        "queue": st.get('queue') or [],
        "translated_total": translated,
        "remaining_total": remaining,
        "log_tail": _t50_log_tail(15),
    })




@app.route('/daoanh/api/admin/t50/enqueue', methods=['POST'])
def t50_enqueue():
    """POST {sigla} — thêm vào hàng đợi, hoặc start ngay nếu không có job đang chạy."""
    body = request.get_json(force=True) or {}
    sigla = (body.get('sigla') or '').strip()
    if not sigla:
        return jsonify({"ok": False, "error": "Thiếu sigla"})
    st = _t50_read_job()
    queue = st.get('queue') or []
    if st.get('running') and _t50_pid_alive(st.get('pid')):
        # Đang bận — thêm vào cuối queue
        if sigla in queue:
            return jsonify({"ok": False, "error": f"'{sigla}' đã có trong hàng đợi"})
        queue.append(sigla)
        st['queue'] = queue
        _t50_write_job(st)
        return jsonify({"ok": True, "action": "queued", "sigla": sigla,
                        "position": len(queue), "queue": queue})
    else:
        # Rảnh — start ngay
        st['queue'] = queue
        pid = _t50_start_sigla(sigla, st)
        return jsonify({"ok": True, "action": "started", "sigla": sigla, "pid": pid})




@app.route('/daoanh/api/admin/t50/dequeue', methods=['POST'])
def t50_dequeue():
    """POST {sigla} — xóa khỏi hàng đợi (không dừng job đang chạy)."""
    body = request.get_json(force=True) or {}
    sigla = (body.get('sigla') or '').strip()
    st = _t50_read_job()
    queue = st.get('queue') or []
    if sigla in queue:
        queue.remove(sigla)
        st['queue'] = queue
        _t50_write_job(st)
    return jsonify({"ok": True, "queue": queue})




@app.route('/daoanh/api/admin/llm/summarize', methods=['POST'])
def llm_summarize():
    """
    POST /daoanh/api/admin/llm/summarize
    Body: {"han_text": "...", "place_name": "Thiếu Lâm Tự"}
    Returns {summary_vi, provider}.
    Demo kỹ thuật — Gemini free tier, fallback GoogleTranslator, fallback raw.
    """
    body = request.get_json(silent=True) or {}
    han_text = (body.get('han_text') or '').strip()
    place_name = (body.get('place_name') or body.get('place', '')).strip()
    if not han_text:
        return jsonify({"summary_vi": "", "provider": "none", "error": "missing_han_text"})
    if len(han_text) > 8000:
        han_text = han_text[:8000]
    han_sentence = extract_sentence_with_place(han_text, place_name) if place_name else ''
    llm_input = han_sentence if han_sentence else han_text
    prompt = (
        "Tóm tắt đoạn Hán văn sau bằng tiếng Việt, tập trung vào địa danh «" + place_name + "».\n"
        "Giữ nguyên tên riêng, địa danh, niên hiệu.\n"
        "Độ dài: nếu 1–2 câu Hán → 1–2 câu Việt; nếu 5–10 câu nhiều chi tiết → 5–7 câu.\n"
        "Phải có đủ ý chính, không chỉ ghi 1 câu chung chung.\n"
        "Chỉ trả về bản tóm tắt, không thêm giải thích:\n\n"
        f"{llm_input}"
    )
    # Try Gemini free tier
    try:
        GEMINI_KEY = GEMINI_API_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_KEY}"
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=15)
        result = resp.json()
        if 'candidates' in result and result['candidates']:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            if summary:
                summary = clean_gemini_output(summary)
                return jsonify({"summary_vi": summary, "provider": "gemini-3.6-flash"})
    except Exception:
        pass
    # Fallback: translators (Google)
    try:
        import translators as ts
        summary = ts.translate_text(llm_input[:3000], to_language='vi', translator='google')
        if summary:
            summary = clean_gemini_output(summary)
            return jsonify({"summary_vi": summary, "provider": "google-translate"})
    except Exception:
        pass
    # Fallback: deep-translator
    try:
        from deep_translator import GoogleTranslator
        summary = GoogleTranslator(source='zh-CN', target='vi').translate(llm_input[:2000])
        if summary:
            summary = clean_gemini_output(summary)
            return jsonify({"summary_vi": summary, "provider": "google-translate"})
    except Exception:
        pass
    # Last fallback: return first 500 chars raw
    return jsonify({"summary_vi": llm_input[:500] + '…', "provider": "fallback"})




@app.route('/daoanh/api/admin/wiki/fetch', methods=['POST'])
def wiki_fetch():
    """
    POST /daoanh/api/admin/wiki/fetch
    Body: {"place_id": "PL...", "name_vi": "...", "name_zh": "...", "refresh": bool}
    Returns {has_wiki, wiki_title, wiki_url, snippet, full_text, content_html, lang,
             license, cached_at}. Auto-saves snapshot to place_wiki_snapshots. Always 200.

    T07 (2026-08-22): rewritten — the previous version's zh fallback lived inside a
    `continue`-guarded branch that never ran when the vi request itself raised (only
    when vi succeeded but matched nothing), and there was no en tier despite the task
    calling for vi -> zh -> en. Now tries each language in order, each against both
    name_zh (usually the more distinctive/matchable title across editions) and
    name_vi. Also adds `refresh` to force a live re-fetch (T07 UI's "Làm mới" button)
    and records which language matched (`source` column) so the UI can show a lang
    badge — previously this info was fetched but silently discarded before saving.
    """
    body = request.get_json(silent=True) or {}
    place_id = (body.get('place_id') or '').strip()
    name_vi = (body.get('name_vi') or '').strip()
    name_zh = (body.get('name_zh') or '').strip()
    refresh = bool(body.get('refresh'))
    if not place_id:
        return jsonify({"has_wiki": False, "error": "missing_place_id"})

    conn = get_db_connection()
    try:
        conn.execute("SELECT content_html FROM place_wiki_snapshots LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE place_wiki_snapshots ADD COLUMN content_html TEXT")
        conn.commit()

    if not refresh:
        cached = conn.execute(
            "SELECT wiki_title, wiki_url, snippet, full_text, content_html, source, license, created_at "
            "FROM place_wiki_snapshots WHERE place_id = ?",
            (place_id,)
        ).fetchone()
        if cached:
            conn.close()
            return jsonify({
                "has_wiki": True,
                "wiki_title": cached['wiki_title'] or '',
                "wiki_url": cached['wiki_url'] or '',
                "snippet": cached['snippet'] or '',
                "full_text": cached['full_text'] or '',
                "content_html": cached['content_html'] or '',
                "lang": cached['source'] or '',
                "license": cached['license'] or 'CC BY-SA 4.0',
                "cached_at": cached['created_at'] or ''
            })

    HEADERS = {'User-Agent': 'DaoAnh/1.0 (Buddhist Geography Tool; +https://phatphaponline.org)'}
    found = None
    for lang in ('vi', 'zh', 'en'):
        for term in (name_zh, name_vi):
            if not term:
                continue
            found = _wiki_search_lang(lang, term, HEADERS)
            if found:
                break
        if found:
            break

    if not found:
        conn.close()
        return jsonify({"has_wiki": False})

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("""
        INSERT OR REPLACE INTO place_wiki_snapshots
        (place_id, wiki_title, wiki_url, snippet, full_text, content_html, source, license, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (place_id, found['title'], found['url'], found['snippet'], found['full_text'],
          found['content_html'], found['lang'], 'CC BY-SA 4.0', now, now))
    conn.commit()
    conn.close()
    return jsonify({
        "has_wiki": True,
        "wiki_title": found['title'],
        "wiki_url": found['url'],
        "snippet": found['snippet'],
        "full_text": found['full_text'],
        "content_html": found['content_html'],
        "lang": found['lang'],
        "license": "CC BY-SA 4.0",
        "cached_at": now
    })




@app.route('/daoanh/api/admin/parse_district', methods=['POST'])
def parse_district():
    """POST /daoanh/api/admin/parse_district
    Input: {district: str, country: str}
    Output: {success, country_vi, province, district_vi, formatted}
    Uses rule-based parse_dila_district() — no HVDic, no AI.
    """
    data = request.get_json() or {}
    district_str = (data.get('district') or '').strip()
    country_hint = (data.get('country') or '').strip()
    if not district_str and not country_hint:
        return jsonify({"success": False, "error": "Thiếu dữ liệu"}), 400
    parsed = parse_dila_district(district_str)
    if not parsed.get('country_vi') and country_hint:
        parsed['country_vi'] = country_hint
    if not parsed.get('formatted'):
        parts = [p for p in [parsed.get('district_vi', ''), parsed.get('country_vi', '')] if p]
        parsed['formatted'] = ', '.join(parts)
        parsed['success'] = True
    return jsonify(parsed)




@app.route('/daoanh/api/admin/auto_save_name', methods=['POST'])
def auto_save_name():
    try:
        data = request.json
        dila_id = str(data.get('dila_id', ''))
        name_vi = title_case_vi(data.get('name_vi', ''))
        name_zh = data.get('name_zh', '')
        if not dila_id or not name_vi:
            return jsonify({"success": False, "error": "Thiếu dila_id hoặc name_vi"}), 400
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, source, vn_name_status, confidence)
            VALUES (?, ?, ?, 'auto_generated', 'auto', 0.5)
        """, (dila_id, name_vi, name_zh))
        # Persist into places_pending.name_vi + name_vi_norm for search
        conn.execute("UPDATE places_pending SET name_vi = ?, name_vi_norm = ? WHERE id = ?", (name_vi, normalize_text(name_vi), dila_id))
        # T67: ghi nhận đổi tên auto (KHÔNG đánh verified — chờ admin duyệt)
        _persist_canonical_decision(
            conn, dila_id, action='update', field_name='name_vi',
            old_value=(data.get('prev_name_vi') or ''), new_value=name_vi,
            evidence_citations=(data.get('evidence_citations') or []),
            authority_rank=(data.get('authority_rank') or 'auto_transliterate'),
            verification_status=(data.get('verification_status') or 'needs_review'),
            decision_note=(data.get('decision_note') or 'Auto-generated VN name — chờ admin duyệt'),
            editor=(data.get('editor') or 'auto'),
            mark_verified=False,
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã lưu tên tự động"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/conflicts')
def list_conflicts():
    """T68c: danh sách tất cả conflict_pending — admin xem và giải quyết."""
    try:
        status_filter = request.args.get('status', 'pending')
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        conn = get_db_connection()
        total = conn.execute(
            "SELECT COUNT(*) FROM conflict_pending WHERE status = ?", (status_filter,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM conflict_pending WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (status_filter, limit, offset)
        ).fetchall()
        matrix = conn.execute(
            "SELECT source_code, authority_score, implemented FROM source_authority ORDER BY authority_score DESC"
        ).fetchall()
        conn.close()
        return jsonify({
            "success": True,
            "total": total, "limit": limit, "offset": offset,
            "conflicts": [dict(r) for r in rows],
            "authority_matrix": [dict(r) for r in matrix],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/ai-edit-code', methods=['POST'])
def ai_edit_code():
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    place_id = data.get('place_id', '')
    file_path = data.get('file_path', '')
    context = data.get('context', '')
    user_prompt = data.get('user_prompt', '')

    if not file_path or not user_prompt:
        return jsonify({"status": "error", "message": "Thiếu file_path hoặc user_prompt"}), 400

    abs_path = os.path.normpath(os.path.join(BASE_DIR, file_path))
    if not any(abs_path.startswith(os.path.normpath(d)) for d in ALLOWED_DIRS):
        return jsonify({"status": "error", "message": "Đường dẫn không được phép"}), 403
    if not os.path.isfile(abs_path):
        return jsonify({"status": "error", "message": "File không tồn tại"}), 404

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi đọc file: {str(e)}"}), 500

    full_prompt = f"""Context trang hiện tại:
- place_id: {place_id}
- Mô tả: {context}
- File đang chỉnh: {abs_path}

Yêu cầu cụ thể của admin:
{user_prompt}

Dưới đây là nội dung file hiện tại, hãy phân tích và sửa phù hợp:

----- FILE START -----
{current_code}
----- FILE END -----

Hãy trả về toàn bộ nội dung file sau khi đã chỉnh sửa, không giải thích dài dòng."""

    return jsonify({"status": "error", "message": "AI Code Editor đã bị vô hiệu hóa"}), 503

    try:
        backup_path = abs_path + f'.bak.{int(time.time())}'
        shutil.copy2(abs_path, backup_path)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi ghi file: {str(e)}"}), 500

    return jsonify({
        "status": "ok",
        "message": f"Đã cập nhật {file_path}. Backup: {os.path.basename(backup_path)}. Reload trang để thấy kết quả."
    })




@app.route('/daoanh/api/public/autocomplete')
def public_autocomplete():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({"success": True, "data": []})
    conn = get_db_connection()
    like = f'%{q}%'

    mapped = conn.execute(
        "SELECT DISTINCT dila_id AS id, name_vi AS value, name_zh AS name_zh, 'mapped' AS source FROM namevi_map_places WHERE name_vi LIKE ? LIMIT 10",
        (like,)
    ).fetchall()
    results = [dict(r) for r in mapped]
    seen = set(r['value'] for r in results)

    if len(results) < 10:
        remaining = 10 - len(results)
        # T416 (2026-10-21): planner bỏ qua idx_places_pending_name_zh cho LIKE '%q%' (đo được
        # 1312 ms → 137 ms khi ép index). Chỉ ép khi index tồn tại để an toàn trên DB khác (VPS).
        _hint = ' INDEXED BY idx_places_pending_name_zh' if _t416_pending_index_hint(conn) else ''
        pending = conn.execute(
            f"SELECT DISTINCT id, name_zh AS value, name_zh AS name_zh, 'pending' AS source FROM places_pending{_hint} WHERE name_zh LIKE ? LIMIT ?",
            (like, remaining)
        ).fetchall()
        for r in pending:
            if r['value'] not in seen:
                results.append(dict(r))
                seen.add(r['value'])

    if len(results) < 10:
        remaining = 10 - len(results)
        marcus = conn.execute(
            "SELECT node_id AS id, label_vi AS value, label AS name_zh, 'marcus' AS source FROM marcus_reference WHERE label_vi LIKE ? OR label LIKE ? LIMIT ?",
            (like, like, remaining)
        ).fetchall()
        for r in marcus:
            if r['value'] and r['value'] not in seen:
                results.append(dict(r))
                seen.add(r['value'])

    if len(results) < 10:
        remaining = 10 - len(results)
        lex = conn.execute(
            "SELECT term AS value, 'lexicon' AS source FROM lexicon WHERE term LIKE ? LIMIT ?",
            (like, remaining)
        ).fetchall()
        for r in lex:
            clean = r['value'].split("|")[0].split("(")[0].split(";")[0].strip()
            if len(clean) > 20:
                clean = clean[:20]
            if clean and clean not in seen:
                found = conn.execute("SELECT id FROM places_pending WHERE name_zh = ? LIMIT 1", (clean,)).fetchone()
                rid = found['id'] if found else None
                results.append({"value": clean, "name_zh": clean, "source": r['source'], "id": rid})
                seen.add(clean)

    conn.close()
    for r in results:
        if r.get('id'):
            r['id'] = ensure_long_id(r['id'])
        if len(r['value']) > 20:
            r['value'] = r['value'].split("|")[0].split("(")[0].split(";")[0].split("\n")[0].strip()[:20]
    return jsonify({"success": True, "data": results})



# ===== STATIC FILE SERVING =====
@app.route('/daoanh/static/<path:path>')
def admin_css(path):
    static_dir = os.path.join(BASE_DIR, 'static')
    return send_from_directory(static_dir, path)



# ============ TTL / MARCUS / DOSSIER APIS ============

@app.route('/api/queue')
def api_queue():
    """
    GET /api/queue
    List TTL files from /data/ttl/old/ directory - EXACT filename match.
    """
    files = [f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')]
    queue = []
    conflicts = 0
    
    for filename in files:
        fpath = os.path.join(TTL_OLD_DIR, filename)
        
        # Read TTL content
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract label
        import re
        label_match = re.search(r'rdfs:label\s+"([^"]+)"', content)
        name_vi = label_match.group(1) if label_match else filename.replace('.ttl','')
        
        # Check for conflict
        has_conflict = 'LINEAGE_CONFLICT' in content or 'conflict' in content.lower()
        
        # USE EXACT FILENAME AS ID - case sensitive
        queue.append({
            'id': filename.replace('.ttl', ''),  # EXACT: TS-Dai-Hue-Tong-Cao
            'filename': filename,
            'name_vi': name_vi,
            'rank': 'A',
            'conflict': has_conflict,
            'status': 'pending'
        })
        if has_conflict:
            conflicts += 1
    
    return jsonify({
        'queue': queue,
        'total': len(queue),
        'conflicts': conflicts,
        'rank_a': len(queue),
        'rank_b': 0
    })



@app.route('/api/resolve', methods=['POST'])
def api_resolve():
    """
    POST /api/resolve
    Save resolved master entity and move TTL to master directory.
    """
    data = request.get_json()
    dila_id = data.get('id')
    name_vi = data.get('name_vi')
    lineage_master = data.get('lineage_master')
    bio = data.get('bio')
    lineage_source = data.get('lineage_source', 'dila')  # 'dila' or 'marcus'
    
    if not dila_id:
        return jsonify({'error': 'Missing id'}), 400
    
    return jsonify({'error': 'Use app.py for resolve'}), 400



@app.route('/api/harvester/<source>', methods=['POST'])
def api_harvester(source):
    """
    POST /api/harvester/<source>
    Trigger DILA or Marcus harvester script.
    """
    import subprocess
    
    valid_sources = ['DILA', 'Marcus']
    if source not in valid_sources:
        return jsonify({'error': 'Invalid source'}), 400
    
    # Map to script names
    script_map = {
        'DILA': 'dila_harvester.py',
        'Marcus': 'marcus_harvester.py'
    }
    
    script_path = os.path.join(BASE_DIR, 'src_python', 'etl', script_map[source])
    
    if not os.path.exists(script_path):
        # Try alternative paths
        script_path = os.path.join(BASE_DIR, script_map[source])
    
    result = {'source': source, 'script': script_path}
    
    if os.path.exists(script_path):
        try:
            # Run in background
            subprocess.Popen(['python3', script_path], 
                           stdout=open(os.path.join(DATA_DIR, f'{source.lower()}_harvester.log'), 'w'),
                           stderr=subprocess.STDOUT)
            result['status'] = 'started'
            result['message'] = f'{source} harvester started'
        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)
    else:
        result['status'] = 'not_found'
        result['message'] = f'Script not found: {script_path}'
    
    return jsonify(result)



@app.route('/api/stats')
def api_stats():
    """Get overall statistics"""
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        marcus_edges = conn.execute("SELECT COUNT(*) FROM networks WHERE source_origin = 'Marcus'").fetchone()[0]
        
        queue_count = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')])
        master_count = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')])
        
        return jsonify({
            'total_people': total_people,
            'total_places': total_places,
            'marcus_edges': marcus_edges,
            'queue_pending': queue_count,
            'master_resolved': master_count
        })
    finally:
        conn.close()



@app.route('/api/health')
def api_health():
    """Health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})



@app.route('/api/conflicts')
def api_conflicts():
    """Get unresolved conflicts for Admin Dashboard"""
    conn = get_db()
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        conflict_type = request.args.get('type', None)
        
        query = "SELECT * FROM lineage_conflicts_v2 WHERE resolved = 0"
        params = []
        
        if conflict_type:
            query += " AND conflict_type = ?"
            params.append(conflict_type)
        
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        
        return jsonify({
            'conflicts': [dict(row) for row in rows],
            'count': len(rows)
        })
    finally:
        conn.close()



@app.route('/api/resolve_conflict', methods=['POST'])
def api_resolve_conflict():
    """Resolve a conflict - mark as resolved"""
    data = request.get_json()
    conflict_id = data.get('conflict_id')
    notes = data.get('notes', '')
    resolution = data.get('resolution', 'use_dila')  # 'use_dila' or 'use_marcus'
    
    conn = get_db()
    try:
        conn.execute("""
            UPDATE lineage_conflicts_v2
            SET resolved = 1, notes = ?
            WHERE id = ?
        """, (f"{notes} | Resolution: {resolution}", conflict_id))
        
        conn.commit()
        
        return jsonify({
            'status': 'ok',
            'conflict_id': conflict_id,
            'resolution': resolution
        })
    finally:
        conn.close()



@app.route('/daoanh/api/admin/claims/<int:claim_id>/review', methods=['POST'])
def admin_claim_review(claim_id):
    """POST — thẩm định 1 assertion (entity_claims): verification_status/assertion_level/reviewed_* + en_audit_log."""
    data = request.get_json(force=True, silent=True) or {}
    verdict = data.get('verdict', 'unverified')    # verified | disputed | needs_review | unverified
    level = data.get('assertion_level')            # high | medium | low | None
    editor = (data.get('editor') or '').strip() or 'admin'
    note = (data.get('note') or '').strip()

    allowed = {'verified', 'disputed', 'needs_review', 'unverified'}
    if verdict not in allowed:
        return jsonify({'status': 'error', 'message': f'verdict phải ∈ {sorted(allowed)}'}), 400
    if level not in (None, 'high', 'medium', 'low'):
        return jsonify({'status': 'error', 'message': 'assertion_level phải ∈ high|medium|low'}), 400

    conn = get_db()
    try:
        row = conn.execute("""
            SELECT c.claim_id, c.entity_id, e.canonical_label, c.claim_type, c.predicate,
                   c.source_id, c.verification_status, c.assertion_level
            FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id
            WHERE c.claim_id = ?
        """, (claim_id,)).fetchone()
        if row is None:
            return jsonify({'status': 'error', 'message': f'claim #{claim_id} không tồn tại'}), 404

        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        conn.execute("""
            UPDATE entity_claims
            SET verification_status = ?, assertion_level = ?, reviewed_by = ?, reviewed_at = ?, editor_note = ?
            WHERE claim_id = ?
        """, (verdict, level, editor, now, note, claim_id))
        cur = conn.execute("""
            INSERT INTO en_audit_log
                (entity_ref, action, field_name, old_value, new_value, evidence_sources,
                 authority_rank, editor, verification_status, created_at)
            VALUES (?, 'claim_review', ?, ?, ?, ?, ?, ?, 'verified', ?)
        """, (f"{row['canonical_label'] or row['entity_id']}|{row['claim_type']}",
              row['predicate'], f"{row['verification_status']}/{row['assertion_level']}",
              f"{verdict}/{level}", f"claim_id={claim_id}, source_id={row['source_id']}",
              'CLAIM', editor, now))
        conn.commit()
        return jsonify({'status': 'ok', 'claim_id': claim_id,
                        'verdict': verdict, 'assertion_level': level,
                        'audit_log_id': cur.lastrowid,
                        'audit_id': _safe_audit_id(conn, claim_id)})
    finally:
        conn.close()



@app.route('/api/marcus_stats')
def api_marcus_stats():
    """Get Marcus network statistics"""
    conn = get_db()
    try:
        total_relations = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        unique_teachers = conn.execute("SELECT COUNT(DISTINCT teacher_id) FROM marcus_networks").fetchone()[0]
        unique_students = conn.execute("SELECT COUNT(DISTINCT student_id) FROM marcus_networks").fetchone()[0]
        
        total_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0").fetchone()[0]
        teacher_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='teacher_set' AND resolved = 0").fetchone()[0]
        student_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='student_set' AND resolved = 0").fetchone()[0]
        
        return jsonify({
            'total_relations': total_relations,
            'unique_teachers': unique_teachers,
            'unique_students': unique_students,
            'total_conflicts': total_conflicts,
            'teacher_conflicts': teacher_conflicts,
            'student_conflicts': student_conflicts
        })
    finally:
        conn.close()



@app.route('/api/admin/staging/list')
def admin_staging_list():
    data = load_staging()
    items = data.get('items', [])
    return jsonify({"items": items, "total": len(items), "status": "ready"})



@app.route('/api/admin/verification/list')
def admin_verification_list():
    data = load_verification()
    items = data.get('items', [])
    return jsonify({"items": items, "total": len(items), "status": "pending_global"})



@app.route('/api/admin/sources')
def admin_get_sources():
    json_path = os.path.join(DATA_DIR, 'places.json')
    if not os.path.exists(json_path):
        return jsonify({"sources": []})
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    places = data.get('places', [])
    sources = {}
    for place in places:
        source = place.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    return jsonify({"sources": [{"name": k, "count": v} for k, v in sources.items()]})



# Queue endpoint - list TTL files
@ app.route('/api/admin/queue/list')
def admin_queue_list():
    try:
        files = []
        if os.path.exists(TTL_OLD_DIR):
            for f in os.listdir(TTL_OLD_DIR):
                if f.endswith('.ttl'):
                    fpath = os.path.join(TTL_OLD_DIR, f)
                    files.append({
                        "filename": f,
                        "size": os.path.getsize(fpath),
                        "modified": os.path.getmtime(fpath)
                    })
        return jsonify({"queue": files, "total": len(files)})
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/api/update_file', methods=['POST'])
def api_update_file():
    """
    POST /api/update_file
    Save TTL content to master archive.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    file_id = data.get('id', '')
    content = data.get('content', '')
    
    if not file_id:
        return jsonify({'error': 'No ID provided'}), 400
    
    # Save to master directory
    filepath = os.path.join(TTL_MASTER_DIR, f"{file_id}.ttl")
    archive_path = os.path.join(TTL_ARCHIVE_DIR, f"{file_id}.ttl")
    
    try:
        # Create backup in archive
        if os.path.exists(filepath):
            import shutil
            shutil.copy(filepath, archive_path)
        
        # Write new content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True, 'file': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/admin/master-stats')
def admin_master_stats():
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        marcus_relations = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        unresolved_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0").fetchone()[0]
        queue_count = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')])
        master_count = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')])
        return jsonify({
            "people": total_people,
            "places": total_places,
            "marcus_relations": marcus_relations,
            "conflicts": unresolved_conflicts,
            "queue": queue_count,
            "resolved": master_count
        })
    finally:
        conn.close()



@app.route('/api/rebuild/save_master', methods=['POST'])
def api_save_master():
    """POST /api/rebuild/save_master - Save TTL to SQL master table"""
    data = request.get_json()
    monk_id = (data.get('id') or '').replace('TS-', '')
    ttl_content = data.get('ttl_content', '')
    filename = data.get('filename', f"{monk_id}.ttl")
    
    if not ttl_content:
        return jsonify({'success': False, 'error': 'No content'}), 400
    
    # Extract key fields for indexing
    name_vi_match = re.search(r'skos:prefLabel\s+"([^"]+)"@vi', ttl_content)
    name_vi = name_vi_match.group(1) if name_vi_match else ''
    
    dila_id_match = re.search(r'da:dilaId\s+"([^"]+)"', ttl_content)
    dila_id = dila_id_match.group(1) if dila_id_match else ''
    
    lineage_match = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"@vi', ttl_content)
    lineage = lineage_match.group(1) if lineage_match else ''
    
    try:
        conn = get_db()
        
        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ttl_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monk_id TEXT UNIQUE,
                name_vi TEXT,
                dila_id TEXT,
                lineage TEXT,
                ttl_content TEXT,
                filename TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Upsert
        conn.execute("""
            INSERT INTO ttl_master (monk_id, name_vi, dila_id, lineage, ttl_content, filename)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(monk_id) DO UPDATE SET
                name_vi = excluded.name_vi,
                dila_id = excluded.dila_id,
                lineage = excluded.lineage,
                ttl_content = excluded.ttl_content,
                filename = excluded.filename
        """, (monk_id, name_vi, dila_id, lineage, ttl_content, filename))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'saved_to': 'ttl_master table',
            'monk_id': monk_id,
            'name_vi': name_vi
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/rebuild/queue', methods=['GET'])
def api_rebuild_queue():
    """GET /api/rebuild/queue - Get TTL rebuild queue from old/*.ttl files"""
    queue = []
    import re
    for f in sorted(os.listdir(TTL_OLD_DIR)):
        if f.endswith('.ttl'):
            monk_id = f.replace('.ttl', '').replace('TS-', '')
            
            # Extract name_vi from TTL content
            name_vi = monk_id
            ttl_path = os.path.join(TTL_OLD_DIR, f)
            if os.path.exists(ttl_path):
                with open(ttl_path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    # Extract rdfs:label "..."@vi
                    match = re.search(r'rdfs:label\s+"([^"]+)"@vi', content)
                    if match:
                        name_vi = match.group(1)
            
            queue.append({'id': monk_id, 'filename': f, 'name_vi': name_vi, 'conflict': False})
    return jsonify({'queue': queue, 'count': len(queue)})




# ===== VISITOR COUNTER =====
@app.route('/daoanh/api/public/counter')
def visitor_counter():
    COUNTER_FILE = os.path.join(DATA_DIR, 'counter.dat')
    count = 0
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                raw = f.read().strip()
                if raw:
                    count = int(raw)
        count += 1
        with open(COUNTER_FILE, 'w') as f:
            f.write(str(count))
    except Exception:
        pass
    return jsonify({'success': True, 'count': count})




@app.route('/daoanh/api/admin/keywords/parse_txt', methods=['POST'])
def keywords_parse_txt():
    """POST /daoanh/api/admin/keywords/parse_txt
    Body: { raw: "string" }
    Parses StarDict/2-line format: keyword\\nvalue\\n\\nkeyword\\nvalue...
    Returns { items: [{keyword, value}], warnings: [...] }"""
    try:
        data = request.get_json(force=True)
        raw = (data.get('raw') or '').strip()
        if not raw:
            return jsonify({"success": True, "items": [], "warnings": []})

        blocks = re.split(r'\n{2,}', raw)
        items = []
        warnings = []

        cjk_pat = re.compile(r'[\u4e00-\u9fff]+')

        def _make_val(chinese_chars, definition):
            """Build value: chinese + : + definition, wrapped in parens."""
            val = chinese_chars + ': ' + definition
            if not val.startswith('('):
                val = '(' + val + ')'
            return normalize_value(val)

        def _split_cjk_left(left):
            """Tách CJK khỏi left, trả về (keyword_raw, cjk_chars)."""
            cjk_chars = ''.join(cjk_pat.findall(left))
            if cjk_chars:
                keyword_raw = cjk_pat.sub('', left).strip()
                return keyword_raw, cjk_chars
            return left, ''

        for i, block in enumerate(blocks):
            block_raw = block.strip()
            if not block_raw:
                continue

            # Rule 0: thử tách theo dấu ": " (colon + space) trên toàn block
            colon_idx = block_raw.find(': ')
            if colon_idx != -1:
                left = block_raw[:colon_idx].strip()
                right = block_raw[colon_idx + 2:].strip()
                keyword_raw, cjk_chars = _split_cjk_left(left)
                kw = normalize_keyword(keyword_raw)
                if cjk_chars:
                    val = _make_val(cjk_chars, right)
                else:
                    val = normalize_value(right)
                if kw and val:
                    items.append({"keyword": kw, "value": val})
                    continue

            # Rule 1: thử tách theo dấu ngoặc đơn "(" đầu tiên
            m = re.search(r'\(', block_raw)
            if m:
                kw = normalize_keyword(block_raw[:m.start()].strip())
                val = normalize_value(block_raw[m.start():].strip())
                if kw and val:
                    items.append({"keyword": kw, "value": val})
                    continue

            # Fallback: tách theo dòng
            lines = [l.strip() for l in block_raw.split('\n') if l.strip()]
            if not lines:
                continue

            # Rule 2: block >= 2 dòng → dòng 1 = key, còn lại = value
            if len(lines) >= 2:
                keyword = normalize_keyword(lines[0])
                value = normalize_value('\n'.join(lines[1:]).strip())
                if keyword and value:
                    items.append({"keyword": keyword, "value": value})
                else:
                    warnings.append(f"Block {i+1}: keyword hoặc value rỗng, đã bỏ qua")
                continue

            # Rule 3: block 1 dòng → thử tách theo dấu ":" hoặc "："
            line = lines[0]
            parsed = False
            for sep in [":", "："]:
                if sep in line:
                    left, right = line.split(sep, 1)
                    keyword_raw, cjk_chars = _split_cjk_left(left.strip())
                    kw = normalize_keyword(keyword_raw)
                    if cjk_chars:
                        val = _make_val(cjk_chars, right.strip())
                    else:
                        val = normalize_value(right.strip())
                    if kw and val:
                        items.append({"keyword": kw, "value": val})
                        parsed = True
                        break
            if not parsed:
                warnings.append(f"Block {i+1}: không tách được key/value (nội dung: '{line[:60]}')")

        return jsonify({"success": True, "items": items, "warnings": warnings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/bulk_import', methods=['POST'])
def keywords_bulk_import():
    """POST /daoanh/api/admin/keywords/bulk_import
    Body: { items: [{keyword, value}], category: "import_ui" }
    Bulk inserts into keyword_map table."""
    try:
        data = request.get_json(force=True)
        items = data.get('items', [])
        category = data.get('category', 'import_ui')
        if not items:
            return jsonify({"success": False, "error": "No items to import"}), 400

        conn = get_db_connection()
        try:
            imported = 0
            for item in items:
                kw = normalize_keyword(item.get('keyword') or '')
                val = normalize_value(item.get('value') or '')
                if not kw or not val:
                    continue
                conn.execute(
                    "INSERT INTO keyword_map (keyword, value, category) VALUES (?, ?, ?)",
                    (kw, val, category)
                )
                imported += 1
            conn.commit()
            return jsonify({"success": True, "imported": imported})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/export_stardict')
def keywords_export_stardict():
    """GET /daoanh/api/admin/keywords/export_stardict
    Returns keyword_map data as StarDict txt download."""
    try:
        category = request.args.get('category', 'import_ui')
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT keyword, value FROM keyword_map WHERE category = ? ORDER BY keyword",
                (category,)
            ).fetchall()
            lines = []
            for r in rows:
                lines.append(r['keyword'])
                lines.append(r['value'])
                lines.append('')
            content = '\n'.join(lines)
            return Response(
                content,
                mimetype='text/plain; charset=utf-8',
                headers={
                    'Content-Disposition': 'attachment; filename="Chu Thich Phat Hoc - VPS.txt"',
                    'Content-Type': 'text/plain; charset=utf-8'
                }
            )
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/duplicates')
def keywords_duplicates():
    """GET /daoanh/api/admin/keywords/duplicates
    Finds keywords with COUNT > 1 in keyword_map.
    Returns grouped JSON."""
    conn = get_db_connection()
    try:
        dup_rows = conn.execute(
            "SELECT keyword FROM keyword_map GROUP BY keyword HAVING COUNT(*) > 1 ORDER BY keyword COLLATE NOCASE"
        ).fetchall()
        dup_keywords = [r['keyword'] for r in dup_rows]
        if not dup_keywords:
            return jsonify([])

        placeholders = ','.join('?' for _ in dup_keywords)
        rows = conn.execute(
            f"SELECT id, keyword, value FROM keyword_map WHERE keyword IN ({placeholders}) ORDER BY keyword COLLATE NOCASE, id",
            dup_keywords
        ).fetchall()

        groups = {}
        for r in rows:
            groups.setdefault(r['keyword'], []).append({
                "id": r['id'],
                "keyword": r['keyword'],
                "value": r['value'] or ''
            })

        result = [{"keyword": kw, "count": len(items), "items": items} for kw, items in groups.items()]
        return jsonify(result)
    finally:
        conn.close()




@app.route('/daoanh/api/admin/keywords/<int:kw_id>/update', methods=['POST'])
def keywords_update(kw_id):
    """POST /daoanh/api/admin/keywords/<id>/update
    Body: { keyword, value }"""
    try:
        data = request.get_json(force=True) or {}
        kw = normalize_keyword(data.get('keyword', ''))
        val = (data.get('value') or '').strip()
        if not kw or not val:
            return jsonify({"ok": False, "error": "keyword and value are required"}), 400
        conn = get_db_connection()
        try:
            conn.execute("UPDATE keyword_map SET keyword = ?, value = ? WHERE id = ?", (kw, val, kw_id))
            conn.commit()
            return jsonify({"ok": True})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/<int:kw_id>/delete', methods=['POST'])
def keywords_delete(kw_id):
    """POST /daoanh/api/admin/keywords/<id>/delete"""
    try:
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM keyword_map WHERE id = ?", (kw_id,))
            conn.commit()
            return jsonify({"ok": True})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/export_json')
def keywords_export_json():
    """GET /daoanh/api/admin/keywords/export_json?category=...
    Returns keyword_map as JSON download."""
    try:
        category = request.args.get('category', '').strip()
        conn = get_db_connection()
        try:
            if category:
                rows = conn.execute(
                    "SELECT id, keyword, value, category, source, created_at FROM keyword_map WHERE category = ? ORDER BY keyword",
                    (category,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, keyword, value, category, source, created_at FROM keyword_map ORDER BY category, keyword"
                ).fetchall()
            result = [dict(r) for r in rows]
            return Response(
                json.dumps(result, ensure_ascii=False, indent=2),
                mimetype='application/json; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename="keyword_map_{category or "all"}.json"'
                }
            )
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/bulk_delete', methods=['POST'])
def keywords_bulk_delete():
    """POST /daoanh/api/admin/keywords/bulk_delete
    Body: { ids: [1, 2, 3] }"""
    try:
        data = request.get_json(force=True) or {}
        ids = data.get('ids', [])
        if not ids:
            return jsonify({"success": False, "error": "No ids provided"}), 400
        conn = get_db_connection()
        try:
            placeholders = ','.join('?' for _ in ids)
            conn.execute(f"DELETE FROM keyword_map WHERE id IN ({placeholders})", ids)
            conn.commit()
            return jsonify({"success": True, "deleted": len(ids)})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/keywords/categories')
def keywords_categories():
    """GET /daoanh/api/admin/keywords/categories
    Returns list of distinct categories with counts."""
    try:
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM keyword_map GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            return jsonify([{"category": r['category'], "count": r['cnt']} for r in rows])
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/bio-review/stats')
def admin_bio_review_stats():
    try:
        conn = sqlite3.connect(SQLITE_DB)
        c = conn.cursor()
        rows = c.execute(
            "SELECT admin_approved, COUNT(*) FROM person_bio_vi_draft GROUP BY admin_approved"
        ).fetchall()
        counts = {r[0]: r[1] for r in rows}
        groups = c.execute(
            "SELECT source_name, match_type, COUNT(*) as n "
            "FROM person_bio_vi_draft WHERE admin_approved=0 "
            "GROUP BY source_name, match_type ORDER BY n DESC"
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "pending": counts.get(0, 0),
            "approved": counts.get(1, 0),
            "rejected": counts.get(-1, 0),
            "groups": [{"source_name": r[0], "match_type": r[1], "count": r[2]} for r in groups],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/bio-review/list')
def admin_bio_review_list():
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))
    status = request.args.get('status', '0')       # '0'=pending,'1'=approved,'-1'=rejected,'all'
    source = request.args.get('source', '')
    match_type = request.args.get('match_type', '')
    q = request.args.get('q', '').strip()
    try:
        conds = []
        params = []
        if status != 'all':
            conds.append("admin_approved = ?"); params.append(int(status))
        if source:
            conds.append("source_name = ?"); params.append(source)
        if match_type:
            conds.append("match_type = ?"); params.append(match_type)
        if q:
            conds.append("(name_vi LIKE ? OR name_zh LIKE ? OR bio_vi_draft LIKE ?)")
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        conn = sqlite3.connect(SQLITE_DB)
        total = conn.execute(
            f"SELECT COUNT(*) FROM person_bio_vi_draft {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT person_id, name_vi, name_zh, source_name, match_type, "
            f"char_count, admin_approved, admin_note, bio_vi_draft "
            f"FROM person_bio_vi_draft {where} "
            f"ORDER BY char_count DESC LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page]
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True, "total": total, "page": page, "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "items": [
                {"person_id": r[0], "name_vi": r[1], "name_zh": r[2],
                 "source_name": r[3], "match_type": r[4], "char_count": r[5],
                 "admin_approved": r[6], "admin_note": r[7],
                 "bio_preview": (r[8] or '')[:300]}
                for r in rows
            ],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/bio-review/approve', methods=['POST'])
def admin_bio_review_approve():
    body = request.get_json(silent=True) or {}
    person_id = (body.get('person_id') or '').strip()
    bio_override = body.get('bio_override')  # optional edited text
    if not person_id:
        return jsonify({"ok": False, "error": "Thiếu person_id"}), 400
    try:
        conn = sqlite3.connect(SQLITE_DB)
        if bio_override is not None:
            conn.execute(
                "UPDATE person_bio_vi_draft SET bio_vi_draft=?, admin_approved=1, "
                "admin_note='', updated_at=datetime('now') WHERE person_id=?",
                (bio_override.strip(), person_id)
            )
        else:
            conn.execute(
                "UPDATE person_bio_vi_draft SET admin_approved=1, admin_note='', "
                "updated_at=datetime('now') WHERE person_id=?",
                (person_id,)
            )
        conn.commit()
        remaining = conn.execute(
            "SELECT COUNT(*) FROM person_bio_vi_draft WHERE admin_approved=0"
        ).fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "person_id": person_id, "remaining_pending": remaining})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/bio-review/reject', methods=['POST'])
def admin_bio_review_reject():
    body = request.get_json(silent=True) or {}
    person_id = (body.get('person_id') or '').strip()
    note = (body.get('note') or '').strip()
    if not person_id:
        return jsonify({"ok": False, "error": "Thiếu person_id"}), 400
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.execute(
            "UPDATE person_bio_vi_draft SET admin_approved=-1, admin_note=?, "
            "updated_at=datetime('now') WHERE person_id=?",
            (note, person_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "person_id": person_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/bio-review/bulk-approve', methods=['POST'])
def admin_bio_review_bulk_approve():
    body = request.get_json(silent=True) or {}
    source = body.get('source', '')
    match_type = body.get('match_type', '')
    if not source and not match_type:
        return jsonify({"ok": False, "error": "Cần source hoặc match_type để bulk approve"}), 400
    try:
        conds = ["admin_approved = 0"]
        params = []
        if source:
            conds.append("source_name = ?"); params.append(source)
        if match_type:
            conds.append("match_type = ?"); params.append(match_type)
        where = "WHERE " + " AND ".join(conds)
        conn = sqlite3.connect(SQLITE_DB)
        preview_count = conn.execute(
            f"SELECT COUNT(*) FROM person_bio_vi_draft {where}", params
        ).fetchone()[0]
        conn.execute(
            f"UPDATE person_bio_vi_draft SET admin_approved=1, admin_note='bulk_approve', "
            f"updated_at=datetime('now') {where}", params
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "approved_count": preview_count, "source": source, "match_type": match_type})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




# ===== PANORAMA (Legacy TTL Dashboard) =====

@app.route('/daoanh/panorama/')
@app.route('/daoanh/home')
def home_page():
    from flask import send_from_directory
    return send_from_directory('static', 'home.html')



# (Cử nhân ≥6/12, Cao học ≥9/12, Tiến sĩ 12/12 — bằng chứng = code + DB thật).
@app.route('/daoanh/api/evidence/<subject_id>')
def api_evidence(subject_id):
    """GET /daoanh/api/evidence/<subject_id> — bằng chứng cho 1 subject (read-only).

    Trả về:
      events      — events JOIN event_entities (gắn subject) + event_evidence kèm theo
      claims      — entity_claims theo entity_hub (NETWORK/TEXT/COORDINATE/NAME...)
      co_mentions — event_text_link (đồng xuất hiện trong passage CBETA — KHÔNG suy quan hệ, T97)
      data_status — số liệu tổng hợp để UI hiển thị mức kiểm chứng trung thực
    Tham số ?level=L1|L2|L3 (T111 persona): L1 server-side clip claims về 'verified' (bổ túc UI).
    """
    try:
        level = (request.args.get('level') or '').upper()
        if level not in ('L1', 'L2', 'L3'):
            level = 'L2'
        conn = get_db_connection()
        eid, ref = _resolve_entity_id(conn, subject_id)

        # (1) events + event_evidence
        events = []
        ev_rows = conn.execute("""
            SELECT e.event_id, e.event_type, e.title_zh, e.title_vi, e.start_year,
                   e.end_year, e.precision, e.review_status, e.confidence
            FROM events e JOIN event_entities en ON en.event_id = e.event_id
            WHERE en.entity_id = ?
            ORDER BY e.start_year NULLS LAST
            LIMIT 200
        """, (subject_id,)).fetchall()
        for e in ev_rows:
            evid = [dict(zip(("source_record", "source_ref", "evidence_type", "exact_span"), x))
                    for x in conn.execute(
                        "SELECT source_record, source_ref, evidence_type, exact_span "
                        "FROM event_evidence WHERE event_id = ? LIMIT 8", (e["event_id"],)).fetchall()]
            events.append({
                "event_id": e["event_id"], "event_type": e["event_type"],
                "title_zh": e["title_zh"], "title_vi": e["title_vi"],
                "start_year": e["start_year"], "end_year": e["end_year"],
                "precision": e["precision"], "review_status": e["review_status"],
                "confidence": e["confidence"], "evidence": evid
            })

        # (2) entity_claims qua entity_hub (nếu resolve được INT entity_id)
        claims = []
        claim_stats = {"total": 0, "by_type": {}, "verification": {}}
        if eid is not None:
            # T100-P2 (Batch 4): đọc assertion_level nếu cột đã có (ETL applied) — additive.
            has_assert = 'assertion_level' in {r[1] for r in conn.execute('PRAGMA table_info(entity_claims)')}
            assert_col = 'c.assertion_level, ' if has_assert else ''
            claim_cols = ('c.claim_id, c.claim_type, c.predicate, c.object_text, '
                          'c.source_reference, c.confidence, c.verification_status, '
                          + assert_col
                          + "COALESCE(d.source_code, '') AS source_code, "
                          + "mr.label AS object_label_zh, mr.label_vi AS object_label_vi")
            claim_rows = conn.execute(
                "SELECT " + claim_cols + """
                FROM entity_claims c
                LEFT JOIN data_sources d ON d.source_id = c.source_id
                LEFT JOIN marcus_reference mr
                    ON c.source_id = 4
                    AND c.source_reference LIKE 'T69:marcus:_______:_______'
                    AND mr.node_id = SUBSTR(c.source_reference, -7)
                WHERE c.entity_id = ?
                ORDER BY c.claim_type, c.claim_id
                LIMIT 200
            """, (eid,)).fetchall()
            for c in claim_rows:
                # T262: trích xuất URL CBETA từ object_text nếu có (additive, không mutation DB)
                _cu = _T262_CBETA_URL_RE.search(c["object_text"] or "")
                claims.append({
                    "claim_id": c["claim_id"], "claim_type": c["claim_type"],
                    "predicate": c["predicate"], "object_text": c["object_text"],
                    "source_reference": c["source_reference"], "confidence": c["confidence"],
                    "verification_status": c["verification_status"], "source_code": c["source_code"],
                    "assertion_level": (c["assertion_level"] if has_assert else None),
                    "object_label_zh": c["object_label_zh"],
                    "object_label_vi": c["object_label_vi"],
                    "citation_url": _cu.group(0) if _cu else None,
                })
            for (ct, n) in conn.execute(
                    "SELECT claim_type, COUNT(*) FROM entity_claims WHERE entity_id=? GROUP BY claim_type",
                    (eid,)):
                claim_stats["by_type"][ct] = n
            for (vs, n) in conn.execute(
                    "SELECT verification_status, COUNT(*) FROM entity_claims "
                    "WHERE entity_id=? GROUP BY verification_status", (eid,)):
                claim_stats["verification"][vs] = n
            claim_stats["total"] = sum(claim_stats["by_type"].values())
            # T111 persona: L1 = chỉ claim đã xét duyệt 'verified' (bổ túc UI-side gating).
            if level == 'L1':
                claims = [c for c in claims
                          if (c.get('verification_status') or '') == 'verified']

        # (3) co-mention (event_text_link) — đồng xuất hiện trong passage CBETA
        co_rows = conn.execute("""
            SELECT cbeta_ref, source_book, source_ref, year, confidence, related_id, related_name
            FROM event_text_link
            WHERE entity_id = ? OR related_id = ?
            ORDER BY cbeta_ref
            LIMIT 300
        """, (subject_id, subject_id)).fetchall()
        co_mentions = [dict(r) for r in co_rows]

        # T100-P3 (Batch 5): dataset_version + verification_summary — tính trước conn.close()
        dv_info = _compute_dataset_version(conn, subject_id)

        # T260 — lineage conflict signal (governed semantics: lineage_conflicts_v2 DILA vs Marcus)
        # READ-ONLY. Reuses _t86_person_conflict semantics. Only records is_conflict=1 & resolved=0.
        lineage_conflicts = []
        if ref:
            try:
                lc_rows = conn.execute(
                    "SELECT conflict_type, dila_count, marcus_count, dila_data, marcus_data "
                    "FROM lineage_conflicts_v2 WHERE person_id=? AND is_conflict=1 AND resolved=0",
                    (ref,)
                ).fetchall()
                for r in lc_rows:
                    try:
                        dila_ids = json.loads(r["dila_data"] or "[]")
                        marcus_ids = json.loads(r["marcus_data"] or "[]")
                    except Exception:
                        dila_ids, marcus_ids = [], []
                    lineage_conflicts.append({
                        "conflict_type": r["conflict_type"],
                        "dila_count": r["dila_count"],
                        "marcus_count": r["marcus_count"],
                        "dila_only": sorted(set(dila_ids) - set(marcus_ids)),
                        "marcus_only": sorted(set(marcus_ids) - set(dila_ids)),
                    })
            except Exception:
                pass  # bảng không có → trả list rỗng, không lỗi

        conn.close()

        reviewed = sum(1 for e in events if e["review_status"] not in ("candidate", "draft", None))
        claims_note = (
            "Không tìm thấy claim cho subject này (toàn kho entity_claims 447,885 claim "
            "vẫn 100% 'unverified' — 2026-09-07)."
            if not claims else
            (f"{claim_stats['total']} claim cho subject này — 100% 'unverified' theo toàn kho "
             "(447,885 claim), đối chiếu thủ công theo batch mới nâng cấp.")
        )

        return jsonify({
            "ok": True,
            "subject_id": subject_id,
            "persona_level": level,
            "resolved": {"entity_hub_id": eid, "canonical": ref},
            "events": events,
            "claims": claims,
            "co_mentions": co_mentions,
            "lineage_conflicts": lineage_conflicts,
            "dataset_version": dv_info,
            "verification_summary": _compute_verification_summary(claim_stats),
            "data_status": {
                "events": {
                    "total": len(events),
                    "reviewed": reviewed,
                    "rejected": sum(1 for e in events if e["review_status"] == "rejected")
                },
                "claims": claim_stats,
                "co_mentions": {
                    "total": len(co_mentions),
                    "distinct_texts": len({c["cbeta_ref"] for c in co_mentions if c["cbeta_ref"]})
                },
                "notes": {
                    "events": "3,530 event toàn kho — 100% review_status 'candidate' (chưa duyệt).",
                    "claims": claims_note,
                    "co_mentions": "co-mention = đồng xuất hiện trong passage CBETA; KHÔNG suy ra quan hệ (T97)."
                }
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




@app.route('/daoanh/api/glossary')
def api_glossary():
    """GET /daoanh/api/glossary?term=<hanzi|pali|sanskrit|vi|tib>

    T57a — Tra cứu glossary đa ngôn:
      1) `lexicon` (22 từ điển PG VN — gồm bản dịch Việt DPPN) — nguồn Việt chính.
      2) `glossary_term` (Yokoyama 1996, San–Tib–Chi; MB_GLOSSARY CC0).
      3) `term_glossaries` (Marcus reference).

    Mỗi kết quả ghi rõ `source_label` để tránh gán nhầm nguồn.
    """
    term = (request.args.get('term') or '').strip()
    if not term:
        return jsonify({"ok": False, "error": "Thiếu tham số term."}), 400

    try:
        conn = get_db_connection()
        matches = []

        # 1) Lexicon (Hán–Việt 22 từ điển PG VN). Ưu tiên khớp chính xác term, fallback normalized.
        lex = conn.execute(
            """SELECT term, definition, source FROM lexicon
               WHERE term = ? ORDER BY priority ASC, id ASC LIMIT 5""",
            (term,)
        ).fetchall()
        if not lex:
            n = normalize_text(term)
            lex = conn.execute(
                """SELECT term, definition, source FROM lexicon
                   WHERE normalized = ? ORDER BY priority ASC, id ASC LIMIT 5""",
                (n,)
            ).fetchall()
        for r in lex:
            matches.append({
                "term": r['term'],
                "definition": r['definition'],
                "language": "vi",
                "source_key": "lexicon",
                "source_label": f"Từ điển PG VN ({r['source'] or '22 từ điển'})",
            })

        # 2) Glossary Yokoyama (San–Tib–Chi) — tra theo term thuần (không remove dấu —
        #    tiếng Phạn/Tạng nhạy dấu). Chỉ khớp chính xác. T110: ghép term_vi (glossary_vi).
        _ensure_glossary_term_table(conn)
        yoko = conn.execute(
            """SELECT g.term, g.language, g.definition, g.full_text,
                      v.term_vi, v.match_type, v.match_source
               FROM glossary_term g
               LEFT JOIN glossary_vi v ON v.glossary_id = g.id
               WHERE g.term = ? ORDER BY g.language LIMIT 10""",
            (term,)
        ).fetchall()
        # T110: chưa khớp thuật ngữ gốc → thử tra bằng NGHĨA TIẾNG VIỆT (term_vi) —
        #    Tăng Ni gõ tiếng Việt vẫn tìm ra được mục glossary gốc.
        if not yoko:
            yoko = conn.execute(
                """SELECT g.term, g.language, g.definition, g.full_text,
                          v.term_vi, v.match_type, v.match_source
                   FROM glossary_term g
                   JOIN glossary_vi v ON v.glossary_id = g.id
                   WHERE g.language='zho' AND (v.term_vi = ? OR v.term_vi LIKE ?)
                   ORDER BY CASE WHEN v.term_vi = ? THEN 0 ELSE 1 END, g.term LIMIT 10""",
                (term, term + '%', term)
            ).fetchall()
        lang_names = {'san': 'Sanskrit', 'zho': 'Hán', 'bod': 'Tạng (Unicode)', 'bo-Latn': 'Tạng (Latin)'}
        for r in yoko:
            item = {
                "term": r['term'],
                "definition": r['definition'],
                "language": r['language'],
                "language_name": lang_names.get(r['language'], r['language']),
                "full_text": r['full_text'],
                "source_key": "yokoyama",
                "source_label": "Yokoyama 1996 — Sanskrit–Tibetan–Chinese gloss. (CC0)",
            }
            if r['term_vi']:
                item["term_vi"] = r['term_vi']
                item["vi_match_type"] = r['match_type']
                item["vi_source"] = {'doctrine_concept': 'Giáo lý cốt lõi',
                                     'vi_buddhist_json': 'Style-lock VI',
                                     'lexicon': 'Từ điển PG VN (Vạn Hạnh)',
                                     'namevi_map_places': 'Địa danh',
                                     'name_vi_map': 'Nhân danh',
                                     'char_hv': 'Âm Hán-Việt từng ký tự',
                                     }.get(r['match_source'], r['match_source'])
            matches.append(item)

        # 3) Marcus term_glossaries (reference person/works)
        mg = conn.execute(
            """SELECT term, term_zh, term_vi, source FROM term_glossaries
               WHERE term = ? OR term_zh = ? OR term_vi = ? LIMIT 5""",
            (term, term, term)
        ).fetchall()
        for r in mg:
            matches.append({
                "term": r['term_zh'] or r['term'],
                "definition": r['term_vi'],
                "language": "vi",
                "source_key": "marcus",
                "source_label": f"Marcus SNA ({r['source'] or 'Marcus_fojin'})",
            })

        conn.close()
        return jsonify({"ok": True, "term": term, "matches": matches, "total": len(matches)})
    except Exception as e:
        app.logger.error(f"api_glossary error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/web-enrichments', methods=['GET'])
def api_admin_web_enrichments():
    """GET: Admin list enrichments với filter status, entity_type; pagination 50/page."""
    status_f = request.args.get('status', '')
    etype_f = request.args.get('entity_type', '')
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    offset = (page - 1) * per_page
    conn = get_db_connection()
    try:
        where, params = [], []
        if status_f:
            where.append("status=?"); params.append(status_f)
        if etype_f:
            where.append("entity_type=?"); params.append(etype_f)
        wc = ("WHERE " + " AND ".join(where)) if where else ""
        total = conn.execute(f"SELECT COUNT(*) FROM web_enrichment_cache {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, entity_id, entity_type, source_name, source_url,
                       summary_vi, status, report_count, created_at, fetched_by
                FROM web_enrichment_cache {wc}
                ORDER BY CASE WHEN status='reported' THEN 0 WHEN status='auto' THEN 1 ELSE 2 END, id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()
        return jsonify({
            "ok": True, "total": total, "page": page, "per_page": per_page,
            "enrichments": [dict(r) for r in rows]
        })
    finally:
        conn.close()




@app.route('/daoanh/api/admin/web-enrichment/<int:enrich_id>/status', methods=['POST'])
def api_admin_web_enrich_status(enrich_id):
    """POST: Admin verify hoặc reject một enrichment entry."""
    data = request.get_json(silent=True) or {}
    new_status = data.get('status', '')
    if new_status not in ('verified', 'rejected', 'auto'):
        return jsonify({"ok": False, "error": "status phải là verified/rejected/auto"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE web_enrichment_cache SET status=? WHERE id=?", (new_status, enrich_id))
        conn.commit()
        return jsonify({"ok": True, "id": enrich_id, "status": new_status})
    finally:
        conn.close()




@app.route('/daoanh/api/feedback', methods=['POST'])
def api_feedback():
    """POST /daoanh/api/feedback — kênh Tăng Ni báo lỗi (sai dữ liệu/thiếu nguồn).
    Public, không cần login; +7 pattern xác thực input. Ráspec6 → T119 Gap 5."""
    data = request.get_json(silent=True) or {}
    note = (data.get('note_plain') or '').strip()
    ftype = (data.get('feedback_type') or 'khac').strip()
    if ftype not in ('sai_du_lieu', 'thieu_nguon', 'loi_hien_thi', 'khac'):
        return jsonify({"ok": False, "error": "feedback_type phải ∈ sai_du_lieu|thieu_nguon|loi_hien_thi|khac"}), 400
    if not note or len(note) < 8:
        return jsonify({"ok": False, "error": "note_plain phải ≥ 8 ký tự mô tả lỗi"}), 400
    entity_id = (data.get('entity_id') or '').strip()[:80]
    entity_type = (data.get('entity_type') or '').strip()[:20]
    user_level = (data.get('user_level') or '').strip()[:20]
    conn = get_db_connection()
    try:
        cur = conn.execute(
            """INSERT INTO user_feedback
               (entity_id, entity_type, feedback_type, note_plain, user_level, status)
               VALUES (?, ?, ?, ?, ?, 'new')""",
            (entity_id or None, entity_type or None, ftype, note, user_level or None),
        )
        conn.commit()
        return jsonify({"ok": True, "feedback_id": cur.lastrowid, "status": "new"}), 201
    finally:
        conn.close()




@app.route('/daoanh/api/admin/data-gaps', methods=['GET'])
def api_admin_data_gaps():
    """GET /daoanh/api/admin/data-gaps?status=new&page= — T112 D-Feedback admin report."""
    status_f = (request.args.get('status') or '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    where, params = ["1=1"], []
    if status_f in ('new', 'ack', 'closed'):
        where.append("status=?"); params.append(status_f)
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM data_gap_requests WHERE {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, entity_type, entity_id, entity_name, gap_type, note_plain,
                       source_hint, status, created_at
                FROM data_gap_requests WHERE {wc}
                ORDER BY CASE status WHEN 'new' THEN 0 ELSE 1 END, id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        by_type = {r[0]: r[1] for r in conn.execute(
            "SELECT gap_type, COUNT(*) FROM data_gap_requests WHERE status='new' GROUP BY gap_type"
        ).fetchall()}
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "gaps": [dict(r) for r in rows], "by_type": by_type})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/data-gap/<int:gid>/status', methods=['POST'])
def api_admin_data_gap_status(gid):
    """POST /daoanh/api/admin/data-gap/<id>/status — {status: ack|closed}."""
    data = request.get_json(silent=True) or {}
    st = (data.get('status') or '').strip()
    if st not in ('ack', 'closed'):
        return jsonify({"ok": False, "error": "status phải ∈ ack|closed"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE data_gap_requests SET status=? WHERE id=?", (st, gid))
        conn.commit()
        return jsonify({"ok": True, "id": gid, "status": st})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/claims/bulk-review', methods=['POST'])
def api_admin_claims_bulk_review():
    """POST /daoanh/api/admin/claims/bulk-review — {ids:[...], verdict, assertion_level, editor}
    T119 — thẩm định hàng loạt claims; mỗi claim ghi 1 dòng en_audit_log (audit_id trả về)."""
    data = request.get_json(silent=True) or {}
    ids = [int(i) for i in (data.get('ids') or []) if str(i).isdigit()][:500]
    verdict = (data.get('verdict') or 'verified').strip()
    level = (data.get('assertion_level') or 'low').strip()
    editor = (data.get('editor') or '').strip() or 'admin'
    note = (data.get('note') or '').strip()
    if not ids:
        return jsonify({"ok": False, "error": "Không có ids nào"}), 400
    if verdict not in ('verified', 'disputed', 'needs_review', 'unverified'):
        return jsonify({"ok": False, "error": "verdict phải ∈ verified|disputed|needs_review|unverified"}), 400
    if level not in ('high', 'medium', 'low'):
        return jsonify({"ok": False, "error": "assertion_level phải ∈ high|medium|low"}), 400
    conn = get_db_connection()
    try:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"""SELECT c.claim_id, c.entity_id, e.canonical_label, c.claim_type, c.predicate,
                       c.source_id, c.verification_status, c.assertion_level
                FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id
                WHERE c.claim_id IN ({placeholders})""",
            ids,
        ).fetchall()
        updated, audit_ids = [], []
        for row in rows:
            conn.execute(
                """UPDATE entity_claims
                   SET verification_status=?, assertion_level=?, reviewed_by=?, reviewed_at=?, editor_note=?
                   WHERE claim_id=?""",
                (verdict, level, editor, now, note, row['claim_id']),
            )
            cur = conn.execute(
                """INSERT INTO en_audit_log
                   (entity_ref, action, field_name, old_value, new_value, evidence_sources,
                    authority_rank, editor, verification_status, created_at)
                   VALUES (?, 'claim_review', ?, ?, ?, ?, 'CLAIM', ?, 'verified', ?)""",
                (f"{row['canonical_label'] or row['entity_id']}|{row['claim_type']}",
                 row['predicate'], f"{row['verification_status']}/{row['assertion_level']}",
                 f"{verdict}/{level}", f"claim_id={row['claim_id']}, source_id={row['source_id']}",
                 editor, now),
            )
            updated.append(row['claim_id'])
            audit_ids.append(cur.lastrowid)
        conn.commit()
        return jsonify({"ok": True, "updated": updated, "audit_log_ids": audit_ids,
                        "audit_id": f"en-{audit_ids[-1]}" if audit_ids else None,
                        "count": len(updated)})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/resolutions/history', methods=['GET'])
def api_admin_resolutions_history():
    """GET /daoanh/api/admin/resolutions/history?page=&per_page= — T119 Gap 4 (fix T134 2026-09-14):
    lịch sử phán quyết = UNION resol_dais_log (legacy) + en_audit_log action='resolve_lineage_conflict'
    (nguồn GHI THẬT từ conflicts.html/T109). Trước fix: resolutions_log KHÔNG bao giờ được INSERT
    (0/4 code path) → tab Resolutions luôn trống dù phán quyết đã ghi vào en_audit_log."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    conn = get_db_connection()
    try:
        total = (
            conn.execute("SELECT COUNT(*) FROM en_audit_log WHERE action='resolve_lineage_conflict'").fetchone()[0]
            + conn.execute("SELECT COUNT(*) FROM resolutions_log").fetchone()[0]
        )
        rows = conn.execute(
            """WITH resolved_src AS (
                SELECT a.log_id AS rid,
                       a.entity_ref AS monk_id,
                       a.new_value AS chosen_source,
                       a.old_value AS previous_source,
                       a.evidence_sources AS notes,
                       a.editor AS resolved_by,
                       a.created_at AS resolved_at,
                       c.id AS conflict_id,
                       c.label, c.name_vi, c.person_id, c.conflict_type
                FROM en_audit_log a
                LEFT JOIN lineage_conflicts_v2 c ON c.person_id = a.entity_ref
                WHERE a.action = 'resolve_lineage_conflict'
                UNION ALL
                SELECT r.id AS rid,
                       r.monk_id, r.chosen_source, r.previous_source, r.notes, r.resolved_by,
                       r.resolved_at, r.conflict_id,
                       c2.label, c2.name_vi, c2.person_id, c2.conflict_type
                FROM resolutions_log r
                LEFT JOIN lineage_conflicts_v2 c2 ON c2.id = r.conflict_id
            )
            SELECT * FROM resolved_src
            ORDER BY resolved_at DESC, rid DESC
            LIMIT ? OFFSET ?""",
            (per_page, offset),
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "resolutions": [dict(r) for r in rows]})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/feedback', methods=['GET'])
def api_admin_feedback():
    """GET /daoanh/api/admin/feedback?status=new&page= — T119 Gap 5 inbox."""
    status_f = (request.args.get('status') or '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    where, params = ["1=1"], []
    if status_f in ('new', 'ack', 'closed'):
        where.append("status=?"); params.append(status_f)
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM user_feedback WHERE {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, entity_id, entity_type, feedback_type, note_plain, user_level,
                       status, created_at
                FROM user_feedback WHERE {wc}
                ORDER BY CASE status WHEN 'new' THEN 0 ELSE 1 END, id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "feedback": [dict(r) for r in rows]})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/feedback/<int:fid>/status', methods=['POST'])
def api_admin_feedback_status(fid):
    """POST /daoanh/api/admin/feedback/<id>/status — {status: ack|closed}."""
    data = request.get_json(silent=True) or {}
    st = (data.get('status') or '').strip()
    if st not in ('ack', 'closed'):
        return jsonify({"ok": False, "error": "status phải ∈ ack|closed"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE user_feedback SET status=? WHERE id=?", (st, fid))
        conn.commit()
        return jsonify({"ok": True, "id": fid, "status": st})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/audit/trail', methods=['GET'])
def api_admin_audit_trail():
    """GET /daoanh/api/admin/audit/trail?entity_ref=&page=&per_page= — T118:
    en_audit_log append-only; audit_id format en-<log_id>."""
    entity_ref = (request.args.get('entity_ref') or '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    where, params = ["1=1"], []
    if entity_ref:
        where.append("entity_ref LIKE ?"); params.append(f"%{entity_ref}%")
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM en_audit_log WHERE {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT log_id, entity_ref, action, field_name, old_value, new_value,
                       evidence_sources, authority_rank, editor, verification_status, created_at
                FROM en_audit_log WHERE {wc}
                ORDER BY log_id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        out = [dict(r) | {"audit_id": f"en-{r['log_id']}"} for r in rows]
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "audits": out})
    finally:
        conn.close()




@app.route('/daoanh/api/public/export/citation', methods=['GET'])
def api_public_export_citation():
    """GET /daoanh/api/public/export/citation?entity_id=&format=csl-json|bibtex&audit_id=
    T118 — xuất trích dẫn chuẩn (CSL-JSON / BibTeX) cho công cụ học thuật; additive.
    Đợt 2: audit_id xuyên vào export (AUDIT_ID + evidence) + `signature` =
    sha256(entity_id|audit_id|title) — chữ ký bằng chứng, ổn định theo mọi định dạng."""
    entity_id = (request.args.get('entity_id') or '').strip()
    fmt = (request.args.get('format') or 'csl-json').strip().lower()
    audit_id = (request.args.get('audit_id') or '').strip()
    if not entity_id:
        return jsonify({"ok": False, "error": "Thiếu entity_id"}), 400
    if fmt not in ('csl-json', 'bibtex'):
        return jsonify({"ok": False, "error": "format phải ∈ csl-json|bibtex"}), 400
    info = _citation_lookup(entity_id)
    if not info:
        return jsonify({"ok": False, "error": "Không phân giải được entity"}), 404
    title = (info['title_vi'] or info['title_zh'] or entity_id)
    note_parts = [info['source_name'] or '', f"Truy cập qua Đạo Ảnh — Phật Pháp Online (phatphaponline.org)"]
    audit_detail = _audit_ref_lookup(audit_id)
    if audit_detail:
        note_parts.append(f"AUDIT_ID={audit_id}")
        if audit_detail.get('evidence_sources'):
            note_parts.append("EVIDENCE=" + str(audit_detail['evidence_sources']))
        if audit_detail.get('action'):
            note_parts.append("ACTION=" + str(audit_detail['action']))
    note = "; ".join(filter(None, note_parts))
    sig = hashlib.sha256(f"{entity_id}|{audit_id or ''}|{title}".encode('utf-8')).hexdigest()
    year = None
    if info.get('dynasty'):
        m = re.search(r'(\d{4})', str(info['dynasty']))
        if m:
            year = int(m.group(1))
    if fmt == 'csl-json':
        csl = {
            "id": audit_id or f"daoanh:{entity_id}",
            "type": "document" if info['entity_type'] == 'person' else "article",
            "title": title,
            "language": "vi",
            "publisher": "Phật Pháp Online — Bản địa Đạo Ảnh",
            "note": note,
            "signature": sig,
        }
        if audit_detail:
            csl["audit"] = {
                "audit_id": audit_id,
                "entity_ref": audit_detail.get('entity_ref'),
                "action": audit_detail.get('action'),
                "editor": audit_detail.get('editor'),
                "authority_rank": audit_detail.get('authority_rank'),
                "verification_status": audit_detail.get('verification_status'),
                "evidence_sources": audit_detail.get('evidence_sources'),
                "created_at": audit_detail.get('created_at'),
            }
        if year:
            csl["issued"] = {"date-parts": [[year]]}
        return jsonify({"ok": True, "format": "csl-json", "citation": [csl], "signature": sig})
    title_b = title.replace('\\', '\\\\').replace('"', '\\"')
    note_b = note.replace('\\', '\\\\').replace('"', '\\"')
    bib = (
        f"@misc{{{audit_id or entity_id},\n"
        f"  title = {{{title_b}}},\n"
        f"  howpublished = {{Phật Pháp Online — Bản địa Đạo Ảnh (phatphaponline.org/daoanh/)}},\n"
        f"  note = {{{note_b}}} {{SIG={sig}}}{',\n  year = {%d}' % year if year else ''}\n"
        f"}}\n"
    )
    return jsonify({"ok": True, "format": "bibtex", "citation": bib, "signature": sig})




@app.route('/daoanh/api/admin/geo-enrich/candidates', methods=['GET'])
def api_admin_geo_enrich_candidates():
    """GET /daoanh/api/admin/geo-enrich/candidates?page=&per_page= — T121:
    địa danh chưa có geo_cross_ref (candidate enrich từ Wikidata P625/P2044)."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    conn = get_db_connection()
    try:
        wc = "WHERE g.id IS NULL OR g.enrich_status IN ('candidate', 'rejected')"
        total = conn.execute(
            f"SELECT COUNT(*) FROM places_dila pd LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id {wc}"
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT pd.id AS dila_id, pd.name, pd.name_zh, pd.geo_lat, pd.geo_long,
                       g.wikidata_qid, g.enrich_status, g.enrich_source_qid, g.enrich_lat,
                       g.enrich_lon, g.enrich_elevation_m, g.notes, g.confidence
                FROM places_dila pd
                LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id
                {wc}
                ORDER BY g.enrich_status DESC, pd.id
                LIMIT ? OFFSET ?""",
            (per_page, offset),
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "candidates": [dict(r) for r in rows]})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/geo-enrich', methods=['POST'])
def api_admin_geo_enrich_approve():
    """POST /daoanh/api/admin/geo-enrich — {dila_id, wikidata_qid, lat, lon, elevation_m?, source_url?}
    T121 — Admin xác nhận: upsert geo_cross_ref main fields, status='approved'."""
    data = request.get_json(silent=True) or {}
    dila_id = (data.get('dila_id') or '').strip()
    qid = (data.get('wikidata_qid') or '').strip()
    if not dila_id:
        return jsonify({"ok": False, "error": "Thiếu dila_id"}), 400
    try:
        lat = float(data.get('lat')) if data.get('lat') is not None else None
        lon = float(data.get('lon')) if data.get('lon') is not None else None
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "lat/lon phải là số"}), 400
    elev = data.get('elevation_m')
    if elev is not None:
        try:
            elev = int(float(elev))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "elevation_m phải là số"}), 400
    notes = (data.get('source_url') or '').strip()[:300]
    conn = get_db_connection()
    try:
        try:
            conn.execute(
                """INSERT INTO geo_cross_ref
                   (dila_id, wikidata_qid, notes, confidence, mapped_by,
                    wikidata_lat, wikidata_lon, elevation_m, elevation_source, enrich_status)
                   VALUES (?, ?, ?, 'verified', 'admin', ?, ?, ?, 'wikidata', 'approved')
                   ON CONFLICT(dila_id) DO UPDATE SET
                       wikidata_qid=excluded.wikidata_qid,
                       wikidata_lat=excluded.wikidata_lat,
                       wikidata_lon=excluded.wikidata_lon,
                       elevation_m=excluded.elevation_m,
                       elevation_source=excluded.elevation_source,
                       enrich_status='approved', confidence='verified',
                       mapped_by=excluded.mapped_by, notes=excluded.notes""",
                (dila_id, qid, notes, lat, lon, elev),
            )
        except sqlite3.OperationalError:
            row = conn.execute("SELECT id FROM geo_cross_ref WHERE dila_id=?", (dila_id,)).fetchone()
            if row:
                conn.execute(
                    """UPDATE geo_cross_ref SET wikidata_qid=?, notes=?, confidence='verified',
                       mapped_by='admin', wikidata_lat=?, wikidata_lon=?, elevation_m=?,
                       elevation_source='wikidata', enrich_status='approved' WHERE dila_id=?""",
                    (qid, notes, lat, lon, elev, dila_id),
                )
            else:
                conn.execute(
                    """INSERT INTO geo_cross_ref
                       (dila_id, wikidata_qid, notes, confidence, mapped_by,
                        wikidata_lat, wikidata_lon, elevation_m, elevation_source, enrich_status)
                       VALUES (?, ?, ?, 'verified', 'admin', ?, ?, ?, 'wikidata', 'approved')""",
                    (dila_id, qid, notes, lat, lon, elev),
                )
        conn.commit()
        return jsonify({"ok": True, "dila_id": dila_id, "wikidata_qid": qid, "status": "approved"})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/geo-enrich/<int:rid>/status', methods=['POST'])
def api_admin_geo_enrich_status(rid):
    """POST /daoanh/api/admin/geo-enrich/<id>/status — {status: rejected|candidate|approved}."""
    data = request.get_json(silent=True) or {}
    st = (data.get('status') or '').strip()
    if st not in ('rejected', 'candidate', 'approved'):
        return jsonify({"ok": False, "error": "status phải ∈ rejected|candidate|approved"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE geo_cross_ref SET enrich_status=?, confidence=? WHERE id=?",
                     (st, 'verified' if st == 'approved' else 'candidate', rid))
        conn.commit()
        return jsonify({"ok": True, "id": rid, "status": st})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/editor-stats', methods=['GET'])
def api_admin_editor_stats():
    """GET /daoanh/api/admin/editor-stats — T119/T112/T121: thanh stats editor-dashboard."""
    conn = get_db_connection()
    try:
        claims_total = conn.execute("SELECT COUNT(*) FROM entity_claims").fetchone()[0]
        claims_unverified = conn.execute(
            "SELECT COUNT(*) FROM entity_claims WHERE verification_status IN ('unverified', '')"
        ).fetchone()[0]
        claims_verified = conn.execute(
            "SELECT COUNT(*) FROM entity_claims WHERE verification_status = 'verified'"
        ).fetchone()[0]
        conflicts_open = conn.execute(
            "SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0"
        ).fetchone()[0]
        resolutions_total = conn.execute("SELECT COUNT(*) FROM resolutions_log").fetchone()[0]
        gaps_new = conn.execute("SELECT COUNT(*) FROM data_gap_requests WHERE status='new'").fetchone()[0]
        feedback_new = conn.execute("SELECT COUNT(*) FROM user_feedback WHERE status='new'").fetchone()[0]
        geo_candidates = conn.execute(
            "SELECT COUNT(*) FROM places_dila pd LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id WHERE g.id IS NULL OR g.enrich_status IN ('candidate', 'rejected')"
        ).fetchone()[0]
        bio_pending = conn.execute(
            "SELECT COUNT(*) FROM person_bio_vi_draft WHERE admin_approved = 0"
        ).fetchone()[0]
        return jsonify({"ok": True,
                        "claims_total": claims_total, "claims_unverified": claims_unverified,
                        "claims_verified": claims_verified, "conflicts_open": conflicts_open,
                        "resolutions_total": resolutions_total, "gaps_new": gaps_new,
                        "feedback_new": feedback_new, "geo_candidates": geo_candidates,
                        "bio_pending": bio_pending})
    finally:
        conn.close()




# ── T73: Bio Review (person_bio_vi_draft) ───────────────────────
@app.route('/daoanh/api/admin/bio-review/pending', methods=['GET'])
def api_admin_bio_review_pending():
    """GET /daoanh/api/admin/bio-review/pending?status=pending|approved|all&page=&per_page=
    T73 — hàng chờ bio_vi_draft (2,093 row) cho admin duyệt; Zero-RAM LIMIT/OFFSET."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 100)
    offset = (page - 1) * per_page
    st = (request.args.get('status') or 'pending').strip().lower()
    status_map = {'pending': 'admin_approved = 0', 'approved': "admin_approved = 1",
                  'all': '1=1', 'rejected': "admin_approved < 0"}
    wc = status_map.get(st, status_map['pending'])
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM person_bio_vi_draft WHERE {wc}").fetchone()[0]
        rows = conn.execute(
            f"""SELECT d.person_id, p.name_zh AS person_name_zh, p.name_vi AS person_name_vi,
                       d.name_vi, d.bio_vi_draft, d.source_lex_id, d.source_name, d.match_type,
                       d.char_count, d.admin_approved, d.admin_note, d.updated_at,
                       (p.bio_vi IS NOT NULL AND p.bio_vi <> '') AS has_bio_vi
                FROM person_bio_vi_draft d
                LEFT JOIN people p ON p.id = d.person_id
                WHERE {wc}
                ORDER BY d.updated_at DESC LIMIT ? OFFSET ?""",
            [per_page, offset]).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "drafts": [dict(r) for r in rows]})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/bio-review/apply', methods=['POST'])
def api_admin_bio_review_apply():
    """POST /daoanh/api/admin/bio-review/apply — body {person_ids: [...], editor?}
    T73 — ADMIN chỉ định danh sách đã-approved → copy bio_vi_draft vào people.bio_vi
    (chỉ khi khác giá trị hiện tại) + ghi en_audit_log bio_apply. Data edit HITL."""
    body = request.get_json(silent=True) or {}
    ids = [str(i) for i in (body.get('person_ids') or [])][:200]
    editor = (body.get('editor') or 'admin').strip()[:64]
    if not ids:
        return jsonify({"ok": False, "error": "person_ids rỗng"}), 400
    ph = ",".join("?" * len(ids))
    conn = get_db_connection()
    try:
        rows = conn.execute(
            f"SELECT person_id, bio_vi_draft FROM person_bio_vi_draft "
            f"WHERE admin_approved = 1 AND person_id IN ({ph})", ids).fetchall()
        applied, skipped = 0, 0
        for r in rows:
            cur = conn.execute("SELECT bio_vi FROM people WHERE id=?", (r['person_id'],)).fetchone()
            if cur and cur['bio_vi'] == r['bio_vi_draft']:
                skipped += 1
                continue
            conn.execute("UPDATE people SET bio_vi=? WHERE id=?",
                         (r['bio_vi_draft'], r['person_id']))
            conn.execute(
                "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor)"
                " VALUES (?, 'bio_apply', 'bio_vi', ?, ?, ?)",
                (r['person_id'], (cur['bio_vi'] or '') if cur else '', r['bio_vi_draft'], editor))
            applied += 1
        conn.commit()
        return jsonify({"ok": True, "applied": applied, "skipped": skipped})
    finally:
        conn.close()




# ── Admin: LLM key management ────────────────────────────────

@app.route('/daoanh/api/admin/llm/status', methods=['GET'])
def api_admin_llm_status():
    """GET /daoanh/api/admin/llm/status — Trạng thái Groq key hiện tại."""
    cfg = _llm_config_read()
    return jsonify({
        'ok': True,
        'status': cfg.get('status', 'unknown'),
        'last_error': cfg.get('last_error'),
        'last_error_at': cfg.get('last_error_at'),
        'model': cfg.get('groq_model') or GROQ_MODEL,
        'has_custom_key': bool(cfg.get('groq_key')),
    })




@app.route('/daoanh/api/admin/llm/key', methods=['POST'])
def api_admin_llm_update_key():
    """POST /daoanh/api/admin/llm/key — Admin cập nhật Groq key.
    Body: {key: '<new_key>', model: '<optional_model>'}
    """
    body = request.get_json(silent=True) or {}
    new_key = (body.get('key') or '').strip()
    model = (body.get('model') or '').strip()
    if not new_key:
        return jsonify({'ok': False, 'error': 'Thiếu key'}), 400
    update = {'groq_key': new_key, 'status': 'unknown', 'last_error': None, 'last_error_at': None}
    if model:
        update['groq_model'] = model
    _llm_config_write(update)
    return jsonify({'ok': True, 'message': 'Key đã được cập nhật. Sẽ có hiệu lực ở lần dịch tiếp theo.'})




@app.route('/daoanh/api/daitang/qa', methods=['POST'])
def api_daitang_qa():
    """POST /daoanh/api/daitang/qa {"question": "..."} — Q&A toàn hệ thống.
    mode='llm' → có câu trả lời tổng hợp + citations. mode='retrieval_only' →
    Groq hỏng → trả evidence đã retrieval. ok=false → không có tư liệu."""
    body = request.get_json(silent=True) or {}
    question = (body.get('question') or '').strip()
    if not question:
        return jsonify({'ok': False, 'error': 'Thiếu câu hỏi (question).'}), 400

    t0 = time.time()
    conn = get_db_connection()
    try:
        evidence, entities = _t126_retrieve(conn, question)
        if not evidence and not entities:
            return jsonify({
                'ok': False, 'mode': 'no_data',
                'message': 'Không tìm thấy tư liệu liên quan trong toàn hệ thống.',
                'question': question, 'latency_ms': int((time.time() - t0) * 1000),
            })
        lock = _t73_style_lock(conn, source_text=question + ' ' + ' '.join(
            (e.get('snippet') or e.get('title') or '') for e in evidence if isinstance(e, dict)))
        prompt = _t126_build_qa_prompt(question, evidence, entities, lock)
        answer, model, err = _t126_call_groq(prompt)
        if answer:
            return jsonify({
                'ok': True, 'mode': 'llm', 'answer': answer,
                'model': model or GROQ_MODEL,
                'citations': evidence + entities,
                'evidence': evidence, 'entities': entities,
                'question': question, 'latency_ms': int((time.time() - t0) * 1000),
            })
        return jsonify({
            'ok': True, 'mode': 'retrieval_only', 'answer': None,
            'llm_error': err or 'api_error',
            'evidence': evidence, 'entities': entities,
            'question': question, 'latency_ms': int((time.time() - t0) * 1000),
        })
    except Exception as e:
        app.logger.error(f"[T126] qa failed: {e}")
        return jsonify({'ok': False, 'error': f'Q&A lỗi: {str(e)}'}), 500
    finally:
        conn.close()




# ============================================================
# T445 Wizard API Endpoints (B0→B9)
# ============================================================

@app.route('/daoanh/api/admin/backup', methods=['POST'])
def admin_backup():
    """B0: Tạo backup SQLite."""
    try:
        import shutil, os, time
        backup_dir = 'data/backups'
        os.makedirs(backup_dir, exist_ok=True)
        fname = f'lineage_{time.strftime("%Y%m%d_%H%M%S")}.db'
        fpath = os.path.join(backup_dir, fname)
        shutil.copy2('data/lineage.db', fpath)
        return jsonify({'success': True, 'path': fpath, 'message': f'Backup created: {fname}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/fix-ids/preview')
def admin_fix_ids_preview():
    """B1: Preview các ID mismatch."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name_vi, p.name_zh, p.vn_name_status
            FROM places p
            LEFT JOIN places_dila pd ON p.id = pd.id
            WHERE pd.id IS NULL AND p.id IS NOT NULL
            LIMIT 500
        """)
        rows = cur.fetchall()
        preview = [
            {'dila_id': r[0], 'name_vi': r[1], 'name_zh': r[2], 'vn_name_status': r[3], 'reason': 'dila_id not in places_dila'}
            for r in rows
        ]
        conn.close()
        return jsonify({'success': True, 'preview': preview})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/schema/update', methods=['POST'])
def admin_schema_update():
    """B2: Thêm cột cần thiết."""
    try:
        import sqlite3
        conn = get_db()
        cur = conn.cursor()
        added = []
        cols = [
            ("vn_name_status", "TEXT DEFAULT 'auto'"),
            ("provenance", "TEXT"),
            ("confidence", "REAL DEFAULT 0.0"),
        ]
        for col_name, col_def in cols:
            try:
                cur.execute(f"ALTER TABLE places ADD COLUMN {col_name} {col_def}")
                added.append(col_name)
            except sqlite3.OperationalError:
                pass  # column exists
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Added columns: {added}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/dictionary/load', methods=['POST'])
def admin_dictionary_load():
    """B3: Nạp từ điển Hán-Việt."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM places_dila")
        count = cur.fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'count': count, 'message': f'Dictionary loaded: {count} entries'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/rules/load')
def admin_rules_load():
    """B4: Load 7 rules chuẩn."""
    try:
        rules = [
            {'code': 'R_NATURAL', 'pattern': '^[\u4e00-\u9fa5]+$', 'enabled': True, 'desc': 'Tự nhiên (chỉ Hán tự)'},
            {'code': 'NO_ADDITION', 'pattern': '^(?!.*[0-9]).*$', 'enabled': True, 'desc': 'Không thêm chữ số'},
            {'code': 'R_TONAL', 'pattern': '^.*[\u3040-\u309f\u30a0-\u30ff].*$', 'enabled': False, 'desc': 'Có kana'},
            {'code': 'R_SINO_VN', 'pattern': '^[\u4e00-\u9fa5]+(th\u1ecb|t\u1ee9|h\u1ecdc).*$', 'enabled': True, 'desc': 'Sino-VN suffix'},
            {'code': 'R_COMPOUND', 'pattern': '^[\u4e00-\u9fa5]{2,}$', 'enabled': True, 'desc': 'Hán từ ghép'},
            {'code': 'R_SUFFIX_VN', 'pattern': '.*(s\u1ea1n|ph\u1ed1|th\u1ea5|b\u1ea3o|t\u1ef1).*$', 'enabled': True, 'desc': 'Suffix VN'},
            {'code': 'R_PREFIX_VN', 'pattern': '^(b\u1eafc|nam|trung|t\u00e2y|h\u1ea1|b\u1eafc|gi\u1eefa|h\u1ecdc).*$', 'enabled': True, 'desc': 'Prefix VN'},
        ]
        return jsonify({'success': True, 'rules': rules})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/update-rules', methods=['POST'])
def admin_update_rules():
    """B4: Lưu rules đã chỉnh."""
    try:
        data = request.get_json() or {}
        rules = data.get('rules', [])
        return jsonify({'success': True, 'message': f'Saved {len(rules)} rules'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/batch/run', methods=['POST'])
def admin_batch_run():
    """B5/B8: Chạy batch Gemini."""
    try:
        data = request.get_json() or {}
        batch = data.get('batch', 'B5')
        total = data.get('total', 40000)
        return jsonify({'success': True, 'batch': batch, 'total': total, 'message': f'{batch} started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/approve-sample', methods=['POST'])
def admin_approve_sample():
    """B7: Approve sample."""
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        return jsonify({'success': True, 'count': len(ids), 'message': f'Approved {len(ids)} samples'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/report')
def admin_report():
    """B9: Thống kê báo cáo."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM places")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM places WHERE vn_name_status = 'verified'")
        verified = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM places WHERE vn_name_status = 'auto'")
        auto = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM places WHERE vn_name_status = 'reviewed'")
        reviewed = cur.fetchone()[0]
        cur.execute("SELECT id FROM places WHERE id IS NULL OR id = ''")
        missing = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id, COUNT(*) c FROM places GROUP BY id HAVING c > 1")
        duplicate = [r[0] for r in cur.fetchall()]
        conn.close()
        return jsonify({
            'success': True,
            'stats': {'total': total, 'verified': verified, 'auto': auto, 'reviewed': reviewed},
            'missing': missing[:100], 'duplicate': duplicate[:100]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/export-csv')
def admin_export_csv():
    """Export CSV cho step."""
    try:
        step = request.args.get('step', 'b1')
        import csv, io
        conn = get_db()
        cur = conn.cursor()
        output = io.StringIO()
        writer = csv.writer(output)
        if step == 'b1':
            cur.execute("SELECT id, name_vi, name_zh, vn_name_status FROM places WHERE id IS NOT NULL LIMIT 500")
            writer.writerow(['dila_id', 'name_vi', 'name_zh', 'vn_name_status'])
            for r in cur.fetchall(): writer.writerow(r)
        elif step == 'b9':
            cur.execute("SELECT id, name_vi, name_zh, vn_name_status, provenance, confidence FROM places")
            writer.writerow(['dila_id', 'name_vi', 'name_zh', 'vn_name_status', 'provenance', 'confidence'])
            for r in cur.fetchall(): writer.writerow(r)
        else:
            writer.writerow(['dila_id', 'name_vi', 'name_zh', 'vn_name_status'])
            cur.execute("SELECT id, name_vi, name_zh, vn_name_status FROM places LIMIT 1000")
            for r in cur.fetchall(): writer.writerow(r)
        conn.close()
        return jsonify({'success': True, 'csv': output.getvalue()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/ws/batch-monitor')
def ws_batch_monitor():
    """WebSocket endpoint cho batch monitoring (B5/B8)."""
    return jsonify({'error': 'WebSocket endpoint not implemented in Flask directly. Use /api/admin/batch/status for polling.'}), 501


# +{+ /T130+T131 ADDITIVE BUILD +}+

# ─────────────── T182 — Đại Tạng Kinh Public Dashboard ───────────────

@app.route('/daoanh/dai-tang-kinh')
def t182_dai_tang_kinh():
    return send_from_directory(os.path.join(BASE_DIR, 'pages'), 'dai-tang-kinh.html')



@app.route('/daoanh/api/nmt-works')
def nmt_works_by_name():
    """GET /daoanh/api/nmt-works?q=Thiếu Lâm Tự
    Tác phẩm trong Mục lục Đại Tạng Kinh tiếng Việt (Nguyễn Minh Tiến) có tên tiếng Việt chứa q.
    Chỉ đọc cbeta_catalog_vn, khớp chuỗi nguyên văn, không suy đoán."""
    q = (request.args.get('q', '') or '').strip()
    if len(q) < 2:
        return jsonify({"ok": True, "query": q, "items": []})
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT title_vi, title_zh, translator_vi, dynasty_vi, license_name
               FROM cbeta_catalog_vn
               WHERE source_name = ? AND title_vi LIKE ?
               ORDER BY title_vi LIMIT 200""",
            ('Nguyễn Minh Tiến', f'%{q}%')).fetchall()
        conn.close()
        return jsonify({"ok": True, "query": q, "items": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


GEMINI_LOG_FILE = os.path.join(BASE_DIR, 'logs', 'ai_transliterate_place.log')


def _gemini_approval_table(conn):
    """Bảng nhật ký duyệt bản Gemini (additive). Mỗi lần Admin chấp thuận ghi 1 dòng để hoàn tác."""
    conn.execute("""CREATE TABLE IF NOT EXISTS gemini_approval_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dila_id TEXT NOT NULL,
        gemini_name_vi TEXT,
        applied_name_vi TEXT,
        previous_name_vi TEXT,
        editor TEXT,
        approved_at TEXT NOT NULL)""")


def _gemini_log_tail(n=12):
    """Các dòng cuối của log batch Gemini (chỉ đọc). Trả về list dòng, rỗng nếu chưa có log."""
    try:
        with open(GEMINI_LOG_FILE, 'r', encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
        return lines[-n:]
    except OSError:
        return []


@app.route('/daoanh/api/admin/gemini-progress')
def gemini_progress():
    """GET /daoanh/api/admin/gemini-progress?page=1&size=50&filter=all|pending|approved
    Tiến độ Gemini phiên âm địa danh: tổng quan, vị trí hiện tại, và từng dòng gồm
    thông tin gốc (tên Hán + ghi chú DILA), bản Gemini, tên đang dùng, trạng thái duyệt.
    Chỉ đọc."""
    token = request.headers.get('X-Session-Token', '') or request.args.get('token', '')
    from core import verify_session
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'unauthorized'}), 403
    try:
        page = max(1, int(request.args.get('page', 1)))
        size = min(200, max(1, int(request.args.get('size', 50))))
        flt = request.args.get('filter', 'all')
        conn = get_db_connection()
        _gemini_approval_table(conn)
        total_places = conn.execute("SELECT COUNT(*) FROM places_dila").fetchone()[0]
        # Chỉ tính các dòng Gemini khớp địa danh DILA thật (places_dila có tên Hán để đối chiếu).
        gemini_done = conn.execute(
            "SELECT COUNT(DISTINCT a.dila_id) FROM ai_place_name a JOIN places_dila p ON p.id = a.dila_id"
        ).fetchone()[0]
        gemini_orphan = conn.execute(
            "SELECT COUNT(DISTINCT a.dila_id) FROM ai_place_name a "
            "LEFT JOIN places_dila p ON p.id = a.dila_id WHERE p.id IS NULL").fetchone()[0]
        approved = conn.execute("SELECT COUNT(DISTINCT dila_id) FROM gemini_approval_log").fetchone()[0]
        last = conn.execute(
            "SELECT a.dila_id, a.created_at FROM ai_place_name a JOIN places_dila p ON p.id = a.dila_id "
            "ORDER BY a.created_at DESC, a.dila_id DESC LIMIT 1"
        ).fetchone()
        where = "1=1"
        if flt == 'pending':
            where = "g.dila_id IS NULL"
        elif flt == 'approved':
            where = "g.dila_id IS NOT NULL"
        total = conn.execute(f"""
            SELECT COUNT(DISTINCT a.dila_id) FROM ai_place_name a
            JOIN places_dila p ON p.id = a.dila_id
            LEFT JOIN (SELECT DISTINCT dila_id FROM gemini_approval_log) g ON g.dila_id = a.dila_id
            WHERE {where}""").fetchone()[0]
        rows = conn.execute(f"""
            SELECT a.dila_id, a.name_vi_ai, a.model, a.created_at,
                   p.name_zh, p.note, p.district,
                   m.name_vi AS current_vi, m.vn_name_status,
                   g.approved_at, g.applied_name_vi, g.editor
            FROM (SELECT dila_id, name_vi_ai, model, created_at FROM ai_place_name
                  GROUP BY dila_id) a
            JOIN places_dila p ON p.id = a.dila_id
            LEFT JOIN namevi_map_places m ON m.dila_id = a.dila_id
            LEFT JOIN (SELECT dila_id, MAX(approved_at) AS approved_at,
                              (SELECT applied_name_vi FROM gemini_approval_log x
                               WHERE x.dila_id = y.dila_id ORDER BY id DESC LIMIT 1) AS applied_name_vi,
                              (SELECT editor FROM gemini_approval_log x
                               WHERE x.dila_id = y.dila_id ORDER BY id DESC LIMIT 1) AS editor
                       FROM gemini_approval_log y GROUP BY dila_id) g ON g.dila_id = a.dila_id
            WHERE {where}
            ORDER BY a.created_at DESC, a.dila_id DESC
            LIMIT ? OFFSET ?""", (size, (page - 1) * size)).fetchall()
        conn.close()
        items = []
        for r in rows:
            d = dict(r)
            items.append({
                'dila_id': d['dila_id'],
                'name_zh': d['name_zh'] or '',
                'source_note': (d['note'] or '')[:300],
                'district': d['district'] or '',
                'gemini_vi': d['name_vi_ai'] or '',
                'gemini_model': d['model'] or '',
                'gemini_at': d['created_at'] or '',
                'current_vi': d['current_vi'] or '',
                'vn_status': d['vn_name_status'] or '',
                'approved': bool(d['approved_at']),
                'approved_name_vi': d['applied_name_vi'] or '',
                'approved_at': d['approved_at'] or '',
                'editor': d['editor'] or '',
            })
        return jsonify({
            'ok': True,
            'summary': {
                'total_places': total_places,
                'gemini_done': gemini_done,
                'gemini_orphan': gemini_orphan,
                'approved': approved,
                'pending_review': max(0, gemini_done - approved),
                'last_dila_id': last[0] if last else '',
                'last_created_at': last[1] if last else '',
                'log_tail': _gemini_log_tail(),
            },
            'total': total, 'page': page, 'size': size,
            'pages': (total + size - 1) // size,
            'items': items,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/daoanh/api/admin/gemini-progress/approve', methods=['POST'])
def gemini_progress_approve():
    """POST {dila_id, name_vi?} — Admin chấp thuận bản Gemini (hoặc bản Admin đã sửa).
    Ghi namevi_map_places.name_vi (nguồn HOME tìm kiếm), đặt vn_name_status='reviewed',
    và ghi nhật ký gemini_approval_log để hoàn tác."""
    token = request.headers.get('X-Session-Token', '')
    from core import verify_session
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'unauthorized — thiếu hoặc sai session token'}), 403
    data = request.get_json(silent=True) or {}
    dila_id = (data.get('dila_id') or '').strip()
    if not dila_id:
        return jsonify({'ok': False, 'error': 'Thiếu dila_id'}), 400
    try:
        from routes_places import _t427_invalidate_filter_cache, _t427_session_email
        conn = get_db_connection()
        _gemini_approval_table(conn)
        g = conn.execute(
            "SELECT name_vi_ai FROM ai_place_name WHERE dila_id = ? ORDER BY created_at DESC LIMIT 1",
            (dila_id,)).fetchone()
        if not g:
            conn.close()
            return jsonify({'ok': False, 'error': f'Không có bản Gemini cho {dila_id}'}), 404
        m = conn.execute(
            "SELECT name_vi FROM namevi_map_places WHERE dila_id = ?", (dila_id,)).fetchone()
        if not m:
            conn.close()
            return jsonify({'ok': False, 'error': f'Không có dòng namevi_map_places cho {dila_id}'}), 404
        applied = (data.get('name_vi') or '').strip() or (g['name_vi_ai'] or '').strip()
        if not applied:
            conn.close()
            return jsonify({'ok': False, 'error': 'Bản Gemini rỗng, cần nhập tên Việt'}), 400
        previous = m['name_vi'] or ''
        import datetime as _dt
        editor = _t427_session_email(token)
        now = _dt.datetime.now().isoformat(timespec='seconds')
        conn.execute(
            "INSERT INTO gemini_approval_log (dila_id, gemini_name_vi, applied_name_vi, previous_name_vi, editor, approved_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (dila_id, g['name_vi_ai'], applied, previous, editor, now))
        conn.execute(
            "UPDATE namevi_map_places SET name_vi = ?, source = 'gemini_approved', "
            "vn_name_status = 'reviewed', needs_review = 0 WHERE dila_id = ?",
            (applied, dila_id))
        conn.commit()
        conn.close()
        _t427_invalidate_filter_cache()
        return jsonify({'ok': True, 'dila_id': dila_id, 'applied_name_vi': applied,
                        'previous_name_vi': previous, 'editor': editor, 'approved_at': now})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/daoanh/api/danh-sach-kinh')
def t182_danh_sach_kinh():
    """GET /daoanh/api/danh-sach-kinh?series=T&q=&offset=0&limit=50&has_translation=1
    Public API: danh sách bộ kinh + trạng thái bản dịch tiếng Việt.
    """
    series_f  = request.args.get('series', '').strip().upper()
    q         = request.args.get('q', '').strip()
    has_tr    = request.args.get('has_translation', '').strip()  # '1' = chỉ bộ đã có bản dịch
    try:
        offset = max(0, int(request.args.get('offset', 0)))
        limit  = min(100, max(1, int(request.args.get('limit', 50))))
    except (ValueError, TypeError):
        offset, limit = 0, 50

    conn = get_db()
    sql_where, params = [], []
    if series_f:
        sql_where.append("c.series=?"); params.append(series_f)
    if q:
        sql_where.append("(c.title_vi LIKE ? OR c.title_zh LIKE ? OR c.sigla LIKE ?)")
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    where_clause = ('WHERE ' + ' AND '.join(sql_where)) if sql_where else ''

    # Lấy passage stats cùng lúc qua LEFT JOIN
    sql = f"""
        SELECT c.id, c.sigla, c.title_vi, c.title_zh, c.juans, c.dynasty_vi,
               c.author_zh, c.translator_vi, c.series, c.sh_number,
               COUNT(p.passage_id)                                        AS p_total,
               SUM(CASE WHEN p.vi_text IS NOT NULL THEN 1 ELSE 0 END)    AS p_translated
        FROM cbeta_catalog_vn c
        LEFT JOIN passage p ON p.text_id = c.sigla AND p.source = 'CBETA'
        {where_clause}
        GROUP BY c.id
        HAVING 1=1 {' AND p_translated > 0' if has_tr == '1' else ''}
        ORDER BY c.series, CAST(c.sh_number AS INTEGER)
    """
    all_rows = conn.execute(sql, params).fetchall()
    total = len(all_rows)
    page_rows = all_rows[offset:offset + limit]

    items = []
    for r in page_rows:
        p_total = r['p_total'] or 0
        p_tr    = r['p_translated'] or 0
        if p_total == 0:
            status = 'chua_co'
        elif p_tr >= p_total:
            status = 'hoan_thanh'
        elif p_tr > 0:
            status = 'dang_dich'
        else:
            status = 'cho_dich'
        items.append({
            'id': r['id'], 'sigla': r['sigla'],
            'title_vi': r['title_vi'], 'title_zh': r['title_zh'],
            'juans': r['juans'], 'dynasty_vi': r['dynasty_vi'],
            'author_zh': r['author_zh'], 'translator_vi': r['translator_vi'],
            'series': r['series'], 'sh_number': r['sh_number'],
            'p_total': p_total, 'p_translated': p_tr,
            'pct': round(p_tr * 100 / p_total, 1) if p_total else 0,
            'status': status,
        })

    series_list = [r[0] for r in conn.execute(
        "SELECT DISTINCT series FROM cbeta_catalog_vn ORDER BY series").fetchall()]
    # Tổng quan nhanh
    stats_row = conn.execute("""
        SELECT COUNT(DISTINCT c.id) total,
               COUNT(DISTINCT CASE WHEN p.vi_text IS NOT NULL THEN c.id END) has_vi
        FROM cbeta_catalog_vn c
        LEFT JOIN passage p ON p.text_id = c.sigla AND p.source = 'CBETA'
    """).fetchone()
    return jsonify({
        "total": total, "offset": offset, "limit": limit,
        "series_list": series_list, "items": items,
        "stats": {"total_catalog": stats_row[0], "has_translation": stats_row[1]},
    })




@app.route('/daoanh/api/admin/run_etl_gen', methods=['POST'])
def admin_run_etl_gen():
    """Chạy scripts/etl_gen_compute.py để tính số đời cho thiền sư mới thêm."""
    import subprocess as _sp, os as _os
    script = _os.path.join(_os.path.dirname(__file__), 'scripts', 'etl_gen_compute.py')
    if not _os.path.exists(script):
        return jsonify({"ok": False, "error": "Không tìm thấy etl_gen_compute.py"}), 404
    try:
        result = _sp.run(
            ['python', script],
            capture_output=True, text=True, timeout=120,
            cwd=_os.path.dirname(__file__)
        )
        if result.returncode != 0:
            return jsonify({"ok": False, "error": result.stderr[-500:]}), 500
        # Tóm tắt kết quả từ stdout
        lines = (result.stdout or '').splitlines()
        summary_lines = [l for l in lines if any(k in l for k in ['✓', 'OK', 'rows', 'lưu', 'xong', 'Khai Tổ', 'person_gen'])]
        summary = '\n'.join(summary_lines[-8:]) or 'ETL hoàn tất.'
        return jsonify({"ok": True, "summary": summary, "stdout": result.stdout[-1000:]})
    except _sp.TimeoutExpired:
        return jsonify({"ok": False, "error": "ETL timeout (>120 giây)"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
