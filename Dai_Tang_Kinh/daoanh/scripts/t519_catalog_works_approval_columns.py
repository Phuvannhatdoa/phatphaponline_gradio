#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T519 — Thêm cột duyệt (approval) cho `dila_catalog_works` (additive, idempotent)
=================================================================================
Mục đích
--------
Route POST /daoanh/api/admin/catalog-works/<cbeta_id>/pass (tab Catalog,
admin/namevimap.html) cần ghi lại AI đã duyệt tên Việt và lúc nào. Bảng
`dila_catalog_works` đã có `title_vi` (tên đề xuất), `vi_source`, `vi_status`
nhưng chưa có người duyệt + thời điểm duyệt.

Thêm 2 cột:
  - vi_approved_by  TEXT  (editor đã Pass, mặc định 'admin' nếu không truyền)
  - vi_approved_at  TEXT  (ISO timestamp lúc Pass)

Tính chất
---------
- ADDITIVE: chỉ ALTER TABLE ADD COLUMN, không đổi/drop cột cũ.
- IDEMPOTENT: kiểm tra PRAGMA table_info trước khi ALTER — chạy lại không lỗi.
- KHÔNG backfill — chỉ route /pass mới ghi giá trị cho dòng được duyệt.
- Revert: KHÔNG DROP COLUMN (sqlite3 cũ không hỗ trợ trực tiếp, và DROP có thể
  mất dữ liệu nếu đã có người Pass sau khi chạy script). --revert chỉ XÓA giá
  trị (set NULL) các dòng đã ghi bởi test này, cột giữ nguyên — additive, mất
  0 dữ liệu tên Việt gốc (title_vi không bị đụng tới trừ khi do route /pass ghi).

Cách dùng
---------
    python -X utf8 scripts/t519_catalog_works_approval_columns.py              # ALTER
    python -X utf8 scripts/t519_catalog_works_approval_columns.py --dry-run    # chỉ in
    python -X utf8 scripts/t519_catalog_works_approval_columns.py --revert     # set NULL 2 cột mới (giữ cột)

Kiểm chứng
----------
    PRAGMA table_info(dila_catalog_works);  -- thấy vi_approved_by, vi_approved_at
    SELECT COUNT(*) FROM dila_catalog_works WHERE vi_status='approved';
"""
import argparse
import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/lineage.db'


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_column(conn, table, col):
    return col in {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}


def run(dry_run=False, revert=False):
    conn = connect()
    try:
        try:
            conn.execute("SELECT 1 FROM dila_catalog_works LIMIT 1")
        except sqlite3.OperationalError as e:
            print(f'[T519] LOI: bang dila_catalog_works khong ton tai hoac khong doc duoc: {e}')
            return 1

        if revert:
            cols = {r[1] for r in conn.execute('PRAGMA table_info(dila_catalog_works)')}
            if 'vi_approved_by' not in cols and 'vi_approved_at' not in cols:
                print('[T519][revert] Cot chua ton tai — khong co gi de revert.')
                return 0
            if dry_run:
                n = conn.execute(
                    "SELECT COUNT(*) FROM dila_catalog_works WHERE vi_approved_by IS NOT NULL OR vi_approved_at IS NOT NULL"
                ).fetchone()[0]
                print(f'[T519][dry-run][revert] Se set NULL vi_approved_by/vi_approved_at cho {n} dong (giu cot).')
                return 0
            cur = conn.execute(
                "UPDATE dila_catalog_works SET vi_approved_by = NULL, vi_approved_at = NULL "
                "WHERE vi_approved_by IS NOT NULL OR vi_approved_at IS NOT NULL"
            )
            conn.commit()
            print(f'[T519][revert] Da set NULL cho {cur.rowcount} dong. Cot van giu (additive).')
            return 0

        cols_now = {r[1] for r in conn.execute('PRAGMA table_info(dila_catalog_works)')}
        changed = False
        for col in ('vi_approved_by', 'vi_approved_at'):
            if col in cols_now:
                print(f'[T519] Cot {col} da co — bo qua (idempotent).')
                continue
            if dry_run:
                print(f'[T519][dry-run] Se ALTER: ADD COLUMN {col} TEXT')
            else:
                conn.execute(f'ALTER TABLE dila_catalog_works ADD COLUMN {col} TEXT')
                changed = True
                print(f'[T519] Da ADD COLUMN {col} TEXT')
        if changed:
            conn.commit()
        cols_after = {r[1] for r in conn.execute('PRAGMA table_info(dila_catalog_works)')}
        print('[T519] Cot hien co:', 'vi_approved_by' in cols_after, 'vi_approved_at' in cols_after)
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='T519: add vi_approved_by/vi_approved_at to dila_catalog_works')
    ap.add_argument('--dry-run', action='store_true', help='chi in ra, khong ALTER/UPDATE')
    ap.add_argument('--revert', action='store_true', help='set NULL 2 cot moi (giu cot, khong DROP)')
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, revert=args.revert))
