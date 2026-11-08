# -*- coding: utf-8 -*-
"""T380 — Số đời truyền thừa nhập tay (Admin).

Mục đích: với các người mà code KHÔNG tính được số đời, Admin nhập tay số đời theo từng dòng pháp.
- Danh sách "chưa xác định" = vn_person_authority không có dòng nào trong person_gen_computed
  có số đời (chỉ đọc, do ETL tính).
- Dòng pháp = khai tổ (lấy từ scripts/anchors_khai_to_dong.json, chỉ các mục đã khóa có dila_id).
- Mỗi (người, dòng pháp) là một dòng nhập tay; mọi thay đổi ghi nhật ký person_generation_manual_history.
- Bảng nhập tay KHÔNG nằm trong danh sách DROP của ETL nên ETL chạy lại không xóa dữ liệu nhập tay.

Đăng ký trong app.py:
    app.register_blueprint(create_manual_generation_blueprint(os.path.dirname(__file__), get_db_connection))
"""
import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

ANCHOR_FILE = os.path.join('scripts', 'anchors_khai_to_dong.json')
GEN_MIN, GEN_MAX = 0, 200

MANUAL_DDL = [
    """CREATE TABLE IF NOT EXISTS person_generation_manual (
        person_id                TEXT NOT NULL,
        lineage_founder_dila_id  TEXT NOT NULL,
        generation               INTEGER NOT NULL,
        note                     TEXT,
        editor                   TEXT,
        updated_at               TEXT NOT NULL,
        PRIMARY KEY (person_id, lineage_founder_dila_id)
    )""",
    """CREATE TABLE IF NOT EXISTS person_generation_manual_history (
        id                       INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id                TEXT NOT NULL,
        lineage_founder_dila_id  TEXT NOT NULL,
        old_generation           INTEGER,
        new_generation           INTEGER,
        action                   TEXT NOT NULL,
        note                     TEXT,
        editor                   TEXT,
        changed_at               TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_pgm_history_person "
    "ON person_generation_manual_history(person_id, changed_at)",
]

# Điều kiện "code đã tính được số đời" cho một người (bất kỳ cột nào có giá trị).
_COMPUTED_OK = ("v.id IN (SELECT person_id FROM person_gen_computed "
                "WHERE gen_sect IS NOT NULL OR gen_lamte IS NOT NULL OR gen_thientong IS NOT NULL)")


def _now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def _ensure_tables(conn):
    for ddl in MANUAL_DDL:
        conn.execute(ddl)


def _load_founders(base_dir):
    """Đọc danh sách khai tổ đã khóa (có dila_id) từ file anchor. Không đoán ID."""
    path = os.path.join(base_dir, ANCHOR_FILE)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    out, seen = [], set()
    for a in data.get('anchors', []):
        dila_id = a.get('dila_id')
        if not dila_id or a.get('trang_thai') != 'locked' or dila_id in seen:
            continue
        seen.add(dila_id)
        out.append({
            'dila_id': dila_id,
            'lineage': a.get('nhanh'),
            'name_vi': a.get('ten_viet'),
            'doi': a.get('doi'),
        })
    return out


def _parse_gen(value):
    try:
        g = int(value)
    except (TypeError, ValueError):
        return None
    return g if GEN_MIN <= g <= GEN_MAX else None


def create_manual_generation_blueprint(base_dir, get_db_connection):
    bp = Blueprint('manual_generation', __name__)

    def _founders():
        return _load_founders(base_dir)

    @bp.route('/daoanh/api/admin/manual-gen/founders')
    def manual_gen_founders():
        return jsonify({'ok': True, 'items': _founders()})

    @bp.route('/daoanh/api/admin/manual-gen/unresolved')
    def manual_gen_unresolved():
        """Người chưa có số đời theo code, kèm các số đời nhập tay hiện có."""
        try:
            page = max(1, int(request.args.get('page', 1)))
            limit = min(max(1, int(request.args.get('limit', 50))), 200)
            q = (request.args.get('q', '') or '').strip()
            conn = get_db_connection()
            try:
                _ensure_tables(conn)
                where = f"WHERE NOT ({_COMPUTED_OK})"
                params = []
                if q:
                    where += " AND (v.name_vi LIKE ? OR v.id LIKE ? OR v.dila_id LIKE ?)"
                    params += [f'%{q}%'] * 3
                total = conn.execute(
                    f"SELECT COUNT(*) FROM vn_person_authority v {where}", params).fetchone()[0]
                rows = conn.execute(
                    f"SELECT v.id, v.name_vi, v.name_zh, v.dila_id FROM vn_person_authority v {where} "
                    "ORDER BY v.name_vi, v.id LIMIT ? OFFSET ?",
                    params + [limit, (page - 1) * limit]).fetchall()
                ids = [r['id'] for r in rows]
                manual = {}
                if ids:
                    marks = ','.join('?' * len(ids))
                    for m in conn.execute(
                            "SELECT person_id, lineage_founder_dila_id, generation, note, editor, updated_at "
                            f"FROM person_generation_manual WHERE person_id IN ({marks})", ids):
                        manual.setdefault(m['person_id'], []).append({
                            'lineage_founder_dila_id': m['lineage_founder_dila_id'],
                            'generation': m['generation'], 'note': m['note'],
                            'editor': m['editor'], 'updated_at': m['updated_at']})
                items = [{
                    'person_id': r['id'], 'name_vi': r['name_vi'], 'name_zh': r['name_zh'],
                    'dila_id': r['dila_id'], 'manual': manual.get(r['id'], []),
                } for r in rows]
                conn.commit()
                return jsonify({'ok': True, 'total': total, 'page': page, 'limit': limit, 'items': items})
            finally:
                conn.close()
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

    @bp.route('/daoanh/api/admin/manual-gen/entry', methods=['POST'])
    def manual_gen_upsert():
        """Thêm/sửa số đời nhập tay cho (người, dòng pháp). Ghi nhật ký trong cùng transaction."""
        data = request.get_json(silent=True) or {}
        person_id = (data.get('person_id') or '').strip()
        founder = (data.get('lineage_founder_dila_id') or '').strip()
        gen = _parse_gen(data.get('generation'))
        note = (data.get('note') or '').strip() or None
        editor = (data.get('editor') or '').strip() or 'admin'
        if not person_id or not founder:
            return jsonify({'ok': False, 'error': 'Thiếu person_id hoặc lineage_founder_dila_id'}), 400
        if gen is None:
            return jsonify({'ok': False, 'error': f'Số đời phải là số nguyên {GEN_MIN}–{GEN_MAX}'}), 400
        if founder not in {f['dila_id'] for f in _founders()}:
            return jsonify({'ok': False, 'error': 'Dòng pháp không thuộc danh sách khai tổ đã khóa'}), 400
        conn = get_db_connection()
        try:
            _ensure_tables(conn)
            if not conn.execute("SELECT 1 FROM vn_person_authority WHERE id=?", (person_id,)).fetchone():
                return jsonify({'ok': False, 'error': f'Không có người `{person_id}`'}), 404
            now = _now()
            with conn:
                old = conn.execute(
                    "SELECT generation FROM person_generation_manual "
                    "WHERE person_id=? AND lineage_founder_dila_id=?", (person_id, founder)).fetchone()
                conn.execute(
                    "INSERT INTO person_generation_manual "
                    "(person_id, lineage_founder_dila_id, generation, note, editor, updated_at) "
                    "VALUES (?,?,?,?,?,?) ON CONFLICT(person_id, lineage_founder_dila_id) DO UPDATE SET "
                    "generation=excluded.generation, note=excluded.note, editor=excluded.editor, "
                    "updated_at=excluded.updated_at",
                    (person_id, founder, gen, note, editor, now))
                conn.execute(
                    "INSERT INTO person_generation_manual_history "
                    "(person_id, lineage_founder_dila_id, old_generation, new_generation, action, note, editor, changed_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (person_id, founder, old['generation'] if old else None, gen,
                     'update' if old else 'insert', note, editor, now))
            return jsonify({'ok': True, 'person_id': person_id, 'lineage_founder_dila_id': founder,
                            'generation': gen, 'old_generation': old['generation'] if old else None})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
        finally:
            conn.close()

    @bp.route('/daoanh/api/admin/manual-gen/entry/delete', methods=['POST'])
    def manual_gen_delete():
        data = request.get_json(silent=True) or {}
        person_id = (data.get('person_id') or '').strip()
        founder = (data.get('lineage_founder_dila_id') or '').strip()
        editor = (data.get('editor') or '').strip() or 'admin'
        if not person_id or not founder:
            return jsonify({'ok': False, 'error': 'Thiếu person_id hoặc lineage_founder_dila_id'}), 400
        conn = get_db_connection()
        try:
            _ensure_tables(conn)
            now = _now()
            with conn:
                old = conn.execute(
                    "SELECT generation FROM person_generation_manual "
                    "WHERE person_id=? AND lineage_founder_dila_id=?", (person_id, founder)).fetchone()
                if not old:
                    return jsonify({'ok': False, 'error': 'Không có dòng nhập tay để xóa'}), 404
                conn.execute(
                    "DELETE FROM person_generation_manual WHERE person_id=? AND lineage_founder_dila_id=?",
                    (person_id, founder))
                conn.execute(
                    "INSERT INTO person_generation_manual_history "
                    "(person_id, lineage_founder_dila_id, old_generation, new_generation, action, note, editor, changed_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (person_id, founder, old['generation'], None, 'delete', None, editor, now))
            return jsonify({'ok': True, 'person_id': person_id, 'lineage_founder_dila_id': founder})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
        finally:
            conn.close()

    @bp.route('/daoanh/api/admin/manual-gen/history')
    def manual_gen_history():
        person_id = (request.args.get('person_id', '') or '').strip()
        limit = min(max(1, int(request.args.get('limit', 100))), 500)
        conn = get_db_connection()
        try:
            _ensure_tables(conn)
            if person_id:
                rows = conn.execute(
                    "SELECT * FROM person_generation_manual_history WHERE person_id=? "
                    "ORDER BY id DESC LIMIT ?", (person_id, limit)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM person_generation_manual_history ORDER BY id DESC LIMIT ?",
                    (limit,)).fetchall()
            return jsonify({'ok': True, 'items': [dict(r) for r in rows]})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
        finally:
            conn.close()

    return bp
