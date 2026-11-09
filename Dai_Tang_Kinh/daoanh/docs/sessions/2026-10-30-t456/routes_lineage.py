"""Route nhom lineage: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""
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
from core import BASE_DIR, DATA_DIR, SQLITE_DB, TAM_DICH_SUFFIX, TTL_OLD_DIR, _ensure_place_person_link_table, _ensure_vietnamese, _get_person_suggest_cache, _get_work_suggest_cache, _hanviet_charwise_translit, _iso_now, _nexus_title_for_sigla, _normalize_charwise_caps, _ok_hanviet_name, _pali_sanskrit_lookup, _resolve_dila_id, _resolve_entity_id, _t112_record_gap, _t120_query_wikidata, _t128_parse_relation_ref, _t138_edge_assertions, _t148_get_extra, _t158_neighbors_consensus, _t166_has_col, _t172_load_hv, _t360_classify_name_vi_source, _t360_resolve_person_name_vi_source, _t412_resolve_display_name, _t426_neighbors_view, _t73_get_active_rules, _t73_rules_version, _t73_source_hash, _t73_style_lock, _t75_entity_info, _t75_search_wikipedia, _t75_summarize, _t86_origin_place, _t86_parse_ref_passage, _t86_person_conflict, _t86_person_info, _t86_resolve_display_name, _zen_ensure_review_table, _zen_suggest, app, calculate_edge_color_and_divergence, check_lineage_conflict, ensure_long_id, ensure_places_pending_fts, get_cbeta_conn, get_chronology_conn, get_db, get_dila_data, get_marcus_data, normalize_text, parse_dila_district, verify_session




@app.route('/daoanh/api/admin/zenlineage/candidates')
def zenlineage_candidates():
    """GET /daoanh/api/admin/zenlineage/candidates?page=&limit=&filter=all|pending|approved|rejected&q=
    Liệt kê candidate pool từ source_staging master + trạng thái review HITL + gợi ý DILA."""
    try:
        conn = get_db_connection()
        try:
            _zen_ensure_review_table(conn)
            page = max(1, int(request.args.get('page', 1)))
            limit = min(max(1, int(request.args.get('limit', 25))), 200)
            flt = (request.args.get('filter', 'all') or 'all').strip()
            q = (request.args.get('q', '') or '').strip()
            offset = (page - 1) * limit

            where = ["s.row_type='master'"]
            params = []
            if flt in ('approved', 'rejected', 'pending'):
                if flt == 'pending':
                    where.append("r.status IS NULL")
                else:
                    where.append("r.status=?")
                    params.append(flt)
            if q:
                where.append("(s.primary_name LIKE ? OR s.source_entity_id LIKE ?)")
                qq = f'%{q}%'
                params += [qq, qq]
            wsql = ' AND '.join(where)
            total = conn.execute(
                f"SELECT COUNT(*) FROM source_staging s "
                f"LEFT JOIN zenlineage_review r ON r.source_entity_id=s.source_entity_id "
                f"WHERE {wsql}", params).fetchone()[0]
            rows = conn.execute(
                f"""SELECT s.source_entity_id, s.primary_name, s.school_slug, s.extra_json,
                           r.status, r.dila_person_id, r.confidence, r.editor, r.note
                    FROM source_staging s
                    LEFT JOIN zenlineage_review r ON r.source_entity_id=s.source_entity_id
                    WHERE {wsql} ORDER BY s.source_entity_id LIMIT ? OFFSET ?""",
                params + [limit, offset]).fetchall()
            items = []
            for r in rows:
                try:
                    extra = json.loads(r['extra_json'] or '{}')
                except Exception:
                    extra = {}
                items.append({
                    'slug': r['source_entity_id'],
                    'name': r['primary_name'],
                    'school': r['school_slug'],
                    'birth_year': extra.get('birth_year'),
                    'death_year': extra.get('death_year'),
                    'status': r['status'] or 'pending',
                    'dila_person_id': r['dila_person_id'],
                    'confidence': r['confidence'],
                    'editor': r['editor'],
                    'note': r['note'],
                    'suggestions': _zen_suggest(conn, r['primary_name']),
                })
            return jsonify({'ok': True, 'total': total, 'page': page, 'limit': limit,
                            'filter': flt, 'items': items})
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"zenlineage_candidates error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/zenlineage/candidate/<slug>/approve', methods=['POST'])
def zenlineage_candidate_approve(slug):
    """POST /daoanh/api/admin/zenlineage/candidate/<slug>/approve  body: {dila_id, confidence, editor}
    Approve mapping zen master → DILA person. Ghi zenlineage_review (approved) +
    entity_source_ids (verified=1, entity_id=entity_hub of DILA person) + en_audit_log."""
    try:
        body = request.get_json(silent=True) or {}
        dila_id = (body.get('dila_id') or '').strip()
        confidence = float(body.get('confidence') or 0.0)
        editor = (body.get('editor') or 'admin').strip()
        if not dila_id:
            return jsonify({'ok': False, 'error': 'Thiếu dila_id'}), 400
        conn = get_db_connection()
        try:
            _zen_ensure_review_table(conn)
            exists = conn.execute(
                "SELECT 1 FROM source_staging WHERE source_code='ZENLINEAGE' AND row_type='master' "
                "AND source_entity_id=?", (slug,)).fetchone()
            if not exists:
                return jsonify({'ok': False, 'error': f'Không thấy zen master `{slug}` trong staging'}), 404
            person = conn.execute(
                "SELECT p.id AS dila_id, p.name_vi, p.name_zh, "
                "  (SELECT eh.entity_id FROM entity_hub eh "
                "   WHERE eh.entity_type='PERSON' AND eh.canonical_label=p.id LIMIT 1) AS entity_hub_id "
                "FROM people p WHERE p.id=?", (dila_id,)).fetchone()
            if not person:
                return jsonify({'ok': False, 'error': f'DILA person `{dila_id}` không tồn tại'}), 404
            now = _iso_now()
            entity_hub_id = person['entity_hub_id']
            if entity_hub_id is None:
                # entity_hub thiếu row PERSON → tạo (additive, entity_hub là DERIVED registry)
                cur = conn.execute(
                    "INSERT OR IGNORE INTO entity_hub (entity_type, canonical_label, status, created_at, updated_at) "
                    "VALUES ('PERSON', ?, 'active', ?, ?)", (dila_id, now, now))
                entity_hub_id = conn.execute(
                    "SELECT entity_id FROM entity_hub WHERE entity_type='PERSON' AND canonical_label=?", (dila_id,)).fetchone()[0]
            # 1) quyết định review
            conn.execute(
                "INSERT OR REPLACE INTO zenlineage_review "
                "(source_entity_id, status, dila_person_id, entity_hub_id, confidence, editor, note, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (slug, 'approved', dila_id, entity_hub_id, confidence, editor, None, now, now))
            # 2) entity_source_ids (entity_id thật, verified=1) — idempotent: xóa row cũ của slug rồi insert mới
            conn.execute(
                "DELETE FROM entity_source_ids WHERE source='ZENLINEAGE' AND source_entity_id=?", (slug,))
            conn.execute(
                """INSERT INTO entity_source_ids
                   (entity_id, source, source_entity_id, source_label, match_status, confidence,
                    verified, verification_note, created_at, updated_at)
                   VALUES (?, 'ZENLINEAGE', ?, ?, 'approved', ?, 1, ?, ?, ?)""",
                (entity_hub_id, slug, person['name_vi'] or person['name_zh'] or slug,
                 confidence, f'zen:{slug}→{dila_id}', now, now))
            # 3) audit
            conn.execute(
                "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (f'zenlineage:{slug}', 'hitl_approve', 'dila_person_id', None, dila_id, editor, now))
            conn.commit()
            return jsonify({'ok': True, 'slug': slug, 'dila_id': dila_id,
                            'entity_hub_id': entity_hub_id, 'status': 'approved'})
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"zenlineage_candidate_approve error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/zenlineage/candidate/<slug>/reject', methods=['POST'])
def zenlineage_candidate_reject(slug):
    """POST /daoanh/api/admin/zenlineage/candidate/<slug>/reject  body: {note, editor}
    Reject: chi ghi zenlineage_review (rejected) — không động entity_source_ids."""
    try:
        body = request.get_json(silent=True) or {}
        note = (body.get('note') or '').strip()[:500]
        editor = (body.get('editor') or 'admin').strip()
        conn = get_db_connection()
        try:
            _zen_ensure_review_table(conn)
            now = _iso_now()
            conn.execute(
                "INSERT OR REPLACE INTO zenlineage_review "
                "(source_entity_id, status, dila_person_id, entity_hub_id, confidence, editor, note, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (slug, 'rejected', None, None, None, editor, note or None, now, now))
            conn.execute(
                "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (f'zenlineage:{slug}', 'hitl_reject', 'status', None, 'rejected', editor, now))
            conn.commit()
            return jsonify({'ok': True, 'slug': slug, 'status': 'rejected'})
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"zenlineage_candidate_reject error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/zenlineage/candidate/<slug>/unset', methods=['POST'])
def zenlineage_candidate_unset(slug):
    """POST /daoanh/api/admin/zenlineage/candidate/<slug>/unset — hủy quyết định (về pending).
    Xóa zenlineage_review + entity_source_ids ZENLINEAGE của slug (verified=1)."""
    try:
        conn = get_db_connection()
        try:
            _zen_ensure_review_table(conn)
            now = _iso_now()
            conn.execute("DELETE FROM zenlineage_review WHERE source_entity_id=?", (slug,))
            conn.execute(
                "DELETE FROM entity_source_ids WHERE source='ZENLINEAGE' AND source_entity_id=?", (slug,))
            conn.execute(
                "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                ('zenlineage:' + slug, 'hitl_unset', 'status', None, 'pending', 'admin', now))
            conn.commit()
            return jsonify({'ok': True, 'slug': slug, 'status': 'pending'})
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"zenlineage_candidate_unset error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/zenlineage/stats')
def zenlineage_stats():
    """GET /daoanh/api/admin/zenlineage/stats — tổng hợp candidate pool + review."""
    try:
        conn = get_db_connection()
        try:
            _zen_ensure_review_table(conn)
            total = conn.execute(
                "SELECT COUNT(*) FROM source_staging WHERE source_code='ZENLINEAGE' AND row_type='master'").fetchone()[0]
            by_status = {}
            for r in conn.execute(
                    "SELECT COALESCE(review.status,'pending') s, COUNT(*) c FROM source_staging st "
                    "LEFT JOIN zenlineage_review review ON review.source_entity_id=st.source_entity_id "
                    "WHERE st.source_code='ZENLINEAGE' AND st.row_type='master' GROUP BY s"):
                by_status[r['s']] = r['c']
            by_tier = {}
            for r in conn.execute(
                    "SELECT tier, COUNT(*) c FROM source_staging "
                    "WHERE source_code='ZENLINEAGE' AND row_type='transmission' GROUP BY tier"):
                by_tier[r['tier']] = r['c']
            approved = by_status.get('approved', 0)
            return jsonify({'ok': True, 'total': total, 'approved': approved,
                            'by_status': by_status, 'by_tier': by_tier,
                            'transmissions': conn.execute(
                                "SELECT COUNT(*) FROM source_staging WHERE source_code='ZENLINEAGE' AND row_type='transmission'").fetchone()[0]})
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"zenlineage_stats error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500




# (Endpoint cũ /daoanh/api/passage/<int:passage_id>/translate ĐÃ BỊ XOÁ — trùng route
#  với /daoanh/api/passage/<passage_id>/translate. Hành vi giữ nguyên trong legacy
#  fallback của unified route: Groq toàn passage → passage.vi_text / GET cached.)


@app.route('/daoanh/api/entity/<entity_id>/related', methods=['GET'])
def api_entity_related(entity_id):
    """GET /daoanh/api/entity/<id>/related — Quan Hệ panel data.
    Returns:
      places  — địa danh co-mentioned qua passage_entity
      persons — thiền sư từ place_person_link (curated) + passage_entity (canonical)
      texts   — danh sách tác phẩm từ cbeta_text_catalog mapped tới entity
    """
    try:
        conn = get_db_connection()
        dila_id, _ = _resolve_dila_id(conn, entity_id)
        canonical_id = dila_id or entity_id

        # ── 1. Co-mentioned PLACES qua passage_entity ───────────────────────
        place_rows = conn.execute("""
            SELECT pe2.entity_id, COUNT(*) AS mentions
            FROM passage_entity pe1
            JOIN passage_entity pe2 ON pe1.passage_id = pe2.passage_id
            WHERE pe1.entity_id IN (?, ?)
              AND pe2.entity_id LIKE 'PL%'
              AND pe2.entity_id NOT IN (?, ?)
            GROUP BY pe2.entity_id
            ORDER BY mentions DESC LIMIT 15
        """, (entity_id, canonical_id, entity_id, canonical_id)).fetchall()

        places = []
        _seen_place_norm = set()  # dedup: passage_entity stores both PL046734 and PL000000046734
        for r in place_rows:
            eid = r['entity_id']
            # normalize: strip leading zeros padding to get short DILA id
            short = eid.replace('PL000000', 'PL') if eid.startswith('PL000000') else eid
            if short in _seen_place_norm:
                continue
            _seen_place_norm.add(short)
            nm = conn.execute(
                "SELECT name_zh, name_vi FROM namevi_map_places WHERE dila_id IN (?, ?) LIMIT 1",
                (eid, short)
            ).fetchone()
            places.append({
                'entity_id': short,
                'name_zh': nm['name_zh'] if nm else eid,
                'name_vi': nm['name_vi'] if nm else None,
                'mentions': r['mentions'],
                'source': 'canonical'
            })

        # ── 2a. Persons — CURATED (place_person_link) ───────────────────────
        _ensure_place_person_link_table(conn)
        curated_rows = conn.execute("""
            SELECT l.person_id, l.relation_type, p.name_zh, p.name_vi, p.dynasty
            FROM place_person_link l JOIN people p ON p.id = l.person_id
            WHERE l.place_id IN (?, ?)
            ORDER BY l.created_at ASC
        """, (entity_id, canonical_id)).fetchall()

        persons = []
        curated_ids = set()
        for r in curated_rows:
            curated_ids.add(r['person_id'])
            persons.append({
                'entity_id': r['person_id'],
                'name_zh': r['name_zh'], 'name_vi': r['name_vi'],
                'dynasty': r['dynasty'],
                'relation_type': r['relation_type'] or 'liên quan',
                'source': 'curated', 'mentions': None
            })

        # ── 2b. Persons — CANONICAL (passage_entity A-prefix) ───────────────
        person_rows = conn.execute("""
            SELECT pe2.entity_id, COUNT(*) AS mentions
            FROM passage_entity pe1
            JOIN passage_entity pe2 ON pe1.passage_id = pe2.passage_id
            WHERE pe1.entity_id IN (?, ?)
              AND pe2.entity_id LIKE 'A%'
            GROUP BY pe2.entity_id
            ORDER BY mentions DESC LIMIT 12
        """, (entity_id, canonical_id)).fetchall()

        for r in person_rows:
            if r['entity_id'] in curated_ids:
                continue
            nm = conn.execute(
                "SELECT name_zh, name_vi, dynasty FROM people WHERE id = ? LIMIT 1",
                (r['entity_id'],)
            ).fetchone()
            persons.append({
                'entity_id': r['entity_id'],
                'name_zh': nm['name_zh'] if nm else r['entity_id'],
                'name_vi': nm['name_vi'] if nm else None,
                'dynasty': nm['dynasty'] if nm else None,
                'relation_type': 'cùng đề cập trong kinh',
                'source': 'canonical', 'mentions': r['mentions']
            })

        # ── 3. Texts — từ cbeta_text_catalog mapped tới entity ──────────────
        texts = []
        try:
            text_rows = conn.execute("""
                SELECT ct.catalog_id, ct.title_zh, ct.title_vi, ct.era_vi,
                       ct.author_vi, em.mapping_status, em.mapping_note
                FROM entity_text_map em
                JOIN cbeta_text_catalog ct ON ct.catalog_id = em.catalog_id
                WHERE em.entity_id IN (?, ?)
                ORDER BY em.mapping_status DESC, ct.catalog_id ASC LIMIT 20
            """, (entity_id, canonical_id)).fetchall()
            texts = [dict(r) for r in text_rows]
        except Exception:
            pass

        conn.close()
        return jsonify({
            'ok': True,
            'entity_id': entity_id,
            'places': places,
            'persons': persons,
            'texts': texts
        })

    except Exception as e:
        app.logger.error(f'api_entity_related error: {e}')
        return jsonify({'ok': False, 'error': str(e)}), 500



@app.route('/daoanh/api/nexus/find')
def api_nexus_find():
    """GET /daoanh/api/nexus/find — T16 Nexus Points query.

    Params: place=PL..., person=A..., year_from=int, year_to=int, min_conf=float (default 0.7)
    Returns: {nexus_points: [{person_dila_id, place_dila_id, source_book, cbeta_ref, confidence,
              person_name_vi, person_name_zh, place_name_vi, place_name_zh}, ...]}
    """
    try:
        place  = request.args.get('place', '').strip()
        person = request.args.get('person', '').strip()
        year_from = request.args.get('year_from', type=int)
        year_to   = request.args.get('year_to',   type=int)
        min_conf  = request.args.get('min_conf',  default=0.7, type=float)

        clauses, params = ["ne.confidence >= ?"], [min_conf]
        if place:  clauses.append("ne.place_dila_id = ?");  params.append(place)
        if person: clauses.append("ne.person_dila_id = ?"); params.append(person)
        if year_from is not None: clauses.append("ne.event_year >= ?"); params.append(year_from)
        if year_to   is not None: clauses.append("ne.event_year <= ?"); params.append(year_to)

        where = " AND ".join(clauses)
        conn = get_db_connection()
        rows = conn.execute(f"""
            SELECT ne.person_dila_id, ne.place_dila_id, ne.source_book,
                   ne.passage_id, ne.confidence, ne.event_year, ne.event_label,
                   p.name_vi  AS pname_vi,  p.name_zh  AS pname_zh,
                   pl.name_vi AS plname_vi, pl.name_zh AS plname_zh
            FROM nexus_events ne
            LEFT JOIN people      p  ON p.id  = ne.person_dila_id
            LEFT JOIN places      pl ON pl.id = ne.place_dila_id
            WHERE {where}
            ORDER BY ne.confidence DESC
            LIMIT 100
        """, params).fetchall()
        conn.close()

        result = [{
            "person_dila_id": r[0], "place_dila_id": r[1],
            "source_book": r[2], "cbeta_ref": r[3],
            "confidence": r[4], "event_year": r[5], "event_label": r[6],
            "person_name_vi": r[7], "person_name_zh": r[8],
            "place_name_vi": r[9], "place_name_zh": r[10]
        } for r in rows]
        return jsonify({"ok": True, "count": len(result), "nexus_points": result})
    except Exception as e:
        app.logger.error(f"api_nexus_find error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/monk/<dila_id>/graph')
def api_monk_graph(dila_id):
    """GET /daoanh/api/monk/<dila_id>/graph — Person-entity counterpart of
    /daoanh/api/places/<id>/graph (T16/T17 realization, Marcus lineage on Đồ Thị tab).

    Same nodes/edges shape as the place graph so places.html can render both with one
    vis-network renderer. Data is the already-verified Marcus SNA link (marcus_people_link,
    exact DILA-ID match, additive — see T04); every edge carries the real CBETA citation
    `ref` from marcus_networks, so this satisfies the "100% nguồn dẫn" bar without any
    fuzzy/regex guessing.
    """
    conn = get_db_connection()
    try:
        person = conn.execute(
            "SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if not person:
            return jsonify({"ok": False, "error": "person not found"}), 404
        # marcus_reference.label holds canonical dharma name (e.g. 慧能, 菩提達磨).
        # people.name_zh often stores DILA authority form: posthumous title, epithet, or
        # temple name (e.g. 大鑒真空普覺圓明禪師, 壁觀婆羅門, 靖居) which is wrong for display.
        marc_ref = conn.execute(
            "SELECT label, label_vi FROM marcus_reference WHERE node_id = ?", (dila_id,)
        ).fetchone()
        canonical_zh = (marc_ref['label'] if marc_ref else None) or person['name_zh']
        # T51f: label_vi now has proper Hán-Việt from marcus_reference (e.g. 菩提達磨→Bồ Đề Đạt Ma)
        # Prefer: marcus_reference.label_vi > people.name_vi > canonical_zh
        marc_label_vi = marc_ref['label_vi'] if marc_ref else None
        if marc_label_vi and marc_label_vi != canonical_zh:
            canonical_vi = marc_label_vi
        else:
            canonical_vi = person['name_vi'] or canonical_zh
        center = {"id": dila_id, "label": canonical_vi, "label_zh": canonical_zh,
                  "dila_stored_name": person['name_zh']}

        link = conn.execute(
            "SELECT marcus_node_id FROM marcus_people_link WHERE person_id = ?", (dila_id,)
        ).fetchone()
        nodes, edges = [], []
        if link:
            node_id = link['marcus_node_id']
            teachers = conn.execute("""
                SELECT teacher_id AS id, teacher_label AS label, relation_type, ref
                FROM marcus_networks WHERE student_id = ?
            """, (node_id,)).fetchall()
            students = conn.execute("""
                SELECT student_id AS id, student_label AS label, relation_type, ref
                FROM marcus_networks WHERE teacher_id = ?
            """, (node_id,)).fetchall()

            # Batch lookup label_vi for all neighbor nodes from marcus_reference
            neighbor_ids = [t['id'] for t in teachers] + [s['id'] for s in students]
            label_vi_map = {}
            if neighbor_ids:
                placeholders = ','.join('?' * len(neighbor_ids))
                for r in conn.execute(
                    f"SELECT node_id, label, label_vi FROM marcus_reference WHERE node_id IN ({placeholders})",
                    neighbor_ids
                ).fetchall():
                    vi = r['label_vi'] if r['label_vi'] and r['label_vi'] != r['label'] else None
                    label_vi_map[r['node_id']] = vi or r['label']

            for t in teachers:
                vi = label_vi_map.get(t['id'], t['label'])
                nodes.append({"id": t['id'], "label": vi, "label_zh": t['label'],
                              "role": "teacher", "group": "person", "navigable": True})
                edges.append({"from": t['id'], "to": dila_id, "label": "thầy của", "ref": t['ref']})
            for s in students:
                vi = label_vi_map.get(s['id'], s['label'])
                nodes.append({"id": s['id'], "label": vi, "label_zh": s['label'],
                              "role": "student", "group": "person", "navigable": True})
                edges.append({"from": dila_id, "to": s['id'], "label": "truyền cho", "ref": s['ref']})

            # Đồng môn (colleague_of) — DERIVED từ Marcus isTeacherOf: các student khác
            # cùng teacher với node đang xem. KHÔNG phải dữ liệu gốc — đánh dấu derived rõ ràng
            # để nghiên cứu tông môn (sư huynh đệ cùng pháp hệ) mà không ghi nhầm nguồn Marcus.
            siblings = conn.execute("""
                SELECT DISTINCT s2.student_id AS id, s2.student_label AS label,
                       s1.teacher_label AS shared_teacher_label
                FROM marcus_networks s1
                JOIN marcus_networks s2
                  ON s1.teacher_id = s2.teacher_id AND s1.student_id != s2.student_id
                WHERE s1.student_id = ?
                ORDER BY s2.student_label
            """, (node_id,)).fetchall()
            sib_ids = [sib['id'] for sib in siblings]
            sib_vi_map = {}
            if sib_ids:
                placeholders = ','.join('?' * len(sib_ids))
                for r in conn.execute(
                    f"SELECT node_id, label, label_vi FROM marcus_reference WHERE node_id IN ({placeholders})",
                    sib_ids
                ).fetchall():
                    vi = r['label_vi'] if r['label_vi'] and r['label_vi'] != r['label'] else None
                    sib_vi_map[r['node_id']] = vi or r['label']
            for sib in siblings:
                vi = sib_vi_map.get(sib['id'], sib['label'])
                nodes.append({"id": sib['id'], "label": vi, "label_zh": sib['label'],
                              "role": "sibling", "group": "person", "navigable": True})
                edges.append({
                    "from": dila_id, "to": sib['id'], "label": "đồng môn",
                    "derived": True, "ref": None,
                    "shared_teacher_label": sib['shared_teacher_label'],
                    "evidence_type": "co_mention",
                })

        return jsonify({
            "ok": True, "entity_type": "person", "person_id": dila_id,
            "center": center, "linked": bool(link),
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA" if link else None,
            "nodes": nodes, "edges": edges
        })
    except Exception as e:
        app.logger.error(f"api_monk_graph error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/monk/<dila_id>/lineage-tree')
def api_monk_lineage_tree(dila_id):
    """GET /daoanh/api/monk/<dila_id>/lineage-tree?up=3&down=3
    Cây phả hệ truyền thừa đệ quy quanh một tăng nhân.
    Mặc định: lineage_edge_consensus (>=2/4 nguồn đồng thuận).
    ?trees=dila,marcus,ttl  -> dùng VIEW T425 (v_tree_dila/marcus/ttl) thay consensus.
    ?overlay=1              -> dùng v_tree_overlay (cạnh gộp multi-source).
    ?include_single=1       -> bao gồm cạnh đơn nguồn (optional filter UI).
    """
    up = max(0, min(int(request.args.get('up', 3)), 6))
    down = max(0, min(int(request.args.get('down', 3)), 6))
    inc_single = request.args.get('include_single', '0') == '1'

    # T426: tham số chọn nguồn
    trees_param = request.args.get('trees', '').strip().lower()
    trees = [t.strip() for t in trees_param.split(',') if t.strip() in ('dila', 'marcus', 'ttl')]
    overlay = request.args.get('overlay', '0') == '1'

    use_view = bool(trees) or overlay

    conn = get_db_connection()
    try:
        # T186: Center có thể là DILA person hoặc danh tăng VN (ttl_persons)
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone()
        if not exists:
            # T381 follow-up fix (2026-10-14): bảng ttl_persons không tồn tại trong
            # DB thực tế (data/lineage.db) -> sqlite3.OperationalError "no such table"
            # nếu không bắt riêng sẽ rơi xuống except Exception chung ở cuối hàm và
            # trả 500 kèm message lộ chi tiết nội bộ. Bắt đúng lỗi "no such table" ở
            # đây, trả 404 rõ ràng, không lộ stack trace.
            try:
                exists = conn.execute("SELECT 1 FROM ttl_persons WHERE id=?", (dila_id,)).fetchone()
            except sqlite3.OperationalError as e:
                if 'no such table' in str(e).lower():
                    return jsonify({"ok": False, "error": "Không tìm thấy tăng nhân (person not found)"}), 404
                raise
        if not exists:
            return jsonify({"ok": False, "error": "person not found"}), 404
        center = _t86_person_info(conn, dila_id)
        center['conflicts'] = _t86_person_conflict(conn, dila_id)
        center['origin_place'] = _t86_origin_place(conn, dila_id)

        nodes = {dila_id: center}
        edges = []
        up_excess = set()
        down_excess = set()
        node_origin = {}

        if use_view:
            # T426: BFS dùng VIEW T425
            view_name = 'overlay' if overlay else (trees[0] if trees else 'dila')

            # BFS lên (thầy)
            frontier = [dila_id]
            depth = {dila_id: 0}
            seen_up = {dila_id}
            while frontier:
                nxt = []
                for pid in frontier:
                    if depth[pid] >= up:
                        continue
                    nb, _cnt = _t426_neighbors_view(conn, pid, 'up', view_name)
                    for nbv in nb:
                        nid = nbv['id']
                        if nid in seen_up:
                            continue
                        seen_up.add(nid)
                        depth[nid] = depth[pid] + 1
                        nodes.setdefault(nid, _t86_person_info(conn, nid))
                        node_origin.setdefault(nid, _t86_origin_place(conn, nid))
                        # edge assertions từ lineage_edge_assertions để lấy màu/by source
                        _e138 = _t138_edge_assertions(conn, nid, pid)
                        _yfork = calculate_edge_color_and_divergence(nbv)
                        edges.append({
                            "from": nid, "to": pid, "direction": "teacher",
                            "relation_type": "dharma_transmission",
                            "ref": _e138['sources'][0]['ref'] if _e138['sources'] and _e138['sources'][0].get('ref') else None,
                            "has_ref": bool(_e138['sources'] and _e138['sources'][0].get('ref')),
                            "derived": False,
                            "sources": _e138['sources'],
                            "trust_level": _e138['trust_level'],
                            "rejected": _e138['rejected'],
                            "source_badge": nbv.get('source_badge', ''),
                            "agreeing_source_count": nbv.get('agreeing_source_count', 0),
                            "consensus_status": nbv.get('consensus_status', 'single_source'),
                            "edge_color": _yfork['edge_color'],
                            "edge_color_token": _yfork['edge_color_token'],
                            "edge_sources": _yfork['edge_sources'],
                            "n_sources": _yfork['n_sources'],
                            "edge_dashed": _yfork['dashed'],
                            "is_divergence": _yfork['is_divergence'],
                        })
                        nxt.append(nid)
                frontier = [x for x in nxt if depth.get(x, 999) < up]

            # BFS xuống (trò)
            frontier = [dila_id]
            depth = {dila_id: 0}
            seen_dn = {dila_id}
            while frontier:
                nxt = []
                for pid in frontier:
                    if depth[pid] >= down:
                        continue
                    nb, _cnt = _t426_neighbors_view(conn, pid, 'down', view_name)
                    for nbv in nb:
                        nid = nbv['id']
                        if nid in seen_dn:
                            continue
                        seen_dn.add(nid)
                        depth[nid] = depth[pid] + 1
                        nodes.setdefault(nid, _t86_person_info(conn, nid))
                        node_origin.setdefault(nid, _t86_origin_place(conn, nid))
                        _e138 = _t138_edge_assertions(conn, pid, nid)
                        _yfork = calculate_edge_color_and_divergence(nbv)
                        edges.append({
                            "from": pid, "to": nid, "direction": "student",
                            "relation_type": "dharma_transmission",
                            "ref": _e138['sources'][0]['ref'] if _e138['sources'] and _e138['sources'][0].get('ref') else None,
                            "has_ref": bool(_e138['sources'] and _e138['sources'][0].get('ref')),
                            "derived": False,
                            "sources": _e138['sources'],
                            "trust_level": _e138['trust_level'],
                            "rejected": _e138['rejected'],
                            "source_badge": nbv.get('source_badge', ''),
                            "agreeing_source_count": nbv.get('agreeing_source_count', 0),
                            "consensus_status": nbv.get('consensus_status', 'single_source'),
                            "edge_color": _yfork['edge_color'],
                            "edge_color_token": _yfork['edge_color_token'],
                            "edge_sources": _yfork['edge_sources'],
                            "n_sources": _yfork['n_sources'],
                            "edge_dashed": _yfork['dashed'],
                            "is_divergence": _yfork['is_divergence'],
                        })
                        nxt.append(nid)
                frontier = [x for x in nxt if depth.get(x, 999) < down]

            # đánh dấu expandable
            for pid in list(nodes.keys()):
                _, uc = _t426_neighbors_view(conn, pid, 'up', view_name)
                _, dc = _t426_neighbors_view(conn, pid, 'down', view_name)
                if uc > 0 and depth.get(pid, 0) >= up:
                    up_excess.add(pid)
                if dc > 0 and depth.get(pid, 0) >= down:
                    down_excess.add(pid)

            source_desc = f"VIEW T425: {view_name}" + (f" (trees={','.join(trees)})" if trees else "")
        else:
            # T158: BFS lên (thầy) — dùng lineage_edge_consensus
            frontier = [dila_id]
            depth = {dila_id: 0}
            seen_up = {dila_id}
            while frontier:
                nxt = []
                for pid in frontier:
                    if depth[pid] >= up:
                        continue
                    nb, _cnt = _t158_neighbors_consensus(conn, pid, 'up', inc_single)
                    # BUG-025 (2026-10-11): disciple có thể có >=2 ứng viên thầy (DILA/Marcus
                    # mâu thuẫn, ví dụ Quy Sơn Linh Hựu A001984 có cả Hoài Hải A001897 is_primary=1
                    # và Nghĩa Tân A010527 is_primary=0 fallback). Cây pháp hệ (tree layout) chỉ có
                    # ĐÚNG MỘT cạnh thầy mỗi node — nếu add hết nb thì frontend _lineageTreeParents()
                    # (par[to]=from, last-wins) sẽ bị ghi đè bởi cạnh sau cùng, có thể là cạnh sai.
                    # nb đã ORDER BY is_primary DESC (xem _t158_neighbors_consensus) → chỉ lấy ứng viên
                    # đầu tiên hợp lệ (bỏ is_primary=-1 "tham học", bỏ cạnh rejected) — nhất quán với
                    # cách ancestor-spine (T152/T187, dòng ~6511) đã chọn thầy.
                    chosen = None
                    for nbv in nb:
                        if nbv.get('is_primary', 0) == -1:
                            continue
                        _e138_probe = _t138_edge_assertions(conn, nbv['id'], pid)
                        if _e138_probe.get('rejected'):
                            continue
                        chosen = nbv
                        break
                    for nbv in ([chosen] if chosen else []):
                        nid = nbv['id']
                        if nid in seen_up:
                            continue
                        seen_up.add(nid)
                        depth[nid] = depth[pid] + 1
                        nodes.setdefault(nid, _t86_person_info(conn, nid))
                        node_origin.setdefault(nid, _t86_origin_place(conn, nid))
                        _e138 = _t138_edge_assertions(conn, nid, pid)
                        _yfork = calculate_edge_color_and_divergence(nbv)
                        edges.append({
                            "from": nid, "to": pid, "direction": "teacher",
                            "relation_type": "dharma_transmission",
                            "ref": _e138['sources'][0]['ref'] if _e138['sources'] and _e138['sources'][0].get('ref') else None,
                            "has_ref": bool(_e138['sources'] and _e138['sources'][0].get('ref')),
                            "derived": False,
                            "sources": _e138['sources'],
                            "trust_level": _e138['trust_level'],
                            "rejected": _e138['rejected'],
                            "source_badge": nbv.get('source_badge', ''),
                            "agreeing_source_count": nbv.get('agreeing_source_count', 0),
                            "consensus_status": nbv.get('consensus_status', 'single_source'),
                            "edge_color": _yfork['edge_color'],
                            "edge_color_token": _yfork['edge_color_token'],
                            "edge_sources": _yfork['edge_sources'],
                            "n_sources": _yfork['n_sources'],
                            "edge_dashed": _yfork['dashed'],
                            "is_divergence": _yfork['is_divergence'],
                        })
                        nxt.append(nid)
                frontier = [x for x in nxt if depth.get(x, 999) < up]

            # T158: BFS xuống (trò) — dùng lineage_edge_consensus
            frontier = [dila_id]
            depth = {dila_id: 0}
            seen_dn = {dila_id}
            while frontier:
                nxt = []
                for pid in frontier:
                    if depth[pid] >= down:
                        continue
                    nb, _cnt = _t158_neighbors_consensus(conn, pid, 'down', inc_single)
                    for nbv in nb:
                        nid = nbv['id']
                        if nid in seen_dn:
                            continue
                        seen_dn.add(nid)
                        depth[nid] = depth[pid] + 1
                        nodes.setdefault(nid, _t86_person_info(conn, nid))
                        node_origin.setdefault(nid, _t86_origin_place(conn, nid))
                        _e138 = _t138_edge_assertions(conn, pid, nid)
                        _yfork = calculate_edge_color_and_divergence(nbv)
                        edges.append({
                            "from": pid, "to": nid, "direction": "student",
                            "relation_type": "dharma_transmission",
                            "ref": _e138['sources'][0]['ref'] if _e138['sources'] and _e138['sources'][0].get('ref') else None,
                            "has_ref": bool(_e138['sources'] and _e138['sources'][0].get('ref')),
                            "derived": False,
                            "sources": _e138['sources'],
                            "trust_level": _e138['trust_level'],
                            "rejected": _e138['rejected'],
                            "source_badge": nbv.get('source_badge', ''),
                            "agreeing_source_count": nbv.get('agreeing_source_count', 0),
                            "consensus_status": nbv.get('consensus_status', 'single_source'),
                            "edge_color": _yfork['edge_color'],
                            "edge_color_token": _yfork['edge_color_token'],
                            "edge_sources": _yfork['edge_sources'],
                            "n_sources": _yfork['n_sources'],
                            "edge_dashed": _yfork['dashed'],
                            "is_divergence": _yfork['is_divergence'],
                        })
                        nxt.append(nid)
                frontier = [x for x in nxt if depth.get(x, 999) < down]

            # đánh dấu expandable dựa trên consensus (không phải marcus_networks)
            for pid in list(nodes.keys()):
                _, uc = _t158_neighbors_consensus(conn, pid, 'up', inc_single)
                _, dc = _t158_neighbors_consensus(conn, pid, 'down', inc_single)
                if uc > 0 and depth.get(pid, 0) >= up:
                    up_excess.add(pid)
                if dc > 0 and depth.get(pid, 0) >= down:
                    down_excess.add(pid)

            source_desc = "consensus:>=2/4 sources (DILA, Marcus, TTL, Lineage)"

        # enrich nodes
        for pid, nd in nodes.items():
            nd['conflicts'] = _t86_person_conflict(conn, pid)
            nd['origin_place'] = node_origin.get(pid) or _t86_origin_place(conn, pid)
            nd['has_more_up'] = pid in up_excess
            nd['has_more_down'] = pid in down_excess
            nd['display_name'] = _t412_resolve_display_name(conn, pid, nd)

        # T138 — lọc cạnh rejected khỏi mạch chuẩn
        active_edges = [e for e in edges if not e.get('rejected')]

        # T381: tree_status — tổng hợp Y-fork divergence trên các cạnh active
        _divergence_count = sum(1 for e in active_edges if e.get('is_divergence'))
        tree_status = {
            "has_divergence": _divergence_count > 0,
            "divergence_count": _divergence_count,
        }

        return jsonify({
            "ok": True, "entity_type": "person", "person_id": dila_id,
            "center": center, "up": up, "down": down,
            "source": source_desc,
            "include_single": inc_single,
            "nodes": list(nodes.values()),
            "edges": active_edges,
            "tree_status": tree_status,
        })
    except Exception as e:
        app.logger.error(f"api_monk_lineage_tree error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T152 — Ancestor Spine: chuỗi thầy đầy đủ ngược lên đầu mạch ────────────────────
# Vấn đề: api_monk_lineage_tree clamp up/down [0,6] + client hardcode up=2 → Pháp Mạch
# chỉ hiển thị ≤2 đời tổ. Endpoint này đi bộ teacher-chain (marcus_networks up) KHÔNG
# clamp theo giới hạn đời — tới khi hết thầy (root) / cạnh bị reject / chạm safety 80 hops.
# Mirror tiêu chí T152: 0 ALTER, 0 Schema, 0 DB write, chỉ đọc cạnh verified (0 rejected).
@app.route('/daoanh/api/monk/<dila_id>/ancestor-spine')
def api_monk_ancestor_spine(dila_id):
    """GET /daoanh/api/monk/<dila_id>/ancestor-spine?max_hops=80
    Chuỗi tổ sư (ancestor spine) từ dila_id ngược lên đầu mạch, KHÔNG bị cắt ở 2/3 đời:
      - Đi bộ teacher-chain qua _t86_neighbors(conn, pid, 'up') (marcus_networks student→teacher).
      - Lọc cạnh rejected qua _t138_edge_assertions (mirror api_monk_lineage_tree active_edges).
      - Safety max_hops (mặc định 80) + cycle-safe (seen set) — T151 A6/A7.
      - break_reason: 'root' (hết thầy) | 'rejected' (còn thầy nhưng cạnh bị reject —
        "Mạch thiếu cạnh đã xác minh") | 'safety' (chạm giới hạn hops).
    Trả nodes (chỉ spine) + edges (chỉ non-rejected) + ancestors [gần→xa] + break_reason."""
    conn = get_db_connection()
    try:
        try:
            max_hops = max(1, min(int(request.args.get('max_hops', 80)), 80))
        except (TypeError, ValueError):
            max_hops = 80
        # T186: cho phép ttl_persons (danh tăng VN) làm start node
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone() \
            or conn.execute("SELECT 1 FROM ttl_persons WHERE id=?", (dila_id,)).fetchone()
        if not exists:
            return jsonify({"ok": False, "error": "person not found"}), 404

        nodes = {}
        edges = []
        ancestors = []        # gần → xa (chính là chuỗi thầy)
        seen = {dila_id}
        cur = dila_id
        break_reason = 'root'
        hops = 0

        while hops < max_hops:
            cur_person = _t86_person_info(conn, cur)
            cur_person['conflicts'] = _t86_person_conflict(conn, cur)
            cur_person['origin_place'] = _t86_origin_place(conn, cur)
            cur_person['display_name'] = _t412_resolve_display_name(conn, cur, cur_person)
            nodes.setdefault(cur, cur_person)

            # T187: dùng consensus (có is_primary) thay vì marcus_networks
            # include_single=True để không bỏ qua TTL-only edges
            nb, _cnt = _t158_neighbors_consensus(conn, cur, 'up', include_single=True)
            if not nb:
                break_reason = 'root'
                break
# chọn thầy ưu tiên cạnh nhiều nguồn (confirmed_2plus > single_source) — BUG-038 fix
            # Thứ tự ưu tiên: confirmed_2plus > confirmed_1plus > ttl_only > single_source
            # Trong cùng mức độ đồng thuận, ưu tiên is_primary=1 (thầy truyền pháp ấn)
            nxt = None
            nxt_ref = ''
            primary_candidate = None
            primary_candidate_rank = (-1, -1)  # (consensus_rank, is_primary)
            saved_e138 = None
            for nbv in nb:
                nid = nbv['id']
                if nid in seen:
                    continue
                # T187: bỏ qua edge đã xác định là tham học (is_primary=-1)
                if nbv.get('is_primary', 0) == -1:
                    continue
                _e138 = _t138_edge_assertions(conn, nid, cur)
                if _e138.get('rejected'):
                    continue
                # Xếp hạng ưu tiên theo consensus_status và is_primary
                consensus = nbv.get('consensus_status', 'single_source')
                is_primary = nbv.get('is_primary', 0)
                # consensus_rank: confirmed_2plus=3, confirmed_1plus=2, ttl_only=1, single_source=0
                if consensus == 'confirmed_2plus':
                    consensus_rank = 3
                elif consensus == 'confirmed_1plus':
                    consensus_rank = 2
                elif consensus == 'ttl_only':
                    consensus_rank = 1
                else:
                    consensus_rank = 0
                # Kết hợp consensus_rank và is_primary để chọn
                candidate_rank = (consensus_rank, is_primary)
                if primary_candidate is None or candidate_rank > primary_candidate_rank:
                    primary_candidate = nid
                    primary_candidate_rank = candidate_rank
                    saved_e138 = _e138
            # Sau khi duyệt hết, dùng candidate có rank cao nhất
            if primary_candidate is not None:
                nxt = primary_candidate
                _e138n = saved_e138
                # Lấy nbv của candidate đã chọn để gắn metadata
                chosen_nbv = next((v for v in nb if v['id'] == primary_candidate), None)
            else:
                # còn thầy ở trên nhưng mọi cạnh bị reject → dừng HONEST
                break_reason = 'rejected'
                break
            _e138 = _e138n
            nid = nxt
            seen.add(nid)
            # T413: gắn edge_color/source_badge/consensus_status cho cạnh spine (mirror lineage-tree)
            _yfork = calculate_edge_color_and_divergence(chosen_nbv) if chosen_nbv else {'edge_color': '#94a3b8', 'edge_color_token': 'unknown', 'edge_sources': [], 'n_sources': 0, 'dashed': True, 'is_divergence': False}
            edges.append({
                "from": nid, "to": cur, "direction": "teacher",
                "relation_type": "da:isTeacherOf", "ref": nxt_ref,
                "has_ref": bool(nxt_ref), "derived": False,
                "sources": _e138.get('sources', []),
                "trust_level": _e138.get('trust_level'),
                "rejected": False,
                "source_badge": chosen_nbv.get('source_badge', '') if chosen_nbv else '',
                "consensus_status": chosen_nbv.get('consensus_status', 'single_source') if chosen_nbv else 'single_source',
                "edge_color": _yfork['edge_color'],
                "edge_color_token": _yfork['edge_color_token'],
                "edge_sources": _yfork['edge_sources'],
                "n_sources": _yfork['n_sources'],
                "edge_dashed": _yfork['dashed'],
                "is_divergence": _yfork['is_divergence'],
            })
            ancestors.append(nid)
            hops += 1
            cur = nid
        if hops >= max_hops and break_reason == 'root':
            break_reason = 'safety'

        # thêm node đầu mạch (đã thêm cur_trong while ở vòng sau — đảm bảo tồn tại)
        last_person = _t86_person_info(conn, cur)
        last_person['conflicts'] = _t86_person_conflict(conn, cur)
        last_person['origin_place'] = _t86_origin_place(conn, cur)
        last_person['display_name'] = _t412_resolve_display_name(conn, cur, last_person)
        nodes.setdefault(cur, last_person)

        return jsonify({
            "ok": True, "entity_type": "person", "person_id": dila_id,
            "center": nodes.get(dila_id),
            "ancestors": ancestors,          # gần → xa
            "nodes": list(nodes.values()),
            "edges": edges,
            "break_reason": break_reason,
            "hops": hops, "max_hops": max_hops,
            "has_more_up": break_reason in ('rejected', 'safety'),
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA",
        })
    except Exception as e:
        app.logger.error(f"api_monk_ancestor_spine error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T5-b — Ancestor Path: BFS tìm đường ngắn nhất từ person lên root cụ thể ─────────
@app.route('/daoanh/api/monk/<dila_id>/ancestor-path')
def api_monk_ancestor_path(dila_id):
    """GET /daoanh/api/monk/<dila_id>/ancestor-path?root=A001719&max_depth=40
    BFS từ dila_id đi ngược lên (teachers) qua lineage_edge_consensus cho đến khi
    gặp root (mặc định: Huệ Năng A001719). Trả path được sắp xếp root→dila_id.
    Nếu không tìm thấy root, trả partial path lên đến tổ xa nhất tìm được."""
    root_id = request.args.get('root', 'A001719')
    try:
        max_depth = max(1, min(int(request.args.get('max_depth', 40)), 60))
    except (TypeError, ValueError):
        max_depth = 40
    conn = get_db_connection()
    try:
        from collections import deque

        # BFS từ dila_id đi lên theo teachers trong lineage_edge_consensus
        parent = {dila_id: None}
        depth_map = {dila_id: 0}
        queue = deque([dila_id])
        found = False

        while queue and not found:
            pid = queue.popleft()
            d = depth_map[pid]
            if d >= max_depth:
                continue
            teachers = conn.execute(
                "SELECT teacher_id FROM lineage_edge_consensus"
                " WHERE disciple_id=? AND is_default_visible=1",
                (pid,)
            ).fetchall()
            for t in teachers:
                tid = t['teacher_id']
                if tid not in parent:
                    parent[tid] = pid
                    depth_map[tid] = d + 1
                    if tid == root_id:
                        found = True
                        break
                    queue.append(tid)

        # Dựng chain từ root → dila_id
        chain_ids = []
        if found:
            cur = root_id
            while cur is not None:
                chain_ids.append(cur)
                cur = parent.get(cur)
            # chain_ids = [root, ..., dila_id]
        else:
            # Không tìm thấy root — trả partial chain từ người xa nhất đến dila_id
            # Tìm node có depth lớn nhất (xa nhất, chưa có cha trong BFS)
            top_nodes = [k for k, v in parent.items() if v is None and k != dila_id]
            if not top_nodes:
                top_nodes = [dila_id]
            # Lấy chain từ top_node[0] (thường chỉ có 1 nhánh chính)
            cur = top_nodes[0]
            while cur is not None:
                chain_ids.append(cur)
                cur = parent.get(cur)

        # Build node info cho từng node trong chain
        path_nodes = []
        for nid in chain_ids:
            info = _t86_person_info(conn, nid)
            info['display_name'] = _t412_resolve_display_name(conn, nid, info)
            path_nodes.append(info)

        return jsonify({
            "ok": True,
            "found": found,
            "path": path_nodes,
            "start": dila_id,
            "root": root_id,
            "depth": len(chain_ids) - 1,
        })
    except Exception as e:
        app.logger.error(f"api_monk_ancestor_path error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/lineage-ref/context')
def api_lineage_ref_context():
    """GET /daoanh/api/lineage-ref/context?ref=... — văn cảnh ±1 đoạn quanh passage đã
    resolve từ dẫn chiếu Marcus (T128 'Đọc văn cảnh'). Fallback trung thực khi passage
    chưa được lập chỉ mục (vd T47n1990 — không backfill)."""
    ref = request.args.get('ref', '')
    conn = get_db_connection()
    try:
        parsed = _t128_parse_relation_ref(ref)
        resolved = _t86_parse_ref_passage(conn, ref)
        context = []
        if resolved and resolved.get('found') and resolved.get('passage_id'):
            pid = resolved['passage_id']
            tid = resolved['text_id']
            cur = conn.execute(
                "SELECT passage_id, text_id, loc_ref, raw_text FROM passage WHERE passage_id=?",
                (pid,)).fetchone()
            if cur:
                context.append({'passage_id': cur['passage_id'], 'text_id': cur['text_id'],
                                'loc_ref': cur['loc_ref'], 'raw_text': cur['raw_text']})
                prv = conn.execute(
                    "SELECT passage_id, text_id, loc_ref, raw_text FROM passage "
                    "WHERE text_id=? AND passage_id<? ORDER BY passage_id DESC LIMIT 1",
                    (tid, pid)).fetchone()
                if prv:
                    context.insert(0, {'passage_id': prv['passage_id'], 'text_id': prv['text_id'],
                                       'loc_ref': prv['loc_ref'], 'raw_text': prv['raw_text']})
                nxt = conn.execute(
                    "SELECT passage_id, text_id, loc_ref, raw_text FROM passage "
                    "WHERE text_id=? AND passage_id>? ORDER BY passage_id ASC LIMIT 1",
                    (tid, pid)).fetchone()
                if nxt:
                    context.append({'passage_id': nxt['passage_id'], 'text_id': nxt['text_id'],
                                    'loc_ref': nxt['loc_ref'], 'raw_text': nxt['raw_text']})
        return jsonify({"ok": True, "parsed": parsed, "resolved": resolved, "context": context})
    except Exception as e:
        app.logger.error(f"api_lineage_ref_context error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/nexus/<entity_id>')
def api_nexus(entity_id):
    """GET /daoanh/api/nexus/<entity_id>?type=person|place

    Event-centric nexus: entity → EVENT → TEXT (passage với citation thật) → TIME
    (year / era). Cùng shape nodes/edges như các graph khác nên places.html tái dùng
    _renderVisGraph. Edge nào cũng có tooltip nguồn (cbeta_ref hoặc source_ref).
    """
    etype = request.args.get('type', 'place')
    conn = get_db_connection()
    try:
        # ── Center label ──
        if etype == 'person':
            p = conn.execute("SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (entity_id,)).fetchone()
            if not p:
                return jsonify({"ok": False, "error": "person not found"}), 404
            mr = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id = ?", (entity_id,)).fetchone()
            label_zh = (mr['label'] if mr else None) or p['name_zh']
            label_vi = p['name_vi'] or (mr['label_vi'] if mr else None)
            disp = _t86_resolve_display_name(conn, entity_id, {'name_vi': label_vi, 'name_zh': label_zh})
            center = {"id": entity_id, "label": disp['primary'], "label_vi": disp['primary'],
                      "label_zh": disp['secondary'] or label_zh, "is_formal_name": disp['is_formal_name']}
        else:
            pl = conn.execute("SELECT id, name, name_zh FROM places_dila WHERE id = ?", (entity_id,)).fetchone()
            if not pl:
                return jsonify({"ok": False, "error": "place not found"}), 404
            vi = conn.execute("SELECT name_vi FROM namevi_map_places WHERE dila_id = ?", (entity_id,)).fetchone()
            # T101 BUG-001: label_zh dùng places_dila.name (tên chính thức DILA), không phải name_zh
            _pl_label_zh = pl['name'] or pl['name_zh']
            center = {"id": entity_id,
                      "label": (vi['name_vi'] if vi else None) or _pl_label_zh,
                      "label_vi": (vi['name_vi'] if vi else None),
                      "label_zh": _pl_label_zh}

        # ── Sự kiện từ event_text_link (bridge Commit 2) ──
        if etype == 'person':
            events = conn.execute(
                "SELECT * FROM event_text_link WHERE entity_type = 'person' AND entity_id = ?",
                (entity_id,)).fetchall()
        else:
            events = conn.execute(
                "SELECT * FROM event_text_link WHERE "
                "(event_type IN ('place_founding','place_dissolved') AND entity_id = ?) "
                "OR (event_type = 'person_place' AND related_id = ?)",
                (entity_id, entity_id)).fetchall()

        nodes, edges = [], []
        seen_nodes = {entity_id, 'center'}

        def _add_node(nid, label, label_zh, group, navigable=False, label_vi=None):
            if nid in seen_nodes:
                return
            seen_nodes.add(nid)
            nodes.append({"id": nid, "label": label, "label_vi": label_vi, "label_zh": label_zh,
                          "group": group, "navigable": navigable})

        # ── Duyệt từng sự kiện → event node, text node, time node ──
        for ev in events:
            et = ev['event_type']
            eid = f"ev-{ev['source_table']}-{ev['id']}"
            if et == 'person_place':
                # person_place: entity_id = person, related_id = place (bất biến từ ETL Commit 2).
                pid = ev['entity_id']
                placeid = ev['related_id']
                if etype == 'person':
                    # center = person → thêm node place (navigable → chuyển sang địa danh)
                    _add_node(placeid, None, None, 'place', navigable=True)
                    _add_node(eid, 'cư trú tại', 'cư trú tại', 'event')
                    _src = ev['source_book'] or None
                    edges.append({"from": entity_id, "to": eid, "label": '—', "ref": None,
                                  "evidence_type": "unverified"})
                    edges.append({"from": eid, "to": placeid, "label": 'cư trú tại',
                                  "ref": _src,
                                  "evidence_type": "partial" if _src else "unverified",
                                  "partial_reason": "Chưa có CBETA locator cụ thể" if _src else None})
                else:
                    # center = place → thêm node person (navigable → chuyển sang nhân vật)
                    if pid:
                        # A=1: pid thật (DILA person id).
                        _add_node(pid, None, None, 'person', navigable=True)
                        person_ref = pid
                    else:
                        # A=1: entity_id NULL → dùng related_name làm label (tên Hán) +
                        # synthetic id (không navigable — không có hồ sô để chuyển sang).
                        # Tránh collision id với event node eid.
                        _add_node(f"pers-{ev['id']}", ev['related_name'], ev['related_name'],
                                  'person', navigable=False)
                        person_ref = f"pers-{ev['id']}"
                    _add_node(eid, 'hiện diện', 'hiện diện', 'event')
                    edges.append({"from": person_ref, "to": eid, "label": '—', "ref": None,
                                  "evidence_type": "unverified"})
                    src = ev['source_book'] or None
                    edges.append({"from": eid, "to": entity_id, "label": 'hiện diện',
                                  "ref": src,
                                  "evidence_type": "partial" if src else "unverified",
                                  "partial_reason": "Chưa có CBETA locator cụ thể" if src else None})
            else:
                # place_founding / place_dissolved → time (year) node
                et_name = {'place_founding': 'pháp duyên sáng lập',
                           'place_dissolved': 'giải tán'}.get(et, et)
                _add_node(eid, et_name, et_name, 'event')
                src_ref = ev['source_ref'] or None
                edges.append({"from": entity_id, "to": eid, "label": et_name, "ref": src_ref,
                              "evidence_type": "with_evidence" if src_ref else "unverified"})
                if ev['year']:
                    tid = f"time-{eid}"
                    _add_node(tid, str(ev['year']), str(ev['year']), 'time')
                    edges.append({"from": eid, "to": tid, "label": 'năm', "ref": src_ref,
                                  "evidence_type": "with_evidence" if src_ref else "unverified"})

            # ── passage (text) node từ cbeta_ref ──
            if ev['cbeta_ref']:
                sigla = ev['cbeta_ref'].split('_')[0] if '_' in ev['cbeta_ref'] else ev['cbeta_ref']
                title = _nexus_title_for_sigla(conn, sigla, ev['source_book'])
                tid = f"txt-{sigla}-{ev['id']}"
                _add_node(tid, title, title, 'text')
                edges.append({
                    "from": eid, "to": tid, "label": 'trích dẫn',
                    "ref": ev['cbeta_ref'],
                    "citation": ev['cbeta_ref'],
                    "evidence_type": "with_evidence",
                })

        # ── fill label_zh cho node place/person chưa có label ──
        # (tra cứu nhanh từ places_dila / marcus_reference)
        if etype == 'person':
            for n in nodes:
                if n.get('group') == 'place' and not n.get('label'):
                    r = conn.execute("SELECT name, name_zh FROM places_dila WHERE id = ?", (n['id'],)).fetchone()
                    if r:
                        vi = conn.execute("SELECT name_vi FROM namevi_map_places WHERE dila_id = ?", (n['id'],)).fetchone()
                        n['label'] = (vi['name_vi'] if vi else None) or r['name'] or r['name_zh']
                        n['label_vi'] = (vi['name_vi'] if vi else None)
                        n['label_zh'] = r['name_zh']
        else:
            for n in nodes:
                if n.get('group') == 'person' and not n.get('label'):
                    r = conn.execute("SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (n['id'],)).fetchone()
                    if r:
                        mr2 = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id = ?", (n['id'],)).fetchone()
                        z = (mr2['label'] if mr2 else None) or r['name_zh']
                        n['label'] = r['name_vi'] or z
                        n['label_vi'] = r['name_vi'] or (mr2['label_vi'] if mr2 else None)
                        n['label_zh'] = z
                        n['dynasty'] = r['dynasty']

        # Aliases + Groups (Nexus grouped view)
        import re as _re
        aliases = []
        groups = {}
        if etype == 'person':
            seen_a = {center.get('label', ''), center.get('label_zh', '')}
            prow = conn.execute("SELECT name_zh, name_vi FROM people WHERE id=?", (entity_id,)).fetchone()
            mrrow = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id=?", (entity_id,)).fetchone()
            for v in (list(prow) if prow else []) + (list(mrrow) if mrrow else []):
                if v and (v2 := str(v).strip()) and v2 not in seen_a:
                    aliases.append(v2); seen_a.add(v2)
            cbeta_row = conn.execute("""
                SELECT COUNT(DISTINCT CASE WHEN INSTR(cbeta_ref,'_')>0
                       THEN SUBSTR(cbeta_ref,1,INSTR(cbeta_ref,'_')-1) ELSE cbeta_ref END) as cnt
                FROM event_text_link WHERE entity_id=? AND cbeta_ref IS NOT NULL
            """, (entity_id,)).fetchone()
            marcus_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM marcus_networks WHERE teacher_id=? OR student_id=?",
                (entity_id, entity_id)).fetchone()
            dila_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM people WHERE id=?", (entity_id,)).fetchone()
            groups = {
                'kinh_dien': {'CBETA': (cbeta_row['cnt'] if cbeta_row else 0)},
                'tang_nhan': {
                    'Marcus': (marcus_row['cnt'] if marcus_row else 0),
                    'DILA': (dila_row['cnt'] if dila_row else 0),
                },
            }
            # Add Marcus teacher/student relation nodes
            for rel in conn.execute("""
                SELECT teacher_id, student_id, teacher_label, student_label, ref
                FROM marcus_networks WHERE teacher_id=? OR student_id=?
            """, (entity_id, entity_id)).fetchall():
                is_t = rel['teacher_id'] == entity_id
                oid = rel['student_id'] if is_t else rel['teacher_id']
                olbl = rel['student_label'] if is_t else rel['teacher_label']
                # Line 1 Marcus (NEXUS-LBL-001): ưu tiên tên Việt đã có trong DB
                # (people.name_vi / marcus_reference.label_vi), không AI, không sửa nguồn;
                # label gốc (Hán) giữ ở label_zh.
                rv = conn.execute(
                    "SELECT p.name_vi, p.name_zh, COALESCE(mr.label_vi, '') AS mvi "
                    "FROM people p LEFT JOIN marcus_reference mr ON mr.node_id = p.id "
                    "WHERE p.id = ?", (oid,)).fetchone()
                if rv is not None:
                    _lvi = rv['name_vi'] or rv['mvi'] or None
                    _lzh = olbl or rv['name_zh']
                    _disp = _t86_resolve_display_name(conn, oid, {'name_vi': _lvi, 'name_zh': _lzh})
                    _add_node(oid, _disp['primary'], _disp['secondary'] or _lzh, 'person',
                              navigable=True, label_vi=_disp['primary'])
                else:
                    _add_node(oid, olbl, olbl, 'person', navigable=True)
                edges.append({"from": entity_id if is_t else oid,
                              "to": oid if is_t else entity_id,
                              "label": "",
                              "direction": "student" if is_t else "teacher",
                              "ref": rel['ref'], "source": "marcus"})
        elif etype == 'place':
            pl_xml_row = conn.execute(
                "SELECT raw_xml FROM places_dila WHERE id=?", (entity_id,)
            ).fetchone()
            if pl_xml_row and pl_xml_row['raw_xml']:
                seen_a = {center.get('label_zh', ''), center.get('label', '')}
                for m in _re.findall(r'<[^>]*[Pp]lace[Nn]ame[^>]*>([^<]{1,80})</', pl_xml_row['raw_xml']):
                    m = m.strip()
                    if m and m not in seen_a:
                        aliases.append(m)
                        seen_a.add(m)
            kd_row = conn.execute("""
                SELECT COUNT(DISTINCT
                    CASE WHEN INSTR(cbeta_ref,'_')>0
                         THEN SUBSTR(cbeta_ref,1,INSTR(cbeta_ref,'_')-1)
                         ELSE cbeta_ref END) as cnt
                FROM event_text_link
                WHERE event_type='person_place' AND related_id=? AND cbeta_ref IS NOT NULL
            """, (entity_id,)).fetchone()
            dyn_rows = conn.execute("""
                SELECT COALESCE(p.dynasty,'(không rõ)') as dynasty,
                       COUNT(DISTINCT etl.entity_id) as cnt
                FROM event_text_link etl
                JOIN people p ON p.id = etl.entity_id
                WHERE etl.event_type='person_place' AND etl.related_id=?
                GROUP BY p.dynasty ORDER BY cnt DESC
            """, (entity_id,)).fetchall()
            groups = {
                'kinh_dien': (kd_row['cnt'] if kd_row else 0),
                'tang_nhan': {r['dynasty']: r['cnt'] for r in dyn_rows},
                'tang_nhan_total': sum(r['cnt'] for r in dyn_rows),
            }
        return jsonify({
            "ok": True, "entity_type": etype, "entity_id": entity_id,
            "center": center, "source": "event_text_link (place_person_bibl + place_timeline_events)",
            "nodes": nodes, "edges": edges,
            "aliases": aliases, "groups": groups,
        })
    except Exception as e:
        app.logger.error(f"api_nexus error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ============================================================
#  T51 — Nhân Vật Học Portal (additive, đọc-only)
# ============================================================
@app.route('/daoanh/api/persons/browse')
def api_persons_browse():
    """GET /daoanh/api/persons/browse — T51a: Duyệt nhân vật độc lập (portal).

    Standalone person-browse for the Nhân Vật tab on home.html — KHÔNG đụng
    route /api/places/<id>/persons (place-centric, T28). Chỉ đọc `people` +
    JOIN `marcus_people_link` (lineage) + đếm `place_person_link` / `person_origin_link`.

    Query params:
      q          — tìm theo name_vi / name_zh (LIKE, không dấu-insensitive tiếng Việt)
      dynasty    — lọc theo dynasty (chính xác)
      sect       — lọc theo sect (chính xác)
      has_lineage — '1' chỉ lấy người có Marcus lineage, '0' ngược lại
      page (1)   — trang
      limit (24) — số dòng/trang (max 100)
      sort       — 'name' | 'dynasty' | 'places' (mặc định dynasty)
    """
    conn = get_db_connection()
    try:
        q = (request.args.get('q') or '').strip()
        dynasty = (request.args.get('dynasty') or '').strip()
        sect = (request.args.get('sect') or '').strip()
        hl = (request.args.get('has_lineage') or '').strip()
        page = max(1, int(request.args.get('page') or 1))
        limit = min(100, max(1, int(request.args.get('limit') or 24)))
        sort = (request.args.get('sort') or 'dynasty').strip()
        offset = (page - 1) * limit

        where, params = [], []
        if q:
            where.append("(p.name_vi LIKE ? OR p.name_zh LIKE ? OR p.name_en LIKE ?)")
            like = f"%{q}%"
            params += [like, like, like]
        if dynasty:
            where.append("p.dynasty = ?")
            params.append(dynasty)
        if sect:
            where.append("p.sect = ?")
            params.append(sect)
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""

        # helpers: has_lineage, place & origin counts — dùng subquery để không nhân dòng
        count_sql = f"""
            SELECT COUNT(*) AS c FROM people p
            {where_sql}
            {(" AND p.id IN (SELECT person_id FROM marcus_people_link)" if hl == '1' else "")}
            {(" AND p.id NOT IN (SELECT person_id FROM marcus_people_link)" if hl == '0' else "")}
        """
        total = conn.execute(count_sql, params).fetchone()['c']

        order_map = {
            'name': "p.name_vi COLLATE NOCASE, p.name_zh",
            'dynasty': "p.dynasty IS NULL, p.dynasty, p.name_vi COLLATE NOCASE",
            'places': "(SELECT COUNT(*) FROM place_person_link pl WHERE pl.person_id = p.id) DESC",
        }
        order_sql = order_map.get(sort, order_map['dynasty'])

        base_sql = f"""
            SELECT
                p.id, p.name_zh, p.name_vi, p.name_en, p.sect, p.dynasty,
                p.birth_year, p.death_year, p.source_origin,
                (SELECT COUNT(*) FROM place_person_link pl WHERE pl.person_id = p.id) AS place_count,
                (SELECT COUNT(*) FROM person_origin_link pol WHERE pol.person_id = p.id) AS origin_count,
                EXISTS(SELECT 1 FROM marcus_people_link mpl WHERE mpl.person_id = p.id) AS has_lineage,
                substr(COALESCE(p.bio, ''), 1, 220) AS bio_preview
            FROM people p
            {where_sql}
            {(" AND p.id IN (SELECT person_id FROM marcus_people_link)" if hl == '1' else "")}
            {(" AND p.id NOT IN (SELECT person_id FROM marcus_people_link)" if hl == '0' else "")}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(base_sql, params + [limit, offset]).fetchall()

        persons = []
        for r in rows:
            persons.append({
                "id": r['id'],
                "name_zh": r['name_zh'], "name_vi": r['name_vi'], "name_en": r['name_en'],
                "sect": r['sect'], "dynasty": r['dynasty'],
                "birth_year": r['birth_year'], "death_year": r['death_year'],
                "source_origin": r['source_origin'],
                "place_count": r['place_count'], "origin_count": r['origin_count'],
                "has_lineage": bool(r['has_lineage']),
                "bio_preview": r['bio_preview'],
            })

        # danh sách triều đại + sect để populate dropdown filter
        dynasties = [r[0] for r in conn.execute(
            "SELECT DISTINCT dynasty FROM people WHERE dynasty IS NOT NULL AND dynasty != '' ORDER BY dynasty").fetchall()]
        sects = [r[0] for r in conn.execute(
            "SELECT DISTINCT sect FROM people WHERE sect IS NOT NULL AND sect != '' ORDER BY sect").fetchall()]

        return jsonify({
            "ok": True,
            "total": total, "page": page, "pages": max(1, -(-total // limit)),
            "limit": limit, "persons": persons,
            "filters": {"dynasties": dynasties, "sects": sects},
            "counts": {
                "total_people": conn.execute("SELECT COUNT(*) AS c FROM people").fetchone()['c'],
                "with_lineage": conn.execute("SELECT COUNT(DISTINCT person_id) AS c FROM marcus_people_link").fetchone()['c'],
            }
        })
    except Exception as e:
        app.logger.error(f"api_persons_browse error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/person/<dila_id>/profile')
def api_person_profile(dila_id):
    """GET /daoanh/api/person/<dila_id>/profile — T51b: tiểu sử nhân vật (portal).

    Kết hợp: people.bio + Marcus lineage (thầy/trò có CBETA citation) + địa danh
    liên quan (place_person_link, person_origin_link, place_person_bio_cache) + kinh
    điển (place_person_bibl). KHÔNG ghi đè bio panel place-centric sẵn có.

    Tái dùng /daoanh/api/monk/<id>/graph cho phả hệ (nodes/edges).
    """
    conn = get_db_connection()
    try:
        p = conn.execute(
            "SELECT id, name_zh, name_vi, name_en, sect, dynasty, birth_year, death_year, "
            "source_origin, bio FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "person not found"}), 404

        profile = {
            "id": p['id'], "name_zh": p['name_zh'], "name_vi": p['name_vi'],
            "name_en": p['name_en'], "sect": p['sect'], "dynasty": p['dynasty'],
            "birth_year": p['birth_year'], "death_year": p['death_year'],
            "source_origin": p['source_origin'], "bio": p['bio'],
        }

        # Marcus lineage (tái dùng logic graph route — thầy/trò có ref citation)
        lineage = {"linked": False, "teachers": [], "students": [], "source": None}
        link = conn.execute(
            "SELECT marcus_node_id FROM marcus_people_link WHERE person_id = ?", (dila_id,)
        ).fetchone()
        if link:
            node_id = link['marcus_node_id']
            lineage["linked"] = True
            lineage["source"] = "Marcus Bingenheimer ChineseBuddhism_SNA"
            lineage["teachers"] = [
                {"id": t['teacher_id'], "label": t['teacher_label'], "ref": t['ref']}
                for t in conn.execute(
                    "SELECT teacher_id, teacher_label, ref FROM marcus_networks WHERE student_id = ?",
                    (node_id,)).fetchall()]
            lineage["students"] = [
                {"id": s['student_id'], "label": s['student_label'], "ref": s['ref']}
                for s in conn.execute(
                    "SELECT student_id, student_label, ref FROM marcus_networks WHERE teacher_id = ?",
                    (node_id,)).fetchall()]

        # Địa danh liên quan
        places = []
        try:
            place_rows = conn.execute("""
                SELECT DISTINCT pl.place_id, pl.relation_type, pl.source_name, pl.source_url
                FROM place_person_link pl WHERE pl.person_id = ?
                ORDER BY pl.created_at LIMIT 50
            """, (dila_id,)).fetchall()
            places = [
                {"place_id": r['place_id'], "relation_type": r['relation_type'],
                 "source_name": r['source_name'], "source_url": r['source_url']}
                for r in place_rows]
        except Exception as pe:
            app.logger.warning(f"profile places (link) failed: {pe}")
        try:
            origin_rows = conn.execute("""
                SELECT pol.place_id, pol.confidence FROM person_origin_link pol
                WHERE pol.person_id = ? ORDER BY pol.confidence DESC LIMIT 50
            """, (dila_id,)).fetchall()
            if origin_rows:
                seen = {x['place_id'] for x in places}
                for r in origin_rows:
                    if r['place_id'] not in seen:
                        places.append({"place_id": r['place_id'], "relation_type": "sinh tại / 籍貫",
                                       "source_name": "DILA Person Authority",
                                       "source_url": f"https://authority.dila.edu.tw/person/?fromInner={dila_id}",
                                       "confidence": r['confidence']})
                        seen.add(r['place_id'])
        except Exception as pe:
            app.logger.warning(f"profile places (origin) failed: {pe}")

        # Kinh điển liên quan (CBETA bibl)
        texts = []
        try:
            bibl_rows = conn.execute("""
                SELECT DISTINCT source_book, cbeta_ref FROM place_person_bibl
                WHERE person_id = ? AND cbeta_ref IS NOT NULL AND cbeta_ref != ''
                ORDER BY source_book LIMIT 50
            """, (dila_id,)).fetchall()
            texts = [{"source_book": r['source_book'], "cbeta_ref": r['cbeta_ref']} for r in bibl_rows]
        except Exception as te:
            app.logger.warning(f"profile texts failed: {te}")

        # T51d — Nhân vật xuất hiện trong kinh (cbeta_person_mentions, exact dila_person_id match)
        mentions = {"text_count": 0, "texts": []}
        try:
            m_rows = conn.execute("""
                SELECT cbeta_text_sigla AS sigla, COUNT(DISTINCT juan) AS juan_count
                FROM cbeta_person_mentions
                WHERE dila_person_id = ? AND cbeta_text_sigla IS NOT NULL AND cbeta_text_sigla != ''
                GROUP BY cbeta_text_sigla
                ORDER BY juan_count DESC
                LIMIT 50
            """, (dila_id,)).fetchall()
            if m_rows:
                siglas = [r['sigla'] for r in m_rows]
                title_map = {}
                try:
                    cconn = get_cbeta_conn()
                    try:
                        phold = ",".join("?" for _ in siglas)
                        t_rows = cconn.execute(
                            f"SELECT sigla, title_zh FROM cbeta_texts WHERE sigla IN ({phold})",
                            siglas).fetchall()
                        title_map = {r['sigla']: r['title_zh'] for r in t_rows}
                    finally:
                        cconn.close()
                except Exception as te:
                    app.logger.warning(f"profile mentions titles failed: {te}")
                mentions["text_count"] = len(m_rows)
                mentions["texts"] = [
                    {"sigla": r['sigla'], "title_zh": title_map.get(r['sigla'], ''),
                     "juan_count": r['juan_count']}
                    for r in m_rows]
        except Exception as me:
            app.logger.warning(f"profile mentions failed: {me}")

        return jsonify({
            "ok": True, "profile": profile,
            "lineage": lineage, "places": places, "texts": texts,
            "mentions": mentions,
        })
    except Exception as e:
        app.logger.error(f"api_person_profile error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T97 Phase 3: Event Candidate CRUD ─────────────────────────────────────────
@app.route('/daoanh/api/events')
def api_events_list():
    """GET /daoanh/api/events?place_id=&status=candidate&limit=50&offset=0
    List event candidates; optionally filter by place + review_status."""
    try:
        conn = get_db_connection()
        conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
        place_id = request.args.get('place_id', '').strip()
        status   = request.args.get('status', '').strip()
        limit    = min(int(request.args.get('limit', 50)), 200)
        offset   = int(request.args.get('offset', 0))

        where, params = [], []
        if status:
            where.append("e.review_status = ?"); params.append(status)
        if place_id:
            dila_id, _ = _resolve_dila_id(conn, place_id)
            target = dila_id or place_id
            where.append("ee.entity_id = ?"); params.append(target)

        where_sql = ("JOIN event_entities ee ON ee.event_id = e.event_id WHERE " + " AND ".join(where)) if where else ""
        sql = f"""
            SELECT e.event_id, e.event_type, e.title_zh, e.title_vi,
                   e.start_year, e.end_year, e.precision, e.review_status,
                   e.confidence, e.extraction_method, e.notes, e.created_at
            FROM events e {where_sql}
            ORDER BY e.start_year ASC NULLS LAST, e.created_at DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, params + [limit, offset]).fetchall()
        total_sql = f"SELECT COUNT(*) FROM events e {where_sql}"
        total = conn.execute(total_sql, params).fetchone()[0]

        events = []
        for r in rows:
            ev = dict(zip(['event_id','event_type','title_zh','title_vi','start_year','end_year',
                           'precision','review_status','confidence','extraction_method','notes','created_at'], r))
            # fetch evidence
            evids = conn.execute(
                "SELECT source_record, source_ref, evidence_type, exact_span FROM event_evidence WHERE event_id=? LIMIT 5",
                (r[0],)
            ).fetchall()
            ev['evidence'] = [{'source_record': e[0], 'source_ref': e[1],
                                'evidence_type': e[2], 'exact_span': e[3]} for e in evids]
            events.append(ev)

        conn.close()
        return jsonify({"ok": True, "total": total, "events": events})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/events/<event_id>', methods=['PATCH'])
def api_event_review(event_id):
    """PATCH /daoanh/api/events/<id> — update review_status + notes.
    Body: {status: candidate|reviewed|disputed|rejected, notes: str}"""
    try:
        data   = request.get_json(force=True) or {}
        status = data.get('status', '').strip()
        notes  = data.get('notes', '')
        valid  = ('candidate', 'reviewed', 'disputed', 'rejected')
        if status not in valid:
            return jsonify({"ok": False, "error": f"status phải là {valid}"}), 400

        conn = get_db_connection()
        conn.execute(
            "UPDATE events SET review_status=?, notes=?, updated_at=datetime('now') WHERE event_id=?",
            (status, notes, event_id)
        )
        if conn.execute("SELECT changes()").fetchone()[0] == 0:
            conn.close()
            return jsonify({"ok": False, "error": "event_id không tìm thấy"}), 404
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "event_id": event_id, "new_status": status})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/dila/stats')
def api_dila_stats():
    """GET /daoanh/api/dila/stats — counts by category and country."""
    try:
        conn = get_db_connection()
        cats = conn.execute(
            "SELECT note_category, COUNT(*) as n FROM places_dila WHERE note_category IS NOT NULL AND note_category != '' GROUP BY note_category ORDER BY n DESC LIMIT 20"
        ).fetchall()
        # Extract country from district (first segment before -)
        countries = conn.execute(
            """SELECT CASE WHEN INSTR(district, '-') > 0 THEN SUBSTR(district, 1, INSTR(district,'-')-1) ELSE district END as country,
               COUNT(*) as n FROM places_dila WHERE district IS NOT NULL AND district != ''
               GROUP BY country ORDER BY n DESC LIMIT 20"""
        ).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
        mapped = conn.execute(
            "SELECT COUNT(DISTINCT pd.id) FROM places_dila pd JOIN namevi_map_places nm ON nm.name_zh = pd.name_zh"
        ).fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "total": total, "mapped_vi": mapped,
                        "by_category": [dict(r) for r in cats],
                        "by_country": [dict(r) for r in countries]})
    except Exception as e:
        app.logger.error(f"api_dila_stats error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




# ── DILA Person Index API (mirror T10 DILA Place Index, additive 0 ALTER) ─────
# Reuses `people` (DILA person authority) + `translation_cache` (T73/T123 draft
# AI translation status, source_type='person_bio', entity_id=people.id) để
# admin theo dõi tiến độ dịch Hán→Việt tương đương DILA Place Index (name_vi
# mapping). KHÔNG suy đoán bio_vi — chỉ đọc trực tiếp cột/bảng đã có.

@app.route('/daoanh/api/dila/persons')
def api_dila_persons_search():
    """GET /daoanh/api/dila/persons?q=&sect=&dynasty=&status=&limit=50&offset=0

    status filter (tùy chọn): 'translated' (đã lưu people.bio_vi) |
    'draft' (có bản nháp AI/edited trong translation_cache, chưa lưu) |
    'none' (chưa có bản dịch nào).
    """
    import csv, io as _io
    q = request.args.get('q', '').strip()
    sect = request.args.get('sect', '').strip()
    dynasty = request.args.get('dynasty', '').strip()
    status = request.args.get('status', '').strip()
    hv_status = request.args.get('hv_status', '').strip()  # T172 debug Hán-Việt charwise
    sort_status = request.args.get('sort_status', '').strip()  # 'asc' | 'desc'
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    fmt = request.args.get('format', 'json')
    try:
        conn = get_db_connection()
        where = []
        params = []
        if q:
            where.append("(p.name_zh LIKE ? OR p.name_vi LIKE ? OR p.id LIKE ?)")
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        if sect:
            where.append("p.sect = ?")
            params.append(sect)
        if dynasty:
            where.append("p.dynasty = ?")
            params.append(dynasty)
        # Status filter phải nằm trong WHERE thật (không nối chuỗi sau ON,
        # nếu không sẽ bị SQLite hiểu nhầm thành điều kiện JOIN — làm filter
        # vô hiệu vì LEFT JOIN vẫn giữ nguyên dòng bên trái).
        if status == 'translated':
            where.append("p.bio_vi IS NOT NULL AND p.bio_vi != ''")
        elif status == 'draft':
            where.append("(p.bio_vi IS NULL OR p.bio_vi = '') AND tc.status IS NOT NULL")
        elif status == 'none':
            where.append("(p.bio_vi IS NULL OR p.bio_vi = '') AND tc.status IS NULL")
        # T172 — filter theo trạng thái kiểm tra phiên âm Hán-Việt (SPEC §5)
        hv_filter_sql = {
            'valid': "d.han_viet_validation_status = 'valid'",
            'normalized': "d.han_viet_validation_status = 'valid' AND d.legacy_match_status = 'normalized'",
            'exact': "d.han_viet_validation_status = 'valid' AND d.legacy_match_status = 'exact'",
            'exception': "d.han_viet_validation_status = 'exception'",
            'mismatch': "d.han_viet_validation_status = 'mismatch'",
            'unknown_char': "d.han_viet_validation_status = 'unknown_char'",
            'needs_review': "d.han_viet_validation_status = 'needs_review'",
            'differs': "d.legacy_match_status = 'differs'",
        }
        if hv_status in hv_filter_sql:
            where.append(hv_filter_sql[hv_status])
        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''

        translation_cte = """
            (SELECT tc.entity_id, tc.status, tc.updated_at, tc.model_id
               FROM translation_cache tc
              WHERE tc.source_type = 'person_bio' AND tc.status != 'invalidated'
                AND tc.id = (SELECT MAX(tc2.id) FROM translation_cache tc2
                              WHERE tc2.entity_id = tc.entity_id
                                AND tc2.source_type = 'person_bio'
                                AND tc2.status != 'invalidated'))
        """

        count_row = conn.execute(
            f"""SELECT COUNT(*) FROM people p
                LEFT JOIN {translation_cte} tc ON tc.entity_id = p.id
                LEFT JOIN person_hanviet_debug d ON d.person_id = p.id
                {where_sql}""", params
        ).fetchone()
        total = count_row[0]
        rows = conn.execute(
            f"""SELECT p.id, p.name_zh, p.name_vi, p.name_en, p.sect, p.dynasty,
                       p.birth_year, p.death_year,
                       (LENGTH(COALESCE(p.bio,'')) > 0) AS has_bio_zh,
                       (p.bio_vi IS NOT NULL AND p.bio_vi != '') AS bio_vi_saved,
                       tc.status AS draft_status,
                       d.han_viet_charwise AS hv_charwise,
                       d.han_viet_legacy AS hv_legacy,
                       d.han_viet_validation_status AS hv_status_col,
                       d.han_viet_validation_reason AS hv_reason,
                       d.legacy_match_status AS hv_legacy_match,
                       d.han_char_count AS hv_han_count,
                       d.han_viet_syllable_count AS hv_syll_count
                FROM people p
                LEFT JOIN {translation_cte} tc ON tc.entity_id = p.id
                LEFT JOIN person_hanviet_debug d ON d.person_id = p.id
                {where_sql}
                ORDER BY {
                    'CASE WHEN p.bio_vi IS NOT NULL AND p.bio_vi!=\'\' THEN 0 WHEN tc.status IS NOT NULL THEN 1 WHEN LENGTH(COALESCE(p.bio,\'\'))>0 THEN 2 ELSE 3 END ASC, p.id'
                    if sort_status == 'asc' else
                    'CASE WHEN p.bio_vi IS NOT NULL AND p.bio_vi!=\'\' THEN 0 WHEN tc.status IS NOT NULL THEN 1 WHEN LENGTH(COALESCE(p.bio,\'\'))>0 THEN 2 ELSE 3 END DESC, p.id'
                    if sort_status == 'desc' else
                    'p.id'
                }
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        conn.close()
        items = [dict(r) for r in rows]
        # T172 — gắn object hv (debug Hán-Việt charwise) cho từng item, không đổi field cũ
        _hv_cols = ('hv_charwise', 'hv_legacy', 'hv_status_col', 'hv_reason',
                    'hv_legacy_match', 'hv_han_count', 'hv_syll_count')
        for it in items:
            if it.get('hv_status_col'):
                it['hv'] = {
                    'charwise': it.get('hv_charwise'),
                    'legacy': it.get('hv_legacy'),
                    'status': it.get('hv_status_col'),
                    'reason': it.get('hv_reason'),
                    'legacy_match': it.get('hv_legacy_match'),
                    'han_count': it.get('hv_han_count'),
                    'syll_count': it.get('hv_syll_count'),
                }
            else:
                it['hv'] = None
            for _k in _hv_cols:
                it.pop(_k, None)
        # T186: bổ sung danh tăng VN từ ttl_persons khi có query q
        if q and fmt != 'csv':
            try:
                conn2 = get_db_connection()
                ttl_rows = conn2.execute(
                    "SELECT id, name_vi, name_zh FROM ttl_persons WHERE name_vi LIKE ? LIMIT 20",
                    (f'%{q}%',)
                ).fetchall()
                conn2.close()
                for tr in ttl_rows:
                    items.append({
                        "id": tr['id'], "name_zh": tr['name_zh'] or '', "name_vi": tr['name_vi'],
                        "name_en": None, "sect": None, "dynasty": None,
                        "birth_year": None, "death_year": None,
                        "has_bio_zh": False, "bio_vi_saved": False, "draft_status": None,
                        "source_type": "ttl_local",
                        "note": "Danh tăng VN — tài liệu TTL local (1 nguồn, chưa có trong DILA)",
                        "hv": None,
                    })
            except Exception:
                pass
        if fmt == 'csv':
            out = _io.StringIO()
            w = csv.DictWriter(out, fieldnames=['id','name_zh','name_vi','name_en','sect','dynasty',
                                                 'birth_year','death_year','has_bio_zh','bio_vi_saved','draft_status'])
            w.writeheader(); w.writerows(items)
            from flask import Response
            return Response(out.getvalue(), mimetype='text/csv',
                            headers={"Content-Disposition": "attachment;filename=dila_persons.csv"})
        return jsonify({"ok": True, "total": total, "limit": limit, "offset": offset, "items": items})
    except Exception as e:
        app.logger.error(f"api_dila_persons_search error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/dila/persons/adjacent')
def api_dila_persons_adjacent():
    """GET /daoanh/api/dila/persons/adjacent?id=A000011 → {prev_id, next_id}"""
    pid = request.args.get('id', '').strip()
    if not pid:
        return jsonify({"ok": False, "error": "missing id"}), 400
    try:
        conn = get_db_connection()
        nxt = conn.execute("SELECT id FROM people WHERE id > ? ORDER BY id LIMIT 1", (pid,)).fetchone()
        prv = conn.execute("SELECT id FROM people WHERE id < ? ORDER BY id DESC LIMIT 1", (pid,)).fetchone()
        conn.close()
        return jsonify({"ok": True, "prev_id": prv[0] if prv else None, "next_id": nxt[0] if nxt else None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/dila/persons/stats')
def api_dila_persons_stats():
    """GET /daoanh/api/dila/persons/stats — counts by sect/dynasty + translation coverage."""
    try:
        conn = get_db_connection()
        sects = conn.execute(
            "SELECT sect, COUNT(*) as n FROM people WHERE sect IS NOT NULL AND sect != '' GROUP BY sect ORDER BY n DESC LIMIT 20"
        ).fetchall()
        dynasties = conn.execute(
            "SELECT dynasty, COUNT(*) as n FROM people WHERE dynasty IS NOT NULL AND dynasty != '' GROUP BY dynasty ORDER BY n DESC LIMIT 20"
        ).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM people').fetchone()[0]
        with_bio = conn.execute(
            "SELECT COUNT(*) FROM people WHERE bio IS NOT NULL AND bio != ''"
        ).fetchone()[0]
        saved = conn.execute(
            "SELECT COUNT(*) FROM people WHERE bio_vi IS NOT NULL AND bio_vi != ''"
        ).fetchone()[0]
        drafted = conn.execute(
            "SELECT COUNT(DISTINCT entity_id) FROM translation_cache "
            "WHERE source_type='person_bio' AND status != 'invalidated'"
        ).fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "total": total, "with_bio_zh": with_bio,
                        "translated_saved": saved, "translated_draft": drafted,
                        "by_category": [{"note_category": r['sect'], "n": r['n']} for r in sects],
                        "by_country": [{"country": r['dynasty'], "n": r['n']} for r in dynasties]})
    except Exception as e:
        app.logger.error(f"api_dila_persons_stats error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/chronology/events')
def api_chronology_events():
    """
    GET /daoanh/api/chronology/events?century=7&dynasty=唐&limit=200
    Returns timeline events from lineage_chronology with GPS coordinates
    when available (matched against places_dila by name_zh).
    """
    try:
        century = request.args.get('century', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        limit = min(int(request.args.get('limit', 200)), 500)
        offset = int(request.args.get('offset', 0))

        conn = get_chronology_conn()
        where = []
        params = []

        if dynasty:
            where.append("c.dynasty = ?")
            params.append(dynasty)
        if century:
            c = int(century)
            where.append("c.century_start <= ? AND (c.century_end >= ? OR c.century_end IS NULL)")
            params.extend([c, c])

        where_sql = " AND ".join(where) if where else "1=1"

        rows = conn.execute(f"""
            SELECT c.id, c.title, c.title_zh, c.century_start, c.century_end,
                   c.dynasty, c.category, c.data_source,
                   p.name_vi, p.bio,
                   pl.name_zh as place_name, pl.geo_lat, pl.geo_long,
                   pl.district
            FROM lineage_chronology c
            LEFT JOIN people p ON p.id = c.id AND c.category = 'person'
            LEFT JOIN places_dila pl ON pl.name_zh = c.title_zh
            WHERE {where_sql}
            ORDER BY c.century_start NULLS LAST, c.title_zh
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()
        conn.close()

        results = []
        for r in rows:
            item = dict(r)
            # Clean up: only include geo if both coords present
            if not item.get('geo_lat') or not item.get('geo_long'):
                item['geo_lat'] = None
                item['geo_long'] = None
            # Sanitize Vietnamese text fields
            if item.get('name_vi'):
                item['name_vi'] = _ensure_vietnamese(item['name_vi'])
            if item.get('title'):
                item['title'] = _ensure_vietnamese(item['title'])
            if item.get('place_name'):
                item['place_name'] = _ensure_vietnamese(item['place_name'])
            results.append(item)

        return jsonify({
            "ok": True,
            "count": len(results),
            "has_gps": sum(1 for r in results if r.get('geo_lat')),
            "results": results
        })

    except Exception as e:
        import traceback
        app.logger.error(f"api_chronology_events error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/chronology/dynasties')
def api_chronology_dynasties():
    """List all dynasties with counts, century range"""
    try:
        conn = get_chronology_conn()
        rows = conn.execute("""
            SELECT dynasty, COUNT(*) as count,
                   MIN(century_start) as min_century,
                   MAX(century_end) as max_century
            FROM lineage_chronology
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return jsonify({"ok": True, "dynasties": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/chronology/search')
def api_chronology_search():
    """Search lineage_chronology by dynasty, century, category, or text"""
    try:
        dynasty = request.args.get('dynasty', '').strip()
        century = request.args.get('century', '').strip()
        category = request.args.get('category', '').strip()
        q = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 50)), 200)

        conn = get_chronology_conn()
        where = []
        params = []

        if dynasty:
            where.append("dynasty = ?")
            params.append(dynasty)
        if century:
            c = int(century)
            where.append("century_start <= ? AND (century_end >= ? OR century_end IS NULL)")
            params.extend([c, c])
        if category:
            where.append("category = ?")
            params.append(category)
        if q:
            where.append("(title LIKE ? OR title_zh LIKE ? OR id LIKE ?)")
            p = f'%{q}%'
            params.extend([p, p, p])

        sql = "SELECT * FROM lineage_chronology"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY century_start NULLS LAST LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return jsonify({"ok": True, "count": len(rows), "results": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/chronology/<chronology_id>')
def api_chronology_detail(chronology_id):
    """Get one chronology record by ID"""
    try:
        conn = get_chronology_conn()
        row = conn.execute("""
            SELECT * FROM lineage_chronology WHERE id = ?
        """, (chronology_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({"ok": False, "error": "Not found"}), 404
        return jsonify({"ok": True, "data": dict(row)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/t50-progress')
def t50_translation_progress():
    """GET /daoanh/api/admin/t50-progress — T50: tiến độ dịch passage theo từng bộ kinh."""
    SIGLA_NAMES = {
        'T51n2076': 'Chỉ Nguyệt Lục (指月錄)',
        'T50n2061': 'Cảnh Đức Truyền Đăng Lục (景德傳燈錄)',
        'T50n2060': 'Tổ Đường Tập (祖堂集)',
        'X77n1524': 'Ngũ Đăng Hội Nguyên (五燈會元)',
        'T50n2062': 'Thiên Thánh Quảng Đăng Lục (天聖廣燈錄)',
    }
    try:
        conn = get_db_connection()

        # Tổng quan toàn DB
        total_all = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        translated_all = conn.execute("SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL").fetchone()[0]
        draft_all = conn.execute("SELECT COUNT(*) FROM passage WHERE translation_draft=1").fetchone()[0]
        cache_all = conn.execute("SELECT COUNT(*) FROM translation_cache WHERE source_type='passage'").fetchone()[0]
        reported_all = conn.execute(
            "SELECT COUNT(*) FROM translation_cache WHERE source_type='passage' AND status='reported'"
        ).fetchone()[0]

        # Passage gắn địa danh (target thực tế của T50)
        place_total = conn.execute(
            "SELECT COUNT(DISTINCT p.passage_id) FROM passage p JOIN passage_entity pe ON pe.passage_id=p.passage_id"
        ).fetchone()[0]
        place_translated = conn.execute(
            "SELECT COUNT(DISTINCT p.passage_id) FROM passage p JOIN passage_entity pe ON pe.passage_id=p.passage_id WHERE p.vi_text IS NOT NULL"
        ).fetchone()[0]

        # Per-sigla (theo text_id)
        rows = conn.execute("""
            SELECT text_id,
                   COUNT(*) as total,
                   SUM(CASE WHEN vi_text IS NOT NULL THEN 1 ELSE 0 END) as translated,
                   SUM(CASE WHEN translation_draft=1 THEN 1 ELSE 0 END) as draft_ai
            FROM passage
            GROUP BY text_id
            ORDER BY total DESC
        """).fetchall()

        sigla_list = []
        for r in rows:
            tid = r['text_id'] or 'unknown'
            total = r['total'] or 0
            translated = r['translated'] or 0
            draft = r['draft_ai'] or 0
            remaining = total - translated
            pct = round(translated / total * 100, 1) if total else 0
            sigla_list.append({
                'sigla': tid,
                'name': SIGLA_NAMES.get(tid, tid),
                'total': total,
                'translated': translated,
                'draft_ai': draft,
                'remaining': remaining,
                'pct': pct,
            })

        # Mẫu 5 passage mới nhất đã dịch
        recent = conn.execute("""
            SELECT p.passage_id, p.text_id, p.loc_ref,
                   SUBSTR(p.raw_text,1,80) as raw_preview,
                   SUBSTR(p.vi_text,1,100) as vi_preview,
                   p.translation_draft
            FROM passage p
            WHERE p.vi_text IS NOT NULL
            ORDER BY p.passage_id DESC
            LIMIT 5
        """).fetchall()

        return jsonify({
            "ok": True,
            "summary": {
                "total_all": total_all,
                "translated_all": translated_all,
                "draft_ai": draft_all,
                "remaining_all": total_all - translated_all,
                "pct_all": round(translated_all / total_all * 100, 1) if total_all else 0,
                "place_total": place_total,
                "place_translated": place_translated,
                "place_remaining": place_total - place_translated,
                "place_pct": round(place_translated / place_total * 100, 1) if place_total else 0,
                "translation_cache": cache_all,
                "reported": reported_all,
            },
            "by_sigla": sigla_list,
            "recent_translated": [dict(r) for r in recent],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})



@app.route('/daoanh/api/admin/search_all')
def search_all():
    try:
        q = (request.args.get('q', '') or '').strip()
        if not q:
            return jsonify({"success": True, "places": []})
        conn = get_db_connection()
        like = f'%{q}%'
        place_rows = conn.execute("""
            SELECT p.id, p.name_zh,
                   COALESCE(m.name_vi, p.name_vi) AS name_vi,
                   d.note_category, d.district,
                   CASE
                       WHEN d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%' THEN 'temple_site'
                       WHEN d.note_category LIKE '%山峰%' OR d.note_category LIKE '%山脈%' THEN 'mountain'
                       WHEN d.note_category LIKE '%河流%' OR d.note_category LIKE '%湖泊%' OR d.note_category LIKE '%水系%' THEN 'river_lake'
                       WHEN d.note_category LIKE '%人文地理區域%' THEN 'dynasty_region'
                       WHEN d.note_category LIKE '%自然地理區域%' THEN 'other'
                       ELSE 'admin_place'
                   END AS cate_internal
            FROM places_pending p
            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
            LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
            WHERE p.id LIKE ? OR p.name_zh LIKE ? OR COALESCE(m.name_vi, p.name_vi) LIKE ?
            ORDER BY
                CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                p.id ASC
            LIMIT 50
        """, (like, like, like, q, like)).fetchall()

        person_rows = conn.execute("""
            SELECT pe.id, pe.name_zh,
                   pe.name_vi AS name_vi,
                   pe.dynasty AS district,
                   NULL AS note_category,
                   'person' AS cate_internal
            FROM people pe
            WHERE pe.id LIKE ? OR pe.name_zh LIKE ?
               OR pe.name_vi LIKE ?
            ORDER BY
                CASE WHEN pe.id = ? THEN 0 WHEN pe.id LIKE ? THEN 1 ELSE 2 END,
                pe.id ASC
            LIMIT 50
        """, (like, like, like, q, like)).fetchall()

        # Tìm theo tên tiếng Việt trong vn_person_authority (tên chuẩn hơn people.name_vi)
        auth_rows = conn.execute("""
            SELECT va.dila_id AS id,
                   COALESCE(NULLIF(va.name_zh,''), pe.name_zh) AS name_zh,
                   va.name_vi AS name_vi,
                   pe.dynasty AS district,
                   NULL AS note_category,
                   'person' AS cate_internal
            FROM vn_person_authority va
            LEFT JOIN people pe ON pe.id = va.dila_id
            WHERE va.name_vi LIKE ?
            ORDER BY CASE WHEN va.status = 'verified' THEN 0 ELSE 1 END,
                     va.dila_id ASC
            LIMIT 50
        """, (like,)).fetchall()

        conn.close()
        places = []
        seen = set()
        for r in list(place_rows) + list(auth_rows) + list(person_rows):
            row = dict(r)
            rid = row['id']
            if rid.startswith('PL'):
                lid = ensure_long_id(rid)
            else:
                lid = rid
            if lid in seen:
                continue
            seen.add(lid)
            row['id'] = lid
            places.append(row)
        return jsonify({"success": True, "places": places})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/search')
def api_global_search():
    """GET /daoanh/api/search?q=<text>&lang=<vi|zh|pa|sa> — HOME page ("Tìm kiếm thiền sư, chùa chiền, kinh sách")
    global search. index.html has called this exact path/shape since it was built
    (data.monks/data.places/data.works, see displayResults() there) but the route
    never existed on the backend — 404 the entire time (found 2026-08-21 while
    checking what T01/T29's name_vi fix actually surfaces on HOME).

    Three sources, each already established/trusted elsewhere in this app:
      monks  -> people.name_vi/name_zh (T01/T29 just brought this to 100% non-empty)
      places -> places_pending + namevi_map_places (same COALESCE pattern as
                the persons/places endpoints elsewhere)
      works  -> cbeta_catalog_vn (Nguyễn Minh Tiến, CC BY-SA — already listed as a
                trusted source in CLAUDE.md, same table T-series "Kinh Điển Liên
                Quan" reads from)
    """
    q = request.args.get('q', '').strip()
    lang = request.args.get('lang', '').strip().lower()
    if not q or len(q) < 2:
        return jsonify({"success": True, "monks": [], "places": [], "works": []})
    conn = get_db_connection()
    like = f'%{q}%'
    try:
        monks = conn.execute("""
            SELECT id, name_vi, name_zh FROM people
            WHERE name_vi LIKE ? OR name_zh LIKE ?
            ORDER BY LENGTH(name_vi) ASC LIMIT 10
        """, (like, like)).fetchall()

        # T58: lang=pa/sa — tra Pali/Sanskrit qua pali_place_ref (15 địa danh, không
        # bảng mới). Chỉ 2 mã ngôn ngữ này có seed thật; 'en' hoặc ngôn ngữ khác
        # KHÔNG được map vì không có nguồn (xem ghi chú "Phần spec chưa làm" trong
        # tasks/T58-tim-kiem-thong-minh.md).
        pali_dila_ids = []
        if lang in ('pa', 'sa'):
            pali_dila_ids = _pali_sanskrit_lookup(q, conn)

        # Places: FTS5 (places_pending_fts) instead of LIKE — a LEFT JOIN + leading-
        # wildcard LIKE across places_pending/namevi_map_places (118K/118K rows) took
        # ~2.5s per query in testing, too slow for a live search box. Same
        # prefix-match pattern already proven in places_search() (T11 fix).
        #
        # IMPORTANT: an empty FTS result is a real, correct answer (most monk-only
        # queries genuinely match zero places) — it must NOT trigger the slow LIKE
        # fallback, or every such query pays the full ~2.5s scan anyway and the
        # optimization does nothing. The LIKE fallback below only runs if FTS itself
        # raised (a real failure to query it), tracked via fts_failed.
        ensure_places_pending_fts(conn)
        place_ids = []
        fts_failed = False
        try:
            terms = [re.sub(r'["*():+\-#@~^&]', '', t) + '*' for t in re.split(r'\s+', q.strip())[:6] if t]
            if terms:
                fq = ' '.join(terms)
                rows = conn.execute(
                    "SELECT id FROM places_pending_fts WHERE places_pending_fts MATCH ? LIMIT 10", (fq,)
                ).fetchall()
                place_ids = [r['id'] for r in rows]
        except Exception:
            fts_failed = True

        # T58: hợp nhất kết quả Pali/Sanskrit (nếu có) vào place_ids trước khi
        # query places_pending — union, giữ thứ tự, không trùng lặp.
        if pali_dila_ids:
            for pid in pali_dila_ids:
                if pid not in place_ids:
                    place_ids.append(pid)

        if place_ids:
            placeholders = ','.join('?' * len(place_ids))
            places = conn.execute(f"""
                SELECT p.id, COALESCE(m.name_vi, p.name_vi) AS name_vi, p.name_zh, p.province, p.gps_lat, p.gps_long
                FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE p.id IN ({placeholders})
            """, place_ids).fetchall()
        elif fts_failed:
            places = conn.execute("""
                SELECT p.id, COALESCE(m.name_vi, p.name_vi) AS name_vi, p.name_zh, p.province, p.gps_lat, p.gps_long
                FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE COALESCE(m.name_vi, p.name_vi) LIKE ? OR p.name_zh LIKE ?
                ORDER BY LENGTH(COALESCE(m.name_vi, p.name_vi)) ASC LIMIT 10
            """, (like, like)).fetchall()
        else:
            places = []

        works = conn.execute("""
            SELECT title_vi, title_zh, translator_vi AS author, dynasty_vi AS era
            FROM cbeta_catalog_vn
            WHERE title_vi LIKE ? OR title_zh LIKE ?
            ORDER BY LENGTH(title_vi) ASC LIMIT 10
        """, (like, like)).fetchall()

        # T453: kinh lục DILA (dila_catalog_works) — additive key, không đổi 3 key cũ.
        # Tên Hán/năm: DILA; title_vi/byline_vi: bản dịch Cloud (unreviewed);
        # tên người: people.name_vi (ZQLOCAL) — badge theo từng nguồn ở UI.
        dila_works = []
        dila_works_total = 0
        try:
            dw_where = """
                WHERE w.title_zh LIKE ? OR w.title_vi LIKE ? OR w.byline_zh LIKE ? OR w.byline_vi LIKE ?
                   OR w.cbeta_id = ? COLLATE NOCASE
                   OR w.cbeta_id IN (SELECT c.cbeta_id FROM dila_catalog_contributors c
                                     WHERE c.name_zh LIKE ? OR c.name_vi LIKE ?)"""
            dw_args = (like, like, like, like, q, like, like)
            # Tổng thật để UI ghi "hiển thị 10 / N" (danh sách vẫn giới hạn 10).
            dila_works_total = conn.execute(
                "SELECT COUNT(*) FROM dila_catalog_works w" + dw_where, dw_args).fetchone()[0]
            rows = conn.execute("""
                SELECT w.cbeta_id, w.authority_id, w.title_zh, w.title_vi, w.byline_zh, w.byline_vi,
                       w.dynasty_vi, w.category_vi, w.juans, w.time_from, w.time_to, w.year_precision,
                       w.vi_source, w.vi_status, w.vol, w.cjk_chars, w.category AS category_zh,
                       json_extract(w.raw_json, '$.orig_category') AS orig_category_zh,
                       json_extract(w.vi_json, '$.orig_category_vi') AS orig_category_vi,
                       (SELECT GROUP_CONCAT(COALESCE(m.name_vi, pl.name_zh), ', ')
                        FROM dila_catalog_places pl LEFT JOIN namevi_map_places m ON m.dila_id = pl.place_id
                        WHERE pl.cbeta_id = w.cbeta_id) AS places_vi
                FROM dila_catalog_works w""" + dw_where + """
                ORDER BY LENGTH(COALESCE(w.title_vi, w.title_zh)) ASC LIMIT 10
            """, dw_args).fetchall()
            for r in rows:
                d = dict(r)
                d["contributors"] = [dict(c) for c in conn.execute(
                    "SELECT c.person_id, c.name_zh, COALESCE(p.name_vi, c.name_vi) AS name_vi, c.name_vi_src "
                    "FROM dila_catalog_contributors c LEFT JOIN people p ON p.id = c.person_id "
                    "WHERE c.cbeta_id = ? ORDER BY c.seq", (d["cbeta_id"],)).fetchall()]
                d["source"] = "DILA_CATALOG"
                dila_works.append(d)
        except sqlite3.OperationalError:
            dila_works = []  # bảng T453 chưa có (DB chưa import) → bỏ qua

        # T453: thẻ người — ai trong kinh lục DILA khớp q (tên Việt DB/tên Hán), kèm tổng tác phẩm và nơi dịch.
        dila_people = []
        try:
            prows = conn.execute("""
                SELECT c.person_id, p.name_vi, p.name_zh,
                       COUNT(DISTINCT c.cbeta_id) AS works, SUM(w.juans) AS juans
                FROM dila_catalog_contributors c
                JOIN dila_catalog_works w ON w.cbeta_id = c.cbeta_id
                LEFT JOIN people p ON p.id = c.person_id
                WHERE c.person_id IN (SELECT person_id FROM dila_catalog_contributors
                                      WHERE name_vi LIKE ? OR name_zh LIKE ?)
                GROUP BY c.person_id ORDER BY works DESC LIMIT 3
            """, (like, like)).fetchall()
            for r in prows:
                d = dict(r)
                d["places"] = [dict(x) for x in conn.execute("""
                    SELECT pl.place_id, pl.name_zh, m.name_vi, COUNT(DISTINCT pl.cbeta_id) AS works
                    FROM dila_catalog_places pl
                    JOIN dila_catalog_contributors c ON c.cbeta_id = pl.cbeta_id
                    LEFT JOIN namevi_map_places m ON m.dila_id = pl.place_id
                    WHERE c.person_id = ? GROUP BY pl.place_id ORDER BY works DESC LIMIT 5
                """, (d["person_id"],)).fetchall()]
                dila_people.append(d)
        except sqlite3.OperationalError:
            dila_people = []

        resp = {
            "success": True,
            "monks": [dict(r) for r in monks],
            "places": [dict(r) for r in places],
            "works": [dict(r) for r in works],
            "dila_works": dila_works,
            "dila_works_total": dila_works_total,
            "dila_people": dila_people,
        }
        if lang in ('pa', 'sa'):
            # Additive: cho UI biết query đã được resolve qua pali_place_ref,
            # backward-compatible — không đổi field cũ.
            resp["cross_lang"] = {"lang": lang, "matched_dila_ids": pali_dila_ids,
                                   "source": "pali_place_ref"}
        return jsonify(resp)
    except Exception as e:
        app.logger.error(f"api_global_search error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()



@app.route('/daoanh/api/search/suggest')
def api_search_suggest():
    """GET /daoanh/api/search/suggest?q=<text> — T469: homepage autocomplete,
    grouped by entity type. NEW endpoint, additive — does NOT change
    /daoanh/api/search's response shape (that one is still consumed elsewhere,
    see its docstring above).

    Trả 2 nhóm:
      persons -> people.id/name_vi/name_zh/dynasty/birth_year/death_year (bảng
                 'people', cùng nguồn "monks" mà api_global_search() dùng) —
                 kèm dynasty/birth_year/death_year làm phụ chú phân biệt tên
                 trùng (vd Huyền Trang có 4 id A000294/A002949/A009306/A014708).
      works   -> cbeta_catalog_vn.title_vi/title_zh/translator_vi/dynasty_vi.
                 translator_vi ĐÃ CÓ SẴN trong cbeta_catalog_vn (đã kiểm schema
                 bằng sqlite_master.sql: cột translator_vi tồn tại, và
                 api_global_search() ở trên cũng SELECT nó làm w.author) —
                 KHÔNG cần JOIN dila_catalog_contributors/dila_catalog_works.

    Nhận diện có dấu/không dấu: tái dùng normalize_text() (định nghĩa ở đầu
    file, dòng ~102, đã dùng cho lexicon/TTL) để chuẩn hoá cả câu query và
    tên/tiêu đề trong cache — không viết lại thuật toán bỏ dấu.

    EXPLAIN QUERY PLAN cho câu SELECT xây cache (đo 2026-10-26, xem report
    T469): SCAN people / SCAN cbeta_catalog_vn — full scan, giống hệt tình
    trạng hiện có của monks/works trong api_global_search() ở trên (cũng
    SCAN TABLE, không index trên name_vi/name_zh/title_vi/title_zh). KHÔNG
    tạo index/đổi schema ở đây — xây cache 1 lần trong RAM (xem trên) để đạt
    mục tiêu <1s ở trạng thái "ấm" mà không cần động tới DB.
    """
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({"success": True, "persons": [], "works": []})
    try:
        nq = normalize_text(q)

        t0 = time.perf_counter()
        persons_cache = _get_person_suggest_cache()
        persons = []
        for r in persons_cache:
            if nq in r['_norm_vi'] or nq in r['_norm_zh']:
                persons.append({k: v for k, v in r.items() if not k.startswith('_')})
                if len(persons) >= 8:
                    break
        t_persons_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        works_cache = _get_work_suggest_cache()
        works = []
        for r in works_cache:
            if nq in r['_norm_vi'] or nq in r['_norm_zh']:
                works.append({k: v for k, v in r.items() if not k.startswith('_')})
                if len(works) >= 8:
                    break
        t_works_ms = (time.perf_counter() - t1) * 1000

        app.logger.info(
            f"api_search_suggest q={q!r} persons={len(persons)} ({t_persons_ms:.1f}ms) "
            f"works={len(works)} ({t_works_ms:.1f}ms)"
        )

        return jsonify({
            "success": True,
            "persons": persons,
            "works": works,
            "_timing_ms": {"persons": round(t_persons_ms, 1), "works": round(t_works_ms, 1)},
        })
    except Exception as e:
        app.logger.error(f"api_search_suggest error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/public/dila_works')
def public_dila_works():
    """T453: toàn bộ tác phẩm kinh lục DILA của một người (nút "Xem tất cả" trên HOME).
    GET ?person_id=A000294&sort=juans|year|title"""
    pid = request.args.get('person_id', '').strip()
    sort = request.args.get('sort', 'juans')
    if not pid:
        return jsonify({"success": False, "error": "person_id required"}), 400
    # Năm chỉ là khung triều đại → xếp sau các bộ có năm cụ thể.
    order = {"year": "w.time_from IS NULL, w.year_precision = 'dynasty_range', w.time_from, w.cbeta_id",
             "title": "COALESCE(w.title_vi, w.title_zh)"}.get(sort, "COALESCE(w.juans, 0) DESC, w.cbeta_id")
    conn = get_db_connection()
    try:
        rows = conn.execute(f"""
            SELECT w.cbeta_id, w.title_zh, w.title_vi, w.byline_zh, w.byline_vi, w.dynasty_vi,
                   w.juans, w.time_from, w.time_to, w.year_precision,
                   (SELECT GROUP_CONCAT(COALESCE(m.name_vi, pl.name_zh), ', ')
                    FROM dila_catalog_places pl LEFT JOIN namevi_map_places m ON m.dila_id = pl.place_id
                    WHERE pl.cbeta_id = w.cbeta_id) AS places_vi
            FROM dila_catalog_works w
            WHERE w.cbeta_id IN (SELECT cbeta_id FROM dila_catalog_contributors WHERE person_id = ?)
            ORDER BY {order}
        """, (pid,)).fetchall()
        return jsonify({"success": True, "person_id": pid, "sort": sort,
                        "count": len(rows), "works": [dict(r) for r in rows]})
    except sqlite3.OperationalError:
        return jsonify({"success": True, "person_id": pid, "count": 0, "works": []})
    finally:
        conn.close()




@app.route('/daoanh/api/public/search')
def public_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"success": True, "data": []})
    conn = get_db_connection()
    like = f'%{q}%'
    mapped = conn.execute(
        "SELECT id, name_vi, name_zh FROM namevi_map_places WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 15",
        (like, like)
    ).fetchall()
    all_results = [dict(r) for r in mapped]
    if len(all_results) < 15:
        remaining = 15 - len(all_results)
        pending = conn.execute(
            "SELECT id, name_zh as name_vi, name_zh FROM places_pending WHERE name_zh LIKE ? LIMIT ?",
            (like, remaining)
        ).fetchall()
        all_results += [dict(r) for r in pending]
    conn.close()
    for r in all_results:
        if r.get('id'):
            r['id'] = ensure_long_id(r['id'])
    return jsonify({"success": True, "data": all_results})



@app.route('/api/dossier/<dila_id>')
def api_dossier(dila_id):
    """
    GET /api/dossier/<dila_id>
    Get full dossier from DILA and Marcus for both columns.
    Includes TTL file fallback when not in DB.
    """
    # Strip TS- prefix if present
    lookup_id = dila_id
    if lookup_id.startswith('TS-'):
        lookup_id = lookup_id[3:]
    
    dila_data = get_dila_data(lookup_id)
    
    # FALLBACK: Parse TTL directly if not in DB - Extract ALL info
    ttl_content = ""
    ttl_file = ""
    if not dila_data:
        # Try to find TTL file by ID or filename pattern
        for f in os.listdir(TTL_OLD_DIR):
            if lookup_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                with open(ttl_file, 'r', encoding='utf-8') as fp:
                    ttl_content = fp.read()
                break
        
        if ttl_content:
            # Parse COMPLETE info from TTL
            import re
            
            # 1. Name VI from rdfs:label (main label only)
            label_match = re.search(r'rdfs:label\s+"([^"]+)"@vi', ttl_content)
            name_vi = label_match.group(1) if label_match else lookup_id
            
            # 2. Parse all names - find all appellation blocks
            all_names = []
            dharma_names = []
            secular_names = []
            
            # Find each block between [ and ]
            app_blocks = re.finditer(r'\[([^\]]+)\]', ttl_content)
            for block in app_blocks:
                block_text = block.group(1)
                name_match = re.search(r'rdfs:label\s+"([^"]+)"@([a-z]{2})', block_text)
                type_match = re.search(r'bkg:hasAppellationType\s+"bkg:(\w+)"', block_text)
                if name_match and type_match:
                    name = name_match.group(1)
                    app_type = type_match.group(1)
                    all_names.append({'name': name, 'lang': name_match.group(2), 'type': app_type})
                    if app_type == 'DharmaName':
                        dharma_names.append(name)
                    elif app_type == 'SecularName':
                        secular_names.append(name)
            
            # 3. Dharma lineage
            lineage_match = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"', ttl_content)
            lineage = lineage_match.group(1) if lineage_match else ''
            
            # 4. Birth/Death years - from event resources (E67_Birth, E69_Death)
            birth_match = re.search(r'a\s+crm:E67_Birth.*?crm:P4_has_time-span\s+"(\d{3,4})"', ttl_content, re.DOTALL)
            birth_year = int(birth_match.group(1)) if birth_match else None
            death_match = re.search(r'a\s+crm:E69_Death.*?crm:P4_has_time-span\s+"(\d{3,4})"', ttl_content, re.DOTALL)
            death_year = int(death_match.group(1)) if death_match else None
            
            # 5. Dynasty
            dynasty_match = re.search(r'bkg:dynasty\s+"([^"]+)"', ttl_content)
            dynasty = dynasty_match.group(1) if dynasty_match else ''
            
            # 6. Biographical note - single-line format (TTL uses " not """)
            bio_match = re.search(r'bkg:biographicalNote\s+"([^"]+)"', ttl_content)
            bio = bio_match.group(1)[:1000] if bio_match else ''
            
            # 7. Associated places - resolve to Vietnamese names
            places_matches = re.findall(r'bkg:associatedPlaces\s+<ex:place/([^>]+)>', ttl_content)
            # Resolve place IDs to names from TTL
            places_with_names = []
            place_label_map = {}
            for pm in re.finditer(r'<ex:place/([^>]+)>\s+rdfs:label\s+"([^"]+)"', ttl_content):
                place_label_map[pm.group(1)] = pm.group(2)
            for pid in places_matches:
                places_with_names.append({'id': pid, 'name_vi': place_label_map.get(pid, pid)})
            
            # 8. Authored works - resolve to names from TTL
            works_matches = re.findall(r'bkg:authoredWorks\s+<ex:work/([^>]+)>', ttl_content)
            work_label_map = {}
            for wm in re.finditer(r'<ex:work/([^>]+)>\s+rdfs:label\s+"([^"]+)"', ttl_content):
                work_label_map[wm.group(1)] = wm.group(2)
            works_with_names = []
            for wid in works_matches:
                works_with_names.append({'id': wid, 'title': work_label_map.get(wid, wid)})
            
            dila_data = {
                'id': lookup_id,
                'name_vi': name_vi,
                'name_zh': next((n['name'] for n in all_names if n['lang'] == 'zh'), ''),
                'all_names': all_names,
                'dharma_names': dharma_names,
                'secular_names': dharma_names[:1] if dharma_names else [],  # First dharma name as fallback secular
                'lineage': lineage,
                'birth_year': birth_year,
                'death_year': death_year,
                'dynasty': dynasty,
                'bio': bio,
                'places': places_with_names,
                'works': works_with_names,
                'ttl_filename': os.path.basename(ttl_file) if ttl_file else ''
            }
    
    if not dila_data:
        return jsonify({'error': 'Person not found: ' + dila_id}), 404
    
    # Use lookup_id for all further operations
    dila_id = lookup_id
    
    # LOOKUP DILA ID from ttl_mapping for Marcus query
    conn = get_db()
    try:
        # Try multiple patterns to find DILA ID
        search_patterns = [
            f"TS-{lookup_id}",
            lookup_id,
            f"{lookup_id}.ttl"
        ]
        marcus_lookup_id = dila_id
        for pattern in search_patterns:
            row = conn.execute(
                "SELECT dila_id FROM ttl_mapping WHERE ttl_filename = ? OR name_vi = ?",
                (pattern, lookup_id)
            ).fetchone()
            if row:
                marcus_lookup_id = row[0]
                break
    except:
        marcus_lookup_id = dila_id
    finally:
        conn.close()
    
    marcus_data = get_marcus_data(marcus_lookup_id)
    is_conflict, dila_lineage, marcus_lineage = check_lineage_conflict(marcus_lookup_id)
    
    # Read TTL content for bio - use lookup_id for file search
    ttl_content = ""
    ttl_file = os.path.join(TTL_OLD_DIR, f"{lookup_id}.ttl")
    if not os.path.exists(ttl_file):
        # Try to find by name pattern
        for f in os.listdir(TTL_OLD_DIR):
            if dila_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                break
    
    if os.path.exists(ttl_file):
        with open(ttl_file, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
    
    # Extract biographical note - single-line format
    bio_match = re.search(r'bkg:biographicalNote\s+"([^"]+)"', ttl_content)
    bio = bio_match.group(1)[:1000] if bio_match else (dila_data.get('bio', '') or '')
    
    # Prepare all TTL-sourced fields
    ttl_data = dila_data if dila_data.get('ttl_filename') else {}
    
    return jsonify({
        'id': dila_id,
        'name_vi': dila_data.get('name_vi', ''),
        'zh': dila_data.get('name_zh', ''),
        'ttl_filename': dila_data.get('ttl_filename', ''),
        'ttl_content_full': ttl_content,  # Raw TTL for VPS Column 2
        'dila_data': {
            'birth': dila_data.get('birth_year'),
            'death': dila_data.get('death_year'),
            'lineage': dila_data.get('lineage', ''),
            'dynasty': dila_data.get('dynasty', ''),
            'bio': bio[:800],
            'all_names': ttl_data.get('all_names', []),
            'dharma_names': ttl_data.get('dharma_names', []),
            'secular_names': ttl_data.get('secular_names', []),
            'places': ttl_data.get('places', []),
            'works': ttl_data.get('works', [])
        },
        'marcus_data': {
            'lineage': marcus_lineage or dila_data.get('lineage', ''),
            'teachers': marcus_data.get('teachers', []) if marcus_data else [],
            'students': marcus_data.get('students', []) if marcus_data else [],
            'edges': marcus_data.get('edge_count', 0) if marcus_data else 0
        },
        'conflict': is_conflict,
        'dila_lineage': dila_lineage or dila_data.get('lineage', ''),
        'marcus_lineage': marcus_lineage,
        'ttl_content': ttl_content[:3000]  # Preview in Col 5
    })



@app.route('/api/marcus_network/<person_id>')
def api_marcus_network(person_id):
    """Get Marcus network data for person"""
    conn = get_db()
    try:
        # Teachers (people who taught this person)
        teachers = conn.execute("""
            SELECT teacher_id, teacher_label, ref
            FROM marcus_networks
            WHERE student_id = ?
        """, (person_id,)).fetchall()
        
        # Students (people this person taught)
        students = conn.execute("""
            SELECT student_id, student_label, ref
            FROM marcus_networks
            WHERE teacher_id = ?
        """, (person_id,)).fetchall()
        
        return jsonify({
            'person_id': person_id,
            'teachers': [dict(t) for t in teachers],
            'students': [dict(s) for s in students],
            'teacher_count': len(teachers),
            'student_count': len(students)
        })
    finally:
        conn.close()



@app.route('/daoanh/api/admin/lineage-conflicts')
def admin_lineage_conflicts():
    """GET — danh sách conflict CHƯA xử lý (lineage_conflicts_v2) kèm dấu vết review (en_audit_log).
    Read-only; doc mới, không sửa /api/conflicts hiện có."""
    conn = get_db()
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        ctype = request.args.get('type', None)

        where = "WHERE c.resolved = 0"
        params = []
        if ctype:
            where += " AND c.conflict_type = ?"
            params.append(ctype)

        rows = conn.execute(f"""
            SELECT c.id, c.person_id, c.label, c.name_vi, c.conflict_type,
                   c.dila_count, c.marcus_count, c.notes, c.created_at,
                   a.verification_status AS last_verdict, a.editor AS last_editor,
                   a.created_at AS last_reviewed_at
            FROM lineage_conflicts_v2 c
            LEFT JOIN (
                SELECT entity_ref, MAX(log_id) AS m
                FROM en_audit_log WHERE action = 'resolve_lineage_conflict' GROUP BY entity_ref
            ) lastlog ON lastlog.entity_ref = c.person_id
            LEFT JOIN en_audit_log a ON a.log_id = lastlog.m
            {where}
            ORDER BY c.id LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()

        total_open = conn.execute(
            f"SELECT COUNT(*) AS n FROM lineage_conflicts_v2 c {where}", params).fetchone()[0]

        return jsonify({
            'conflicts': [dict(r) for r in rows],
            'count': len(rows),
            'total_open': total_open,
            'status': 'ok'
        })
    finally:
        conn.close()



@app.route('/daoanh/api/admin/lineage-conflicts/<int:conflict_id>/resolve', methods=['POST'])
def admin_lineage_conflict_resolve(conflict_id):
    """POST — ghi verdict conflict: UPDATE resolved=1 + INSERT en_audit_log (Lean, Zero-ALTER).
    dila_data/marcus_data bất biến (minh chứng gốc); verdict ghi qua UPDATE + audit sổ.
    T136 (2026-09-14): thêm resolution_type ∈ pick|merge|reject — đóng đặc tả
    'T115/T109 Lineage Consensus' §2 "chọn 1 giá trị, gộp, hoặc bác bỏ cả hai".
    Mặc định 'pick' → tương thích tuyệt đối với caller cũ (conflicts.html không gửi type)."""
    data = request.get_json(force=True, silent=True) or {}
    resolution_type = (data.get('resolution_type') or 'pick').strip()
    winner = data.get('winner_source_id', 'dila')          # 'dila' | 'marcus' (pick) | 'both' (merge) | 'none' (reject)
    editor = (data.get('editor') or '').strip() or 'admin'
    reason = (data.get('reason') or '').strip()

    if resolution_type not in ('pick', 'merge', 'reject'):
        return jsonify({'status': 'error', 'message': 'resolution_type phải ∈ pick|merge|reject'}), 400
    if resolution_type == 'pick' and winner not in ('dila', 'marcus'):
        return jsonify({'status': 'error', 'message': 'pick: winner_source_id phải ∈ dila|marcus'}), 400

    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM lineage_conflicts_v2 WHERE id=?", (conflict_id,)).fetchone()
        if row is None:
            return jsonify({'status': 'error', 'message': f'conflict #{conflict_id} không tồn tại'}), 404
        if row['resolved']:
            return jsonify({'status': 'error', 'message': f'conflict #{conflict_id} đã resolved'}), 409

        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        old_value = f"dila={row['dila_data']} | marcus={row['marcus_data']}"
        if resolution_type == 'pick':
            new_value, rk = winner, ('DILA' if winner == 'dila' else 'MARCUS')
            note_tag = 'T109 winner=' + winner
        elif resolution_type == 'merge':
            new_value, rk = 'both', 'DILA+MARCUS'
            note_tag = 'T136 merge: giu ca hai'
        else:
            new_value, rk = 'rejected', 'NONE'
            note_tag = 'T136 reject: bac bo ca hai'
        conn.execute("""
            UPDATE lineage_conflicts_v2
            SET resolved = 1, notes = COALESCE(?, '') || ' | ' || ?
            WHERE id = ?
        """, (reason, note_tag, conflict_id))
        cur = conn.execute("""
            INSERT INTO en_audit_log
                (entity_ref, action, field_name, old_value, new_value, evidence_sources,
                 authority_rank, editor, verification_status, created_at)
            VALUES (?, 'resolve_lineage_conflict', ?, ?, ?, ?, ?, ?, 'verified', ?)
        """, (row['person_id'], row['conflict_type'], old_value, new_value,
              f"dila_count={row['dila_count']}, marcus_count={row['marcus_count']} | resolution_type={resolution_type}",
              rk, editor, now))
        conn.commit()
        return jsonify({'status': 'ok', 'conflict_id': conflict_id,
                        'resolution_type': resolution_type,
                        'winner_source_id': new_value, 'audit_log_id': cur.lastrowid})
    finally:
        conn.close()



@app.route('/daoanh/api/monk-resolve')
def api_monk_resolve():
    """
    GET /daoanh/api/monk-resolve?name=<name>
    (path deliberately avoids /daoanh/api/monk/<monk_id> - that generic
    dynamic route intercepts any single path segment under /monk/, including
    a literal "resolve", before this handler would ever be reached)
    Resolve a monk name (Vietnamese or Chinese) to a DILA person id via the
    bulk `people` table (48k+ rows) - used because monk_dict is still mostly
    unpopulated (see Task 1). Exact match first, then LIKE fallback.
    """
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({"ok": False, "error": "name required"}), 400
    conn = get_db_connection()
    try:
        match_type = None
        row = conn.execute(
            "SELECT id, name_zh, name_vi, dynasty FROM people WHERE name_vi = ? OR name_zh = ? LIMIT 1",
            (name, name)
        ).fetchone()
        if row:
            match_type = 'exact_name_vi' if (row['name_vi'] or '') == name else 'exact_name_zh'
        if not row:
            like = f'%{name}%'
            row = conn.execute(
                "SELECT id, name_zh, name_vi, dynasty FROM people WHERE name_vi LIKE ? OR name_zh LIKE ? ORDER BY LENGTH(name_vi) ASC LIMIT 1",
                (like, like)
            ).fetchone()
            if row:
                match_type = 'fuzzy_name_vi' if name in (row['name_vi'] or '') else 'fuzzy_name_zh'
        # Fallback: tìm trong vn_person_authority (tên 4 chữ TTL như Đơn Hà Thiên Nhiên,
        # Thúy Vi Vô Học) — people.name_vi chỉ lưu 2 chữ nên không match được.
        if not row:
            like = f'%{name}%'
            vpa = conn.execute(
                "SELECT dila_id FROM vn_person_authority WHERE name_vi LIKE ? AND dila_id IS NOT NULL AND dila_id != '' ORDER BY LENGTH(name_vi) ASC LIMIT 1",
                (like,)
            ).fetchone()
            if vpa and vpa['dila_id']:
                row = conn.execute(
                    "SELECT id, name_zh, name_vi, dynasty FROM people WHERE id=?",
                    (vpa['dila_id'],)
                ).fetchone()
                if row:
                    # [T200] dùng helper có ORDER BY xác định (dila_id KHÔNG unique).
                    vpa_full = _t200_vnpa_lookup_by_dila(conn, vpa['dila_id'])
                    row = dict(row)
                    if vpa_full:
                        if vpa_full['name_vi']:
                            row['name_vi'] = vpa_full['name_vi']
                        if vpa_full['name_zh']:
                            row['name_zh'] = vpa_full['name_zh']
                    match_type = 'authority_vi'
        if not row:
            # BUG-015: "not found" is an expected outcome for a name-resolver
            # endpoint (e.g. a place name typed into the combined place/monk
            # search box), not a server error — return 200 so callers can
            # safely call r.json() without special-casing non-2xx status.
            return jsonify({"ok": False, "error": "not found", "results": []}), 200
        return jsonify({"ok": True, "person": dict(row), "match_type": match_type, "matched_query": name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/monk/<dila_id>/marcus-network')
def api_monk_marcus_network(dila_id):
    """
    GET /daoanh/api/monk/<dila_id>/marcus-network
    Task 4 (Marcus term glossaries -> people/works integration).
    Returns teacher/student lineage relations for a DILA person from the real
    Marcus (Bingenheimer ChineseBuddhism_SNA) dataset — marcus_reference /
    marcus_networks tables, joined via marcus_people_link (id-match, additive,
    read-only; does not touch people/marcus_reference/marcus_networks).
    Distinct from the pre-existing /api/monk/<id>/marcus route, which reads
    TTL files and is unrelated to this dataset.
    """
    conn = get_db_connection()
    try:
        person = conn.execute(
            "SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if not person:
            return jsonify({"ok": False, "error": "person not found"}), 404

        link = conn.execute(
            "SELECT marcus_node_id, match_confidence FROM marcus_people_link WHERE person_id = ?",
            (dila_id,)
        ).fetchone()
        if not link:
            return jsonify({
                "ok": True,
                "person": dict(person),
                "linked": False,
                "teachers": [],
                "students": []
            })

        node_id = link['marcus_node_id']
        teachers = conn.execute("""
            SELECT teacher_id AS id, teacher_label AS label, relation_type, ref
            FROM marcus_networks WHERE student_id = ?
        """, (node_id,)).fetchall()
        students = conn.execute("""
            SELECT student_id AS id, student_label AS label, relation_type, ref
            FROM marcus_networks WHERE teacher_id = ?
        """, (node_id,)).fetchall()

        return jsonify({
            "ok": True,
            "person": dict(person),
            "linked": True,
            "match_confidence": link['match_confidence'],
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA",
            "teachers": [dict(r) for r in teachers],
            "students": [dict(r) for r in students]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/api/admin/dila-stats')
def admin_dila_stats():
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        dynasty_counts = conn.execute("""
            SELECT dynasty, COUNT(*) as cnt FROM people 
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty ORDER BY cnt DESC LIMIT 10
        """).fetchall()
        return jsonify({
            "total_people": total_people,
            "total_places": total_places,
            "dynasties": [{"name": r[0], "count": r[1]} for r in dynasty_counts]
        })
    finally:
        conn.close()



@app.route('/api/admin/person-stats')
def admin_person_stats():
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        dynasty_counts = conn.execute("""
            SELECT dynasty, COUNT(*) as cnt FROM people 
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty ORDER BY cnt DESC
        """).fetchall()
        return jsonify({
            "total": total,
            "dynasties": [{"name": r[0], "count": r[1]} for r in dynasty_counts]
        })
    finally:
        conn.close()



@app.route('/api/dict/<dila_id>')
def api_dict(dila_id):
    """
    GET /api/dict/<dila_id>
    Get Startdict biography for a monk.
    Returns placeholder data if not found.
    """
    # Try to find in startdict database
    # For now, return placeholder - integrate with startdict data later
    return jsonify({
        'id': dila_id,
        'bio': 'Chưa có dữ liệu từ điển cho ' + dila_id
    })



# =============================================================================
# TTL REBUILD v4.0 - API ENDPOINTS
# =============================================================================

@app.route('/api/monk/<dila_id>/marcus', methods=['GET'])
def api_monk_marcus(dila_id):
    """GET /api/monk/{id}/marcus - Get Marcus network data (teachers/students)
    Searches by name_vi, name_zh, hasTeacher/hasStudent from TTL.
    """
    lookup_id = dila_id.replace('TS-', '')
    conn = get_db()
    try:
        teachers = set()
        students = set()
        lineage = ''
        search_keys = []
        
        # Get name and relationships from TTL
        import re
        ttl_file = os.path.join(TTL_OLD_DIR, f"TS-{lookup_id}.ttl")
        if not os.path.exists(ttl_file):
            for f in os.listdir(TTL_OLD_DIR):
                if lookup_id.lower() in f.lower():
                    ttl_file = os.path.join(TTL_OLD_DIR, f)
                    break
        
        ttl_teachers = []  # From hasTeacher in TTL
        ttl_students = []  # From hasStudent in TTL
        
        if os.path.exists(ttl_file):
            with open(ttl_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Get name_vi
                label_match = re.search(r'rdfs:label\s+"([^"]+)"@vi', content)
                if label_match:
                    search_keys.append(label_match.group(1))
                # Get name_zh
                zh_match = re.search(r'rdfs:label\s+"([^\n]+)"@zh', content)
                if zh_match:
                    search_keys.append(zh_match.group(1))
                # Get hasTeacher IDs
                ttl_teachers = re.findall(r'bkg:hasTeacher\s+<ex:monk/([^>]+)>', content)
                # Get hasStudent IDs
                ttl_students = re.findall(r'bkg:hasStudent\s+<ex:monk/([^>]+)>', content)
        
        # Convert TTL monk IDs to names
        def get_monks_name(monk_ids, current_ttl_content=''):
            names = []
            for mid in monk_ids:
                found = False
                # Convert underscore to hyphen, title case
                parts = mid.split('_')
                mid_title = '-'.join(p.capitalize() for p in parts)
                mfile = os.path.join(TTL_OLD_DIR, f"TS-{mid_title}.ttl")
                
                if os.path.exists(mfile):
                    with open(mfile, 'r', encoding='utf-8') as f:
                        c = f.read()
                        m = re.search(r'rdfs:label\s+"([^"]+)"@vi', c)
                        if m:
                            names.append(m.group(1))
                            found = True
                
                # Try fuzzy match (case-insensitive, ignore hyphens)
                if not found:
                    for f in os.listdir(TTL_OLD_DIR):
                        fname = f.lower().replace('.ttl','').replace('ts-','').replace('-','_')
                        if mid.lower() in fname:
                            mfile = os.path.join(TTL_OLD_DIR, f)
                            with open(mfile, 'r', encoding='utf-8') as fp:
                                c = fp.read()
                                m = re.search(r'rdfs:label\s+"([^"]+)"@vi', c)
                                if m:
                                    names.append(m.group(1))
                            break
                
                # Try to find in current TTL content (if defined in same file)
                if not found and current_ttl_content:
                    # Look for <ex:monk/nguyen_thieu_tho_tong> rdfs:label "Nguyên Thiều Thọ Tông"@vi
                    pattern = r'<ex:monk/' + re.escape(mid) + r'>\s+rdfs:label\s+"([^"]+)"'
                    m = re.search(pattern, current_ttl_content)
                    if m:
                        names.append(m.group(1))
                        found = True
            return names
        
        # Add teachers from TTL
        if ttl_teachers:
            teachers.update(get_monks_name(ttl_teachers, content if os.path.exists(ttl_file) else ''))
        # Add students from TTL  
        if ttl_students:
            students.update(get_monks_name(ttl_students, content if os.path.exists(ttl_file) else ''))
        
        # Also search in marcus_networks by name_vi / name_zh
        for key in search_keys:
            if key:
                if not teachers:
                    rows = conn.execute(
                        "SELECT teacher_id, teacher_label FROM marcus_networks WHERE student_label LIKE ?",
                        (f'%{key}%',)
                    ).fetchall()
                    for r in rows:
                        teachers.add(r['teacher_label'] or r['teacher_id'])
                
                if not students:
                    rows = conn.execute(
                        "SELECT student_id, student_label FROM marcus_networks WHERE teacher_label LIKE ?",
                        (f'%{key}%',)
                    ).fetchall()
                    for r in rows:
                        students.add(r['student_label'] or r['student_id'])
        
        return jsonify({
            'teachers': list(teachers)[:10],
            'students': list(students)[:15],
            'edges': len(teachers) + len(students),
            'lineage': lineage,
            'ttl_teachers': ttl_teachers,
            'ttl_students': ttl_students,
            'search_keys': search_keys
        })
    finally:
        conn.close()



@app.route('/api/monk/<dila_id>/vps_ttl', methods=['GET'])
def api_monk_vps_ttl(dila_id):
    """GET /api/monk/{id}/vps_ttl - Get VPS TTL file content"""
    lookup_id = dila_id.replace('TS-', '')
    ttl_file = os.path.join(TTL_OLD_DIR, f"{lookup_id}.ttl")
    if not os.path.exists(ttl_file):
        for f in os.listdir(TTL_OLD_DIR):
            if lookup_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                break
    if os.path.exists(ttl_file):
        with open(ttl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'ttl_file': os.path.basename(ttl_file),
            'ttl_content': content[:5000],
            'ttl_content_full': content
        })
    return jsonify({'error': 'TTL not found'}), 404



@app.route('/api/monk/<dila_id>/truoctac', methods=['GET'])
def api_monk_truoctac(dila_id):
    """GET /api/monk/{id}/truoctac - Get Trước Tác works from canon_catalog"""
    lookup_id = dila_id.replace('TS-', '')
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT title_vi, title_zh, volume, cb_page FROM canon_catalog WHERE author_dila_id = ? OR author_vi LIKE ? LIMIT 50",
            (lookup_id, f'%{lookup_id}%')
        ).fetchall()
        works = [{'title_vi': r['title_vi'], 'title_zh': r['title_zh'], 'volume': r['volume'], 'cb_page': r['cb_page']} for r in rows]
        return jsonify({'works': works, 'count': len(works)})
    finally:
        conn.close()



@app.route('/daoanh/api/progress/task/<task_id>/status', methods=['POST'])
@app.route('/api/progress/task/<task_id>/status', methods=['POST'])
def admin_progress_task_status(task_id):
    """POST — Admin bấm nút Done trên bảng UNDONE của dashboard.

    Ghi vào `data/task_status_overrides.json` (additive) thay vì sửa thẳng
    `tasks/*.md`: file `.md` là SSOT nhưng đang được nhiều session sửa song song,
    ghi từ web có nguy cơ race / mất nội dung. Xoá file override là revert
    trọn vẹn. Provenance (`by` / `at` / `note`) giữ trong file.

    BẮT BUỘC verify_session — endpoint này thay đổi trạng thái task trên board.
    """
    # T198/T223 — endpoint này đổi trạng thái task hiển thị cho Admin ⇒ cần auth.
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    task_id = (task_id or '').strip()
    # chỉ cho phép đúng dạng ID task để tránh path traversal khi tìm file
    if not re.match(r'^[A-Za-z]+[-A-Za-z0-9_]*$', task_id):
        return jsonify({"success": False,
                        "error": "task_id không hợp lệ"}), 400

    data = request.get_json(silent=True) or {}
    new_status = str(data.get('status', '')).strip()
    note = str(data.get('note', '')).strip()[:400]
    if new_status not in ('done', 'in_progress', 'pending', 'blocked'):
        return jsonify({"success": False,
                        "error": "status phải là done|in_progress|pending|blocked"}), 400

    # task phải tồn tại thật trong tasks/ — tránh ghi override cho task không có
    tasks_dir = os.path.join(BASE_DIR, 'tasks')
    match = [f for f in os.listdir(tasks_dir)
             if os.path.isfile(os.path.join(tasks_dir, f))
             and f.endswith('.md')
             and (f == task_id or f.startswith(task_id + '-')
                  or f == task_id + '.md')]
    if not match:
        return jsonify({"success": False,
                        "error": "không tìm thấy task trong tasks/"}), 404

    ov_path = os.path.join(DATA_DIR, 'task_status_overrides.json')
    overrides = {}
    if os.path.isfile(ov_path):
        try:
            with open(ov_path, encoding='utf-8') as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                overrides = {k: v for k, v in loaded.items()
                             if not k.startswith('_')}
        except Exception as e:
            return jsonify({"success": False,
                            "error": "file override đang hỏng: %s" % e}), 500

    overrides[task_id] = {
        'status': new_status,
        'by': 'admin',
        'at': datetime.now().isoformat(timespec='seconds'),
        'note': note,
        'file': match[0],
    }
    try:
        payload = {'_comment': 'Lớp override status do Admin bấm Done trên '
                              'dashboard. Xoá file này để revert toàn bộ.'}
        payload.update(overrides)
        with open(ov_path, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as e:
        return jsonify({"success": False, "error": "ghi file thất bại: %s" % e}), 500

    # sinh lại dashboard để thấy ngay
    try:
        import subprocess as _sp
        _sp.run([_sys.executable,
                  os.path.join(BASE_DIR, 'scripts', 'build_progress_data.py')],
                 cwd=BASE_DIR, capture_output=True, text=True,
                 encoding='utf-8', errors='replace', timeout=60)
    except Exception:
        pass   # không chặn: file override đã ghi, lần tải sau sẽ thấy

    return jsonify({
        'success': True,
        'task_id': task_id,
        'status': new_status,
        'file': match[0],
        'override_file': os.path.basename(ov_path),
        'revert_hint': 'xoá %s để hoàn nguyên' % os.path.basename(ov_path),
    })



@app.route('/api/name_vi/<path:dila_id>', methods=['GET'])
def api_name_vi_lookup(dila_id):
    """GET /api/name_vi/<dila_id> - Lookup Vietnamese name from name_vi_map"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        
        # Try to find by dila_id first
        row = conn.execute("""
            SELECT name_vi, name_vi_auto, name_vi_final, name_zh, birth_year, death_year, bio_snippet, marcus_ids
            FROM name_vi_map 
            WHERE dila_id = ? OR name_zh IN (
                SELECT name_zh FROM people WHERE id = ?
            )
            LIMIT 1
        """, (dila_id, dila_id)).fetchone()
        
        if row:
            result = dict(row)
            result['name_vi'] = row['name_vi_final'] or row['name_vi_auto'] or row['name_vi'] or ''
            # T166 §7.2 C — cho biết nguồn hiển thị: Manual (final) vs Auto (LLM-cache).
            # UI hiển thị badge 'Auto' + 'chưa duyệt' ⇒ KHÔNG được xem là LOCKED.
            if row['name_vi_final']:
                result['name_vi_source'] = 'final'
            elif row['name_vi_auto']:
                result['name_vi_source'] = 'auto'
            else:
                result['name_vi_source'] = 'base'
            result['found'] = 'dila'
        else:
            # Try by marcus_id
            row = conn.execute("""
                SELECT name_vi, name_vi_auto, name_vi_final, name_zh, birth_year, death_year, bio_snippet, dila_id
                FROM name_vi_map 
                WHERE marcus_ids LIKE ?
                LIMIT 1
            """, (f'%{dila_id}%',)).fetchone()
            
            if row:
                result = dict(row)
                result['name_vi'] = row['name_vi_final'] or row['name_vi_auto'] or row['name_vi'] or ''
                if row['name_vi_final']:
                    result['name_vi_source'] = 'final'
                elif row['name_vi_auto']:
                    result['name_vi_source'] = 'auto'
                else:
                    result['name_vi_source'] = 'base'
                result['found'] = 'marcus'
            else:
                result = {'found': None}
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/daoanh/api/name_vi/search', methods=['GET'])
@app.route('/api/name_vi/search', methods=['GET'])
def api_name_vi_search():
    """GET /api/name_vi/search?q=<query> - Search Vietnamese names"""
    try:
        query = request.args.get('q', '')
        if len(query) < 2:
            return jsonify({'results': [], 'error': 'Query too short'})
        
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("""
            SELECT name_vi, name_vi_auto, name_vi_final, name_zh, birth_year, death_year, dila_id, marcus_ids
            FROM name_vi_map 
            WHERE name_vi LIKE ? OR name_vi_auto LIKE ? OR name_vi_final LIKE ? OR name_zh LIKE ?
            LIMIT 20
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        
        results = [dict(row) for row in rows]
        conn.close()
        
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/daoanh/api/admin/keywords/search')
def keywords_search():
    """GET /daoanh/api/admin/keywords/search?q=...&limit=20
    Search keyword_map by keyword (LIKE). Returns JSON list."""
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    limit = min(int(request.args.get('limit', 20)), 100)
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, keyword, value FROM keyword_map WHERE keyword LIKE ? ORDER BY keyword COLLATE NOCASE LIMIT ?",
            (f'%{q}%', limit)
        ).fetchall()
        return jsonify([{"id": r['id'], "keyword": r['keyword'], "value": r['value']} for r in rows])
    finally:
        conn.close()




# ===== DILA INTEGRATION LAYER API (ENTITY + PASSAGES) =====

@app.route('/daoanh/api/entity/<entity_id>')
def entity_info(entity_id):
    """GET /daoanh/api/entity/<entity_id>
    Returns entity info from the ENTITY table."""
    conn = get_db_connection()
    try:
        entity = conn.execute(
            "SELECT * FROM entity WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if not entity:
            # Try with normalized PL ID
            digits = re.sub(r'[^0-9]', '', entity_id)
            if entity_id.startswith('PL') or (digits and len(digits) >= 6):
                normalized = 'PL' + digits
                entity = conn.execute(
                    "SELECT * FROM entity WHERE entity_id = ?", (normalized,)
                ).fetchone()
        if not entity:
            return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 200
        result = dict(entity)
        if entity['marcus_id']:
            marcus_ref = conn.execute(
                "SELECT label AS marcus_label, label_vi AS marcus_label_vi, birth_year AS marcus_birth, death_year AS marcus_death "
                "FROM marcus_reference WHERE node_id = ?", (entity['marcus_id'],)
            ).fetchone()
            if marcus_ref:
                result['marcus'] = dict(marcus_ref)
        return jsonify({"success": True, "has_data": True, "entity": result})
    finally:
        conn.close()




@app.route('/daoanh/api/entity/<entity_id>/marcus')
def entity_marcus(entity_id):
    """GET /daoanh/api/entity/<entity_id>/marcus
    Returns Marcus glossary reference + network data for this entity."""
    conn = get_db_connection()
    try:
        entity = conn.execute(
            "SELECT entity_id, marcus_id FROM entity WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if not entity or not entity['marcus_id']:
            return jsonify({"success": False, "has_data": False, "error": "No Marcus data for this entity"}), 200

        mid = entity['marcus_id']
        ref = conn.execute(
            "SELECT * FROM marcus_reference WHERE node_id = ?", (mid,)
        ).fetchone()

        teachers = conn.execute(
            "SELECT teacher_id, teacher_label FROM marcus_networks WHERE student_id = ?", (mid,)
        ).fetchall()
        students = conn.execute(
            "SELECT student_id, student_label FROM marcus_networks WHERE teacher_id = ?", (mid,)
        ).fetchall()
        edge_count = len(teachers) + len(students)

        return jsonify({
            "success": True,
            "has_data": True,
            "entity_id": entity_id,
            "marcus_id": mid,
            "reference": dict(ref) if ref else None,
            "teachers": [dict(t) for t in teachers],
            "students": [dict(s) for s in students],
            "edge_count": edge_count
        })
    finally:
        conn.close()




@app.route('/daoanh/api/entity/<entity_id>/summary')
def entity_summary(entity_id):
    """GET /daoanh/api/entity/<entity_id>/summary
    Returns a structured summary of all passages linked to this entity,
    grouped by source text with metadata from CBETA catalog."""
    conn = get_db_connection()
    try:
        entity = conn.execute(
            "SELECT * FROM entity WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if not entity:
            digits = re.sub(r'[^0-9]', '', entity_id)
            if entity_id.startswith('PL') or (digits and len(digits) >= 6):
                normalized = 'PL' + digits
                entity = conn.execute(
                    "SELECT * FROM entity WHERE entity_id = ?", (normalized,)
                ).fetchone()
        if not entity:
            return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 200

        entity = dict(entity)
        rows = conn.execute(
            """SELECT p.passage_id, p.source, p.text_id, p.loc_ref, p.raw_text, p.norm_text, p.vi_text
               FROM passage_entity pe
               JOIN passage p ON pe.passage_id = p.passage_id
               WHERE pe.entity_id = ?
               ORDER BY p.text_id, p.passage_id""",
            (entity['entity_id'],)
        ).fetchall()

        total = len(rows)
        text_groups = {}
        cbeta_conn = get_cbeta_conn()
        try:
            cbeta_catalog = {}
            for row in cbeta_conn.execute(
                "SELECT sigla, title_zh, author_zh, translator_zh FROM cbeta_texts"
            ).fetchall():
                cbeta_catalog[row['sigla']] = dict(row)
        finally:
            cbeta_conn.close()

        for r in rows:
            r = dict(r)
            tid = r['text_id']
            if tid not in text_groups:
                text_groups[tid] = {
                    "text_id": tid,
                    "catalog": cbeta_catalog.get(tid, {}),
                    "count": 0,
                    "loc_refs": [],
                    "passage_ids": [],
                    "preview_passages": []
                }
            g = text_groups[tid]
            g['count'] += 1
            if r['loc_ref']:
                g['loc_refs'].append(r['loc_ref'])
            g['passage_ids'].append(r['passage_id'])
            if len(g['preview_passages']) < 3:
                g['preview_passages'].append({
                    "passage_id": r['passage_id'],
                    "loc_ref": r['loc_ref'],
                    "raw_text_preview": r['raw_text'][:200],
                    "has_vi": bool(r['vi_text'])
                })

        return jsonify({
            "success": True,
            "has_data": total > 0,
            "entity_id": entity['entity_id'],
            "entity_label_zh": entity.get('alias_zh', ''),
            "entity_label_vi": entity.get('alias_vi', ''),
            "entity_type": entity.get('type', ''),
            "passage_count": total,
            "text_group_count": len(text_groups),
            "text_groups": text_groups
        })
    finally:
        conn.close()




# ===== TAB ĐẠI TẠNG (TASK_TAB_DAI_TANG_PLACE): CANON ENDPOINT =====

@app.route('/daoanh/api/entity/<entity_id>/canon')
def entity_canon(entity_id):
    """GET /daoanh/api/entity/<entity_id>/canon
    Tab "ĐẠI TẠNG" cho ĐỊA ĐIỂM/THỰC THỂ — tổng hợp 3 lớp (chỉ đọc, không đụng DB/schema):
      Layer A  dila_references : ref thô từ places_dila.listbibl + fosizhi (raw_xml)
      Layer B  passages        : passage đã index (passage_entity JOIN passage) + match evidence
      Layer C  texts           : metadata tác phẩm (catalog_mapping JOIN canon_catalog bởi cb_cbeta)
    Query params: page (1), page_size (20) — chỉ áp dụng cho passages.
    Không bịa dữ liệu: translation_count tính từ passage.vi_text thật (hiện = 0)."""
    import re as _re
    page = max(int(request.args.get('page', 1)), 1)
    page_size = min(max(int(request.args.get('page_size', 20)), 1), 100)
    offset = (page - 1) * page_size

    conn = get_db_connection()
    try:
        # 1. Resolve entity — chấp nhận cả short id (places.id / PL023255) và DILA id
        #    (PL000000023255). Dùng _resolve_dila_id để chuẩn hoá về DILA id.
        resolved_dila, resolved_zh = _resolve_dila_id(conn, entity_id)
        cand = entity_id
        if resolved_dila:
            cand = resolved_dila
        entity_row = conn.execute(
            "SELECT entity_id, entity_type, dila_id, alias_zh, alias_vi, extra_alias, cbeta_occ "
            "FROM entity WHERE entity_id = ?", (cand,)).fetchone()
        if not entity_row:
            digits = _re.sub(r'[^0-9]', '', cand)
            if (cand.startswith(('PL', 'pl', 'P')) or (digits and len(digits) >= 6)):
                normalized = 'PL' + digits
                entity_row = conn.execute(
                    "SELECT entity_id, entity_type, dila_id, alias_zh, alias_vi, extra_alias, cbeta_occ "
                    "FROM entity WHERE entity_id = ?", (normalized,)).fetchone()
        if not entity_row:
            return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 404
        entity = dict(entity_row)

        # Tên Việt ưu tiên từ bản đồ tên (namevi_map_places), fallback alias_vi
        name_vi_row = conn.execute(
            "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? ORDER BY confidence DESC LIMIT 1",
            (entity['entity_id'],)).fetchone()
        name_vi = entity.get('alias_vi') or ''
        if name_vi_row and name_vi_row['name_vi']:
            name_vi = name_vi_row['name_vi']

        # Danh sách alias từ places_dila (tên Hán chuẩn lưu trữ + raw_xml placeName nếu có)
        aliases = []
        authority_sources = []
        dila_row = None
        dila_id = cand
        dila_row = conn.execute(
            "SELECT id, name_zh, name_en, listbibl, raw_xml FROM places_dila WHERE id = ? LIMIT 1",
            (dila_id,)).fetchone()
        if dila_row:
            # tên Hán chuẩn lưu trữ (vd 少室寺) — luôn thêm trước
            stored_zh = (dila_row['name_zh'] or '').strip()
            if stored_zh and stored_zh not in aliases:
                aliases.append(stored_zh)
            for stored_name in [dila_row['name_en']]:
                stored_name = (stored_name or '').strip()
                if stored_name and stored_name not in aliases:
                    aliases.append(stored_name)
            raw_xml = dila_row['raw_xml'] or ''
            for pn in _re.findall(r'<placeName[^>]*>([^<]+)</placeName>', raw_xml):
                pn = pn.strip()
                if pn and pn not in aliases:
                    aliases.append(pn)
            if 'dila' in raw_xml or 'dila' in (dila_row['listbibl'] or ''):
                authority_sources.append('DILA')
        if entity.get('alias_zh') and entity['alias_zh'] not in aliases:
            aliases.insert(0, entity['alias_zh'])
        for a in [entity.get('alias_vi'), entity.get('extra_alias')]:
            if a and a not in aliases:
                aliases.append(a)
        if dila_id and 'DILA' not in authority_sources:
            authority_sources.append('DILA')
        if 'CBETA' not in authority_sources:
            authority_sources.append('CBETA')

        # 2. LAYER A — dẫn chiếu DILA (listbibl + fosizhi)
        dila_references = []
        seen_refs = set()
        if dila_row and dila_row['listbibl']:
            for entry in [e.strip() for e in dila_row['listbibl'].split(';') if e.strip()]:
                m = _re.match(r'\(\s*CBETA\s+([\w_]+)\s*\)\s*(.*)', entry)
                if not m:
                    continue
                ref = m.group(1).strip()
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                rest = m.group(2).strip()
                tag_m = _re.search(r'\{([^}]+)\}', rest)
                place_tag = tag_m.group(1).strip() if tag_m else ''
                title_context = _re.sub(r'\s*\{[^}]+\}\s*', '', rest).strip()
                dila_references.append({
                    'ref_type': 'CBETA',
                    'ref_code': ref,
                    'sigla': ref.split('_')[0] if '_' in ref else ref,
                    'title_context': title_context,
                    'place_tag': place_tag,
                })
        if dila_row and dila_row['raw_xml']:
            raw_xml = dila_row['raw_xml'] or ''
            fz_matches = _re.findall(
                r'target="([^"]*fosizhi[^"]*)">([^(<]+)\(([^)]+)\)</[^>]+>\s*\{([^}]+)\}',
                raw_xml)
            seen_fz = set()
            for url, ref_code, book_title, place_tag in fz_matches:
                ref_code = ref_code.strip()
                if ref_code in seen_fz:
                    continue
                seen_fz.add(ref_code)
                dila_references.append({
                    'ref_type': 'FOSIZHI',
                    'ref_code': ref_code,
                    'book_title': book_title.strip(),
                    'place_tag': place_tag.strip(),
                    'url': url.replace('&amp;', '&'),
                })

        # 3. LAYER B — passage đã index (passage_entity JOIN passage)
        total_passages = conn.execute(
            """SELECT COUNT(*) FROM passage_entity pe
               JOIN passage p ON pe.passage_id = p.passage_id
               WHERE pe.entity_id = ?""", (entity['entity_id'],)).fetchone()[0]
        passage_rows = conn.execute(
            """SELECT p.passage_id, p.source, p.text_id, p.loc_ref, p.raw_text, p.norm_text,
                      p.vi_text, p.translation_draft
               FROM passage_entity pe
               JOIN passage p ON pe.passage_id = p.passage_id
               WHERE pe.entity_id = ?
               ORDER BY p.text_id, p.passage_id
               LIMIT ? OFFSET ?""",
            (entity['entity_id'], page_size, offset)).fetchall()
        passages = []
        translated_count = 0
        for pr in passage_rows:
            pr = dict(pr)
            if pr.get('vi_text'):
                translated_count += 1
            passages.append({
                'passage_id': pr['passage_id'],
                'source': pr['source'],
                'text_id': pr['text_id'],
                'loc_ref': pr['loc_ref'],
                'raw_text': pr['raw_text'],
                'norm_text': pr['norm_text'],
                'vi_text': pr['vi_text'],
                'has_vi': bool(pr['vi_text']),
                'is_translation_draft': bool(pr.get('translation_draft')),
            })

        # 4. LAYER C — metadata tác phẩm (catalog_mapping JOIN canon_catalog bởi cb_cbeta)
        mapping_rows = conn.execute(
            """SELECT catalog_id, source, status, note, quality_flag FROM catalog_mapping
               WHERE place_id = ? ORDER BY status, catalog_id""", (entity['entity_id'],)).fetchall()
        mapping = [dict(r) for r in mapping_rows]
        texts = []
        for cm in mapping_rows:
            cc = conn.execute(
                """SELECT work_id, title_vi, title_zh, author_vi, era_vi, year_start, year_end,
                          cbeta_id, cb_volume, cb_page, source, verified
                   FROM canon_catalog WHERE CAST(cb_cbeta AS TEXT) = ? LIMIT 1""",
                (cm['catalog_id'],)).fetchone()
            if not cc:
                continue
            cc = dict(cc)
            texts.append({
                'catalog_id': cm['catalog_id'],
                'work_id': cc.get('work_id'),
                'title_vi': cc.get('title_vi'),
                'title_zh': cc.get('title_zh'),
                'author_vi': cc.get('author_vi'),
                'era_vi': cc.get('era_vi'),
                'year_start': cc.get('year_start'),
                'year_end': cc.get('year_end'),
                'volume': cc.get('cb_volume'),
                'page': cc.get('cb_page'),
                'source': cc.get('source'),
                'verified': cc.get('verified'),
                'mapping_source': cm['source'],
                'mapping_status': cm['status'],
                'mapping_note': cm['note'],
            })

        has_more = (offset + len(passages)) < total_passages

        return jsonify({
            "success": True,
            "has_data": len(dila_references) > 0 or total_passages > 0 or len(texts) > 0,
            "entity": {
                "id": entity['entity_id'],
                "entity_type": entity.get('entity_type'),
                "name_vi": name_vi,
                "name_zh": entity.get('alias_zh'),
                "alias_vi": entity.get('alias_vi'),
                "alias_zh": entity.get('alias_zh'),
                "extra_alias": entity.get('extra_alias'),
                "aliases": aliases,
                "authority_sources": authority_sources,
                "dila_id": dila_id,
            },
            "summary": {
                "dila_reference_count": len(dila_references),
                "indexed_passage_count": total_passages,
                "text_count": len(texts),
                "translation_count": translated_count,
            },
            "data_status": {
                "has_dila_references": len(dila_references) > 0,
                "has_indexed_passages": total_passages > 0,
                "has_text_metadata": len(texts) > 0,
                "has_translations": translated_count > 0,
            },
            "dila_references": dila_references,
            "passages": {
                "items": passages,
                "total": total_passages,
                "page": page,
                "page_size": page_size,
                "has_more": has_more,
            },
            "texts": texts,
            "mapping": mapping,
        })
    except sqlite3.OperationalError as e:
        return jsonify({"success": False, "has_data": False, "error": f"Table unavailable: {e}"}), 200
    finally:
        conn.close()




# ===== T26: UNIFIED ENTITY ENDPOINT =====

@app.route('/daoanh/api/entity/<entity_id>/unified')
def entity_unified(entity_id):
    """T26: Unified API Response — consolidate all sources for an entity.
    Returns entity + sources[] + claims[] + conflicts[] in one response.
    GET /daoanh/api/entity/<entity_id>/unified
    """
    conn = get_db_connection()
    try:
        # 1. Resolve entity from entity_hub (INTEGER PK)
        hub = conn.execute(
            "SELECT entity_id, canonical_label, entity_type FROM entity_hub WHERE entity_id = ?",
            (entity_id,)
        ).fetchone()

        # Fallback: try entity table (TEXT PK, DILA-centric)
        if not hub:
            ent = conn.execute(
                "SELECT entity_id, alias_zh AS canonical_label, alias_vi AS canonical_name_vi, entity_type FROM entity WHERE entity_id = ?",
                (entity_id,)
            ).fetchone()
            if ent:
                hub = ent

        if not hub:
            return jsonify({"ok": False, "error": "Entity not found"}), 404

        entity = dict(hub)
        # canonical_name = Hán name; canonical_name_vi = Vietnamese name
        entity['canonical_name'] = entity.get('canonical_label')
        # canonical_name_vi: prefer namevi_map_places; fall back to alias_vi from entity table
        vi_name_row = conn.execute(
            "SELECT name_vi, confidence, source FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
            (entity_id,)
        ).fetchone()
        if vi_name_row and vi_name_row['name_vi']:
            entity['canonical_name_vi'] = vi_name_row['name_vi']
        elif 'canonical_name_vi' not in entity:
            entity['canonical_name_vi'] = None

        # T360 — badge nguồn/độ tin cậy cho canonical_name_vi (cột source/confidence
        # THẬT của namevi_map_places — endpoint này là đường thực tế places.html
        # dùng trước tiên, legacy /daoanh/api/places/<id> chỉ là fallback).
        try:
            if vi_name_row and vi_name_row['name_vi']:
                _label, _color = _t360_classify_name_vi_source(
                    vi_name_row['source'], vi_name_row['confidence'])
                entity['source_of_name_vi'] = _label
                entity['confidence_name_vi'] = vi_name_row['confidence']
                entity['badge_color_name_vi'] = _color
            else:
                entity['source_of_name_vi'] = None
                entity['confidence_name_vi'] = None
                entity['badge_color_name_vi'] = None
        except Exception:
            entity['source_of_name_vi'] = None
            entity['confidence_name_vi'] = None
            entity['badge_color_name_vi'] = None
        # CBETA mention count from T51d aggregate table
        try:
            cbeta_stat = conn.execute(
                "SELECT mention_count, top_texts FROM cbeta_place_mention_stats WHERE place_id = ? LIMIT 1",
                (entity_id,)
            ).fetchone()
            entity['cbeta_mention_count'] = cbeta_stat['mention_count'] if cbeta_stat else 0
        except Exception:
            entity['cbeta_mention_count'] = None

        # 2. Resolve source mappings from entity_source_ids
        # entity_source_ids uses INTEGER entity_id (from entity_hub), but entity_id param may be
        # a TEXT DILA ID like 'PL000000023255' → resolve integer hub ID via source_entity_id lookup
        sources = {}
        esi_id_row = conn.execute(
            "SELECT entity_id FROM entity_source_ids WHERE source_entity_id = ? LIMIT 1",
            (entity_id,)
        ).fetchone()
        hub_int_id = esi_id_row['entity_id'] if esi_id_row else entity_id
        source_rows = conn.execute(
            "SELECT source, source_entity_id, confidence, verified FROM entity_source_ids WHERE entity_id = ?",
            (hub_int_id,)
        ).fetchall()
        source_map = {}
        for sr in source_rows:
            source_map[sr['source']] = dict(sr)

        # DILA source — BUG-011 fix: fallback to entity_id for PL* places when entity_source_ids incomplete
        # Primary: entity_source_ids mapping; fallback: entity_id IS the DILA ID for place entities
        _dila_source_id = None
        if 'DILA' in source_map:
            _dila_source_id = source_map['DILA']['source_entity_id']
        elif str(entity_id).startswith('PL'):
            # For place entities, entity_id equals the DILA ID — entity_source_ids may be incomplete
            _dila_source_id = entity_id
        if _dila_source_id:
            dila_id = _dila_source_id
            dila_detail = conn.execute(
                "SELECT name_zh, geo_lat, geo_long, note, district, note_category FROM places_dila WHERE id = ?",
                (dila_id,)
            ).fetchone()
            # Fallback: places_dila uses long DILA IDs (PL000000000001); short IDs (PL056722)
            # only exist in places table — read GPS/name_zh/province from there when places_dila empty
            _places_fb = None
            if not dila_detail:
                _pf = conn.execute(
                    "SELECT name_zh, gps_lat, gps_long, province FROM places WHERE id = ?",
                    (dila_id,)
                ).fetchone()
                if _pf and (_pf['gps_lat'] or _pf['name_zh']):
                    _places_fb = _pf
                    # Secondary fallback: find matching places_dila by GPS (same coords = same site)
                    # Resolves note/district when entity_source_ids has short ID but places_dila uses long ID
                    if _pf['gps_lat'] and _pf['gps_long']:
                        _gps_match = conn.execute(
                            "SELECT name_zh, geo_lat, geo_long, note, district, note_category"
                            " FROM places_dila"
                            " WHERE ABS(geo_lat - ?) < 0.001 AND ABS(geo_long - ?) < 0.001"
                            " LIMIT 1",
                            (_pf['gps_lat'], _pf['gps_long'])
                        ).fetchone()
                        if _gps_match:
                            dila_detail = _gps_match
            vi_detail = conn.execute(
                "SELECT name_vi, country_vi, district_vi, vn_name_status FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
                (dila_id,)
            ).fetchone()
            _district_src = (dila_detail['district'] if dila_detail else None) or (_places_fb['province'] if _places_fb else None)
            parsed = parse_dila_district(_district_src) if _district_src else {}
            # Strip HTML/XML tags from note before sending to frontend
            _raw_note = dila_detail['note'] if dila_detail else None
            if _raw_note:
                _raw_note = re.sub(r'<[^>]+>', ' ', _raw_note)
                _raw_note = re.sub(r'\s+', ' ', _raw_note).strip() or None
            _fb_gps = (f"{_places_fb['gps_lat']},{_places_fb['gps_long']}"
                       if _places_fb and _places_fb['gps_lat'] else None)
            sources['dila'] = {
                "active": True,
                "source_record_id": dila_id,
                "name_zh": (dila_detail['name_zh'] if dila_detail else None) or (_places_fb['name_zh'] if _places_fb else None),
                "name_vi": vi_detail['name_vi'] if vi_detail else None,
                "gps": (f"{dila_detail['geo_lat']},{dila_detail['geo_long']}" if dila_detail and dila_detail['geo_lat'] else None) or _fb_gps,
                "district_raw": _district_src,
                "note": _raw_note,
                "note_category": dila_detail['note_category'] if dila_detail else None,
                "country_vi": (vi_detail['country_vi'] if vi_detail else None) or parsed.get('country_vi'),
                "district_vi": vi_detail['district_vi'] if vi_detail else None,
                "district_vi_computed": parsed.get('district_vi', ''),
                "province": parsed.get('province', ''),
                "vn_name_status": vi_detail['vn_name_status'] if vi_detail else None
            }
        else:
            sources['dila'] = {"active": False}

        # CBETA source
        if 'CBETA' in source_map:
            try:
                cb_row = conn.execute(
                    "SELECT source_id FROM data_sources WHERE source_code = 'CBETA' AND active = 1 LIMIT 1"
                ).fetchone()
                cb_src = cb_row['source_id'] if cb_row else 3
            except Exception:
                cb_src = 3
            try:
                cbeta_refs = conn.execute(
                    "SELECT source_record_id FROM entity_claims WHERE entity_id = ? AND source_id = ? LIMIT 10",
                    (entity_id, cb_src)
                ).fetchall()
                sources['cbeta'] = {
                    "active": True,
                    "refs": [r['source_record_id'] for r in cbeta_refs if r['source_record_id']]
                }
            except Exception:
                sources['cbeta'] = {"active": True, "refs": []}
        else:
            sources['cbeta'] = {"active": False, "refs": []}

        # ZQLOCAL source (Vietnamese names)
        if 'ZQLOCAL' in source_map:
            vi_name_row = conn.execute(
                "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
                (source_map['ZQLOCAL']['source_entity_id'],)
            ).fetchone()
            sources['zqlocal'] = {
                "active": True,
                "vi_name": vi_name_row['name_vi'] if vi_name_row else None
            }
        else:
            sources['zqlocal'] = {"active": False}

        # Marcus source
        sources['marcus'] = {"active": "MARCUS" in source_map}

        # Wikidata source (via geo_cross_ref)
        wiki = conn.execute(
            "SELECT wikidata_qid FROM geo_cross_ref WHERE dila_id = ? LIMIT 1",
            (entity_id,)
        ).fetchone()
        sources['wikidata'] = {
            "active": wiki is not None and wiki['wikidata_qid'] is not None,
            "qid": wiki['wikidata_qid'] if wiki else None
        }

        # 84000 source
        try:
            e4k = conn.execute(
                "SELECT COUNT(*) as cnt FROM eight_four_thousand_place_map WHERE dila_id = ?",
                (entity_id,)
            ).fetchone()
            sources['84000'] = {"active": e4k is not None and e4k['cnt'] > 0}
        except Exception:
            sources['84000'] = {"active": False}

        # Kanripo source
        try:
            kr = conn.execute(
                "SELECT COUNT(*) as cnt FROM kanripo_place_mapping WHERE dila_id = ?",
                (entity_id,)
            ).fetchone()
            sources['kanripo'] = {"active": kr is not None and kr['cnt'] > 0}
        except Exception:
            sources['kanripo'] = {"active": False}

        # SAT source (via sat_crossref table — T35)
        try:
            sat = conn.execute(
                "SELECT COUNT(*) as cnt FROM sat_crossref LIMIT 1",
            ).fetchone()
            sources['sat'] = {"active": sat is not None and sat['cnt'] > 0, "note": "SAT Daizōkyō deep-links (21dzk.l.u-tokyo.ac.jp)"}
        except Exception:
            sources['sat'] = {"active": False}

        # VRI source
        try:
            vri = conn.execute(
                "SELECT COUNT(*) as cnt FROM vri_place_mapping WHERE dila_id = ?",
                (entity_id,)
            ).fetchone()
            sources['vri'] = {"active": vri is not None and vri['cnt'] > 0}
        except Exception:
            sources['vri'] = {"active": False}

        # 3. Get all claims
        claims_rows = conn.execute(
            """SELECT claim_type, subject, predicate, object_text,
                      source_id, source_record_id, authority_role, confidence, verification_status
               FROM entity_claims WHERE entity_id = ?
               ORDER BY confidence DESC""",
            (entity_id,)
        ).fetchall()
        claims = [dict(r) for r in claims_rows]

        # 4. Get conflicts
        try:
            conflict_rows = conn.execute(
                """SELECT conflict_type, source_a, source_b, detail
                   FROM lineage_conflicts_v2 WHERE entity_id = ? LIMIT 10""",
                (entity_id,)
            ).fetchall()
            conflicts = [dict(r) for r in conflict_rows]
        except Exception:
            conflicts = []

        # 5. Get founding data
        founding = None
        try:
            f_row = conn.execute(
                """SELECT year, source, source_ref
                   FROM place_timeline_events
                   WHERE entity_id = ? AND event_type = 'founding'
                   ORDER BY confidence DESC LIMIT 1""",
                (entity_id,)
            ).fetchone()
            if f_row:
                founding = {"year": f_row[0], "source": f_row[1], "source_ref": f_row[2]}
        except Exception:
            pass

        # 6. Assemble unified response
        active_sources = [k for k, v in sources.items() if v.get('active')]

        return jsonify({
            "ok": True,
            "entity": entity,
            "sources": sources,
            "claims": claims,
            "claims_count": len(claims),
            "conflicts": conflicts,
            "conflicts_count": len(conflicts),
            "founding": founding,
            "meta": {
                "generated_at": __import__('datetime').datetime.now().isoformat(),
                "sources_active": active_sources,
                "sources_count": len(active_sources)
            }
        })
    finally:
        conn.close()




# ===== MONK API (Personography) =====

@app.route('/daoanh/api/monk/<monk_id>')
def api_monk_profile(monk_id):
    """
    GET /daoanh/api/monk/<dila_id>
    GET /daoanh/api/monk/<dila_id>?view=tooltip
    Returns full profile or tooltip-view for a monk.
    """
    try:
        view = request.args.get('view', 'full')
        conn = get_db_connection()

        # Try dila_id first, then numeric id
        monk = conn.execute("""
            SELECT * FROM monk_dict
            WHERE (dila_id = ? OR CAST(id AS TEXT) = ?)
              AND status = 'approved'
            LIMIT 1
        """, (monk_id, monk_id)).fetchone()

        if not monk:
            conn.close()
            return jsonify({"ok": False, "error": "Monk not found"}), 404

        monk_data = dict(monk)

        # Fetch all names from index
        names = conn.execute("""
            SELECT lang, name_form, name_type, normalized
            FROM monk_name_index
            WHERE monk_id = ?
            ORDER BY
                CASE name_type WHEN 'official' THEN 0 WHEN 'primary' THEN 1 WHEN 'alias' THEN 2 ELSE 3 END,
                id
        """, (monk['id'],)).fetchall()
        monk_data['names'] = [dict(n) for n in names]

        conn.close()

        if view == 'tooltip':
            return jsonify({
                "ok": True,
                "id": monk_data.get('dila_id') or str(monk_data['id']),
                "han_name": monk_data['han_name'],
                "vn_name": monk_data['vn_name'],
                "pinyin": monk_data['pinyin'],
                "dynasty": monk_data['dynasty'],
                "role_main": monk_data['role_main'],
                "era": monk_data['era'],
            })

        return jsonify({"ok": True, "monk": monk_data})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/monk/search')
def api_monk_search():
    """
    GET /daoanh/api/monk/search?q=<query>&limit=20
    Searches monk_name_index.normalized with prefix match.
    Returns deduplicated monk records joined with monk_dict.
    """
    try:
        q = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        if not q or len(q) < 1:
            return jsonify({"ok": False, "error": "Query too short"}), 400

        conn = get_db_connection()
        q_norm = normalize_text(q)

        rows = conn.execute("""
            SELECT DISTINCT m.id, m.dila_id, m.han_name, m.vn_name, m.pinyin,
                   m.dynasty, m.era, m.role_main, m.biography,
                   mi.lang, mi.name_form, mi.name_type, mi.normalized
            FROM monk_dict m
            JOIN monk_name_index mi ON mi.monk_id = m.id
            WHERE m.status = 'approved'
              AND mi.normalized LIKE ? || '%'
            ORDER BY
                CASE mi.lang WHEN 'zh' THEN 0 WHEN 'vi' THEN 1 WHEN 'pinyin' THEN 2 ELSE 3 END,
                LENGTH(mi.normalized) ASC
            LIMIT ?
        """, (q_norm, limit)).fetchall()

        conn.close()

        # Group by monk
        seen = {}
        for r in rows:
            mid = r['id']
            if mid not in seen:
                seen[mid] = {
                    "id": r['dila_id'] or str(mid),
                    "han_name": r['han_name'],
                    "vn_name": r['vn_name'],
                    "pinyin": r['pinyin'],
                    "dynasty": r['dynasty'],
                    "era": r['era'],
                    "role_main": r['role_main'],
                    "matched_name": r['name_form'],
                    "matched_lang": r['lang'],
                }

        results = list(seen.values())
        return jsonify({
            "ok": True,
            "query": q,
            "count": len(results),
            "results": results,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/persons/<person_id>')
def api_person_by_id(person_id):
    """GET /daoanh/api/persons/<person_id> — Profile nhân vật DILA.
    Trả về bio_zh (gốc) + bio_vi từ translation_cache nếu đã có (status != invalidated).
    """
    conn = get_db_connection()
    try:
        p = conn.execute(
            "SELECT id, name_zh, name_vi, name_en, sect, dynasty, birth_year, death_year, bio, bio_vi "
            "FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "person not found"}), 404

        result = {
            "id": p['id'], "name_zh": p['name_zh'], "name_vi": p['name_vi'],
            "name_en": p['name_en'], "sect": p['sect'], "dynasty": p['dynasty'],
            "birth_year": p['birth_year'], "death_year": p['death_year'],
            "biography": p['bio'] or '',
            "bio_zh": p['bio'] or '',
            "bio_vi": None, "bio_vi_status": None, "translation_id": None,
            "rules_outdated": False,
        }

        # Fallback: nếu people.bio_vi đã có (từ admin/import), dùng luôn
        if p['bio_vi']:
            result['bio_vi'] = p['bio_vi']
            result['bio_vi_status'] = 'from_db'

        # Kiểm tra cache (T165: dual-key + source_type + edited guard)
        if p['bio']:
            src_hash = _t73_source_hash(p['bio'])
            _lk = _t73_style_lock(conn, source_text=p['bio'])
            rv = _lk['rules_version']
            cached = _t165_lookup_cache(conn, src_hash, _lk.get('constitution_hash'),
                                        rv, 'person_bio')
            if cached:
                result['bio_vi'] = cached['translated_text']
                result['bio_vi_status'] = cached['status']
                result['translation_id'] = cached['id']
                result['rules_version'] = cached['rules_version']
                result['model_id'] = cached['model_id']
                # T178 gap 16 — tính thật (nhánh edited / hash lệch / hash NULL)
                result['rules_outdated'] = _t165_is_rules_outdated(
                    cached, _lk.get('constitution_hash'))

        # T82 Step4 — wire timeline từ vn_person_events (T79 birth/death, T81 active/floruit, T82 legacy)
        timeline = []
        rows = conn.execute(
            "SELECT event_type, event_year, event_label_vi, source, confidence "
            "FROM vn_person_events WHERE person_id=? ORDER BY event_year IS NULL, event_year ASC",
            (person_id,)
        ).fetchall()
        for r in rows:
            if r['event_type'] in ('active', 'floruit', 'birth', 'death',
                                   'KeyLifeEvent', 'Contribution', 'PhilosophicalStance'):
                timeline.append({
                    "event_type": r['event_type'],
                    "event_year": r['event_year'],
                    "label_vi": r['event_label_vi'] or '',
                    "source": r['source'],
                    "confidence": r['confidence'],
                })
        result['timeline'] = timeline
        result['timeline_count'] = len(timeline)

        # T359 fix 3 — expose origin_place (person_origin_link -> places) cho UI.
        # Bọc try/except: _t86_origin_place vốn phục vụ route khác, không để lỗi ở đây
        # làm sập toàn bộ /api/persons/<id>.
        try:
            result['origin_place'] = _t86_origin_place(conn, person_id)
        except Exception:
            result['origin_place'] = None

        # T172 — attach Hán-Việt charwise debug (sidecar person_hanviet_debug)
        try:
            result['hv'] = _t172_load_hv(conn, person_id)
        except Exception as e:
            result['hv'] = {}  # Fallback nếu _t172_load_hv fail

        # T360 — badge nguồn/độ tin cậy cho name_vi (person_display_names →
        # vn_person_authority → fallback ZQ tự động theo CLAUDE.md). Bọc try/except
        # vì các bảng authority có thể thiếu trên VPS.
        try:
            _label, _conf, _color = _t360_resolve_person_name_vi_source(conn, person_id)
        except Exception:
            _label, _conf, _color = None, None, None
        result['source_of_name_vi'] = _label
        result['confidence_name_vi'] = _conf
        result['badge_color_name_vi'] = _color

        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Internal error: {str(e)}"}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/admin/person/<person_id>/bio_vi', methods=['POST'])
def api_admin_save_person_bio_vi(person_id):
    """POST /daoanh/api/admin/person/<person_id>/bio_vi
    Body: {bio_vi: str, translation_id?: int}
    Admin trực tiếp lưu bản dịch đã chỉnh sửa vào translation_cache (status=edited)
    và cập nhật people.bio_vi.
    Header: X-Session-Token (bắt buộc).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    bio_vi = (data.get('bio_vi') or '').strip()
    translation_id = data.get('translation_id')

    if not bio_vi:
        return jsonify({"ok": False, "error": "bio_vi không được để trống"}), 400

    conn = get_db_connection()
    try:
        p = conn.execute("SELECT id, bio FROM people WHERE id = ?", (person_id,)).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "Không tìm thấy nhân vật"}), 404

        now = datetime.now().isoformat()
        new_id = translation_id

        # T166 §6.3 — post_check trên bản admin-manual DÙ nguồn là con người đã đăng
        # nhập (verify_session ở trên): invariant 'post_check → cache write' KHÔNG TRỪ
        # ai. Policy RECORD-not-block: admin là authority cao nhất (can sửa canonical
        # name), KHÔNG chặn save — chỉ ghi identity metadata để UI/audit cảnh báo
        # nếu admin đè tên canonical.
        if p['bio']:
            t166 = _t166_post_check_translation(
                conn, p['bio'], bio_vi,
                policy=_t166_identity_lock_policy(conn))
            _identity_issue = json.dumps(
                t166['identity_issues'], ensure_ascii=False) if t166['identity_issues'] else None
        else:
            t166 = None

        _has_ident = _t166_has_col(conn, 'translation_cache', 'identity_status')

        if translation_id:
            if _has_ident and p['bio']:
                conn.execute(
                    "UPDATE translation_cache SET translated_text=?, status='edited', "
                    " identity_status=?, identity_issues=?, identity_lock_hash=?, updated_at=? "
                    "WHERE id=?",
                    (bio_vi, t166['identity_status'], _identity_issue,
                     t166['identity_lock_hash'], now, translation_id)
                )
            else:
                conn.execute(
                    "UPDATE translation_cache SET translated_text=?, status='edited', updated_at=? WHERE id=?",
                    (bio_vi, now, translation_id)
                )
        elif p['bio']:
            src_hash = _t73_source_hash(p['bio'])
            rv = _t73_rules_version(_t73_get_active_rules(conn))
            conn.execute(
                "UPDATE translation_cache SET status='invalidated', updated_at=? "
                "WHERE source_hash=? AND source_type='person_bio' AND entity_id=?",
                (now, src_hash, person_id)
            )
            if _has_ident:
                cur = conn.execute(
                    "INSERT INTO translation_cache "
                    "(source_hash, source_type, entity_id, source_text, translated_text, "
                    " model_id, rules_version, status, identity_status, identity_issues, "
                    " identity_lock_hash, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,'edited',?,?,?,?,?)",
                    (src_hash, 'person_bio', person_id, p['bio'], bio_vi, 'manual', rv,
                     t166['identity_status'], _identity_issue, t166['identity_lock_hash'], now, now)
                )
            else:
                cur = conn.execute(
                    "INSERT INTO translation_cache "
                    "(source_hash, source_type, entity_id, source_text, translated_text, "
                    " model_id, rules_version, status, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,'edited',?,?)",
                    (src_hash, 'person_bio', person_id, p['bio'], bio_vi, 'manual', rv, now, now)
                )
            new_id = cur.lastrowid
        else:
            return jsonify({"ok": False, "error": "Nhân vật chưa có tiểu sử DILA"}), 400

        conn.execute("UPDATE people SET bio_vi=? WHERE id=?", (bio_vi, person_id))
        conn.commit()

        resp = {"ok": True, "translation_id": new_id, "status": "edited"}
        if t166:
            resp["identity_status"] = t166['identity_status']
            resp["identity_issues"] = t166['identity_issues']
        return jsonify(resp)
    finally:
        conn.close()




@app.route('/daoanh/api/admin/person/<person_id>/dila_vi', methods=['POST'])
def api_admin_save_person_dila_vi(person_id):
    """POST /daoanh/api/admin/person/<person_id>/dila_vi
    Body: {translation_id?: int, bio_concise_vi?: str, bio_extensive_vi?: str,
           dynasty_vi?: str, occupation_vi?: str, place_of_origin_vi?: str,
           works_tripitaka_vi?: str, works_by_vi?: str, mentioned_in_vi?: str,
           active_at_vi?: str, alt_names_vi?: list[str]}
    Lưu các field đã chỉnh sửa vào translation_cache (dila_card, status=edited)
    và cập nhật people.bio_vi nếu có bio_concise_vi.
    Header: X-Session-Token (bắt buộc).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    translation_id = data.get('translation_id')

    TEXT_FIELDS = ['bio_concise_vi', 'bio_extensive_vi', 'dynasty_vi', 'occupation_vi',
                   'place_of_origin_vi', 'works_tripitaka_vi', 'works_by_vi', 'secondary_lit_vi',
                   'mentioned_in_vi', 'active_at_vi', 'death_note_vi', 'birth_death_quote_vi']

    updates = {}
    for k in TEXT_FIELDS:
        if k in data and data[k] is not None:
            updates[k] = data[k].strip()
    if 'alt_names_vi' in data and isinstance(data['alt_names_vi'], list):
        updates['alt_names_vi'] = [s.strip() for s in data['alt_names_vi'] if s and s.strip()]

    if not updates:
        return jsonify({"ok": False, "error": "Không có field nào để lưu"}), 400

    import json as _j
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()

        # T166 §6.3 — admin-manual mirror: cập nhật thành vi_dict cho post_check,
        # RECORD-not-block (admin là authority, chỉ ghi identity metadata).
        t166 = None
        _identity_issue = None
        _vi_merged = None

        if translation_id:
            row = conn.execute(
                "SELECT translated_text FROM translation_cache WHERE id=? AND source_type='dila_card'",
                (translation_id,)
            ).fetchone()
            if row:
                try:
                    vi_dict = _j.loads(row['translated_text'])
                except Exception:
                    vi_dict = {}
                vi_dict.update(updates)
                _vi_merged = _j.dumps(vi_dict, ensure_ascii=False)
                ph = conn.execute("SELECT bio FROM people WHERE id = ?", (person_id,)).fetchone()
                if ph and ph['bio']:
                    t166 = _t166_post_check_translation(
                        conn, ph['bio'], _vi_merged,
                        policy=_t166_identity_lock_policy(conn))
                    _identity_issue = json.dumps(
                        t166['identity_issues'], ensure_ascii=False) if t166['identity_issues'] else None
                if _t166_has_col(conn, 'translation_cache', 'identity_status') and t166:
                    conn.execute(
                        "UPDATE translation_cache SET translated_text=?, status='edited', "
                        " identity_status=?, identity_issues=?, identity_lock_hash=?, updated_at=? "
                        "WHERE id=?",
                        (_vi_merged, t166['identity_status'], _identity_issue,
                         t166['identity_lock_hash'], now, translation_id)
                    )
                else:
                    conn.execute(
                        "UPDATE translation_cache SET translated_text=?, status='edited', updated_at=? WHERE id=?",
                        (_vi_merged if _vi_merged is not None else row['translated_text'], now, translation_id)
                    )

        if 'bio_concise_vi' in updates and updates['bio_concise_vi']:
            conn.execute("UPDATE people SET bio_vi=? WHERE id=?", (updates['bio_concise_vi'], person_id))

        conn.commit()
        resp = {"ok": True, "translation_id": translation_id, "status": "edited"}
        if t166:
            resp["identity_status"] = t166['identity_status']
            resp["identity_issues"] = t166['identity_issues']
        return jsonify(resp)
    finally:
        conn.close()




@app.route('/daoanh/api/admin/person/<person_id>/name_vi', methods=['POST'])
def api_admin_save_person_name_vi(person_id):
    """POST /daoanh/api/admin/person/<person_id>/name_vi
    Body: {name_vi: str}
    Lưu tên tiếng Việt (name_vi) vào bảng people.
    Header: X-Session-Token (bắt buộc).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    name_vi = (data.get('name_vi') or '').strip()
    if not name_vi:
        return jsonify({"ok": False, "error": "name_vi không được để trống"}), 400

    conn = get_db_connection()
    try:
        conn.execute("UPDATE people SET name_vi=? WHERE id=?", (name_vi, person_id))
        # Sync person_hanviet_debug: legacy + match_status + validation_status + reason
        conn.execute(
            "UPDATE person_hanviet_debug "
            "SET han_viet_legacy=?, "
            "    legacy_match_status=CASE WHEN lower(han_viet_charwise)=lower(?) THEN 'ok' ELSE 'differs' END, "
            "    han_viet_validation_status=CASE WHEN lower(han_viet_charwise)=lower(?) THEN 'valid' ELSE han_viet_validation_status END, "
            "    han_viet_validation_reason=CASE WHEN lower(han_viet_charwise)=lower(?) THEN '' ELSE 'legacy name_vi khác charwise' END "
            "WHERE person_id=?",
            (name_vi, name_vi, name_vi, name_vi, person_id)
        )
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()




@app.route('/daoanh/api/person/<person_id>/dila_full')
def api_person_dila_full(person_id):
    """GET /daoanh/api/person/<person_id>/dila_full
    T148: Trả về dữ liệu đầy đủ từ DILA Person Authority XML cho một person:
    - alt_names: các tên khác (persName type="alternative")
    - listbibl: danh sách CBETA citations (listBibl/bibl)
    - works_tripitaka: kinh điển trong Đại Tạng (note type="worksInTripitaka")
    - works_by: tác phẩm (note type="worksBy")
    - mentioned_in: được đề cập trong (note type="mentionedIn")
    Load XML lần đầu (~3-5s), cache trong RAM cho các lần tiếp theo.
    """
    extra = _t148_get_extra(person_id)
    if not extra:
        return jsonify({"ok": True, "person_id": person_id, "has_extra": False})
    # T372: Removed TTL name loading for relations
    # Show only Chinese name + charwise transliteration, not full temple name
    relations = list(extra.get('relations') or [])
    # T372 (bổ sung 2026-10-13): gắn hanviet_charwise (suy luận tự động, không phải
    # tên nguồn DILA/ZQLOCAL đã xác thực) cho mỗi relation để admin/person.html
    # relCardVi() có fallback hiển thị khi relation chưa có tên Việt chính thức.
    # Ưu tiên giá trị đã precompute trong person_hanviet_debug (T172 — xử lý đa âm
    # tốt hơn, ví dụ 行 trong "行思" → "Hành" chứ không phải "hàng" mặc định trong
    # hanviet_fallback); chỉ tính live bằng _hanviet_charwise_translit() khi
    # person đó chưa có dòng trong person_hanviet_debug.
    _rel_ids = [_r.get('person_id') for _r in relations if _r.get('person_id')]
    _precomputed = {}
    _rel_name_vi = {}
    if _rel_ids:
        _conn = get_db_connection()
        try:
            _rows = _conn.execute(
                "SELECT person_id, han_viet_charwise FROM person_hanviet_debug "
                "WHERE person_id IN ({})".format(','.join('?' * len(_rel_ids))),
                _rel_ids
            ).fetchall()
            _precomputed = {row['person_id']: row['han_viet_charwise'] for row in _rows}
            # BUG-043 (T421): tên Việt của SƯ PHỤ/ĐỆ TỬ đã có sẵn trong people.name_vi
            # (phiên âm Hán-Việt — xem person_hanviet_debug.han_viet_legacy nguồn gốc)
            # cho hầu hết relation person_id, nhưng route này trước đây không trả về
            # field này nên UI (places.html _relGroup/_linRelationCard) luôn fallback
            # về tên Hán thô. Join thêm name_vi từ people — KHÔNG gọi AI, KHÔNG ghi DB.
            _vi_rows = _conn.execute(
                "SELECT id, name_vi FROM people WHERE id IN ({}) AND name_vi IS NOT NULL AND name_vi != ''".format(
                    ','.join('?' * len(_rel_ids))),
                _rel_ids
            ).fetchall()
            _rel_name_vi = {row['id']: row['name_vi'] for row in _vi_rows}
        finally:
            _conn.close()
    for _r in relations:
        _pre = _precomputed.get(_r.get('person_id'))
        if _pre:
            _r['hanviet_charwise'] = _normalize_charwise_caps(_pre)
        else:
            _charwise, _ = _hanviet_charwise_translit(_r.get('name', ''))
            _r['hanviet_charwise'] = _charwise or None
        _r['name_vi'] = _rel_name_vi.get(_r.get('person_id')) or None
    return jsonify({
        "ok": True,
        "person_id": person_id,
        "has_extra": True,
        "bio_extensive": extra.get('bio_extensive'),
        "alt_names": extra.get('alt_names') or [],
        "listbibl": extra.get('listbibl') or [],
        "listbibl_items": extra.get('listbibl_items') or [],
        "works_tripitaka": extra.get('works_tripitaka'),
        "works_by": extra.get('works_by'),
        "secondary_lit": extra.get('secondary_lit'),
        "mentioned_in": extra.get('mentioned_in'),
        "mentioned_in_refs": extra.get('mentioned_in_refs') or [],
        "active_at": extra.get('active_at'),
        "name_latin": extra.get('name_latin'),
        "occupation": extra.get('occupation'),
        "place_of_origin": extra.get('place_of_origin'),
        "birth_death_quote": extra.get('birth_death_quote'),
        "wikidata_id": extra.get('wikidata_id'),
        "wikidata_ids": extra.get('wikidata_ids') or [],
        "birth_date": extra.get('birth_date'),
        "death_date": extra.get('death_date'),
        "death_note": extra.get('death_note'),
        "relations": relations,
        "sex": extra.get('sex'),
        "dynasty_xml": extra.get('dynasty_xml'),
        "is_monk": extra.get('is_monk'),
    })




@app.route('/daoanh/api/person/<person_id>/dila-axis')
def api_person_dila_axis(person_id):
    """GET /daoanh/api/person/<person_id>/dila-axis
    T157 B-4: Trả về danh sách thầy/trò theo nguồn DILA (lineage_edge_assertions L2).
    da:isTeacherOf: subject=thầy → object=đệ tử.
    teachers: object=person_id (người khác là thầy của person_id)
    students: subject=person_id (person_id là thầy của người khác)
    """
    conn = get_db_connection()
    try:
        # person_id là thầy: subject=person_id, object=đệ tử
        student_rows = conn.execute(
            "SELECT a.object_person_id as pid, a.trust_level, a.ref, a.mapping_verified,"
            " p.name_zh, p.name_vi"
            " FROM lineage_edge_assertions a"
            " LEFT JOIN people p ON p.id = a.object_person_id"
            " WHERE a.source_code='DILA' AND a.subject_person_id=? AND a.status='active'"
            " GROUP BY a.object_person_id ORDER BY p.name_zh",
            (person_id,)
        ).fetchall()
        # person_id là trò: object=person_id, subject=thầy
        teacher_rows = conn.execute(
            "SELECT a.subject_person_id as pid, a.trust_level, a.ref, a.mapping_verified,"
            " p.name_zh, p.name_vi"
            " FROM lineage_edge_assertions a"
            " LEFT JOIN people p ON p.id = a.subject_person_id"
            " WHERE a.source_code='DILA' AND a.object_person_id=? AND a.status='active'"
            " GROUP BY a.subject_person_id ORDER BY p.name_zh",
            (person_id,)
        ).fetchall()
    finally:
        conn.close()

    def _row(r):
        nv = r['name_vi'] or ''
        return {
            'id': r['pid'],
            'name_zh': r['name_zh'] or '',
            'name_vi': nv if _ok_hanviet_name(nv) else '',
            'trust_level': r['trust_level'],
            'mapping_verified': bool(r['mapping_verified']),
        }

    return jsonify({
        'ok': True,
        'person_id': person_id,
        'teachers': [_row(r) for r in teacher_rows],
        'students': [_row(r) for r in student_rows],
    })




@app.route('/daoanh/api/entity/<entity_id>/web-enrichments', methods=['GET'])
def api_web_enrichments_list(entity_id):
    """GET: Lấy danh sách enrichments đã cache cho entity."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """SELECT id, source_name, source_url, summary_vi, status,
                      report_count, created_at, fetched_by
               FROM web_enrichment_cache
               WHERE entity_id=? AND status != 'rejected'
               ORDER BY CASE WHEN status='verified' THEN 0 ELSE 1 END, id DESC""",
            (entity_id,)
        ).fetchall()
        enrichments = [dict(r) for r in rows]
        return jsonify({"ok": True, "enrichments": enrichments, "count": len(enrichments)})
    finally:
        conn.close()




@app.route('/daoanh/api/entity/<entity_id>/web-enrich', methods=['POST'])
def api_web_enrich(entity_id):
    """POST: Fetch thông tin mới từ Wikipedia, AI tóm tắt, save cache.
    Cooldown 30 ngày: không fetch lại nếu đã có entry còn mới.
    """
    conn = get_db_connection()
    try:
        # Cooldown check (30 ngày)
        recent = conn.execute(
            """SELECT id, summary_vi, source_name, source_url, created_at, status
               FROM web_enrichment_cache
               WHERE entity_id=? AND status != 'rejected'
               AND julianday('now') - julianday(created_at) < 30
               ORDER BY id DESC LIMIT 1""",
            (entity_id,)
        ).fetchone()
        if recent:
            return jsonify({
                "ok": True, "from_cache": True,
                "enrichment_id": recent['id'],
                "summary_vi": recent['summary_vi'],
                "source_name": recent['source_name'],
                "source_url": recent['source_url'],
                "created_at": recent['created_at'],
                "status": recent['status'],
                "msg": "Đã có thông tin cập nhật trong 30 ngày qua"
            })

        # Lấy tên entity
        entity_type, name_zh, name_en, name_vi_guess = _t75_entity_info(entity_id, conn)
        if not entity_type:
            return jsonify({"ok": False, "error": f"Không tìm thấy entity {entity_id}"}), 404
        if not name_zh and not name_en:
            return jsonify({"ok": False, "error": "Entity không có tên để tra cứu"}), 400

        _raw_display = name_vi_guess or name_en or name_zh
        display_name = _raw_display.replace(TAM_DICH_SUFFIX, '').strip() if _raw_display else _raw_display

        # Tìm Wikipedia (vi → zh)
        wiki_url, raw_content, wiki_title, source_label = _t75_search_wikipedia(name_zh, name_en, lang='vi')
        if not wiki_url:
            # T112 D-Feedback: tự ghi "thiếu nguồn" khi entity không index được trên Wikipedia
            _t112_record_gap(entity_type, entity_id, display_name, 'thieu_nguon',
                             f"Không tìm thấy Wikipedia cho '{display_name}'",
                             source_hint='Wikipedia (vi|zh)')
            return jsonify({
                "ok": False,
                "error": f"Không tìm thấy thông tin Wikipedia cho '{display_name}'"
            }), 404

        # AI tóm tắt
        summary_vi = _t75_summarize(display_name, entity_type, raw_content, source_label, entity_id)
        if not summary_vi:
            return jsonify({"ok": False, "error": "Lỗi AI tóm tắt"}), 500

        # Lưu vào cache
        cur = conn.execute(
            """INSERT INTO web_enrichment_cache
               (entity_id, entity_type, source_url, source_name, raw_content, summary_vi, fetched_by, status)
               VALUES (?, ?, ?, ?, ?, ?, 'user', 'auto')""",
            (entity_id, entity_type, wiki_url, source_label, raw_content[:3000], summary_vi)
        )
        conn.commit()
        enrich_id = cur.lastrowid

        return jsonify({
            "ok": True, "from_cache": False,
            "enrichment_id": enrich_id,
            "summary_vi": summary_vi,
            "source_name": source_label,
            "source_url": wiki_url,
            "entity_name": display_name,
            "status": "auto"
        })
    finally:
        conn.close()




@app.route('/daoanh/api/entity/<entity_id>/web-enrich/report', methods=['POST'])
def api_web_enrich_report(entity_id):
    """POST: Báo lỗi enrichment — tăng report_count, status='reported' nếu >= 2."""
    data = request.get_json(silent=True) or {}
    enrich_id = data.get('enrichment_id')
    if not enrich_id:
        return jsonify({"ok": False, "error": "Thiếu enrichment_id"}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE web_enrichment_cache SET report_count = report_count + 1 WHERE id=? AND entity_id=?",
            (enrich_id, entity_id)
        )
        row = conn.execute("SELECT report_count FROM web_enrichment_cache WHERE id=?", (enrich_id,)).fetchone()
        if row and row['report_count'] >= 2:
            conn.execute("UPDATE web_enrichment_cache SET status='reported' WHERE id=?", (enrich_id,))
        conn.commit()
        return jsonify({"ok": True, "report_count": row['report_count'] if row else 1})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/entity-claims/unverified', methods=['GET'])
def api_admin_claims_unverified():
    """GET /daoanh/api/admin/entity-claims/unverified?page=&per_page=&entity_type=&status=
    T119 — hàng chờ claims chưa thẩm định (447,885 unverified); pagination, Zero-RAM."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    entity_type = (request.args.get('entity_type') or '').strip()
    status_f = (request.args.get('status') or 'unverified').strip()
    where = ["c.verification_status = ?"]
    params = []
    params.append(status_f if status_f != 'any' else '')
    if entity_type:
        where.append("e.entity_type = ?"); params.append(entity_type)
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id WHERE {wc}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT c.claim_id, c.entity_id, e.entity_type, e.canonical_label, c.claim_type,
                       c.predicate, c.object_text, c.source_reference, c.verification_status,
                       c.assertion_level, c.source_url, c.created_at
                FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id
                WHERE {wc}
                ORDER BY c.claim_id
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "claims": [dict(r) for r in rows]})
    finally:
        conn.close()




@app.route('/daoanh/api/research/entity/<entity_ref>/audit-trail', methods=['GET'])
def api_research_entity_audit_trail(entity_ref):
    """GET /daoanh/api/research/entity/<entity_ref>/audit-trail — T118 (implement trong T135, 2026-09-14):
    Audit Trail bậc Tiến sĩ (Policy Filter L3) — read-only, 0 ALTER, NO_DATA trung thực.
    Trả lịch sử thay đổi record từ en_audit_log (append-only) + audit_id SHA-256 từ
    entity_claims_audit (T109). entity_ref nhận PL… | A… | dila id; resolve qua entity_hub."""
    conn = get_db_connection()
    try:
        eid, ref = _resolve_entity_id(conn, entity_ref)
        pats = {ref, entity_ref}
        if eid is not None:
            hub = conn.execute("SELECT canonical_label FROM entity_hub WHERE entity_id=?", (eid,)).fetchone()
            if hub and hub['canonical_label']:
                pats.add(hub['canonical_label'])
        pats.discard(None)
        pats.discard('')
        pats = sorted(pats)
        same = ""
        params = []
        for p in pats:
            same += "entity_ref LIKE ? OR "
            params.append(f"%{p}%")
        same = same.rstrip(" OR ") or "0"

        history = conn.execute(f"""
            SELECT log_id, entity_ref, action, field_name, old_value, new_value,
                   evidence_sources, authority_rank, editor, verification_status, created_at
            FROM en_audit_log WHERE {same}
            ORDER BY log_id DESC LIMIT 200
        """, params).fetchall()

        claims_audit = {"total": 0, "by_status": {}, "samples": []}
        if eid is not None:
            rows = conn.execute("""
                SELECT c.claim_id, c.claim_type, c.predicate, c.object_text,
                       COALESCE(d.source_code, '') AS source_code,
                       c.verification_status, a.audit_id, c.reviewed_by, c.reviewed_at
                FROM entity_claims c
                LEFT JOIN data_sources d ON d.source_id = c.source_id
                LEFT JOIN entity_claims_audit a ON a.claim_id = c.claim_id
                WHERE c.entity_id = ?
                ORDER BY c.claim_id LIMIT 200
            """, (eid,)).fetchall()
            claims_audit["total"] = len(rows)
            for r in rows:
                claims_audit["by_status"][r["verification_status"]] = \
                    claims_audit["by_status"].get(r["verification_status"], 0) + 1
                if len(claims_audit["samples"]) < 20:
                    claims_audit["samples"].append(dict(r))
        else:
            claims_audit["note"] = "entity không resolve được qua entity_hub — chỉ trả history bằng chuỗi thô"

        return jsonify({
            "ok": True,
            "subject_id": entity_ref,
            "persona_level": "L3",
            "resolved": {"entity_hub_id": eid, "canonical": ref},
            "history": [dict(h) | {"audit_id": f"en-{h['log_id']}"} for h in history],
            "claims_audit": claims_audit,
            "data_status": "indexed" if (history or claims_audit["total"]) else "no_data"
        })
    finally:
        conn.close()




@app.route('/daoanh/api/admin/bio-review/<person_id>', methods=['POST'])
def api_admin_bio_review(person_id):
    """POST /daoanh/api/admin/bio-review/<person_id> — body {action, note?, editor?}
    T73 — approve (admin_approved=1) / reject (-1) 1 draft + ghi en_audit_log.
    KHÔNG tự ghi people.bio_vi — bước apply tách biệt (HITL 2 bước)."""
    body = request.get_json(silent=True) or {}
    action = (body.get('action') or '').strip().lower()
    note = (body.get('note') or '').strip()[:255]
    editor = (body.get('editor') or 'admin').strip()[:64]
    if action not in ('approve', 'reject'):
        return jsonify({"ok": False, "error": "action phải ∈ approve|reject"}), 400
    flag = 1 if action == 'approve' else -1
    conn = get_db_connection()
    try:
        r = conn.execute("SELECT bio_vi_draft, source_name FROM person_bio_vi_draft WHERE person_id=?",
                         (person_id,)).fetchone()
        if not r:
            return jsonify({"ok": False, "error": "Không có draft cho person này"}), 404
        conn.execute(
            "UPDATE person_bio_vi_draft SET admin_approved=?, admin_note=?, "
            "updated_at=? WHERE person_id=?",
            (flag, note, datetime.now().isoformat(timespec='seconds'), person_id))
        conn.execute(
            "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor)"
            " VALUES (?, ?, 'bio_vi_draft', ?, ?, ?)",
            (person_id, 'bio_review_' + action, 'unreviewed', str(flag), editor))
        conn.commit()
        return jsonify({"ok": True, "person_id": person_id, "action": action, "status": flag})
    finally:
        conn.close()




@app.route('/daoanh/api/v1/entity/<entity_id>/lookup', methods=['GET'])
def api_v1_entity_lookup(entity_id):
    """GET /daoanh/api/v1/entity/<entity_id>/lookup — 5-layer unified lookup.
    Reuse tables hoàn toàn (T120 spec: 'Không tạo bảng mới'). Read-only, Zero-RAM.
    ?live=1: fetch Wikidata on-demand (Phase A). HITL: chỉ trả data candidate, KHÔNG ghi DB.
    """
    conn = get_db_connection()
    live = request.args.get('live', '0') == '1'
    live_result = None
    try:
        found = {}
        sources_used = []
        confidence = 0.0

        # Layer 1 — DILA core: entity_hub / entity + namevi_map_places + places/places_dila
        hub = conn.execute(
            "SELECT entity_id, canonical_label, entity_type FROM entity_hub WHERE entity_id = ?",
            (entity_id,)
        ).fetchone()
        if not hub:
            hub = conn.execute(
                "SELECT entity_id, alias_zh AS canonical_label, alias_vi AS canonical_name_vi, entity_type "
                "FROM entity WHERE entity_id = ?",
                (entity_id,)
            ).fetchone()
        if hub:
            core = {
                "entity_id": entity_id,
                "canonical_name_zh": hub['canonical_label'],
                "entity_type": hub['entity_type'],
            }
            vi_row = conn.execute(
                "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? OR name_zh = ? LIMIT 1",
                (entity_id, hub['canonical_label'] or '')
            ).fetchone()
            core["canonical_name_vi"] = vi_row['name_vi'] if vi_row else hub.get('canonical_name_vi')
            found['core'] = core
            sources_used.append('dila')
            confidence += 0.5
            if core.get('canonical_name_vi'):
                confidence += 0.1

            # DILA geo detail (places_dila, fallback places theo short/long ID)
            dila = conn.execute(
                "SELECT name_zh, geo_lat, geo_long, note, district, note_category FROM places_dila "
                "WHERE id = ?",
                (entity_id,)
            ).fetchone()
            if not dila or not dila['geo_lat']:
                dila = None
            places_fb = None
            if not dila:
                places_fb = conn.execute(
                    "SELECT name_zh, gps_lat, gps_long, province FROM places WHERE id = ?",
                    (entity_id,)
                ).fetchone()
            if dila and dila['geo_lat']:
                found['dila'] = {
                    "name_zh": dila['name_zh'],
                    "geo_lat": dila['geo_lat'],
                    "geo_long": dila['geo_long'],
                    "district": dila['district'],
                    "note": dila['note'],
                    "conf": 1.0,
                }
                found['core'].setdefault('geo_lat', dila['geo_lat'])
                found['core'].setdefault('geo_long', dila['geo_long'])
            elif places_fb and (places_fb['gps_lat'] or places_fb['gps_long']):
                found['dila'] = {
                    "name_zh": places_fb['name_zh'],
                    "geo_lat": places_fb['gps_lat'],
                    "geo_long": places_fb['gps_long'],
                    "district": places_fb['province'],
                    "conf": 1.0,
                }
                found['core'].setdefault('geo_lat', places_fb['gps_lat'])
                found['core'].setdefault('geo_long', places_fb['gps_long'])

        # Layer 2 — Wikidata ref: geo_cross_ref bridge (đã có 181 QID, candidate T121)
        gcr = conn.execute(
            "SELECT wikidata_qid, bdrc_id, confidence, mapped_by FROM geo_cross_ref WHERE dila_id = ?",
            (entity_id,)
        ).fetchone()
        if gcr:
            wd = {"qid": gcr['wikidata_qid'], "mapped_by": gcr['mapped_by'], "conf": gcr['confidence']}
            if gcr['bdrc_id']:
                wd['bdrc_id'] = gcr['bdrc_id']
            found['wikidata_ref'] = wd
            confidence += (0.2 if gcr['confidence'] == 'verified' else 0.1)
            if gcr['wikidata_qid']:
                sources_used.append('wikidata_ref')
                # T120 Phase A — live Wikidata fetch (HITL-safe: no DB write, candidate in response only)
                if live and gcr['wikidata_qid']:
                    live_result = _t120_query_wikidata(gcr['wikidata_qid'])
                    if live_result:
                        found['wikidata_live'] = {
                            "qid": live_result['qid'],
                            "label_vi": live_result.get('label_vi'),
                            "label_zh": live_result.get('label_zh'),
                            "lat": live_result.get('lat'),
                            "lon": live_result.get('lon'),
                            "elevation_m": live_result.get('elevation_m'),
                            "status": "candidate",
                            "wiki": {k: v for k, v in live_result.items() if k.startswith('wiki_')},
                        }
                        sources_used.append('wikidata_live')
                        confidence += 0.15

        # Layer 3 — Wikipedia cache: place_wiki_snapshots
        wiki = conn.execute(
            "SELECT wiki_title, wiki_url, snippet, source, created_at FROM place_wiki_snapshots "
            "WHERE place_id = ?",
            (entity_id,)
        ).fetchone()
        if wiki:
            found['wikipedia'] = {
                "title": wiki['wiki_title'],
                "url": wiki['wiki_url'],
                "snippet": (wiki['snippet'] or '')[:500],
                "lang": wiki['source'],
                "cached_at": wiki['created_at'],
            }
            sources_used.append('wikipedia_cache')
            confidence += 0.1

        # Layer 4 — Web enrichment: web_enrichment_cache (verified/cached)
        enrich = conn.execute(
            "SELECT id, source_name, source_url, summary_vi, status, created_at "
            "FROM web_enrichment_cache WHERE entity_id = ? AND status != 'rejected' "
            "ORDER BY CASE WHEN status='verified' THEN 0 ELSE 1 END, id DESC LIMIT 1",
            (entity_id,)
        ).fetchone()
        if enrich:
            found['web_enrichment'] = {
                "enrichment_id": enrich['id'],
                "source_name": enrich['source_name'],
                "source_url": enrich['source_url'],
                "summary_vi": (enrich['summary_vi'] or '')[:800],
                "status": enrich['status'],
                "cached_at": enrich['created_at'],
            }
            sources_used.append('web_enrichment')
            confidence += (0.1 if enrich['status'] == 'verified' else 0.05)

        # Layer 5 — Wikidata QID → Wikipedia name variant hint (bridge đã có trong geo_cross_ref)
        if gcr and gcr['wikidata_qid']:
            found.setdefault('name_variant', {})['wikidata'] = {
                "qid": gcr['wikidata_qid']}

        if not found:
            return jsonify({"ok": False, "error": "Entity not found in any lookup layer"}), 404

        resp = {
            "ok": True,
            "entity_id": entity_id,
            "sources_used": sources_used,
            "confidence": round(min(confidence, 1.0), 2),
            "data": found,
        }
        # T120 Phase A — live mode metadata (no DB write, HITL-safe)
        if live:
            resp["live"] = True
            resp["live_unavailable"] = (live_result is None and bool(gcr and gcr['wikidata_qid']))
            if resp["live_unavailable"]:
                resp["live_error"] = "network_timeout_or_blocked"
        return resp
    finally:
        conn.close()



# ─────────────── /T182 ───────────────

# ─────────────── Monk TTL Admin (monk_ttl_add) ───────────────

@app.route('/daoanh/api/admin/lineages', methods=['GET'])
def admin_list_lineages():
    """Trả danh sách tông phái và Khai Tổ từ bảng lineage_founders."""
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT lineage_name, khai_to_name_vi, khai_to_gen, lineage_key
            FROM lineage_founders
            ORDER BY khai_to_gen ASC
        """).fetchall()
        return jsonify({
            "ok": True,
            "lineages": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/monk_names_slugs', methods=['GET'])
def admin_monk_names_slugs():
    """GET /daoanh/api/admin/monk_names_slugs
    Trả [{name_vi, slug}] đọc trực tiếp từ *.ttl trong data/ttl/.
    Chỉ lấy monk chính (bkg:Monk), không lấy stub thầy/đệ tử.
    Dùng cho autocomplete 'Tên thầy' trong monk_ttl_add — đảm bảo slug khớp
    chính xác với URI đã đăng ký trong TTL, tránh duplicate slug."""
    import glob as _glob, re as _re, os as _os
    ttl_dir = _os.path.join(_os.path.dirname(__file__), 'data', 'ttl')
    result = []
    seen = set()
    try:
        for path in sorted(_glob.glob(_os.path.join(ttl_dir, '*.ttl'))):
            try:
                with open(path, encoding='utf-8') as _f:
                    content = _f.read()
                # Tìm monk chính: <ex:monk/SLUG> a <bkg:Monk>
                m = _re.search(r'<ex:monk/([^>]+)>\s+a\s+<bkg:Monk>', content)
                if not m:
                    continue
                slug = m.group(1).strip()
                if slug in seen:
                    continue
                seen.add(slug)
                # Lấy rdfs:label @vi đầu tiên trong 400 ký tự sau khai báo Monk
                lm = _re.search(r'rdfs:label "([^"]+)"@vi', content[m.start():m.start() + 400])
                if not lm:
                    continue
                result.append({'name_vi': lm.group(1), 'slug': slug})
            except Exception:
                continue
        result.sort(key=lambda x: x['name_vi'])
        return jsonify({'ok': True, 'monks': result, 'total': len(result)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/admin/monk_ttl', methods=['POST'])
def admin_save_monk_ttl():
    """Nhận TTL content từ form và lưu vào data/ttl/[filename].ttl."""
    import re as _re, os as _os
    body = request.get_json(force=True) or {}
    filename    = body.get('filename', '').strip()
    slug        = body.get('slug', '').strip()
    ttl_content = body.get('ttl_content', '').strip()

    if not filename or not slug or not ttl_content:
        return jsonify({"ok": False, "error": "Thiếu filename, slug hoặc ttl_content"}), 400

    # Sanitize filename — chỉ cho phép chữ, số, dấu gạch
    safe_name = _re.sub(r'[^A-Za-z0-9\-_]', '', filename)
    if not safe_name:
        return jsonify({"ok": False, "error": "Tên file không hợp lệ"}), 400

    ttl_dir = _os.path.join(_os.path.dirname(__file__), 'data', 'ttl')
    _os.makedirs(ttl_dir, exist_ok=True)
    filepath = _os.path.join(ttl_dir, f'{safe_name}.ttl')

    # Không ghi đè file đã tồn tại (tránh mất dữ liệu)
    if _os.path.exists(filepath):
        return jsonify({
            "ok": False,
            "error": f"File đã tồn tại: {safe_name}.ttl — Đổi tên hoặc xóa file cũ trước"
        }), 409

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ttl_content)

    return jsonify({
        "ok": True,
        "filepath": f"data/ttl/{safe_name}.ttl",
        "slug": slug,
        "message": f"Đã lưu {safe_name}.ttl thành công!"
    })
