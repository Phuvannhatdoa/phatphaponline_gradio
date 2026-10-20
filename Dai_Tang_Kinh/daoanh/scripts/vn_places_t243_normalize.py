# -*- coding: utf-8 -*-
"""T243 (M7 GIS VN) — Ingest DILA place + Xây chỉ số tìm kiếm theo khóa chuẩn.

Đọc BẢNG RAW `places_dila` (READ-ONLY, Zero-RAM qua generator) + tên Việt tốt nhất
từ `namevi_map_places`, sinh khóa chuẩn (NFKC + không dấu tiếng Việt + bỏ cơ sở
thờ tự + Hán-Việt + pinyin) vào 2 bảng ADDITIVE:

  place_norm_keys   — mỗi dòng = 1 (dila_id, name_role, key_kind) → norm_key
  place_norm_fts    — FTS5 external-content trên place_norm_keys (tìm theo norm_key)

KHÔNG sửa places_dila / places / namevi_map_places. Thuộc tính đều tính lại từ nguồn
READ-ONLY ⇒ apply idempotent; revert = DROP 2 bảng (additive, mất 0 dữ liệu cũ).

CLI:
  python -X utf8 scripts/vn_places_t243_normalize.py --dry-run [--limit N]
  python -X utf8 scripts/vn_places_t243_normalize.py --apply
  python -X utf8 scripts/vn_places_t243_normalize.py --revert
  python -X utf8 scripts/vn_places_t243_normalize.py --db=<path> --apply|--dry-run|--revert
  --report=<path>   đường dẫn JSON report (mặc định data/t243_place_norm_report.json)
"""

import argparse
import json
import os
import sqlite3
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)

try:
    from vn_places_name_utils import load_hanviet_map, place_key_entries, pinyin_available
except ImportError:
    sys.path.insert(0, _HERE)
    from vn_places_name_utils import load_hanviet_map, place_key_entries, pinyin_available

DEFAULT_DB = os.path.join(_DAOANH, 'data', 'lineage.db')
DEFAULT_REPORT = os.path.join(_DAOANH, 'data', 't243_place_norm_report.json')

DDL_KEYS = '''
CREATE TABLE IF NOT EXISTS place_norm_keys (
  rowid    INTEGER PRIMARY KEY,
  dila_id  TEXT NOT NULL,
  name_role TEXT NOT NULL,
  name_text TEXT NOT NULL,
  norm_key TEXT NOT NULL,
  key_kind TEXT NOT NULL,
  hanvi    TEXT,
  pinyin   TEXT,
  district TEXT,
  has_geo  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pnk_dila ON place_norm_keys(dila_id);
CREATE INDEX IF NOT EXISTS idx_pnk_normkey ON place_norm_keys(norm_key);
'''

DDL_FTS = '''
CREATE VIRTUAL TABLE IF NOT EXISTS place_norm_fts USING fts5(
  norm_key, name_text, hanvi, pinyin,
  content='place_norm_keys', content_rowid='rowid'
);
'''

TB_KEYS = 'place_norm_keys'
TB_FTS = 'place_norm_fts'


def ensure_env(conn):
    conn.executescript(DDL_KEYS)
    conn.executescript(DDL_FTS)
    conn.commit()


def read_only_tables_exist(conn):
    """Kiểm places_dila + namevi_map_places có mặt (nguồn đọc)."""
    for t in ('places_dila', 'namevi_map_places', 'hanviet_char_map'):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
        if not row:
            raise RuntimeError('Thiếu bảng nguồn READ-ONLY: %s' % t)


def load_best_vi_names(conn):
    """dila_id → name_vi tốt nhất (MIN = deterministic). ~59k key, Zero-RAM đủ nhỏ."""
    m = {}
    cur = conn.execute(
        'SELECT dila_id, MIN(name_vi) AS name_vi FROM namevi_map_places '
        'WHERE dila_id IS NOT NULL AND dila_id != \'\' '
        'AND name_vi IS NOT NULL AND name_vi != \'\' GROUP BY dila_id')
    for dila_id, name_vi in cur:
        m[dila_id] = name_vi
    return m


def iter_dila_places(conn, limit=None):
    """Generator đọc places_dila từng dòng (Zero-RAM)."""
    sql = ('SELECT id, name, name_zh, district, geo_lat, geo_long '
           'FROM places_dila')
    if limit:
        sql += ' LIMIT %d' % int(limit)
    cur = conn.execute(sql)
    for row in cur:
        yield {
            'id': row[0],
            'name': row[1] or '',
            'name_zh': row[2] or '',
            'district': row[3] or '',
            'geo_lat': row[4],
            'geo_long': row[5],
        }


def build_index(conn, dry_run=False, limit=None):
    """Đọc places_dila + sinh keys (dry_run: đếm không ghi). Trả dict stats."""
    read_only_tables_exist(conn)
    ensure_env(conn)
    if not dry_run:
        # derived table ⇒ rebuild toàn bộ cho idempotent
        conn.execute('DELETE FROM %s' % TB_KEYS)
    hanvi_map = load_hanviet_map(conn)
    vi_names = load_best_vi_names(conn)

    stats = {
        'places_total': 0,
        'places_with_geo': 0,
        'places_with_vi_name': 0,
        'rows_keys': 0,
        'distinct_norm_keys': 0,
        'hanvi_rows': 0,
        'pinyin_rows': 0,
        'suffix_stripped_rows': 0,
        'fts_rows': 0,
    }
    key_set = set()
    batch = []
    t0 = time.time()

    for p in iter_dila_places(conn, limit):
        stats['places_total'] += 1
        if p['geo_lat'] is not None and p['geo_long'] is not None:
            stats['places_with_geo'] += 1
        has_geo = 1 if (p['geo_lat'] is not None and p['geo_long'] is not None) else 0

        roles = [('dila', p['name'])]
        if p['name_zh'] and p['name_zh'] != p['name']:
            roles.append(('dila_zh', p['name_zh']))
        vi = vi_names.get(p['id'])
        if vi and vi not in (p['name'], p['name_zh']):
            roles.append(('vi', vi))
        if vi:
            stats['places_with_vi_name'] += 1

        for role, name in roles:
            make_hanvi = (role == 'dila_zh')
            for rec in place_key_entries(name, hanvi_map=hanvi_map, make_hanvi=make_hanvi):
                stats['rows_keys'] += 1
                if rec['key_kind'] == 'stripped' and rec['norm_key']:
                    stripped_full = vn_full_key(name)
                    if rec['norm_key'] != stripped_full:
                        stats['suffix_stripped_rows'] += 1
                if rec['hanvi']:
                    stats['hanvi_rows'] += 1
                if rec['pinyin']:
                    stats['pinyin_rows'] += 1
                key_set.add(rec['norm_key'])
                if not dry_run:
                    batch.append((p['id'], role, rec['name_text'], rec['norm_key'],
                                  rec['key_kind'], rec['hanvi'], rec['pinyin'],
                                  p['district'], has_geo))
                    if len(batch) >= 2000:
                        conn.executemany(
                            'INSERT INTO %s (dila_id,name_role,name_text,norm_key,key_kind,'
                            'hanvi,pinyin,district,has_geo) VALUES (?,?,?,?,?,?,?,?,?)' % TB_KEYS,
                            batch)
                        batch = []
    if batch and not dry_run:
        conn.executemany(
            'INSERT INTO %s (dila_id,name_role,name_text,norm_key,key_kind,'
            'hanvi,pinyin,district,has_geo) VALUES (?,?,?,?,?,?,?,?,?)' % TB_KEYS,
            batch)

    stats['distinct_norm_keys'] = len(key_set)

    if not dry_run:
        conn.execute("INSERT INTO %s(%s) VALUES('rebuild')" % (TB_FTS, TB_FTS))
        conn.commit()
        stats['fts_rows'] = conn.execute('SELECT COUNT(*) FROM %s' % TB_KEYS).fetchone()[0]
    stats['seconds'] = round(time.time() - t0, 2)
    stats['pinyin_available'] = pinyin_available()
    stats['limit'] = limit
    return stats


def vn_full_key(name):
    from vn_places_name_utils import vn_key
    return vn_key(name, stripped=False)


def revert(conn):
    """Revert additive: DROP 2 bảng tạo bởi T243. Mất 0 dữ liệu cũ."""
    conn.execute('DROP TABLE IF EXISTS %s' % TB_FTS)
    conn.execute('DROP TABLE IF EXISTS %s' % TB_KEYS)
    conn.commit()


def stats_to_report(stats, db_path):
    from vn_places_name_utils import NORMALIZE_FROM_APP
    return {
        'task': 'T243',
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'db': os.path.basename(db_path),
        'normalize_text_from_app': NORMALIZE_FROM_APP,
        'stats': stats,
        'tables': [TB_KEYS, TB_FTS],
        'revert': 'python -X utf8 scripts/vn_places_t243_normalize.py --revert',
    }


def cli():
    ap = argparse.ArgumentParser(description='T243 — Ingest DILA place + chỉ số khóa chuẩn')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--apply', action='store_true', help='Build bảng + FTS (idempotent)')
    g.add_argument('--dry-run', action='store_true', help='Đếm mà không ghi')
    g.add_argument('--revert', action='store_true', help='DROP 2 bảng additive')
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--report', default=DEFAULT_REPORT)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        if args.revert:
            revert(conn)
            print('[OK] T243 revert: đã DROP %s, %s' % (TB_FTS, TB_KEYS))
            return 0
        stats = build_index(conn, dry_run=args.dry_run, limit=args.limit)
        report = stats_to_report(stats, args.db)
        if not args.dry_run:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print('[OK] T243 apply: %s' % args.report)
        else:
            print('[OK] T243 dry-run (không ghi): %s' % json.dumps(stats, ensure_ascii=False))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(cli())