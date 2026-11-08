# -*- coding: utf-8 -*-
"""
T381b — Sửa liên kết DILA ID sai cho Long Thọ và Pháp Dung trong vn_person_authority (Admin 2026-11-08).

Việc làm:
  1. Long Thọ: bo_tat_long_tho đang gắn A046539 (隆壽, SAI). Đổi dila_id -> A001482 (龍樹),
     name_zh -> 龍樹 cho khớp anchor Tam Luận.
  2. Pháp Dung: nguu_dau_phap_dung đang gắn A018085 (法融). Anchor Ngưu Đầu dùng A003867 (法融,
     DILA xác nhận khai tổ). Đổi dila_id -> A003867.
     alias_A019985 (A019985, 法融) trỏ về nguu_dau_phap_dung (superseded_by), không xóa.
     A018085 và A019985 là DILA ID khác, không xóa; ghi chú để Admin xem sau.

Không xóa dòng nào, không đổi schema. Sao lưu DB trước khi ghi, ghi trong 1 transaction.

Chế độ:
  python scripts/t381b_fix_long_tho_phap_dung.py            (mặc định --dry-run)
  python scripts/t381b_fix_long_tho_phap_dung.py --apply

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
    r = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id='bo_tat_long_tho'").fetchone()
    if not r:
        out.append("1. bo_tat_long_tho: KHÔNG TỒN TẠI — bỏ qua")
    elif r[0] == 'A001482':
        out.append("1. bo_tat_long_tho: đã đúng A001482 — bỏ qua")
    else:
        out.append(f"1. bo_tat_long_tho: dila_id {r[0]} -> A001482; name_zh -> 龍樹")
    r = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id='nguu_dau_phap_dung'").fetchone()
    if not r:
        out.append("2. nguu_dau_phap_dung: KHÔNG TỒN TẠI — bỏ qua")
    elif r[0] == 'A003867':
        out.append("2. nguu_dau_phap_dung: đã đúng A003867 — bỏ qua")
    else:
        out.append(f"2. nguu_dau_phap_dung: dila_id {r[0]} -> A003867")
    out.append("2. alias_A019985.superseded_by = nguu_dau_phap_dung")
    return out


def apply(db):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f"lineage_pre_t381b_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(db, backup)
    print(f"[backup] {backup}")
    conn = sqlite3.connect(db)
    try:
        with conn:
            conn.execute("UPDATE vn_person_authority SET dila_id='A001482', name_zh='龍樹' "
                         "WHERE id='bo_tat_long_tho' AND dila_id='A046539'")
            conn.execute("UPDATE vn_person_authority SET dila_id='A003867' "
                         "WHERE id='nguu_dau_phap_dung' AND dila_id='A018085'")
            conn.execute("UPDATE vn_person_authority SET superseded_by='nguu_dau_phap_dung' "
                         "WHERE id='alias_A019985'")
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
