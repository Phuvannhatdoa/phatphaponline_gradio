# -*- coding: utf-8 -*-
"""t200_canonical_name_row.py — T200: thêm dòng canonical cho A001984 vào vn_person_authority.

Bối cảnh: A001984 chỉ có dòng alias (alias_A001984, name_vi='Linh Hựu', status='alias_vi_suffix').
Test tests/test_t200_vnpa_tiebreak.py (mục 7 "DB that") kỳ vọng lookup_by_dila('A001984')
trả 'Quy Sơn Linh Hựu' (tên đầy đủ, lấy từ people.name_vi — DB thắng).

Thay đổi (ADDITIVE, +1 dòng, KHÔNG sửa/xoá dòng nào khác, KHÔNG đụng bảng people):
    INSERT INTO vn_person_authority (id, ttl_filename, name_vi, name_zh, dila_id,
                                     status, entity_type, created_at)
    VALUES ('canonical_A001984', <ttl từ alias>, <people.name_vi>, <people.name_zh>,
            'A001984', 'auto_ttl', 'monk', CURRENT_TIMESTAMP)

Status = 'auto_ttl' (rank 2 trong vnpa_lookup.VNPA_STATUS_RANK): nguồn là TTL + DILA;
thắng alias_vi_suffix (rank 3) nên lookup trả dòng canonical.

Usage:
    python -X utf8 scripts/t200_canonical_name_row.py --dry-run   # in SQL kế hoạch + backup path (0 ghi)
    python -X utf8 scripts/t200_canonical_name_row.py --apply     # backup + INSERT 1 dòng (idempotent)
    python -X utf8 scripts/t200_canonical_name_row.py --revert    # backup + DELETE đúng dòng canonical

REVERT:
    1) python -X utf8 scripts/t200_canonical_name_row.py --revert
    2) hoặc khôi phục backup: data/backups/lineage_t200_<YYYYmmdd_HHMMSS>.db
"""
import argparse
import datetime
import os
import sqlite3
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

DILA_ID = 'A001984'
ALIAS_ID = 'alias_A001984'
CANON_ID = 'canonical_A001984'
CANON_STATUS = 'auto_ttl'
CANON_ENTITY = 'monk'


def _backup_path():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return os.path.join(BACKUP_DIR,
                        f'lineage_t200_{datetime.datetime.now():%Y%m%d_%H%M%S}.db')


def _make_backup(conn):
    """Backup bằng sqlite backup API — PHẢI gọi trước mọi lệnh ghi."""
    path = _backup_path()
    dst = sqlite3.connect(path)
    try:
        conn.backup(dst)
    finally:
        dst.close()
    return path


def _read_source(conn):
    """Lấy name_vi/name_zh từ people (DB thắng) + ttl_filename từ dòng alias."""
    p = conn.execute(
        "SELECT name_vi, name_zh FROM people WHERE id=?", (DILA_ID,)).fetchone()
    if not p or not p[0]:
        raise SystemExit(f'LỖI: people.id={DILA_ID} không có name_vi — dừng.')
    a = conn.execute(
        "SELECT ttl_filename FROM vn_person_authority WHERE id=?", (ALIAS_ID,)).fetchone()
    if not a or not a[0]:
        raise SystemExit(f'LỖI: không có dòng alias {ALIAS_ID} (ttl_filename) — dừng.')
    return {'name_vi': p[0], 'name_zh': p[1], 'ttl_filename': a[0]}


def _canon_rows(conn):
    return conn.execute(
        "SELECT id, name_vi, name_zh, dila_id, status, ttl_filename "
        "FROM vn_person_authority WHERE dila_id=? ORDER BY id", (DILA_ID,)).fetchall()


def _count(conn):
    return conn.execute("SELECT COUNT(*) FROM vn_person_authority").fetchone()[0]


def _sql_plan(src):
    """SQL kế hoạch (chỉ để in; apply dùng tham số hoá cùng cấu trúc)."""
    return [
        ("INSERT", (
            "INSERT INTO vn_person_authority "
            "(id, ttl_filename, name_vi, name_zh, dila_id, status, entity_type, created_at) "
            f"VALUES ('{CANON_ID}', '{src['ttl_filename']}', '{src['name_vi']}', "
            f"'{src['name_zh']}', '{DILA_ID}', '{CANON_STATUS}', '{CANON_ENTITY}', "
            "CURRENT_TIMESTAMP);")),
    ]


def _revert_sql():
    return (f"DELETE FROM vn_person_authority "
            f"WHERE id='{CANON_ID}' AND dila_id='{DILA_ID}';")


def _print_rows(conn):
    for r in _canon_rows(conn):
        print(f'  {r}')


def _dry_run(conn):
    src = _read_source(conn)
    print('=== T200 dry-run (0 ghi) ===')
    print(f'  DB: {DB_PATH}')
    print(f'  vn_person_authority số dòng hiện tại: {_count(conn)}')
    print(f'  dòng dila_id={DILA_ID} hiện tại:')
    _print_rows(conn)
    exists = conn.execute(
        "SELECT 1 FROM vn_person_authority WHERE id=?", (CANON_ID,)).fetchone()
    print('\n[SQL plan]')
    for kind, sql in _sql_plan(src):
        mark = 'skip (đã có)' if exists else 'run '
        print(f'  {mark}  {sql}')
    print(f'\n  revert: {_revert_sql()}')
    print(f'\n  backup → {_backup_path()}')


def _apply(conn):
    src = _read_source(conn)
    backup = _make_backup(conn)
    print(f'  backup → {backup}')
    before = _count(conn)
    print(f'  số dòng trước: {before}')

    conn.isolation_level = None  # tự quản transaction
    conn.execute('BEGIN IMMEDIATE')
    try:
        exists = conn.execute(
            "SELECT 1 FROM vn_person_authority WHERE id=?", (CANON_ID,)).fetchone()
        if exists:
            print(f'  SKIP {CANON_ID} (đã có — idempotent)')
        else:
            conn.execute(
                "INSERT INTO vn_person_authority "
                "(id, ttl_filename, name_vi, name_zh, dila_id, status, entity_type, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (CANON_ID, src['ttl_filename'], src['name_vi'], src['name_zh'],
                 DILA_ID, CANON_STATUS, CANON_ENTITY))
            print(f'  INSERT {CANON_ID}')
        conn.execute('COMMIT')
    except Exception:
        conn.execute('ROLLBACK')
        raise

    after = _count(conn)
    print(f'  số dòng sau: {after} (chênh lệch {after - before:+d})')
    return backup


def _revert(conn):
    backup = _make_backup(conn)
    print(f'  backup → {backup}')
    before = _count(conn)
    conn.isolation_level = None
    conn.execute('BEGIN IMMEDIATE')
    try:
        cur = conn.execute(
            "DELETE FROM vn_person_authority WHERE id=? AND dila_id=?",
            (CANON_ID, DILA_ID))
        print(f'  DELETE {CANON_ID}: {cur.rowcount} dòng (dòng alias KHÔNG bị xoá)')
        conn.execute('COMMIT')
    except Exception:
        conn.execute('ROLLBACK')
        raise
    after = _count(conn)
    print(f'  số dòng: {before} → {after}')
    return backup


def main():
    ap = argparse.ArgumentParser(
        description='T200: thêm dòng canonical A001984 vào vn_person_authority (additive)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true',
                   help='In SQL kế hoạch + backup path (0 ghi)')
    g.add_argument('--apply', action='store_true',
                   help='Backup + INSERT 1 dòng canonical (idempotent)')
    g.add_argument('--revert', action='store_true',
                   help='Backup + DELETE đúng dòng canonical (không đụng alias)')
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(f'LỖI: không tìm thấy DB {DB_PATH}')
        sys.exit(1)

    if args.dry_run:
        conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        try:
            _dry_run(conn)
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        if args.apply:
            print(f'[T200 --apply] opening: {DB_PATH}')
            backup = _apply(conn)
            print(f'BACKUP_PATH={backup}')
        elif args.revert:
            print(f'[T200 --revert] opening: {DB_PATH}')
            backup = _revert(conn)
            print(f'BACKUP_PATH={backup}')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
