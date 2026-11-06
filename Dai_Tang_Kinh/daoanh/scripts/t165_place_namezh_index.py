# -*- coding: utf-8 -*-
"""t165_place_namezh_index.py — T165 + index cho tab Place — thêm index name_zh
=================================================================================
Bối cảnh: GET /daoanh/api/dila/places chạy 2 correlated subquery trên
`namevi_map_places` lọc theo `name_zh` cho mỗi dòng `places_dila` trả về
(app.py ~9478-9491). Index hiện có `idx_namevi_places_cover(name_vi, dila_id,
name_zh)` không giúp vì `name_zh` không phải cột dẫn đầu (leading column).

Thêm 1 index additive, KHÔNG đổi dữ liệu:
    CREATE INDEX IF NOT EXISTS idx_namevi_places_name_zh
    ON namevi_map_places(name_zh)

Idempotent (CREATE INDEX IF NOT EXISTS). Backup tự động trước --apply.
Usage:
    python scripts/t165_place_namezh_index.py --stats      # đọc trạng thái (0 apply)
    python scripts/t165_place_namezh_index.py --dry-run    # in SQL + backup path (0 apply)
    python scripts/t165_place_namezh_index.py --apply      # backup + CREATE INDEX
    python scripts/t165_place_namezh_index.py --revert     # DROP INDEX (rollback)
"""
import argparse
import os
import sqlite3
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

INDEX_NAME = 'idx_namevi_places_name_zh'
INDEX_DDL = f'CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON namevi_map_places(name_zh)'


def _index_exists(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (name,)
    ).fetchone())


def _backup_path():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return os.path.join(BACKUP_DIR, f'lineage_t165idx_{datetime.datetime.now():%Y%m%d_%H%M%S}.db')


def _make_backup(conn):
    path = _backup_path()
    dst = sqlite3.connect(path)
    try:
        conn.backup(dst)
    finally:
        dst.close()
    return path


def _stats(conn):
    print('=== namevi_map_places — index stats ===')
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='namevi_map_places'"
    ).fetchall()
    for name, sql in rows:
        print(f'  {name}: {sql}')
    print(f'\n  [{"OK  " if _index_exists(conn, INDEX_NAME) else "MISS"}] {INDEX_NAME}')
    n = conn.execute('SELECT COUNT(*) FROM namevi_map_places').fetchone()[0]
    print(f'\n  namevi_map_places rows: {n}')


def _apply(conn):
    backup = _make_backup(conn)
    print(f'[backup] {backup}')
    if _index_exists(conn, INDEX_NAME):
        print(f'[skip ] {INDEX_NAME} đã tồn tại')
    else:
        conn.execute(INDEX_DDL)
        conn.commit()
        print(f'[add  ] {INDEX_NAME}')
    return backup


def _revert(conn):
    if _index_exists(conn, INDEX_NAME):
        conn.execute(f'DROP INDEX IF EXISTS {INDEX_NAME}')
        conn.commit()
        print(f'[drop ] {INDEX_NAME}')
    else:
        print(f'[skip ] {INDEX_NAME} không tồn tại')


def main():
    ap = argparse.ArgumentParser(description='T165 — index name_zh cho namevi_map_places (additive)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--stats', action='store_true')
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    ap.add_argument('--db', default=None, help='DB path khác (test trên copy). Default: data/lineage.db')
    args = ap.parse_args()
    if args.db:
        global DB_PATH, BACKUP_DIR
        DB_PATH = args.db
        # Backup phải nằm cạnh DB THẬT (data/backups của đúng cây chứa DB này),
        # không phải cạnh vị trí file script (có thể ở worktree khác).
        BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(DB_PATH)), 'backups')

    if not os.path.exists(DB_PATH):
        print(f'LỖI: không tìm thấy DB {DB_PATH}')
        sys.exit(1)

    if args.stats or args.dry_run:
        conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        try:
            _stats(conn)
            if args.dry_run:
                print('\n[SQL plan]')
                mark = 'skip' if _index_exists(conn, INDEX_NAME) else 'run '
                print(f'  {mark}  {INDEX_DDL}')
                print(f'  backup → {_backup_path()}')
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        if args.apply:
            print(f'[--apply] opening: {DB_PATH}')
            backup = _apply(conn)
            print(f'BACKUP_PATH={backup}')
            _stats(conn)
        elif args.revert:
            print(f'[--revert] opening: {DB_PATH}')
            _revert(conn)
            _stats(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
