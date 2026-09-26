#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build 2 — Phase B: thêm cột provenance vào `entity_claims` (additive, idempotent)
=================================================================================
Mục đích
--------
Bổ sung 2 cột `source_url` và `retrieved_at` cho `entity_claims` để lưu dấu vết
nguồn (source URL + thời điểm lấy dữ liệu) — yêu cầu evidence-layer của TGS Build 2.

Tính chất
---------
- ADDITIVE: chỉ `ALTER TABLE ADD COLUMN` (không đổi/drop cột cũ, không đụng bảng nguồn).
- IDEMPOTENT: kiểm tra `PRAGMA table_info` trước khi ALTER → chạy lại không lỗi/nhân đôi.
- NONDESTRUCTIVE backfill: chỉ điền `source_url` cho Wikidata EXTERNAL_ID (Q-…, URL rõ ràng),
  KHÔNG ghi đè dữ liệu sẵn có.
- DB KHÔNG drop/rename; reversible bằng cách bỏ qua cột mới (app chỉ đọc cột mới nếu có) hoặc restore backup.

Cách dùng
---------
    python scripts/build2_add_evidence_provenance_columns.py            # ALTER + backfill
    python scripts/build2_add_evidence_provenance_columns.py --dry-run  # chỉ in, không ALTER
    python scripts/build2_add_evidence_provenance_columns.py --undo     # xóa backfill (giữ cột)

Kiểm chứng
----------
    SELECT source_id, COUNT(*) FROM entity_claims WHERE source_url IS NOT NULL GROUP BY source_id;
"""
import argparse
import re
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'data/lineage.db'


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_column(conn, table, col):
    return col in {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}


def backfill_wikidata_urls(conn, dry_run):
    """Điền source_url cho EXTERNAL_ID Wikidata dạng 'T69:wikidata:Q12345'."""
    # Cột source_url có thể chưa tồn tại (dry-run không ALTER) → guard filter.
    src_url_clause = "AND (source_url IS NULL OR source_url='')" if has_column(conn, 'entity_claims', 'source_url') else ""
    rows = conn.execute(
        f"SELECT claim_id, source_reference FROM entity_claims "
        f"WHERE claim_type='EXTERNAL_ID' AND source_reference LIKE 'T69:wikidata:%' {src_url_clause}"
    ).fetchall()
    todo = []
    for r in rows:
        m = re.search(r'Q\d+', r['source_reference'])
        if m:
            url = f"https://www.wikidata.org/wiki/{m.group(0)}"
            todo.append((url, r['claim_id']))
    if dry_run:
        print(f'[B][dry-run] Sẽ backfill source_url cho {len(todo)} Wikidata EXTERNAL_ID claims.')
        return 0
    conn.executemany("UPDATE entity_claims SET source_url = ? WHERE claim_id = ?", todo)
    conn.commit()
    print(f'[B] Backfill xong source_url cho {len(todo)} Wikidata EXTERNAL_ID claims.')
    return len(todo)


def run(dry_run=False, undo=False):
    conn = connect()
    try:
        cols_now = {r[1] for r in conn.execute('PRAGMA table_info(entity_claims)')}

        if undo:
            # Reversible: chỉ xóa backfill (giữ cột). Cột là additive nên không cần DROP.
            n = conn.execute(
                "UPDATE entity_claims SET source_url = NULL WHERE claim_type='EXTERNAL_ID'"
            ).rowcount if not dry_run else 0
            if not dry_run:
                conn.commit()
                print(f'[B][undo] Đã xóa backfill source_url ({n} rows). Cột giữ nguyên (additive).')
            else:
                print('[B][dry-run][undo] Sẽ xóa backfill source_url.')
            return 0

        changed = False
        if 'source_url' not in cols_now:
            if dry_run:
                print('[B][dry-run] Sẽ ALTER: ADD COLUMN source_url TEXT')
            else:
                conn.execute("ALTER TABLE entity_claims ADD COLUMN source_url TEXT")
                changed = True
                print('[B] Đã ADD COLUMN source_url TEXT')
        else:
            print('[B] Cột source_url đã có — bỏ qua (idempotent).')

        if 'retrieved_at' not in cols_now:
            if dry_run:
                print('[B][dry-run] Sẽ ALTER: ADD COLUMN retrieved_at TEXT')
            else:
                conn.execute("ALTER TABLE entity_claims ADD COLUMN retrieved_at TEXT")
                changed = True
                print('[B] Đã ADD COLUMN retrieved_at TEXT')
        else:
            print('[B] Cột retrieved_at đã có — bỏ qua (idempotent).')

        if changed:
            conn.commit()

        # Ghi retrieved_at (thời điểm này) cho claims vừa wire T69 (có verification_note? dùng source_reference T69:)
        # Lưu ý: entity_claims không có cột verification_note; dùng created_at gần đây.
        if not dry_run:
            ts = time.strftime('%Y-%m-%dT%H:%M:%S')
            # chỉ set nếu NULL — non-destructive
            cur = conn.execute(
                "UPDATE entity_claims SET retrieved_at = ? WHERE retrieved_at IS NULL AND created_at >= datetime('now','-1 day')",
                (ts,)
            )
            conn.commit()
            print(f'[B] Gán retrieved_at={ts} cho {cur.rowcount:,} claims (created trong 24h, NULL trước).')

        n = backfill_wikidata_urls(conn, dry_run)

        if not dry_run:
            print('\n[B] Kiểm chứng provenance:')
            for r in conn.execute(
                "SELECT source_id, COUNT(*) FROM entity_claims WHERE source_url IS NOT NULL GROUP BY source_id"
            ):
                print(f'   source_id={r[0]}: {r[1]:,} rows có source_url')
            print('   total claims:', conn.execute("SELECT COUNT(*) FROM entity_claims").fetchone()[0])
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Phase B: add source_url/retrieved_at to entity_claims')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in ra, không ALTER/UPDATE')
    ap.add_argument('--undo', action='store_true', help='xóa backfill source_url (giữ cột)')
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, undo=args.undo))
