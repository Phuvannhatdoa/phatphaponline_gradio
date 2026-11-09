# -*- coding: utf-8 -*-
"""
T381d — Gắn DILA ID cho Tứ Tổ Đạo Tín (Admin 2026-11-09).

Việc làm:
  1. dao_tin: dila_id='' -> 'A003654', name_zh='道信', generation_order=31,
     status 'pending' -> 'verified'. (Đời 31 khớp dila_global của A003654 và
     vị trí Tứ Tổ trong BFS Thiền Tông.)
  2. alias_A003654 (trùng cùng DILA ID, status alias_vi_suffix): superseded_by='dao_tin'.
     KHÔNG xóa dòng.

Chế độ:
  python scripts/t381d_dao_tin_dila.py            (mặc định --dry-run)
  python scripts/t381d_dao_tin_dila.py --apply

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


def plan(conn):
    out = []
    r = conn.execute("SELECT dila_id, status FROM vn_person_authority WHERE id='dao_tin'").fetchone()
    if not r:
        out.append("1. dao_tin: KHÔNG TỒN TẠI — dừng")
    elif r[0] == 'A003654' and r[1] == 'verified':
        out.append("1. dao_tin: đã đúng — bỏ qua")
    else:
        out.append(f"1. dao_tin: dila_id '{r[0]}' -> A003654; name_zh -> 道信; "
                   f"generation_order -> 31; status '{r[1]}' -> verified")
    r = conn.execute("SELECT superseded_by FROM vn_person_authority WHERE id='alias_A003654'").fetchone()
    if not r:
        out.append("2. alias_A003654: KHÔNG TỒN TẠI — bỏ qua")
    elif r[0] == 'dao_tin':
        out.append("2. alias_A003654: đã gộp — bỏ qua")
    else:
        out.append(f"2. alias_A003654.superseded_by: {r[0]} -> dao_tin")
    return out


def apply(db):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f"lineage_pre_t381d_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(db, backup)
    print(f"[backup] {backup}")
    conn = sqlite3.connect(db)
    try:
        with conn:
            conn.execute("UPDATE vn_person_authority SET dila_id='A003654', name_zh='道信', "
                         "generation_order=31, status='verified' "
                         "WHERE id='dao_tin' AND (dila_id IS NULL OR dila_id='')")
            conn.execute("UPDATE vn_person_authority SET superseded_by='dao_tin' "
                         "WHERE id='alias_A003654' AND superseded_by IS NULL")
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
