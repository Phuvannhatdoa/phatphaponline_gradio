#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T380 — Bảng số đời nhập tay (Admin duyệt 2026-11-08: "Đồng ý thêm hai bảng").

Thêm 2 bảng MỚI (additive, không đụng bảng cũ):
  - person_generation_manual          : số đời Admin nhập tay, khóa (person_id, lineage_founder_dila_id)
  - person_generation_manual_history  : nhật ký mọi thay đổi (thêm / sửa / xóa)

Hai bảng này KHÔNG nằm trong danh sách DROP của scripts/etl_gen_compute.py
(ETL chỉ DROP lineage_founders và person_gen_computed), nên ETL chạy lại không xóa nhập tay.

Modes:
  --dry-run (MẶC ĐỊNH)  Chỉ đọc, in DDL sẽ chạy, không ghi DB.
  --apply               Backup (shutil.copy2) -> CREATE TABLE IF NOT EXISTS x2 + index,
                        trong 1 transaction. PRAGMA integrity_check sau commit.
  --revert              DROP 2 bảng mới. Từ chối nếu đã có dòng nhập tay (để tránh mất dữ liệu
                        Admin đã nhập; khi đó khôi phục từ file backup).

Dùng DB đường dẫn mặc định data/lineage.db (chạy từ thư mục daoanh/).
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join('data', 'lineage.db')
BACKUP_DIR = os.path.join('data', 'backups')

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

NEW_TABLES = ['person_generation_manual', 'person_generation_manual_history']


def table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def row_count(conn, name):
    return conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]


def dry_run(db):
    conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    print('=== T380 manual-generation DRY-RUN (chỉ đọc) ===')
    print(f'DB: {db}')
    for t in NEW_TABLES:
        print(f'  {t}: đã tồn tại = {table_exists(conn, t)}')
    print('DDL sẽ chạy khi --apply:')
    for ddl in MANUAL_DDL:
        print('  ' + ' '.join(ddl.split()))
    conn.close()


def apply(db):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = os.path.join(BACKUP_DIR, f'lineage_pre_t380_{stamp}.db')
    print(f'[backup] {backup}')
    shutil.copy2(db, backup)
    conn = sqlite3.connect(db)
    try:
        with conn:  # 1 transaction
            for ddl in MANUAL_DDL:
                conn.execute(ddl)
        ok = conn.execute('PRAGMA integrity_check').fetchone()[0]
        print(f'[apply] integrity_check = {ok}')
        for t in NEW_TABLES:
            print(f'  {t}: {row_count(conn, t)} dòng')
        if ok != 'ok':
            print('[apply] CẢNH BÁO: integrity_check không ok — khôi phục từ backup.')
            return 1
    finally:
        conn.close()
    print(f'[apply] Hoàn tất. Backup giữ để revert: {backup}')
    return 0


def revert(db):
    conn = sqlite3.connect(db)
    try:
        n = sum(row_count(conn, t) for t in NEW_TABLES if table_exists(conn, t))
        if n:
            print(f'[revert] TỪ CHỐI: đã có {n} dòng nhập tay/nhật ký. Không DROP để tránh mất dữ liệu.')
            return 1
        with conn:
            for t in NEW_TABLES:
                conn.execute(f'DROP TABLE IF EXISTS {t}')
        print('[revert] Đã DROP 2 bảng T380 (không có dữ liệu).')
        return 0
    finally:
        conn.close()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    p.add_argument('--db', default=DB_PATH)
    args = p.parse_args()
    if args.apply:
        return apply(args.db)
    if args.revert:
        return revert(args.db)
    dry_run(args.db)
    return 0


if __name__ == '__main__':
    sys.exit(main())
