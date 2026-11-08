# -*- coding: utf-8 -*-
"""
T381 — Xử lý các bản ghi vn_person_authority liên quan đến khai tổ (Admin 2026-11-08).

Việc làm:
  A. Duyệt pending -> verified: vo_ngon_thong (Vô Ngôn Thông), duong_ki_phuong_hoi (Phương Hội A004146).
  B. Gộp trùng lặp (KHÔNG xóa, chỉ đánh dấu superseded_by):
       alias_A001984 -> canonical_A001984 (Quy Sơn Linh Hựu, A001984)
       alias_A003627 -> lam_te_nghia_huyen (Nghĩa Huyền, A003627); bổ sung name_zh 義玄 cho bản chính.
  C. Tạo bản ghi mới (status=pending) cho khai tổ chưa có dòng nào trong bảng:
       tri_khai, dong_son_luong_gioi, tao_son_ban_tich, van_mon_van_yen, phap_nhan_van_ich.
     Riêng Long Thọ (A001482) và Pháp Dung (A003867) KHÔNG tạo mới vì đã có bản ghi
     (bo_tat_long_tho gắn A046539 sai; nguu_dau_phap_dung) — script chỉ báo cáo, Admin quyết định.

Chế độ:
  python scripts/t381_vn_authority_merge.py            (mặc định: --dry-run, chỉ in kế hoạch)
  python scripts/t381_vn_authority_merge.py --apply    (sao lưu -> ghi trong 1 transaction -> integrity_check)

Chạy từ thư mục daoanh/. Không đụng schema, không xóa dòng nào.
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join('data', 'lineage.db')
BACKUP_DIR = os.path.join('data', 'backups')

VERIFY_IDS = ['vo_ngon_thong', 'duong_ki_phuong_hoi']

SUPERSEDE = [
    ('alias_A001984', 'canonical_A001984'),
    ('alias_A003627', 'lam_te_nghia_huyen'),
]

# (id mới, dila_id, ten_viet, doi, is_founder, dharma_lineage)
NEW_ROWS = [
    ('tri_khai', 'A001301', 'Trí Khải', 1, 1, 'Tông phái ngoài Thiền - Thiên Thai (Pháp Hoa)'),
    ('dong_son_luong_gioi', 'A009489', 'Động Sơn Lương Giới', 38, 1, 'Thiền Tông Trung Hoa - Tào Động'),
    ('tao_son_ban_tich', 'A009449', 'Tào Sơn Bản Tịch', 39, 0, 'Thiền Tông Trung Hoa - Tào Động'),
    ('van_mon_van_yen', 'A003703', 'Vân Môn Văn Yển', 39, 1, 'Thiền Tông Trung Hoa - Vân Môn'),
    ('phap_nhan_van_ich', 'A000174', 'Pháp Nhãn Văn Ích', 40, 1, 'Thiền Tông Trung Hoa - Pháp Nhãn'),
]
SKIPPED_ANCHORS = [
    ('A001482', 'Long Thọ', "đã có bo_tat_long_tho (gắn A046539 sai) — Admin quyết định"),
    ('A003867', 'Pháp Dung', "đã có nguu_dau_phap_dung — kiểm tra dila_id rồi quyết định"),
]


def _now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def plan(conn):
    lines = []
    for vid in VERIFY_IDS:
        r = conn.execute("SELECT status FROM vn_person_authority WHERE id=?", (vid,)).fetchone()
        lines.append(f"A. {vid}: {'thiếu' if not r else r[0]} -> verified")
    for old, new in SUPERSEDE:
        lines.append(f"B. {old}.superseded_by = {new}")
    lines.append("B. lam_te_nghia_huyen.name_zh: '' -> '義玄' (nếu đang trống)")
    for nid, dila, name, doi, fnd, lin in NEW_ROWS:
        exists = conn.execute("SELECT 1 FROM vn_person_authority WHERE id=? OR dila_id=?",
                              (nid, dila)).fetchone()
        note = 'BỎ QUA (đã có)' if exists else 'TẠO MỚI'
        lines.append(f"C. {nid} ({dila}, {name}, đời {doi}): {note}")
    for dila, name, why in SKIPPED_ANCHORS:
        lines.append(f"C. {name} ({dila}): KHÔNG tạo — {why}")
    return lines


def apply(conn, db):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f"lineage_pre_t381_vn_authority_{datetime.now():%Y%m%d_%H%M%S}.db")
    conn.close()
    shutil.copy2(db, backup)
    print(f"[backup] {backup}")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            now = _now()
            for vid in VERIFY_IDS:
                conn.execute("UPDATE vn_person_authority SET status='verified' "
                             "WHERE id=? AND status='pending'", (vid,))
            for old, new in SUPERSEDE:
                conn.execute("UPDATE vn_person_authority SET superseded_by=? WHERE id=?", (new, old))
            conn.execute("UPDATE vn_person_authority SET name_zh='義玄' "
                         "WHERE id='lam_te_nghia_huyen' AND (name_zh IS NULL OR name_zh='')")
            for nid, dila, name, doi, fnd, lin in NEW_ROWS:
                if conn.execute("SELECT 1 FROM vn_person_authority WHERE id=? OR dila_id=?",
                                (nid, dila)).fetchone():
                    continue
                zh_row = conn.execute("SELECT name_zh FROM people WHERE id=?", (dila,)).fetchone()
                zh = zh_row[0] if zh_row else None
                conn.execute(
                    "INSERT INTO vn_person_authority (id, ttl_filename, name_vi, name_zh, dharma_lineage, "
                    "generation_order, is_lineage_founder, dila_id, status, created_at, entity_type) "
                    "VALUES (?,?,?,?,?,?,?,?, 'pending', ?, 'monk')",
                    (nid, '', name, zh, lin, doi, fnd, dila, now))
        ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"integrity_check = {ok}")
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
    conn = sqlite3.connect(args.db)
    return apply(conn, args.db)


if __name__ == '__main__':
    sys.exit(main())
