# -*- coding: utf-8 -*-
"""t166_identity_migrate.py — T166 Canonical Identity Hard Guard: schema migration (additive).

Usage:
    python -X utf8 scripts/t166_identity_migrate.py --stats     # đọc trạng thái hiện tại (0 apply)
    python -X utf8 scripts/t166_identity_migrate.py --dry-run   # in SQL + backup path (0 apply)
    python -X utf8 scripts/t166_identity_migrate.py --apply     # backup + ADD cột + index
    python -X utf8 scripts/t166_identity_migrate.py --revert    # DROP cột + index (rollback schema)

KHÔNG DROP dữ liệu. KHÔNG gán `identity_status` cho row cũ (NULL = legacy = pass,
không đoán lịch sử — SPEC T166 §8.5).

REVERT:
    1) python -X utf8 scripts/t166_identity_migrate.py --revert
    2) hoặc khôi phục backup: data/backups/lineage_t166_<YYYYmmdd_HHMMSS>.db
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

# ── Cột mới (additive) ────────────────────────────────────────────────────
# translation_cache: cờ identity + chi tiết lỗi + fingerprint lock
CACHE_COLS = ('identity_status', 'identity_issues', 'identity_lock_hash')
# translation_rules: policy unknown P-PARTIAL | P-STOP (Admin đổi được)
RULES_COLS = ('identity_lock_policy',)
INDEX_DDL = ("CREATE INDEX IF NOT EXISTS idx_tc_identity "
             "ON translation_cache(identity_status)")

# Enum hợp lệ (SPEC §8.5) — NULL = legacy pass
VALID_IDENTITY_STATUS = ('pass', 'review_required', 'failed', 'conflict')
VALID_POLICY = ('P-PARTIAL', 'P-STOP')


def _col_exists(conn, table, col):
    try:
        return any(r[1] == col for r in conn.execute(f'PRAGMA table_info({table})'))
    except sqlite3.Error:
        return False


def _table_exists(conn, table):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone())


def _index_exists(conn, index):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (index,)
    ).fetchone())


def _sql_plan():
    """Kế hoạch ADD: [(table, col, ddl), ...] — dùng cho cả apply và revert."""
    plan = []
    for col in CACHE_COLS:
        plan.append(('translation_cache', col,
                     f'ALTER TABLE translation_cache ADD COLUMN {col} TEXT'))
    for col in RULES_COLS:
        plan.append(('translation_rules', col,
                     f"ALTER TABLE translation_rules ADD COLUMN {col} TEXT "
                     f"DEFAULT 'P-PARTIAL'"))
    return plan


def _backup_path():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return os.path.join(BACKUP_DIR,
                        f'lineage_t166_{datetime.datetime.now():%Y%m%d_%H%M%S}.db')


def _make_backup(conn):
    """Backup bằng sqlite backup API (an toàn khi DB đang mở)."""
    path = _backup_path()
    dst = sqlite3.connect(path)
    try:
        conn.backup(dst)
    finally:
        dst.close()
    return path


def _stats(conn):
    print('=== T166 identity schema ===')
    for table in ('translation_cache', 'translation_rules'):
        if not _table_exists(conn, table):
            print(f'  {table}: KHÔNG tồn tại (bỏ qua)')
            continue
        cols = CACHE_COLS if table == 'translation_cache' else RULES_COLS
        for col in cols:
            mark = 'OK  ' if _col_exists(conn, table, col) else 'MISS'
            print(f'  [{mark}] {table}.{col}')

    if _col_exists(conn, 'translation_cache', 'identity_status'):
        print('\n=== identity_status distribution ===')
        rows = conn.execute(
            "SELECT COALESCE(identity_status,'(NULL=legacy pass)') s, COUNT(*) n "
            "FROM translation_cache GROUP BY s ORDER BY n DESC"
        ).fetchall()
        for s, n in rows:
            print(f'  {s:24s} {n:>6}')

    if _col_exists(conn, 'translation_rules', 'identity_lock_policy'):
        print('\n=== identity_lock_policy distribution ===')
        try:
            rows = conn.execute(
                "SELECT COALESCE(identity_lock_policy,'(NULL=default)') p, COUNT(*) n "
                "FROM translation_rules GROUP BY p ORDER BY n DESC"
            ).fetchall()
            for p, n in rows:
                print(f'  {p:24s} {n:>6}')
        except sqlite3.Error as exc:
            print(f'  (không đọc được: {exc})')

    if _index_exists(conn, 'idx_tc_identity'):
        print('\n  [OK  ] index idx_tc_identity')
    else:
        print('\n  [MISS] index idx_tc_identity')

    # Tổng cache row — để đánh giá mass-miss khi bật fingerprint
    if _table_exists(conn, 'translation_cache'):
        total = conn.execute("SELECT COUNT(*) FROM translation_cache").fetchone()[0]
        with_hash = 0
        if _col_exists(conn, 'translation_cache', 'constitution_hash'):
            with_hash = conn.execute(
                "SELECT COUNT(*) FROM translation_cache "
                "WHERE constitution_hash IS NOT NULL"
            ).fetchone()[0]
        print(f'\n  translation_cache: {total} row '
              f'({with_hash} có constitution_hash) — baseline cho mass-miss T166 §9')


def _apply(conn):
    backup = _make_backup(conn)
    print(f'  backup → {backup}')

    for table, col, ddl in _sql_plan():
        if not _table_exists(conn, table):
            print(f'  SKIP {table} (không tồn tại)')
            continue
        if _col_exists(conn, table, col):
            print(f'  SKIP {table}.{col} (đã có)')
            continue
        conn.execute(ddl)
        print(f'  ADD  {table}.{col}')

    if not _index_exists(conn, 'idx_tc_identity'):
        conn.execute(INDEX_DDL)
        print('  ADD  index idx_tc_identity')

    conn.commit()
    return backup


def _revert(conn):
    if _index_exists(conn, 'idx_tc_identity'):
        conn.execute('DROP INDEX IF EXISTS idx_tc_identity')
        print('  DROP index idx_tc_identity')

    for table, col, _ddl in reversed(_sql_plan()):
        if not _table_exists(conn, table) or not _col_exists(conn, table, col):
            print(f'  SKIP {table}.{col} (không có)')
            continue
        # SQLite >= 3.35 hỗ trợ DROP COLUMN; fallback = khôi phục backup
        try:
            conn.execute(f'ALTER TABLE {table} DROP COLUMN {col}')
            print(f'  DROP {table}.{col}')
        except sqlite3.Error as exc:
            print(f'  FAIL {table}.{col}: {exc}')
            print('        → SQLite < 3.35: khôi phục backup thủ công')
    conn.commit()


def main():
    ap = argparse.ArgumentParser(
        description='T166 identity schema migration (additive)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--stats', action='store_true',
                   help='In trạng thái hiện tại (0 apply)')
    g.add_argument('--dry-run', action='store_true',
                   help='In kế hoạch SQL + backup path (0 apply)')
    g.add_argument('--apply', action='store_true',
                   help='Backup + ADD cột + index')
    g.add_argument('--revert', action='store_true',
                   help='DROP cột + index (rollback schema)')
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(f'LỖI: không tìm thấy DB {DB_PATH}')
        sys.exit(1)

    if args.stats or args.dry_run:
        conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        try:
            _stats(conn)
            if args.dry_run:
                print('\n[SQL plan]')
                for table, col, ddl in _sql_plan():
                    mark = 'skip' if _col_exists(conn, table, col) else 'run '
                    print(f'  {mark}  {ddl}')
                mark = 'skip' if _index_exists(conn, 'idx_tc_identity') else 'run '
                print(f'  {mark}  {INDEX_DDL}')
                print(f'\n  backup → {_backup_path()}')
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        if args.apply:
            print(f'[T166 --apply] opening: {DB_PATH}')
            backup = _apply(conn)
            print(f'BACKUP_PATH={backup}')
            _stats(conn)
        elif args.revert:
            print(f'[T166 --revert] opening: {DB_PATH}')
            _revert(conn)
            _stats(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
