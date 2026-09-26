#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build 2 — Phase A2: Thêm Wikidata vào bảng `data_sources`
===========================================================
Mục đích
--------
T69 wire script chèn EXTERNAL_ID cho Wikidata với source_id=None vì Wikidata không
nằm trong `data_sources` (chỉ nằm trong `source_authority` với score 25, chưa implement).
Additive script này thêm Wikidata vào `data_sources` (source_id=6) để T69 wire có thể
chèn 148 EXTERNAL_ID claims với source_id hợp lệ (không NULL).

Tính chất
---------
- IDEMPOTENT: INSERT OR IGNORE → chạy lại không lỗi, không nhân đôi.
- ADDITIVE: chỉ thêm 1 dòng, KHÔNG sửa/xóa bất kỳ dòng nguồn hiện có.
- REVERSIBLE: xóa dòng vừa thêm bằng lệnh DELETE đơn giản (ghi trong --undo).
- KHÔNG checkpoint/WAL: chỉ INSERT OR IGNORE.

Cách dùng
---------
    python scripts/build2_add_wikidata_to_data_sources.py            # thêm nếu chưa có
    python scripts/build2_add_wikidata_to_data_sources.py --dry-run  # in ra sẽ làm gì
    python scripts/build2_add_wikidata_to_data_sources.py --undo     # xóa dòng Wikidata vừa thêm

Kiểm chứng sau khi chạy
-----------------------
    SELECT source_id, source_code, active FROM data_sources WHERE source_code='Wikidata';
"""
import argparse
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'data/lineage.db'

# source_id=6 = số nguyên tiếp theo sau MAX(5) trong data_sources (không autoincrement)
WIKIDATA_ROW = {
    'source_id': 6,
    'source_code': 'Wikidata',
    'source_name': 'Wikidata (reference)',
    'source_type': 'reference',
    'authority_scope': 'global',
    'license_note': 'CC0',
    'active': 1,
}


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def run(dry_run=False, undo=False):
    conn = connect()
    try:
        ok_cols = [d[1] for d in conn.execute('PRAGMA table_info(data_sources)')]
        missing = [k for k in WIKIDATA_ROW if k not in ok_cols]
        if missing:
            print(f'[A2] LỖI: data_sources thiếu cột {missing} — không đúng schema. Không làm gì.')
            return 1

        # Kiểm tra dòng cũ (repository chưa từng có Wikidata)
        existing = conn.execute(
            "SELECT * FROM data_sources WHERE source_code = ?", (WIKIDATA_ROW['source_code'],)
        ).fetchone()

        if undo:
            if existing:
                # chỉ xóa nếu đúng source_id=6 (dòng do build này thêm)
                if existing['source_id'] == 6:
                    if dry_run:
                        print('[A2][dry-run] Sẽ xóa: source_id=6, source_code=Wikidata')
                    else:
                        conn.execute("DELETE FROM data_sources WHERE source_id = 6")
                        conn.commit()
                        print('[A2] Đã xóa Wikidata khỏi data_sources (source_id=6). Reversible hoàn tất.')
                else:
                    print('[A2] Dòng Wikidata đã có với source_id khác 6 — không xóa (an toàn).')
            else:
                print('[A2] Không tìm thấy Wikidata trong data_sources — không cần xóa.')
            return 0

        if existing:
            print(f'[A2] Wikidata đã có sẵn: source_id={existing["source_id"]} — không thay đổi (idempotent).')
            return 0

        if dry_run:
            print(f'[A2][dry-run] Sẽ INSERT OR IGNORE: {WIKIDATA_ROW}')
            return 0

        cols = ', '.join(WIKIDATA_ROW.keys())
        ph = ', '.join('?' * len(WIKIDATA_ROW))
        conn.execute(
            f"INSERT OR IGNORE INTO data_sources ({cols}) VALUES ({ph})",
            list(WIKIDATA_ROW.values()),
        )
        conn.commit()
        print('[A2] Đã thêm Wikidata vào data_sources: source_id=6, source_code=Wikidata, active=1.')
        print('[A2] Kiểm chứng:')
        for r in conn.execute("SELECT source_id, source_code, source_name, active FROM data_sources WHERE source_code='Wikidata'"):
            print('   ', tuple(r))
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Add Wikidata to data_sources (A2)')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in ra, không thay đổi DB')
    ap.add_argument('--undo', action='store_true', help='xóa dòng Wikidata vừa thêm (revert)')
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, undo=args.undo))
