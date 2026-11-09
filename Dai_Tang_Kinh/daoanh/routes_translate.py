"""Route nhom translate: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""
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
from core import ANTHROPIC_KEY, CBETA_REF_TABLE, DATA_DIR, GEMINI_API_KEY, GROQ_KEY, GROQ_MODEL, GROQ_URL, SQLITE_DB, _BUDDHIST_SYSTEM_PROMPT, _DN_SIGLA_MAP, _T181_IMPORT_PY, _T181_XML_ROOT, _T447_RETRANSLATE_UNSUPPORTED_SOURCE_TYPES, _T95_JOBS_LIST_SQL, _T95_UNITS_SQL, _anthropic_sdk, _build_dila_card_prompt, _call_gemini, _dict_or, _error_report_suggestion, _json_or_parse, _llm_config_read, _ok_hanviet_name, _p8_compute_assertion_status, _p8_pilot_active, _parse_dila_vi_json, _post_edit_hanzi_leakage, _resolve_dila_id, _save_suggested_rules, _sync_ref_passage, _t128_parse_relation_ref, _t148_get_extra, _t166_has_col, _t181_xml_path, _t183_lazy_fetch_xml, _t50_read_job, _t50_start_sigla, _t50_write_job, _t55_normalize_sigla, _t73_build_style_prompt, _t73_call_gemini, _t73_get_active_rules, _t73_rules_version, _t73_source_hash, _t73_style_lock, _t85_get_segments, _t85_post_segments, _t85_units, _t86_parse_ref_passage, _t95_badge, _t95_coverage, _t95_export_iter, _t95_export_markdown, _t95_raw_dir, _t95_worker, app, clean_gemini_output, extract_sentence_with_place, get_cbdb_conn, get_cbeta_conn, get_db, parse_dila_district, parse_ref, translate_han_vi, verify_session



@app.route('/daoanh/api/admin/translate_context', methods=['POST'])
def translate_context():
    body = request.get_json(silent=True) or {}
    text = (body.get('text') or '').strip()
    style = body.get('style', 'formal')
    source_lang = body.get('source_lang', 'zho-Hant')
    target_lang = body.get('target_lang', 'vi')
    if not text:
        return jsonify({"success": False, "error": "Thiếu text"}), 400
    # T123 — Style Constitution unified builder (thay prompt cứng) — T165: filter rules theo text
    conn = get_db_connection()
    try:
        lock = _t73_style_lock(conn, source_text=text)
        rv = lock['rules_version']
    finally:
        conn.close()
    prompt = _t73_build_style_prompt(text, lock, label='đoạn văn')
    meta = {"llm_provider": "", "style": style, "source_lang": source_lang,
            "target_lang": target_lang, "rules_version": rv}
    # Try Groq first
    try:
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.1, 'max_tokens': 2048},
            timeout=15)
        result = resp.json()
        if result.get('choices'):
            text_vi = result['choices'][0]['message']['content']
            if text_vi:
                text_vi = clean_gemini_output(text_vi)
                meta["llm_provider"] = GROQ_MODEL
                return jsonify({"success": True, "text_vi": text_vi, "meta": meta})
    except Exception:
        pass
    # Fallback: translators (Google)
    try:
        import translators as ts
        text_vi = ts.translate_text(text[:3000], to_language='vi', translator='google')
        if text_vi:
            text_vi = clean_gemini_output(text_vi)
            meta["llm_provider"] = "google-translate"
            return jsonify({"success": True, "text_vi": text_vi, "meta": meta})
    except Exception:
        pass
    # Fallback: deep-translator
    try:
        from deep_translator import GoogleTranslator
        text_vi = GoogleTranslator(source='zh-CN', target='vi').translate(text)
        if text_vi:
            text_vi = clean_gemini_output(text_vi)
            meta["llm_provider"] = "google-translate"
            return jsonify({"success": True, "text_vi": text_vi, "meta": meta})
    except Exception:
        pass
    meta["llm_provider"] = "fallback"
    return jsonify({"success": True, "text_vi": text, "meta": meta})




@app.route('/daoanh/api/admin/cbeta/update_summary', methods=['POST'])
def admin_cbeta_update_summary():
    """
    POST /daoanh/api/admin/cbeta/update_summary
    Body: { ref: "T50n2060_p0574b20", vi_summary_clean: "..." }
    Manual override for vi_summary_clean of a CBETA ref.
    """
    try:
        body = request.get_json(silent=True) or {}
        ref = (body.get('ref') or '').strip()
        new_summary = (body.get('vi_summary_clean') or '').strip()
        if not ref:
            return jsonify({"ok": False, "error": "Thiếu ref"}), 400
        conn = get_db_connection()
        conn.execute(f"""
            UPDATE {CBETA_REF_TABLE}
            SET vi_summary_clean = ?, vi_summary_raw = COALESCE(vi_summary_raw, ''),
                updated_at = CURRENT_TIMESTAMP
            WHERE ref_code = ?
        """, (new_summary, ref))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "success": True, "ref": ref})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/cbeta/explain', methods=['POST'])
def admin_cbeta_explain():
    """
    POST /daoanh/api/admin/cbeta/explain
    Body: { ref: "T50n2060_p0457c16", place_han: "少林寺", place_id: "shaolin" }
    Flow:
    1) Sync han_text from cbeta.db (reuse _sync_ref_passage).
    2) Extract sentence containing place_han.
    3) Check cbeta_ref_explanations cache → return instantly if found.
    4) Call Gemini for explanation → cache → return.
    """
    try:
        body = request.get_json(silent=True) or {}
        ref = (body.get('ref') or '').strip()
        place_han = (body.get('place_han') or '').strip()
        place_id = (body.get('place_id') or '').strip()

        if not ref or not place_han:
            return jsonify({"ok": False, "error": "Thiếu ref hoặc place_han"}), 400
        if not place_id:
            place_id = place_han

        # 1) Sync han_text from cbeta.db
        sync_result = _sync_ref_passage(ref)
        if not sync_result or not sync_result.get('han_text'):
            return jsonify({"ok": False, "error": "no_text", "message": f"Chưa có văn bản CBETA cho {ref}"}), 404

        han_text = sync_result['han_text']

        # 2) Extract sentence containing place_han
        han_sentence = extract_sentence_with_place(han_text, place_han)
        if not han_sentence:
            return jsonify({"ok": False, "error": "no_match", "message": f"Không tìm thấy '{place_han}' trong văn bản CBETA"}), 404

        # 3) Check cache
        conn = get_db_connection()
        try:
            cached = conn.execute(
                "SELECT explanation_vi FROM cbeta_ref_explanations WHERE ref = ? AND place_id = ?",
                (ref, place_id)
            ).fetchone()
            if cached and cached['explanation_vi']:
                return jsonify({
                    "ok": True, "success": True,
                    "ref": ref, "place_han": place_han, "place_id": place_id,
                    "han_sentence": han_sentence,
                    "explanation_vi": cached['explanation_vi'],
                    "cached": True
                })
        finally:
            conn.close()

        # 4) Call Gemini
        prompt = f"""Bạn là chuyên gia Phật học và Hán-Nôm. Hãy giải thích địa danh / khái niệm sau đây xuất hiện trong văn bản CBETA (Phật giáo Trung Quốc cổ đại):

Địa danh / thuật ngữ Hán: {place_han}
Số hiệu CBETA: {ref}

Câu văn gốc:
「{han_sentence}」

Yêu cầu:
- Giải thích bằng tiếng Việt, 2–4 câu, hướng tới độc giả phổ thông.
- Cho biết ý nghĩa, vị trí (nếu là địa danh), và bối cảnh xuất hiện trong đoạn kinh.
- Nếu là địa danh, cố gắng liên hệ với tên gọi Việt Nam hiện đại nếu có.
- Chỉ tường thuật dựa trên văn bản, không thêm hư cấu."""
        explanation = _call_gemini(prompt, timeout=15)
        if not explanation:
            explanation = f"Địa danh {place_han} xuất hiện trong văn bản CBETA {ref}. {han_sentence}"
        explanation = clean_gemini_output(explanation)

        # 5) Cache
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO cbeta_ref_explanations (ref, place_id, place_han, han_sentence, explanation_vi)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ref, place_id) DO UPDATE SET
                    place_han=excluded.place_han,
                    han_sentence=excluded.han_sentence,
                    explanation_vi=excluded.explanation_vi,
                    updated_at=CURRENT_TIMESTAMP
            """, (ref, place_id, place_han, han_sentence, explanation))
            conn.commit()
        finally:
            conn.close()

        return jsonify({
            "ok": True, "success": True,
            "ref": ref, "place_han": place_han, "place_id": place_id,
            "han_sentence": han_sentence,
            "explanation_vi": explanation,
            "cached": False
        })

    except Exception as e:
        import traceback
        app.logger.error(f"admin_cbeta_explain error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/places/<place_id>/cbeta')
def api_places_cbeta(place_id):
    """GET /daoanh/api/places/<id>/cbeta — CBETA passages + catalog matches for a place."""
    import re as _re
    try:
        conn = get_db_connection()
        dila_id, name_zh = _resolve_dila_id(conn, place_id)

        passages = []
        fosizhi_entries = []
        if dila_id:
            dila_row = conn.execute("SELECT listbibl, raw_xml FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
            if dila_row and dila_row['listbibl']:
                listbibl_raw = dila_row['listbibl']
                seen_refs = set()
                for entry in [e.strip() for e in listbibl_raw.split(';') if e.strip()]:
                    m = _re.match(r'\(\s*CBETA\s+([\w_]+)\s*\)\s*(.*)', entry)
                    if m:
                        ref = m.group(1).strip()
                        if ref in seen_refs:
                            continue
                        seen_refs.add(ref)
                        rest = m.group(2).strip()
                        tag_m = _re.search(r'\{([^}]+)\}', rest)
                        place_tag = tag_m.group(1).strip() if tag_m else ''
                        title_context = _re.sub(r'\s*\{[^}]+\}\s*', '', rest).strip()
                        passages.append({
                            'ref_code': ref,
                            'sigla': ref.split('_')[0] if '_' in ref else ref,
                            'title_context': title_context,
                            'place_tag': place_tag,
                        })
            # Fosi Zhi (g-series): chỉ có trong raw_xml, không có trong listbibl
            raw_xml = (dila_row['raw_xml'] or '') if dila_row else ''
            if raw_xml:
                # ns0:ref namespace prefix + URL may span a line — use flexible pattern
                fz_matches = _re.findall(
                    r'target="([^"]*fosizhi[^"]*)">([^(<]+)\(([^)]+)\)</[^>]+>\s*\{([^}]+)\}',
                    raw_xml
                )
                seen_fz = set()
                for url, ref_code, book_title, place_tag in fz_matches:
                    ref_code = ref_code.strip()
                    if ref_code in seen_fz:
                        continue
                    seen_fz.add(ref_code)
                    fosizhi_entries.append({
                        'ref_code': ref_code,
                        'book_title': book_title.strip(),
                        'place_tag': place_tag.strip(),
                        'url': url.replace('&amp;', '&')
                    })

        # Kinh Điển Liên Quan — T-series only, JOIN cbeta_catalog_vn (Nguyễn Minh Tiến, CC BY-SA 4.0)
        # Chỉ T-series vì cbeta_catalog_vn chỉ cover Đại Chính Tạng; X-series không có tên Việt.
        related_texts = []
        if dila_id:
            dila_row2 = conn.execute("SELECT listbibl FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
            if dila_row2 and dila_row2['listbibl']:
                seen_sh = set()
                for m2 in _re.finditer(r'CBETA\s+T\d+n(\d+)_', dila_row2['listbibl']):
                    sh = m2.group(1)
                    if sh in seen_sh:
                        continue
                    seen_sh.add(sh)
                    cat = conn.execute(
                        "SELECT title_zh, title_vi, translator_vi, dynasty_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ? AND (series='T' OR series IS NULL) LIMIT 1",
                        (sh,)
                    ).fetchone()
                    if cat and cat['title_vi']:
                        related_texts.append({
                            'sh_number': sh,
                            'title_zh': cat['title_zh'],
                            'title_vi': cat['title_vi'],
                            'translator_vi': cat['translator_vi'] or '',
                            'dynasty_vi': cat['dynasty_vi'] or '',
                        })

        conn.close()
        return jsonify({"ok": True, "place_id": place_id, "dila_id": dila_id,
                        "passages": passages, "fosizhi_entries": fosizhi_entries,
                        "related_texts": related_texts})
    except Exception as e:
        app.logger.error(f"api_places_cbeta error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/cbeta/<sigla>/related')
def api_cbeta_related(sigla):
    """GET /daoanh/api/cbeta/<sigla>/related — gợi ý 3 nhóm (T55 spec §T55b).
    Nhóm 1 'crossref' — SAT URL / Toh 84000 / Pali map (đối chiếu chuẩn).
    Nhóm 2 'topic'    — 2 kinh khác cùng đề tài (chia sẻ ≥3 DILA persons, verified).
    Nhóm 3 'persons'  — thiền sư/nhân vật xuất hiện trong kinh này.
    Trung thực: nhóm không có data → trả [] kèm 'status':'NO_DATA' chứ không bịa.
    """
    try:
        s_key, s_num = _t55_normalize_sigla(sigla)
        s_series = (s_key or 'T')[0].upper()
        conn = get_db_connection()

        # ── Nhóm 1: crossref ───────────────────────────────────────────────
        crossref = []
        sat = conn.execute(
            "SELECT cbeta_sigla, sat_url, has_unique FROM sat_crossref WHERE cbeta_sigla = ? LIMIT 1",
            (s_key,)).fetchone()
        if sat:
            crossref.append({'kind': 'sat', 'sigla': sat['cbeta_sigla'],
                             'url': sat['sat_url'], 'has_unique': bool(sat['has_unique'])})
        toh = conn.execute(
            "SELECT toh, cbeta_sigla, title_vi, title_en, url_84000, canon_section, confidence "
            "FROM toh_cbeta_crossref WHERE cbeta_sigla = ? LIMIT 1", (s_key,)).fetchone()
        if toh:
            crossref.append({'kind': 'toh', 'toh': toh['toh'], 'sigla': toh['cbeta_sigla'],
                             'title_vi': toh['title_vi'], 'title_en': toh['title_en'],
                             'url_84000': toh['url_84000'], 'canon_section': toh['canon_section'],
                             'confidence': toh['confidence']})
        if s_num and s_num.isdigit():
            pali_sh = '{:04d}'.format(int(s_num))
            pali = conn.execute(
                "SELECT sh, pali_title, pts_sutta, note FROM pali_cbeta_map WHERE sh = ? LIMIT 1",
                (pali_sh,)).fetchone()
            if pali:
                crossref.append({'kind': 'pali', 'pali_title': pali['pali_title'],
                                 'pts_sutta': pali['pts_sutta'], 'note': pali['note']})

        # ── Nhóm 3: persons trong chính kinh ───────────────────────────────
        persons = []
        p_rows = []
        if s_num and s_num.isdigit():
            # mentions lưu ref đầy đủ ('T51n2076'/'X77n1524') → GLOB theo series + số
            glob_pat = "{}*n{}".format(s_series, str(int(s_num)))
            p_rows = conn.execute(
                """SELECT dila_person_id, person_name_zh, COUNT(*) AS mentions
                   FROM cbeta_person_mentions
                   WHERE cbeta_text_sigla GLOB ?
                   GROUP BY dila_person_id, person_name_zh
                   ORDER BY mentions DESC LIMIT 12""", (glob_pat,)).fetchall()
        if not p_rows:
            # fallback: raw input (vài bảng lưu full ref như 'T50n2059_p0338c09')
            base = sigla.split('_')[0]
            p_rows = conn.execute(
                """SELECT dila_person_id, person_name_zh, COUNT(*) AS mentions
                   FROM cbeta_person_mentions
                   WHERE cbeta_text_sigla LIKE ?
                   GROUP BY dila_person_id, person_name_zh
                   ORDER BY mentions DESC LIMIT 12""", (base + '%',)).fetchall()
        pid_mapping = {}
        if p_rows:
            ids = [r['dila_person_id'] for r in p_rows]
            qmarks = ','.join('?' * len(ids))
            try:
                pmeta = conn.execute(f"""SELECT id, name_zh, name_vi, dynasty
                                         FROM people WHERE id IN ({qmarks})""", ids).fetchall()
                pid_mapping = {r['id']: r for r in pmeta}
            except Exception:
                pass
            for r in p_rows:
                meta = pid_mapping.get(r['dila_person_id'])
                persons.append({
                    'entity_id': r['dila_person_id'],
                    'name_zh': r['person_name_zh'],
                    'name_vi': meta['name_vi'] if meta else None,
                    'dynasty': meta['dynasty'] if meta else None,
                    'mentions': r['mentions']})

        # ── Nhóm 2: topic — 2 kinh khác chia sẻ same persons ──────────────
        topic = []
        if p_rows:
            ids = list({r['dila_person_id'] for r in p_rows})
            qmarks = ','.join('?' * len(ids))
            glob_pat = "{}*n{}".format(s_series, str(int(s_num))) if s_num and s_num.isdigit() else None
            if glob_pat:
                # loại trừ chính văn bản nguồn (mọi volume cùng số) để chỉ còn 'kinh khác'
                topic_rows = conn.execute(
                    f"""SELECT cbeta_text_sigla, COUNT(*) AS shared
                        FROM cbeta_person_mentions
                        WHERE dila_person_id IN ({qmarks}) AND cbeta_text_sigla NOT GLOB ?
                        GROUP BY cbeta_text_sigla
                        HAVING COUNT(*) >= 3
                        ORDER BY shared DESC LIMIT 8""", ids + [glob_pat]).fetchall()
                for r in topic_rows:
                    topic.append({'sigla': r['cbeta_text_sigla'], 'shared_persons': r['shared']})

        conn.close()
        resp = {
            'ok': True,
            'sigla': sigla, 'short_key': s_key, 'text_num': s_num,
            'groups': {
                'crossref': crossref or [{'status': 'NO_DATA'}],
                'topic': topic or [{'status': 'NO_DATA'}],
                'persons': persons or [{'status': 'NO_DATA'}],
            },
        }
        return jsonify(resp)

    except Exception as e:
        app.logger.error(f'api_cbeta_related error: {e}')
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/translate', methods=['POST'])
def api_translate_passage():
    """POST /daoanh/api/translate — Dịch đoạn Hán văn với cache DB.
    Body: { ref_code: str } — han_text không cần gửi, backend tự fetch từ DB
    Returns: { ok: bool, vi_text: str, cached: bool }
    """
    data = request.get_json(force=True, silent=True) or {}
    ref_code = (data.get('ref_code') or '').strip()

    if not ref_code:
        return jsonify({'ok': False, 'error': 'Thiếu ref_code'}), 400

    try:
        conn = get_db_connection()

        # Kiểm tra cache trước
        db_row = conn.execute(
            "SELECT han_text, vi_summary_clean FROM cbeta_ref_passages WHERE ref_code = ?",
            (ref_code,)
        ).fetchone()
        conn.close()

        if db_row and (db_row['vi_summary_clean'] or '').strip():
            return jsonify({'ok': True, 'vi_text': db_row['vi_summary_clean'].strip(), 'cached': True})

        han_text = (db_row['han_text'] or '').strip() if db_row else ''
        if not han_text:
            return jsonify({'ok': False, 'error': f'Không có nội dung hán văn cho {ref_code}'}), 404

        if not ANTHROPIC_KEY or _anthropic_sdk is None:
            return jsonify({'ok': False, 'error': 'ANTHROPIC_KEY chưa cấu hình hoặc module anthropic chưa cài — set env var và install package'}), 503

        # Gọi Claude Haiku
        client = _anthropic_sdk.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=2048,
            system=_BUDDHIST_SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': f'Dịch đoạn văn ngôn Phật giáo sau sang tiếng Việt:\n\n{han_text}'
            }]
        )
        vi_text = msg.content[0].text.strip()

        # Lưu cache vào DB
        if ref_code and vi_text:
            conn2 = get_db_connection()
            conn2.execute(
                "UPDATE cbeta_ref_passages SET vi_summary_clean = ? WHERE ref_code = ?",
                (vi_text, ref_code)
            )
            conn2.commit()
            conn2.close()

        return jsonify({'ok': True, 'vi_text': vi_text, 'cached': False})

    except Exception as e:
        app.logger.error(f'api_translate_passage error: {e}')
        if _anthropic_sdk is not None:
            return jsonify({'ok': False, 'error': f'Lỗi API: {e.status_code}'}), 502
        return jsonify({'ok': False, 'error': 'Lỗi dịch - module anthropic chưa sẵn sàng'}), 502
        return jsonify({'ok': False, 'error': str(e)}), 500




@app.route('/daoanh/api/lineage-ref/passage')
def api_lineage_ref_passage():
    """GET /daoanh/api/lineage-ref/passage?ref=... — resolve dẫn chiếu CBETA (từ edge
    marcus_networks.ref) → passage (mở Đọc trong Đại Tạng). Trung thực null nếu passage
    chưa được lập chỉ mục trong bảng passage."""
    ref = request.args.get('ref', '')
    conn = get_db_connection()
    try:
        result = _t86_parse_ref_passage(conn, ref)
        return jsonify({"ok": True, "resolved": result or {"found": False, "message": "Thiếu ref"}})
    finally:
        conn.close()




@app.route('/daoanh/api/relation/translate', methods=['POST'])
def api_relation_translate():
    """POST /daoanh/api/relation/translate — dịch AI đoạn dẫn chứng quan hệ (T128).

    body {ref, relation_id?, from_id?, to_id?, direction?}
    - Cache hit (translation_cache.source_hash = sha256(excerpt)[:24], source_type='relation_evidence')
      → trả ngay, KHÔNG gọi LLM.
    - Miss → Groq qwen (T73 _t73_build_style_prompt + _t73_call_gemini) → write-through
      translation_cache status='draft'.
    KHÔNG dùng legacy /api/translate (Claude, cần passage_id — evidence không có)."""
    data = request.get_json(silent=True) or {}
    ref = data.get('ref') or ''
    from_id = data.get('from_id') or ''
    to_id = data.get('to_id') or ''
    direction = data.get('direction') or ''
    relation_id = data.get('relation_id') or ''
    if not ref.strip():
        return jsonify({"ok": False, "error": "Thiếu dẫn chứng (ref)"}), 400

    parsed = _t128_parse_relation_ref(ref, from_id, to_id, direction)
    excerpt = parsed['original_excerpt']
    if not excerpt.strip():
        return jsonify({
            "ok": False,
            "error": "Dẫn chứng không có đoạn trích Hán văn để dịch (chỉ có URL/địa chỉ thư mục).",
            "parsed": parsed}), 422

    conn = get_db_connection()
    try:
        src_hash = parsed['text_hash'] or _t73_source_hash(excerpt.strip())
        # T165: dual-key lookup (constitution_hash → legacy rules_version) với source_type + edited guard
        xs = excerpt.strip()
        prompt_src = xs if len(xs) <= 1400 else xs[:1400]
        lock = _t73_style_lock(conn, source_text=prompt_src)
        existing = _t165_lookup_cache(conn, src_hash, lock['constitution_hash'],
                                      lock['rules_version'], 'relation_evidence')
        if existing:
            return jsonify({
                "ok": True, "from_cache": True, "translation_id": existing['id'],
                "translated_text": existing['translated_text'],
                "status": existing['status'], "model_id": existing['model_id'],
                "rules_version": existing['rules_version'],
                "rules_outdated": _t165_is_rules_outdated(
                    existing, lock['constitution_hash']),
                "parsed": parsed,
                "identity_status": _dict_or(existing, 'identity_status'),
                "identity_issues": _json_or_parse(existing, 'identity_issues')})

        # Cache miss → Groq (nhánh T123 Style Constitution)
        prompt = _t73_build_style_prompt(prompt_src, lock, label='đoạn dẫn chứng')
        vi, model_id, err_type = _t73_call_gemini(
            prompt, source_type='relation_evidence', source_text=prompt_src, conn=conn,
            constitution_hash=lock['constitution_hash'])
        if not vi:
            return jsonify({
                "ok": False, "error_type": err_type or 'api_error',
                "error": "Dịch thất bại — thử lại sau.", "parsed": parsed}), 503

        # T166 §6.3 — post_check trên đoạn dẫn chứng (tên religious + BUDDHIST_TERM)
        t166 = _t166_post_check_translation(
            conn, prompt_src, vi,
            policy=_t166_identity_lock_policy(conn))

        rv = lock['rules_version']
        now = datetime.now().isoformat()
        ent_id = parsed['relation_id'] or relation_id
        tid, replaced = _t165_write_cache(
            conn, src_hash, 'relation_evidence', ent_id, excerpt.strip(), vi, model_id, rv,
            status='draft',
            constitution_hash=lock.get('constitution_hash'),
            selected_rule_codes=lock.get('codes'),
            glossary_hash=lock.get('glossary_hash'),
            identity_status=t166['identity_status'],
            identity_issues=t166['identity_issues'],
            identity_lock_hash=t166['identity_lock_hash'])
        conn.commit()

        return jsonify({
            "ok": True, "from_cache": False, "translation_id": tid,
            "translated_text": vi, "status": 'draft', "model_id": model_id,
            "rules_version": rv, "parsed": parsed,
            "identity_status": t166['identity_status'],
            "identity_issues": t166['identity_issues']})
    except Exception as e:
        app.logger.error(f"api_relation_translate error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/admin/cbeta/fuzzy_rescore', methods=['POST'])
def api_cbeta_fuzzy_rescore():
    """POST — T03: Rescore cbeta_catalog_place_fuzzy using RapidFuzz for a given place_id or name_zh.
    Body: {place_id?: str, name_zh?: str, threshold?: int}
    Returns top matches with improved scores.
    """
    try:
        from rapidfuzz import fuzz
        data = request.get_json(force=True, silent=True) or {}
        place_id = data.get('place_id', '').strip()
        name_zh_q = data.get('name_zh', '').strip()
        threshold = int(data.get('threshold', 50))
        conn = get_db_connection()
        if not name_zh_q and place_id:
            row = conn.execute("SELECT name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
            name_zh_q = row['name_zh'] if row else ''
        if not name_zh_q:
            conn.close()
            return jsonify({"ok": False, "error": "need place_id or name_zh"}), 400
        titles = conn.execute("SELECT id, catalog_id, name_zh, title_zh, title_vi, score FROM cbeta_catalog_place_fuzzy LIMIT 5000").fetchall()
        scored = []
        for t in titles:
            s = fuzz.partial_ratio(name_zh_q, t['title_zh'] or '')
            s2 = fuzz.ratio(name_zh_q, t['name_zh'] or '')
            best = max(s, s2, t['score'] or 0)
            if best >= threshold:
                scored.append({'catalog_id': t['catalog_id'], 'name_zh': t['name_zh'],
                               'title_zh': t['title_zh'], 'title_vi': t['title_vi'],
                               'score_old': t['score'], 'score_new': best})
        scored.sort(key=lambda x: -x['score_new'])
        conn.close()
        return jsonify({"ok": True, "query": name_zh_q, "matches": scored[:20]})
    except Exception as e:
        app.logger.error(f"api_cbeta_fuzzy_rescore error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/cbeta/aggregates')
def api_cbeta_aggregates():
    """GET /daoanh/api/admin/cbeta/aggregates — T51d place mention stats.
    Query params: limit (default 50), min_count (default 1)
    """
    try:
        conn = get_db_connection()
        limit = min(int(request.args.get('limit', 50)), 500)
        min_count = int(request.args.get('min_count', 1))
        rows = conn.execute(
            """SELECT place_id, mention_count, top_texts, vi_name, last_updated
               FROM cbeta_place_mention_stats
               WHERE mention_count >= ?
               ORDER BY mention_count DESC
               LIMIT ?""",
            (min_count, limit)
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM cbeta_place_mention_stats WHERE mention_count >= ?",
            (min_count,)
        ).fetchone()[0]
        conn.close()
        return jsonify({
            "ok": True,
            "total": total,
            "limit": limit,
            "data": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/cbeta/catalog')
def api_cbeta_catalog():
    """GET /daoanh/api/cbeta/catalog — T52c public catalog browser.
    Params: q (search), dynasty, series, page (1-based), limit (default 20, max 100)
    """
    try:
        conn = get_db_connection()
        q = request.args.get('q', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        series = request.args.get('series', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = (page - 1) * limit

        where = []
        params = []
        if q:
            where.append("(title_vi LIKE ? OR title_zh LIKE ?)")
            params += [f'%{q}%', f'%{q}%']
        if dynasty:
            where.append("dynasty_vi = ?")
            params.append(dynasty)
        if series:
            where.append("series = ?")
            params.append(series)

        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
        total = conn.execute(
            f"SELECT COUNT(*) FROM cbeta_catalog_vn {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT sh_number, title_vi, title_zh, juans, dynasty_vi,
                       translator_vi, series, cbeta_ref, q_number, page
                FROM cbeta_catalog_vn {where_sql}
                ORDER BY CAST(sh_number AS INTEGER)
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "data": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/place/<place_id>/cbeta')
def api_place_cbeta_catalog(place_id):
    """
    GET /daoanh/api/admin/place/<place_id>/cbeta
    Returns approved catalog mappings for a place, joined with cbeta_catalog_vn.
    """
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT m.id, m.catalog_id, m.source, m.status, m.note,
                   v.title_vi, v.title_zh, v.dynasty_vi, v.translator_vi,
                   v.q_number, v.page, v.sh_number, v.juans,
                   v.source_name, v.license_name, v.cbeta_ref
            FROM catalog_mapping m
            LEFT JOIN cbeta_catalog_vn v ON m.catalog_id = v.sh_number
            WHERE m.place_id = ? AND m.status = 'approved'
            ORDER BY v.title_vi NULLS LAST
        """, (place_id,)).fetchall()
        conn.close()

        entries = []
        for r in rows:
            d = dict(r)
            # Build a user-friendly code from catalog_vn data if available
            if d.get('sh_number'):
                d['code'] = f"T{int(d['sh_number']):04d}" if d['sh_number'].isdigit() else d['sh_number']
            else:
                d['code'] = d['catalog_id']
            entries.append(d)

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "count": len(entries),
            "cbeta_entries": entries
        })

    except sqlite3.OperationalError as e:
        return jsonify({"ok": True, "place_id": place_id, "count": 0, "cbeta_entries": [],
                        "note": f"Table not available: {e}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/translate_location', methods=['POST'])
def translate_location():
    data = request.get_json()
    raw_text = (data.get('district') or '').strip()
    country_input = (data.get('country') or '').strip()
    if not raw_text and not country_input:
        return jsonify({"success": False, "error": "Thiếu dữ liệu đầu vào"}), 400

    place_id = (data.get('id') or '').strip()
    if not raw_text and place_id:
        conn = get_db_connection()
        note_row = conn.execute(
            "SELECT d.note_category FROM places_pending p LEFT JOIN places_dila d ON p.id = d.id WHERE p.id = ?",
            (place_id,)
        ).fetchone()
        conn.close()
        if note_row and note_row['note_category'] == '廣大之陸上人文地理區域':
            return jsonify({
                "success": True,
                "translated_district": "",
                "translated_country": "",
                "formatted": ""
            })

    print(f'[translate_location] Input: raw_text="{raw_text}", country="{country_input}"', flush=True)
    # First try: rule-based parse (no HVDic)
    parsed = parse_dila_district(raw_text)
    if parsed.get('country_vi') or parsed.get('district_vi'):
        print(f'[translate_location] Rule-based parse OK: {parsed}', flush=True)
        return jsonify({
            "success": True,
            "translated_district": parsed.get('district_vi', ''),
            "translated_country": parsed.get('country_vi', country_input),
            "formatted": parsed.get('formatted', '')
        })
    # Fallback: GoogleTranslator
    print(f'[translate_location] Fallback to GoogleTranslator', flush=True)
    try:
        from deep_translator import GoogleTranslator
        translated_district = ''
        translated_country = ''
        if raw_text:
            try:
                translated_district = GoogleTranslator(source='zh-CN', target='vi').translate(raw_text)
            except Exception:
                translated_district = GoogleTranslator(source='auto', target='vi').translate(raw_text)
        if country_input and country_input != raw_text:
            try:
                translated_country = GoogleTranslator(source='auto', target='vi').translate(country_input)
            except Exception:
                translated_country = country_input
        if not translated_country and country_input:
            translated_country = country_input
        if not translated_district and raw_text:
            translated_district = raw_text
        return jsonify({
            "success": True,
            "translated_district": translated_district,
            "translated_country": translated_country,
            "formatted": (translated_district + ', ' + translated_country).strip(', ')
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/daoanh/api/admin/places/<place_id>/cbdb_translate', methods=['POST'])
def cbdb_place_translate(place_id):
    try:
        digits = ''.join(filter(str.isdigit, place_id))
        full_id = f'PL{digits.zfill(12)}' if digits else place_id
        conn = get_db_connection()
        row = conn.execute(
            "SELECT cbdb_addr_id FROM place_cbdb_map WHERE place_id = ?",
            (full_id,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"success": False, "has_data": False, "error": "no_cbdb_mapping"})
        cconn = get_cbdb_conn()
        cdata = cconn.execute(
            "SELECT c_name_chn, c_admin_type, c_notes FROM ADDR_CODES WHERE c_addr_id = ?",
            (row['cbdb_addr_id'],)
        ).fetchone()
        cconn.close()
        if not cdata:
            return jsonify({"success": False, "has_data": False, "error": "cbdb_record_not_found"})
        text_parts = []
        if cdata['c_name_chn']:
            text_parts.append(f"Tên: {cdata['c_name_chn']}")
        if cdata['c_admin_type']:
            text_parts.append(f"Loại hành chính: {cdata['c_admin_type']}")
        if cdata['c_notes']:
            text_parts.append(f"Ghi chú: {cdata['c_notes']}")
        text = '\n'.join(text_parts)
        prompt = f"Dịch đoạn mô tả địa danh sau từ Hán văn sang tiếng Việt. Giữ nguyên tên riêng và số liệu. Chỉ trả về bản dịch, không thêm giải thích:\n\n{text}"
        meta = {"llm_provider": "", "source": "CBDB"}
        try:
            resp = requests.post('https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
                json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.1, 'max_tokens': 2048},
                timeout=15)
            result = resp.json()
            if result.get('choices'):
                vi_draft = result['choices'][0]['message']['content']
                if vi_draft:
                    meta["llm_provider"] = GROQ_MODEL
                    return jsonify({"success": True, "vi_draft": vi_draft, "source": "CBDB", "meta": meta})
        except Exception:
            pass
        try:
            from deep_translator import GoogleTranslator
            vi_draft = GoogleTranslator(source='zh-CN', target='vi').translate(text)
            if vi_draft:
                meta["llm_provider"] = "google-translate"
                return jsonify({"success": True, "vi_draft": vi_draft, "source": "CBDB", "meta": meta})
        except Exception:
            pass
        meta["llm_provider"] = "fallback"
        return jsonify({"success": True, "vi_draft": text, "source": "CBDB", "meta": meta})
    except Exception as e:
        return jsonify({"error": True, "success": False, "message": str(e)}), 500



# ─── CBETA Routes ────────────────────────────────────────────

@app.route('/daoanh/api/admin/cbeta/search-place', methods=['POST'])
def cbeta_search_place():
    """
    POST /daoanh/api/admin/cbeta/search-place
    Body: {"place_name": "..."}
    Search CBETA texts where the place name appears.
    Returns: list of {sigla, title_zh, juan, page, context_snippet}
    """
    try:
        data = request.get_json(force=True) or {}
        place_name = (data.get('place_name') or data.get('query') or '').strip()
        if not place_name:
            return jsonify({"has_cbeta": False, "results": [], "message": "no_match"}), 200
        limit = min(int(data.get('limit', 50)), 200)
        results = []
        # 1. Annotated place mentions (explicit <placeName> tags)
        conn_lineage = get_db_connection()
        rows = conn_lineage.execute(
            "SELECT cbeta_text_sigla AS sigla, place_name_zh, dila_place_id, juan, page, context_snippet "
            "FROM cbeta_place_mentions WHERE place_name_zh LIKE ? ORDER BY juan LIMIT ?",
            (f'%{place_name}%', limit)
        ).fetchall()
        for r in rows:
            cconn = get_cbeta_conn()
            title_zh_row = cconn.execute(
                "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (r['sigla'],)
            ).fetchone()
            cconn.close()
            results.append({
                "type": "annotated",
                "sigla": r['sigla'],
                "title_zh": title_zh_row['title_zh'] if title_zh_row else '',
                "juan": r['juan'],
                "page": r['page'],
                "context_snippet": r['context_snippet'],
                "dila_id": r['dila_place_id']
            })
        conn_lineage.close()
        # 2. FTS full-text search (implicit mentions)
        if len(results) < limit:
            remaining = limit - len(results)
            try:
                cconn = get_cbeta_conn()
                fts_rows = cconn.execute(
                    "SELECT sigla, title_zh, juan, page, snippet(cbeta_fts, 4, '<mark>', '</mark>', '...', 30) AS ctx "
                    "FROM cbeta_fts WHERE cbeta_fts MATCH ? ORDER BY rank LIMIT ?",
                    (place_name, remaining)
                ).fetchall()
                for r in fts_rows:
                    results.append({
                        "type": "fts",
                        "sigla": r['sigla'],
                        "title_zh": r['title_zh'],
                        "juan": r['juan'],
                        "page": r['page'],
                        "context_snippet": r['ctx'],
                        "dila_id": None
                    })
                cconn.close()
            except Exception as fts_err:
                app.logger.warning(f"CBETA FTS search failed for '{place_name}': {fts_err}")
            # 2b. LIKE fallback for CJK (FTS5 unicode61 doesn't handle multi-char CJK well)
            if len(results) < remaining:
                remaining2 = remaining - len(results)
                try:
                    cconn2 = get_cbeta_conn()
                    like_rows = cconn2.execute(
                        "SELECT t.sigla, t.title_zh, ci.juan, ci.page, "
                        "SUBSTR(ci.content_zh, MAX(1, INSTR(ci.content_zh, ?) - 40), 120) AS ctx "
                        "FROM cbeta_content_index ci JOIN cbeta_texts t ON t.id = ci.text_id "
                        "WHERE ci.content_zh LIKE ? LIMIT ?",
                        (place_name, f'%{place_name}%', remaining2)
                    ).fetchall()
                    for r in like_rows:
                        results.append({
                            "type": "like",
                            "sigla": r['sigla'],
                            "title_zh": r['title_zh'],
                            "juan": r['juan'],
                            "page": r['page'],
                            "context_snippet": r['ctx'],
                            "dila_id": None
                        })
                    cconn2.close()
                except Exception as like_err:
                    app.logger.warning(f"CBETA LIKE search failed for '{place_name}': {like_err}")
        has_cbeta = len(results) > 0
        return jsonify({"has_cbeta": has_cbeta, "results": results, "total": len(results), "message": "found" if has_cbeta else "no_match", "error": False})
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA search-place error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": True, "message": "cbeta_internal_error"}), 500




@app.route('/daoanh/api/admin/cbeta/fuzzy-match-place', methods=['POST'])
def cbeta_fuzzy_match_place():
    """
    POST /daoanh/api/admin/cbeta/fuzzy-match-place
    Body: {"place_name": "...", "place_id": "...", "threshold": 60}
    Fuzzy match a place name against CBETA catalog titles using pre-computed table.
    """
    try:
        data = request.get_json(force=True) or {}
        place_name = (data.get('place_name') or '').strip()
        place_id = (data.get('place_id') or '').strip()
        threshold = int(data.get('threshold', 60))
        limit = min(int(data.get('limit', 20)), 100)

        conn = get_db_connection()

        if place_id:
            rows = conn.execute("""
                SELECT f.place_id, f.name_zh, f.catalog_id, f.title_zh, f.title_vi,
                       f.score, f.rank,
                       v.dynasty_vi, v.translator_vi,
                       v.q_number, v.sh_number, v.juans,
                       v.source_name, v.license_name, v.cbeta_ref
                FROM cbeta_catalog_place_fuzzy f
                JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                WHERE f.place_id = ? AND f.score >= ?
                ORDER BY f.score DESC
                LIMIT ?
            """, (place_id, threshold, limit)).fetchall()
        elif place_name:
            rows = conn.execute("""
                SELECT f.place_id, f.name_zh, f.catalog_id, f.title_zh, f.title_vi,
                       f.score, f.rank,
                       v.dynasty_vi, v.translator_vi,
                       v.q_number, v.sh_number, v.juans,
                       v.source_name, v.license_name, v.cbeta_ref
                FROM cbeta_catalog_place_fuzzy f
                JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                WHERE (f.name_zh = ? OR f.name_zh LIKE ?) AND f.score >= ?
                ORDER BY f.score DESC
                LIMIT ?
            """, (place_name, f'%{place_name}%', threshold, limit)).fetchall()
        else:
            conn.close()
            return jsonify({"ok": False, "error": "Provide place_name or place_id"}), 400

        conn.close()
        return jsonify({
            "ok": True,
            "count": len(rows),
            "results": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500




@app.route('/daoanh/api/admin/cbeta/search-person', methods=['POST'])
def cbeta_search_person():
    """
    POST /daoanh/api/admin/cbeta/search-person
    Body: {"person_name": "..."}
    """
    try:
        data = request.get_json(force=True) or {}
        person_name = (data.get('person_name') or data.get('query') or '').strip()
        if not person_name:
            return jsonify({"has_cbeta": False, "results": [], "message": "no_match"}), 200
        limit = min(int(data.get('limit', 50)), 200)
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT cbeta_text_sigla AS sigla, person_name_zh, dila_person_id, juan, page, context_snippet "
            "FROM cbeta_person_mentions WHERE person_name_zh LIKE ? ORDER BY juan LIMIT ?",
            (f'%{person_name}%', limit)
        ).fetchall()
        results = []
        for r in rows:
            cconn = get_cbeta_conn()
            title_zh_row = cconn.execute(
                "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (r['sigla'],)
            ).fetchone()
            cconn.close()
            results.append({
                "sigla": r['sigla'],
                "title_zh": title_zh_row['title_zh'] if title_zh_row else '',
                "juan": r['juan'],
                "page": r['page'],
                "context_snippet": r['context_snippet'],
                "dila_id": r['dila_person_id']
            })
        conn.close()
        # Fallback: FTS search for person name in text
        if len(results) < limit:
            remaining = limit - len(results)
            try:
                cconn = get_cbeta_conn()
                fts_rows = cconn.execute(
                    "SELECT sigla, title_zh, juan, page, snippet(cbeta_fts, 4, '<mark>', '</mark>', '...', 30) AS ctx "
                    "FROM cbeta_fts WHERE cbeta_fts MATCH ? ORDER BY rank LIMIT ?",
                    (person_name, remaining)
                ).fetchall()
                for r in fts_rows:
                    results.append({
                        "sigla": r['sigla'],
                        "title_zh": r['title_zh'],
                        "juan": r['juan'],
                        "page": r['page'],
                        "context_snippet": r['ctx'],
                        "dila_id": None,
                        "type": "fts"
                    })
                cconn.close()
            except Exception as fts_err:
                app.logger.warning(f"CBETA FTS search failed for '{person_name}': {fts_err}")
            # 2b. LIKE fallback for CJK
            if len(results) < remaining:
                remaining2 = remaining - len(results)
                try:
                    cconn2 = get_cbeta_conn()
                    like_rows = cconn2.execute(
                        "SELECT t.sigla, t.title_zh, ci.juan, ci.page, "
                        "SUBSTR(ci.content_zh, MAX(1, INSTR(ci.content_zh, ?) - 40), 120) AS ctx "
                        "FROM cbeta_content_index ci JOIN cbeta_texts t ON t.id = ci.text_id "
                        "WHERE ci.content_zh LIKE ? LIMIT ?",
                        (person_name, f'%{person_name}%', remaining2)
                    ).fetchall()
                    for r in like_rows:
                        results.append({
                            "sigla": r['sigla'],
                            "title_zh": r['title_zh'],
                            "juan": r['juan'],
                            "page": r['page'],
                            "context_snippet": r['ctx'],
                            "dila_id": None,
                            "type": "like"
                        })
                    cconn2.close()
                except Exception as like_err:
                    app.logger.warning(f"CBETA LIKE search failed for '{person_name}': {like_err}")
        has_cbeta = len(results) > 0
        return jsonify({"has_cbeta": has_cbeta, "results": results, "total": len(results), "message": "found" if has_cbeta else "no_match", "error": False})
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA search-person error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": True, "message": "cbeta_internal_error"}), 500




@app.route('/daoanh/api/admin/cbeta/stats')
def cbeta_stats():
    """GET /daoanh/api/admin/cbeta/stats — DB statistics."""
    try:
        cconn = get_cbeta_conn()
        texts = cconn.execute("SELECT COUNT(*) AS c FROM cbeta_texts").fetchone()['c']
        paras = cconn.execute("SELECT COUNT(*) AS c FROM cbeta_content_index").fetchone()['c']
        fts = cconn.execute("SELECT COUNT(*) AS c FROM cbeta_fts").fetchone()['c']
        import_count = cconn.execute(
            "SELECT COUNT(*) AS c FROM cbeta_import_log WHERE status='success'"
        ).fetchone()['c']
        cconn.close()
        conn = get_db_connection()
        place_m = conn.execute("SELECT COUNT(*) AS c FROM cbeta_place_mentions").fetchone()['c']
        person_m = conn.execute("SELECT COUNT(*) AS c FROM cbeta_person_mentions").fetchone()['c']
        conn.close()
        return jsonify({
            "success": True,
            "texts": texts,
            "paragraphs": paras,
            "fts_entries": fts,
            "files_imported": import_count,
            "place_mentions": place_m,
            "person_mentions": person_m
        })
    except Exception as e:
        return jsonify({"error": True, "success": False, "message": str(e)})




@app.route('/daoanh/api/admin/cbeta/quality-report')
def cbeta_quality_report():
    """GET /daoanh/api/admin/cbeta/quality-report — T50: full CBETA data quality report."""
    try:
        conn = get_db_connection()

        # Fuzzy match quality
        fuzzy_total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy").fetchone()[0]
        fuzzy_low = conn.execute(
            "SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy WHERE low_confidence = 1"
        ).fetchone()[0]
        fuzzy_high = fuzzy_total - fuzzy_low

        # Fuzzy score distribution
        fuzzy_dist = conn.execute("""
            SELECT CAST(score AS INTEGER) as bucket, COUNT(*) as cnt
            FROM cbeta_catalog_place_fuzzy GROUP BY bucket ORDER BY bucket
        """).fetchall()

        # Catalog mapping audit
        cm_total = conn.execute("SELECT COUNT(*) FROM catalog_mapping").fetchone()[0]
        cm_orphaned = conn.execute(
            "SELECT COUNT(*) FROM catalog_mapping WHERE quality_flag = 'orphaned'"
        ).fetchone()[0]
        cm_verified = conn.execute(
            "SELECT COUNT(*) FROM catalog_mapping WHERE quality_flag = 'verified'"
        ).fetchone()[0]

        # Legacy canon mapping
        legacy_count = 0
        try:
            legacy_count = conn.execute("SELECT COUNT(*) FROM legacy_canon_mapping").fetchone()[0]
        except:
            pass

        # Translation status
        ref_passages_total = conn.execute("SELECT COUNT(*) FROM cbeta_ref_passages").fetchone()[0]
        ref_passages_translated = conn.execute(
            "SELECT COUNT(*) FROM cbeta_ref_passages WHERE vi_summary_clean IS NOT NULL AND vi_summary_clean != ''"
        ).fetchone()[0]
        ref_passages_pending = conn.execute(
            "SELECT COUNT(*) FROM cbeta_ref_passages WHERE han_text IS NOT NULL AND han_text != '' "
            "AND (vi_summary_clean IS NULL OR vi_summary_clean = '')"
        ).fetchone()[0]

        # Passage translation
        passage_total = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        passage_vi = conn.execute(
            "SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL AND vi_text != ''"
        ).fetchone()[0]

        # SAT / Toh crossref
        sat_count = conn.execute("SELECT COUNT(*) FROM sat_crossref").fetchone()[0]
        toh_count = conn.execute("SELECT COUNT(*) FROM toh_cbeta_crossref").fetchone()[0]
        catalog_count = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]

        # Place mentions
        pm_total = conn.execute("SELECT COUNT(*) FROM cbeta_place_mentions").fetchone()[0]
        pp_total = conn.execute("SELECT COUNT(*) FROM cbeta_person_mentions").fetchone()[0]

        conn.close()

        return jsonify({
            "ok": True,
            "fuzzy": {
                "total": fuzzy_total,
                "high_confidence_ge80": fuzzy_high,
                "low_confidence_lt80": fuzzy_low,
                "distribution": [{"bucket": int(b), "count": c} for b, c in fuzzy_dist]
            },
            "catalog_mapping": {
                "total": cm_total,
                "valid": cm_verified,
                "orphaned": cm_orphaned
            },
            "legacy_canon": {
                "migrated": legacy_count
            },
            "translations": {
                "ref_passages_total": ref_passages_total,
                "ref_passages_translated": ref_passages_translated,
                "ref_passages_pending": ref_passages_pending,
                "passage_vi_total": passage_vi,
                "passage_total": passage_total
            },
            "crossref": {
                "sat": sat_count,
                "toh": toh_count,
                "catalog_total": catalog_count,
                "sat_coverage_pct": round(sat_count * 100 / catalog_count, 1) if catalog_count else 0
            },
            "mentions": {
                "place_mentions": pm_total,
                "person_mentions": pp_total
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




@app.route('/daoanh/api/admin/cbeta-catalog')
def t181_cbeta_catalog():
    """GET /daoanh/api/admin/cbeta-catalog?series=T&q=&offset=0&limit=50
    Trả danh sách bộ kinh từ cbeta_catalog_vn với trạng thái disk/passage.
    """
    series_f = request.args.get('series', '').strip().upper()
    q = request.args.get('q', '').strip()
    status_f = request.args.get('status', '').strip()  # no_xml|xml_ready|imported|translating|done
    try:
        offset = max(0, int(request.args.get('offset', 0)))
        limit  = min(200, max(1, int(request.args.get('limit', 50))))
    except (ValueError, TypeError):
        offset, limit = 0, 50

    conn = get_db()
    sql_where = []
    params = []
    if series_f:
        sql_where.append("series=?"); params.append(series_f)
    if q:
        sql_where.append("(title_vi LIKE ? OR title_zh LIKE ? OR sigla LIKE ?)")
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    where_clause = ('WHERE ' + ' AND '.join(sql_where)) if sql_where else ''

    # Khi filter theo status: phải tính status cho toàn bộ rows (không LIMIT) rồi mới paginate
    if status_f:
        rows = conn.execute(
            f"""SELECT id, sigla, title_vi, title_zh, juans, dynasty_vi, author_zh,
                       translator_vi, series, sh_number
                FROM cbeta_catalog_vn {where_clause}
                ORDER BY series, CAST(sh_number AS INTEGER)""",
            params
        ).fetchall()
    else:
        total_row = conn.execute(f"SELECT COUNT(*) FROM cbeta_catalog_vn {where_clause}", params).fetchone()
        total = total_row[0] if total_row else 0
        rows = conn.execute(
            f"""SELECT id, sigla, title_vi, title_zh, juans, dynasty_vi, author_zh,
                       translator_vi, series, sh_number
                FROM cbeta_catalog_vn {where_clause}
                ORDER BY series, CAST(sh_number AS INTEGER)
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()

    # Lấy passage counts cho các sigla trong batch này
    siglas_in_batch = [r['sigla'] for r in rows if r['sigla']]
    passage_counts = {}
    translated_counts = {}
    if siglas_in_batch:
        placeholders = ','.join('?' * len(siglas_in_batch))
        pc_rows = conn.execute(
            f"SELECT text_id, COUNT(*) as cnt, SUM(CASE WHEN vi_text IS NOT NULL THEN 1 ELSE 0 END) as tr "
            f"FROM passage WHERE text_id IN ({placeholders}) GROUP BY text_id",
            siglas_in_batch
        ).fetchall()
        for pr in pc_rows:
            passage_counts[pr['text_id']]    = pr['cnt']
            translated_counts[pr['text_id']] = pr['tr'] or 0

    all_items = []
    for r in rows:
        sigla = r['sigla']
        xml_path = _t181_xml_path(sigla) if sigla else None
        xml_exists = xml_path is not None
        p_cnt   = passage_counts.get(sigla, 0)
        tr_cnt  = translated_counts.get(sigla, 0)
        if p_cnt > 0 and tr_cnt >= p_cnt:
            status = 'done'
        elif p_cnt > 0 and tr_cnt > 0:
            status = 'translating'
        elif p_cnt > 0:
            status = 'imported'
        elif xml_exists:
            status = 'xml_ready'
        else:
            status = 'no_xml'
        all_items.append({
            'id': r['id'], 'sigla': sigla, 'title_vi': r['title_vi'],
            'title_zh': r['title_zh'], 'juans': r['juans'], 'dynasty_vi': r['dynasty_vi'],
            'author_zh': r['author_zh'], 'translator_vi': r['translator_vi'],
            'series': r['series'], 'sh_number': r['sh_number'],
            'xml_exists': xml_exists,
            'passage_count': p_cnt, 'translated_count': tr_cnt,
            'translate_pct': round(tr_cnt * 100 / p_cnt, 1) if p_cnt else 0,
            'status': status,
        })

    if status_f:
        # Filter theo status sau khi đã tính xong, rồi paginate
        all_items = [it for it in all_items if it['status'] == status_f]
        total = len(all_items)
        items = all_items[offset:offset + limit]
    else:
        items = all_items

    series_list = [r[0] for r in conn.execute(
        "SELECT DISTINCT series FROM cbeta_catalog_vn ORDER BY series").fetchall()]
    return jsonify({
        "total": total, "offset": offset, "limit": limit,
        "series_list": series_list, "items": items,
        "xml_root_exists": os.path.exists(_T181_XML_ROOT),
    })




@app.route('/daoanh/api/admin/cbeta/import-xml', methods=['POST'])
def t181_import_xml():
    """POST {sigla: "T50n2060"} — lazy import 1 bộ kinh từ XML vào DB rồi enqueue T50.
    Trả {ok, sigla, imported_passages, already_imported, enqueued, message}
    """
    body = request.get_json(force=True) or {}
    sigla = (body.get('sigla') or '').strip()
    if not sigla:
        return jsonify({"ok": False, "error": "missing_sigla"}), 400

    xml_path = _t181_xml_path(sigla)
    if not xml_path:
        # CASE B — XML chưa có: lazy fetch 1 lần từ GitHub raw (T183)
        fetched_path, fetch_reason = _t183_lazy_fetch_xml(sigla)
        if fetch_reason == 'sigla_invalid':
            return jsonify({"ok": False, "error": "invalid_sigla",
                            "message": f"Sigla không hợp lệ: {sigla}"}), 400
        if not fetched_path:
            return jsonify({"ok": False, "error": "fetch_failed",
                            "fetch_reason": fetch_reason,
                            "message": f"Không tải được XML cho {sigla}: {fetch_reason}"}), 503
        xml_path = fetched_path

    # Chạy import trong cùng tiến trình (file nhỏ, 1 lần)
    try:
        import importlib.util, sys as _sys
        spec = importlib.util.spec_from_file_location("import_cbeta", _T181_IMPORT_PY)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run([__import__('pathlib').Path(xml_path)])
    except Exception as e:
        return jsonify({"ok": False, "error": "import_failed", "message": str(e)}), 500

    # Đếm passage đã import
    conn = get_db()
    p_cnt = conn.execute("SELECT COUNT(*) FROM passage WHERE text_id=?", (sigla,)).fetchone()[0]

    # Enqueue T50
    enqueued = False
    if p_cnt > 0:
        st = _t50_read_job()
        queue = st.get('queue') or []
        if sigla not in queue and st.get('sigla') != sigla:
            queue.append(sigla)
            st['queue'] = queue
            if not st.get('running'):
                _t50_start_sigla(sigla, st)
                enqueued = True
            else:
                _t50_write_job(st)
                enqueued = True

    return jsonify({
        "ok": True, "sigla": sigla,
        "passage_count": p_cnt, "enqueued": enqueued,
        "message": f"Import xong: {p_cnt} đoạn văn, T50 {'đã enqueue' if enqueued else 'bỏ qua (đã có)'}",
    })




@app.route('/daoanh/api/admin/cbeta/check-update')
def t181_check_update():
    """GET — kiểm tra có bản kinh mới trong CBETA repo không (git fetch --dry-run).
    Trả {ok, xml_root_exists, new_files, message}
    """
    if not os.path.exists(_T181_XML_ROOT):
        return jsonify({
            "ok": False, "xml_root_exists": False,
            "message": "Chưa có data/cbeta/xml-p5-full/. Sẽ tạo tự động khi import lần đầu (T183 lazy fetch).",
        })
    git_dir = os.path.join(_T181_XML_ROOT, '.git')
    if not os.path.exists(git_dir):
        # Thư mục tồn tại nhưng không phải git repo
        xml_count = sum(1 for _ in __import__('pathlib').Path(_T181_XML_ROOT).rglob('*.xml'))
        return jsonify({
            "ok": True, "xml_root_exists": True, "is_git_repo": False,
            "xml_count": xml_count,
            "message": f"Thư mục xml-p5a có {xml_count} file XML (không phải git repo — không check update được).",
        })
    try:
        import subprocess
        r = subprocess.run(
            ['git', '-C', _T181_XML_ROOT, 'fetch', '--dry-run'],
            capture_output=True, text=True, timeout=30
        )
        has_updates = bool(r.stdout.strip() or r.stderr.strip())
        xml_count = sum(1 for _ in __import__('pathlib').Path(_T181_XML_ROOT).rglob('*.xml'))
        return jsonify({
            "ok": True, "xml_root_exists": True, "is_git_repo": True,
            "xml_count": xml_count, "has_updates": has_updates,
            "message": "Có bản kinh mới, chạy git pull để cập nhật." if has_updates
                       else "Đã cập nhật mới nhất.",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




@app.route('/daoanh/api/admin/cbeta/catalog-stats')
def t181_catalog_stats():
    """GET — tổng quan nhanh cho header trang."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]
    has_sigla = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE sigla IS NOT NULL").fetchone()[0]
    imported = conn.execute("SELECT COUNT(DISTINCT text_id) FROM passage WHERE source='CBETA'").fetchone()[0]
    translated = conn.execute(
        "SELECT COUNT(DISTINCT text_id) FROM passage WHERE source='CBETA' AND vi_text IS NOT NULL").fetchone()[0]
    xml_count = sum(1 for _ in __import__('pathlib').Path(_T181_XML_ROOT).rglob('*.xml')) \
        if os.path.exists(_T181_XML_ROOT) else 0
    return jsonify({
        "total_catalog": total, "has_sigla": has_sigla,
        "xml_on_disk": xml_count, "imported": imported, "translated_any": translated,
        "xml_root_exists": os.path.exists(_T181_XML_ROOT),
    })




@app.route('/daoanh/api/admin/cbeta/snippet')
def cbeta_snippet():
    """
    GET /daoanh/api/admin/cbeta/snippet?id=T50n2060_p0457c16
    Returns the full logical unit (div/story/section) containing the page reference.
    Response: {success, sigla, title, page, unit_title, preview, full_text}
    """
    cbeta_id = request.args.get('id', '').strip()
    if not cbeta_id:
        return jsonify({"success": False, "error": "missing_id", "message": "Missing ?id= parameter"})
    m = re.match(r'^([A-Z])(\d+)n(\d+)_(p?\d+[a-z]\d*)$', cbeta_id)
    if not m:
        return jsonify({"success": False, "error": "invalid_id", "message": f"Invalid CBETA ID format: {cbeta_id}"})
    canon, vol_str, text_num, page_ref = m.group(1), m.group(2), m.group(3), m.group(4)
    sigla = f"{canon}{vol_str}n{text_num}"
    xml_path = os.path.join(DATA_DIR, 'cbeta', 'xml-p5a', canon, f"{canon}{vol_str}", f"{sigla}.xml")
    if not os.path.isfile(xml_path):
        return jsonify({
            "success": False, "error": "not_imported",
            "message": f"CBETA {sigla} chưa được import",
            "sigla": sigla, "cbeta_id": cbeta_id
        })
    try:
        import xml.etree.ElementTree as ET
        NS = 'http://www.tei-c.org/ns/1.0'
        tree = ET.parse(xml_path)
        root = tree.getroot()
        body = root.find(f'.//{{{NS}}}body') or root
        # Build element → parent map
        parent_map = {}
        stack = [(body, None)]
        while stack:
            el, p = stack.pop()
            parent_map[el] = p
            for child in list(el):
                stack.append((child, el))
        # Find matching <pb>
        all_pbs = list(body.iter(f'{{{NS}}}pb'))
        target_pb = None
        stripped_ref = page_ref.lstrip('p')
        for pb in all_pbs:
            n = pb.get('n', '')
            if n == page_ref or n == stripped_ref or n.startswith(stripped_ref):
                target_pb = pb
                break
        if target_pb is None:
            return jsonify({
                "success": False, "error": "page_not_found",
                "message": f"Page {page_ref} not found in {sigla}",
                "sigla": sigla, "cbeta_id": cbeta_id
            })
        # Walk up to find enclosing <div> (TEI or CBETA namespace)
        NS_CB = 'http://www.cbeta.org/ns/1.0'
        unit_div = None
        cur = parent_map.get(target_pb)
        while cur is not None and cur is not body:
            if cur.tag.endswith('}div'):
                unit_div = cur
                break
            cur = parent_map.get(cur)
        # If pb outside any div, find the next div sibling (any namespace)
        if unit_div is None:
            body_children = list(body)
            pb_idx = -1
            for i, c in enumerate(body_children):
                if c is target_pb:
                    pb_idx = i
                    break
            for c in body_children[pb_idx:]:
                if c.tag.endswith('}div'):
                    unit_div = c
                    break
        # Build full text: find all content in this div
        if unit_div is not None:
            unit_heads = unit_div.findall(f'{{{NS}}}head')
            unit_title = ''
            for h in unit_heads:
                ht = ''.join(h.itertext()).strip()
                if ht:
                    unit_title = ht
                    break
            # Extract plain text from all descendant elements
            all_text = []
            for child in list(unit_div):
                t = ''.join(child.itertext()).strip()
                if t:
                    all_text.append(t)
            # Also recursively get deeper text
            full_text = ''.join(unit_div.itertext()).strip()
            preview = full_text[:250] if full_text else ''
        else:
            # Fallback: get surrounding text from body
            unit_title = ''
            all_els = list(body.iter())
            start_el = target_pb
            texts = []
            for ei, el in enumerate(all_els):
                if el is start_el:
                    for j in range(ei + 1, min(ei + 15, len(all_els))):
                        txt = ''.join(all_els[j].itertext()).strip()
                        if txt and len(txt) > 5:
                            texts.append(txt)
                    break
            full_text = '\n'.join(texts)
            preview = full_text[:250] if full_text else ''
        # Get work title from DB
        cconn = get_cbeta_conn()
        title_row = cconn.execute(
            "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (sigla,)
        ).fetchone()
        cconn.close()
        work_title = title_row['title_zh'] if title_row else sigla
        return jsonify({
            "success": True,
            "cbeta_id": cbeta_id,
            "sigla": sigla,
            "title": work_title,
            "page": page_ref,
            "unit_title": unit_title,
            "preview": preview,
            "full_text": full_text,
            "has_full": bool(unit_div is not None)
        })
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA snippet error for {cbeta_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"error": True, "success": False, "message": str(e)})



@app.route('/daoanh/api/admin/cbeta/unit')
def cbeta_unit():
    """
    GET /daoanh/api/admin/cbeta/unit?id=X77n1524_p0484c06
    Returns has_local + full unit text (han_text) for a CBETA citation.
    On-demand loading — no auto-fetch.
    """
    cbeta_id = request.args.get('id', '').strip()
    if not cbeta_id:
        return jsonify({"has_local": False, "id": cbeta_id, "error": "missing_id"})
    m = re.match(r'^([A-Z])(\d+)n(\d+)_(p?\d+[a-z]\d*)$', cbeta_id)
    if not m:
        return jsonify({"has_local": False, "id": cbeta_id, "error": "invalid_id"})
    canon, vol_str, text_num, page_ref = m.group(1), m.group(2), m.group(3), m.group(4)
    sigla = f"{canon}{vol_str}n{text_num}"
    xml_path = os.path.join(DATA_DIR, 'cbeta', 'xml-p5a', canon, f"{canon}{vol_str}", f"{sigla}.xml")
    if not os.path.isfile(xml_path):
        # Fallback: try SQL query on cbeta_texts + cbeta_content_index
        try:
            cconn = get_cbeta_conn()
            text_row = cconn.execute(
                "SELECT id, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?",
                (sigla,)
            ).fetchone()
            if text_row:
                page_key = page_ref.lstrip('p')
                contents = cconn.execute("""
                    SELECT id, juan, page, content_zh
                    FROM cbeta_content_index
                    WHERE text_id = ? AND (page = ? OR page = ?)
                    ORDER BY line_num
                """, (text_row['id'], page_key, page_key.upper())).fetchall()
                if not contents:
                    prefix = page_key[:4]
                    contents = cconn.execute("""
                        SELECT id, juan, page, content_zh
                        FROM cbeta_content_index
                        WHERE text_id = ? AND page LIKE ?
                        ORDER BY page, line_num LIMIT 20
                    """, (text_row['id'], f"{prefix}%")).fetchall()
                cconn.close()
                if contents:
                    han_text = '\n'.join(r['content_zh'] for r in contents)
                    return jsonify({
                        "has_local": True, "id": cbeta_id, "sigla": sigla,
                        "work": text_row['title_zh'], "section": '',
                        "han_text": han_text[:50000],
                        "source": "db"
                    })
            else:
                cconn.close()
        except Exception:
            pass
        return jsonify({"has_local": False, "id": cbeta_id, "sigla": sigla,
                        "message": f"CBETA {sigla} chưa được import"})
    try:
        import xml.etree.ElementTree as ET
        NS = 'http://www.tei-c.org/ns/1.0'
        tree = ET.parse(xml_path)
        root = tree.getroot()
        body = root.find(f'.//{{{NS}}}body') or root
        # Build parent map
        parent_map = {}
        stack = [(body, None)]
        while stack:
            el, p = stack.pop()
            parent_map[el] = p
            for child in list(el):
                stack.append((child, el))
        # Find <pb>
        all_pbs = list(body.iter(f'{{{NS}}}pb'))
        target_pb = None
        stripped_ref = page_ref.lstrip('p')
        for pb in all_pbs:
            n = pb.get('n', '')
            if n == page_ref or n == stripped_ref or n.startswith(stripped_ref):
                target_pb = pb
                break
        if target_pb is None:
            return jsonify({"has_local": False, "id": cbeta_id, "sigla": sigla,
                            "error": "page_not_found", "page": page_ref})
        # Walk up to enclosing <div>
        unit_div = None
        cur = parent_map.get(target_pb)
        while cur is not None and cur is not body:
            if cur.tag.endswith('}div'):
                unit_div = cur
                break
            cur = parent_map.get(cur)
        if unit_div is None:
            body_children = list(body)
            pb_idx = -1
            for i, c in enumerate(body_children):
                if c is target_pb:
                    pb_idx = i
                    break
            for c in body_children[pb_idx:]:
                if c.tag.endswith('}div'):
                    unit_div = c
                    break
        # Extract han_text
        if unit_div is not None:
            unit_heads = unit_div.findall(f'{{{NS}}}head')
            section = ''
            for h in unit_heads:
                ht = ''.join(h.itertext()).strip()
                if ht:
                    section = ht
                    break
            han_text = ''.join(unit_div.itertext()).strip()
        else:
            section = ''
            texts = []
            all_els = list(body.iter())
            for ei, el in enumerate(all_els):
                if el is target_pb:
                    for j in range(ei + 1, min(ei + 15, len(all_els))):
                        txt = ''.join(all_els[j].itertext()).strip()
                        if txt and len(txt) > 5:
                            texts.append(txt)
                    break
            han_text = '\n'.join(texts)
        # Get work title
        cconn = get_cbeta_conn()
        title_row = cconn.execute(
            "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (sigla,)
        ).fetchone()
        cconn.close()
        work = title_row['title_zh'] if title_row else sigla
        return jsonify({
            "has_local": True,
            "id": cbeta_id,
            "sigla": sigla,
            "work": work,
            "section": section,
            "han_text": han_text[:50000] if han_text else ''
        })
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA unit error for {cbeta_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"has_local": False, "id": cbeta_id, "error": "parse_error"})




@app.route('/daoanh/api/admin/cbeta/fulltext')
def cbeta_fulltext():
    """
    GET /daoanh/api/admin/cbeta/fulltext?id=X77n1524_p0400c10
    SQL-based CBETA fulltext lookup from cbeta_texts + cbeta_content_index.
    Falls back to XML-based /cbeta/unit if DB has no matching sigla.
    """
    cbeta_id = request.args.get('id', '').strip()
    if not cbeta_id:
        return jsonify({"success": False, "error": "missing_id"})
    m = re.match(r'^([A-Z])(\d+)n(\d+)_(p?\d+[a-z]\d*)$', cbeta_id)
    if not m:
        return jsonify({"success": False, "error": "invalid_id", "message": f"Invalid format: {cbeta_id}"})
    canon, vol_str, text_num, page_ref = m.group(1), m.group(2), m.group(3), m.group(4)
    sigla = f"{canon}{vol_str}n{text_num}"
    page_key = page_ref.lstrip('p')

    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id, sigla, title_zh, author_zh, translator_zh FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()

        if text_row:
            text_id = text_row['id']
            contents = cconn.execute("""
                SELECT id, juan, page, line_num, content_zh
                FROM cbeta_content_index
                WHERE text_id = ? AND (page = ? OR page = ?)
                ORDER BY line_num
            """, (text_id, page_key, page_key.upper())).fetchall()
            if not contents:
                prefix = page_key[:4]
                contents = cconn.execute("""
                    SELECT id, juan, page, line_num, content_zh
                    FROM cbeta_content_index
                    WHERE text_id = ? AND page LIKE ?
                    ORDER BY page, line_num LIMIT 20
                """, (text_id, f"{prefix}%")).fetchall()
            full_text = '\n'.join(r['content_zh'] for r in contents) if contents else ''
            cconn.close()
            return jsonify({
                "source": "db",
                "citation_id": cbeta_id,
                "sigla": text_row['sigla'],
                "title": text_row['title_zh'],
                "author": text_row['author_zh'],
                "page": page_key,
                "content_blocks": len(contents),
                "full_text": full_text[:50000]
            })
        cconn.close()
        return jsonify({
            "source": "none",
            "citation_id": cbeta_id,
            "sigla": sigla,
            "message": f"CBETA {sigla} chưa được import vào database"
        })
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA fulltext error: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e), "citation_id": cbeta_id})




@app.route('/daoanh/api/admin/cbeta/resolve')
def cbeta_resolve():
    """
    GET /daoanh/api/admin/cbeta/resolve?ref=T50n2060_p0457c16
    Pure Han text resolver from cbeta.db only.
    NEVER joins cbeta_ref_passages or any Vietnamese/translation table.
    Layer 1 of the two-layer architecture:
      Layer 1 (this): resolve_ref → pure Han text
      Layer 2:          translate_ref → LLM translation of han_text
    Returns JSON with ensure_ascii=False (raw UTF-8 Han chars).
    """
    ref = request.args.get('ref', '').strip()
    context = request.args.get('context', '').strip()
    if not ref:
        return jsonify({"ok": False, "error": "missing_ref", "message": "Thiếu ref"}), 400

    parsed = parse_ref(ref)
    if not parsed:
        return jsonify({"ok": False, "error": "invalid_ref", "message": f"Ref không đúng định dạng: {ref}"}), 400

    sigla = parsed['sigla']
    page_comp = parsed['page_comp']
    page_num = parsed['page_num']
    line_num = parsed['line_num']

    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id, sigla, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()

        if not text_row:
            cconn.close()
            return jsonify({
                "ok": False, "success": False, "error": "not_imported",
                "message": f"CBETA {sigla} chưa được import vào cbeta.db",
                "sigla": sigla
            }), 404

        text_id = text_row['id']
        title = text_row['title_zh'] or sigla

        # Exact page+col match (e.g. page='0457c')
        rows = cconn.execute("""
            SELECT juan, page, line_num, content_zh FROM cbeta_content_index
            WHERE text_id = ? AND (page = ? OR page = ?)
            ORDER BY page, rowid LIMIT 20
        """, (text_id, page_comp, page_comp.upper())).fetchall()

        if not rows:
            # Prefix fallback: find any column for this page number
            rows = cconn.execute("""
                SELECT juan, page, line_num, content_zh FROM cbeta_content_index
                WHERE text_id = ? AND page LIKE ?
                ORDER BY page, rowid LIMIT 20
            """, (text_id, f"{page_num}%")).fetchall()

        if not rows and context:
            # Context-aware fallback: search nearby pages for context term
            nearby = cconn.execute("""
                SELECT juan, page, line_num, content_zh FROM cbeta_content_index
                WHERE text_id = ?
                ORDER BY ABS(CAST(page AS INTEGER) - ?)
                LIMIT 200
            """, (text_id, page_num)).fetchall()
            context_rows = [r for r in nearby if r['content_zh'] and context in r['content_zh']]
            if context_rows:
                rows = context_rows[:5]

        cconn.close()

        if not rows:
            return jsonify({
                "ok": False, "success": False, "error": "page_not_found",
                "message": f"Không tìm thấy trang {page_comp} cho {sigla} trong cbeta.db",
                "sigla": sigla, "page": page_comp
            }), 404

        han_text = '\n'.join(r['content_zh'] for r in rows)
        source_page = rows[0]['page']

        return Response(
            json.dumps({
                "ok": True, "success": True,
                "ref": ref,
                "sigla": sigla,
                "title": title,
                "author": text_row['author_zh'] or '',
                "page": source_page,
                "ref_page": page_comp,
                "line_num": line_num,
                "han_text": han_text[:50000],
                "content_blocks": len(rows),
                "source": "cbeta.db"
            }, ensure_ascii=False),
            mimetype='application/json'
        )
    except Exception as e:
        app.logger.error(f"cbeta_resolve error: {e}")
        return jsonify({"ok": False, "success": False, "error": "internal_error", "message": str(e)}), 500




@app.route('/daoanh/api/admin/cbeta/context')
def cbeta_context():
    """
    GET /daoanh/api/admin/cbeta/context?work=T50n2060&query=少林寺&window=2
    Search for query across all pages of a work, return Han-only context windows.
    Each result is one matching segment with N context segments before/after.
    """
    work = request.args.get('work', '').strip()
    query = request.args.get('query', '').strip()
    window = request.args.get('window', 2, type=int)

    if not work or not query:
        return jsonify({"error": "missing_params", "message": "Thiếu work hoặc query"}), 400

    if window < 1:
        window = 1
    if window > 10:
        window = 10

    try:
        cconn = get_cbeta_conn()

        sigla_match = re.match(r'^([A-Z]\d+n\d+)', work)
        sigla = sigla_match.group(1) if sigla_match else work

        text_row = cconn.execute(
            "SELECT id, sigla, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()

        if not text_row:
            cconn.close()
            return jsonify({"error": "work_not_found", "message": f"Không tìm thấy {sigla} trong cbeta.db"}), 404

        rows = cconn.execute(
            "SELECT rowid, juan, page, line_num, content_zh FROM cbeta_content_index WHERE text_id = ? ORDER BY rowid",
            (text_row['id'],)
        ).fetchall()
        cconn.close()

        # Flatten all rows, then split into sentence segments by Chinese punctuation
        all_text = '\n'.join(r['content_zh'] or '' for r in rows)
        segments = re.split(r'[。！？；\n]+', all_text)
        segments = [s.strip() for s in segments if s.strip()]

        def han_only(text):
            if not text:
                return ''
            return ' '.join(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+', text))

        results = []
        for i, seg in enumerate(segments):
            if query not in seg:
                continue
            before = segments[max(0, i - window):i]
            after = segments[i + 1:i + 1 + window]
            results.append({
                "segment_id": f"{sigla}_seg{i:04d}",
                "context_before": [han_only(s) for s in before],
                "match": query,
                "context_after": [han_only(s) for s in after],
            })

        return jsonify({
            "work": work,
            "sigla": sigla,
            "title": text_row['title_zh'],
            "author": text_row['author_zh'] or '',
            "query": query,
            "window": window,
            "matches_found": len(results),
            "results": results[:50]
        })
    except Exception as e:
        app.logger.error(f"cbeta_context error: {e}")
        return jsonify({"error": "internal_error", "message": str(e)}), 500




@app.route('/daoanh/api/admin/cbeta/translate_segment', methods=['POST'])
def cbeta_translate_segment():
    """
    POST /daoanh/api/admin/cbeta/translate_segment
    Body: {"han_text": "…", "segment_id": "T50n2060_seg9098"}
    Splits han_text into sentences, translates each with Google Translate fallback,
    returns bilingual units: [{han, vi}, ...].
    """
    body = request.get_json(silent=True) or {}
    han_text = (body.get('han_text') or '').strip()
    segment_id = (body.get('segment_id') or '').strip()
    if not han_text:
        return jsonify({"error": "missing_han_text"}), 400

    try:
        segments = re.split(r'(?<=[。！？；])', han_text)
        segments = [s.strip() for s in segments if s.strip()]

        units = []
        for i, seg in enumerate(segments):
            vi = ''
            try:
                from deep_translator import GoogleTranslator
                vi = GoogleTranslator(source='zh-CN', target='vi').translate(seg[:2000])
            except Exception:
                vi = ''
            units.append({"han": seg, "vi": vi or ''})

        fallback = len(units) == 0
        if fallback:
            vi = ''
            try:
                from deep_translator import GoogleTranslator
                vi = GoogleTranslator(source='zh-CN', target='vi').translate(han_text[:2000])
            except Exception:
                vi = ''
            units.append({"han": han_text, "vi": vi or ''})

        return jsonify({
            "segment_id": segment_id,
            "units": units,
            "sentence_count": len(units),
            "source": "google-translate"
        })
    except Exception as e:
        app.logger.error(f"cbeta_translate_segment error: {e}")
        return jsonify({"error": "internal_error", "message": str(e)}), 500




@app.route('/daoanh/api/monk/<dila_id>/cbeta-mentions')
def api_monk_cbeta_mentions(dila_id):
    """
    GET /daoanh/api/monk/<dila_id>/cbeta-mentions
    T235 — Kinh Dien Dan Chieu: CBETA Person Citation Panel.
    Tra cuu cac bo kinh CBETA co de cap den mot vi thien su (dila_person_id).
    Aggregates cbeta_person_mentions, left-joins cbeta_catalog_vn.
    Khong filter X77n1524 (evidence/provenance surface, khong phai biography-only).
    Response contract:
      {ok, dila_id, mention_count, text_count, texts: [{sigla, title_vi, title_zh,
        mention_count, juan_count, snippets: [{mention_id, context_snippet, juan, page}]}]}
    T236: mention_id added to snippets for passage reader.
    """
    conn = get_db_connection()
    try:
        # -- Aggregate by text: mention_count + juan_count
        text_rows = conn.execute("""
            SELECT cm.cbeta_text_sigla AS sigla,
                   cv.title_vi,
                   cv.title_zh,
                   COUNT(*)                   AS mention_count,
                   COUNT(DISTINCT cm.juan)    AS juan_count
            FROM cbeta_person_mentions cm
            LEFT JOIN cbeta_catalog_vn cv
                   ON cv.sigla = cm.cbeta_text_sigla
            WHERE cm.dila_person_id = ?
              AND cm.cbeta_text_sigla IS NOT NULL
              AND cm.cbeta_text_sigla != ''
            GROUP BY cm.cbeta_text_sigla
            ORDER BY mention_count DESC, cm.cbeta_text_sigla ASC
        """, (dila_id,)).fetchall()

        if not text_rows:
            return jsonify({
                "ok": True,
                "dila_id": dila_id,
                "mention_count": 0,
                "text_count": 0,
                "texts": []
            })

        total_mentions = sum(r["mention_count"] for r in text_rows)

        # -- Snippets: up to 3 per text, stable source order (rowid ASC)
        # T236: include id (mention_id) for passage reader deep-link
        siglas = [r["sigla"] for r in text_rows]
        placeholders = ",".join("?" * len(siglas))
        snippet_rows = conn.execute(f"""
            SELECT id AS mention_id, cbeta_text_sigla AS sigla,
                   context_snippet, juan, page
            FROM cbeta_person_mentions
            WHERE dila_person_id = ?
              AND cbeta_text_sigla IN ({placeholders})
            ORDER BY cbeta_text_sigla ASC, rowid ASC
        """, [dila_id] + siglas).fetchall()

        # Group snippets by sigla, cap at 3
        from collections import defaultdict
        snippets_by_sigla = defaultdict(list)
        for s in snippet_rows:
            sig = s["sigla"]
            if len(snippets_by_sigla[sig]) < 3:
                snippets_by_sigla[sig].append({
                    "mention_id": s["mention_id"],
                    "context_snippet": s["context_snippet"] or "",
                    "juan": s["juan"] or "",
                    "page": s["page"] or ""
                })

        texts = []
        for r in text_rows:
            sig = r["sigla"]
            texts.append({
                "sigla": sig,
                "title_vi": r["title_vi"] or "",
                "title_zh": r["title_zh"] or "",
                "mention_count": r["mention_count"],
                "juan_count": r["juan_count"],
                "snippets": snippets_by_sigla.get(sig, [])
            })

        return jsonify({
            "ok": True,
            "dila_id": dila_id,
            "mention_count": total_mentions,
            "text_count": len(texts),
            "texts": texts
        })
    except Exception as e:
        app.logger.error(f"api_monk_cbeta_mentions error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/cbeta/person-passage/<int:mention_id>')
def api_cbeta_person_passage(mention_id):
    """
    GET /daoanh/api/cbeta/person-passage/<mention_id>
    T236 — CBETA Passage Reader. Returns full primary-source context for one
    cbeta_person_mentions row (identified by PK mention_id).
    Resolution priority (deterministic, no fuzzy):
      1. cbeta_ref_passages WHERE sigla=pm.sigla AND page=pm.page -> use han_text (richer)
      2. fallback: pm.context_snippet (200 chars, always present when > 0 chars)
    Response contract:
      {ok, mention_id, dila_id, person_name_zh, sigla, title_vi, title_zh,
       juan, page, passage_text, passage_source, ref_code}
    passage_source: 'cbeta_ref_passages' | 'context_snippet' | 'NONE'
    If mention_id not found: HTTP 404 {ok:false, error:'not found'}
    """
    conn = get_db_connection()
    try:
        pm = conn.execute("""
            SELECT pm.id, pm.dila_person_id, pm.person_name_zh, pm.cbeta_text_sigla,
                   pm.juan, pm.page, pm.context_snippet,
                   cv.title_vi, cv.title_zh
            FROM cbeta_person_mentions pm
            LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
            WHERE pm.id = ?
        """, (mention_id,)).fetchone()

        if not pm:
            return jsonify({"ok": False, "error": "mention not found"}), 404

        # Deterministic resolution: exact sigla+page match in cbeta_ref_passages
        passage_text = ""
        passage_source = "NONE"
        ref_code = None
        if pm["page"]:
            rp = conn.execute("""
                SELECT ref_code, han_text FROM cbeta_ref_passages
                WHERE sigla = ? AND page = ? LIMIT 1
            """, (pm["cbeta_text_sigla"], pm["page"])).fetchone()
            if rp and rp["han_text"]:
                passage_text = rp["han_text"]
                passage_source = "cbeta_ref_passages"
                ref_code = rp["ref_code"]

        # Fallback to context_snippet
        if not passage_text and pm["context_snippet"]:
            passage_text = pm["context_snippet"]
            passage_source = "context_snippet"

        return jsonify({
            "ok": True,
            "mention_id": mention_id,
            "dila_id": pm["dila_person_id"] or "",
            "person_name_zh": pm["person_name_zh"] or "",
            "sigla": pm["cbeta_text_sigla"] or "",
            "title_vi": pm["title_vi"] or "",
            "title_zh": pm["title_zh"] or "",
            "juan": pm["juan"] or "",
            "page": pm["page"] or "",
            "passage_text": passage_text,
            "passage_source": passage_source,
            "ref_code": ref_code or ""
        })
    except Exception as e:
        app.logger.error(f"api_cbeta_person_passage error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T237 — CBETA Corpus Search ────────────────────────────────────────────────
@app.route('/daoanh/api/cbeta/corpus-search')
def api_cbeta_corpus_search():
    """GET /daoanh/api/cbeta/corpus-search?q=<query>&limit=30
    T237 — Tìm trong Đại Tạng / CBETA.
    Tìm kiếm substring Hán văn trong cbeta_person_mentions.context_snippet.
    Trả về kết quả với mention_id để mở T236 reader.
    Corpus: 5 bộ kinh đã nhập (~72,628 đoạn văn).
    """
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({
            "ok": False,
            "error": "query_too_short",
            "min_length": 2,
            "message": "Vui lòng nhập ít nhất 2 ký tự để tìm kiếm."
        }), 400

    try:
        limit = min(int(request.args.get('limit', 30)), 50)
    except (ValueError, TypeError):
        limit = 30

    db_path = os.path.join(os.path.dirname(__file__), 'data', 'lineage.db')
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        # Coverage counts — computed from real data
        total_passages = conn.execute(
            "SELECT COUNT(*) FROM cbeta_person_mentions "
            "WHERE context_snippet IS NOT NULL AND context_snippet != ''"
        ).fetchone()[0]
        total_texts = conn.execute(
            "SELECT COUNT(DISTINCT cbeta_text_sigla) FROM cbeta_person_mentions"
        ).fetchone()[0]
        catalog_total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]

        # Parameterized LIKE search — no fuzzy, no LLM, exact substring only
        pattern = '%' + q + '%'
        rows = conn.execute("""
            SELECT pm.id          AS mention_id,
                   pm.cbeta_text_sigla AS sigla,
                   pm.person_name_zh,
                   pm.juan,
                   pm.page,
                   pm.context_snippet  AS snippet,
                   cv.title_vi,
                   cv.title_zh
            FROM   cbeta_person_mentions pm
            LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
            WHERE  pm.context_snippet LIKE ?
            ORDER  BY pm.cbeta_text_sigla ASC, pm.page ASC, pm.id ASC
            LIMIT  ?
        """, (pattern, limit)).fetchall()

        results = [
            {
                "mention_id": r["mention_id"],
                "sigla":      r["sigla"] or "",
                "title_vi":   r["title_vi"] or "",
                "title_zh":   r["title_zh"] or "",
                "juan":       r["juan"] or "",
                "page":       r["page"] or "",
                "snippet":    r["snippet"] or "",
                "reader_ref": r["mention_id"]
            }
            for r in rows
        ]

        return jsonify({
            "ok":           True,
            "query":        q,
            "result_count": len(results),
            "limit":        limit,
            "coverage": {
                "texts_searchable":   total_texts,
                "passages_searchable": total_passages,
                "catalog_total":       catalog_total,
                "scope":               "imported_corpus"
            },
            "results": results
        })
    except Exception as e:
        app.logger.error(f"api_cbeta_corpus_search error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T238 — CBETA Text Browser ─────────────────────────────────────────────────
@app.route('/daoanh/api/cbeta/texts')
def api_cbeta_texts():
    """GET /daoanh/api/cbeta/texts
    T238 — Danh sách bộ kinh có thể đọc được trong corpus đã nhập.
    Trả về 5 siglas hiện có với metadata và số đoạn văn.
    """
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'lineage.db')
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT pm.cbeta_text_sigla                         AS sigla,
                   cv.title_vi,
                   cv.title_zh,
                   COUNT(*)                                    AS total_mentions,
                   COUNT(CASE WHEN pm.page IS NOT NULL AND pm.page != '' THEN 1 END)
                                                               AS mentions_with_page,
                   COUNT(DISTINCT CASE WHEN pm.page IS NOT NULL AND pm.page != '' THEN pm.page END)
                                                               AS unique_pages
            FROM   cbeta_person_mentions pm
            LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
            GROUP  BY pm.cbeta_text_sigla
            ORDER  BY total_mentions DESC
        """).fetchall()

        texts = [
            {
                "sigla":              r["sigla"] or "",
                "title_vi":           r["title_vi"] or "",
                "title_zh":           r["title_zh"] or "",
                "total_mentions":     r["total_mentions"],
                "mentions_with_page": r["mentions_with_page"],
                "unique_pages":       r["unique_pages"],
            }
            for r in rows
        ]
        return jsonify({"ok": True, "count": len(texts), "texts": texts})
    except Exception as e:
        app.logger.error(f"api_cbeta_texts error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/cbeta/text/<sigla>/browse')
def api_cbeta_text_browse(sigla):
    """GET /daoanh/api/cbeta/text/<sigla>/browse?offset=0&limit=20
    T238 — Duyệt bộ kinh theo trang nguồn (page locator).
    CASE D: không có juan; nhóm theo trang nguồn dạng 0196c.
    Trả về unique pages với snippet đại diện (MIN id) + số người được đề cập.
    """
    try:
        offset = max(0, int(request.args.get('offset', 0)))
        limit  = min(100, max(1, int(request.args.get('limit', 20))))
    except (ValueError, TypeError):
        offset, limit = 0, 20

    # Sigla must be exact — no fuzzy
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'lineage.db')
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        # Check sigla exists
        exists = conn.execute(
            "SELECT 1 FROM cbeta_person_mentions WHERE cbeta_text_sigla = ? LIMIT 1",
            (sigla,)
        ).fetchone()
        if not exists:
            return jsonify({"ok": False, "error": "sigla_not_found"}), 404

        # Catalog metadata
        cat = conn.execute(
            "SELECT title_vi, title_zh FROM cbeta_catalog_vn WHERE sigla = ? LIMIT 1",
            (sigla,)
        ).fetchone()
        title_vi = cat["title_vi"] if cat else ""
        title_zh = cat["title_zh"] if cat else ""

        # Coverage counts
        total_mentions = conn.execute(
            "SELECT COUNT(*) FROM cbeta_person_mentions WHERE cbeta_text_sigla = ?",
            (sigla,)
        ).fetchone()[0]
        total_pages = conn.execute(
            "SELECT COUNT(DISTINCT page) FROM cbeta_person_mentions "
            "WHERE cbeta_text_sigla = ? AND page IS NOT NULL AND page != ''",
            (sigla,)
        ).fetchone()[0]

        # Browse: group by page, take MIN(id) as reader_ref, count persons
        # Ordering: page ASC (CBETA page locators like 0196c sort correctly as strings)
        items_rows = conn.execute("""
            SELECT page,
                   MIN(id)         AS reader_ref,
                   COUNT(*)        AS mention_count,
                   MIN(context_snippet) AS snippet
            FROM   cbeta_person_mentions
            WHERE  cbeta_text_sigla = ?
              AND  page IS NOT NULL AND page != ''
            GROUP  BY page
            ORDER  BY page ASC, MIN(id) ASC
            LIMIT  ? OFFSET ?
        """, (sigla, limit, offset)).fetchall()

        items = [
            {
                "page":          r["page"] or "",
                "reader_ref":    r["reader_ref"],
                "mention_count": r["mention_count"],
                "snippet":       r["snippet"] or "",
            }
            for r in items_rows
        ]

        return jsonify({
            "ok":     True,
            "sigla":  sigla,
            "title_vi": title_vi,
            "title_zh": title_zh,
            "coverage": {
                "total_mentions":     total_mentions,
                "unique_pages":       total_pages,
                "granularity":        "context_snippet",
                "complete_text":      False,
                "note":               "Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn."
            },
            "items": items,
            "pagination": {
                "offset":   offset,
                "limit":    limit,
                "total":    total_pages,
                "has_next": (offset + limit) < total_pages,
                "has_prev": offset > 0,
            }
        })
    except Exception as e:
        app.logger.error(f"api_cbeta_text_browse error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()



# ============ TRANSLATION & ADMIN APIS (from main) ============

if True:
    
    # ========== TRANSLATION APIs ==========
    
    @app.route('/api/translate/hvdic', methods=['POST'])
    def translate_hvdic():
        """POST /api/translate/hvdic - Dịch Hán-Việt qua HVDic API"""
        data = request.get_json()
        text = data.get('text', '') if data else request.form.get('text', '')
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        try:
            url = "https://hvdic.thivien.net/transcript-query.json.php"
            payload = f"mode=trans&lang=1&input={urllib.parse.quote(text)}"
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            
            resp = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
            result = resp.json().get('result', [])
            
            hanviet = " ".join([el.get('o', [''])[0] for el in result if el.get('o')])
            
            return jsonify({'text': text, 'hanviet': hanviet or text})
        except Exception as e:
            return jsonify({'error': str(e), 'text': text}), 500

    @app.route('/api/translate/google', methods=['GET'])
    def translate_google():
        """GET /api/translate/google?text= - Dịch via MyMemory (free)"""
        text = request.args.get('text', '')
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        try:
            url = f"https://api.mymemory.translated.net/get?q={text}&langpair=zh-Hans|vi"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            translated = data.get('responseData', {}).get('translatedText', text)
            
            return jsonify({'text': text, 'google': translated})
        except Exception as e:
            return jsonify({'error': str(e), 'text': text}), 500

    @app.route('/daoanh/api/translate/all', methods=['GET'])
    @app.route('/api/translate/all', methods=['GET'])
    def translate_all():
        """GET /api/translate/all?text= - Return all translations"""
        text = request.args.get('text', '')
        name_zh = request.args.get('name_zh', text)
        
        search_text = text or name_zh
        if not search_text:
            return jsonify({'error': 'Missing text'}), 400
        
        result = {'text': search_text, 'hvdic': '', 'google': '', 'final': ''}
        
        # Try HVDic
        try:
            url = "https://hvdic.thivien.net/transcript-query.json.php"
            payload = f"mode=trans&lang=1&input={urllib.parse.quote(search_text)}"
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            resp = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
            hv_result = resp.json().get('result', [])
            result['hvdic'] = " ".join([el.get('o', [''])[0] for el in hv_result if el.get('o')])
        except:
            pass
        
        # Try MyMemory
        try:
            url = f"https://api.mymemory.translated.net/get?q={search_text}&langpair=zh-Hans|vi"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            result['google'] = data.get('responseData', {}).get('translatedText', '')
        except:
            pass
        
        result['final'] = result['hvdic'] or result['google'] or search_text
        
        return jsonify(result)

    def _suggest_name(main_name_han, aka_names_raw='', bio='', refs='', rules_context=''):
        """Generate a Vietnamese name suggestion. Returns string or None.

        T447: nạp quy tắc qua cổng dịch thống nhất (_t73_style_lock — SSOT
        style_constitution.py) thay vì SQL LIMIT 20 3-loại cũ (lỗ hổng đã xác
        nhận trong plan T447). Không gọi translate_han_vi() trực tiếp vì prompt
        khung của cổng (build_style_prompt) được thiết kế cho DỊCH ĐOẠN VĂN
        Hán→Việt ("Dịch đoạn {label} Hán văn... sang tiếng Việt"), không khớp
        tác vụ sinh MỘT tên gợi ý theo chỉ dẫn có cấu trúc — ép qua khung đó có
        rủi ro model dịch luôn phần chỉ dẫn. Dùng CÙNG engine chọn rules
        (_t73_style_lock) + CÙNG bảng cache/versioning (translation_cache,
        rules_version/constitution_hash) để kết quả vẫn được đánh dấu/tra lại
        nhất quán với mọi lệnh dịch khác đi qua cổng — giữ nguyên định dạng trả
        về (string hoặc None) cho caller cũ (admin_namevi_suggest).
        param rules_context giữ lại cho tương thích chữ ký cũ, không còn dùng
        (cổng đã nạp đủ quy tắc active, bao trùm cả 20 rule 3-loại cũ)."""
        if not main_name_han:
            return None

        _gw_conn = None
        lock = None
        try:
            _gw_conn = get_db_connection()
            lock = _t73_style_lock(_gw_conn, source_text=main_name_han + ' ' + (aka_names_raw or ''),
                                   prompt_label='name_suggestion')
        except Exception as e:
            app.logger.warning(f"[T447 _suggest_name] style_lock lỗi, dùng rules rỗng: {e}")
            lock = {'rules': [], 'rules_version': None, 'constitution_hash': None}

        # T447 vòng 2 (QA lỗi 4, không bắt buộc) — _suggest_name GHI cache
        # (source_type='name_suggestion') nhưng trước đây KHÔNG đọc lại, nên luôn
        # cache-miss và gọi AI lại dù đã dịch cùng main_name_han+rules trước đó.
        # Tra cache trước khi build prompt + gọi AI, cùng khóa dual-key như mọi
        # source_type khác đi qua cổng.
        if _gw_conn is not None and lock.get('rules_version'):
            try:
                _cached = _t165_lookup_cache(
                    _gw_conn, _t73_source_hash(main_name_han), lock.get('constitution_hash'),
                    lock.get('rules_version'), 'name_suggestion')
                if _cached and _cached['translated_text']:
                    _cached_name = _cached['translated_text'].strip()
                    if _cached_name and len(_cached_name) <= 100 and '\n' not in _cached_name:
                        _gw_conn.close()
                        return _cached_name
            except Exception as e:
                app.logger.warning(f"[T447 _suggest_name] tra cache lỗi (bỏ qua, gọi AI như cũ): {e}")

        rule_block = "\n".join(
            "[" + r['rule_type'].upper() + "] " + (r.get('rule_text') or '')
            for r in (lock.get('rules') or [])
        )

        prompt_lines = [
            "Bạn là công cụ chuẩn hóa tên tăng sĩ / nhân vật Phật giáo từ chữ Hán sang tên tiếng Việt chuẩn Hán-Việt dùng trong nghiên cứu Phật học Hán tạng.",
            "",
            "YÊU CẦU:",
            "1. Ưu tiên main_name_han để quyết định tên chính.",
            "2. Dùng aka_names_raw để nhận thêm biệt hiệu Hán nếu hữu ích, bỏ qua tiếng Nhật (kana) và Latin/Pinyin.",
            "3. Chỉ phiên âm Hán-Việt, không dịch nghĩa sang tiếng Việt hiện đại.",
            "4. Kết quả là một tên tiếng Việt duy nhất, ngắn gọn.",
            "5. Viết hoa chuẩn (chữ cái đầu mỗi tiếng).",
            "6. Không liệt kê nhiều phương án, không giải thích, không in lại chữ Hán.",
            "7. Output là một dòng duy nhất, chỉ chứa tên tiếng Việt.",
        ]
        if rule_block:
            prompt_lines += [
                "",
                "QUY TẮC HỌC THUẬT BẮT BUỘC (từ hệ thống PTDA — phải tuân thủ tuyệt đối):",
                rule_block,
            ]
        prompt_lines += [
            "",
            "---",
            "DỮ LIỆU:",
            "main_name_han: " + main_name_han,
        ]
        if aka_names_raw:
            prompt_lines.append("aka_names_raw: " + aka_names_raw)
        if bio:
            prompt_lines.append("bio: " + bio[:500])
        if refs:
            prompt_lines.append("refs: " + refs[:200])
        prompt_lines.append("")
        prompt_lines.append("Output:")
        prompt = "\n".join(prompt_lines)
        result, model_id, _err = _t73_call_gemini(
            prompt, source_type='name_suggestion', source_text=main_name_han,
            conn=_gw_conn, constitution_hash=lock.get('constitution_hash'))
        if not result:
            result = _call_gemini(prompt, timeout=15)  # dự phòng khi cổng lỗi hẳn
            model_id = model_id or (GROQ_MODEL if result else None)
        if _gw_conn is not None:
            try:
                if result and lock.get('rules_version'):
                    # Ghi cache cùng bảng/versioning với mọi lệnh dịch khác đi qua cổng
                    # (source_type='name_suggestion', KHÔNG ảnh hưởng hành vi
                    # name_vi_map ở dưới — đây chỉ là audit trail của cổng).
                    _t165_write_cache(
                        _gw_conn, _t73_source_hash(main_name_han), 'name_suggestion',
                        None, main_name_han, result.strip()[:200], model_id,
                        lock.get('rules_version'), status='auto')
                    _gw_conn.commit()
            except Exception as e:
                app.logger.warning(f"[T447 _suggest_name] ghi cache lỗi (không chặn kết quả): {e}")
            finally:
                _gw_conn.close()
        if result:
            result = result.strip()
            if len(result) <= 100 and '\n' not in result:
                return result
        try:
            url = "https://hvdic.thivien.net/transcript-query.json.php"
            payload = "mode=trans&lang=1&input=" + urllib.parse.quote(main_name_han)
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            resp = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
            hv_result = resp.json().get('result', [])
            hv_text = " ".join([el.get('o', [''])[0] for el in hv_result if el.get('o')])
            if hv_text:
                return hv_text.strip().title()
        except Exception:
            pass
        return None

    @app.route('/api/admin/namevi/suggest', methods=['POST'])
    def admin_namevi_suggest():
        """
        POST /api/admin/namevi/suggest
        Body: {"main_name_han": "笑庵了悟", "aka_names_raw": "...", "bio": "...", "refs": "..."}
        Returns: {"vietnamese_name": "Tiếu Am Liễu Ngộ"} or error.
        Uses Gemini 2.0 Flash with a structured Hán-Việt name suggestion prompt.
        """
        body = request.get_json(silent=True) or {}
        main_name_han = (body.get('main_name_han') or '').strip()
        aka_names_raw = (body.get('aka_names_raw') or '').strip()
        bio = (body.get('bio') or '').strip()
        refs = (body.get('refs') or '').strip()
        dila_id = (body.get('dila_id') or '').strip()
        if not main_name_han:
            return jsonify({"success": False, "error": "Thiếu main_name_han"}), 400

        # Tải translation rules hàn lâm đang active để inject vào prompt Gemini
        rules_context = ''
        try:
            _rc = get_db_connection()
            _rows = _rc.execute(
                "SELECT rule_type, description, rule_text FROM translation_rules "
                "WHERE is_active=1 AND status='active' "
                "AND rule_type IN ('forbidden','terminology','style') "
                "ORDER BY priority ASC LIMIT 20"
            ).fetchall()
            _rc.close()
            rules_context = "\n".join(
                "[" + r["rule_type"].upper() + "] " + (r["description"] or r["rule_text"])[:200]
                for r in _rows if r["rule_text"]
            )
        except Exception:
            pass

        result = _suggest_name(main_name_han, aka_names_raw, bio, refs, rules_context=rules_context)
        if not result:
            return jsonify({"success": False, "error": "Không thể sinh tên gợi ý"}), 502

        # Auto-save to name_vi_auto in name_vi_map
        if dila_id:
            try:
                conn2 = sqlite3.connect(SQLITE_DB)
                row = conn2.execute(
                    "SELECT id, name_vi_final FROM name_vi_map WHERE dila_id = ?", (dila_id,)
                ).fetchone()
                now = datetime.now().isoformat()
                if row:
                    conn2.execute(
                        "UPDATE name_vi_map SET name_vi_auto = ? WHERE dila_id = ?",
                        (result, dila_id,)
                    )
                else:
                    conn2.execute(
                        "INSERT INTO name_vi_map (name_vi, name_vi_auto, name_zh, dila_id, source, confidence, created_at) VALUES (?, ?, ?, ?, 'auto_suggest', 0.7, ?)",
                        (result, result, main_name_han, dila_id, now)
                    )
                conn2.commit()
                conn2.close()
            except Exception:
                pass

        return jsonify({
            "success": True, "vietnamese_name": result, "provider": "auto", "dila_id": dila_id
        })

    @app.route('/api/admin/namevi-map/approve', methods=['POST'])
    def admin_namevi_map_approve():
        """
        POST /api/admin/namevi-map/approve
        Body: {"dila_id": "A000001", "name_vi_final": "optional override"}
        Copies name_vi_auto → name_vi_final and sets approved_by/approved_at.
        If name_vi_final is provided, uses that instead of auto.
        """
        data = request.get_json(silent=True) or {}
        dila_id = (data.get('dila_id') or '').strip()
        override = (data.get('name_vi_final') or '').strip()
        if not dila_id:
            return jsonify({"success": False, "error": "Thiếu dila_id"}), 400
        conn = None
        try:
            conn = sqlite3.connect(SQLITE_DB)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT id, name_vi_auto, name_vi_final FROM name_vi_map WHERE dila_id = ?", (dila_id,)).fetchone()
            if not row:
                return jsonify({"success": False, "error": "Không tìm thấy bản ghi"}), 404
            final_val = override or row['name_vi_auto'] or ''
            if not final_val:
                return jsonify({"success": False, "error": "Không có name_vi_auto để duyệt"}), 400
            now = datetime.now().isoformat()
            conn.execute("""
                UPDATE name_vi_map SET name_vi_final = ?, name_vi = ?, approved_by = 'admin', approved_at = ?
                WHERE dila_id = ?
            """, (final_val, final_val, now, dila_id))
            conn.commit()
            return jsonify({"success": True, "dila_id": dila_id, "name_vi_final": final_val})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if conn: conn.close()

    @app.route('/api/admin/namevi/batch-suggest', methods=['POST'])
    def admin_namevi_batch_suggest():
        """
        POST /api/admin/namevi/batch-suggest
        Body: {"limit": 100, "dila_ids": ["A000001", ...]}  (optional limit or specific IDs)
        Generates name_vi_auto for all records in the queue without it.
        Returns count of records processed.
        """
        body = request.get_json(silent=True) or {}
        limit = body.get('limit', 50)
        specific_ids = body.get('dila_ids', None)

        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        try:
            if specific_ids:
                placeholders = ','.join('?' * len(specific_ids))
                rows = conn.execute(f"""
                    SELECT p.id, p.name_zh
                    FROM people p
                    LEFT JOIN name_vi_map n ON p.id = n.dila_id
                    WHERE p.id IN ({placeholders})
                      AND (n.name_vi_auto IS NULL OR n.name_vi_auto = '')
                      AND p.name_zh IS NOT NULL AND p.name_zh != ''
                    LIMIT ?
                """, (*specific_ids, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT p.id, p.name_zh
                    FROM people p
                    LEFT JOIN name_vi_map n ON p.id = n.dila_id
                    WHERE (n.name_vi_auto IS NULL OR n.name_vi_auto = '')
                      AND p.name_zh IS NOT NULL AND p.name_zh != ''
                    LIMIT ?
                """, (limit,)).fetchall()
            conn.close()

            processed = 0
            errors = []
            for r in rows:
                try:
                    result = _suggest_name(r['name_zh'], '')
                    if result:
                        dila_id = r['id']
                        conn2 = sqlite3.connect(SQLITE_DB)
                        existing = conn2.execute(
                            "SELECT id, name_vi_final FROM name_vi_map WHERE dila_id = ?", (dila_id,)
                        ).fetchone()
                        now = datetime.now().isoformat()
                        if existing:
                            conn2.execute(
                                "UPDATE name_vi_map SET name_vi_auto = ? WHERE dila_id = ?",
                                (result, dila_id,)
                            )
                        else:
                            conn2.execute(
                                "INSERT INTO name_vi_map (name_vi, name_vi_auto, name_zh, dila_id, source, confidence, created_at) VALUES (?, ?, ?, ?, 'auto_suggest', 0.7, ?)",
                                (result, result, r['name_zh'], dila_id, now)
                            )
                        conn2.commit()
                        conn2.close()
                        processed += 1
                except Exception as e:
                    errors.append({'dila_id': r['id'], 'error': str(e)})
            return jsonify({
                "success": True, "processed": processed, "total": len(rows), "errors": errors
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


    # Initialize name_vi_map_places table if not exists
    conn = sqlite3.connect(SQLITE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS name_vi_map_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT NOT NULL,
            name_zh TEXT,
            dila_id TEXT UNIQUE,
            confidence REAL DEFAULT 1.0,
            source TEXT DEFAULT 'admin',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    # Check directories
    

    @app.route('/api/admin/sqlite-search', methods=['GET'])
    def admin_sqlite_search():
        """GET /api/admin/sqlite-search?q=<text> - Search across all tables for Chinese text"""
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'error': 'Missing search term'}), 400
        
        conn = get_db()
        results = {}
        
        try:
            # Tables to search (with text columns that might contain Chinese)
            # Note: Exclude 'places_pending' (DILA import data), only search processed/reference tables
            tables_to_search = [
                ('name_vi_map', ['name_zh', 'name_vi', 'bio_snippet']),
                ('name_vi_map_places', ['name_zh', 'name_vi']),
                ('places_vps', ['name_zh', 'name_vi', 'address']),
                # places_dila now has 17 columns - search all relevant text fields
                ('places_dila', ['name_zh', 'name_vi', 'name_en', 'name_san', 'name_jpn', 'name_other', 
                                'district', 'note', 'note_category', 'listbibl', 'location_xml']),
                ('people', ['name_zh', 'name_vi', 'bio']),
                ('entity_monks', ['name_zh', 'name_vi']),
                ('text_mapping', ['name_zh', 'name_vi']),
                # Dictionary/lexicon tables for Chinese-Vietnamese translation
                ('lexicon', ['term', 'normalized', 'definition']),
                ('lexicon_fts', ['term', 'normalized', 'definition']),
            ]
            
            for table, columns in tables_to_search:
                try:
                    # Check if table exists
                    table_exists = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                        (table,)
                    ).fetchone()
                    
                    if not table_exists:
                        continue
                    
                    # Build search query using LIKE for each column
                    conditions = []
                    params = []
                    for col in columns:
                        conditions.append(f"{col} LIKE ?")
                        params.append(f"%{search_term}%")
                    
                    query = f"SELECT * FROM {table} WHERE {' OR '.join(conditions)} LIMIT 10"
                    rows = conn.execute(query, params).fetchall()
                    
                    if rows:
                        results[table] = [dict(r) for r in rows]
                except Exception as e:
                    continue
            
            return jsonify({'search_term': search_term, 'results': results, 'total_tables': len(results)})
        finally:
            conn.close()
    
    @app.route('/api/admin/auto-scan', methods=['GET'])
    def admin_auto_scan():
        """GET /api/admin/auto-scan?limit=10 - Auto scan DILA places, prioritize those with SQLite results"""
        limit = request.args.get('limit', 10, type=int)
        conn = get_db()
        results = []
        
        try:
            # Get DILA places without Vietnamese names
            places = conn.execute(
                "SELECT * FROM places_pending WHERE name_vi IS NULL OR name_vi = '' LIMIT ?", 
                (limit,)
            ).fetchall()
            
            for place in places:
                p = dict(place)
                # Search SQLite for this place's Chinese name
                search_term = p.get('name_zh', '')
                sqlite_results = {}
                total_tables = 0
                
                if search_term:
                    # Search in reference tables
                    tables_to_search = [
                        ('name_vi_map', ['name_zh', 'name_vi', 'bio_snippet']),
                        ('name_vi_map_places', ['name_zh', 'name_vi']),
                        ('places_vps', ['name_zh', 'name_vi', 'address']),
                        # places_dila now has 17 columns - search all relevant text fields
                        ('places_dila', ['name_zh', 'name_vi', 'name_en', 'name_san', 'name_jpn', 'name_other', 
                                        'district', 'note', 'note_category', 'listbibl', 'location_xml']),
                        ('people', ['name_zh', 'name_vi', 'bio']),
                        ('entity_monks', ['name_zh', 'name_vi']),
                        ('text_mapping', ['name_zh', 'name_vi']),
                        # Lexicon dictionary - use correct column names
                        ('lexicon', ['term', 'normalized', 'definition']),
                        ('lexicon_fts', ['term', 'normalized', 'definition']),
                    ]
                    
                    for table, columns in tables_to_search:
                        try:
                            table_exists = conn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                                (table,)
                            ).fetchone()
                            
                            if not table_exists:
                                continue
                            
                            conditions = []
                            params = []
                            for col in columns:
                                conditions.append(f"{col} LIKE ?")
                                params.append(f"%{search_term}%")
                            
                            query = f"SELECT * FROM {table} WHERE {' OR '.join(conditions)} LIMIT 5"
                            rows = conn.execute(query, params).fetchall()
                            
                            if rows:
                                sqlite_results[table] = [dict(r) for r in rows]
                                total_tables += 1
                        except:
                            continue
                
                results.append({
                    'place': p,
                    'sqlite_results': sqlite_results,
                    'total_tables': total_tables,
                    'has_results': total_tables > 0
                })
            
            # Sort: places with SQLite results first (prioritize)
            results.sort(key=lambda x: x['has_results'], reverse=True)
            
            return jsonify({
                'limit': limit,
                'total_scanned': len(results),
                'results': results
            })
        finally:
            conn.close()
    
    @app.route('/api/admin/get-all-data/<place_id>')
    def admin_get_all_data(place_id):
        """GET /api/admin/get-all-data/<place_id> - Get complete data from ALL tables for a place"""
        conn = get_db()
        try:
            result = {'place_id': place_id, 'tables': {}}
            
            # 1. Check places_dila (17 columns with full DILA data)
            # First try exact match
            row = conn.execute("""
                SELECT id, name, name_zh, name_en, name_san, name_jpn, name_peo, name_other,
                       geo_lat, geo_long, place_key, district, note, note_category, listbibl, raw_xml
                FROM places_dila WHERE id = ?
            """, (place_id,)).fetchone()
            
            if not row:
                # Try matching by numeric portion (handle ID format mismatch)
                row = conn.execute("""
                    SELECT id, name, name_zh, name_en, name_san, name_jpn, name_peo, name_other,
                           geo_lat, geo_long, place_key, district, note, note_category, listbibl, raw_xml
                    FROM places_dila 
                    WHERE CAST(SUBSTR(id, 3) AS INTEGER) = CAST(SUBSTR(?, 3) AS INTEGER)
                """, (place_id,)).fetchone()
            
            if row:
                result['tables']['places_dila'] = {
                    'id': row[0],
                    'name': row[1],
                    'name_zh': row[2],
                    'name_en': row[3],
                    'name_san': row[4],
                    'name_jpn': row[5],
                    'name_peo': row[6],
                    'name_other': row[7],
                    'geo_lat': row[8],
                    'geo_long': row[9],
                    'place_key': row[10],
                    'district': row[11],
                    'note': row[12],
                    'note_category': row[13],
                    'listbibl': row[14],
                    'raw_xml': row[15][:1000] + '...' if row[15] and len(row[15]) > 1000 else row[15]  # Truncate raw_xml
                }
            
            # 2. Check places_pending
            row = conn.execute("SELECT * FROM places_pending WHERE id = ?", (place_id,)).fetchone()
            if row:
                result['tables']['places_pending'] = dict(row)
            
            # 3. Check places_vps (if migrated)
            if '_' not in place_id:  # places_vps IDs don't have underscore
                row = conn.execute("SELECT * FROM places_vps WHERE id = ?", (place_id,)).fetchone()
                if row:
                    result['tables']['places_vps'] = dict(row)
            
            # 4. Check name_vi_map_places
            row = conn.execute("SELECT * FROM name_vi_map_places WHERE dila_id = ?", (place_id,)).fetchone()
            if row:
                result['tables']['name_vi_map_places'] = dict(row)
            
            # Summary
            result['total_tables'] = len(result['tables'])
            result['has_data'] = result['total_tables'] > 0
            
            return jsonify(result)
        finally:
            conn.close()
    
    @app.route('/api/admin/migrate-place-types', methods=['POST'])
    def admin_migrate_place_types():
        """POST /api/admin/migrate-place-types - Migrate old place types to new groups"""
        conn = get_db()
        try:
            results = {}
            
            # Migration for places_vps (has place_type column)
            migrations_vps = [
                ("UPDATE places_vps SET place_type = 'Nhóm Cơ sở Tôn giáo' WHERE place_type IN ('Chùa', 'Tự', 'Viện', 'Am', 'Đạo tràng', 'Tịnh xá', 'Thánh địa', 'Giới đàn', 'Hang tu hành')", 'places_vps'),
                ("UPDATE places_vps SET place_type = 'Nhóm Hành chính – Chính trị' WHERE place_type IN ('Tổ đình', 'Kinh đô', 'Phủ', 'Lộ', 'Trấn', 'Thôn', 'Lý', 'Địa khu', 'Vùng rộng không rõ cấp hành chính')", 'places_vps'),
                ("UPDATE places_vps SET place_type = 'Nhóm Địa lý tự nhiên' WHERE place_type IN ('Thắng cảnh', 'Núi', 'Thủy', 'Hang', 'Giang', 'Hà', 'Hồ', 'Trì', 'Hải', 'Đảo', 'Cốc', 'Cao nguyên', 'Sa mạc', 'Lâm')", 'places_vps'),
                ("UPDATE places_vps SET place_type = 'Nhóm Di tích – Kiến trúc' WHERE place_type IN ('Di tích Quốc gia', 'Tháp', 'Cung điện', 'Điện thờ', 'Lăng Mộ', 'Bia ký', 'Phế tích', 'Di chỉ khảo cổ')", 'places_vps'),
            ]
            
            for query, table in migrations_vps:
                try:
                    cursor = conn.execute(query)
                    count = cursor.rowcount
                    conn.commit()
                    results[table] = count
                except Exception as e:
                    results[f"error_{table}"] = str(e)
            
            # Migration for places_pending (has place_type column)
            migrations_pending = [
                ("UPDATE places_pending SET place_type = 'Nhóm Cơ sở Tôn giáo' WHERE place_type IN ('Chùa', 'Tự', 'Viện', 'Am', 'Đạo tràng', 'Tịnh xá', 'Thánh địa', 'Giới đàn', 'Hang tu hành')", 'places_pending'),
                ("UPDATE places_pending SET place_type = 'Nhóm Hành chính – Chính trị' WHERE place_type IN ('Tổ đình', 'Kinh đô', 'Phủ', 'Lộ', 'Trấn', 'Thôn', 'Lý', 'Địa khu', 'Vùng rộng không rõ cấp hành chính')", 'places_pending'),
                ("UPDATE places_pending SET place_type = 'Nhóm Địa lý tự nhiên' WHERE place_type IN ('Thắng cảnh', 'Núi', 'Thủy', 'Hang', 'Giang', 'Hà', 'Hồ', 'Trì', 'Hải', 'Đảo', 'Cốc', 'Cao nguyên', 'Sa mạc', 'Lâm')", 'places_pending'),
                ("UPDATE places_pending SET place_type = 'Nhóm Di tích – Kiến trúc' WHERE place_type IN ('Di tích Quốc gia', 'Tháp', 'Cung điện', 'Điện thờ', 'Lăng Mộ', 'Bia ký', 'Phế tích', 'Di chỉ khảo cổ')", 'places_pending'),
            ]
            
            for query, table in migrations_pending:
                try:
                    cursor = conn.execute(query)
                    count = cursor.rowcount
                    conn.commit()
                    if table in results:
                        results[table] += count
                    else:
                        results[table] = count
                except Exception as e:
                    results[f"error_{table}"] = str(e)
            
            return jsonify({'success': True, 'message': 'Migration completed', 'results': results})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()




@app.route('/daoanh/api/entity/<entity_id>/passages')
def entity_passages(entity_id):
    """GET /daoanh/api/entity/<entity_id>/passages
    Query params: limit (50), offset (0), source (CBETA), mode (linked|like)
    mode=linked: use PASSAGE_ENTITY table (pre-built links, default)
    mode=like: LIKE search on raw_text using entity alias_zh at query time"""
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    source = request.args.get('source', 'CBETA')
    mode = request.args.get('mode', 'linked')

    conn = get_db_connection()
    try:
        if mode == 'like':
            entity = conn.execute(
                "SELECT entity_id, alias_zh, alias_vi FROM entity WHERE entity_id = ?",
                (entity_id,)
            ).fetchone()
            if not entity:
                return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 200

            alias = entity['alias_zh'] or entity['alias_vi']
            if not alias or len(alias) < 2:
                return jsonify({
                    "success": True, "has_data": False, "mode": mode,
                    "entity_id": entity_id, "count": 0, "passages": [],
                    "note": "Entity alias too short for LIKE matching (need >=2 chars)"
                })

            like_pattern = f'%{alias}%'
            total = conn.execute(
                "SELECT COUNT(*) FROM passage WHERE source = ? AND raw_text LIKE ?",
                (source, like_pattern)
            ).fetchone()[0]

            rows = conn.execute(
                "SELECT passage_id, source, text_id, loc_ref, raw_text, norm_text "
                "FROM passage WHERE source = ? AND raw_text LIKE ? "
                "ORDER BY passage_id LIMIT ? OFFSET ?",
                (source, like_pattern, limit, offset)
            ).fetchall()

            return jsonify({
                "success": True, "has_data": total > 0, "mode": mode,
                "entity_id": entity_id, "count": total,
                "alias_zh": alias,
                "passages": [dict(r) for r in rows]
            })
        else:
            total = conn.execute(
                """SELECT COUNT(*) FROM passage_entity pe
                   JOIN passage p ON pe.passage_id = p.passage_id
                   WHERE pe.entity_id = ? AND p.source = ?""",
                (entity_id, source)
            ).fetchone()[0]

            rows = conn.execute(
                """SELECT p.passage_id, p.source, p.text_id, p.loc_ref, p.raw_text, p.norm_text
                   FROM passage_entity pe
                   JOIN passage p ON pe.passage_id = p.passage_id
                   WHERE pe.entity_id = ? AND p.source = ?
                   ORDER BY p.passage_id
                   LIMIT ? OFFSET ?""",
                (entity_id, source, limit, offset)
            ).fetchall()

            return jsonify({
                "success": True, "has_data": total > 0, "mode": mode,
                "entity_id": entity_id, "count": total,
                "passages": [dict(r) for r in rows]
            })
    except sqlite3.OperationalError as e:
        return jsonify({"success": True, "has_data": False, "mode": mode,
                        "entity_id": entity_id, "count": 0, "passages": [],
                        "note": f"Table not available: {e}"})
    finally:
        conn.close()




# T38 — Toh-CBETA Crossref badge
@app.route('/daoanh/api/cbeta/<sigla>/toh')
def api_cbeta_toh(sigla):
    """GET /daoanh/api/cbeta/<sigla>/toh - Tibetan canon (Toh) crossref for a CBETA text."""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT toh, cbeta_sigla, title_zh, title_vi, title_en,
                      url_84000, canon_section, note_vi, confidence
               FROM toh_cbeta_crossref
               WHERE cbeta_sigla = ? AND needs_review = 0
               ORDER BY confidence DESC""",
            (sigla.upper(),)
        ).fetchall()
        conn.close()

        if not rows:
            return jsonify({"ok": True, "sigla": sigla, "toh_refs": [], "total": 0})

        toh_refs = []
        for r in rows:
            toh_refs.append({
                "toh": r[0],
                "cbeta_sigla": r[1],
                "title_zh": r[2],
                "title_vi": r[3],
                "title_en": r[4],
                "url_84000": r[5],
                "canon_section": r[6],
                "note_vi": r[7],
                "confidence": r[8],
                "badge_label": f"Tạng Truyền: Toh {r[0]}",
            })

        return jsonify({
            "ok": True,
            "sigla": sigla,
            "toh_refs": toh_refs,
            "total": len(toh_refs)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})



@app.route('/daoanh/api/cbeta/<sigla>/parallels')
def api_cbeta_parallels(sigla):
    """GET /daoanh/api/cbeta/<sigla>/parallels - DharmaNexus parallel passages link + metadata."""
    import os as _os, json as _json, time as _time
    try:
        sigla_upper = sigla.upper()
        cache_dir = _os.path.join(_os.path.dirname(__file__), 'data', 'cache')
        _os.makedirs(cache_dir, exist_ok=True)
        cache_path = _os.path.join(cache_dir, f'dharmanexus_{sigla_upper}.json')

        # Check 24h cache
        if _os.path.exists(cache_path):
            age = _time.time() - _os.path.getmtime(cache_path)
            if age < 86400:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached = _json.load(f)
                cached['from_cache'] = True
                return jsonify(cached)

        # Resolve DharmaNexus ID
        dn_id = _DN_SIGLA_MAP.get(sigla_upper)

        # If not in static map, try to infer from menudata
        if not dn_id:
            try:
                import requests as _req
                menu_r = _req.get(
                    'https://dharmamitra.org/api-db/menudata/?language=zh',
                    timeout=8, headers={'Accept': 'application/json'}
                )
                if menu_r.status_code == 200:
                    menudata = menu_r.json().get('menudata', [])
                    sigla_num = sigla_upper.lstrip('T')  # '0251'
                    # menudata: [{collection, categories: [{category, texts: [{filename,...}]}]}]
                    for section in menudata:
                        for cat in section.get('categories', []):
                            for text in cat.get('texts', []):
                                fname = text.get('filename', '')
                                if fname.endswith(f'_{sigla_num}'):
                                    dn_id = fname
                                    break
                            if dn_id:
                                break
                        if dn_id:
                            break
            except Exception:
                pass

        if not dn_id:
            result = {
                "ok": True,
                "sigla": sigla_upper,
                "dharmanexus_id": None,
                "dharmanexus_url": None,
                "metadata": None,
                "note": "Text không có trong DharmaNexus database (có thể là Luận/Truyện Trung Hoa thuần túy, không có parallel trong Tạng ngữ/Pali)",
                "total_parallels": 0
            }
            return jsonify(result)

        dn_url = f"https://dharmamitra.org/nexus/db/zh/{dn_id}/text"

        # Fetch metadata from DharmaNexus
        metadata_raw = None
        try:
            import requests as _req
            meta_r = _req.get(
                f'https://dharmamitra.org/api-db/utils/raw-metadata/?filename={dn_id}',
                timeout=8, headers={'Accept': 'application/json'}
            )
            if meta_r.status_code == 200:
                metadata_raw = meta_r.json().get('raw_metadata') or None
                # raw_metadata may itself be a dict if API wraps it
                if isinstance(metadata_raw, dict):
                    metadata_raw = metadata_raw.get('raw_metadata')
        except Exception:
            pass

        result = {
            "ok": True,
            "sigla": sigla_upper,
            "dharmanexus_id": dn_id,
            "dharmanexus_url": dn_url,
            "metadata_md": metadata_raw,
            "badge_label": "Xem trên DharmaNexus",
            "note_vi": "DharmaNexus (dharmamitra.org) phân tích text-reuse xuyên suốt Hán Tạng, Pali, Tây Tạng, Sanskrit. Nhấp để khám phá các đoạn kinh tương đồng.",
            "from_cache": False
        }

        # Save to cache
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                _json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




@app.route('/daoanh/api/cbeta/<sigla>/sat')
def api_cbeta_sat(sigla):
    """GET /daoanh/api/cbeta/<sigla>/sat — SAT Daizōkyō cross-reference link (T35)."""
    try:
        conn = get_db_connection()
        sigla_upper = sigla.strip().upper()
        # Normalize: numeric string → T{n:04d}
        if sigla_upper.isdigit():
            sigla_upper = f"T{int(sigla_upper):04d}"
        row = conn.execute(
            "SELECT cbeta_sigla, sat_url, has_unique FROM sat_crossref WHERE cbeta_sigla = ? LIMIT 1",
            (sigla_upper,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({
                "ok": True, "sigla": sigla, "found": False,
                "note_vi": "Không tìm thấy link SAT cho kinh này (có thể là X-series hoặc sh_number không hợp lệ)",
            })
        return jsonify({
            "ok": True, "sigla": sigla,
            "cbeta_sigla": row['cbeta_sigla'],
            "sat_url": row['sat_url'],
            "has_unique": bool(row['has_unique']),
            "badge_label": "Xem trên SAT Daizōkyō",
            "note_vi": "SAT Daizōkyō Text Database (21dzk.l.u-tokyo.ac.jp) — phiên bản Kanji Unicode chuẩn JIS của Đại Chính Tạng, do Đại học Tokyo duy trì.",
            "found": True,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




@app.route('/daoanh/api/person/<person_id>/translate', methods=['GET', 'POST'])
def api_person_translate(person_id):
    """GET = cache-only (pre-check cho lazy UI), POST = cache + LLM call on miss.
    Check cache → GET trả về nếu có, POST dịch nếu chưa có.
    Body (optional): {} — không cần tham số.
    """
    conn = get_db_connection()
    try:
        p = conn.execute("SELECT id, bio FROM people WHERE id = ?", (person_id,)).fetchone()
        if not p or not p['bio']:
            return jsonify({"ok": False, "error": "Không có tiểu sử DILA cho nhân vật này"}), 404

        bio_zh = p['bio'].strip()
        src_hash = _t73_source_hash(bio_zh)

        # T165: dual-key lookup (constitution_hash → legacy rules_version) + source_type + edited guard
        lock = _t73_style_lock(conn, source_text=bio_zh)
        rv = lock['rules_version']

        existing = _t165_lookup_cache(conn, src_hash, lock.get('constitution_hash'),
                                      rv, 'person_bio')

        if existing:
            bio_vi_cached = existing['translated_text']
            if request.method == 'POST' and bio_vi_cached:
                conn.execute("UPDATE people SET bio_vi=? WHERE id=? AND (bio_vi IS NULL OR bio_vi='')",
                             (bio_vi_cached, person_id))
                conn.commit()
            return jsonify({
                "ok": True, "from_cache": True,
                "translation_id": existing['id'],
                "bio_vi": bio_vi_cached,
                "status": existing['status'],
                "rules_version": existing['rules_version'],
                "current_rules_version": rv,
                # T178 gap 16 — tính thật (nhánh edited / hash lệch / hash NULL), không hardcode
                "rules_outdated": _t165_is_rules_outdated(
                    existing, lock.get('constitution_hash')),
            })

        if request.method == 'GET':
            return jsonify({"ok": True, "from_cache": False, "bio_vi": None})

        # POST: cache miss → call LLM (T123 Style Constitution unified builder)
        prompt = _t73_build_style_prompt(bio_zh, lock, label='tiểu sử')
        bio_vi, model_id, err_type = _t73_call_gemini(
            prompt, source_type='person_bio', source_text=bio_zh, conn=conn,
            constitution_hash=lock.get('constitution_hash'))
        if not bio_vi:
            return jsonify({"ok": False, "error_type": err_type or 'api_error',
                            "error": "Dịch thất bại — thử lại sau"}), 503

        # T166 §6.3 — post_check: LOCKED không render → WARN (draft), sai tên → HARD (blocked)
        t166 = _t166_post_check_translation(
            conn, bio_zh, bio_vi,
            policy=_t166_identity_lock_policy(conn))
        if not t166['ok']:
            return jsonify({
                "ok": False, "error_type": "REVIEW_REQUIRED",
                "error": "T166 Identity Lock chặn bản dịch — tên nhân vật bị biến đổi so với chính pháp.",
                "identity_issues": t166['identity_issues'],
            }), 422

        now = datetime.now().isoformat()
        tid, _replaced = _t165_write_cache(
            conn, src_hash, 'person_bio', person_id, bio_zh, bio_vi, model_id, rv,
            status='auto',
            constitution_hash=lock.get('constitution_hash'),
            selected_rule_codes=lock.get('codes'),
            glossary_hash=lock.get('glossary_hash'),
            identity_status=t166['identity_status'],
            identity_issues=t166['identity_issues'],
            identity_lock_hash=t166['identity_lock_hash'])
        conn.execute("UPDATE people SET bio_vi=? WHERE id=? AND (bio_vi IS NULL OR bio_vi='')",
                     (bio_vi, person_id))
        conn.commit()

        return jsonify({
            "ok": True, "from_cache": False,
            "translation_id": tid,
            "bio_vi": bio_vi,
            "status": "auto",
            "rules_version": rv,
            "rules_outdated": False,
            "model_id": model_id,
            "identity_status": t166['identity_status'],
            "identity_issues": t166['identity_issues'],
        })
    finally:
        conn.close()




@app.route('/daoanh/api/person/<person_id>/dila_translate', methods=['GET', 'POST'])
def api_person_dila_translate(person_id):
    """GET = kiểm tra cache. POST = dịch DILA card sang tiếng Việt Phật học hàn lâm.
    Cache key: translation_cache (source_type='dila_card', entity_id=person_id).
    """
    import json as _j
    # BUG#2 fix: _t148_get_extra chỉ index dữ liệu MỞ RỘNG từ DILA XML (alt_names/
    # listbibl/works/...), KHÔNG phải nguồn của people.bio (bio_zh cơ bản). Trước đây
    # endpoint chặn 404 "Không có dữ liệu DILA XML" chỉ dựa vào `extra` rỗng, dù
    # people.bio đã có nội dung hợp lệ để dịch — cùng root cause với bug Tiểu sử trống
    # (renderer/endpoint coi "không có extra XML" = "không có gì để dịch").
    # Fix: chỉ 404 khi CẢ extra VÀ bio đều rỗng — không có nguồn Hán văn nào để dịch.
    extra = _t148_get_extra(person_id) or {}

    conn = get_db_connection()
    try:
        p = conn.execute("SELECT id, name_zh, bio FROM people WHERE id = ?", (person_id,)).fetchone()
        name_zh = (p['name_zh'] or '') if p else ''
        bio_zh = (p['bio'] or '') if p else ''

        if not extra and not bio_zh:
            return jsonify({"ok": False, "error": "Không có dữ liệu DILA XML"}), 404

        # Tra name_vi từ DB cho tất cả relations — dùng làm NAME LOCK trong prompt
        rel_list = extra.get('relations') or []
        rel_ids = [r['person_id'] for r in rel_list if r.get('person_id')]
        name_vi_map = {}
        if rel_ids:
            rows = conn.execute(
                "SELECT id, name_vi FROM people WHERE id IN ({})".format(','.join('?' * len(rel_ids))),
                rel_ids
            ).fetchall()
            name_vi_map = {row['id']: row['name_vi'] for row in rows if row['name_vi']}
        # person_name_lock: zh_name → {name_vi, person_id}
        # Chỉ inject tên đã pass _ok_hanviet_name() — loại bỏ machine transliteration xấu
        person_name_lock = {}
        for r in rel_list:
            pid = r.get('person_id', '')
            zh = (r.get('name') or '').strip()
            nv = name_vi_map.get(pid, '')
            if pid and zh and nv and _ok_hanviet_name(nv):
                person_name_lock[zh] = {'name_vi': nv, 'person_id': pid}

        source_data = {
            'name_zh': name_zh,
            'alt_names': extra.get('alt_names') or [],
            'occupation': extra.get('occupation') or '',
            'place_of_origin': extra.get('place_of_origin') or '',
            'dynasty_xml': extra.get('dynasty_xml') or '',
            'bio_concise': bio_zh[:2000],
            'bio_extensive': (extra.get('bio_extensive') or '')[:4000],
            'listbibl': (extra.get('listbibl') or [])[:20],
            'works_tripitaka': extra.get('works_tripitaka') or '',
            'works_by': extra.get('works_by') or '',
            'secondary_lit': extra.get('secondary_lit') or '',
            'mentioned_in': extra.get('mentioned_in') or '',
            'active_at': extra.get('active_at') or '',
            'relations': [{'person_id': r['person_id'], 'name': r.get('name', '')}
                          for r in rel_list],
        }
        src_hash = _t73_source_hash(_j.dumps(source_data, ensure_ascii=False, sort_keys=True))

        # T165: lock BEFORE lookup → source_text lọc rules/glossary + resolver merge + hash post-merge (#5a)
        _res_src = ' '.join(filter(None, [
            source_data.get('bio_concise', ''), source_data.get('bio_extensive', ''),
            source_data.get('place_of_origin', ''), source_data.get('active_at', ''),
            source_data.get('dynasty_xml', ''), source_data.get('occupation', ''),
            source_data.get('name_zh', ''),
        ]))
        _name_lock_lines = sorted(
            f"{zh}={v['name_vi']}({v['person_id']})" for zh, v in person_name_lock.items())
        lock = _t73_style_lock(conn, source_text=_res_src, prompt_label='dila_card',
                               extra_hash=_name_lock_lines)

        force_retranslate = (request.method == 'POST' and
                             (request.args.get('force') == '1'
                              or (request.is_json and (request.get_json() or {}).get('force'))))

        existing = _t165_lookup_cache(conn, src_hash, lock.get('constitution_hash'),
                                      lock['rules_version'], 'dila_card')

        if existing and not force_retranslate:
            try:
                vi = _j.loads(existing['translated_text'])
            except Exception:
                vi = {}
            # Filter cached relations_vi: null out bad machine-transliterated names
            for rel in vi.get('relations_vi') or []:
                if rel.get('name_vi') and not _ok_hanviet_name(rel['name_vi']):
                    rel['name_vi'] = None
            # Override with DB-confirmed names (person_name_lock)
            if person_name_lock and vi.get('relations_vi'):
                pid_to_nv = {v['person_id']: v['name_vi'] for v in person_name_lock.values()}
                for rel in vi['relations_vi']:
                    pid = rel.get('person_id', '')
                    if pid and pid_to_nv.get(pid):
                        rel['name_vi'] = pid_to_nv[pid]
            return jsonify({
                "ok": True, "from_cache": True,
                "translation_id": existing['id'],
                "vi": vi, "status": existing['status'],
                # T166 §8.3 — expose identity để UI hiện badge "chưa duyệt" nếu WARN
                "identity_status": _dict_or(existing, 'identity_status'),
                "identity_issues": _json_or_parse(existing, 'identity_issues'),
            })

        if existing and force_retranslate:
            now_ts = datetime.utcnow().isoformat()
            conn.execute(
                "UPDATE translation_cache SET status='invalidated', updated_at=? "
                "WHERE source_hash=? AND source_type='dila_card' AND status != 'invalidated'",
                (now_ts, src_hash)
            )
            conn.commit()

        if request.method == 'GET':
            # Fallback: hash changed (source evolved) → dùng bản dịch mới nhất theo entity_id
            fallback = conn.execute(
                "SELECT id, translated_text FROM translation_cache "
                "WHERE entity_id=? AND source_type='dila_card' AND status NOT IN ('invalidated') "
                "ORDER BY id DESC LIMIT 1",
                (person_id,)
            ).fetchone()
            if fallback:
                try:
                    vi_fb = _j.loads(fallback['translated_text'])
                except Exception:
                    vi_fb = {}
                return jsonify({"ok": True, "from_cache": True, "vi": vi_fb})
            # Last resort: dùng bản invalidated nếu không có bản nào khác
            stale = conn.execute(
                "SELECT id, translated_text FROM translation_cache "
                "WHERE entity_id=? AND source_type='dila_card' AND status='invalidated' "
                "ORDER BY id DESC LIMIT 1",
                (person_id,)
            ).fetchone()
            if stale:
                try:
                    vi_st = _j.loads(stale['translated_text'])
                except Exception:
                    vi_st = {}
                return jsonify({"ok": True, "from_cache": True, "stale": True, "vi": vi_st})
            return jsonify({"ok": True, "from_cache": False, "vi": None})

        # POST: gọi LLM (Qwen/Groq trước vì mạnh hơn về Hán-Việt, fallback Gemini)
        # lock đã build ở trên (source_text + resolver merge + hash post-merge, #5a/#5b)
        prompt = _build_dila_card_prompt(source_data, lock, person_name_lock)
        vi_text = None
        model_id = None
        # Primary: Qwen qua Groq (mạnh hơn về Hán văn và phiên âm Hán-Việt)
        cfg = _llm_config_read()
        groq_key = cfg.get('groq_key') or GROQ_KEY
        groq_model = cfg.get('groq_model') or GROQ_MODEL
        if groq_key:
            try:
                gr = requests.post(GROQ_URL,
                    headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'},
                    json={'model': groq_model, 'messages': [{'role': 'user', 'content': prompt}],
                          'temperature': 0.1, 'max_tokens': 4096},
                    timeout=35)
                gd = gr.json()
                if gd.get('choices'):
                    vi_text = gd['choices'][0]['message']['content'].strip()
                    model_id = groq_model
            except Exception as eg:
                app.logger.warning(f"[dila_translate] Qwen/Groq error: {eg}")

        if not vi_text:
            # Fallback: Gemini
            try:
                GEMINI_KEY = GEMINI_API_KEY
                g_url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                         "gemini-3.6-flash:generateContent?key=" + GEMINI_KEY)
                g_resp = requests.post(g_url, json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.1},
                }, timeout=45)
                g_data = g_resp.json()
                if g_data.get('candidates'):
                    vi_text = g_data['candidates'][0]['content']['parts'][0]['text']
                    model_id = 'gemini-3.6-flash'
            except Exception as e:
                app.logger.warning(f"[dila_translate] Gemini fallback error: {e}")
        if not vi_text:
            return jsonify({"ok": False, "error_type": 'api_error',
                                "error": "Dịch thất bại — thử lại sau"}), 503

        vi_dict = _parse_dila_vi_json(vi_text)
        if not vi_dict:
            return jsonify({"ok": False, "error": "AI không trả về JSON hợp lệ",
                            "raw": vi_text[:500]}), 500

        # Post-edit: fix Hanzi leaked into Vietnamese fields (e.g. Pháp嗣 → Pháp tự)
        _post_edit_hanzi_leakage(vi_dict)

        # Post-process: override relations_vi[].name_vi bằng DB values (không cho AI phịa tên)
        if person_name_lock and vi_dict.get('relations_vi'):
            pid_to_nv = {v['person_id']: v['name_vi'] for v in person_name_lock.values()}
            for rel in vi_dict['relations_vi']:
                pid = rel.get('person_id', '')
                if pid and pid_to_nv.get(pid):
                    rel['name_vi'] = pid_to_nv[pid]

        # Tách suggested_rules ra khỏi dữ liệu dịch trước khi lưu cache
        suggested_raw = vi_dict.pop('suggested_rules', None) or []
        vi_json = _j.dumps(vi_dict, ensure_ascii=False)

        # T166 §6.3 — post_check trên CẢ card (sau override relations bằng DB truth,
        # nên names đã được DB sửa sẽ KHÔNG bị false-block; chỉ flag neu LLM đổi
        # tên chính person/card hoặc name trong bio).
        t166 = _t166_post_check_translation(
            conn, _res_src, vi_json,
            policy=_t166_identity_lock_policy(conn))

        rv = lock['rules_version']
        now = datetime.now().isoformat()
        # T165: write với constitution_hash + selected_rule_codes + glossary_hash (edited guard)
        tid, _replaced = _t165_write_cache(
            conn, src_hash, 'dila_card', person_id,
            _j.dumps(source_data, ensure_ascii=False)[:5000], vi_json, model_id, rv,
            status='auto',
            constitution_hash=lock.get('constitution_hash'),
            selected_rule_codes=lock.get('codes'),
            glossary_hash=lock.get('glossary_hash'),
            identity_status=t166['identity_status'],
            identity_issues=t166['identity_issues'],
            identity_lock_hash=t166['identity_lock_hash'])
        conn.commit()

        # Trả card: gắn identity để UI hiện badge "chưa duyệt" nếu WARN (SPEC §8.3)
        vi_dict['identity_status'] = t166['identity_status']
        vi_dict['identity_issues'] = t166['identity_issues']

        # Lưu rules đề xuất vào DB (status='pending', chờ admin phê chuẩn)
        new_rules = _save_suggested_rules(conn, suggested_raw, person_id, model_id,
                                          resolver=lock.get('resolver'))

        return jsonify({
            "ok": True, "from_cache": False,
            "translation_id": tid,
            "vi": vi_dict, "status": "auto", "model_id": model_id,
            "suggested_rules": new_rules,  # [] nếu không có đề xuất mới
        })
    finally:
        conn.close()




@app.route('/daoanh/api/person/<person_id>/translate/report', methods=['POST'])
def api_person_translate_report(person_id):
    """POST /daoanh/api/person/<person_id>/translate/report
    User báo lỗi bản dịch. Body: {translation_id, note}.
    Nếu report_count >= 3 → status='reported' (admin chú ý).
    """
    body = request.get_json(silent=True) or {}
    tid = body.get('translation_id')
    note = (body.get('note') or '')[:500]
    error_type = (body.get('error_type') or 'style').strip()[:50]
    page_url = (body.get('page_url') or '').strip()[:500]
    if not tid:
        return jsonify({"ok": False, "error": "Thiếu translation_id"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, report_count, status, entity_id, source_type, translated_text "
            "FROM translation_cache WHERE id=?", (tid,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy bản dịch"}), 404
        new_count = row['report_count'] + 1
        new_status = 'reported' if new_count >= 3 else row['status']
        conn.execute(
            "UPDATE translation_cache SET report_count=?, status=?, updated_at=datetime('now') WHERE id=?",
            (new_count, new_status, tid)
        )
        # T123 — ghi chi tiết lỗi cho admin
        conn.execute(
            "INSERT INTO translation_error_report "
            "  (cache_id, source_type, entity_id, translated_text_snapshot, error_type, note, page_url, status) "
            "VALUES (?,?,?,?,?,?,?, 'pending')",
            (tid, row['source_type'] or 'person_bio', row['entity_id'] or person_id,
             (row['translated_text'] or '')[:2000], error_type, note, page_url)
        )
        conn.commit()
        return jsonify({"ok": True, "report_count": new_count, "status": new_status})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-rules')
def api_admin_translation_rules_list():
    """GET /daoanh/api/admin/translation-rules — Danh sách rules + pending rules đề xuất."""
    # T269 B1: route quản lý quy tắc dịch — bắt buộc admin session (cùng mẫu verify_session
    # dùng cho các route /daoanh/api/admin/* khác trong file này).
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    conn = get_db_connection()
    try:
        rules = _t73_get_active_rules(conn)
        # T165: match_scope/match_terms (guard pre-migration)
        _has_ms = any(r[1] == 'match_scope' for r in
                      conn.execute("PRAGMA table_info(translation_rules)").fetchall())
        _cols = ("id, rule_code, rule_type, description, rule_text, is_active, priority, "
                 "status, suggested_by, created_at, updated_at"
                 + (", match_scope, match_terms" if _has_ms else ""))
        all_rules = [dict(r) for r in conn.execute(
            "SELECT " + _cols + " FROM translation_rules ORDER BY updated_at DESC, priority, id"
        ).fetchall()]
        pending_rules = [dict(r) for r in conn.execute(
            "SELECT id, rule_code, rule_type, description, rule_text, suggested_by, created_at "
            "FROM translation_rules WHERE status='pending' ORDER BY id DESC"
        ).fetchall()]
        rv = _t73_rules_version(rules)
        cache_stats = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM translation_cache GROUP BY status"
        ).fetchall()
        return jsonify({
            "ok": True,
            "rules": all_rules,
            "pending_rules": pending_rules,
            "pending_count": len(pending_rules),
            "active_count": len(rules),
            "rules_version": rv,
            "cache_stats": {r['status']: r['cnt'] for r in cache_stats},
        })
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-rules/<int:rule_id>/approve', methods=['POST'])
def api_admin_translation_rule_approve(rule_id):
    """POST — Admin phê chuẩn rule đề xuất (pending→active)."""
    # T269 B1: bắt buộc admin session trước khi đổi status rule.
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()
        n = conn.execute(
            "UPDATE translation_rules SET status='active', is_active=1, updated_at=? "
            "WHERE id=? AND status='pending'",
            (now, rule_id)
        ).rowcount
        conn.commit()
        if not n:
            return jsonify({"ok": False, "error": "Không tìm thấy rule pending"}), 404
        rule = dict(conn.execute(
            "SELECT id, rule_code, rule_type, description, rule_text FROM translation_rules WHERE id=?",
            (rule_id,)
        ).fetchone())
        # T165 #10b: rule active mới → invalidate toàn bộ cache liên quan rule này
        invalidated = _t165_invalidate_cache_for_rule(conn, rule['rule_code'])
        conn.commit()
        return jsonify({"ok": True, "approved": rule,
                        "invalidated_cache_count": invalidated})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-rules/<int:rule_id>/dismiss', methods=['POST'])
def api_admin_translation_rule_dismiss(rule_id):
    """POST — Admin từ chối rule đề xuất (pending→dismissed)."""
    # T269 B1: bắt buộc admin session trước khi đổi status rule.
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()
        n = conn.execute(
            "UPDATE translation_rules SET status='dismissed', updated_at=? "
            "WHERE id=? AND status='pending'",
            (now, rule_id)
        ).rowcount
        conn.commit()
        if not n:
            return jsonify({"ok": False, "error": "Không tìm thấy rule pending"}), 404
        # T165 #10b: rule bị hủy → xoá khỏi cache references nếu đã bị inject trước đó
        rm_row = conn.execute(
            "SELECT rule_code FROM translation_rules WHERE id=?", (rule_id,)).fetchone()
        invalidated = _t165_invalidate_cache_for_rule(
            conn, rm_row['rule_code'] if rm_row else 'DISMISSED-%d' % rule_id)
        conn.commit()
        return jsonify({"ok": True, "dismissed": rule_id,
                        "invalidated_cache_count": invalidated})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-rules', methods=['POST'])
def api_admin_translation_rules_upsert():
    """POST /daoanh/api/admin/translation-rules — Thêm hoặc cập nhật rule.
    Body: {rule_code, rule_type, description, rule_text, priority, is_active}.
    """
    # T269 B1: bắt buộc admin session trước khi thêm/sửa rule.
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    body = request.get_json(silent=True) or {}
    rule_code = (body.get('rule_code') or '').strip().upper()
    if not rule_code or not body.get('rule_text'):
        return jsonify({"ok": False, "error": "Thiếu rule_code hoặc rule_text"}), 400
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()
        rule_text = body['rule_text']
        desc = body.get('description', '')
        # '_keep_' = sentinel từ toggleRule: chỉ đổi is_active, không đổi rule_text/description
        keep_text = (rule_text == '_keep_')
        conn.execute("""
            INSERT INTO translation_rules (rule_code, rule_type, description, rule_text, is_active, priority, status, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,'active','admin',?,?)
            ON CONFLICT(rule_code) DO UPDATE SET
              rule_type=excluded.rule_type,
              description=CASE WHEN ? THEN description ELSE excluded.description END,
              rule_text=CASE WHEN ? THEN rule_text ELSE excluded.rule_text END,
              is_active=excluded.is_active,
              status='active',
              priority=excluded.priority, updated_at=excluded.updated_at
        """, (rule_code, body.get('rule_type', 'style'), desc,
              rule_text, int(body.get('is_active', 1)),
              int(body.get('priority', 100)), now, now,
              keep_text, keep_text))
        # T165 #10b: chỉ invalidate khi rule_text thực sự đổi (không phải toggle _keep_)
        invalidated = 0
        if not keep_text:
            invalidated = _t165_invalidate_cache_for_rule(conn, rule_code)
        # T165 #10: tự backfill match_scope/match_terms khi rule_text đổi
        if _t165_extract_match_terms and not keep_text:
            _r_type = body.get('rule_type', 'style')
            _req_scope = (body.get('match_scope') or 'auto').strip()
            if _r_type == 'terminology' and _req_scope not in ('always',):
                _terms = _t165_extract_match_terms(rule_text) or []
                _ms = 'terms' if _terms else 'always'
                _mtd = _j.dumps(_terms, ensure_ascii=False) if _terms else None
            else:
                _ms, _mtd = 'always', None
            try:
                conn.execute(
                    "UPDATE translation_rules SET match_scope=?, match_terms=? "
                    "WHERE rule_code=?",
                    (_ms, _mtd, rule_code))
            except Exception as _e:
                app.logger.warning(f"[T165] backfill match_scope lỗi (chưa migrate?): {_e}")
        conn.commit()
        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)
        return jsonify({"ok": True, "rule_code": rule_code, "new_rules_version": rv,
                        "invalidated_cache_count": invalidated})
    finally:
        conn.close()




# ============================================================
#  T74 — Tạm Dịch Place Note (mở rộng T73 cho địa danh DILA)
#  Cùng kiến trúc lazy-cache, source_type='place_note'
# ============================================================

@app.route('/daoanh/api/place/<dila_id>/translate', methods=['GET', 'POST'])
def api_place_translate(dila_id):
    """GET/POST /daoanh/api/place/<dila_id>/translate
    GET  → trả về bản dịch từ cache nếu có (không dịch mới).
    POST → check cache → dịch Gemini nếu MISS → auto-save → trả về.
    """
    conn = get_db_connection()
    try:
        place = conn.execute(
            "SELECT id, note FROM places_dila WHERE id = ?", (dila_id,)
        ).fetchone()
        if not place or not (place['note'] or '').strip():
            # Fallback: try by dila_id field
            place = conn.execute(
                "SELECT id, note FROM places_dila WHERE id = ? OR id LIKE ?",
                (dila_id, f"%{dila_id}%")
            ).fetchone()
        if not place or not (place['note'] or '').strip():
            # Fallback: short ID (PL056722) → look up GPS from places → match places_dila by GPS
            gps_row = conn.execute(
                "SELECT gps_lat, gps_long FROM places WHERE id = ?", (dila_id,)
            ).fetchone()
            if gps_row and gps_row['gps_lat']:
                place = conn.execute(
                    "SELECT id, note FROM places_dila"
                    " WHERE ABS(geo_lat - ?) < 0.001 AND ABS(geo_long - ?) < 0.001"
                    " AND note IS NOT NULL AND note != '' LIMIT 1",
                    (gps_row['gps_lat'], gps_row['gps_long'])
                ).fetchone()
        if not place or not (place['note'] or '').strip():
            return jsonify({"ok": False, "error": "Không có mô tả DILA cho địa danh này"}), 404

        note_zh = place['note'].strip()
        src_hash = _t73_source_hash(note_zh)
        # T165: lock trước → source_text lọc rules/glossary + resolver + hash post-merge (#5a)
        lock = _t73_style_lock(conn, source_text=note_zh)
        rv = lock['rules_version']

        # GET → chỉ trả cache, không dịch (T165 dual-key lookup)
        if request.method == 'GET':
            cached = _t165_lookup_cache(conn, src_hash, lock.get('constitution_hash'),
                                        rv, 'place_note')
            if cached:
                return jsonify({
                    "ok": True, "from_cache": True,
                    "translation_id": cached['id'],
                    "note_vi": cached['translated_text'],
                    "status": cached['status'],
                    "rules_version": cached['rules_version'],
                    # T178 gap 16 — tính thật thay vì so rules_version cũ
                    "rules_outdated": _t165_is_rules_outdated(
                        cached, lock.get('constitution_hash')),
                    "identity_status": _dict_or(cached, 'identity_status'),
                    "identity_issues": _json_or_parse(cached, 'identity_issues'),
                })
            return jsonify({"ok": True, "from_cache": False, "note_vi": None})

        # POST → dịch nếu chưa có (T165 dual-key lookup)
        existing = _t165_lookup_cache(conn, src_hash, lock.get('constitution_hash'),
                                      rv, 'place_note')
        if existing:
            return jsonify({
                "ok": True, "from_cache": True,
                "translation_id": existing['id'],
                "note_vi": existing['translated_text'],
                "status": existing['status'],
                "rules_version": existing['rules_version'],
                # T178 gap 16 — tính thật thay vì so rules_version cũ
                "rules_outdated": _t165_is_rules_outdated(
                    existing, lock.get('constitution_hash')),
                "identity_status": _dict_or(existing, 'identity_status'),
                "identity_issues": _json_or_parse(existing, 'identity_issues'),
            })

        # T165-P8.3: pilot gate — OFF by default; requires gate=True + X-T165-P8-Pilot:1
        _p8_active = _p8_pilot_active(request)
        _p8_key_map = {}
        _p8_entity_evidence = None
        _p8_alignment_method = None
        _p8_assertion_status = None
        _p8_types_covered = None

        prompt = _t73_build_style_prompt(note_zh, lock, label='mô tả địa danh')

        if _p8_active:
            _identity_lock = lock.get('t166_identity_lock') or []
            _p8_key_map = _p8_build_entity_key_map(_identity_lock)
            _entity_instr = _p8_build_entity_prompt_instruction(_p8_key_map)
            if _entity_instr:
                prompt = prompt + '\n\n' + _entity_instr
            _p8_alignment_method = 'xml'

        note_vi_raw, model_id, err_type = _t73_call_gemini(
            prompt, source_type='place_note', source_text=note_zh, conn=conn,
            constitution_hash=lock.get('constitution_hash'))
        if not note_vi_raw:
            return jsonify({"ok": False, "error_type": err_type or 'api_error',
                            "error": "Dịch thất bại — thử lại sau"}), 503

        note_vi = note_vi_raw  # default: raw LLM output

        if _p8_active and _p8_key_map:
            # Parse entity XML markers from LLM output
            note_vi, assertions = _p8_parse_entity_xml(note_vi_raw, _p8_key_map)
            _identity_lock = lock.get('t166_identity_lock') or []
            assertion_results = _p8_check_entity_assertions(
                assertions, _p8_key_map, _identity_lock)
            _p8_assertion_status = _p8_compute_assertion_status(assertion_results)
            _p8_entity_evidence = [
                {'key': a.key, 'surface': a.target_surface,
                 'assertion_status': a.assertion_status, 'entity_type': a.entity_type}
                for a in assertions
            ]
            _p8_types_covered = list({a.entity_type for a in assertions if a.entity_type})
        elif _p8_active:
            # Gate active but no LOCKED entities to align
            _p8_assertion_status = 'all_pass'

        # T166 §6.3 — post_check: 少林寺 loại 1-char chỉ WARN; tên địa danh ngắn jTX
        t166 = _t166_post_check_translation(
            conn, note_zh, note_vi,
            policy=_t166_identity_lock_policy(conn))

        now = datetime.now().isoformat()
        tid, _replaced = _t165_write_cache(
            conn, src_hash, 'place_note', dila_id, note_zh, note_vi, model_id, rv,
            status='auto',
            constitution_hash=lock.get('constitution_hash'),
            selected_rule_codes=lock.get('codes'),
            glossary_hash=lock.get('glossary_hash'),
            identity_status=t166['identity_status'],
            identity_issues=t166['identity_issues'],
            identity_lock_hash=t166['identity_lock_hash'],
            entity_evidence=_p8_entity_evidence,
            alignment_method=_p8_alignment_method,
            entity_assertion_status=_p8_assertion_status,
            entity_types_covered=_p8_types_covered)
        conn.commit()
        return jsonify({
            "ok": True, "from_cache": False,
            "translation_id": tid,
            "note_vi": note_vi, "status": "auto",
            "rules_version": rv, "model_id": model_id,
            "p8_assertion_status": _p8_assertion_status,
        })
    finally:
        conn.close()




@app.route('/daoanh/api/place/<dila_id>/translate/report', methods=['POST'])
def api_place_translate_report(dila_id):
    """POST /daoanh/api/place/<dila_id>/translate/report — user báo lỗi bản dịch địa danh."""
    body = request.get_json(silent=True) or {}
    tid = body.get('translation_id')
    note = (body.get('note') or '')[:500]
    error_type = (body.get('error_type') or 'style').strip()[:50]
    page_url = (body.get('page_url') or '').strip()[:500]
    if not tid:
        return jsonify({"ok": False, "error": "Thiếu translation_id"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, report_count, status, entity_id, translated_text "
            "FROM translation_cache WHERE id=? AND source_type='place_note'",
            (tid,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy bản dịch"}), 404
        new_count = row['report_count'] + 1
        new_status = 'reported' if new_count >= 3 else row['status']
        conn.execute(
            "UPDATE translation_cache SET report_count=?, status=?, updated_at=datetime('now') WHERE id=?",
            (new_count, new_status, tid)
        )
        # T123 — ghi chi tiết lỗi cho admin
        conn.execute(
            "INSERT INTO translation_error_report "
            "  (cache_id, source_type, entity_id, translated_text_snapshot, error_type, note, page_url, status) "
            "VALUES (?,?,?,?,?,?,?, 'pending')",
            (tid, 'place_note', row['entity_id'] or dila_id,
             (row['translated_text'] or '')[:2000], error_type, note, page_url)
        )
        conn.commit()
        return jsonify({"ok": True, "report_count": new_count, "status": new_status})
    finally:
        conn.close()




@app.route('/daoanh/api/passage/<passage_id>/translate', methods=['GET', 'POST'])
def api_passage_translate(passage_id):
    """GET = cache-only, POST = cache + Groq call on miss (T85).
    Passage có text_passages (schema T94/T95) → dịch qua translation_segments (SSOT).
    Passage chưa có text_passages → dịch TOÀN PHẦN passage bằng Groq (legacy, vi_text)."""
    conn = get_db_connection()
    try:
        p = conn.execute(
            "SELECT passage_id, raw_text FROM passage WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "Không tìm thấy passage"}), 404
        raw_text = (p['raw_text'] or '').strip()
        if not raw_text:
            return jsonify({"ok": False, "error": "Passage không có raw_text"}), 404
        units = _t85_units(conn, passage_id)
        if units is not None:
            if request.method == 'GET':
                return _t85_get_segments(conn, units)
            body = request.get_json(silent=True) or {}
            return _t85_post_segments(conn, passage_id, units, bool(body.get('force')))
        # --- Legacy fallback: passage chưa có text_passages (vd T51n2076) ---
        # Dịch TOÀN PHẦN passage bằng Groq (giữ hành vi endpoint cũ /daoanh/api/passage/<int>/translate)
        # + cache bằng passage.vi_text. force=True → bỏ qua cached, dịch lại.
        cfg = _llm_config_read()
        key = cfg.get('groq_key') or GROQ_KEY
        model = cfg.get('groq_model') or GROQ_MODEL
        body = request.get_json(silent=True) or {}
        force = bool(body.get('force'))
        cached_vt = None
        if not force:
            c = conn.execute(
                "SELECT vi_text FROM passage WHERE passage_id = ? AND vi_text IS NOT NULL AND vi_text != ''",
                (passage_id,)
            ).fetchone()
            if c:
                cached_vt = c['vi_text']
        if request.method == 'GET':
            return jsonify({
                "ok": True, "mode": "legacy", "from_cache": bool(cached_vt),
                "vi_text": cached_vt, "translation_id": None,
                "status": "cached" if cached_vt else "missing",
            })
        if cached_vt:
            return jsonify({
                "ok": True, "mode": "legacy", "from_cache": True,
                "vi_text": cached_vt, "translation_id": None, "status": "cached",
            })
        if not key:
            return jsonify({'ok': False, 'error': 'GROQ_API_KEY chưa cấu hình'}), 503
        preview = raw_text[:4000]
        try:
            # T123 — Style Constitution unified builder (thay system tĩnh _BUDDHIST_SYSTEM_PROMPT)
            prompt = _t73_build_style_prompt(preview, _t73_style_lock(conn, source_text=preview),
                                             label='passage')
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                json={'model': model,
                      'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.1, 'max_tokens': 2048},
                timeout=30
            )
            result = resp.json()
        except Exception as e:
            return jsonify({"ok": False, "error": f"Groq error: {str(e)}"}), 500
        if not result.get('choices'):
            return jsonify({'ok': False, 'error': f'Groq API lỗi: {result.get("error", {}).get("message", "unknown")}'}), 500
        vi_text = result['choices'][0]['message']['content'].strip()
        if not vi_text:
            return jsonify({"ok": False, "error": "Dịch thất bại — kết quả rỗng"}), 500
        conn.execute(
            "UPDATE passage SET vi_text = ?, translation_draft = 1 WHERE passage_id = ?",
            (vi_text, passage_id)
        )
        conn.commit()
        return jsonify({
            "ok": True, "mode": "legacy", "from_cache": False,
            "vi_text": vi_text, "translation_id": None, "status": "draft",
        })
    finally:
        conn.close()




@app.route('/daoanh/api/passage/<passage_id>/translate/report', methods=['POST'])
def api_passage_translate_report(passage_id):
    """POST /daoanh/api/passage/<passage_id>/translate/report
    User báo lỗi bản dịch nháp của một passage. Tăng report_count trong translation_cache
    (source_type='passage'), đạt ≥3 → status='reported' để admin thấy trong Dashboard
    (admin/translation_cache.html filter source_type=passage)."""
    body = request.get_json(silent=True) or {}
    note = (body.get('note') or '').strip()[:500]
    error_type = (body.get('error_type') or 'style').strip()[:50]
    page_url = (body.get('page_url') or '').strip()[:500]
    conn = get_db_connection()
    try:
        # Ưu tiên: cache đã có cho passage này (theo source_hash của raw_text)
        p = conn.execute(
            "SELECT passage_id, raw_text, vi_text FROM passage WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "Không tìm thấy passage"}), 404
        src_hash = _t73_source_hash(p['raw_text'] or '')
        row = conn.execute(
            "SELECT id, report_count, status, translated_text FROM translation_cache "
            "WHERE source_hash=? AND source_type='passage' ORDER BY id DESC LIMIT 1",
            (src_hash,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Chưa có bản dịch cache cho passage này"}), 404
        new_count = row['report_count'] + 1
        new_status = 'reported' if new_count >= 3 else row['status']
        conn.execute(
            "UPDATE translation_cache SET report_count=?, status=?, updated_at=datetime('now') WHERE id=?",
            (new_count, new_status, row['id'])
        )
        # T123 — ghi chi tiết lỗi (snapshot + link + note) cho admin
        conn.execute(
            "INSERT INTO translation_error_report "
            "  (cache_id, source_type, entity_id, translated_text_snapshot, error_type, note, page_url, status) "
            "VALUES (?,?,?,?,?,?,?, 'pending')",
            (row['id'], 'passage', passage_id,
             (row['translated_text'] or p['vi_text'] or '')[:2000],
             error_type, note, page_url)
        )
        conn.commit()
        return jsonify({"ok": True, "report_count": new_count, "status": new_status})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-cache', methods=['GET'])
def api_admin_translation_cache_list():
    """GET /daoanh/api/admin/translation-cache — danh sách bản dịch, hỗ trợ filter/pagination."""
    status = request.args.get('status', '')
    source_type = request.args.get('source_type', '')
    entity_id = request.args.get('entity_id', '')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    conn = get_db_connection()
    try:
        conds, params = [], []
        if status:
            conds.append("status = ?"); params.append(status)
        if source_type:
            conds.append("source_type = ?"); params.append(source_type)
        if entity_id:
            conds.append("entity_id LIKE ?"); params.append(f"%{entity_id}%")
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        total = conn.execute(f"SELECT COUNT(*) FROM translation_cache {where}", params).fetchone()[0]
        # T447 (fix): schema T165 (constitution_hash/selected_rule_codes/glossary_hash) có thể
        # CHƯA migrate trên DB này (PRAGMA table_info xác nhận thiếu trên data/lineage.db hiện
        # tại khi audit T447) — SELECT literal cột đó trước đây làm toàn endpoint 500
        # (sqlite3.OperationalError: no such column). Chọn cột động theo _t166_has_col, giữ
        # nguyên output shape cho FE cũ (cột thiếu → giá trị None, không có trong dict nếu
        # client không cần — FE chỉ đọc qua `row.constitution_hash` optional).
        _extra_cols = [c for c in ('constitution_hash', 'selected_rule_codes', 'glossary_hash')
                      if _t166_has_col(conn, 'translation_cache', c)]
        _select_cols = ("id, entity_id, source_type, translated_text, model_id, "
                       "rules_version, status, report_count, created_at"
                       + (", " + ", ".join(_extra_cols) if _extra_cols else ""))
        rows = conn.execute(
            f"SELECT {_select_cols} FROM translation_cache "
            f"{where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        # T178 gap 16 — trả `rules_outdated` + `outdated_reason` do server tính.
        # So với CURRENT constitution_hash (load từ lock), không phải hash của chính row
        # (bug cũ: truyền ch=r['constitution_hash'] vào is_rules_outdated → ch != ch luôn False).
        _has_ch_col = 'constitution_hash' in _extra_cols
        try:
            _cur_lock_ch = _t73_style_lock(conn)['constitution_hash']
        except Exception:
            _cur_lock_ch = None
        out = []
        for r in rows:
            d = dict(r)
            st = (r['status'] or '')
            if st == 'edited':
                reason = 'edited'          # bản human, cần bấm "Dịch lại"
            elif not _has_ch_col:
                # T447: DB chưa migrate constitution_hash — so rules_version (legacy) thay vì
                # suy đoán 'unverified' cứng cho MỌI row (khớp policy translate_han_vi()).
                _cur_rv = None
                try:
                    _cur_rv = _t73_rules_version(_t73_get_active_rules(conn))
                except Exception:
                    pass
                reason = 'ok' if (r['rules_version'] and r['rules_version'] == _cur_rv) else 'mismatch'
            elif not d.get('constitution_hash'):
                reason = 'unverified'      # chưa có fingerprint → chưa biết
            elif _t165_is_rules_outdated(r, _cur_lock_ch):
                reason = 'mismatch'        # rules đã đổi sau khi dịch
            else:
                reason = 'ok'
            d['outdated_reason'] = reason
            d['rules_outdated'] = reason in ('edited', 'mismatch')
            out.append(d)
        return jsonify({"ok": True, "total": total, "rows": out})
    finally:
        conn.close()




@app.route('/daoanh/api/translate-rules')
def api_translate_rules_public():
    """T123 — GET /daoanh/api/translate-rules (public).
    Hiển thị Style Constitution: rules_version + active rules + số lượng glossary/exemplar.
    Dùng cho badge "Ban Dịch PTDA" trong giao diện và để user/admin thấy rules hiện hành."""
    conn = get_db_connection()
    try:
        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)
        try:
            gloss_count = conn.execute(
                "SELECT COUNT(*) FROM translation_glossary WHERE is_locked=1").fetchone()[0]
        except Exception:
            gloss_count = 0
        try:
            ex_count = conn.execute(
                "SELECT COUNT(*) FROM translation_exemplar WHERE is_active=1").fetchone()[0]
        except Exception:
            ex_count = 0
        return jsonify({
            "ok": True,
            "rules_version": rv,
            "active_count": len(rules),
            "rules": [{'rule_code': r['rule_code'], 'rule_type': r['rule_type'],
                       'rule_text': r['rule_text']} for r in rules],
            "glossary_locked": gloss_count,
            "exemplar_active": ex_count,
            "persona": "Ban Dịch PTDA",
        })
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-error-reports', methods=['GET'])
def api_admin_translation_error_reports():
    """T123 — GET /daoanh/api/admin/translation-error-reports — danh sách báo lỗi dịch.
    Trả chi tiết: snapshot, error_type, note, page_url, entity, kèm đề xuất rule fix
    (map theo error_type + note) + rules active để admin tra cứu."""
    status = request.args.get('status', '')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    conn = get_db_connection()
    try:
        conds, params = [], []
        if status:
            conds.append("r.status = ?"); params.append(status)
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        total = conn.execute(
            f"SELECT COUNT(*) FROM translation_error_report r {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT r.id, r.cache_id, r.source_type, r.entity_id, "
            f"       r.translated_text_snapshot, r.error_type, r.note, r.page_url, "
            f"       r.status, r.created_at, "
            f"       COALESCE(c.rule_text_c, '<gốc ngoài cache>') AS rule_version_note "
            f" FROM translation_error_report r "
            f" LEFT JOIN (SELECT source_hash as rule_text_c, rules_version FROM translation_cache GROUP BY source_hash, rules_version) c "
            f"   ON 1=0 "
            f" {where} ORDER BY r.id DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        rules = _t73_get_active_rules(conn)
        out = []
        for r in rows:
            row = dict(r)
            row.pop('rule_version_note', None)
            row['suggested_rules'] = _error_report_suggestion(
                row['error_type'], row['note'], rules)
            out.append(row)
        return jsonify({"ok": True, "total": total, "rows": out, "rules": [
            {'rule_code': x['rule_code'], 'rule_text': x['rule_text']} for x in rules]})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translation-error-reports/<int:report_id>', methods=['POST'])
def api_admin_translation_error_report_resolve(report_id):
    """T123 — POST /daoanh/api/admin/translation-error-reports/<id>
    Admin đóng báo lỗi. Body: {status: 'resolved'|'rejected', admin_note?}.
    Ghi nhận bằng cách update status; cache giữ nguyên (quyết định Lee: bản cũ để nguyên)."""
    body = request.get_json(silent=True) or {}
    new_status = body.get('status', 'resolved')
    if new_status not in ('resolved', 'rejected'):
        return jsonify({"ok": False, "error": "status phải là resolved|rejected"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id FROM translation_error_report WHERE id=?", (report_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy báo lỗi"}), 404
        conn.execute(
            "UPDATE translation_error_report SET status=? WHERE id=?",
            (new_status, report_id))
        conn.commit()
        return jsonify({"ok": True, "id": report_id, "status": new_status})
    finally:
        conn.close()




# T178 — BUG-001 fix: hàm này thiếu @app.route ⇒ endpoint /daoanh/api/admin/translate/invalidate
# trả 404 ⇒ nút "Invalidate" ở admin/translation_cache.html + admin/translation_rules.html
# chưa bao giờ chạy được (latent bug, không ai báo lỗi vì fetch không assert status).
@app.route('/daoanh/api/admin/translate/invalidate', methods=['POST'])
def api_admin_translate_invalidate():
    """POST /daoanh/api/admin/translate/invalidate
    Mass-invalidate bản dịch theo rules_version (hoặc tất cả nếu rules_version='ALL').
    Body: {rules_version: '<hash>', source_type: 'person_bio'|'all', limit: int}.
    Dùng khi admin cập nhật rules → muốn user dịch lại với rules mới.

    T178 gap 15 — `limit` (SPEC §8 mục 15): thêm mode "Dịch lại có giới hạn" (batch N row)
    bên cạnh nút full. `limit` absent/0 ⇒ hành vi CŨ (full) — KHÔNG phá call site cũ.
    `limit > 0` ⇒ chỉ invalidate tối đa N row (theo id tăng dần, ưu tiên row cũ nhất),
    trả `limited: true` + `limit` để Admin biết batch có bị cắt không.
    """
    # T269 B1: bắt buộc admin session trước khi mass-invalidate cache dịch.
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    body = request.get_json(silent=True) or {}
    rv = (body.get('rules_version') or '').strip()
    source_type = body.get('source_type', 'all')
    if not rv:
        return jsonify({"ok": False, "error": "Thiếu rules_version. Dùng 'ALL' để xóa tất cả."}), 400
    try:
        limit = int(body.get('limit') or 0)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "limit phải là số nguyên >= 0 (0 = full)"}), 400
    if limit < 0:
        return jsonify({"ok": False, "error": "limit phải là số nguyên >= 0 (0 = full)"}), 400

    # WHERE chung cho cả 2 chế độ (limited dùng thêm id IN (SELECT ... LIMIT ?))
    if rv == 'ALL':
        where = "status != 'invalidated'" if source_type == 'all' \
            else "source_type=? AND status != 'invalidated'"
    else:
        where = "rules_version=? AND status != 'invalidated'" if source_type == 'all' \
            else "rules_version=? AND source_type=? AND status != 'invalidated'"
    params = []
    if rv == 'ALL':
        if source_type != 'all':
            params.append(source_type)
    else:
        params.append(rv)
        if source_type != 'all':
            params.append(source_type)

    conn = get_db_connection()
    try:
        if limit > 0:
            # Batch: chọn tối đa N row theo id tăng dần (row cũ trước) — có kiểm soát
            cur = conn.execute(
                f"UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
                f"WHERE id IN (SELECT id FROM translation_cache WHERE {where} ORDER BY id LIMIT ?)",
                (*params, limit)
            )
        else:
            cur = conn.execute(
                f"UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
                f"WHERE {where}",
                tuple(params)
            )
        cnt = cur.rowcount
        conn.commit()
        return jsonify({"ok": True, "invalidated_count": cnt, "rules_version": rv,
                        "source_type": source_type, "limited": limit > 0, "limit": limit})
    finally:
        conn.close()




@app.route('/daoanh/api/admin/translate/retranslate', methods=['POST'])
def api_admin_translate_retranslate():
    """T447 — POST /daoanh/api/admin/translate/retranslate
    Nút "Dịch lại" MỘT bản dịch cụ thể trong Cpanel (admin/translation_cache.html).
    Body: {id: <translation_cache.id>}. Nhận `cache_id` của dòng đang xem (không
    tính lại hash từ text ở client) — tra đúng dòng theo id, lấy source_hash/
    source_type đã lưu sẵn trong dòng đó.
    Bỏ qua cache, gọi cổng translate_han_vi(force=True) với quy tắc HIỆN TẠI; bản dịch
    cũ được copy vào history_json (cột T447 migration) trước khi bị ghi đè — giữ lịch sử,
    không xoá (SPEC plan §4). Nếu cột history_json chưa migrate, dịch lại vẫn chạy được
    (chỉ không giữ được lịch sử — xem log cảnh báo).

    T447 vòng 2 (QA lỗi 2 + lỗi 3):
    - source_type thuộc `_T447_RETRANSLATE_UNSUPPORTED_SOURCE_TYPES` → 422, không
      âm thầm tạo dòng cache rác (xem comment ở hằng số trên).
    - TRƯỚC khi gọi translate_han_vi() (sửa lỗi 2026-11-01, QA a4012b79): tính lại
      hash của `row['source_text'].strip()` bằng đúng cách cổng dùng
      (`_t73_source_hash`), so với `source_hash` đã lưu của dòng cache này. Lệch
      → 422 HASH_MISMATCH NGAY, KHÔNG gọi AI, KHÔNG đụng DB. Trước đây hash chỉ
      được so SAU khi translate_han_vi() đã gọi AI + ghi dòng cache mới + commit
      (status='auto') mà KHÔNG tìm thấy/invalidate được dòng cũ (vì hash tính lại
      không khớp source_hash cũ, nên lookup cache-hit trong cổng không ra đúng
      dòng) — để lọt dòng cache rác (ví dụ ca `relation_evidence` có excerpt tận
      cùng bằng `；`/`;`: hash gốc = `sha256(excerpt.rstrip('；;'))[:24]`, hash
      cổng tính lại = `_t73_source_hash(excerpt.strip())` — không khớp).
    - source_type='person_bio' → cổng `translate_han_vi()` chạy
      `_t166_post_check_translation` (qua tham số `pre_commit_check`) giống
      luồng chính (`/daoanh/api/person/<id>/translate`), và chạy TRƯỚC khi
      invalidate dòng cũ / ghi dòng mới (sửa lỗi 2026-11-01 — trước đây chạy
      SAU, nên bị chặn vẫn mất bản cũ tốt + để lại dòng cache 'auto' bị chặn
      nằm im lặng). Nếu bị chặn (identity HARD) → 422 REVIEW_REQUIRED, KHÔNG
      đụng cache. Nếu không bị chặn, identity_status/identity_issues/
      identity_lock_hash được ghi vào dòng cache mới trong CÙNG lượt commit
      (nếu cột đã migrate).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
    body = request.get_json(silent=True) or {}
    try:
        cache_id = int(body.get('id'))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Thiếu hoặc sai 'id'"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM translation_cache WHERE id=?", (cache_id,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy bản dịch id=" + str(cache_id)}), 404

        src_type = row['source_type']
        if src_type in _T447_RETRANSLATE_UNSUPPORTED_SOURCE_TYPES:
            return jsonify({
                "ok": False,
                "error_type": "UNSUPPORTED_SOURCE_TYPE",
                "error": (f"source_type='{src_type}' chưa được cổng translate_han_vi "
                          "hỗ trợ đúng cách (hash/định dạng khác cấu trúc văn bản "
                          "thường của cổng) — dùng nút 'Dịch lại' riêng của tab đó, "
                          "không dùng nút chung này."),
            }), 422

        stored_hash = row['source_hash']
        # T447 vòng sửa lỗi 2026-11-01 (QA a4012b79) — HASH_MISMATCH phải phát
        # hiện TRƯỚC khi gọi AI / đụng DB, không phải SAU khi translate_han_vi()
        # đã commit dòng cache mới. Tính lại hash theo đúng cách cổng dùng
        # (_t73_source_hash trên source_text.strip() đang lưu trong dòng này) —
        # nếu lệch với stored_hash, dòng này không còn là nguồn sự thật cho hash
        # của chính nó (ví dụ source_text lưu khác công thức hash gốc, như
        # dila_card JSON hoặc relation_evidence excerpt có `；`/`;` cuối) → trả
        # 422 ngay, không gọi translate_han_vi(), không invalidate/ghi cache.
        recomputed_hash = _t73_source_hash((row['source_text'] or '').strip())
        if recomputed_hash != stored_hash:
            return jsonify({
                "ok": False,
                "error_type": "HASH_MISMATCH",
                "error": (f"Hash tính lại từ source_text không khớp source_hash đã lưu "
                          f"của dòng cache gốc (id={cache_id}) — KHÔNG gọi AI, KHÔNG "
                          "đụng dòng cache cũ, tránh tạo cache rác. Cần xử lý riêng cho "
                          f"source_type='{src_type}'."),
                "old_id": cache_id,
            }), 422

        # T447 vòng sửa lỗi 2026-11-01 (lỗi 3) — person_bio phải chạy T166
        # post-check TRƯỚC KHI cổng invalidate dòng cũ / ghi dòng mới, giống
        # luồng chính (/daoanh/api/person/<id>/translate). Trước đây post-check
        # chạy SAU translate_han_vi(force=True) — cổng đã invalidate bản cũ và
        # ghi 'auto' trước rồi mới kiểm, nên bị chặn vẫn mất bản cũ + để lại
        # dòng cache bị chặn. Truyền callback vào cổng để nó tự kiểm trước khi
        # đụng DB.
        pre_commit_check = None
        if src_type == 'person_bio':
            pre_commit_check = lambda translated_text: _t166_post_check_translation(
                conn, row['source_text'], translated_text or '',
                policy=_t166_identity_lock_policy(conn))
        result = translate_han_vi(
            conn, row['source_text'], src_type, entity_id=row['entity_id'],
            force=True, purpose='admin_retranslate', pre_commit_check=pre_commit_check)
        if result.get('error_type') == 'REVIEW_REQUIRED':
            # Bị T166 chặn TRƯỚC khi ghi cache — dòng cũ KHÔNG bị invalidate,
            # KHÔNG có dòng mới nào được tạo. Trả 422 giống luồng chính.
            precheck = result.get('precheck') or {}
            return jsonify({
                "ok": False, "error_type": "REVIEW_REQUIRED",
                "error": "T166 Identity Lock chặn bản dịch lại — tên nhân vật bị "
                         "biến đổi so với chính pháp.",
                "identity_issues": precheck.get('identity_issues'),
                "old_id": cache_id,
            }), 422
        if not result.get('ok'):
            return jsonify({"ok": False, "error": result.get('error') or 'Dịch lại thất bại'}), 502

        # T447 vòng sửa lỗi 2026-11-01 — lưới an toàn thứ 2 (phòng trường hợp
        # translate_han_vi() tự tính lại hash khác với recomputed_hash đã kiểm
        # ở trên, ví dụ do lock/prompt thay đổi text_in). Nhánh chính (HASH_MISMATCH
        # phát hiện SỚM, trước khi gọi AI) đã chặn ở trên nên nhánh này không còn
        # là đường phát hiện chính, chỉ giữ lại để không lộ cache rác nếu có sai lệch
        # phát sinh bên trong cổng mà bước kiểm trước không bắt được.
        if result.get('source_hash') != stored_hash:
            return jsonify({
                "ok": False,
                "error_type": "HASH_MISMATCH",
                "error": (f"Hash tính lại không khớp dòng cache gốc (id={cache_id}) — "
                          "dòng cũ KHÔNG được invalidate để tránh tạo cache rác. "
                          f"Cần xử lý riêng cho source_type='{src_type}'."),
            }), 422

        # T447 vòng sửa lỗi 2026-11-01 (lỗi 3) — post-check person_bio đã chạy
        # ĐÚNG MỘT LẦN bên trong cổng (pre_commit_check, xem nhánh
        # REVIEW_REQUIRED phía trên) và kết quả identity_status/identity_issues
        # đã được ghi vào dòng cache mới trong CÙNG lượt commit. Không gọi lại
        # _t166_post_check_translation ở đây — tránh chạy T166 hai lần và
        # tránh một khoảng hở UPDATE sau INSERT.
        precheck = result.get('precheck') or {}
        identity_status = precheck.get('identity_status')
        identity_issues = precheck.get('identity_issues')

        return jsonify({
            "ok": True, "id": result.get('cache_id'), "old_id": cache_id,
            "translated_text": result.get('translated_text'),
            "model_id": result.get('model_id'), "rules_version": result.get('rules_version'),
            "used_fallback": result.get('used_fallback', False),
            "identity_status": identity_status, "identity_issues": identity_issues,
        })
    finally:
        conn.close()




@app.route('/daoanh/api/translation/jobs', methods=['GET', 'POST'])
def api_t95_jobs():
    """POST: tạo + chạy job dịch (body: work_id, scope, run_now, mock).
    GET: danh sách job gần đây (query: limit)."""
    if request.method == 'POST':
        import threading
        body = request.get_json(silent=True) or {}
        work_id = (body.get('work_id') or 'T50n2060').strip()
        scope = (body.get('scope') or 'untranslated').strip()
        run_now = bool(body.get('run_now', True))
        mock = bool(body.get('mock', False))
        w = _t95_worker()
        try:
            job_id = w.create_job(work_id, scope=scope)
        except Exception as e:
            app.logger.warning(f'[T95] create_job lỗi: {e}')
            return jsonify({'ok': False, 'error': f'Lỗi tạo job: {e}'}), 400
        if job_id and run_now:
            thread = threading.Thread(target=w.worker_run, args=(job_id,),
                                      kwargs={'mock': mock}, daemon=True)
            thread.start()
            app.logger.info(f'[T95] job {job_id} khởi chạy thread nền')
        return jsonify({'ok': True, 'job_id': job_id, 'running': bool(job_id and run_now)})
    # GET list
    w = _t95_worker()
    con = w._con()
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        rows = con.execute(
            "SELECT job_id, work_id, status, requested_scope, total_passages, "
            "completed_passages, failed_passages, created_at, started_at, finished_at, last_error "
            "FROM translation_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return jsonify({'ok': True, 'jobs': [dict(r) for r in rows]})
    finally:
        con.close()




@app.route('/daoanh/api/translation/jobs/<job_id>')
def api_t95_job_detail(job_id):
    """GET: chi tiết job + item gần nhất + phân bố trạng thái (query: items)."""
    w = _t95_worker()
    con = w._con()
    try:
        j = con.execute("SELECT * FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not j:
            return jsonify({'ok': False, 'error': 'job không tồn tại'}), 404
        items_n = min(int(request.args.get('items', 20)), 200)
        items = con.execute(
            "SELECT ji.passage_id, ji.sequence_no, ji.status, ji.attempt_count, "
            "ji.error_message, ji.completed_at, "
            "(SELECT ts.translation_id FROM translation_segments ts "
            " WHERE ts.passage_id = ji.passage_id AND ts.translation_status <> 'superseded' "
            " ORDER BY ts.revision_no DESC LIMIT 1) AS translation_id, "
            "(SELECT ts.validation_status FROM translation_segments ts "
            " WHERE ts.passage_id = ji.passage_id AND ts.translation_status <> 'superseded' "
            " ORDER BY ts.revision_no DESC LIMIT 1) AS validation_status "
            "FROM translation_job_items ji WHERE ji.job_id=? ORDER BY ji.sequence_no DESC LIMIT ?",
            (job_id, items_n)).fetchall()
        cnt = con.execute(
            "SELECT status, COUNT(*) n FROM translation_job_items WHERE job_id=? GROUP BY status",
            (job_id,)).fetchall()
        return jsonify({'ok': True, 'job': dict(j),
                        'items': [dict(r) for r in items],
                        'counts': {r['status']: r['n'] for r in cnt}})
    finally:
        con.close()




@app.route('/daoanh/api/cbeta/passages/<int:legacy_id>/units')
def api_t95_units(legacy_id):
    """GET: units (text_passages) của 1 passage CBETA theo legacy_id + bản dịch + coverage."""
    work_id = (request.args.get('work_id') or 'T50n2060').strip()
    con = get_db()
    try:
        rows = con.execute(_T95_UNITS_SQL, (work_id, legacy_id)).fetchall()
        units = [_t95_badge(dict(r)) for r in rows]
        ln = con.execute("SELECT passage_id, text_id, loc_ref, raw_text FROM passage WHERE passage_id=?",
                         (legacy_id,)).fetchone()
        legacy = dict(ln) if ln else {}
        cov = _t95_coverage(con, work_id)
        return jsonify({'ok': True, 'work_id': work_id, 'legacy': legacy,
                        'units': units, 'coverage': cov})
    finally:
        con.close()




@app.route('/daoanh/api/cbeta/works/<work_id>/coverage')
def api_t95_work_coverage(work_id):
    """GET: coverage tích lũy của 1 tác phẩm (dùng cho header progress + Phase E export)."""
    con = get_db()
    try:
        return jsonify({'ok': True, 'work_id': work_id, 'coverage': _t95_coverage(con, work_id)})
    finally:
        con.close()




@app.route('/daoanh/api/cbeta/works/<work_id>/translation-export')
def api_t95_translation_export(work_id):
    """GET: export tích lũy toàn tác phẩm (JSON streaming).
    Query: ?download=1 → Content-Disposition attachment; ?format=md → Markdown."""
    con = get_db()
    fmt = (request.args.get('format') or 'json').lower()
    if fmt == 'md':
        try:
            cov = _t95_coverage(con, work_id)
            return _t95_export_markdown(con, work_id, cov)
        finally:
            con.close()

    def stream():
        try:
            cov = _t95_coverage(con, work_id)
            for part in _t95_export_iter(con, work_id, cov):
                yield part
        finally:
            con.close()

    resp = Response(stream(), mimetype='application/json; charset=utf-8')
    if request.args.get('download'):
        resp.headers['Content-Disposition'] = f"attachment; filename={work_id}_translation_export.json"
    return resp




@app.route('/daoanh/api/admin/translation/jobs')
def api_t95_admin_jobs():
    """GET: ds job dịch + tổng hợp (admin monitor) + số file raw audit mỗi job."""
    w = _t95_worker()
    con = w._con()
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        rows = con.execute(_T95_JOBS_LIST_SQL + ' LIMIT ?', (limit,)).fetchall()
        jobs = []
        for r in rows:
            d = dict(r)
            d['raw_audit'] = len(os.listdir(_t95_raw_dir(d['job_id']))) if os.path.isdir(_t95_raw_dir(d['job_id'])) else 0
            d['progress_percent'] = round(d['done_items'] * 100.0 / d['item_total']) if d['item_total'] else 0
            jobs.append(d)
        return jsonify({'ok': True, 'jobs': jobs})
    finally:
        con.close()




@app.route('/daoanh/api/admin/translation/jobs/<job_id>/raw')
def api_t95_admin_job_raw(job_id):
    """GET: danh sách file raw audit của 1 job (admin only, không đọc nội dung)."""
    d = _t95_raw_dir(job_id)
    if not os.path.isdir(d):
        return jsonify({'ok': True, 'files': []})
    files = []
    for name in sorted(os.listdir(d)):
        try:
            st = os.stat(os.path.join(d, name))
            files.append({'name': name, 'size': st.st_size, 'modified': datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')})
        except OSError:
            continue
    return jsonify({'ok': True, 'job_id': job_id, 'files': files})




@app.route('/daoanh/api/admin/translation/jobs/<job_id>/resume', methods=['POST'])
def api_t95_admin_job_resume(job_id):
    """POST: resume job — requeue toàn bộ item failed (reset attempt) rồi chạy lại worker nền."""
    import threading
    w = _t95_worker()
    con = w._con()
    try:
        job = con.execute("SELECT job_id, status, total_passages FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not job:
            return jsonify({'ok': False, 'error': f'Không tìm thấy job {job_id}'}), 404
        if job['status'] in ('completed', 'running', 'cancelled'):
            return jsonify({'ok': False, 'error': f'Job ở trạng thái {job["status"]} — chỉ resume khi paused/failed.'}), 400
        now = datetime.now().isoformat(timespec='seconds')
        con.execute("UPDATE translation_job_items SET status='queued', attempt_count=0, error_message=NULL, "
                    "started_at=NULL, completed_at=NULL WHERE job_id=? AND status IN ('failed','error')",
                    (job_id,))
        con.execute("UPDATE translation_jobs SET status='paused', finished_at=NULL, last_error=NULL, updated_at=? WHERE job_id=?",
                    (now, job_id))
        con.commit()
        remaining = con.execute("SELECT COUNT(*) FROM translation_job_items WHERE job_id=? AND status IN ('queued','running')",
                                (job_id,)).fetchone()[0]
        if remaining == 0:
            return jsonify({'ok': True, 'job_id': job_id, 'message': 'Không còn item để resume.'})
        thread = threading.Thread(target=w.worker_run, args=(job_id,), kwargs={'mock': False}, daemon=True)
        thread.start()
        app.logger.info(f'[T95/admin] resume job {job_id} — {remaining} item được requeue')
        return jsonify({'ok': True, 'job_id': job_id, 'resumed': remaining})
    finally:
        con.close()




@app.route('/daoanh/api/admin/translation/jobs/<job_id>/cancel', methods=['POST'])
def api_t95_admin_job_cancel(job_id):
    """POST: cancel job — hủy các item còn queued/running (đã dịch vẫn giữ)."""
    w = _t95_worker()
    con = w._con()
    try:
        job = con.execute("SELECT job_id, status FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not job:
            return jsonify({'ok': False, 'error': f'Không tìm thấy job {job_id}'}), 404
        now = datetime.now().isoformat(timespec='seconds')
        changed = con.execute("UPDATE translation_job_items SET status='cancelled', completed_at=? "
                              "WHERE job_id=? AND status IN ('queued','running')", (now, job_id)).rowcount
        if job['status'] == 'running':
            con.execute("UPDATE translation_jobs SET status='cancelled', finished_at=?, updated_at=? WHERE job_id=?",
                        (now, now, job_id))
        con.commit()
        return jsonify({'ok': True, 'job_id': job_id, 'cancelled_items': changed})
    finally:
        con.close()




# ============================================================
# T94 Phase 3 — Duyệt chuẩn thủ công (manual_verified alignment)
#   Admin verify 1 segment → quality_status='reviewed',
#   review_status='verified' + passage_translation_alignment manual_verified
# ============================================================

@app.route('/daoanh/api/admin/translation/verify', methods=['POST'])
def api_t94_admin_verify_translation():
    """POST: admin duyệt chuẩn thủ công 1 segment đã dịch.

    Body JSON:
      passage_id (bắt buộc) — id text_passages (unit) đã có bản dịch hiện hành
      reviewer   (tùy chọn, mặc định 'admin')
      note       (tùy chọn)  — ghi chú duyệt

    Idempotent: bản dịch cũ vẫn giữ; ghi đè manual_verified cũ cho (passage, translation).
    Rollback thủ công: xóa dòng passage_translation_alignment manual_verified
      + UPDATE translation_segments SET quality_status=NULL, review_status='pending', reviewer=NULL
        WHERE translation_id=<tid>.
    """
    dta = request.get_json(silent=True) or {}
    passage_id = (dta.get('passage_id') or '').strip()
    reviewer = (dta.get('reviewer') or 'admin').strip()
    note = (dta.get('note') or '').strip()
    if not passage_id:
        return jsonify({'ok': False, 'error': 'Thiếu passage_id.'}), 400
    con = get_db()
    try:
        ts = con.execute(
            "SELECT translation_id, translation_status FROM translation_segments "
            "WHERE passage_id=? AND translation_status <> 'superseded' "
            "ORDER BY revision_no DESC LIMIT 1", (passage_id,)).fetchone()
        if not ts:
            return jsonify({'ok': False,
                            'error': 'Không tìm thấy bản dịch hiện hành cho passage này.'}), 404
        tid = ts['translation_id']
        now = datetime.now().isoformat(timespec='seconds')
        con.execute(
            "UPDATE translation_segments SET quality_status='reviewed', review_status='verified', "
            "reviewer=?, updated_at=? WHERE translation_id=?",
            (reviewer, now, tid))
        con.execute(
            "DELETE FROM passage_translation_alignment WHERE passage_id=? AND translation_id=? "
            "AND alignment_type='manual_verified'", (passage_id, tid))
        con.execute(
            "INSERT INTO passage_translation_alignment "
            "(passage_id, translation_id, alignment_type, confidence, alignment_method, "
            " review_status, reviewer, note, created_at) "
            "VALUES (?,?,'manual_verified',1.0,'manual_admin_verify','verified',?,?,?)",
            (passage_id, tid, reviewer, note or 'Duyệt chuẩn thủ công', now))
        con.commit()
        app.logger.info(f'[T94] duyệt chuẩn translation {tid} cho passage {passage_id} bởi {reviewer}')
        return jsonify({'ok': True, 'translation_id': tid, 'passage_id': passage_id,
                        'reviewer': reviewer, 'manual_verified': True})
    except Exception as e:
        con.rollback()
        app.logger.warning(f'[T94] verify translation lỗi: {e}')
        return jsonify({'ok': False, 'error': f'Lỗi khi duyệt chuẩn: {e}'}), 500
    finally:
        con.close()




# ============================================================
# T96 — Per-Segment Translation APIs
# ============================================================

@app.route('/daoanh/api/segments/<path:canonical_ref>', methods=['GET'])
def api_segments_list(canonical_ref):
    """GET /daoanh/api/segments/<canonical_ref>
    Trả về tất cả text_passages segments cho 1 canonical_ref (loc_ref),
    kèm trạng thái bản dịch từng segment từ translation_segments.

    canonical_ref: e.g. "0-0457a-" (URL-encoded khi cần)
    """
    conn = get_db_connection()
    try:
        segs = conn.execute(
            """SELECT tp.passage_id, tp.sequence_no, tp.original_zh,
                      ts.translation_id, ts.translation_text AS translation_vi,
                      ts.translation_status, ts.model_name, ts.updated_at
               FROM text_passages tp
               LEFT JOIN translation_segments ts
                 ON ts.passage_id = tp.passage_id
                 AND ts.language = 'vi'
                 AND ts.translation_status NOT IN ('failed', 'superseded')
               WHERE tp.canonical_ref = ?
               ORDER BY tp.sequence_no""",
            (canonical_ref,)
        ).fetchall()
        if not segs:
            return jsonify({'ok': False, 'error': 'Không tìm thấy segments cho canonical_ref này'}), 404
        items = []
        done_count = 0
        for s in segs:
            status = s['translation_status'] or 'pending'
            if status == 'done':
                done_count += 1
            items.append({
                'passage_id': s['passage_id'],
                'sequence_no': s['sequence_no'],
                'original_zh': s['original_zh'],
                'translation_id': s['translation_id'],
                'translation_vi': s['translation_vi'],
                'translation_status': status,
                'model_name': s['model_name'],
                'updated_at': s['updated_at'],
            })
        return jsonify({
            'ok': True,
            'canonical_ref': canonical_ref,
            'total': len(items),
            'translated': done_count,
            'segments': items,
        })
    finally:
        conn.close()




@app.route('/daoanh/api/segments/translate', methods=['POST'])
def api_segment_translate():
    """POST /daoanh/api/segments/translate
    Dịch 1 segment text_passages bằng Groq. Lưu vào translation_segments.
    Body: {"passage_id": "daoanh:cbeta:T50n2060:0457a:p0001"}
    Dedup: nếu đã có bản dịch status=done thì trả ngay, không gọi API.
    """
    cfg = _llm_config_read()
    _groq_key = cfg.get('groq_key') or GROQ_KEY
    _groq_model = cfg.get('groq_model') or GROQ_MODEL
    if not _groq_key:
        return jsonify({'ok': False, 'error': 'GROQ_API_KEY chưa cấu hình'}), 503
    body = request.get_json(silent=True) or {}
    passage_id = (body.get('passage_id') or '').strip()
    if not passage_id:
        return jsonify({'ok': False, 'error': 'Thiếu passage_id'}), 400
    conn = get_db_connection()
    try:
        seg = conn.execute(
            "SELECT passage_id, sequence_no, canonical_ref, original_zh, work_id "
            "FROM text_passages WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not seg:
            return jsonify({'ok': False, 'error': 'Không tìm thấy passage_id trong text_passages'}), 404
        zh_text = (seg['original_zh'] or '').strip()
        if not zh_text:
            return jsonify({'ok': False, 'error': 'Segment không có nội dung Hán văn'}), 404
        # Dedup: kiểm tra đã có bản dịch done chưa
        existing = conn.execute(
            "SELECT translation_id, translation_text, translation_status FROM translation_segments "
            "WHERE passage_id = ? AND language = 'vi' AND translation_status = 'done' "
            "ORDER BY created_at DESC LIMIT 1", (passage_id,)
        ).fetchone()
        if existing:
            return jsonify({
                'ok': True, 'from_cache': True,
                'passage_id': passage_id,
                'translation_id': existing['translation_id'],
                'translation_vi': existing['translation_text'],
                'status': 'done',
            })
        # Dedup: đang queued/translating?
        in_progress = conn.execute(
            "SELECT translation_id, translation_status FROM translation_segments "
            "WHERE passage_id = ? AND language = 'vi' AND translation_status IN ('queued', 'translating') "
            "LIMIT 1", (passage_id,)
        ).fetchone()
        if in_progress:
            return jsonify({
                'ok': False, 'error': 'already_queued',
                'passage_id': passage_id,
                'translation_id': in_progress['translation_id'],
                'status': in_progress['translation_status'],
            }), 409
        # Đánh dấu queued
        import uuid as _uuid
        tid = 'ts-' + _uuid.uuid4().hex[:12]
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO translation_segments
               (translation_id, work_id, language, translation_text, translator_type,
                model_name, prompt_version, source_passage_ids, translation_status,
                passage_id, created_at, updated_at)
               VALUES (?, ?, 'vi', '', 'ai_groq', ?, 't96v1', ?, 'queued', ?, ?, ?)""",
            (tid, seg['work_id'], _groq_model, passage_id, passage_id, now, now)
        )
        conn.commit()
        # Gọi Groq
        total_count = conn.execute(
            "SELECT COUNT(*) FROM text_passages WHERE canonical_ref = ?",
            (seg['canonical_ref'],)
        ).fetchone()[0]
        prompt = (
            f"Bạn là dịch giả Hán-Việt chuyên ngành Phật học. Dịch đoạn Hán văn sau sang tiếng Việt.\n\n"
            f"Quy tắc:\n"
            f"- Chỉ dịch đoạn này, không giải thích thêm\n"
            f"- Giữ nguyên tên riêng Hán-Việt phổ thông (Thiếu Lâm, Bồ Đề Đạt Ma, Huyền Trang, v.v.)\n"
            f"- Không dịch ID hay mã kỹ thuật\n"
            f"- Trả về JSON: {{\"translation_vi\": \"...\"}}\n\n"
            f"Đoạn {seg['sequence_no']}/{total_count} — {seg['canonical_ref']}:\n{zh_text}"
        )
        try:
            conn.execute(
                "UPDATE translation_segments SET translation_status='translating', updated_at=? "
                "WHERE translation_id=?", (datetime.now().isoformat(), tid)
            )
            conn.commit()
            import json as _json
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {_groq_key}', 'Content-Type': 'application/json'},
                json={'model': _groq_model, 'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.2, 'max_tokens': 1024},
                timeout=30
            )
            result = resp.json()
            raw_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            vi_text = None
            try:
                parsed = _json.loads(raw_content.strip())
                vi_text = parsed.get('translation_vi', '').strip()
            except Exception:
                vi_text = raw_content.strip()
            if not vi_text:
                raise ValueError("LLM trả về nội dung rỗng")
            conn.execute(
                "UPDATE translation_segments SET translation_text=?, translation_status='done', "
                "model_name=?, updated_at=? WHERE translation_id=?",
                (vi_text, _groq_model, datetime.now().isoformat(), tid)
            )
            conn.commit()
            return jsonify({
                'ok': True, 'from_cache': False,
                'passage_id': passage_id,
                'translation_id': tid,
                'translation_vi': vi_text,
                'model_name': _groq_model,
                'status': 'done',
            })
        except Exception as e:
            conn.execute(
                "UPDATE translation_segments SET translation_status='failed', "
                "updated_at=? WHERE translation_id=?",
                (datetime.now().isoformat(), tid)
            )
            conn.commit()
            app.logger.error(f"[T96] translate segment {passage_id} failed: {e}")
            return jsonify({'ok': False, 'error': f'Groq error: {str(e)}', 'passage_id': passage_id}), 500
    finally:
        conn.close()




@app.route('/daoanh/api/admin/cbeta/batch-import', methods=['POST'])
def t182_batch_import():
    """POST {series: 'T', limit: 5} — import hàng loạt XML theo thứ tự series.
    Chỉ import bộ chưa có passages, tuần tự tối đa `limit` bộ.
    Trả {ok, queued: [{sigla, status, passages}], skipped, errors}
    """
    body    = request.get_json(force=True) or {}
    series  = (body.get('series') or 'T').strip().upper()
    max_n   = min(20, max(1, int(body.get('limit', 5))))

    conn = get_db()
    # Lấy các bộ chưa import (sigla có XML, chưa có passage) theo thứ tự
    candidates = conn.execute("""
        SELECT c.sigla FROM cbeta_catalog_vn c
        WHERE c.series = ? AND c.sigla IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM passage p WHERE p.text_id = c.sigla)
        ORDER BY CAST(c.sh_number AS INTEGER)
        LIMIT ?
    """, (series, max_n * 3)).fetchall()  # lấy dư để lọc bộ có XML

    queued, skipped, errors = [], [], []
    count = 0
    for row in candidates:
        if count >= max_n:
            break
        sigla = row['sigla']

        # Bước 1: tìm XML local
        xml_path = _t181_xml_path(sigla)

        # Bước 2 (T183 lazy-fetch): nếu không có local → thử download tự động
        fetch_note = None
        if not xml_path:
            xml_path, fetch_reason = _t183_lazy_fetch_xml(sigla)
            if xml_path:
                # Download thành công — ghi chú để log
                fetch_note = fetch_reason   # 'downloaded'
            else:
                # Không thể lấy tự động (T56-T84 hoặc lỗi mạng)
                skipped.append({
                    'sigla': sigla,
                    'reason': 'xml_not_found',
                    'fetch_note': fetch_reason,
                })
                continue

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("import_cbeta", _T181_IMPORT_PY)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.run([__import__('pathlib').Path(xml_path)])
            p_cnt = conn.execute(
                "SELECT COUNT(*) FROM passage WHERE text_id=?", (sigla,)).fetchone()[0]
            queued.append({
                'sigla': sigla, 'status': 'imported', 'passages': p_cnt,
                'fetch_note': fetch_note,   # None = từ local, 'downloaded' = lazy-fetch
            })
            count += 1
        except Exception as e:
            errors.append({'sigla': sigla, 'error': str(e)})

    return jsonify({
        "ok": True, "series": series,
        "queued": queued, "skipped": skipped, "errors": errors,
        "total_imported": count,
    })




@app.route('/daoanh/api/kinh/<sigla>/passages')
def t182_kinh_passages(sigla):
    """GET /daoanh/api/kinh/T51n2076/passages?offset=0&limit=20
    Lấy passages đã dịch của 1 bộ kinh để web users đọc.
    """
    sigla = sigla.strip()
    try:
        offset = max(0, int(request.args.get('offset', 0)))
        limit  = min(50, max(1, int(request.args.get('limit', 20))))
    except (ValueError, TypeError):
        offset, limit = 0, 20
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) FROM passage WHERE text_id=? AND source='CBETA'", (sigla,)).fetchone()[0]
    rows = conn.execute(
        """SELECT passage_id, loc_ref, raw_text, vi_text
           FROM passage WHERE text_id=? AND source='CBETA'
           ORDER BY rowid LIMIT ? OFFSET ?""",
        (sigla, limit, offset)).fetchall()
    catalog = conn.execute(
        "SELECT title_vi, title_zh, dynasty_vi, author_zh, juans FROM cbeta_catalog_vn WHERE sigla=?",
        (sigla,)).fetchone()
    return jsonify({
        "sigla": sigla,
        "catalog": dict(catalog) if catalog else {},
        "total": total, "offset": offset, "limit": limit,
        "items": [{"passage_id": r['passage_id'], "loc_ref": r['loc_ref'],
                   "raw_text": r['raw_text'], "vi_text": r['vi_text']} for r in rows],
    })
