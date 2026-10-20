#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_event_text_link.py
========================
Nexus Commit 2 — BUILD EVENT↔TEXT BRIDGE (`event_text_link`).

Bảng bridge nối EVENT ↔ TEXT passage (điểm hội tụ true-nexus của hệ thống).
Nó TỔNG HỢP mọi citation thật từ các bảng ETL hiện có, giữ nguyên nguồn gốc.
Additive: KHÔNG sửa/xoá bảng nguồn (place_person_bibl, place_timeline_events, ...).

Nguồn:
  1) place_person_bibl (13,933 rows)  — person resided ở place, có cbeta_ref thật
       (vd T50n2060_p0447c17) + source_book (梁高僧傳/唐高僧傳).
       → event_type='person_place', entity_type='person'.
  2) place_timeline_events (3,351 rows) — place founding/dissolved, có year + source_ref
       (vd Q902·P571, dila_era_name, dila_dynasty...). cbeta_ref để NULL (passage nối
       động qua cbeta_place_mentions trong Commit 4).
       → event_type='place_founding' | 'place_dissolved', entity_type='place'.

Đích: bảng `event_text_link` (idempotent — re-run an toàn nhờ UNIQUE(source_table, source_id)).

Chạy (từ root daoanh):
  python scripts/build_event_text_link.py             # apply
  python scripts/build_event_text_link.py --dry-run   # chỉ xem
"""
import io
import os
import sqlite3
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--dry-run' in sys.argv


def main():
    mode = 'DRY-RUN' if DRY_RUN else 'APPLY'
    print(f'=== Nexus Commit 2 — Build EVENT↔TEXT bridge event_text_link [{mode}] ===')
    print(f'DB: {DB_PATH}')
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ---- Nguồn 1: place_person_bibl ----
    print('Step 1: read place_person_bibl...')
    bibl = conn.execute(
        "SELECT id, place_id, person_id, person_name_raw, cbeta_ref, source_book, confidence "
        "FROM place_person_bibl"
    ).fetchall()
    print(f'  {len(bibl):,} rows')

    # ---- Nguồn 2: place_timeline_events ----
    print('Step 2: read place_timeline_events...')
    tl = conn.execute(
        "SELECT id, dila_id, event_type, year, label_zh, label_vi, source, source_ref, confidence "
        "FROM place_timeline_events"
    ).fetchall()
    print(f'  {len(tl):,} rows')

    rows_bibl = []
    for r in bibl:
        rows_bibl.append((
            'person_place', 'person', r['person_id'], r['place_id'],
            r['person_name_raw'] or '', r['cbeta_ref'] or '', r['source_book'] or '',
            'place_person_bibl', r['source_book'] or '', r['id'], None, r['confidence'] or 1.0,
        ))
    rows_tl = []
    for r in tl:
        et = f"place_{r['event_type']}"
        rows_tl.append((
            et, 'place', r['dila_id'], None,
            r['label_zh'] or r['label_vi'] or '', None, '',
            'place_timeline_events', r['source_ref'] or '', r['id'], r['year'], r['confidence'] or 1.0,
        ))

    print(f'  person_place rows (bibl): {len(rows_bibl):,}')
    print(f'  place_timeline rows     : {len(rows_tl):,}')
    print(f'  total to insert         : {len(rows_bibl) + len(rows_tl):,}')

    if DRY_RUN:
        print('[DRY-RUN] Không thay đổi DB. Run again without --dry-run to apply.')
        conn.close()
        return

    # ---- Apply (additive, idempotent) ----
    print('Step 3: create + populate event_text_link...')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS event_text_link (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type   TEXT,
            entity_type  TEXT,
            entity_id    TEXT,
            related_id   TEXT,
            related_name TEXT,
            cbeta_ref    TEXT,
            source_book  TEXT,
            source_table TEXT,
            source_ref   TEXT,
            source_id    INTEGER,
            year         INTEGER,
            confidence   REAL,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_table, source_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_etl_entity ON event_text_link(entity_type, entity_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_etl_cbetaref ON event_text_link(cbeta_ref)")

    cols = ("(event_type, entity_type, entity_id, related_id, related_name, cbeta_ref, "
            "source_book, source_table, source_ref, source_id, year, confidence)")
    sql = (
        "INSERT OR IGNORE INTO event_text_link "
        "(event_type, entity_type, entity_id, related_id, related_name, cbeta_ref, "
        "source_book, source_table, source_ref, source_id, year, confidence) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    conn.executemany(sql, rows_bibl)
    conn.executemany(sql, rows_tl)
    conn.commit()

    total = conn.execute('SELECT COUNT(*) FROM event_text_link').fetchone()[0]
    by_type = [tuple(r) for r in conn.execute(
        'SELECT event_type, COUNT(*) FROM event_text_link GROUP BY event_type ORDER BY 2 DESC')]
    print(f'  event_text_link total: {total:,}')
    print('  by event_type:', by_type)
    print('[DONE]')
    conn.close()


if __name__ == '__main__':
    main()
