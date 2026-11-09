"""Route nhom places: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""
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
from core import DYNASTY_NAMES, _T169_DIFF_SORT, _build_cate_ids_map, _compute_dataset_version, _detect_conflicts, _ensure_geo_cross_ref_table, _ensure_place_person_link_table, _ensure_place_timeline_events_table, _ensure_vietnamese, _fetch_wikidata_founders, _fetch_wikidata_timeline, _get_dynasty_context, _lexicon_han_lookup, _name_vi_evidence, _note_category_to_icon_type, _persist_canonical_decision, _resolve_dila_id, _resolve_entity_id, _resolve_place_id, _source_authority_map, _t112_record_gap, _t360_resolve_place_name_vi_source, _t427_filter_counts, _t427_invalidate_filter_cache, _t427_session_email, _t427_source_badge, _t86_resolve_display_name, _translate_admin_text, _translate_dynasty_name, _translate_zh_term, app, ensure_long_id, ensure_places_pending_fts, ensure_places_search_fts, get_cbdb_conn, get_chronology_conn, get_db, normalize_text, parse_dila_district, verify_session



@app.route('/daoanh/api/admin/places_missing_info')
def places_missing_info():
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        conn = get_db_connection()
        where = "WHERE (country IS NULL OR country = '') OR (district_raw IS NULL OR district_raw = '')"
        total = conn.execute(f"SELECT COUNT(*) FROM places_pending {where}").fetchone()[0]
        rows = conn.execute(f"""
            SELECT id, name_zh, name_vi, country, district_raw, province, gps_lat, gps_long
            FROM places_pending {where}
            ORDER BY id ASC NULLS LAST
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        conn.close()
        places = []
        for r in rows:
            p = dict(r)
            p['id'] = ensure_long_id(p['id'])
            places.append(p)
        return jsonify({"success": True, "total": total, "limit": limit, "offset": offset, "places": places})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/place-groq-review', methods=['GET'])
def api_admin_place_groq_review_list():
    """GET list hàng review của pipeline T169.

    Filter mặc định (G7): needs_review=1 AND diff_type IS NOT NULL AND review_status='conflict'
    (chỉ conflict — KHÔNG trộn api_error/pending).
    status query: conflict | api_error | verified | approved_dict | all  (tab UI)
    diff query: POLYPHONIC_CHAR | TAXONOMY_VARIANT | PHONETIC_MISMATCH | NONE (optional)
    """
    try:
        token = request.headers.get('X-Session-Token', '')
        if not verify_session(token):
            return jsonify({'ok': False, 'error': 'Unauthorized'}), 403
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        status = (request.args.get('status') or 'conflict').strip()
        diff = (request.args.get('diff') or '').strip()
        where = []
        params = []
        if status == 'api_error':
            where.append("a.review_status='api_error' AND a.needs_review=1")
        elif status in ('verified', 'approved_dict'):
            where.append("a.review_status=? AND a.needs_review=0")
            params.append(status)
        elif status == 'all':
            pass
        else:  # default conflict (G7)
            where.append("a.needs_review=1 AND a.diff_type IS NOT NULL AND a.review_status='conflict'")
        if diff:
            where.append('a.diff_type=?')
            params.append(diff)
        wsql = (' WHERE ' + ' AND '.join(where)) if where else ''
        con = get_db_connection()
        total = con.execute(f"SELECT COUNT(*) FROM place_groq_audit a {wsql}", params).fetchone()[0]
        rows = con.execute(f"""
            SELECT a.id, a.name_zh,
                   COALESCE(p.name_vi, a.dict_vi) AS dict_vi,
                   a.groq_trans_vi, a.needs_review, a.review_status,
                   a.diff_type, a.diff_reason, a.model_id, a.checked_at
            FROM place_groq_audit a
            LEFT JOIN places_pending p ON p.id = a.id
            {wsql}
            ORDER BY {_T169_DIFF_SORT}, a.id
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()
        con.close()
        return jsonify({'ok': True, 'total': total, 'limit': limit, 'offset': offset,
                        'items': [dict(r) for r in rows], 'status': status})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/place-groq-review/<id>', methods=['PUT'])
def api_admin_place_groq_review_put(id):
    """PUT duyệt 1 địa danh — 3 bước 1 transaction (G6):
    ① place_groq_audit: status=verified|approved_dict, needs_review=0
    ② places_pending: name_vi=? + name_vi_norm=<recompute> (reuse normalize_text)
    ③ namevi_map_places: UPSERT name_vi (WHERE dila_id; INSERT nếu thiếu)
    Body: {chosen: 'dict'|'groq'|'manual', name_vi? (bắt buộc khi manual)}
    """
    try:
        token = request.headers.get('X-Session-Token', '')
        if not verify_session(token):
            return jsonify({'ok': False, 'error': 'Unauthorized'}), 403
        body = request.get_json(silent=True) or {}
        chosen = (body.get('chosen') or '').strip()
        manual_vi = (body.get('name_vi') or '').strip()
        if chosen not in ('dict', 'groq', 'manual'):
            return jsonify({'ok': False, 'error': "chosen phải là dict|groq|manual"}), 400
        con = get_db_connection()
        try:
            row = con.execute("SELECT id, name_zh, dict_vi, groq_trans_vi FROM place_groq_audit WHERE id=?",
                              (id,)).fetchone()
            if not row:
                return jsonify({'ok': False, 'error': 'Không có hàng audit này'}), 404
            if chosen == 'dict':
                live = con.execute("SELECT name_vi FROM places_pending WHERE id=?", (id,)).fetchone()
                name_vi = ((live['name_vi'] if live and live['name_vi'] else '') or (row['dict_vi'] or '')).strip()
                new_status = 'verified'
            elif chosen == 'groq':
                name_vi = (row['groq_trans_vi'] or '').strip()
                new_status = 'approved_dict'
            else:
                name_vi = manual_vi
                new_status = 'verified'
            if not name_vi:
                return jsonify({'ok': False, 'error': 'name_vi rỗng — không thể duyệt'}), 400
            name_vi_norm = normalize_text(name_vi)
            with con:  # atomic 3 bước
                con.execute("""
                    UPDATE place_groq_audit
                    SET review_status=?, needs_review=0
                    WHERE id=?
                """, (new_status, id))
                con.execute("""
                    UPDATE places_pending SET name_vi=?, name_vi_norm=? WHERE id=?
                """, (name_vi, name_vi_norm, id))
                cur = con.execute("""
                    UPDATE namevi_map_places SET name_vi=?, source='reviewed_t169', needs_review=0
                    WHERE dila_id=?
                """, (name_vi, id))
                if cur.rowcount == 0:
                    con.execute("""
                        INSERT INTO namevi_map_places (dila_id, name_vi, name_zh, source, confidence, needs_review)
                        VALUES (?, ?, ?, 'reviewed_t169', 1.0, 0)
                    """, (id, name_vi, row['name_zh'] or ''))
            return jsonify({'ok': True, 'id': id, 'name_vi': name_vi,
                            'review_status': new_status, 'name_vi_norm': name_vi_norm})
        finally:
            con.close()
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/places_pending')
def places_pending():
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        search = (request.args.get('search', '') or '').strip()
        cate = (request.args.get('cate', 'admin_place') or '').strip()
        valid_cates = ('admin_place', 'temple_site', 'dynasty_region', 'mountain', 'river_lake', 'other')
        if cate not in valid_cates:
            cate = 'admin_place'

        cate_case = """
            CASE
                WHEN d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%' THEN 'temple_site'
                WHEN d.note_category LIKE '%山峰%' OR d.note_category LIKE '%山脈%' THEN 'mountain'
                WHEN d.note_category LIKE '%河流%' OR d.note_category LIKE '%湖泊%' OR d.note_category LIKE '%水系%' THEN 'river_lake'
                WHEN d.note_category LIKE '%人文地理區域%' THEN 'dynasty_region'
                WHEN d.note_category LIKE '%自然地理區域%' THEN 'other'
                ELSE 'admin_place'
            END
        """

        conn = get_db_connection()
        base_where = "p.id IS NOT NULL AND p.id != '' AND p.name_zh IS NOT NULL AND p.name_zh != '' AND p.note IS NOT NULL AND p.note != ''"
        params = [cate]
        if search:
            like = f'%{search}%'
            base_where += " AND (p.id LIKE ? OR p.name_zh LIKE ? OR p.name_vi LIKE ? OR m.name_vi LIKE ?)"
            params = [cate, like, like, like, like]

        if not search:
            # Đường nhanh: id theo cate đã cache → tra bằng index (không quét 176K dòng)
            cate_map = _build_cate_ids_map()
            cate_ids = cate_map["ids"].get(cate, [])
            cate_json = json.dumps(cate_ids)
            total = cate_map["distinct"].get(cate, 0)
            places = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       CASE WHEN p.note IS NOT NULL AND p.note != '' THEN 1 ELSE 0 END AS has_note
                FROM places_pending p
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE p.id IN (SELECT value FROM json_each(?))
                ORDER BY p.id ASC
                LIMIT ? OFFSET ?
            """, (cate_json, limit, offset)).fetchall()
        else:
            total = conn.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT p.id, {cate_case} AS cate_internal
                    FROM places_pending p
                    LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                    LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                    WHERE {base_where}
                )
                WHERE cate_internal = ?
            """, params).fetchone()[0]
            places = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       CASE WHEN p.note IS NOT NULL AND p.note != '' THEN 1 ELSE 0 END as has_note
                FROM places_pending p
                LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE {base_where} AND ({cate_case}) = ?
                ORDER BY p.id ASC NULLS LAST
                LIMIT ? OFFSET ?
            """, [*params, limit, offset]).fetchall()
        conn.close()
        places_list = []
        seen = set()
        for p in places:
            row = dict(p)
            lid = ensure_long_id(row['id'])
            if lid in seen:
                continue
            seen.add(lid)
            row['id'] = lid
            places_list.append(row)
        return jsonify({"success": True, "total": total, "limit": limit, "offset": offset, "places": places_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/places_error')
def places_error():
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT dila_id AS id, name_vi, name_zh, source, needs_review
            FROM namevi_map_places WHERE needs_review = 1
            LIMIT 500
        """).fetchall()
        seen = set(r['id'] for r in rows)
        results = [dict(r) for r in rows]
        if len(results) < 500:
            remaining = 500 - len(results)
            extra = conn.execute("""
                SELECT dila_id AS id, name_vi, name_zh, source, needs_review
                FROM namevi_map_places WHERE needs_review = 0
                LIMIT ?
            """, (remaining * 10,)).fetchall()
            for r in extra:
                if r['id'] in seen:
                    continue
                if re.search(r'[\u4e00-\u9fff]', str(r['name_vi'] or '')):
                    results.append(dict(r))
                    seen.add(r['id'])
                    if len(results) >= 500:
                        break
        conn.close()
        for r in results:
            r['id'] = ensure_long_id(r['id'])
        return jsonify({"success": True, "places": results, "total": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




# ── Public Place Search API (for places.html GIS map) ──────────────────


@app.route('/daoanh/api/places/search')
def api_places_search():
    """
    GET /daoanh/api/places/search?q=...&limit=20&dynasty=...
    Searches both `places` (GPS) and `namevi_map_places` (Vietnamese names).
    Optional `dynasty` param filters to places with matching lineage_chronology entries.
    Returns deduplicated results sorted by confidence.
    """
    try:
        q = request.args.get('q', '').strip()
        scope = request.args.get('scope', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        limit = min(int(request.args.get('limit', 50)), 5000)
        conn = get_db_connection()
        results = []
        seen = set()

        if q and len(q) < 2:
            return jsonify({"ok": False, "error": "Query too short (min 2 chars)"}), 400

        # Scope filter: temple only
        # place_type is empty for all records, so filter by name patterns
        scope_temple = scope == 'temple'
        temple_patterns = ['%寺', '%庵', '%塔', '%院', '%禪林', '%精舍', '%石窟', '%伽藍']
        temple_patterns_vi = ['%chùa%', '%tự viện%', '%thiền viện%', '%tịnh xá%', '%am%']
        offset = int(request.args.get('offset', 0))
        cate = request.args.get('cate', '').strip()
        # BUG-008: bbox filter for nearby places (south,west,north,east)
        bbox_filter = ""
        bbox_params_list = []
        raw_bbox = request.args.get('bbox', '').strip()
        if raw_bbox:
            try:
                south, west, north, east = map(float, raw_bbox.split(','))
                bbox_filter = "AND p.gps_lat BETWEEN ? AND ? AND p.gps_long BETWEEN ? AND ?"
                bbox_params_list = [south, north, west, east]
            except Exception:
                pass

        # Category filter by name_zh keywords (note_category column does not exist; place_type all null)
        CATE_LIKES = {
            'temple_site':   ['%寺', '%廟%', '%塔', '%庵', '%禪%', '%精舍%', '%伽藍%', '%石窟%'],
            'mountain':      ['%山', '%峰', '%嶺%', '%崖%', '%岳%', '%丘%'],
            'river_lake':    ['%江', '%河', '%湖', '%溪', '%潭%', '%海%', '%港%', '%渡%'],
            'dynasty_region':['%郡%', '%州', '%路%', '%府%', '%道%', '%縣%', '%鄉%'],
            'other':         ['%洞%', '%岩%', '%林%', '%原%', '%坡%', '%野%'],
        }
        VALID_CATES = set(CATE_LIKES.keys()) | {'admin_place'}

        # Dynasty filter: if set, only places matching lineage_chronology entries
        chrono_dynasty_join = ""
        chrono_params = []
        if dynasty:
            # Get unique name_zh from lineage_chronology for this dynasty
            chrono_names = conn.execute("""
                SELECT DISTINCT c.title_zh
                FROM lineage_chronology c
                WHERE c.dynasty = ? AND c.title_zh IS NOT NULL AND c.title_zh != ''
            """, (dynasty,)).fetchall()
            chrono_zh_set = set(r['title_zh'] for r in chrono_names)
            # Build filter: only places whose name_zh appears in chrono set
            # Use a subquery for efficiency if set is large
            if not chrono_zh_set:
                return jsonify({"ok": True, "query": q, "dynasty": dynasty, "count": 0, "results": []})
            # We'll filter inline in each query block below instead

        if len(q) >= 2:
            pattern = f'%{q}%'

            # FTS5 nhanh — khớp có dấu / không dấu / gõ dở / ID / Hán.
            # MATCH thử lần lượt: phrase → token AND → prefix AND ("thiếu* lâm* tự*").
            # FTS đã chạy mà không khớp → trả rỗng nhanh (không LIKE full-scan gây "autocomplete ko chạy").
            fts_raw_ids = None
            try:
                ensure_places_search_fts(conn)
                ensure_places_pending_fts(conn)
                fts_candidates = [f'"{q.replace(chr(34), chr(34)+chr(34))}"']
                if re.fullmatch(r'[\w\s]+', q, re.UNICODE):
                    fts_candidates.append(q)
                prefix_terms = []
                for t in re.split(r'\s+', q.strip())[:6]:
                    t = re.sub(r'["*():+\-#@~^&]', '', t)
                    if t:
                        prefix_terms.append(t + '*')
                if prefix_terms:
                    fts_candidates.append(' '.join(prefix_terms))

                fts_raw_ids = []
                for fq in fts_candidates:
                    ids = []
                    for table, col in (("places_search_fts", "dila_id"), ("places_pending_fts", "id")):
                        try:
                            cand = conn.execute(
                                f"SELECT {col} AS vid FROM {table} WHERE {table} MATCH ? LIMIT 100",
                                (fq,)
                            ).fetchall()
                            ids.extend(r['vid'] for r in cand if r['vid'])
                        except Exception:
                            continue
                    if ids:
                        fts_raw_ids = ids
                        break
            except Exception:
                fts_raw_ids = None

            if fts_raw_ids:
                # Dedupe id (dạng ngắn + dạng đầy đủ) trước khi truy vấn kết quả
                in_seen = set()
                in_ids = []
                for raw in fts_raw_ids:
                    for form in (str(raw), ensure_long_id(raw)):
                        if form and form not in in_seen:
                            in_seen.add(form)
                            in_ids.append(form)
                if in_ids:
                    placeholders = ','.join('?' * len(in_ids))
                    try:
                        rows = conn.execute(f"""
                            SELECT p.id,
                                   p.name_zh,
                                   COALESCE(m.name_vi, p.name_vi) AS name_vi,
                                   COALESCE(g.gps_lat, m.gps_lat) AS lat,
                                   COALESCE(g.gps_long, m.gps_long) AS lng,
                                   g.place_type AS type,
                                   COALESCE(g.confidence, m.confidence, 1.0) AS confidence,
                                   d.note_category AS note_category
                            FROM places_pending p
                            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                            LEFT JOIN places g ON g.name_zh = p.name_zh AND p.name_zh != ''
                            LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
                            WHERE p.id IN ({placeholders})
                            ORDER BY
                                CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                                p.id ASC
                            LIMIT ?
                        """, in_ids + [q, pattern, limit]).fetchall()
                    except Exception:
                        rows = []
                    for r in rows:
                        rid = ensure_long_id(r['id'])
                        if rid not in seen:
                            seen.add(rid)
                            results.append({
                                "id": rid, "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                                "lat": r['lat'], "lng": r['lng'],
                                "type": r['type'], "confidence": r['confidence'],
                                "source": "fts",
                                "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh'])
                            })
            if not results:
                # FTS không tìm thấy (index lỗi, hoặc entry mới chưa được index) → LIKE fallback.
                # 1) Search places table (has GPS coordinates)
                try:
                    rows = conn.execute("""
                        SELECT p.id, p.name_zh, p.name_vi, p.gps_lat, p.gps_long,
                               p.place_type, p.confidence, d.note_category
                        FROM places p
                        LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
                        WHERE (p.name_zh LIKE ? OR p.name_vi LIKE ? OR p.id LIKE ?)
                          AND p.gps_lat IS NOT NULL
                        ORDER BY p.confidence DESC
                        LIMIT ?
                    """, (pattern, pattern, pattern, limit)).fetchall()
                    for r in rows:
                        rid = r['id']
                        if rid not in seen:
                            seen.add(rid)
                            results.append({
                                "id": rid, "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                                "lat": r['gps_lat'], "lng": r['gps_long'],
                                "type": r['place_type'], "confidence": r['confidence'],
                                "source": "places",
                                "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh'])
                            })
                except Exception:
                    pass

                # 2) Supplement from namevi_map_places (has full name_vi)
                remaining = limit - len(results)
                if remaining > 0:
                    try:
                        rows = conn.execute("""
                            SELECT n.dila_id, n.name_zh, n.name_vi,
                                   COALESCE(p.gps_lat, n.gps_lat) as lat,
                                   COALESCE(p.gps_long, n.gps_long) as lng,
                                   p.place_type,
                                   COALESCE(p.confidence, n.confidence) as confidence,
                                   d.note_category
                            FROM namevi_map_places n
                            LEFT JOIN places p ON p.name_zh = n.name_zh AND p.name_zh != ''
                            LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(n.dila_id, 3) AS INTEGER))
                            WHERE (n.name_vi LIKE ? OR n.name_zh LIKE ?)
                            GROUP BY n.dila_id
                            ORDER BY confidence DESC
                            LIMIT ?
                        """, (pattern, pattern, remaining)).fetchall()
                        for r in rows:
                            rid = r['dila_id']
                            if rid not in seen:
                                seen.add(rid)
                                results.append({
                                    "id": rid, "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                                    "lat": r['lat'], "lng": r['lng'],
                                    "type": r['place_type'], "confidence": r['confidence'],
                                    "source": "namevi_map",
                                    "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh'])
                                })
                    except Exception:
                        pass
            # else: FTS đã chạy, không khớp → results rỗng, trả về nhanh.
        else:
            # No query: return top places with GPS + name_vi
            temple_likes = []
            temple_params = []
            if scope_temple:
                for pat in temple_patterns:
                    temple_likes.append("p.name_zh LIKE ?")
                    temple_params.append(pat)
                for pat in temple_patterns_vi:
                    temple_likes.append("COALESCE(n.name_vi, p.name_vi) LIKE ?")
                    temple_params.append(pat)
                temple_where = "AND (" + " OR ".join(temple_likes) + ")"
            elif cate and cate in VALID_CATES:
                cate_likes_list = []
                cate_params_list = []
                if cate == 'admin_place':
                    # Exclude all known non-admin categories (filter by name_zh)
                    exclude_pats = []
                    exclude_params = []
                    for pats in CATE_LIKES.values():
                        for p_ in pats:
                            exclude_pats.append("p.name_zh NOT LIKE ?")
                            exclude_params.append(p_)
                    temple_where = "AND (" + " AND ".join(exclude_pats) + ")"
                    temple_params = exclude_params
                else:
                    for p_ in CATE_LIKES[cate]:
                        cate_likes_list.append("p.name_zh LIKE ?")
                        cate_params_list.append(p_)
                    temple_where = "AND (" + " OR ".join(cate_likes_list) + ")"
                    temple_params = cate_params_list
            else:
                # No filter specified: return empty so UI prompts user to choose a category
                temple_where = "AND 1=0"
                temple_params = []
            params = temple_params + bbox_params_list + [limit]
            if offset:
                params.append(offset)
            try:
                sql = f"""
                    SELECT p.id, p.name_zh,
                           COALESCE(n.name_vi, p.name_vi) AS name_vi,
                           p.gps_lat, p.gps_long,
                           p.place_type, p.confidence,
                           d.note_category,
                           p.province
                    FROM places p
                    LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                    LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
                    WHERE p.gps_lat IS NOT NULL
                      {temple_where}
                      {bbox_filter}
                    GROUP BY p.id
                    ORDER BY p.confidence DESC
                    LIMIT ?{ ' OFFSET ?' if offset else '' }
                """
                rows = conn.execute(sql, params).fetchall()
                _prov_cache = {}
                for r in rows:
                    prov_raw = r['province'] or ''
                    if prov_raw not in _prov_cache:
                        _prov_cache[prov_raw] = _translate_admin_text(prov_raw, conn) if prov_raw else ''
                    results.append({
                        "id": r['id'], "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                        "lat": r['gps_lat'], "lng": r['gps_long'],
                        "type": r['place_type'], "confidence": r['confidence'],
                        "source": "places",
                        "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh']),
                        "province_vi": _prov_cache[prov_raw]
                    })
            except Exception:
                pass

        conn.close()

        # Post-filter by dynasty if set
        if dynasty and chrono_zh_set:
            results = [r for r in results if r.get('name_zh') in chrono_zh_set]

        # Sanitize name_vi (replace any remaining CJK with Hán-Việt)
        for r in results:
            if r.get('name_vi'):
                r['name_vi'] = _ensure_vietnamese(r['name_vi'])

        # Re-rank by string similarity khi có query — FTS trả đúng candidates
        # nhưng ORDER BY id ASC có thể đặt kết quả kém hơn lên đầu.
        if q:
            q_n = normalize_text(q)
            def _qscore(r):
                name = (r.get('name_vi') or r.get('name_zh') or '').strip()
                nlo = name.lower()
                qlo = q.lower()
                nn = normalize_text(name)
                if nlo == qlo:      return 100
                if nn == q_n:       return 90
                if nlo.startswith(qlo): return 80
                if nn.startswith(q_n):  return 70
                if qlo in nlo:      return 60
                if q_n in nn:       return 50
                return 10
            results.sort(key=_qscore, reverse=True)

        return jsonify({
            "ok": True, "query": q, "count": len(results), "results": results
        })

    except Exception as e:
        import traceback
        app.logger.error(f"api_places_search error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/places/all')
def api_places_all():
    """Get all places with optional category filter (temple, mountain, cave, all)."""
    try:
        category = request.args.get('category', 'all').strip()
        limit = min(int(request.args.get('limit', 5000)), 10000)
        conn = get_db_connection()
        # Build base query selecting needed fields — note_category from places_dila (places table has no such column)
        query = """
            SELECT p.id, p.name_zh, COALESCE(n.name_vi, p.name_vi) AS name_vi,
                   p.gps_lat, p.gps_long, p.place_type, d.note_category
            FROM places p
            LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
            LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
            WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
        """
        params = []
        if category != 'all':
            # Map to internal categories based on note_category patterns (from joined places_dila)
            if category == 'temple':
                query += " AND (d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%')"
            elif category == 'mountain':
                query += " AND d.note_category LIKE '%山峰%'"
            elif category == 'cave':
                query += " AND d.note_category LIKE '%石窟%'"
        query += " GROUP BY p.id ORDER BY p.confidence DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        results = []
        for r in rows:
            vi = r['name_vi'] or r['name_zh'] or ''
            vi = _ensure_vietnamese(vi)
            results.append({
                'id': r['id'],
                'name_zh': r['name_zh'],
                'name_vi': vi,
                'lat': r['gps_lat'],
                'lng': r['gps_long'],
                'category': r['note_category'],
                'icon_type': _note_category_to_icon_type(r['note_category'], r['name_zh'])
            })
        return jsonify({"ok": True, "count": len(results), "places": results})
    except Exception as e:
        app.logger.error(f"api_places_all error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/places/unified')
def api_places_unified():
    """
    GET /daoanh/api/places/unified?dynasty=...&limit=300
    Returns ALL GPS locations from places + lineage_chronology, deduplicated.
    One entry per GPS coordinate for single-marker rendering.
    """
    try:
        dynasty = request.args.get('dynasty', '').strip()
        limit = min(int(request.args.get('limit', 300)), 1000)
        conn = get_db_connection()

        # Part 1: places with GPS (+ name_vi from namevi_map_places)
        if dynasty:
            chrono_names = conn.execute("""
                SELECT DISTINCT c.title_zh
                FROM lineage_chronology c
                WHERE c.dynasty = ? AND c.title_zh IS NOT NULL AND c.title_zh != ''
            """, (dynasty,)).fetchall()
            chrono_zh_set = set(r['title_zh'] for r in chrono_names)
            if not chrono_zh_set:
                conn.close()
                return jsonify({"ok": True, "dynasty": dynasty, "count": 0, "results": []})
            all_places = conn.execute("""
                SELECT p.id, p.name_zh,
                       COALESCE(n.name_vi, p.name_vi) AS name_vi,
                       p.gps_lat, p.gps_long,
                       p.confidence, p.source_origin
                FROM places p
                LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
                GROUP BY p.id
                ORDER BY p.confidence DESC
                LIMIT 2000
            """).fetchall()
            place_rows = [p for p in all_places if p['name_zh'] in chrono_zh_set]
        else:
            place_rows = conn.execute("""
                SELECT p.id, p.name_zh,
                       COALESCE(n.name_vi, p.name_vi) AS name_vi,
                       p.gps_lat, p.gps_long,
                       p.confidence, p.source_origin
                FROM places p
                LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
                GROUP BY p.id
                ORDER BY p.confidence DESC
                LIMIT ?
            """, (limit,)).fetchall()

        # Part 2: chronology events with GPS (via places_dila)
        chrono_rows = conn.execute("""
            SELECT lc.id, lc.title_zh,
                   COALESCE(lc.title, lc.title_zh) AS name_vi,
                   pd.geo_lat, pd.geo_long,
                   lc.dynasty
            FROM lineage_chronology lc
            JOIN places_dila pd ON pd.name_zh = lc.title_zh
            WHERE pd.geo_lat IS NOT NULL AND pd.geo_long IS NOT NULL
              AND (? = '' OR lc.dynasty = ?)
            GROUP BY lc.id
        """, (dynasty, dynasty)).fetchall()
        conn.close()

        # Merge by GPS proximity (rounded to 3 decimals ≈ 100m)
        merged = {}
        for p in place_rows:
            key = (round(p['gps_lat'], 3), round(p['gps_long'], 3))
            merged[key] = {
                'id': p['id'],
                'name_vi': _ensure_vietnamese(p['name_vi'] or p['name_zh'] or ''),
                'name_zh': p['name_zh'] or '',
                'lat': p['gps_lat'],
                'lng': p['gps_long'],
                'confidence': p['confidence'] or 0.5,
                'source': 'place',
                'dynasty': '',
                'has_chronology': False,
            }

        for c in chrono_rows:
            key = (round(c['geo_lat'], 3), round(c['geo_long'], 3))
            if key in merged:
                merged[key]['has_chronology'] = True
                if c['dynasty'] and not merged[key]['dynasty']:
                    merged[key]['dynasty'] = c['dynasty']
            else:
                merged[key] = {
                    'id': f"c_{c['id']}",
                    'name_vi': _ensure_vietnamese(c['name_vi'] or c['title_zh'] or ''),
                    'name_zh': c['title_zh'] or '',
                    'lat': c['geo_lat'],
                    'lng': c['geo_long'],
                    'confidence': 0.5,
                    'source': 'chronology',
                    'dynasty': c['dynasty'] or '',
                    'has_chronology': True,
                }

        results = list(merged.values())
        if not dynasty:
            results = results[:limit]

        return jsonify({
            "ok": True,
            "count": len(results),
            "has_chronology": sum(1 for r in results if r['has_chronology']),
            "results": results
        })

    except Exception as e:
        import traceback
        app.logger.error(f"api_places_unified error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/places/<place_id>')
def api_places_detail(place_id):
    """
    GET /daoanh/api/places/<id>
    Returns full detail from both places + namevi_map_places.
    Tries exact ID match in both tables, then falls back to name_zh match.
    """
    try:
        conn = get_db_connection()
        detail = None

        # 1) Try places table by ID (has GPS)
        row = conn.execute("""
            SELECT * FROM places WHERE id = ?
        """, (place_id,)).fetchone()

        if row:
            detail = dict(row)
            detail['source'] = 'places'
            # Supplement dila_id, name_vi, note_vi from namevi_map_places
            if detail.get('name_zh'):
                nv = conn.execute("""
                    SELECT name_vi, note_vi, dila_id, confidence, source
                    FROM namevi_map_places
                    WHERE name_zh = ? AND (name_vi != '' OR dila_id IS NOT NULL)
                    ORDER BY (vn_name_status = 'reviewed') DESC, (source = 'manual') DESC, confidence DESC
                    LIMIT 1
                """, (detail['name_zh'],)).fetchone()
                if nv:
                    if not detail.get('name_vi') and nv['name_vi']:
                        detail['name_vi'] = nv['name_vi']
                        # T360 — name_vi thực ra đến từ namevi_map_places, không phải
                        # places.source_origin/confidence → giữ lại cột nguồn thật.
                        detail['_namevi_source'] = nv['source']
                        detail['_namevi_confidence'] = nv['confidence']
                    if not detail.get('note_vi') and nv['note_vi']:
                        detail['note_vi'] = nv['note_vi']
                    if not detail.get('dila_id') and nv['dila_id']:
                        detail['dila_id'] = nv['dila_id']
        else:
            # 2) Try namevi_map_places by dila_id (has name_vi)
            row = conn.execute("""
                SELECT * FROM namevi_map_places WHERE dila_id = ?
            """, (place_id,)).fetchone()

            if row:
                detail = dict(row)
                # T360 — giữ lại cột source/confidence THẬT của namevi_map_places
                # trước khi gắn nhãn 'namevi_map' đánh dấu bảng gốc.
                detail['_namevi_source'] = detail.get('source')
                detail['_namevi_confidence'] = detail.get('confidence')
                detail['source'] = 'namevi_map'
                # Bổ sung GPS/province/country từ places (khớp name_zh) khi THIẾU
                # — không chỉ khi GPS thiếu: namevi_map có thể có GPS nhưng rỗng
                # province/country (VD 少林寺 PL000000023255 → province rỗng).
                if detail.get('name_zh') and (not detail.get('province') or not detail.get('country') or not detail.get('gps_lat')):
                    p = conn.execute("""
                        SELECT gps_lat, gps_long, province, country, source_origin
                        FROM places WHERE name_zh = ?
                        ORDER BY gps_lat IS NOT NULL DESC, province IS NOT NULL DESC
                        LIMIT 1
                    """, (detail['name_zh'],)).fetchone()
                    if p:
                        if not detail.get('gps_lat'):
                            detail['gps_lat'] = p['gps_lat']
                        if not detail.get('gps_long'):
                            detail['gps_long'] = p['gps_long']
                        if not detail.get('province'):
                            detail['province'] = p['province']
                        if not detail.get('country'):
                            detail['country'] = p['country']
                        if not detail.get('source_origin'):
                            detail['source_origin'] = p['source_origin']

        # Supplement with cbeta_catalog_vn (text_info + license)
        # Uses: (1) exact LIKE, (2) fuzzy match table, (3) VI name search
        name_zh = detail.get('name_zh', '') if detail else ''
        name_vi = detail.get('name_vi', '') if detail else ''
        # text_info: only attach CBETA catalog data when the match is about a WORK
        # whose title IS the place name (exact prefix), not just contains it.
        # This prevents "少林無孔笛" from incorrectly matching the place "少林寺".
        if detail and name_zh:
            cat = None
            fuzzy = None
            # Exact title match only (title_zh starts with or equals name_zh)
            exact = conn.execute("""
                SELECT title_vi, title_zh, dynasty_vi, translator_vi,
                       q_number, page, sh_number, juans,
                       source_name, source_full_title,
                       license_name, license_url, source_note
                FROM cbeta_catalog_vn
                WHERE title_zh = ? OR title_zh LIKE ?
                LIMIT 1
            """, (name_zh, f'{name_zh} %')).fetchone()
            if exact:
                cat = exact
            if not cat:
                # Fuzzy match — only accept high-confidence (score >= 90)
                fuzzy = conn.execute("""
                    SELECT v.title_vi, v.title_zh, v.dynasty_vi, v.translator_vi,
                           v.q_number, v.page, v.sh_number, v.juans,
                           v.source_name, v.source_full_title,
                           v.license_name, v.license_url, v.source_note
                    FROM cbeta_catalog_place_fuzzy f
                    JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                    WHERE f.place_id = ? AND f.score >= 90
                    ORDER BY f.score DESC, f.rank ASC
                    LIMIT 1
                """, (place_id,)).fetchone()
                if fuzzy:
                    # Sanity check: title must start with the place name
                    ft = dict(fuzzy).get('title_zh', '')
                    if ft.startswith(name_zh):
                        cat = fuzzy
                    else:
                        fuzzy = None
            if cat:
                detail['text_info'] = dict(cat)
                match_type = 'exact' if exact else ('fuzzy' if fuzzy else 'like')
                detail['text_info_match'] = match_type

        conn.close()

        if not detail:
            return jsonify({"ok": False, "error": "Place not found"}), 404

        # Sanitize name_vi, note_vi and province — never leave raw CJK on the page.
        # If name_vi is missing (e.g. dynasty/historical entities like 遼, 清朝),
        # synthesize it from name_zh via lexicon-first + flagged Hán-Việt fallback.
        if detail.get('name_vi'):
            detail['name_vi'] = _ensure_vietnamese(detail['name_vi'])
        elif detail.get('name_zh'):
            _lex_conn = get_db_connection()
            try:
                detail['name_vi'] = _translate_zh_term(detail['name_zh'], _lex_conn)
            finally:
                _lex_conn.close()
        # Known dynasty/kingdom names always display with a "Nhà " prefix,
        # regardless of whether name_vi came from admin-curated data
        # (namevi_map_places), the DB, or the fallback above.
        if detail.get('name_zh') in DYNASTY_NAMES and detail.get('name_vi'):
            _nv = detail['name_vi']
            if not _nv.startswith('Nhà ') and not _nv.startswith('Triều '):
                _lex_conn = get_db_connection()
                try:
                    detail['name_vi'] = _translate_dynasty_name(detail['name_zh'], _lex_conn) or f'Nhà {_nv}'
                finally:
                    _lex_conn.close()
        if detail.get('note_vi'):
            detail['note_vi'] = _ensure_vietnamese(detail['note_vi'])

        # Vị trí (3 Lớp RAG): dữ liệu thô + địa chỉ cấu trúc giống placevn.html
        # district_raw/geo hiển thị nguyên trạng; district_vi/country_vi là bản
        # đã chuẩn hoá (rule-based parse_dila_district, không tốn AI).
        raw_district = detail.get('province') or detail.get('district_raw') or detail.get('address') or ''
        raw_country = detail.get('country') or ''
        detail['district_raw'] = raw_district
        parsed = parse_dila_district(raw_district) if raw_district else {}
        # Ưu tiên địa chỉ rule-based sạch; fallback district_vi/country_vi admin (namevi_map_places)
        detail['district_vi'] = (parsed.get('district_vi') or parsed.get('formatted') or '') or detail.get('district_vi') or ''
        country_vi = (parsed.get('country_vi') or '') or detail.get('country_vi') or raw_country or ''
        if country_vi in ('中國', '中国', 'China'):
            country_vi = 'Trung Quốc'
        elif country_vi in ('阿富汗', 'افغانستان'):
            country_vi = 'Afghanistan'
        elif country_vi in ('印度', 'भारत'):
            country_vi = 'Ấn Độ'
        detail['country_vi'] = country_vi

        # Supplement from places_dila: note (raw description), listbibl (CBETA refs),
        # note_category. Lookup priority: dila_id (exact) → name_zh fallback.
        try:
            _dconn = get_db_connection()
            try:
                _dila_row = None
                _dila_id = detail.get('dila_id', '')
                if _dila_id:
                    _dila_row = _dconn.execute(
                        "SELECT note, listbibl, note_category FROM places_dila WHERE id = ? LIMIT 1",
                        (_dila_id,)
                    ).fetchone()
                if not _dila_row and detail.get('name_zh'):
                    _dila_row = _dconn.execute(
                        "SELECT note, listbibl, note_category FROM places_dila WHERE (name = ? OR name_zh = ?) AND note IS NOT NULL AND note != '' LIMIT 1",
                        (detail['name_zh'], detail['name_zh'])
                    ).fetchone()
            finally:
                _dconn.close()
            if _dila_row:
                if not (detail.get('note_vi') or '').strip() and _dila_row['note']:
                    raw = re.sub(r'<[^>]+>', ' ', _dila_row['note'])
                    raw = re.sub(r'\s+', ' ', raw).strip()
                    detail['dila_note'] = raw
                if _dila_row['listbibl']:
                    detail['dila_listbibl'] = _dila_row['listbibl']
                if _dila_row['note_category']:
                    detail['dila_category'] = _dila_row['note_category']
        except Exception:
            pass

        # T112 D-Feedback: tự ghi gap khi địa danh thiếu nội dung mô tả (note_vi + dila_note đều trống)
        if detail and not (detail.get('note_vi') or '').strip() and not detail.get('dila_note') \
                and not (detail.get('description_vi') or '').strip():
            _t112_record_gap('place', place_id, detail.get('name_zh') or detail.get('name') or '',
                             'thieu_noidung',
                             "Địa danh thiếu mô tả nội dung tiếng Việt/DILA trực tiếp (note_vi, dila_note)",
                             source_hint='places_dila; namevi_map_places')

        # Lexicon verification: "Đã Duyệt" khi tên Việt xuất hiện trong 25 bộ từ điển Phật học
        _name_for_lex = (detail.get('name_vi') or '').strip()
        if _name_for_lex:
            try:
                _lconn = get_db_connection()
                _lex = _lconn.execute(
                    "SELECT source FROM lexicon WHERE term = ? LIMIT 5",
                    (_name_for_lex,)
                ).fetchall()
                if not _lex:
                    # Thử dạng thay thế: "Chùa X" ↔ "X Tự"
                    _alt = _name_for_lex
                    if _alt.endswith(' Tự'):
                        _alt = 'Chùa ' + _alt[:-3].strip()
                    elif _alt.startswith('Chùa '):
                        _alt = _alt[5:].strip() + ' Tự'
                    if _alt != _name_for_lex:
                        _lex = _lconn.execute(
                            "SELECT source FROM lexicon WHERE term = ? LIMIT 5",
                            (_alt,)
                        ).fetchall()
                _lconn.close()
                if _lex:
                    detail['vn_name_status'] = 'reviewed'
                    detail['lexicon_sources'] = [r['source'] for r in _lex]
            except Exception:
                pass

# T29: bdrc_id removed — BDRC integration skipped per admin decision.
        # Previously: real BDRC IDs require P2477 SPARQL from Wikidata; all 148 rows had bdrc_id = NULL.

        # Parallel structured founding data from Wikidata + DILA rawtext
        # Source priority: Wikidata P571 (place_timeline_events) > DILA note fallback
        try:
            # 1. Wikidata P571 founded date from place_timeline_events
            founding = conn.execute(
                "SELECT year, source, source_ref "
                "FROM place_timeline_events "
                "WHERE entity_id = ? AND event_type = 'founding' "
                "ORDER BY confidence DESC LIMIT 1",
                (place_id,)
            ).fetchone()
            
            if founding:
                detail['founding_year'] = founding[0]
                detail['founding_source'] = founding[1] or 'wikidata'
                detail['founding_source_ref'] = founding[2] or ''
            else:
                detail['founding_year'] = None
                detail['founding_source'] = None
                detail['founding_source_ref'] = None
        except Exception:
            detail['founding_year'] = None
            detail['founding_source'] = None
            detail['founding_source_ref'] = None

        # 2. DILA rawtext (始建於...) as fallback when Wikidata missing
        try:
            _dconn = get_db_connection()
            try:
                _dila_row = None
                _dila_id = detail.get('dila_id', '')
                if _dila_id:
                    _dila_row = _dconn.execute(
                        "SELECT note FROM places_dila WHERE id = ? LIMIT 1",
                        (_dila_id,)
                    ).fetchone()
            finally:
                _dconn.close()
            
            if _dila_row and _dila_row[0]:
                _raw = re.sub(r'<[^>]+>', ' ', _dila_row[0])
                _raw = re.sub(r'\s+', ' ', _raw).strip()
                # Extract founding year (e.g., "始建於495年")
                _m = re.search(r'始建於\s*(\d{3,4})', _raw)
                if _m:
                    detail['dila_founding_year'] = int(_m.group(1))
                    detail['dila_rawtext'] = _raw
                else:
                    detail['dila_founding_year'] = None
                    detail['dila_rawtext'] = _raw
            else:
                detail['dila_founding_year'] = None
                detail['dila_rawtext'] = ''
        except Exception:
            detail['dila_founding_year'] = None
            detail['dila_rawtext'] = ''

        # 3. Wikidata QID from geo_cross_ref (already populated: 148/148)
        # Already available in detail from earlier geo_cross_ref lookup

        # 4. DILA ID (always present for places in this API)
        detail['dila_id'] = detail.get('dila_id')

        if detail.get('province'):
            detail['province'] = _translate_admin_text(detail['province'])

        # T360 — badge nguồn/độ tin cậy cho name_vi (đọc từ cột thật trong DB, xem
        # _t360_resolve_place_name_vi_source). Bọc try/except theo CLAUDE.md.
        try:
            _label, _conf, _color = _t360_resolve_place_name_vi_source(detail)
        except Exception:
            _label, _conf, _color = None, None, None
        detail['source_of_name_vi'] = _label
        detail['confidence_name_vi'] = _conf
        detail['badge_color_name_vi'] = _color
        # Xoá field nội bộ dùng để truyền dữ liệu giữa các bước — không thuộc contract API.
        detail.pop('_namevi_source', None)
        detail.pop('_namevi_confidence', None)

        return jsonify({"ok": True, "data": detail})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




# ─── PLACES × CHRONOLOGY CROSS-SEARCH ───────────────────────

@app.route('/daoanh/api/places/<place_id>/chronology')
def api_places_chronology(place_id):
    """
    GET /daoanh/api/places/<id>/chronology?limit=20
    Finds lineage_chronology entries matching this place's name_zh.
    Returns cross-linked people/works associated with this location.
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        conn = get_db_connection()

        # Get place's name_zh from either table
        name_zh = None
        row = conn.execute("SELECT name_zh FROM places WHERE id = ?", (place_id,)).fetchone()
        if row:
            name_zh = row['name_zh']
        if not name_zh:
            row = conn.execute("SELECT name_zh FROM namevi_map_places WHERE dila_id = ?", (place_id,)).fetchone()
            if row:
                name_zh = row['name_zh']
        if not name_zh:
            row = conn.execute("SELECT name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
            if row:
                name_zh = row['name_zh']

        if not name_zh:
            conn.close()
            return jsonify({"ok": False, "error": "No name_zh for this place"}), 404

        # Query lineage_chronology matching name_zh
        chrono_conn = get_chronology_conn()
        rows = chrono_conn.execute("""
            SELECT * FROM lineage_chronology
            WHERE title_zh = ?
            ORDER BY century_start NULLS LAST
            LIMIT ?
        """, (name_zh, limit)).fetchall()
        chrono_conn.close()
        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "name_zh": name_zh,
            "count": len(rows),
            "results": [dict(r) for r in rows]
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/places/<place_id>/graph')
def api_places_graph(place_id):
    """GET /daoanh/api/places/<id>/graph — Unified knowledge graph (T16/T17 realization).

    Nodes/edges built ONLY from source-traceable authority data:
    - alt_names: places_dila.raw_xml placeName[type="alternative"] (DILA-curated, real attribute)
    - related texts: places_dila.listbibl CBETA sigla -> JOIN cbeta_catalog_vn (Nguyễn Minh Tiến,
      CC BY-SA 4.0) — same T-series JOIN pattern used in api_places_cbeta(), not fuzzy matching.
    - nearby places: same-province structural lookup (not a content/authority claim).

    Removed 2026-08-19: `persons_mentioned` (regex-scraped from free `note` text against a
    hand-picked name list — no scholarly-reviewed place<->person link exists anywhere in the
    schema; `places`/`places_dila`/`people` all lack a person<->place column) and `text_links`
    via `cbeta_catalog_place_fuzzy` (RapidFuzz score match). Both are the same category of
    violation as the passage_entity/fuzzy blocks already removed elsewhere per CLAUDE.md's
    content-integrity rule — an auto-derived guess standing in for a real authority source.

    See GET /daoanh/api/monk/<dila_id>/graph for the person-entity counterpart (Marcus SNA
    teacher/student lineage, each edge carries a real CBETA citation `ref`).
    """
    import re as _re
    try:
        conn = get_db_connection()
        place_row = conn.execute("SELECT * FROM places WHERE id = ?", (place_id,)).fetchone()
        dila_id, name_zh = _resolve_dila_id(conn, place_id)
        if not name_zh and place_row:
            name_zh = place_row['name_zh'] or ''
        _raw_name_vi = (place_row['name_vi'] if place_row else None) or None
        # Enrich center: try namevi_map_places by dila_id first (gives ZQ name_vi + intended name_zh)
        if not _raw_name_vi and dila_id:
            _vi_row = conn.execute(
                "SELECT name_vi, name_zh FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
                (dila_id,)
            ).fetchone()
            if _vi_row and _vi_row['name_vi']:
                _raw_name_vi = _vi_row['name_vi']
                # When places table has no row, prefer ZQ's name_zh over DILA canonical
                if not place_row and _vi_row['name_zh']:
                    name_zh = _vi_row['name_zh']
        # Fall back to name_zh lookup if still missing
        if not _raw_name_vi and name_zh:
            _vi_row = conn.execute(
                "SELECT name_vi FROM namevi_map_places WHERE name_zh = ? LIMIT 1", (name_zh,)
            ).fetchone()
            if _vi_row and _vi_row['name_vi']:
                _raw_name_vi = _vi_row['name_vi']
        label_vi = _raw_name_vi or name_zh

        alt_names = []
        related_sh = []
        if dila_id:
            dila_row = conn.execute("SELECT raw_xml, listbibl, district FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
            if dila_row:
                raw_xml = dila_row['raw_xml'] or ''
                raw_alts = _re.findall(r'placeName type="alternative"[^>]*>([^<]+)<', raw_xml)
                # FIX 1: enrich alt_names with Việt readings from namevi_map_places
                alt_names = []
                for zh_alt in raw_alts:
                    vi_row = conn.execute(
                        "SELECT name_vi FROM namevi_map_places WHERE name_zh = ? LIMIT 1",
                        (zh_alt,)
                    ).fetchone()
                    alt_names.append({
                        'zh': zh_alt,
                        'vi': vi_row['name_vi'] if vi_row and vi_row['name_vi'] else None
                    })
                listbibl = dila_row['listbibl'] or ''
                seen_sh = set()
                for m in _re.finditer(r'CBETA\s+T\d+n(\d+)_', listbibl):
                    sh = m.group(1)
                    if sh not in seen_sh:
                        seen_sh.add(sh)
                        related_sh.append(sh)

        # Map Cao Tang Truyen collection -> sh_number for text node hub
        _CTT_SH = {'唐高僧傳': '2060', '宋高僧傳': '2061', '明高僧傳': '2062'}

        nodes, edges = [], []
        text_node_ids = set()   # track which text nodes already exist

        for sh in related_sh:
            cat = conn.execute(
                "SELECT title_zh, title_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ? LIMIT 1",
                (sh,)
            ).fetchone()
            if cat:
                node_id = 'text:' + sh
                nodes.append({"id": node_id, "label": cat['title_vi'] or cat['title_zh'] or sh,
                              "label_zh": cat['title_zh'],
                              "group": "text", "navigable": False})
                edges.append({"from": place_id, "to": node_id, "label": "kinh điển liên quan",
                              "evidence_type": "with_evidence"})
                text_node_ids.add(node_id)

        _nearby_province = (place_row['province'] if place_row and place_row['province'] else None)
        if not _nearby_province and dila_id:
            # Fallback: place not in places table — use places_dila.district (same format as province)
            _nearby_province = dila_row['district'] if dila_row and dila_row['district'] else None
        if _nearby_province:
            nearby_rows = conn.execute(
                "SELECT id, name_zh, name_vi FROM places WHERE province = ? AND id != ?",
                (_nearby_province, place_id)
            ).fetchall()
            for r in nearby_rows:
                nodes.append({"id": r['id'], "label": r['name_vi'] or r['name_zh'], "label_zh": r['name_zh'],
                              "group": "place", "navigable": True})
                edges.append({"from": place_id, "to": r['id'], "label": "lân cận",
                              "evidence_type": "co_mention"})

        # T16 — Person nodes qua text-hub: place → Cao Tang Truyen → person
        # Edge structure: place→text_node (collection hub) →person (temporal layering)
        # nexus_events may not exist on all deployments — degrade gracefully
        if dila_id:
            try:
                nexus_rows = conn.execute("""
                    SELECT ne.person_dila_id, ne.event_label, ne.source_book, ne.confidence,
                           p.name_vi, p.name_zh
                    FROM nexus_events ne
                    LEFT JOIN people p ON p.id = ne.person_dila_id
                    WHERE ne.place_dila_id = ? AND ne.person_dila_id IS NOT NULL
                    ORDER BY ne.confidence DESC
                """, (dila_id,)).fetchall()
            except Exception:
                nexus_rows = []
            seen_pids = set()
            for r in nexus_rows:
                pid = r[0]
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)
                src_book = r[2]
                sh = _CTT_SH.get(src_book)
                hub_id = ('text:' + sh) if sh else None

                # Create hub text node if not already from listbibl
                if hub_id and hub_id not in text_node_ids:
                    cat = conn.execute(
                        "SELECT title_zh, title_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ? LIMIT 1",
                        (sh,)
                    ).fetchone()
                    if cat:
                        nodes.append({"id": hub_id, "label": cat['title_vi'] or cat['title_zh'] or sh,
                                      "label_zh": cat['title_zh'], "group": "text", "navigable": False})
                        edges.append({"from": place_id, "to": hub_id, "label": "kinh điển liên quan",
                                      "evidence_type": "with_evidence"})
                        text_node_ids.add(hub_id)
                    else:
                        hub_id = None  # catalog miss — fall back to direct edge

                dn = _t86_resolve_display_name(conn, pid)
                pname = dn['primary']
                node_id = 'person:' + pid
                nodes.append({
                    "id": node_id, "label": pname,
                    "label_zh": dn['authority_secondary'] or dn['secondary'] or r[5] or r[1],
                    "group": "person", "navigable": True, "dila_id": pid,
                    "source": "nexus_tei",
                    "title": f"Nguồn: {src_book} (confidence {r[3]})"
                })
                from_id = hub_id if hub_id else place_id
                conf = r[3]
                ev_type = "with_evidence" if conf >= 0.7 else "partial"
                p_reason = None if conf >= 0.7 else f"Confidence thấp ({conf:.2f}): {src_book}"
                edges.append({"from": from_id, "to": node_id,
                              "label": "", "has_ref": True, "ref": src_book,
                              "evidence_type": ev_type, "partial_reason": p_reason})

        # T101 BUG-004: curated place_person_link — scholarly-reviewed links (Bồ Đề Đạt Ma, Huệ Khả…)
        # Ưu tiên hơn nexus_events vì có note + source_url rõ ràng. Dedupe qua seen_pids.
        if dila_id:
            try:
                ppl_rows = conn.execute("""
                    SELECT l.person_id, l.relation_type, l.source_name, l.note,
                           p.name_vi, p.name_zh
                    FROM place_person_link l
                    LEFT JOIN people p ON p.id = l.person_id
                    WHERE l.place_id = ?
                """, (dila_id,)).fetchall()
            except Exception:
                ppl_rows = []
            for r in ppl_rows:
                pid = r[0]
                if not pid or pid in seen_pids:
                    continue
                seen_pids.add(pid)
                node_id = 'person:' + pid
                dn = _t86_resolve_display_name(conn, pid)
                pname = dn['primary']
                title_str = (r[2] or '') + (': ' + r[3] if r[3] else '')
                nodes.append({
                    "id": node_id, "label": pname,
                    "label_zh": dn['authority_secondary'] or dn['secondary'] or r[5] or '',
                    "group": "person", "navigable": True, "dila_id": pid,
                    "source": "curated",
                    "title": title_str
                })
                edges.append({"from": place_id, "to": node_id,
                              "label": r[1] or '', "has_ref": True,
                              "ref": r[2] or '', "evidence_type": "with_evidence"})

        conn.close()
        return jsonify({
            "ok": True, "entity_type": "place", "place_id": place_id,
            "center": {"id": place_id, "label": label_vi, "label_zh": name_zh, "label_vi": _raw_name_vi},
            "alt_names": alt_names,
            "nodes": nodes, "edges": edges
        })
    except Exception as e:
        app.logger.error(f"api_places_graph error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/places/<place_id>/persons')
def api_places_persons(place_id):
    """GET /daoanh/api/places/<id>/persons — T22/T28 (Nhân Vật tab).

    Three additive sources, all cited:
    1. `persons` — curated place_person_link rows (DILA person_id, clickable into Truyền Thừa).
    2. `wikidata_persons` — live Wikidata P112 ("founded by") lookup.
    3. `bio_persons` — auto-detected from people.bio text search using place name variants
       extracted from places_dila.raw_xml. Source = "DILA Tiểu Sử" (biographical authority).
       Confidence varies: "僧人/住持" context = high; passing mentions = lower.
    """
    conn = get_db_connection()
    try:
        _ensure_place_person_link_table(conn)
        _ensure_geo_cross_ref_table(conn)

        rows = conn.execute("""
            SELECT l.person_id, l.relation_type, l.source_name, l.source_url, l.note,
                   p.name_zh, p.name_vi, p.dynasty,
                   COALESCE(
                       (SELECT tc.translated_text FROM translation_cache tc
                        WHERE tc.entity_id = l.person_id AND tc.source_type = 'person_bio'
                        AND tc.status != 'invalidated'
                        ORDER BY tc.id DESC LIMIT 1),
                       p.bio_vi
                   ) AS bio_vi
            FROM place_person_link l JOIN people p ON p.id = l.person_id
            WHERE l.place_id = ?
            ORDER BY l.created_at ASC
        """, (place_id,)).fetchall()
        persons = []
        for r in rows:
            has_marcus = conn.execute(
                "SELECT 1 FROM marcus_people_link WHERE person_id = ?", (r['person_id'],)
            ).fetchone() is not None
            marcus_label = conn.execute(
                "SELECT label FROM marcus_reference WHERE node_id = ?", (r['person_id'],)
            ).fetchone()
            persons.append({
                "id": r['person_id'], "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                "marcus_label": marcus_label['label'] if marcus_label else None,
                "dynasty": r['dynasty'], "relation_type": r['relation_type'],
                "source_name": r['source_name'], "source_url": r['source_url'], "note": r['note'],
                "bio_vi": r['bio_vi'] or None,
                "has_lineage": has_marcus
            })

        wikidata_persons = []
        dila_id, _ = _resolve_dila_id(conn, place_id)
        xref = conn.execute(
            "SELECT wikidata_qid, bdrc_id FROM geo_cross_ref WHERE dila_id = ?", (dila_id or place_id,)
        ).fetchone()
        if xref and xref['wikidata_qid']:
            qid = xref['wikidata_qid']
            for f in _fetch_wikidata_founders(qid):
                wikidata_persons.append({
                    "wikidata_qid": f['wikidata_qid'], "label": f['label'], "label_zh": f.get('label_zh'),
                    "relation_type": "founded by (Wikidata P112)",
                    "source_name": f"Wikidata {qid}",
                    "source_url": f"https://www.wikidata.org/wiki/{qid}",
                })
        # ── Source 3: bio text search from DILA Person Authority ────────────────
        # Uses pre-computed cache (T43) if available; falls back to real-time LIKE.
        bio_persons = []
        try:
            target_pid = dila_id or place_id
            linked_ids = {p['id'] for p in persons}
            # Try cache first (T43 pre-compute)
            cache_rows = conn.execute("""
                SELECT ppbc.person_id, ppbc.matched_variant, ppbc.is_direct,
                       ppbc.relation_hint, ppbc.bio_snippet, ppbc.confidence,
                       p.name_zh, p.name_vi, p.dynasty,
                       COALESCE(
                           (SELECT tc.translated_text FROM translation_cache tc
                            WHERE tc.entity_id = ppbc.person_id AND tc.source_type = 'person_bio'
                            AND tc.status != 'invalidated'
                            ORDER BY tc.id DESC LIMIT 1),
                           p.bio_vi
                       ) AS bio_vi
                FROM place_person_bio_cache ppbc
                JOIN people p ON p.id = ppbc.person_id
                WHERE ppbc.place_id = ?
                ORDER BY ppbc.is_direct DESC, p.dynasty
                LIMIT 200
            """, (target_pid,)).fetchall()

            if cache_rows:
                for cr in cache_rows:
                    if cr['person_id'] in linked_ids:
                        continue
                    has_marcus = conn.execute(
                        "SELECT 1 FROM marcus_people_link WHERE person_id=?", (cr['person_id'],)
                    ).fetchone() is not None
                    marcus_label_row = conn.execute(
                        "SELECT label FROM marcus_reference WHERE node_id=?", (cr['person_id'],)
                    ).fetchone()
                    mv = cr['matched_variant'] or ''
                    is_direct = bool(cr['is_direct'])
                    bio_persons.append({
                        "id": cr['person_id'],
                        "name_zh": cr['name_zh'],
                        "name_vi": cr['name_vi'],
                        "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                        "dynasty": cr['dynasty'],
                        "relation_type": "住持/僧人 @ " + mv if is_direct else "đề cập @ " + mv,
                        "source_name": "DILA Tiểu Sử (tự động)",
                        "source_url": f"https://authority.dila.edu.tw/person/?val={cr['person_id']}",
                        "note": cr['bio_snippet'] or '',
                        "bio_vi": cr['bio_vi'] or None,
                        "has_lineage": has_marcus,
                        "is_direct": is_direct,
                    })
            else:
                # Fallback: real-time LIKE (for places not yet in cache)
                place_row = conn.execute(
                    "SELECT raw_xml, name_zh FROM places_dila WHERE id=?", (target_pid,)
                ).fetchone()
                if place_row and place_row['raw_xml']:
                    import re as _re
                    name_variants = _re.findall(
                        r'<[^:]*:?placeName[^>]*>([^<]{1,40})</[^:]*:?placeName>',
                        place_row['raw_xml']
                    )
                    if place_row['name_zh']:
                        name_variants.append(place_row['name_zh'])
                    seen_v = set()
                    uniq_variants = []
                    for v in name_variants:
                        v = v.strip()
                        if v and len(v) >= 2 and v not in seen_v:
                            seen_v.add(v)
                            uniq_variants.append(v)
                    if uniq_variants:
                        uniq_variants.sort(key=len, reverse=True)
                        like_clauses = ' OR '.join(['bio LIKE ?'] * len(uniq_variants))
                        like_params = [f'%{v}%' for v in uniq_variants]
                        bio_rows = conn.execute(
                            f"SELECT id, name_zh, name_vi, dynasty, bio, bio_vi FROM people "
                            f"WHERE bio IS NOT NULL AND ({like_clauses}) LIMIT 200",
                            like_params
                        ).fetchall()
                        direct_keywords = ['僧人', '住持', '方丈', '上座', '寺主', '書記',
                                           '首座', '出家', '居', '嗣法', '中興', '開山']
                        for br in bio_rows:
                            if br['id'] in linked_ids:
                                continue
                            bio_text = br['bio'] or ''
                            snippet = ''
                            matched_variant = ''
                            for v in uniq_variants:
                                idx = bio_text.find(v)
                                if idx >= 0:
                                    matched_variant = v
                                    snippet = bio_text[max(0, idx-20):idx+len(v)+60].strip()
                                    break
                            ctx = bio_text[max(0, bio_text.find(matched_variant)-60):
                                           bio_text.find(matched_variant)+80] if matched_variant else ''
                            is_direct = any(kw in ctx for kw in direct_keywords)
                            has_marcus = conn.execute(
                                "SELECT 1 FROM marcus_people_link WHERE person_id=?", (br['id'],)
                            ).fetchone() is not None
                            marcus_label_row = conn.execute(
                                "SELECT label FROM marcus_reference WHERE node_id=?", (br['id'],)
                            ).fetchone()
                            bio_persons.append({
                                "id": br['id'],
                                "name_zh": br['name_zh'],
                                "name_vi": br['name_vi'],
                                "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                                "dynasty": br['dynasty'],
                                "relation_type": "住持/僧人 @ " + matched_variant if is_direct else "đề cập @ " + matched_variant,
                                "source_name": "DILA Tiểu Sử (tự động)",
                                "source_url": f"https://authority.dila.edu.tw/person/?val={br['id']}",
                                "note": snippet,
                                "bio_vi": br['bio_vi'] or None,
                                "has_lineage": has_marcus,
                                "is_direct": is_direct,
                            })
            bio_persons.sort(key=lambda x: (0 if x['is_direct'] else 1, x['dynasty'] or ''))
        except Exception as bio_err:
            app.logger.warning(f"bio_persons search failed: {bio_err}")

        # ── Source 4: DILA Place Authority listBibl (T39) ──────────────────────
        bibl_persons = []
        try:
            bibl_rows = conn.execute("""
                SELECT ppb.person_id, ppb.person_name_raw, ppb.cbeta_ref,
                       ppb.source_book, ppb.mention_keyword, ppb.confidence,
                       p.name_zh, p.name_vi, p.dynasty
                FROM place_person_bibl ppb
                LEFT JOIN people p ON p.id = ppb.person_id
                WHERE ppb.place_id = ? AND ppb.person_id IS NOT NULL
                ORDER BY ppb.confidence DESC, ppb.source_book, ppb.person_name_raw
                LIMIT 150
            """, (dila_id or place_id,)).fetchall()
            linked_ids_all = {p['id'] for p in persons} | {p['id'] for p in bio_persons}
            for br in bibl_rows:
                if br['person_id'] in linked_ids_all:
                    continue
                has_marcus = conn.execute(
                    "SELECT 1 FROM marcus_people_link WHERE person_id=?", (br['person_id'],)
                ).fetchone() is not None
                marcus_label_row = conn.execute(
                    "SELECT label FROM marcus_reference WHERE node_id=?", (br['person_id'],)
                ).fetchone()
                kw = br['mention_keyword'] or ''
                cbeta_ref = br['cbeta_ref'] or ''
                bibl_persons.append({
                    "id": br['person_id'],
                    "name_zh": br['name_zh'] or br['person_name_raw'],
                    "name_vi": br['name_vi'],
                    "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                    "dynasty": br['dynasty'],
                    "relation_type": f"CBETA @ {kw}" if kw else "CBETA",
                    "source_name": br['source_book'] or "DILA CBETA Bibl",
                    "source_url": f"https://cbetaonline.dila.edu.tw/zh/{cbeta_ref}" if cbeta_ref else "https://cbeta.org",
                    "note": f"{br['source_book']} {cbeta_ref}",
                    "has_lineage": has_marcus,
                    "cbeta_ref": cbeta_ref,
                    "confidence": br['confidence'],
                })
        except Exception as bibl_err:
            app.logger.warning(f"bibl_persons query failed: {bibl_err}")

        # ── Source 5: DILA Person Authority placeOfOrigin (T41) ────────────────
        origin_persons = []
        try:
            all_linked_ids = (
                {p['id'] for p in persons}
                | {p['id'] for p in bio_persons}
                | {p.get('id') for p in bibl_persons if p.get('id')}
            )
            origin_rows = conn.execute("""
                SELECT pol.person_id, pol.confidence,
                       p.name_zh, p.name_vi, p.dynasty
                FROM person_origin_link pol
                JOIN people p ON p.id = pol.person_id
                WHERE pol.place_id = ?
                ORDER BY pol.confidence DESC, p.dynasty, p.name_zh
                LIMIT 100
            """, (dila_id or place_id,)).fetchall()
            for or_ in origin_rows:
                if or_['person_id'] in all_linked_ids:
                    continue
                marcus_label_row = conn.execute(
                    "SELECT label FROM marcus_reference WHERE node_id=?", (or_['person_id'],)
                ).fetchone()
                has_marcus = conn.execute(
                    "SELECT 1 FROM marcus_people_link WHERE person_id=?", (or_['person_id'],)
                ).fetchone() is not None
                origin_persons.append({
                    "id": or_['person_id'],
                    "name_zh": or_['name_zh'],
                    "name_vi": or_['name_vi'],
                    "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                    "dynasty": or_['dynasty'],
                    "relation_type": "sinh tại / 籍貫",
                    "source_name": "DILA Person Authority",
                    "source_url": f"https://authority.dila.edu.tw/person/?fromInner={or_['person_id']}",
                    "note": "quê quán",
                    "confidence": or_['confidence'],
                    "has_lineage": has_marcus,
                })
        except Exception as origin_err:
            app.logger.warning(f"origin_persons query failed: {origin_err}")

        if not persons and not wikidata_persons and not bio_persons and not bibl_persons and not origin_persons:
            return jsonify({
                "ok": True, "status": "pending", "place_id": place_id,
                "persons": [], "wikidata_persons": [], "bio_persons": [],
                "bibl_persons": [], "origin_persons": [],
                "message": "Chưa có liên kết nhân vật đã xác minh cho địa danh này.",
                "research_directions": [
                    "Wikidata P112 (founded by) — xây bridge geo_cross_ref.wikidata_qid cho địa danh này",
                    "Admin curation thủ công qua place_person_link (source_url bắt buộc)",
                ]
            })
        return jsonify({"ok": True, "status": "ok", "place_id": place_id,
                        "persons": persons, "wikidata_persons": wikidata_persons,
                        "bio_persons": bio_persons, "bibl_persons": bibl_persons,
                        "origin_persons": origin_persons})
    except Exception as e:
        app.logger.error(f"api_places_persons error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/admin/place-person-link', methods=['POST'])
def api_admin_place_person_link_add():
    """POST /daoanh/api/admin/place-person-link
    body: {place_id, person_id, relation_type?, source_name, source_url, note?}
    Curated add for T22 — source_name + source_url are mandatory so every entry is citable.
    Does not verify the citation content; the human submitting is asserting it, same trust
    model as CUSTOM_HANVIET/custom_hanviet_override (T08).
    """
    data = request.get_json(silent=True) or {}
    place_id = (data.get('place_id') or '').strip()
    person_id = (data.get('person_id') or '').strip()
    source_name = (data.get('source_name') or '').strip()
    source_url = (data.get('source_url') or '').strip()
    if not place_id or not person_id:
        return jsonify({"ok": False, "error": "place_id and person_id required"}), 400
    if not source_name or not source_url:
        return jsonify({"ok": False, "error": "source_name and source_url required — mọi liên kết phải có trích dẫn"}), 400
    conn = get_db_connection()
    try:
        _ensure_place_person_link_table(conn)
        person = conn.execute("SELECT id FROM people WHERE id = ?", (person_id,)).fetchone()
        if not person:
            return jsonify({"ok": False, "error": f"person_id {person_id} not found in people table"}), 404
        conn.execute("""
            INSERT INTO place_person_link (place_id, person_id, relation_type, source_name, source_url, note, added_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (place_id, person_id, data.get('relation_type') or '', source_name, source_url, data.get('note') or '', request.remote_addr))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/places/<place_id>/timeline')
def api_places_timeline(place_id):
    """GET /daoanh/api/places/<id>/timeline — T21 Geo-Identity Linking (2026-08-20).
    Returns founding date (Wikidata P571 via geo_cross_ref) + dynasty context (DILA time_periods)
    + static events (place_timeline_events). No data fabricated: returns no_mapping if QID unknown."""
    try:
        conn = get_db_connection()
        _ensure_geo_cross_ref_table(conn)
        _ensure_place_timeline_events_table(conn)

        dila_id, _ = _resolve_dila_id(conn, place_id)
        target_id = dila_id or place_id

        xref = conn.execute(
            "SELECT wikidata_qid, bgis_id, chgis_svid, marcus_ref, confidence, mapped_by FROM geo_cross_ref WHERE dila_id = ?",
            (target_id,)
        ).fetchone()

        static_events = conn.execute(
            """SELECT event_type, year, year_end, label_zh, label_vi, source, source_ref, confidence
               FROM place_timeline_events WHERE dila_id = ? ORDER BY year ASC""",
            (target_id,)
        ).fetchall()
        static_ev_list = [
            {"event_type": r[0], "year": r[1], "year_end": r[2],
             "label_zh": r[3], "label_vi": r[4],
             "source": r[5], "source_ref": r[6], "confidence": r[7]}
             for r in static_events
        ]

        if not xref or not xref[0]:
            # No Wikidata QID — fallback to DILA-sourced founding event (Hướng A, T21)
            dila_founding = conn.execute(
                """SELECT year, source, source_ref, confidence, label_zh, label_vi
                   FROM place_timeline_events
                   WHERE dila_id = ? AND event_type = 'founding' AND year IS NOT NULL
                   ORDER BY CASE source
                     WHEN 'dila_era_name' THEN 1
                     WHEN 'dila_dynasty' THEN 2
                     WHEN 'dila_note' THEN 3
                     ELSE 4
                   END, confidence DESC LIMIT 1""",
                (target_id,)
            ).fetchone()
            if dila_founding:
                dila_year = dila_founding[0]
                dynasty = _get_dynasty_context(dila_year, conn)
                conn.close()
                return jsonify({
                    "ok": True,
                    "status": "dila_fallback",
                    "dila_id": target_id,
                    "founding": {
                        "year": dila_year,
                        "source": dila_founding[1],
                        "source_ref": dila_founding[2],
                        "confidence": dila_founding[3],
                        "label_zh": dila_founding[4],
                        "label_vi": dila_founding[5],
                        "note_vi": "Nguồn DILA — chưa cross-verify Wikidata",
                        "license": "CC BY-NC-SA 4.0 (DILA)"
                    },
                    "dynasty_context": dynasty,
                    "static_events": static_ev_list,
                    "wikidata_qid": None
                })
            conn.close()
            return jsonify({
                "ok": True,
                "status": "no_mapping",
                "dila_id": target_id,
                "message": "Chưa có ID xác minh (Wikidata QID) cho địa danh này. Xem T21 task để biết cách thêm mapping.",
                "static_events": static_ev_list,
                "founding": None,
                "dynasty_context": None
            })

        qid = xref[0]
        wd = _fetch_wikidata_timeline(qid)
        founding_year = wd.get("founding_year")
        dynasty = _get_dynasty_context(founding_year, conn) if founding_year else None

        conn.close()
        return jsonify({
            "ok": True,
            "status": "ok",
            "dila_id": target_id,
            "cross_refs": {
                "wikidata_qid": qid,
                "bgis_id": xref[1],
                "chgis_svid": xref[2],
                "marcus_ref": xref[3],
                "confidence": xref[4],
                "mapped_by": xref[5]
            },
            "founding": {
                "year": founding_year,
                "label": wd.get("label", ""),
                "heritage": wd.get("heritage", []),
                "source": "wikidata",
                "source_ref": wd.get("source_ref", f"{qid}·P571"),
                "license": "CC0",
                "wikidata_url": wd.get("wikidata_url", f"https://www.wikidata.org/wiki/{qid}")
            } if not wd.get("error") else None,
            "dynasty_context": dynasty,
            "static_events": static_ev_list,
            "wikidata_error": wd.get("error")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




# ── T97: Place Events API ──────────────────────────────────────────────────────
@app.route('/daoanh/api/places/<place_id>/events')
def api_places_events(place_id):
    """GET /daoanh/api/places/<id>/events — T97 Tab Sự Kiện.
    Returns events linked to this place from nexus_events + event_text_link.
    Evidence-first: every event has passage_id / cbeta_ref + source_book.
    No self-generated events, no year fabrication."""
    try:
        conn = get_db_connection()
        conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
        dila_id, _ = _resolve_dila_id(conn, place_id)
        target_id = dila_id or place_id

        # 1. nexus_events — person-place co-mentions from CBETA passages
        ne_rows = conn.execute("""
            SELECT ne.passage_id, ne.person_dila_id, ne.event_year,
                   ne.event_label, ne.source_book, ne.confidence,
                   p.name_zh, p.name_vi
            FROM nexus_events ne
            LEFT JOIN people p ON p.id = ne.person_dila_id
            WHERE ne.place_dila_id = ?
            ORDER BY ne.event_year ASC NULLS LAST, ne.confidence DESC
            LIMIT 100
        """, (target_id,)).fetchall()

        nexus = []
        for r in ne_rows:
            nexus.append({
                "passage_id": r[0],
                "person_dila_id": r[1],
                "event_year": r[2],
                "event_label": r[3],
                "source_book": r[4],
                "confidence": r[5],
                "person_name_zh": r[6],
                "person_name_vi": r[7],
                "evidence_type": "cbeta_co_mention"
            })

        # 2. event_text_link — person-place links with exact CBETA ref
        etl_rows = conn.execute("""
            SELECT etl.event_type, etl.entity_id, etl.related_name,
                   etl.cbeta_ref, etl.source_book, etl.year, etl.confidence,
                   p.name_vi
            FROM event_text_link etl
            LEFT JOIN people p ON p.id = etl.entity_id
            WHERE etl.related_id = ? AND etl.event_type = 'person_place'
            ORDER BY etl.year ASC NULLS LAST, etl.confidence DESC
            LIMIT 100
        """, (target_id,)).fetchall()

        text_links = []
        seen_cbeta = set()
        for r in etl_rows:
            key = (r[1], r[3])  # entity_id + cbeta_ref — dedup
            if key in seen_cbeta:
                continue
            seen_cbeta.add(key)
            text_links.append({
                "event_type": r[0],
                "person_dila_id": r[1],
                "person_name_zh": r[2],
                "cbeta_ref": r[3],
                "source_book": r[4],
                "year": r[5],
                "confidence": r[6],
                "person_name_vi": r[7],
                "evidence_type": "cbeta_text_link"
            })

        # 3. events (T97 Build 2) — bảng events + event_entities
        ev_rows = conn.execute("""
            SELECT e.event_id, e.event_type, e.title_zh, e.title_vi,
                   e.start_year, e.end_year, e.precision, e.extraction_method,
                   e.review_status, e.confidence
            FROM events e
            JOIN event_entities ee ON ee.event_id = e.event_id
            WHERE ee.entity_id = ? AND ee.entity_type = 'place'
            ORDER BY (e.review_status = 'reviewed') DESC, e.start_year ASC NULLS LAST
            LIMIT 50
        """, (target_id,)).fetchall()

        reviewed_events, candidate_events = [], []
        for r in ev_rows:
            ev = {
                "event_id": r[0], "event_type": r[1],
                "title_zh": r[2], "title_vi": r[3],
                "start_year": r[4], "end_year": r[5],
                "precision": r[6], "extraction_method": r[7],
                "review_status": r[8], "confidence": r[9]
            }
            (reviewed_events if r[8] == 'reviewed' else candidate_events).append(ev)

        # T97b: cross-reference vn_person_events cho tu sĩ co-mention trong kinh.
        # Cầu nối person timeline ↔ place qua passage CBETA (evidence-first, 0 ALTER).
        person_ids = sorted({n['person_dila_id'] for n in nexus if n.get('person_dila_id')})
        person_timelines = []
        if person_ids:
            ph_placeholders = ','.join('?' * len(person_ids))
            pe_rows = conn.execute(
                f"SELECT person_id, event_type, event_year, event_label_vi, source, confidence "
                f"FROM vn_person_events WHERE person_id IN ({ph_placeholders}) "
                f"AND event_type IN ('active','floruit','birth','death',"
                f"'KeyLifeEvent','Contribution','PhilosophicalStance') "
                f"ORDER BY person_id, event_year IS NULL, event_year ASC",
                person_ids
            ).fetchall()
            by_pid = {}
            for pr in pe_rows:
                by_pid.setdefault(pr[0], []).append({
                    "event_type": pr[1], "event_year": pr[2],
                    "label_vi": pr[3], "source": pr[4], "confidence": pr[5],
                })
            name_map = {n['person_dila_id']: n for n in nexus if n.get('person_dila_id')}
            for pid in sorted(by_pid):
                nm = name_map.get(pid, {})
                person_timelines.append({
                    "person_dila_id": pid,
                    "person_name_vi": nm.get('person_name_vi'),
                    "person_name_zh": nm.get('person_name_zh'),
                    "source_book": nm.get('source_book'),
                    "timeline": by_pid[pid],
                })

        total = len(nexus) + len(text_links)
        conn.close()
        return jsonify({
            "ok": True,
            "dila_id": target_id,
            "total": total,
            "nexus_events": nexus,
            "text_links": text_links,
            "person_timelines": person_timelines,
            "reviewed_events": reviewed_events,
            "candidate_events": candidate_events,
            "note": "Evidence-first: mỗi sự kiện trỏ về passage_id/cbeta_ref trong CBETA."
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/places/<place_id>/time-mentions')
def api_place_time_mentions(place_id):
    """GET /daoanh/api/places/<id>/time-mentions — T97 Phase 2 output."""
    try:
        conn = get_db_connection()
        conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
        dila_id, _ = _resolve_dila_id(conn, place_id)
        target = dila_id or place_id

        rows = conn.execute("""
            SELECT tm.mention_id, tm.raw_time_zh, tm.normalized_start, tm.normalized_end,
                   tm.precision, tm.extraction_method, tm.confidence, tm.time_authority_id
            FROM time_mentions tm
            JOIN place_timeline_events pte ON pte.id = CAST(tm.source_record_id AS INTEGER)
            WHERE tm.source_table='place_timeline_events' AND pte.dila_id=?
            ORDER BY tm.normalized_start ASC NULLS LAST
        """, (target,)).fetchall()

        mentions = [dict(zip(['mention_id','raw_time_zh','normalized_start','normalized_end',
                               'precision','extraction_method','confidence','time_authority_id'], r))
                    for r in rows]
        conn.close()
        return jsonify({"ok": True, "dila_id": target, "total": len(mentions), "mentions": mentions})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




# ── T10: DILA Place Index API ─────────────────────────────────────────────────

@app.route('/daoanh/api/dila/places')
def api_dila_places_search():
    """GET /daoanh/api/dila/places?q=&category=&country=&limit=50&offset=0"""
    import csv, io as _io
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    country = request.args.get('country', '').strip()
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    fmt = request.args.get('format', 'json')
    try:
        conn = get_db_connection()
        where = []
        params = []
        if q:
            where.append("(pd.name_zh LIKE ? OR pd.name LIKE ? OR pd.id LIKE ?)")
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        if category:
            where.append("pd.note_category = ?")
            params.append(category)
        if country:
            where.append("pd.district LIKE ?")
            params.append(f'{country}%')
        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
        count_row = conn.execute(
            f"SELECT COUNT(*) FROM places_dila pd {where_sql}", params
        ).fetchone()
        total = count_row[0]
        rows = conn.execute(
            f"""SELECT pd.id, pd.name_zh, pd.name, pd.note_category, pd.district,
                       pd.geo_lat, pd.geo_long,
                       (SELECT nm.name_vi FROM namevi_map_places nm WHERE nm.name_zh = pd.name_zh
                        AND nm.dila_id IS NOT NULL
                        ORDER BY (nm.vn_name_status='reviewed') DESC, nm.confidence DESC LIMIT 1) AS name_vi,
                       (SELECT nm.confidence FROM namevi_map_places nm WHERE nm.name_zh = pd.name_zh
                        AND nm.dila_id IS NOT NULL
                        ORDER BY (nm.vn_name_status='reviewed') DESC, nm.confidence DESC LIMIT 1) AS confidence
                FROM places_dila pd
                {where_sql}
                ORDER BY pd.id
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        conn.close()
        items = [dict(r) for r in rows]
        if fmt == 'csv':
            out = _io.StringIO()
            w = csv.DictWriter(out, fieldnames=['id','name_zh','name','note_category','district','geo_lat','geo_long','name_vi','confidence'])
            w.writeheader(); w.writerows(items)
            from flask import Response
            return Response(out.getvalue(), mimetype='text/csv',
                            headers={"Content-Disposition": "attachment;filename=dila_places.csv"})
        return jsonify({"ok": True, "total": total, "limit": limit, "offset": offset, "items": items})
    except Exception as e:
        app.logger.error(f"api_dila_places_search error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/places/map-timeline')
def api_places_map_timeline():
    """
    GET /daoanh/api/places/map-timeline?min_year=&max_year=&dynasty=&limit=500
    T56 (phương án b — KHÔNG tạo bảng map_chronology): truy vấn runtime trực tiếp
    từ place_timeline_events (founding year, PL id) JOIN places_dila (GPS).
    Dynasty suy từ founding_year qua _get_dynasty_context() (hardcoded CE range,
    KHÔNG tự suy từ note/era — tuân data-integrity.md "evidence-first cho thời gian").
    Chỉ SELECT — không CREATE/ALTER bảng nào. Bọc try/except để chịu được VPS
    thiếu bảng (graceful degradation theo CLAUDE.md "VPS DB schema lag").
    """
    try:
        min_year = request.args.get('min_year', '').strip()
        max_year = request.args.get('max_year', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        try:
            limit = min(int(request.args.get('limit', 500)), 2000)
        except ValueError:
            limit = 500
        try:
            min_year = int(min_year) if min_year else None
        except ValueError:
            min_year = None
        try:
            max_year = int(max_year) if max_year else None
        except ValueError:
            max_year = None

        conn = get_db_connection()
        try:
            where = ["pte.event_type = 'founding'", "pte.year IS NOT NULL",
                     "pd.geo_lat IS NOT NULL", "pd.geo_long IS NOT NULL"]
            params = []
            if min_year is not None:
                where.append("pte.year >= ?")
                params.append(min_year)
            if max_year is not None:
                where.append("pte.year <= ?")
                params.append(max_year)
            where_sql = " AND ".join(where)

            # Khi có dynasty filter: dynasty suy từ year ở tầng Python (_get_dynasty_context),
            # nên KHÔNG thể LIMIT trong SQL trước khi lọc — ORDER BY year ASC + LIMIT sẽ chỉ
            # lấy các năm sớm nhất và có thể bỏ sót toàn bộ triều đại muộn hơn (ví dụ "唐").
            # Bảng place_timeline_events chỉ ~2.3K dòng founding nên fetch hết rồi lọc là rẻ.
            sql = f"""
                SELECT pte.dila_id, pte.year, pte.year_end, pte.label_zh, pte.label_vi,
                       pte.source, pte.confidence,
                       pd.name AS name_vi_raw, pd.name_zh,
                       pd.geo_lat, pd.geo_long,
                       n.name_vi AS name_vi_mapped
                FROM place_timeline_events pte
                JOIN places_dila pd ON pd.id = pte.dila_id
                LEFT JOIN namevi_map_places n ON n.dila_id = pte.dila_id
                WHERE {where_sql}
                ORDER BY pte.year ASC
            """
            if not dynasty:
                sql += "LIMIT ?"
                params = params + [limit]
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()

        results = []
        for r in rows:
            ctx = _get_dynasty_context(r['year'], None)
            dyn_zh = ctx['dynasty_zh'] if ctx else ''
            dyn_vi = ctx['dynasty_vi'] if ctx else ''
            if dynasty and dynasty not in (dyn_zh, dyn_vi):
                continue
            name_vi = r['name_vi_mapped'] or r['label_vi'] or _ensure_vietnamese(r['name_vi_raw'] or r['name_zh'] or '')
            results.append({
                "id": r['dila_id'],
                "name_vi": name_vi,
                "name_zh": r['name_zh'] or '',
                "lat": r['geo_lat'],
                "lng": r['geo_long'],
                "founding_year": r['year'],
                "founding_year_end": r['year_end'],
                "dynasty_zh": dyn_zh,
                "dynasty_vi": dyn_vi,
                "source": r['source'] or '',
                "confidence": r['confidence'] or '',
            })
            if len(results) >= limit:
                break

        return jsonify({"ok": True, "count": len(results), "results": results})
    except sqlite3.OperationalError as e:
        # VPS schema lag (place_timeline_events/places_dila chưa có) — trả rỗng, không sập route
        app.logger.warning(f"api_places_map_timeline: schema lag — {e}")
        return jsonify({"ok": True, "count": 0, "results": [], "warning": "schema_lag"})
    except Exception as e:
        app.logger.error(f"api_places_map_timeline error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/places/map-timeline/dynasties')
def api_places_map_timeline_dynasties():
    """
    GET /daoanh/api/places/map-timeline/dynasties
    Danh sách triều đại (suy từ founding_year qua _get_dynasty_context) kèm số
    lượng chùa và khoảng năm — phục vụ dropdown lọc trên bản đồ lịch sử (T56).
    Read-only, không bảng mới.
    """
    try:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT pte.year
                FROM place_timeline_events pte
                JOIN places_dila pd ON pd.id = pte.dila_id
                WHERE pte.event_type = 'founding' AND pte.year IS NOT NULL
                  AND pd.geo_lat IS NOT NULL AND pd.geo_long IS NOT NULL
            """).fetchall()
        finally:
            conn.close()

        agg = {}
        for r in rows:
            ctx = _get_dynasty_context(r['year'], None)
            if not ctx:
                continue
            key = ctx['dynasty_zh']
            if key not in agg:
                agg[key] = {"dynasty_zh": ctx['dynasty_zh'], "dynasty_vi": ctx['dynasty_vi'],
                             "min_year": r['year'], "max_year": r['year'], "count": 0}
            agg[key]["min_year"] = min(agg[key]["min_year"], r['year'])
            agg[key]["max_year"] = max(agg[key]["max_year"], r['year'])
            agg[key]["count"] += 1

        dynasties = sorted(agg.values(), key=lambda d: d["min_year"])
        return jsonify({"ok": True, "dynasties": dynasties})
    except sqlite3.OperationalError as e:
        app.logger.warning(f"api_places_map_timeline_dynasties: schema lag — {e}")
        return jsonify({"ok": True, "dynasties": [], "warning": "schema_lag"})
    except Exception as e:
        app.logger.error(f"api_places_map_timeline_dynasties error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/places_all')
def places_all():
    """
    GET /daoanh/api/admin/places_all
    Returns all places from places_pending with mapping status
    Supports filtering, sorting, pagination
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 per page
        offset = int(request.args.get('offset', 0))
        cate = request.args.get('cate', '').strip()
        country = request.args.get('country', '').strip()
        province = request.args.get('province', '').strip()
        mapped_status = request.args.get('mapped_status', '').strip()  # 'mapped', 'unmapped', or empty for all
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'asc').upper()
        
        # Validate sort_by to prevent SQL injection
        allowed_sort_fields = ['id', 'name_zh', 'name_vi', 'province', 'country', 'gps_lat', 'gps_long', 'created_at', 'updated_at']
        if sort_by not in allowed_sort_fields:
            sort_by = 'id'
        
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'ASC'
        
        conn = get_db_connection()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if cate:
            where_conditions.append("cate = ?")
            params.append(cate)
        
        if country:
            where_conditions.append("country = ?")
            params.append(country)
        
        if province:
            where_conditions.append("province = ?")
            params.append(province)
        
        if search:
            where_conditions.append("(name_zh LIKE ? OR name_vi LIKE ? OR id LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Map status filter: check if place_id exists in namevi_map_places
        if mapped_status == 'mapped':
            where_conditions.append("id IN (SELECT dila_id FROM namevi_map_places)")
        elif mapped_status == 'unmapped':
            where_conditions.append("id NOT IN (SELECT dila_id FROM namevi_map_places)")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM places_pending 
            {where_clause}
        """
        total_result = conn.execute(count_query, params).fetchone()
        total_count = total_result['total'] if total_result else 0
        
        # Get paginated results
        # We need to join with namevi_map_places to get mapping info
        query = f"""
            SELECT 
                p.*,
                CASE WHEN m.dila_id IS NOT NULL THEN 1 ELSE 0 END as is_mapped,
                m.name_vi as mapped_name_vi,
                m.updated_at as mapped_updated_at
            FROM places_pending p
            LEFT JOIN namevi_map_places m ON p.id = m.dila_id
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        places = conn.execute(query, params).fetchall()
        conn.close()
        
        # Convert to list of dicts
        places_list = []
        for place in places:
            place_dict = dict(place)
            places_list.append(place_dict)
        
        return jsonify({
            "success": True,
            "places": places_list,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/places/<place_id>/cbdb')
def cbdb_place_lookup(place_id):
    try:
        digits = ''.join(filter(str.isdigit, place_id))
        full_id = f'PL{digits.zfill(12)}' if digits else place_id
        conn = get_db_connection()
        row = conn.execute(
            "SELECT cbdb_addr_id, note FROM place_cbdb_map WHERE place_id = ?",
            (full_id,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"has_cbdb": False, "place_id": full_id, "cbdb_places": []})
        cbdb_id = row['cbdb_addr_id']
        cconn = get_cbdb_conn()
        cdata = cconn.execute(
            "SELECT c_name_chn, c_admin_type, c_notes FROM ADDR_CODES WHERE c_addr_id = ?",
            (cbdb_id,)
        ).fetchone()
        cconn.close()
        if not cdata:
            return jsonify({
                "has_cbdb": True, "place_id": full_id,
                "cbdb_places": [{"cbdb_addr_id": cbdb_id, "error": "ADDR_CODES row not found"}]
            })
        return jsonify({
            "has_cbdb": True,
            "place_id": full_id,
            "cbdb_places": [{
                "cbdb_addr_id": cbdb_id,
                "name_zh": cdata['c_name_chn'] or '',
                "admin_type": cdata['c_admin_type'] or '',
                "notes_zh": cdata['c_notes'] or ''
            }]
        })
    except Exception as e:
        return jsonify({"error": True, "has_cbdb": False, "place_id": place_id, "cbdb_places": [], "message": str(e)})




@app.route('/daoanh/api/places/vi-map', methods=['GET'])
def api_places_vi_map_list():
    """T427 (1): danh sách địa danh places_dila + name_vi hiện tại (namevi_map_places),
    phân trang 50/trang, tìm kiếm + 6 bộ lọc. T465: cột Claude JOIN codex_place_name.dila_id
    (T443 applied 2026-10-23, 59.353 dòng). T466: cột Gemini JOIN ai_place_name.dila_id
    (PK 1-1, không nhân dòng); cột Từ điển dùng _lexicon_han_lookup() (cùng hàm endpoint
    ai_judge dùng) thay cho match chuỗi term y nguyên (luôn None vì lexicon.term lưu
    tiếng Việt, không phải Hán)."""
    try:
        q = (request.args.get('q') or '').strip()
        filt = (request.args.get('filter') or 'all').strip()
        # T478: client gửi hide_done nhưng trước đây server không đọc -> ID đã Pass
        # (vn_name_status='reviewed') vẫn quay lại hàng đợi sau reload dù checkbox
        # "Ẩn đã Pass" đang checked (default true). Đọc param, mặc định true để khớp
        # checkbox default trên UI.
        hide_done = (request.args.get('hide_done', 'true') or 'true').strip().lower() in ('1', 'true', 'yes')
        try:
            page = max(1, int(request.args.get('page', 1)))
        except Exception:
            page = 1
        try:
            size = max(1, min(200, int(request.args.get('size', 50))))
        except Exception:
            size = 50
        offset = (page - 1) * size

        conn = get_db_connection()

        has_gemini = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ai_place_name'").fetchone() is not None
        gemini_join = "LEFT JOIN ai_place_name g ON g.dila_id = pd.id" if has_gemini else ""
        gemini_col = "g.name_vi_ai" if has_gemini else "NULL"
        base_from = f"""
            FROM places_dila pd
            LEFT JOIN namevi_map_places m ON m.dila_id = pd.id
            LEFT JOIN codex_place_name c ON c.dila_id = pd.id
            {gemini_join}
        """
        where = []
        params = []
        if q:
            if q.upper().startswith('PL'):
                # Tìm theo Place ID -> exact match (có index tự nhiên trên PK), không LIKE
                # toàn bảng. Đây là nguồn chậm chính khi q là ID (1.2-1.7s trước khi sửa).
                qlong = ensure_long_id(q)
                where.append("pd.id = ?")
                params.append(qlong)
            else:
                # Tìm theo Hán tự / tên Việt -> LIKE (không tránh được full scan, nhưng
                # dataset chỉ 59K dòng nên vẫn <1s).
                where.append("(pd.name_zh LIKE ? OR m.name_vi LIKE ?)")
                params.extend([f'%{q}%', f'%{q}%'])

        if filt == 'needs_review':
            where.append("(m.id IS NULL OR m.vn_name_status IS NULL OR m.vn_name_status != 'reviewed')")
        elif filt == 'no_ttl':
            where.append("NOT EXISTS (SELECT 1 FROM vn_person_places vp WHERE vp.place_id = pd.id)")
        elif filt == 'pass100':
            # Giai đoạn 1: chưa có Claude/Gemini cho địa danh -> không dòng nào đạt Pass 100%.
            where.append("1 = 0")
        # 'no_claude', 'no_gemini', 'all': chưa có cột AI -> toàn bộ đều "thiếu", không thêm điều kiện.

        # T478: hide_done ẩn các dòng đã Pass (vn_name_status='reviewed') khỏi hàng đợi.
        # filt == 'needs_review' đã tự loại 'reviewed' ở trên -> không thêm điều kiện trùng.
        if hide_done and filt != 'needs_review':
            where.append("(m.vn_name_status IS NULL OR m.vn_name_status != 'reviewed')")

        where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''

        # QA vòng 3 (fix 1) — ĐÃ THỬ gộp COUNT bằng window function COUNT(*) OVER() nhưng ĐO
        # THẤY CHẬM HƠN (3.6s so với 0.35s của 2 query tách riêng, q='寺'): EXPLAIN QUERY PLAN
        # cho thấy window function buộc SQLite vật chất hoá (CO-ROUTINE/materialize) toàn bộ
        # kết quả rồi USE TEMP B-TREE FOR ORDER BY, mất khả năng dùng PK (pd.id) để lấy ORDER BY
        # + LIMIT giá rẻ như cách 2 query tách riêng đang làm. ĐÃ BÁO LẠI QA, KHÔNG áp dụng —
        # giữ 2 query tách riêng (COUNT trước, SELECT LIMIT sau) như vòng 2.
        total = conn.execute(f"SELECT COUNT(*) {base_from} {where_sql}", params).fetchone()[0]

        rows = conn.execute(f"""
            SELECT pd.id AS place_id, pd.name_zh AS name_zh,
                   m.name_vi AS name_vi, m.source AS source,
                   m.vn_name_status AS vn_name_status, m.confidence AS confidence,
                   m.needs_review AS needs_review,
                   c.name_vi AS claude_name_vi,
                   {gemini_col} AS gemini_name_vi
            {base_from}
            {where_sql}
            ORDER BY pd.id
            LIMIT ? OFFSET ?
        """, params + [size, offset]).fetchall()

        place_ids = [r['place_id'] for r in rows]
        name_zhs = [r['name_zh'] for r in rows if r['name_zh']]

        # T466: thay match chuỗi term y nguyên (luôn None vì lexicon.term lưu tiếng Việt,
        # không phải Hán) bằng _lexicon_han_lookup() — cùng hàm endpoint ai_judge (gợi ý
        # Lexicon trong tab Sửa của placevn.html) dùng để tìm thuật ngữ có definition chứa
        # Hán tự của địa danh. Có cache in-memory sẵn trong hàm, không full-scan mỗi dòng.
        lex_map = {}
        for han_name in set(name_zhs):
            terms = _lexicon_han_lookup(conn, han_name)
            if terms:
                lex_map[han_name] = '; '.join(terms)

        ttl_map = {}
        if place_ids:
            qmarks = ','.join('?' * len(place_ids))
            for tr in conn.execute(f"""
                SELECT place_id, place_label_vi FROM vn_person_places WHERE place_id IN ({qmarks})
            """, place_ids):
                ttl_map[tr['place_id']] = tr['place_label_vi']

        # T427 round 3 follow-up (lỗi 4 — không hiển thị editor): editor + thời gian duyệt
        # đã được _persist_canonical_decision() ghi vào canonical_decision.editor/updated_at
        # (1 dòng/entity_ref, luôn là quyết định mới nhất) khi Pass/Sửa. Chỉ tra cho đúng
        # place_ids của TRANG hiện tại (≤200 dòng) — không quét toàn bảng, không thêm cột
        # mới, không đổi schema.
        editor_map = {}
        if place_ids:
            qmarks = ','.join('?' * len(place_ids))
            try:
                for er in conn.execute(f"""
                    SELECT entity_ref, editor, updated_at FROM canonical_decision
                    WHERE entity_ref IN ({qmarks})
                """, place_ids):
                    editor_map[er['entity_ref']] = {'editor': er['editor'], 'updated_at': er['updated_at']}
            except Exception:
                pass  # Bảng có thể thiếu trên môi trường khác -> vẫn render trang bình thường.

        items = []
        for r in rows:
            ed = editor_map.get(r['place_id'])
            items.append({
                'place_id': r['place_id'],
                'name_zh': r['name_zh'],
                'name_vi': r['name_vi'],
                'source': r['source'],
                'source_badge': _t427_source_badge(r['source']),
                'vn_name_status': r['vn_name_status'],
                'confidence': r['confidence'],
                'needs_review': r['needs_review'],
                'claude_name_vi': r['claude_name_vi'],  # T465 — JOIN codex_place_name.dila_id (T443 applied 2026-10-23)
                'gemini_name_vi': r['gemini_name_vi'],   # T466 — JOIN ai_place_name.dila_id (PK, 1-1)
                'ttl_name_vi': ttl_map.get(r['place_id']),
                'dictionary_definition': lex_map.get(r['name_zh']),
                'editor': ed['editor'] if ed else None,
                'editor_at': ed['updated_at'] if ed else None,
            })

        filters = _t427_filter_counts(conn)

        conn.close()
        return jsonify({
            'ok': True,
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'pages': max(1, (total + size - 1) // size),
            'filters': filters,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ────────────────────────────────────────────────────────────────────────────────
# T482 — Tab "Catalog": danh mục địa danh DILA ĐẦY ĐỦ (place_catalog, 59.373 dòng =
# 59.167 places_dila + 206 dila_place_authority, nạp bởi scripts/t482_build_place_catalog.py).
# Bảng place_catalog CHỈ là khoá canonical hợp nhất — Claude/Gemini/name_vi hiện tại vẫn
# JOIN SỐNG từ bảng gốc (không denormalize, tránh lệch khi Admin Pass/Sửa ở Tab Place).
# Nút Kết luận/Sửa của tab này gọi lại ĐÚNG /daoanh/api/places/vi-map/<id>/approve và
# /edit đã có — KHÔNG tạo endpoint approve/edit riêng.

# Cache in-memory riêng cho cột Từ điển (đa nguồn, nội dung đầy đủ) — KHÔNG dùng chung
# _LEXICON_MEM của _lexicon_han_lookup() (bản đó chỉ giữ definition đã .lower(), không
# giữ source/term gốc để hiển thị). Khoảng trắng OCR giữa mỗi ký tự Hán trong lexicon
# (ví dụ "阿 育 王 寺") bị loại bỏ trước khi so khớp, để so được với name_zh không có
# khoảng trắng (ví dụ "阿育王寺").
_T482_DICT_CACHE = {}
_T482_DICT_CACHE_MAX = 2000
_T482_CJK_RUN_RE = re.compile(r'[㐀-䶿一-鿿]+')
_T482_WS_RE = re.compile(r'\s+')
# T482 perf fix round 2 (QA đo curl thực tế 2026-10-28: trang "chưa truy cập" 7.9-13.9s/
# trang). Root cause THẬT (đã xác minh bằng curl + EXPLAIN QUERY PLAN trên data/lineage.db,
# không phải benchmark hàm cô lập): round 1 (index Python RAM _T482_EXACT_IDX/_T482_BIGRAM_IDX,
# xem lịch sử git) chỉ nhanh SAU KHI đã build 1 lần trong RAM tiến trình — nhưng build đó
# (~10-37s, quét 166K dòng) phải LÀM LẠI mỗi khi tiến trình Flask khởi động lại, và môi
# trường dev restart app.py rất thường xuyên (xem AGENTS.md §17: nhiều session sửa file
# song song). Vi phạm Zero-RAM Principle (AGENTS.md §2) — không được nạp 166K dòng vào RAM
# Python mỗi lần start. Fix: chuyển hẳn sang SQL index BỀN trong DB (cột term_ns/def_ns +
# bảng lexicon_cjk_bigram, build 1 LẦN DUY NHẤT bằng scripts/t482_build_lexicon_cjk_idx.py
# --apply, KHÔNG build lại khi server restart) + BATCH QUERY cho cả trang (tối đa 50 tên/
# request) thay vì tra từng tên riêng (N+1). Giữ nguyên _T482_DICT_CACHE (cache theo
# name_zh, vẫn hữu ích cho các request lặp lại trong đời tiến trình).
_T482_SQL_IDX_READY = None  # None = chưa kiểm; True/False = đã kiểm, cache theo đời tiến trình


def _t482_sql_idx_ready(conn):
    """Kiểm 1 lần/đời tiến trình: cột term_ns + bảng lexicon_cjk_bigram đã được migration
    scripts/t482_build_lexicon_cjk_idx.py --apply tạo chưa. Nếu chưa (env chưa chạy migration),
    fallback về quét tuần tự an toàn (chậm nhưng đúng kết quả) thay vì lỗi 500."""
    global _T482_SQL_IDX_READY
    if _T482_SQL_IDX_READY is not None:
        return _T482_SQL_IDX_READY
    has_col = any(r[1] == 'term_ns' for r in conn.execute("PRAGMA table_info(lexicon)"))
    has_tbl = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lexicon_cjk_bigram'"
    ).fetchone() is not None
    _T482_SQL_IDX_READY = bool(has_col and has_tbl)
    return _T482_SQL_IDX_READY


# Ưu tiên nguồn khi nhiều nguồn cùng khớp (Admin chốt): Thông Thiền cao nhất trong số
# các nguồn lexicon hiện có. "Từ Điển Đại Tạng Kinh của Nguyễn Minh Tiến" — đã tìm trong
# translation_glossary/term_glossaries/glossary_term/glossary_vi/monk_dict/dila_reference/
# data_sources, KHÔNG thấy bộ từ điển này trong DB (chỉ thấy cbeta_catalog_vn = MỤC LỤC
# sutra Nguyễn Minh Tiến, khoá theo title_vi, không phải từ điển thuật ngữ theo name_zh —
# không dùng được cho cột này). Xem T482 report.
_T482_SOURCE_PRIORITY = {
    'Tu Dien Thien Tong Han Viet - Han Man - Thong Thien': 0,
}


def _t482_source_rank(source):
    return _T482_SOURCE_PRIORITY.get(source, 1)


def _t482_dictionary_lookup_fallback_scan(conn, name_ns_list):
    """Fallback KHÔNG dùng SQL index (chỉ chạy khi migration lexicon_cjk_bigram chưa --apply
    trên env này) — quét tuần tự 166K dòng 1 lần cho TOÀN BỘ tên cần tra trong batch (vẫn
    tốt hơn quét riêng từng tên). Chậm nhưng đúng, không lỗi 500. Trả {name_ns: [matches]}."""
    need = set(n for n in name_ns_list if n)
    out = {n: [] for n in need}
    if not need:
        return out
    rows = conn.execute("SELECT term, definition, source FROM lexicon")
    for r in rows:
        term = r['term'] or ''
        definition = r['definition'] or ''
        term_ns = _T482_WS_RE.sub('', term)
        def_ns = _T482_WS_RE.sub('', definition)
        for n in need:
            if n == term_ns:
                out[n].append({'source': r['source'], 'term': term, 'definition': definition, 'match_type': 'exact_term'})
            elif n in def_ns:
                out[n].append({'source': r['source'], 'term': term, 'definition': definition, 'match_type': 'substring_def'})
    return out


def _t482_dictionary_lookup_batch(conn, name_zh_list):
    """Tra lexicon cho NHIỀU name_zh cùng lúc (1 trang catalog = tối đa 50 tên) bằng SQL
    BATCH QUERY trên index bền (term_ns/def_ns/lexicon_cjk_bigram — xây 1 lần bằng
    scripts/t482_build_lexicon_cjk_idx.py --apply), thay vì N+1 lần tra riêng từng tên
    hoặc quét tuần tự 166K dòng trong RAM Python (T482 perf fix round 2). Trả
    {name_zh: [matches]} — TOÀN BỘ nội dung + tên nguồn, tối đa 5 kết quả/tên, ưu tiên
    exact_term > substring_def rồi theo _T482_SOURCE_PRIORITY."""
    result = {}
    uncached = []
    for name_zh in name_zh_list:
        if not name_zh:
            result[name_zh] = []
            continue
        if name_zh in _T482_DICT_CACHE:
            result[name_zh] = _T482_DICT_CACHE[name_zh]
        else:
            uncached.append(name_zh)
    if not uncached:
        return result

    name_ns_of = {nz: _T482_WS_RE.sub('', nz) for nz in uncached}
    distinct_ns = sorted(set(v for v in name_ns_of.values() if v))

    if not _t482_sql_idx_ready(conn):
        scan = _t482_dictionary_lookup_fallback_scan(conn, distinct_ns)
        for name_zh in uncached:
            ns = name_ns_of[name_zh]
            matches = scan.get(ns, [])
            matches = sorted(matches, key=lambda m: (0 if m['match_type'] == 'exact_term' else 1, _t482_source_rank(m['source'])))[:5]
            if len(_T482_DICT_CACHE) >= _T482_DICT_CACHE_MAX:
                _T482_DICT_CACHE.pop(next(iter(_T482_DICT_CACHE)))
            _T482_DICT_CACHE[name_zh] = matches
            result[name_zh] = matches
        return result

    matches_by_ns = {ns: [] for ns in distinct_ns}

    # 1) Exact match — 1 query IN(...) cho toàn bộ tên khác nhau trong trang, dùng index
    #    idx_lexicon_term_ns (O(log n) mỗi tên, không quét bảng).
    if distinct_ns:
        placeholders = ','.join('?' * len(distinct_ns))
        for r in conn.execute(
            f"SELECT term, definition, source, term_ns FROM lexicon WHERE term_ns IN ({placeholders})",
            distinct_ns,
        ):
            matches_by_ns[r['term_ns']].append(
                {'source': r['source'], 'term': r['term'], 'definition': r['definition'], 'match_type': 'exact_term'}
            )

    # 2) Substring (definition) — thu hẹp ứng viên bằng bigram_idx TRONG SQL (1 query),
    #    rồi chỉ fetch + verify substring thật trên tập ứng viên nhỏ (không quét 166K dòng).
    bigrams_of_ns = {}
    all_bigrams = set()
    for ns in distinct_ns:
        if len(ns) < 2:
            bigrams_of_ns[ns] = None  # tên 1 ký tự Hán (hiếm) -> fallback quét riêng dưới đây
            continue
        bgs = [ns[j:j + 2] for j in range(len(ns) - 1)]
        bigrams_of_ns[ns] = bgs
        all_bigrams.update(bgs)

    bigram_to_ids = {}
    if all_bigrams:
        placeholders = ','.join('?' * len(all_bigrams))
        for r in conn.execute(
            f"SELECT bigram, lexicon_id FROM lexicon_cjk_bigram WHERE bigram IN ({placeholders})",
            list(all_bigrams),
        ):
            bigram_to_ids.setdefault(r['bigram'], set()).add(r['lexicon_id'])

    candidate_ids_by_ns = {}
    all_candidate_ids = set()
    for ns, bgs in bigrams_of_ns.items():
        if bgs is None:
            continue  # tên 1 ký tự: xử lý riêng dưới (quét tuần tự chỉ cho các tên này)
        candidates = None
        for bg in bgs:
            ids_for_bg = bigram_to_ids.get(bg)
            if not ids_for_bg:
                candidates = set()
                break
            candidates = ids_for_bg if candidates is None else (candidates & ids_for_bg)
            if not candidates:
                break
        candidate_ids_by_ns[ns] = candidates or set()
        all_candidate_ids.update(candidate_ids_by_ns[ns])

    if all_candidate_ids:
        # 2-pass fetch (đo thực tế: trang có nhiều ứng viên — ví dụ 464 id — tốn ~1.5s nếu
        # SELECT luôn cả cột `definition` cho TẤT CẢ ứng viên, vì definition dài tràn sang
        # overflow page riêng trong SQLite, I/O đĩa tốn cho cả những ứng viên KHÔNG khớp.
        # Pass 1: chỉ lấy id + def_ns (nhẹ) để verify substring thật. Pass 2: chỉ fetch
        # term/definition/source đầy đủ cho các id ĐÃ xác nhận khớp (luôn rất nhỏ, tối đa
        # vài chục id so với hàng trăm ứng viên thô).
        placeholders = ','.join('?' * len(all_candidate_ids))
        def_ns_by_id = {}
        for r in conn.execute(
            f"SELECT id, def_ns FROM lexicon WHERE id IN ({placeholders})",
            list(all_candidate_ids),
        ):
            def_ns_by_id[r['id']] = r['def_ns'] or ''

        matched_ids_by_ns = {}
        all_matched_ids = set()
        for ns, ids in candidate_ids_by_ns.items():
            matched = [lid for lid in ids if ns in def_ns_by_id.get(lid, '')]
            matched_ids_by_ns[ns] = matched
            all_matched_ids.update(matched)

        if all_matched_ids:
            placeholders = ','.join('?' * len(all_matched_ids))
            full_rows = {}
            for r in conn.execute(
                f"SELECT id, term, definition, source FROM lexicon WHERE id IN ({placeholders})",
                list(all_matched_ids),
            ):
                full_rows[r['id']] = r
            for ns, ids in matched_ids_by_ns.items():
                for lid in ids:
                    r = full_rows.get(lid)
                    if r is None:
                        continue
                    matches_by_ns[ns].append(
                        {'source': r['source'], 'term': r['term'], 'definition': r['definition'], 'match_type': 'substring_def'}
                    )

    # Tên 1 ký tự Hán (hiếm, không có bigram) — fallback quét tuần tự CHỈ cho nhóm nhỏ này.
    one_char_ns = [ns for ns, bgs in bigrams_of_ns.items() if bgs is None]
    if one_char_ns:
        scan = _t482_dictionary_lookup_fallback_scan(conn, one_char_ns)
        for ns in one_char_ns:
            # scan() đã trả cả exact_term lẫn substring_def; exact_term đã có ở bước 1 cho
            # mọi độ dài tên nên chỉ lấy phần substring_def ở đây để khỏi trùng.
            for m in scan.get(ns, []):
                if m['match_type'] == 'substring_def':
                    matches_by_ns[ns].append(m)

    for name_zh in uncached:
        ns = name_ns_of[name_zh]
        matches = matches_by_ns.get(ns, [])
        matches = sorted(matches, key=lambda m: (0 if m['match_type'] == 'exact_term' else 1, _t482_source_rank(m['source'])))[:5]
        if len(_T482_DICT_CACHE) >= _T482_DICT_CACHE_MAX:
            _T482_DICT_CACHE.pop(next(iter(_T482_DICT_CACHE)))
        _T482_DICT_CACHE[name_zh] = matches
        result[name_zh] = matches
    return result


def _t482_dictionary_lookup(conn, name_zh):
    """Tra lexicon cho 1 tên — giữ lại cho tương thích ngược (nếu có code khác gọi đơn lẻ).
    Route catalog dùng _t482_dictionary_lookup_batch() để tra cả trang trong vài query."""
    return _t482_dictionary_lookup_batch(conn, [name_zh]).get(name_zh, [])


@app.route('/daoanh/api/places/catalog', methods=['GET'])
def api_places_catalog_list():
    """T482: danh mục địa danh DILA ĐẦY ĐỦ (place_catalog = places_dila + dila_place_authority,
    59.373 dòng) cho tab "Catalog" (namevimap.html). Cột Kết luận/Sửa dùng lại
    /daoanh/api/places/vi-map/<id>/approve và /edit — không tạo cơ chế mới."""
    try:
        q = (request.args.get('q') or '').strip()
        try:
            page = max(1, int(request.args.get('page', 1)))
        except Exception:
            page = 1
        try:
            size = max(1, min(200, int(request.args.get('size', 50))))
        except Exception:
            size = 50
        offset = (page - 1) * size

        conn = get_db_connection()

        has_catalog = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='place_catalog'").fetchone() is not None
        if not has_catalog:
            conn.close()
            return jsonify({'ok': False, 'error': "Bảng place_catalog chưa được tạo — chạy scripts/t482_build_place_catalog.py --apply"}), 500

        has_gemini = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ai_place_name'").fetchone() is not None
        gemini_join = "LEFT JOIN ai_place_name g ON g.dila_id = pc.place_id" if has_gemini else ""
        gemini_col = "g.name_vi_ai" if has_gemini else "NULL"

        base_from = f"""
            FROM place_catalog pc
            LEFT JOIN namevi_map_places m ON m.dila_id = pc.place_id
            LEFT JOIN codex_place_name c ON c.dila_id = pc.place_id
            {gemini_join}
        """
        where = []
        params = []
        if q:
            if q.upper().startswith('PL'):
                qlong = ensure_long_id(q)
                where.append("pc.place_id = ?")
                params.append(qlong)
            else:
                where.append("(pc.name_zh LIKE ? OR m.name_vi LIKE ?)")
                params.extend([f'%{q}%', f'%{q}%'])
        where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''

        total = conn.execute(f"SELECT COUNT(*) {base_from} {where_sql}", params).fetchone()[0]

        rows = conn.execute(f"""
            SELECT pc.place_id AS place_id, pc.name_zh AS name_zh, pc.source_table AS source_table,
                   m.name_vi AS name_vi, m.source AS source, m.vn_name_status AS vn_name_status,
                   c.name_vi AS claude_name_vi,
                   {gemini_col} AS gemini_name_vi
            {base_from}
            {where_sql}
            ORDER BY pc.place_id
            LIMIT ? OFFSET ?
        """, params + [size, offset]).fetchall()

        # T482 perf fix round 2: tra Từ điển cho CẢ TRANG trong 1 lượt (vài query SQL batch)
        # thay vì gọi _t482_dictionary_lookup() riêng cho từng tên (N+1, 50 lần/trang).
        dict_matches_by_name = _t482_dictionary_lookup_batch(conn, [r['name_zh'] for r in rows])
        items = []
        for r in rows:
            dict_matches = dict_matches_by_name.get(r['name_zh'], [])
            items.append({
                'place_id': r['place_id'],
                'name_zh': r['name_zh'],
                'source_table': r['source_table'],
                'name_vi': r['name_vi'],
                'source': r['source'],
                'source_badge': _t427_source_badge(r['source']),
                'vn_name_status': r['vn_name_status'],
                'claude_name_vi': r['claude_name_vi'],
                'gemini_name_vi': r['gemini_name_vi'],
                'dictionary_matches': dict_matches,
            })

        conn.close()
        return jsonify({
            'ok': True,
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'pages': max(1, (total + size - 1) // size),
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/daoanh/api/places/vi-map/<place_id>/approve', methods=['POST'])
def api_places_vi_map_approve(place_id):
    """T427 (2): Pass — xác nhận name_vi hiện tại của 1 địa danh. Chỉ ghi namevi_map_places
    (bản ID dài), không ghi places_pending. Ghi audit qua _persist_canonical_decision()."""
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'unauthorized — thiếu hoặc sai session token'}), 403
    try:
        data = request.json or {}
        long_id = ensure_long_id(place_id)
        conn = get_db_connection()
        row = conn.execute(
            "SELECT name_vi, vn_name_status FROM namevi_map_places WHERE dila_id = ?", (long_id,)
        ).fetchone()
        if not row:
            conn.close()
            return jsonify({'ok': False, 'error': f'Không có dòng namevi_map_places cho {long_id} — chưa thể Pass. Dùng Sửa để tạo trước.'}), 404
        name_vi = row['name_vi']
        conn.execute(
            "UPDATE namevi_map_places SET vn_name_status = 'reviewed', needs_review = 0 WHERE dila_id = ?",
            (long_id,)
        )
        # QA vòng 2 (fix 1): canonical_name_vi / audit new_value phải là TÊN VIỆT THỰC
        # (name_vi), không phải chữ "reviewed" — 'reviewed' chỉ là vn_name_status, một
        # trường trạng thái riêng, không phải giá trị canonical name.
        # QA vòng 3 (fix 2): audit của Pass phải theo dõi THAY ĐỔI TÊN (field_name='name_vi'),
        # không phải trạng thái (field_name='vn_name_status') — Pass không đổi name_vi nên
        # old_value == new_value == name_vi hiện tại (ghi nhận: tên này vừa được xác nhận/duyệt).
        # T427 round 3 follow-up (lỗi 4): lấy editor + thời gian NGAY tại đây (cùng giá trị
        # _persist_canonical_decision() ghi vào canonical_decision.editor/updated_at) để trả
        # thẳng cho client hiển thị cạnh badge, không cần gọi lại API khác.
        import datetime as _dt427
        editor_email = _t427_session_email(token)
        decided_at = _dt427.datetime.now().isoformat(timespec='seconds')
        _persist_canonical_decision(
            conn, long_id, action='approve', field_name='name_vi',
            old_value=(name_vi or ''), new_value=(name_vi or ''),
            authority_rank='admin_approved', verification_status='verified',
            decision_note='T427: Pass tab Place (namevimap.html)',
            editor=editor_email,
            mark_verified=True,
        )
        conn.commit()
        conn.close()
        _t427_invalidate_filter_cache()
        return jsonify({'ok': True, 'place_id': long_id, 'name_vi': name_vi, 'vn_name_status': 'reviewed',
                         'editor': editor_email, 'editor_at': decided_at})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/places/vi-map/<place_id>/edit', methods=['POST'])
def api_places_vi_map_edit(place_id):
    """T427 (2): Sửa name_vi tại chỗ cho 1 địa danh. Trim nhưng KHÔNG title-case (giữ nguyên
    Admin gõ). Chỉ ghi namevi_map_places (bản ID dài), không ghi places_pending."""
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'unauthorized — thiếu hoặc sai session token'}), 403
    try:
        data = request.json or {}
        name_vi = (data.get('name_vi') or '').strip()
        if not name_vi:
            return jsonify({'ok': False, 'error': 'Thiếu name_vi'}), 400
        long_id = ensure_long_id(place_id)
        conn = get_db_connection()
        row = conn.execute(
            "SELECT name_vi FROM namevi_map_places WHERE dila_id = ?", (long_id,)
        ).fetchone()
        if not row:
            conn.close()
            return jsonify({'ok': False, 'error': f'Không có dòng namevi_map_places cho {long_id} — giai đoạn 1 chỉ UPDATE, không tạo dòng mới.'}), 404
        old_value = row['name_vi'] or ''
        conn.execute(
            "UPDATE namevi_map_places SET name_vi = ?, source = 'manual', vn_name_status = 'reviewed', needs_review = 0 WHERE dila_id = ?",
            (name_vi, long_id)
        )
        # T427 round 3 follow-up (lỗi 4): xem chú thích ở route /approve phía trên.
        import datetime as _dt427e
        editor_email = _t427_session_email(token)
        decided_at = _dt427e.datetime.now().isoformat(timespec='seconds')
        _persist_canonical_decision(
            conn, long_id, action='edit', field_name='name_vi',
            old_value=old_value, new_value=name_vi,
            authority_rank='admin_edit', verification_status='verified',
            decision_note='T427: Sửa tab Place (namevimap.html)',
            editor=editor_email,
            mark_verified=True,
        )
        conn.commit()
        conn.close()
        _t427_invalidate_filter_cache()
        return jsonify({'ok': True, 'place_id': long_id, 'name_vi': name_vi, 'source': 'manual', 'vn_name_status': 'reviewed',
                         'editor': editor_email, 'editor_at': decided_at})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500



@app.route('/daoanh/api/admin/place/<id>/canonical')
def place_canonical(id):
    """T67c: trả về quyết định canonical hiện tại + audit history cho 1 địa danh."""
    try:
        conn = get_db_connection()
        ref = _resolve_place_id(conn, id)
        decision = conn.execute(
            "SELECT * FROM canonical_decision WHERE entity_ref = ?", (ref,)
        ).fetchone()
        history = conn.execute(
            "SELECT log_id, action, field_name, old_value, new_value, evidence_sources, authority_rank, editor, verification_status, created_at "
            "FROM en_audit_log WHERE entity_ref = ? ORDER BY log_id DESC LIMIT 50", (ref,)
        ).fetchall()
        hub = conn.execute(
            "SELECT status, updated_at FROM entity_hub WHERE canonical_label = ?", (ref,)
        ).fetchone()
        conn.close()
        return jsonify({
            "success": True,
            "entity_ref": ref,
            "decision": dict(decision) if decision else None,
            "history": [dict(h) for h in history],
            "entity_hub_status": dict(hub) if hub else None,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/place/<id>/authority')
def place_authority(id):
    """T68b: trả về authority rank + các nguồn đóng góp + conflict_pending cho 1 địa danh."""
    try:
        conn = get_db_connection()
        ref = _resolve_place_id(conn, id)
        a_map = _source_authority_map(conn)
        ranked = _name_vi_evidence(conn, ref, a_map)
        _detect_conflicts(conn, ranked, ref)
        conn.commit()
        conflicts = conn.execute(
            "SELECT * FROM conflict_pending WHERE entity_ref = ? AND status = 'pending' ORDER BY id",
            (ref,)
        ).fetchall()
        source_rows = conn.execute(
            "SELECT source_code, source_id, authority_score, precedence_order, implemented, note FROM source_authority ORDER BY authority_score DESC"
        ).fetchall()
        conn.close()
        return jsonify({
            "success": True,
            "entity_ref": ref,
            "canonical_candidates": [
                {"value": v, "score": d['score'], "sources": d['sources'],
                 "confidence": d['confidence'], "order": d['order']}
                for v, d in ranked
            ],
            "conflicts": [dict(c) for c in conflicts],
            "authority_matrix": [dict(r) for r in source_rows],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/place/<id>/conflict/resolve', methods=['POST'])
def place_conflict_resolve(id):
    """T68c: admin chọn 1 giá trị để giải quyết xung đột → ghi conflict_pending + en_audit_log."""
    try:
        data = request.json or {}
        conflict_id = data.get('conflict_id')
        choice = (data.get('choice_value') or '').strip()
        source_code = (data.get('source_code') or '').strip()
        editor = (data.get('editor') or request.headers.get('X-Forwarded-Email') or 'admin')
        if not conflict_id or not choice:
            return jsonify({"success": False, "error": "Thiếu conflict_id hoặc choice_value"}), 400
        conn = get_db_connection()
        ref = _resolve_place_id(conn, id)
        row = conn.execute(
            "SELECT * FROM conflict_pending WHERE id = ? AND entity_ref = ?", (conflict_id, ref)
        ).fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "error": "Không tìm thấy xung đột"}), 404
        now = datetime.now().isoformat(timespec='seconds')
        # Chọn value_a hoặc value_b HOẶC giá trị khác do admin nhập
        source_chosen = source_code or (row['source_a'] if choice == row['value_a'] else row['source_b'])
        conn.execute("""
            UPDATE conflict_pending
            SET status='resolved', resolved_choice=?, resolved_by=?, resolved_at=?
            WHERE id = ?
        """, (choice, editor, now, conflict_id))
        # Ghi audit log (T67 pattern) — provenance cho quyết định xung đột
        conn.execute("""
            INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value,
                evidence_sources, authority_rank, editor, verification_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'resolved', ?)
        """, (ref, 'resolve_conflict', row['field'], f"{row['source_a']}: {row['value_a']}|{row['source_b']}: {row['value_b']}", choice, source_chosen, str(max(row['authority_a'] or 0, row['authority_b'] or 0)), editor, now))
        # Nếu chọn tên Việt → cập nhật canonical_decision + entity_hub nếu chưa có
        if row['field'] == 'name_vi' and choice:
            _persist_canonical_decision(
                conn, ref, action='resolve_conflict', field_name='name_vi',
                old_value=(row['value_a'] if choice != row['value_a'] else row['value_b']),
                new_value=choice,
                evidence_citations=[f"conflict #{conflict_id} resolved ({source_chosen})"],
                authority_rank=(source_chosen or 'admin'),
                verification_status='verified',
                decision_note='Conflict resolved bằng lựa chọn của admin (T68)',
                editor=editor, mark_verified=True,
            )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã giải quyết xung đột", "resolved_choice": choice})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/places_auto_names')
def places_auto_names():
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        conn = get_db_connection()
        total = conn.execute("""
            SELECT COUNT(*) FROM namevi_map_places m
            JOIN places_pending p ON p.id = m.dila_id
            WHERE m.vn_name_status = 'auto'
        """).fetchone()[0]
        rows = conn.execute("""
            SELECT p.id, p.name_zh, m.name_vi, m.vn_name_status,
                   p.district_raw, p.country, p.gps_lat, p.gps_long
            FROM namevi_map_places m
            JOIN places_pending p ON p.id = m.dila_id
            WHERE m.vn_name_status = 'auto'
            ORDER BY p.id ASC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        conn.close()
        places = []
        for r in rows:
            row = dict(r)
            row['id'] = ensure_long_id(row['id'])
            places.append(row)
        return jsonify({"success": True, "total": total, "limit": limit, "offset": offset, "places": places})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/places_search')
def places_search():
    try:
        q = (request.args.get('q', '') or '').strip()
        cate = (request.args.get('cate', 'admin_place') or '').strip()
        print(f'[places_search] q={q!r} cate={cate!r}', flush=True)
        if not q:
            return jsonify({"success": True, "places": []})
        valid_cates = ('admin_place', 'temple_site', 'dynasty_region', 'mountain', 'river_lake', 'other')
        if cate not in valid_cates:
            cate = 'admin_place'

        cate_case = """
            CASE
                WHEN d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%' THEN 'temple_site'
                WHEN d.note_category LIKE '%山峰%' OR d.note_category LIKE '%山脈%' THEN 'mountain'
                WHEN d.note_category LIKE '%河流%' OR d.note_category LIKE '%湖泊%' OR d.note_category LIKE '%水系%' THEN 'river_lake'
                WHEN d.note_category LIKE '%人文地理區域%' THEN 'dynasty_region'
                WHEN d.note_category LIKE '%自然地理區域%' THEN 'other'
                ELSE 'admin_place'
            END
        """

        conn = get_db_connection()
        like = f'%{q}%'
        q_norm = normalize_text(q)
        like_norm = f'%{q_norm}%' if q_norm else None

        # Phase 0: FTS5 nhanh (cơ chế "gõ mớm" kiểu StarDict) — populate 1 lần, rồi MATCH tên có dấu / không dấu / ID / gõ dở (prefix)
        # Nếu FTS đã chạy mà không khớp => trả về rỗng nhanh (tránh chuỗi LIKE full-scan ~15s gây timeout).
        fts_tried = False
        try:
            ensure_places_search_fts(conn)
            ensure_places_pending_fts(conn)
            fts_tried = True

            # Dựng chuỗi MATCH từ cụ thể → prefix (bắt gõ dở từng ký tự "thiếu lâm t"):
            #   '"thiếu lâm tự"' (phrase) → 'thiếu lâm tự' (token AND) → 'thiếu* lâm* tự*' (prefix AND)
            fts_candidates = [f'"{q.replace(chr(34), chr(34)+chr(34))}"']
            if re.fullmatch(r'[\w\s]+', q, re.UNICODE):
                fts_candidates.append(q)
            prefix_terms = []
            for t in re.split(r'\s+', q.strip())[:6]:
                t = re.sub(r'["*():+\-#@~^&]', '', t)
                if t:
                    prefix_terms.append(t + '*')
            if prefix_terms:
                fts_candidates.append(' '.join(prefix_terms))

            fts_raw_ids = []
            for fq in fts_candidates:
                ids = []
                for table, col in (("places_search_fts", "dila_id"), ("places_pending_fts", "id")):
                    try:
                        cand = conn.execute(
                            f"SELECT {col} AS vid FROM {table} WHERE {table} MATCH ? LIMIT 100",
                            (fq,)
                        ).fetchall()
                        ids.extend(r['vid'] for r in cand if r['vid'])
                    except Exception:
                        continue
                if ids:
                    fts_raw_ids = ids
                    break
            if fts_raw_ids:
                seen = set()
                in_ids = []
                for raw in fts_raw_ids:
                    for form in (str(raw), ensure_long_id(raw)):
                        if form and form not in seen:
                            seen.add(form)
                            in_ids.append(form)
                if in_ids:
                    placeholders = ','.join('?' * len(in_ids))
                    rows = conn.execute(f"""
                        SELECT p.id, p.name_zh,
                               COALESCE(m.name_vi, p.name_vi) AS name_vi,
                               m.vn_name_status
                        FROM places_pending p
                        LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                        LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                        WHERE p.id IN ({placeholders})
                          AND ({cate_case}) = ?
                        ORDER BY
                            CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                            p.id ASC
                        LIMIT 20
                    """, in_ids + [cate, q, like]).fetchall()
                    if rows:
                        conn.close()
                        places = []
                        seen = set()
                        for r in rows:
                            row = dict(r)
                            lid = ensure_long_id(row['id'])
                            if lid in seen:
                                continue
                            seen.add(lid)
                            row['id'] = lid
                            places.append(row)
                        return jsonify({"success": True, "places": places, "mode": "fts"})
        except Exception:
            pass

        # Phase 0.5: query giống ID (PLxxxxxx hoặc số) → tra theo index id chính xác, không quét LIKE.
        # Tránh trường hợp tìm ID trong tab "sai" phải chạy full-scan ~4s rồi trả 0 kết quả.
        q_strip = q.strip()
        m_id = re.match(r'^(?:PL)?(\d{1,12})$', q_strip, re.IGNORECASE)
        if m_id:
            short_id = 'PL' + m_id.group(1)
            long_id = 'PL' + m_id.group(1).zfill(12)
            rows = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       m.vn_name_status
                FROM places_pending p
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                WHERE p.id IN (?, ?)
                  AND ({cate_case}) = ?
                ORDER BY p.id ASC
                LIMIT 20
            """, (short_id, long_id, cate)).fetchall()
            if rows:
                conn.close()
                places = []
                seen = set()
                for r in rows:
                    row = dict(r)
                    lid = ensure_long_id(row['id'])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    row['id'] = lid
                    places.append(row)
                return jsonify({"success": True, "places": places, "mode": "id"})
            conn.close()
            return jsonify({"success": True, "places": [], "mode": "none"})

        # FTS đã chạy nhưng không khớp → trả rỗng nhanh (tránh LIKE full-scan ~15s gây timeout).
        if fts_tried:
            conn.close()
            return jsonify({"success": True, "places": [], "mode": "fts_none"})

        # Phase 1: Direct DB search (with name_vi_norm for diacritics-free)
        # Chỉ chạy khi FTS chưa sẵn sàng (places_search_fts / places_pending_fts lỗi tạo index).
        where_parts = ["(p.id LIKE ? OR p.name_zh LIKE ? OR COALESCE(m.name_vi, p.name_vi) LIKE ?)"]
        params = [like, like, like]
        if like_norm:
            where_parts.append("p.name_vi_norm LIKE ?")
            params.append(like_norm)
        params.append(cate)
        params.append(q)
        params.append(like)

        rows = conn.execute(f"""
            SELECT p.id, p.name_zh,
                   COALESCE(m.name_vi, p.name_vi) AS name_vi,
                   m.vn_name_status
            FROM places_pending p
            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
            LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
            WHERE ({" OR ".join(where_parts)})
              AND ({cate_case}) = ?
            ORDER BY
                CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                p.id ASC
            LIMIT 20
        """, params).fetchall()

        if rows:
            conn.close()
            places = []
            seen = set()
            for r in rows:
                row = dict(r)
                lid = ensure_long_id(row['id'])
                if lid in seen:
                    continue
                seen.add(lid)
                row['id'] = lid
                places.append(row)
            return jsonify({"success": True, "places": places, "mode": "db"})

        # Phase 2: Word-level fallback — try matching individual query words
        # This helps when no place has the full query as name_vi but words match
        q_word_patterns = []
        if q_norm:
            q_words = q_norm.split()
            for w in q_words:
                if len(w) >= 2:
                    q_word_patterns.append(f'%{w}%')

        if q_word_patterns:
            word_conditions = " OR ".join(["(p.name_vi_norm LIKE ? OR COALESCE(m.name_vi, p.name_vi) LIKE ?)" for _ in q_word_patterns])
            word_params = []
            for w in q_word_patterns:
                word_params.extend([w, w])
            word_params.append(cate)
            try:
                rows = conn.execute(f"""
                    SELECT p.id, p.name_zh,
                           COALESCE(m.name_vi, p.name_vi) AS name_vi,
                           m.vn_name_status,
                           (SELECT COUNT(*) FROM places_pending p2
                            LEFT JOIN namevi_map_places m2 ON m2.dila_id = p2.id
                            WHERE p2.id = p.id AND ({word_conditions})) AS match_score
                    FROM places_pending p
                    LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                    LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                    WHERE ({word_conditions})
                      AND ({cate_case}) = ?
                    GROUP BY p.id
                    ORDER BY match_score DESC, p.id ASC
                    LIMIT 20
                """, word_params + word_params + [cate]).fetchall()
            except Exception:
                rows = []

            if rows:
                conn.close()
                places = []
                seen = set()
                for r in rows:
                    row = dict(r)
                    lid = ensure_long_id(row['id'])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    row['id'] = lid
                    places.append(row)
                return jsonify({"success": True, "places": places, "mode": "word_fallback"})

        # Phase 3: Việt → Hán lookup via hanviet_fallback (require multi-char match)
        hv_map = {}
        hv_rows = conn.execute("SELECT ch, hv FROM hanviet_fallback").fetchall()
        for r in hv_rows:
            hv_norm = normalize_text(r['hv'])
            if hv_norm not in hv_map:
                hv_map[hv_norm] = []
            hv_map[hv_norm].append(r['ch'])

        # For each query word, get matching Hán chars. Require at least 3 words matched.
        q_words = q_norm.split() if q_norm else []
        han_groups = []
        for word in q_words:
            if len(word) >= 2 and word in hv_map:
                han_groups.append(hv_map[word])

        if len(han_groups) >= 3:
            # Build AND condition: name_zh must contain at least one Hán char from EACH word
            han_conditions = " AND ".join([f"(p.name_zh LIKE ?)" for _ in han_groups])
            han_params = []
            for grp in han_groups:
                # Try each char from this group (OR within group)
                han_params.append(f'%{grp[0]}%')  # Use first char as pattern
            han_params.append(cate)
            rows = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       m.vn_name_status
                FROM places_pending p
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                WHERE {han_conditions}
                  AND ({cate_case}) = ?
                ORDER BY p.id ASC LIMIT 10
            """, han_params).fetchall()
            if rows:
                conn.close()
                places = []
                seen = set()
                for r in rows:
                    row = dict(r)
                    lid = ensure_long_id(row['id'])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    row['id'] = lid
                    places.append(row)
                return jsonify({"success": True, "places": places, "mode": "han_fallback"})

        conn.close()
        return jsonify({"success": True, "places": [], "mode": "none"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/admin/places')
def admin_places():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    conn = get_db()
    try:
        offset = (page - 1) * per_page
        if search:
            # Search in all name fields and location
            search_pattern = f'%{search}%'
            rows = conn.execute("""
                SELECT * FROM places 
                WHERE name_zh LIKE ? OR name_vi LIKE ? OR name_en LIKE ? OR location LIKE ?
                LIMIT ? OFFSET ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern, per_page, offset)).fetchall()
            
            total = conn.execute("""
                SELECT COUNT(*) FROM places 
                WHERE name_zh LIKE ? OR name_vi LIKE ? OR name_en LIKE ? OR location LIKE ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern)).fetchone()[0]
        else:
            rows = conn.execute("SELECT * FROM places LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        
        return jsonify({"places": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})
    finally:
        conn.close()



@app.route('/api/admin/places/<place_id>', methods=['PUT'])
def admin_update_place(place_id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("""
            UPDATE places SET 
                name = COALESCE(?, name),
                name_vi = COALESCE(?, name_vi),
                gps_lat = COALESCE(?, gps_lat),
                gps_lng = COALESCE(?, gps_lng),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data.get('name'), data.get('name_vi'), data.get('gps_lat'), data.get('gps_lng'), place_id))
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    finally:
        conn.close()



@app.route('/api/admin/places_vps', methods=['GET'])
def admin_places_vps():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    conn = get_db()
    try:
        offset = (page - 1) * per_page
        if search:
            query = "SELECT * FROM places_vps WHERE name_vi LIKE ? OR name_zh LIKE ? OR province LIKE ? LIMIT ? OFFSET ?"
            search_term = f"%{search}%"
            rows = conn.execute(query, (search_term, search_term, search_term, per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_vps WHERE name_vi LIKE ? OR name_zh LIKE ? OR province LIKE ?", 
                            (search_term, search_term, search_term)).fetchone()[0]
        else:
            rows = conn.execute("SELECT * FROM places_vps LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_vps").fetchone()[0]
        return jsonify({"places": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})
    finally:
        conn.close()



@app.route('/api/admin/places_vps/add', methods=['POST'])
def admin_add_place_vps():
    data = request.get_json()
    conn = get_db()
    try:
        import uuid
        place_id = data.get('id') or "VPS-" + uuid.uuid4().hex[:8].upper()
        now = datetime.now().isoformat()
        gps_lat = data.get('gps_lat')
        gps_long = data.get('gps_long')
        
        vals = [
            place_id,
            (data.get('name_zh') or '')[:100],
            (data.get('name_vi') or '')[:100],
            (data.get('name_en') or '')[:100],
            (data.get('location') or '')[:200],
            float(gps_lat) if gps_lat else None,
            float(gps_long) if gps_long else None,
            (data.get('address') or '')[:200],
            (data.get('province') or '')[:50],
            (data.get('country') or 'Vietnam')[:50],
            (data.get('place_type') or 'Chùa')[:50],
            'VPS',
            1.0,
            now,
            now
        ]
        
        conn.execute("""
            INSERT INTO places_vps (id, name_zh, name_vi, name_en, location, gps_lat, gps_long, address, province, country, place_type, source_origin, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vals)
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()



@app.route('/api/admin/places_vps/<place_id>', methods=['DELETE'])
def admin_delete_place_vps(place_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM places_vps WHERE id = ?", (place_id,))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()



@app.route('/api/admin/places_vps/<place_id>', methods=['PUT'])
def admin_update_place_vps(place_id):
    data = request.get_json()
    conn = get_db()
    try:
        now = datetime.now().isoformat()
        conn.execute("""
            UPDATE places_vps SET 
                name_zh = COALESCE(?, name_zh),
                name_vi = COALESCE(?, name_vi),
                name_en = COALESCE(?, name_en),
                location = COALESCE(?, location),
                gps_lat = COALESCE(?, gps_lat),
                gps_long = COALESCE(?, gps_long),
                address = COALESCE(?, address),
                province = COALESCE(?, province),
                country = COALESCE(?, country),
                place_type = COALESCE(?, place_type),
                updated_at = ?
            WHERE id = ?
        """, (
            data.get('name_zh'), data.get('name_vi'), data.get('name_en'), data.get('location'),
            data.get('gps_lat'), data.get('gps_long'), data.get('address'), data.get('province'),
            data.get('country'), data.get('place_type'), now, place_id
        ))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()



@app.route('/api/admin/places_pending', methods=['GET'])
def admin_places_pending():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    no_vi = request.args.get('no_vi', 'false').lower() == 'true'
    conn = get_db_connection()
    try:
        offset = (page - 1) * per_page
        if search:
            query = "SELECT * FROM places_pending WHERE (name_vi LIKE ? OR name_zh LIKE ?) AND (name_vi IS NULL OR name_vi = '') LIMIT ? OFFSET ?"
            search_term = f"%{search}%"
            rows = conn.execute(query, (search_term, search_term, per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi LIKE ? OR name_zh LIKE ?", 
                            (search_term, search_term)).fetchone()[0]
        elif no_vi:
            rows = conn.execute("SELECT * FROM places_pending WHERE name_vi IS NULL OR name_vi = '' LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi IS NULL OR name_vi = ''").fetchone()[0]
        else:
            rows = conn.execute("SELECT * FROM places_pending LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
        return jsonify({"places": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})
    finally:
        conn.close()



@app.route('/api/admin/places_pending/<place_id>', methods=['GET'])
def admin_get_place_pending(place_id):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM places_pending WHERE id = ?", (place_id,)).fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()



@app.route('/api/admin/places_pending/<place_id>/move_to_vps', methods=['POST'])
def admin_move_place_to_vps(place_id):
    data = request.get_json()
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM places_pending WHERE id = ?", (place_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        import uuid
        place_id = data.get('id') or "VPS-" + uuid.uuid4().hex[:8].upper()
        name_vi = data.get('name_vi') or row['name_vi']
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO places_vps (id, name_zh, name_vi, name_en, location, gps_lat, gps_long, address, province, country, place_type, source_origin, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            place_id,
            row['name_zh'],
            name_vi,
            row['name_en'],
            row['location'],
            row['gps_lat'],
            row['gps_long'],
            row['address'],
            row['province'],
            row['country'],
            row['place_type'],
            'VPS',
            1.0,
            now,
            now
        ))
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()




# ===== TAM TANG INTEGRATION ROUTES (T34/T37/T38) =====

@app.route('/daoanh/api/places/<place_id>/eight_four_thousand')
def api_places_eight_four_thousand(place_id):
    # GET /daoanh/api/places/<id>/eight_four_thousand - Return 84000 translations mapped to this place
    import re as _re
    try:
        conn = get_db_connection()
        dila_id, name_zh = _resolve_dila_id(conn, place_id)

        # Get 84000 texts mapped to this place via the place_map table
        mapped_texts = []
        place_mappings = conn.execute(
            "SELECT eft.toh, eft.title_en, eft.title_zh, eft.canon_section, eftm.confidence, eftm.source "
            "FROM eight_four_thousand eft "
            "JOIN eight_four_thousand_place_map eftm ON eft.toh = eftm.toh "
            "WHERE eftm.dila_id = ? "
            "ORDER BY eftm.confidence DESC",
            (dila_id,)
        ).fetchall()

        for row in place_mappings:
            toh = row[0]
            title_en = row[1] if row[1] else ""
            title_zh = row[2] if row[2] else ""
            canon_section = row[3] if row[3] else ""
            confidence = row[4] if row[4] is not None else 0.0
            source = row[5] if row[5] else ""

            mapped_texts.append({
                "toh": toh,
                "title_en": title_en,
                "title_zh": title_zh,
                "canon_section": canon_section,
                "confidence": confidence,
                "source": source
            })

        # Also get CBETA cross-references
        cbeta_refs = []
        if mapped_texts:
            seen_refs = set()
            for text in mapped_texts:
                refs = conn.execute(
                    'SELECT DISTINCT place_id, name_zh, name_vi '
                    "FROM cbeta_catalog_place_fuzzy "
                    "WHERE title_zh LIKE ? OR title_vi LIKE ? LIMIT 5",
                    ("%T" + str(text["toh"]) + "%", "%T" + str(text["toh"]) + "%")
                ).fetchall()
                for r in refs:
                    ref_key = (r[0], r[1], r[2])
                    if ref_key not in seen_refs:
                        seen_refs.add(ref_key)
                        cbeta_refs.append({
                            "place_id": r[0],
                            "name_zh": r[1],
                            "name_vi": r[2]
                        })

        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "dila_id": dila_id,
            "mapped_texts": mapped_texts,
            "cbeta_refs": cbeta_refs,
            "total_mapped": len(mapped_texts)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/daoanh/api/places/<place_id>/kanripo')
def api_places_kanripo(place_id):
    """GET /daoanh/api/places/<id>/kanripo - Return Kanripo texts mapped to this place."""
    try:
        conn = get_db_connection()
        place_mappings = conn.execute(
            """SELECT vm.text_id, vm.dila_id, vm.confidence, vc.title_zh, vc.category, vc.title_en
            FROM kanripo_place_mapping vm
            JOIN kanripo_catalog vc ON vm.text_id = vc.text_id
            WHERE vm.dila_id = ?
            ORDER BY vm.confidence DESC""",
            (place_id,)
        ).fetchall()
        mapped_texts = []
        for row in place_mappings:
            # Indices: 0=vm.text_id, 1=vm.dila_id, 2=vm.confidence, 3=vc.title_zh, 4=vc.category
            mapped_texts.append({
                "text_id": row[0],
                "title_zh": row[3] if len(row) > 3 else "",
                "category": row[4] if len(row) > 4 else "",
                "confidence": row[2] if len(row) > 2 else 0.8
            })
        # Get cached texts
        cached_texts = conn.execute(
            """SELECT text_id, title_zh FROM kanripo_catalog
            WHERE text_id IN (SELECT text_id FROM kanripo_place_mapping)
            LIMIT 5""",
            ()
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "place_id": place_id,
            "mapped_texts": mapped_texts,
            "cached_texts": [{"text_id": r[0], "title_zh": r[1]} for r in cached_texts],
            "total_mapped": len(mapped_texts)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




@app.route('/daoanh/api/places/<place_id>/vri')
def api_places_vri(place_id):
    """GET /daoanh/api/places/<id>/vri - Return VRI Tipitaka texts mapped to this place."""
    import re as _re
    try:
        conn = get_db_connection()

        # Get VRI place mappings for this place_id
        place_mappings = conn.execute(
            """SELECT vpm.*, vtc.nikaya, vtc.title_pali, vtc.reference, vtc.word_count
            FROM vri_place_mapping vpm
            JOIN vri_tipitaka_catalog vtc ON vpm.vri_sutta_id = vtc.id
            WHERE vpm.dila_id = ?
            ORDER BY vpm.confidence DESC""",
            (place_id,)
        ).fetchall()

        mapped_texts = []
        for row in place_mappings:
            mapped_texts.append({
                "nikaya": row[1],
                "sutta_id": row[3] if len(row) > 3 else row[0],
                "title_pali": row[4] if len(row) > 4 else "",
                "title_vi": row[5] if len(row) > 5 else "",
                "title_zh": row[6] if len(row) > 6 else "",
                "reference": row[7] if len(row) > 7 else "",
                "place_name_pali": row[8] if len(row) > 8 else "",
                "context": row[9] if len(row) > 9 else "",
                "confidence": row[10] if len(row) > 10 else 0.8
            })

        # Also get cached text excerpts
        cached_texts = conn.execute(
            """SELECT vct.paragraph_id, vct.text_pali, vct.text_vi, vct.text_zh
            FROM vri_cached_texts vct
            WHERE vct.sutta_id IN (SELECT id FROM vri_tipitaka_catalog)
            LIMIT 5""",
            ()
        ).fetchall()

        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "mapped_texts": mapped_texts,
            "cached_texts": [{"paragraph": r[0], "pali": r[1], "vi": r[2], "zh": r[3]} for r in cached_texts],
            "total_mapped": len(mapped_texts)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




# T37 — Pali Place Reference
@app.route('/daoanh/api/places/<place_id>/pali')
def api_places_pali(place_id):
    """GET /daoanh/api/places/<id>/pali - Pali/Sanskrit references for Indian sacred sites."""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT dila_id, name_zh, name_vi, name_pali, name_skt,
                      sc_uid, sc_uids_more, sc_note_vi, confidence
               FROM pali_place_ref
               WHERE dila_id = ?
               ORDER BY confidence DESC""",
            (place_id,)
        ).fetchall()
        conn.close()

        if not rows:
            return jsonify({"ok": True, "place_id": place_id, "refs": [], "total": 0})

        refs = []
        for r in rows:
            sc_uid = r[5]
            refs.append({
                "dila_id": r[0],
                "name_zh": r[1],
                "name_vi": r[2],
                "name_pali": r[3],
                "name_skt": r[4],
                "sc_uid": sc_uid,
                "sc_uids_more": r[6],
                "sc_note_vi": r[7],
                "confidence": r[8],
                "sc_url_vi": f"https://suttacentral.net/{sc_uid}/vi/minh_chau" if sc_uid else None,
                "sc_url_en": f"https://suttacentral.net/{sc_uid}" if sc_uid else None,
            })

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "refs": refs,
            "total": len(refs)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




# TGS Build 2 — Phase C: Evidence claims endpoint (đa-nguồn, kèm authority + provenance)
@app.route('/daoanh/api/places/<place_id>/claims')
def api_places_claims(place_id):
    """GET /daoanh/api/places/<id>/claims — evidence đa-nguồn cho 1 địa danh.

    Trả về các claim trong entity_claims JOIN data_sources + source_authority,
    kèm source_url / retrieved_at (provenance từ Phase B), xung đột chưa resolve
    (conflict_pending), và bảng xếp hạng authority để UI hiển thị.
    """
    try:
        conn = get_db_connection()

        # Resolve place_id ('PL…' hoặc integer) → entity_id (INT) trong entity_claims
        eid, ref = _resolve_entity_id(conn, place_id)

        # Authority map (source_code → score/order/implemented) để UI xếp hạng
        authority_map = {}
        for r in conn.execute(
            "SELECT source_code, authority_score, precedence_order, implemented FROM source_authority"
        ):
            authority_map[r['source_code']] = {
                'score': r['authority_score'], 'order': r['precedence_order'] or 99,
                'implemented': r['implemented'],
            }

        claims = []
        if eid is not None:
            rows = conn.execute(
                """SELECT c.claim_id, c.claim_type, c.subject, c.predicate, c.object_text,
                          c.source_record_id, c.source_reference,
                          c.authority_role, c.confidence, c.verification_status,
                          c.source_url, c.retrieved_at,
                          d.source_code, d.source_name,
                          sa.authority_score, sa.precedence_order, sa.implemented
                   FROM entity_claims c
                   LEFT JOIN data_sources d      ON d.source_id = c.source_id
                   LEFT JOIN source_authority sa ON sa.source_code = d.source_code
                   WHERE c.entity_id = ?
                   ORDER BY sa.authority_score DESC NULLS LAST, c.confidence DESC""",
                (eid,)
            ).fetchall()
            for r in rows:
                claims.append({
                    "claim_id": r[0],
                    "claim_type": r[1],
                    "subject": r[2],
                    "predicate": r[3],
                    "object_text": r[4],
                    "source_record_id": r[5],
                    "source_reference": r[6],
                    "authority_role": r[7],
                    "confidence": r[8],
                    "verification_status": r[9],
                    "source_url": r[10],
                    "retrieved_at": r[11],
                    "source": {
                        "code": r[12],
                        "name": r[13],
                        "authority_score": r[14],
                        "precedence_order": r[15],
                        "implemented": r[16],
                    },
                })
        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "resolved_entity_id": eid,
            "claims": claims,
            "claims_count": len(claims),
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




# T100-P3 (Batch 5) — JSON-LD export học thuật cho 1 địa danh.
# GET /daoanh/api/places/<id>/export?format=jsonld
# Dùng pth: namespace (nội bộ) + Schema.org @context. Claims → additionalProperty.
# dataset_version từ SHA256 claims (deterministic, stable, ổn định cho citation).
@app.route('/daoanh/api/places/<place_id>/export')
def api_places_export(place_id):
    """T100-P3 (Batch 5) — Xuất JSON-LD học thuật cho địa danh.

    GET /daoanh/api/places/<id>/export?format=jsonld
    Trả JSON-LD: Place + identifier + name(vi/zh) + geo + pth:datasetVersion + additionalProperty (claims).
    Signature = sha256(place_id|claims_full_hash) — ổn định dùng cho trích dẫn học thuật.
    """
    fmt = (request.args.get('format') or 'jsonld').strip().lower()
    if fmt != 'jsonld':
        return jsonify({"ok": False, "error": "Chỉ hỗ trợ format=jsonld hiện tại"}), 400
    try:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT id, name, name_zh, note, latitude, longitude FROM places_dila WHERE id=? LIMIT 1",
            (place_id,)
        ).fetchone()
        dv = _compute_dataset_version(conn, place_id)
        eid, _ = _resolve_entity_id(conn, place_id)
        claim_rows = []
        if eid is not None:
            claim_rows = conn.execute(
                "SELECT claim_type, predicate, object_text, verification_status, confidence, source_reference "
                "FROM entity_claims WHERE entity_id=? ORDER BY claim_id LIMIT 200",
                (eid,)
            ).fetchall()
        conn.close()
        name_vi = (row['name'] if row else None) or place_id
        name_zh = (row['name_zh'] if row else None)
        lat = float(row['latitude']) if (row and row['latitude']) else None
        lng = float(row['longitude']) if (row and row['longitude']) else None
        base = "https://phatphaponline.org"
        props = [
            {
                "@type": "PropertyValue",
                "name": f"{r['claim_type'] or 'claim'}:{r['predicate'] or ''}",
                "value": r['object_text'] or '',
                "description": (
                    f"verification_status:{r['verification_status'] or 'unverified'}"
                    f"|confidence:{r['confidence'] or ''}"
                    f"|source:{r['source_reference'] or ''}"
                ),
            }
            for r in claim_rows
        ]
        jsonld = {
            "@context": {
                "@vocab": "https://schema.org/",
                "pth": "https://phatphaponline.org/daoanh/ns#",
                "dila": "https://dila.ac.tw/authority/",
            },
            "@type": "Place",
            "@id": f"{base}/daoanh/places/{place_id}",
            "identifier": place_id,
            "name": name_vi,
        }
        if name_zh:
            jsonld["alternateName"] = name_zh
        if lat is not None and lng is not None:
            jsonld["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng}
        jsonld["pth:datasetVersion"] = dv.get("version")
        jsonld["pth:claimCount"] = dv.get("claim_count", 0)
        if props:
            jsonld["additionalProperty"] = props
        sig = hashlib.sha256(
            f"{place_id}|{dv.get('full_hash', '')}".encode('utf-8')
        ).hexdigest()
        return jsonify({
            "ok": True,
            "format": "jsonld",
            "place_id": place_id,
            "dataset_version": dv.get("version"),
            "signature": sig,
            "data": jsonld,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




# T100-P2 (Batch 4) — GIÁO LÝ PHÂN ĐÔI: khối "Giáo lý Phật học".
# Route read-only cho khối giáo lý: khái niệm từ doctrine_concept (whitelist, THEMATIC)
# + claims liên quan (entity_claims, badge assertion_level DIRECT/THEMATIC/SCHOLARLY).
# Bảng mới seed qua scripts/etl_t100_batch4.py (additive — CHẠY ETL TRƯỚC).
@app.route('/daoanh/api/places/<place_id>/doctrine')
def api_places_doctrine(place_id):
    """GET /daoanh/api/places/<id>/doctrine — giáo lý Phật học (khối 1 tab GIÁO LÝ).

    Trả về:
      concepts       — doctrine_concept (whitelist 12 khái niệm core, assertion_level THEMATIC)
      related_claims — entity_claims của subject (kèm assertion_level/verification_status/source_code)
      data_status    — số liệu để UI hiển thị trung thực (0/unseeded → empty-state)
    KHÔNG ghi DB. 404 nếu place không resolve. Fallback trống khi bảng doctrine_concept chưa seed.
    Tham số ?level=L1|L2|L3 (T111 persona): L1 server-side clip claims về 'verified' (bổ túc UI).
    """
    try:
        level = (request.args.get('level') or '').upper()
        if level not in ('L1', 'L2', 'L3'):
            level = 'L2'
        conn = get_db_connection()

        # (1) whitelist khái niệm giáo lý — chủ đề truy vấn (không phụ thuộc entity)
        concepts = []
        try:
            has_doctrine = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='doctrine_concept'"
            ).fetchone()
            if has_doctrine:
                for r in conn.execute(
                    "SELECT name_vi, name_zh, pth_uri, definition_vi, assertion_level, "
                    "related_entities, updated_at FROM doctrine_concept "
                    "WHERE name_vi IS NOT NULL ORDER BY id"
                ):
                    concepts.append({
                        "name_vi": r["name_vi"], "name_zh": r["name_zh"] or "",
                        "pth_uri": r["pth_uri"] or "", "definition_vi": r["definition_vi"] or "",
                        "assertion_level": r["assertion_level"] or "THEMATIC",
                        "related_entities": (r["related_entities"] or "").split(','),
                        "updated_at": r["updated_at"] or "",
                    })
        except Exception:
            concepts = []

        # (2) claims liên quan của subject (cùng pattern api_places_claims)
        eid, ref = _resolve_entity_id(conn, place_id)
        related_claims = []
        if eid is not None:
            try:
                rows = conn.execute(
                    """SELECT c.claim_id, c.claim_type, c.subject, c.predicate, c.object_text,
                              c.source_reference, c.authority_role, c.confidence,
                              c.verification_status, c.assertion_level,
                              d.source_code, d.source_name
                       FROM entity_claims c
                       LEFT JOIN data_sources d ON d.source_id = c.source_id
                       WHERE c.entity_id = ?
                       ORDER BY CASE c.assertion_level WHEN 'DIRECT' THEN 0
                                    WHEN 'THEMATIC' THEN 1 WHEN 'SCHOLARLY' THEN 2 ELSE 3 END,
                                c.claim_type, c.claim_id
                       LIMIT 100""",
                    (eid,)
                ).fetchall()
            except Exception:
                rows = []
            for r in rows:
                related_claims.append({
                    "claim_id": r["claim_id"], "claim_type": r["claim_type"],
                    "subject": r["subject"], "predicate": r["predicate"],
                    "object_text": r["object_text"], "source_reference": r["source_reference"],
                    "authority_role": r["authority_role"], "confidence": r["confidence"],
                    "verification_status": r["verification_status"],
                    "assertion_level": r["assertion_level"] or None,
                    "source_code": r["source_code"] or "",
                    "source_name": r["source_name"] or "",
                })
        # T111 persona: L1 = chỉ claim đã xét duyệt 'verified' (bổ túc UI-side gating).
        if level == 'L1':
            related_claims = [c for c in related_claims
                              if (c.get('verification_status') or '') == 'verified']
        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "resolved_entity_id": eid,
            "persona_level": level,
            "concepts": concepts,
            "related_claims": related_claims,
            "data_status": {
                "concepts": {
                    "total": len(concepts),
                    "level": "whitelist doctrine_concept ('THEMATIC')",
                },
                "related_claims": {
                    "total": len(related_claims),
                    "by_level": {
                        lvl: sum(1 for c in related_claims if c["assertion_level"] == lvl)
                        for lvl in ("DIRECT", "THEMATIC", "SCHOLARLY")
                    },
                    "note": ("entity_claims toàn kho 447,885 claim — 100% 'unverified'; "
                             "assertion_level chưa gán khi claim chưa qua xét duyệt (P3)."),
                },
            },
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ---------------------------------------------------------------------------
# T484: tab Catalog tên Kinh (dila_catalog_works) — đối chiếu nhiều nguồn + Admin pass.
# Bản phiên âm Claude nằm ở title_vi (giữ nguyên). Admin pass lưu trong vi_json.admin_pass
# và đặt vi_status='admin_passed' (cột có sẵn, không đổi schema).
# ---------------------------------------------------------------------------
_T484_GEMINI_DRAFT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'sessions',
                                  '2026-10-28', 'catalog', 't484_gemini_titles_draft.jsonl')
_T484_HVDIC_DRAFT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'sessions',
                                 '2026-10-28', 'catalog', 't484_hvdic_titles.jsonl')


def _t484_base_zh(title):
    """Tên Hán gốc: bỏ phần chú thích quyển và tác giả."""
    return re.split(r'\s*[\(（]', title or '', maxsplit=1)[0].strip()


def _t484_mlk_index(conn):
    """Mục Lục Nguyễn Minh Tiến: tên Hán gốc -> danh sách tên Việt."""
    idx = {}
    for title_vi, title_zh in conn.execute(
            "SELECT title_vi, title_zh FROM cbeta_catalog_vn WHERE title_zh IS NOT NULL AND title_zh <> ''"):
        idx.setdefault(_t484_base_zh(title_zh), []).append(title_vi)
    return idx


def _t484_draft_index(path, field):
    """File nháp JSONL: cbeta_id -> field. Thiếu file thì trả rỗng."""
    idx = {}
    if not os.path.exists(path):
        return idx
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get(field):
                idx[row['cbeta_id']] = row[field]
    return idx


def _t484_vi_json(raw):
    try:
        return json.loads(raw) if raw else {}
    except ValueError:
        return {}


@app.route('/daoanh/api/admin/catalog-works', methods=['GET'])
def api_admin_catalog_works():
    """GET /daoanh/api/admin/catalog-works?q=&page=&size= — đối chiếu tên Kinh theo từng tác phẩm DILA."""
    try:
        q = (request.args.get('q') or '').strip()
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1
        try:
            size = max(1, min(200, int(request.args.get('size', 50))))
        except ValueError:
            size = 50
        conn = get_db_connection()
        where, params = '', []
        if q:
            where = ' WHERE cbeta_id LIKE ? OR title_zh LIKE ?'
            params = [f'%{q}%', f'%{q}%']
        total = conn.execute(f'SELECT COUNT(*) FROM dila_catalog_works{where}', params).fetchone()[0]
        rows = conn.execute(
            f'SELECT cbeta_id, title_zh, title_vi, vi_status, vi_json FROM dila_catalog_works{where} '
            f'ORDER BY cbeta_id LIMIT ? OFFSET ?', params + [size, (page - 1) * size]).fetchall()
        mlk = _t484_mlk_index(conn)
        gemini = _t484_draft_index(_T484_GEMINI_DRAFT, 'gemini_vi')
        hvdic = _t484_draft_index(_T484_HVDIC_DRAFT, 'hvdic_vi')
        items = []
        for r in rows:
            base = _t484_base_zh(r['title_zh'])
            vj = _t484_vi_json(r['vi_json'])
            lex = conn.execute("SELECT COUNT(*) FROM lexicon WHERE term LIKE ?", (f'%({base})%',)).fetchone()[0]
            items.append({
                'cbeta_id': r['cbeta_id'],
                'title_zh': r['title_zh'],
                'phien_am_claude': r['title_vi'],
                'gemini_free': gemini.get(r['cbeta_id']),
                'hvdic': hvdic.get(r['cbeta_id']),
                'muc_luc_nmt': mlk.get(base, []),
                'lexicon_hits': lex,
                'admin_pass': vj.get('admin_pass'),
                'vi_status': r['vi_status'],
            })
        conn.close()
        return jsonify({'ok': True, 'total': total, 'page': page, 'size': size,
                        'pages': max(1, (total + size - 1) // size), 'items': items})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/daoanh/api/admin/catalog-works/<cbeta_id>/pass', methods=['POST'])
def api_admin_catalog_work_pass(cbeta_id):
    """POST — Admin pass một tên Kinh. Body tùy chọn {name_vi}; không có thì lấy bản phiên âm Claude."""
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'unauthorized — thiếu hoặc sai session token'}), 403
    try:
        data = request.json or {}
        conn = get_db_connection()
        row = conn.execute('SELECT title_vi, vi_json FROM dila_catalog_works WHERE cbeta_id = ?',
                           (cbeta_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({'ok': False, 'error': f'Không có tác phẩm {cbeta_id} trong dila_catalog_works'}), 404
        name_vi = (data.get('name_vi') or row['title_vi'] or '').strip()
        if not name_vi:
            conn.close()
            return jsonify({'ok': False, 'error': 'Tên Việt rỗng — không thể Pass'}), 400
        import datetime as _dt484
        vj = _t484_vi_json(row['vi_json'])
        vj['admin_pass'] = {'name_vi': name_vi, 'editor': _t427_session_email(token) or '',
                            'at': _dt484.datetime.now().isoformat(timespec='seconds')}
        conn.execute("UPDATE dila_catalog_works SET vi_status = 'admin_passed', vi_json = ? WHERE cbeta_id = ?",
                     (json.dumps(vj, ensure_ascii=False), cbeta_id))
        conn.commit()
        conn.close()
        return jsonify({'ok': True, 'cbeta_id': cbeta_id, 'admin_pass': vj['admin_pass']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# T484 (bước Gemini): dịch từng tên Kinh bằng Gemini free, theo yêu cầu của Admin.
# Mỗi lần gọi một tên, ghi vào file nháp (không ghi DB). Cần session admin vì tốn hạn mức.
# ---------------------------------------------------------------------------
_T484_GEMINI_MODEL = 'gemini-3.8-flash'
_T484_GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
_t484_gemini_lock = _t148_threading.Lock()


def _t484_gemini_title(title_zh):
    """Gọi Gemini free dịch một tên Kinh. Trả về (vi, lỗi); đúng một trong hai là None."""
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key:
        return None, 'Thiếu GEMINI_API_KEY trong .env'
    prompt = ('Bạn là chuyên gia Phật học. Dịch tên bộ kinh Hán sau sang tiếng Việt, '
              'giữ thuật ngữ Phật học chuẩn; tên riêng giữ theo phiên âm Hán-Việt. '
              'Trả về JSON dạng {"vi": "..."}, không thêm chú thích.\n\nTên: ' + title_zh)
    body = {'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.1, 'responseMimeType': 'application/json'}}
    try:
        resp = requests.post(_T484_GEMINI_URL.format(model=_T484_GEMINI_MODEL),
                             headers={'x-goog-api-key': key, 'Content-Type': 'application/json'},
                             json=body, timeout=60)
    except requests.RequestException as e:
        return None, f'Lỗi mạng tới Gemini: {type(e).__name__}'
    if resp.status_code == 429:
        return None, 'Gemini hết hạn mức (429). Thử lại sau.'
    if resp.status_code != 200:
        return None, f'Gemini trả HTTP {resp.status_code}. Thử lại sau.'
    try:
        text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        vi = str(json.loads(text).get('vi', '')).strip()
    except (KeyError, IndexError, ValueError, AttributeError):
        return None, 'Phản hồi Gemini không đúng cấu trúc'
    if not vi:
        return None, 'Gemini trả về tên rỗng'
    return vi, None


@app.route('/daoanh/api/admin/catalog-works/<cbeta_id>/gemini', methods=['POST'])
def api_admin_catalog_work_gemini(cbeta_id):
    """POST /daoanh/api/admin/catalog-works/<cbeta_id>/gemini — Gemini free dịch 1 tên Kinh, ghi nháp JSONL."""
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'unauthorized — thiếu hoặc sai session token'}), 403
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT title_zh FROM dila_catalog_works WHERE cbeta_id = ?', (cbeta_id,)).fetchone()
        conn.close()
        if not row or not row['title_zh']:
            return jsonify({'ok': False, 'error': 'Không có tên Hán cho mã này'}), 404
        zh = _t484_base_zh(row['title_zh'])
        vi, err = _t484_gemini_title(zh)
        if err:
            return jsonify({'ok': False, 'error': err}), 502
        import datetime as _dt484g
        rec = {'cbeta_id': cbeta_id, 'title_zh': zh, 'gemini_vi': vi, 'model': _T484_GEMINI_MODEL,
               'ts': _dt484g.datetime.now().isoformat(timespec='seconds')}
        with _t484_gemini_lock:
            os.makedirs(os.path.dirname(_T484_GEMINI_DRAFT), exist_ok=True)
            with open(_T484_GEMINI_DRAFT, 'a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        return jsonify({'ok': True, 'cbeta_id': cbeta_id, 'gemini_vi': vi})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
