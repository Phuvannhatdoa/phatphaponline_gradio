#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T82 — Step 2: Data-Lock Checksum (Zero-RAM streaming)

Tính SHA-256 + row_count cho các bảng lớn để "khoá" dữ liệu, phát hiện regression
sau mỗi phiên build. Tuân Zero-RAM Principle: scan từng dòng, feed vào hasher
tuần tự (byte-offset/streaming), KHÔNG nạp toàn bộ bảng vào RAM.

Ghi/đọc data/checksums.json:
  { "<table>": { "row_count": N, "sha256": "<hex>", "updated_at": "..." } }

Usage:
  python t82_checksum.py              # tính và GHI data/checksums.json (hiện trạng)
  python t82_checksum.py --verify     # đọc lại DB + so với file -> phát hiện thay đổi
  python t82_checksum.py --list       # liệt kê bảng cần khoá
"""

import sys
import os
import json
import hashlib
import argparse
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
SUM_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\checksums.json'

# Bảng lớn / quan trọng cần khoá (tăng dần khi cần)
TABLES = [
    'people',
    'places',
    'places_dila',
    'place_timeline_events',
    'vn_person_events',
    'place_person_bibl',
    'entity_claims',
]


def table_exists(conn, table):
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return c.fetchone() is not None


def row_key(conn, table):
    """Trả tên cột PK nếu có (để iteration ổn định), else cột đầu tiên / rowid."""
    c = conn.cursor()
    c.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in c.fetchall()]
    if 'id' in cols:
        return 'id'
    return cols[0] if cols else None


def checksum_table(conn, table):
    """Streaming checksum: iterate rows, hash canonical JSON per row."""
    c = conn.cursor()
    c.execute(f'SELECT * FROM "{table}"')
    h = hashlib.sha256()
    row_count = 0
    while True:
        rows = c.fetchmany(1000)
        if not rows:
            break
        for row in rows:
            # canonical encode: repr of tuple (bytes-safe cho None/int/float/str)
            h.update(repr(row).encode('utf-8', errors='replace'))
            h.update(b'\n')
            row_count += 1
    return row_count, h.hexdigest()


def compute(conn):
    result = {}
    for table in TABLES:
        if not table_exists(conn, table):
            print(f"  [SKIP] bảng không tồn tại: {table}")
            continue
        cnt, digest = checksum_table(conn, table)
        result[table] = {'row_count': cnt, 'sha256': digest,
                         'updated_at': datetime.now().isoformat(timespec='seconds')}
        print(f"  {table}: {cnt} rows, sha256={digest[:16]}...")
    return result


def main():
    parser = argparse.ArgumentParser(description='T82 Step2: Data-Lock Checksum')
    parser.add_argument('--verify', action='store_true', help='So sánh DB hiện tại với checksums.json')
    parser.add_argument('--list', action='store_true', help='Liệt kê bảng cần khoá')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.list:
        print("Bảng cần khoá (Data-Lock):")
        for t in TABLES:
            print(f"  {t}")
        conn.close()
        return

    if args.verify:
        if not os.path.isfile(SUM_PATH):
            print(f"[ERR] Không có {SUM_PATH}. Chạy `python t82_checksum.py` trước để tạo baseline.")
            conn.close()
            return 1
        with open(SUM_PATH, encoding='utf-8') as f:
            data = json.load(f)
        saved = data.get('tables', data)  # hỗ trợ cả cấu trúc cũ lẫn mới
        print("=== VERIFY: DB hiện tại vs checksums.json ===")
        all_ok = True
        for table in TABLES:
            if table not in saved:
                print(f"  [SKIP] {table}: không có trong checksums.json")
                continue
            if not table_exists(conn, table):
                print(f"  [CHANGED] {table}: bảng không còn tồn tại!")
                all_ok = False
                continue
            cnt, digest = checksum_table(conn, table)
            s = saved[table]
            if cnt == s['row_count'] and digest == s['sha256']:
                print(f"  [OK] {table}: {cnt} rows, sha256={digest[:12]}... (khớp)")
            else:
                all_ok = False
                print(f"  [CHANGED] {table}: saved({s['row_count']}, {s['sha256'][:12]}...) "
                      f"vs current({cnt}, {digest[:12]}...) — DỮ LIỆU ĐÃ THAY ĐỔI")
        print("\n" + ("ALL CHECKS PASSED (data locked)" if all_ok else "DATA CHANGED — review regression!"))
        conn.close()
        return 0 if all_ok else 1

    # default: compute + ghi file
    print("=== TÍNH CHECKSUM (streaming zero-RAM) ===")
    result = compute(conn)
    out = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'method': 'sha256-streaming-rowwise',
        'db': os.path.basename(DB_PATH),
        'tables': result,
    }
    with open(SUM_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Đã ghi {SUM_PATH} ({len(result)} bảng)")
    conn.close()


if __name__ == '__main__':
    sys.exit(main())
