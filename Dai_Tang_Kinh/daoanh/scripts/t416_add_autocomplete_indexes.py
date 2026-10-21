#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T416 — Thêm index cho autocomplete (DB write, Admin duyệt 2026-10-21).

Index thêm (additive, revert = DROP INDEX, KHÔNG mất dữ liệu):
  - idx_namevi_places_name_vi ON namevi_map_places(name_vi)
  - idx_lexicon_term          ON lexicon(term)

Lý do: route /daoanh/api/public/autocomplete chạy LIKE '%q%' trên 2 bảng này mà
không có index → 170–274 ms/query. places_pending đã xử lý ở code (INDEXED BY hint).

Usage:
    python -X utf8 scripts/t416_add_autocomplete_indexes.py --dry-run
    python -X utf8 scripts/t416_add_autocomplete_indexes.py --apply
    python -X utf8 scripts/t416_add_autocomplete_indexes.py --revert
"""

import argparse
import os
import shutil
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

INDEXES = [
    # Covering index: LIKE '%q%' không seek được, nhưng SQLite quét COVERING INDEX
    # (không đọc bảng) → namevi 147 ms → 70–99 ms. Cột phải gồm đủ cột SELECT
    # (name_vi, dila_id, name_zh) để planner chọn covering scan.
    ('idx_namevi_places_cover', 'namevi_map_places', 'name_vi, dila_id, name_zh'),
    ('idx_lexicon_term', 'lexicon', 'term'),
]

# Index 1 cột cũ không giúp LIKE '%q%' (wildcard đầu) — dọn nếu có.
DROP_LEGACY = ['idx_namevi_places_name_vi']


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def index_exists(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=? LIMIT 1", (name,)
    ).fetchone())


def table_exists(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)
    ).fetchone())


def backup_db():
    ts = time.strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join(BACKUP_DIR, f'T416_{ts}')
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'lineage.db')
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    except Exception:
        pass
    conn.close()
    shutil.copy2(DB_PATH, dst)
    chk = sqlite3.connect(dst)
    ok = chk.execute('PRAGMA quick_check').fetchone()[0]
    chk.close()
    print(f'[backup] {dst} (quick_check={ok})')
    return dst


def dry_run():
    conn = connect()
    for name, table, col in INDEXES:
        t_ok = table_exists(conn, table)
        i_ok = index_exists(conn, name)
        print(f'  {name} ON {table}({col}) — table={"OK" if t_ok else "MISSING"}, '
              f'index={"da co (skip)" if i_ok else "chua co (se tao)"}')
        if t_ok:
            t0 = time.time()
            conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", ('%Thiếu L%',)).fetchone()
            print(f'      LIKE "%Thiếu L%" hien tai: {(time.time()-t0)*1000:.0f} ms')
    conn.close()


def apply():
    backup = backup_db()
    conn = connect()
    for legacy in DROP_LEGACY:
        if index_exists(conn, legacy):
            conn.execute(f'DROP INDEX {legacy}')
            conn.commit()
            print(f'[drop-legacy] {legacy} (1 cot, khong giup LIKE %q%)')
    for name, table, col in INDEXES:
        if not table_exists(conn, table):
            print(f'[skip] bang {table} khong ton tai')
            continue
        if index_exists(conn, name):
            print(f'[skip] {name} da ton tai')
            continue
        t0 = time.time()
        conn.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table}({col})')
        conn.commit()
        print(f'[create] {name} ON {table}({col}) — {(time.time()-t0):.1f}s')
    print('[analyze] ANALYZE 2 bang de cap nhat planner stats...')
    for _, table, _ in INDEXES:
        try:
            conn.execute(f'ANALYZE {table}')
        except Exception as e:
            print('   ANALYZE warn:', e)
    conn.commit()
    conn.close()
    print(f'[backup] Giu cho revert: {backup}')


def revert():
    conn = connect()
    for name, table, col in INDEXES:
        if index_exists(conn, name):
            conn.execute(f'DROP INDEX {name}')
            conn.commit()
            print(f'[drop] {name}')
        else:
            print(f'[skip] {name} khong ton tai')
    conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='T416 — them index autocomplete')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    a = ap.parse_args()
    if a.dry_run:
        dry_run()
    elif a.apply:
        apply()
    else:
        revert()
