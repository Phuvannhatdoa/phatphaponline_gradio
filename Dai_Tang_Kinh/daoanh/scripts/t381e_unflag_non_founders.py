# -*- coding: utf-8 -*-
"""
T381e — Bỏ cờ khai tổ sai cho hai tổ sư truyền thừa (Admin 2026-11-09).

Thiện Chiêu (phan_duong_thien_chieu) và Sư Phạm (vo_chuan_su_pham) là tổ sư truyền thừa
trong dòng Lâm Tế, KHÔNG phải tổ sư khai phái. Đặt is_lineage_founder = 0.
Không xóa dòng, không đụng dila_id/status/generation_order.

Chế độ:
  python scripts/t381e_unflag_non_founders.py            (mặc định --dry-run)
  python scripts/t381e_unflag_non_founders.py --apply

Chạy từ thư mục daoanh/.
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join('data', 'lineage.db')
BACKUP_DIR = os.path.join('data', 'backups')
IDS = ['phan_duong_thien_chieu', 'vo_chuan_su_pham']


def plan(conn):
    out = []
    for vid in IDS:
        r = conn.execute("SELECT is_lineage_founder FROM vn_person_authority WHERE id=?", (vid,)).fetchone()
        if not r:
            out.append(f"{vid}: KHÔNG TỒN TẠI — bỏ qua")
        elif r[0] == 0:
            out.append(f"{vid}: đã là 0 — bỏ qua")
        else:
            out.append(f"{vid}: is_lineage_founder {r[0]} -> 0")
    return out


def apply(db):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f"lineage_pre_t381e_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(db, backup)
    print(f"[backup] {backup}")
    conn = sqlite3.connect(db)
    try:
        with conn:
            for vid in IDS:
                conn.execute("UPDATE vn_person_authority SET is_lineage_founder=0 "
                             "WHERE id=? AND is_lineage_founder=1", (vid,))
        ok = conn.execute("PRAGMA quick_check").fetchone()[0]
        print(f"quick_check = {ok}")
        return 0 if ok == 'ok' else 1
    finally:
        conn.close()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    p.add_argument('--db', default=DB_PATH)
    args = p.parse_args()
    if not os.path.exists(args.db):
        print(f"Không tìm thấy DB: {args.db}. Chạy từ thư mục daoanh/.")
        return 1
    conn = sqlite3.connect(f'file:{args.db}?mode=ro', uri=True)
    for line in plan(conn):
        print(line)
    conn.close()
    if not args.apply:
        print("DRY-RUN: chưa ghi. Dùng --apply để thực hiện.")
        return 0
    return apply(args.db)


if __name__ == '__main__':
    sys.exit(main())
