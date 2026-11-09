# -*- coding: utf-8 -*-
"""
T381c — Gỡ liên kết gộp sai: alias_A019985 không phải Ngưu Đầu Pháp Dung.

Lý do: DILA cho thấy A019985 (法融, Đường, Phổ Tịch ở Tung Sơn) là thiền sư mạch Bắc Tông,
không phải Ngưu Đầu Pháp Dung (A003867). T381b đã đặt superseded_by='nguu_dau_phap_dung'
cho alias_A019985 là sai.

Việc làm:
  - alias_A019985.superseded_by: nguu_dau_phap_dung -> NULL (chỉ khi đang đúng giá trị sai đó).
  - Không xóa dòng, không đổi status, không đụng nguu_dau_phap_dung (đã đúng A003867).

Chế độ:
  python scripts/t381c_clear_alias_a019985.py            (mặc định --dry-run)
  python scripts/t381c_clear_alias_a019985.py --apply

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
    r = conn.execute("SELECT superseded_by FROM vn_person_authority WHERE id='alias_A019985'").fetchone()
    if not r:
        return ["alias_A019985: KHÔNG TỒN TẠI — không làm gì"]
    if r[0] is None:
        return ["alias_A019985: superseded_by đã là NULL — không làm gì"]
    if r[0] != 'nguu_dau_phap_dung':
        return [f"alias_A019985: superseded_by = {r[0]} (khác giá trị sai dự kiến) — KHÔNG ghi"]
    return ["alias_A019985.superseded_by: nguu_dau_phap_dung -> NULL"]


def apply(db):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f"lineage_pre_t381c_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(db, backup)
    print(f"[backup] {backup}")
    conn = sqlite3.connect(db)
    try:
        with conn:
            conn.execute("UPDATE vn_person_authority SET superseded_by=NULL "
                         "WHERE id='alias_A019985' AND superseded_by='nguu_dau_phap_dung'")
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
