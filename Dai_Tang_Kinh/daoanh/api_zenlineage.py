# -*- coding: utf-8 -*-
"""T378 (bước 1 của T364): Zen Lineage HITL Review — tách nguyên văn từ app.py sang blueprint.

Nội dung route, SQL và response giữ y như khi còn trong app.py (T139 Phase 2). Đăng ký trong app.py:
    app.register_blueprint(create_zenlineage_blueprint(get_db_connection))
Route giữ nguyên đường dẫn /daoanh/api/admin/zenlineage/*; tên endpoint đổi thành "zenlineage.<hàm>".
"""
import json

from flask import Blueprint, current_app, jsonify, request


def _iso_now():
    from datetime import datetime as _dt
    return _dt.now().isoformat(timespec='seconds')


# ============================================================
# T139 Phase 2 — Zen Lineage HITL Review (additive, DERIVED-only)
# ------------------------------------------------------------
# Candidate pool: source_staging (row_type='master') — không đụng entity_source_ids
# (schema chặn entity_id NULL).
# Quyết định HITL: bảng DERIVED zenlineage_review (0 ALTER base).
# Approve → ghi entity_source_ids (entity_id thật, verified=1, match_status='approved').
# ============================================================
_ZEN_REVIEW_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS zenlineage_review (
    source_entity_id   TEXT PRIMARY KEY,
    status             TEXT NOT NULL,      -- approved | rejected
    dila_person_id     TEXT,
    entity_hub_id      INTEGER,
    confidence         REAL,
    editor             TEXT,
    note               TEXT,
    created_at         TEXT,
    updated_at         TEXT
)
"""


def _zen_ensure_review_table(conn):
    conn.execute(_ZEN_REVIEW_TABLE_SQL)
    conn.commit()


def _zen_suggest(conn, name, limit=5):
    """Gợi ý DILA person cho 1 zen slug — dò token trong tên (name_zh/name_vi/name_en/id).
    Trả về top candidates: {dila_id, name_vi, name_zh, sect, entity_hub_id, score}."""
    name = (name or '').strip()
    if not name:
        return []
    tokens = [t for t in (name.replace('-', ' ').replace('_', ' ').split()) if len(t) >= 2]
    if not tokens:
        return []
    # dò từng token riêng (OR) — token dài >=3 lấy nguyên, token 2 ký tự dùng prefix
    likes = []
    for t in tokens[:4]:
        like = t + '%' if len(t) >= 3 else '%' + t + '%'
        likes.append(like)
    ors = ' OR '.join(['p.name_zh LIKE ?', 'p.name_vi LIKE ?', 'p.name_en LIKE ?', 'p.name_ja LIKE ?'] * len(likes))
    params = []
    for like in likes:
        params += [like, like, like, like]
    params.append(limit * 8)
    rows = conn.execute(
        """SELECT p.id AS dila_id, p.name_vi, p.name_zh, p.name_en, p.name_ja, p.sect,
                  (SELECT eh.entity_id FROM entity_hub eh
                    WHERE eh.entity_type='PERSON' AND eh.canonical_label=p.id LIMIT 1) AS entity_hub_id
             FROM people p
             WHERE %s
             LIMIT ?""" % ors, params).fetchall()
    out = []
    for r in rows:
        hay = ' '.join(x or '' for x in (r['name_zh'], r['name_vi'], r['name_en'], r['name_ja']))
        score = 0
        for t in tokens:
            if t in hay:
                score += 2
            elif t[:2] in hay or t[:2] in (r['name_zh'] or ''):
                score += 1
        # tiêu chuẩn hóa Hán tự: nếu zen tên Hán trùng 1-2 ký tự chữ Hán
        if r['name_zh']:
            for ch in tokens:
                for c in ch:
                    if len(c) == 1 and c in r['name_zh']:
                        score += 1
        if score == 0:
            continue
        hit = {'dila_id': r['dila_id'], 'name_vi': r['name_vi'], 'name_zh': r['name_zh'],
               'name_en': r['name_en'], 'sect': r['sect'], 'entity_hub_id': r['entity_hub_id'],
               'score': score}
        out.append(hit)
    out.sort(key=lambda x: -x['score'])
    seen = set()
    uniq = []
    for h in out:
        if h['dila_id'] not in seen:
            seen.add(h['dila_id'])
            uniq.append(h)
    return uniq[:limit]


def create_zenlineage_blueprint(get_db_connection):
    bp = Blueprint('zenlineage', __name__)

    @bp.route('/daoanh/api/admin/zenlineage/candidates')
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
            current_app.logger.error(f"zenlineage_candidates error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500


    @bp.route('/daoanh/api/admin/zenlineage/candidate/<slug>/approve', methods=['POST'])
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
            current_app.logger.error(f"zenlineage_candidate_approve error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500


    @bp.route('/daoanh/api/admin/zenlineage/candidate/<slug>/reject', methods=['POST'])
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
            current_app.logger.error(f"zenlineage_candidate_reject error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500


    @bp.route('/daoanh/api/admin/zenlineage/candidate/<slug>/unset', methods=['POST'])
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
            current_app.logger.error(f"zenlineage_candidate_unset error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500


    @bp.route('/daoanh/api/admin/zenlineage/stats')
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
            current_app.logger.error(f"zenlineage_stats error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500

    return bp
