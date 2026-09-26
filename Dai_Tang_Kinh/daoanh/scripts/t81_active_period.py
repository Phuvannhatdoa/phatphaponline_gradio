#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T81 — Active Period / Flourished extraction from DILA person bios

Trích giai đoạn hoạt động (active/floruit) cho nhân vật từ các năm
「（YYYY）」 đơn (single-year CE parens) trong `people.bio`:

- >=2 distinct single years  -> event_type='active', event_year = start year,
                                range ghi trong event_label_vi "Hoạt động YY–YY" (conf 0.70)
- đúng 1 single year          -> event_type='floruit', event_year = năm đó       (conf 0.55)

Bỏ qua 2-year ranges （YYYY-YYYY） vì đây thường là năm sống của sư phụ/vị khác
(không phải hoạt động của chủ thể) — rút kinh nghiệm từ probe thật.

Usage:
  python t81_active_period.py            # dry-run
  python t81_active_period.py --apply    # insert
  python t81_active_period.py --revert   # DELETE source='dila_active_regex'
  python t81_active_period.py --stats    # thống kê
"""

import sys
import os
import re
import json
import argparse
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
LOG_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\t81_active_log.json'
PEOPLE_TABLE = 'people'
EVENTS_TABLE = 'vn_person_events'
SOURCE = 'dila_active_regex'

VALID_RANGE = (100, 2000)

# Single-year parens only: （1053） — NOT （1238-1319）/（1271-1295）
SINGLE_YEAR = re.compile(r'[（(]\s*(\d{3,4})\s*[）)]')


def extract_years(bio_text):
    """Return sorted distinct CE years from single-year parens."""
    if not bio_text:
        return []
    years = set()
    for m in SINGLE_YEAR.finditer(bio_text):
        try:
            y = int(m.group(1))
        except (ValueError, TypeError):
            continue
        if VALID_RANGE[0] <= y <= VALID_RANGE[1]:
            years.add(y)
    return sorted(years)


def build_events(person_id, years):
    """Return a single event dict for a person (or None)."""
    if not years:
        return None
    if len(years) >= 2:
        start, end = years[0], years[-1]
        return {
            'person_id': person_id,
            'event_type': 'active',
            'event_id': person_id,
            'event_label_vi': f'Hoạt động {start}–{end}',
            'event_year': start,
            'source': SOURCE,
            'source_ref': f'active_range:{start}-{end}',
            'confidence': 0.70,
        }
    else:
        y = years[0]
        return {
            'person_id': person_id,
            'event_type': 'floruit',
            'event_id': person_id,
            'event_label_vi': f'Hoạt động khoảng {y}',
            'event_year': y,
            'source': SOURCE,
            'source_ref': f'floruit:{y}',
            'confidence': 0.55,
        }


def run(arguments):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ---- REVERT ----
    if arguments.revert:
        c.execute("DELETE FROM vn_person_events WHERE source = ?", (SOURCE,))
        deleted = conn.total_changes
        conn.commit()
        c.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source")
        print(f"Reverted: {deleted} rows removed (source='{SOURCE}')")
        print("Remaining events by source:")
        for s, n in c.fetchall():
            print(f"  {s}: {n}")
        conn.close()
        return

    # ---- STATS ----
    if arguments.stats:
        c.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source")
        for s, n in c.fetchall():
            print(f"  {s}: {n}")
        c.execute("SELECT COUNT(*) FROM vn_person_events")
        print(f"Total vn_person_events: {c.fetchone()[0]}")
        conn.close()
        return

    # ---- READ PERSONS ----
    c.execute(f"SELECT id, bio FROM {PEOPLE_TABLE} WHERE bio IS NOT NULL AND bio != ''")
    rows = c.fetchall()
    print(f"Persons with bio to analyze: {len(rows)}")

    # Existing events for this source (to be idempotent)
    if arguments.apply:
        c.execute("SELECT person_id FROM vn_person_events WHERE source = ?", (SOURCE,))
        existing = set(r[0] for r in c.fetchall())
        print(f"Existing {SOURCE} events: {len(existing)}")
    else:
        existing = set()

    active_events = []
    floruit_events = []
    for person_id, bio in rows:
        years = extract_years(bio)
        ev = build_events(person_id, years)
        if ev is None:
            continue
        if arguments.apply and person_id in existing:
            continue
        if ev['event_type'] == 'active':
            active_events.append(ev)
        else:
            floruit_events.append(ev)

    print(f"\nActive window events (>=2 years, conf 0.70): {len(active_events)}")
    print(f"Floruit events (1 year, conf 0.55): {len(floruit_events)}")
    print(f"Total new events: {len(active_events) + len(floruit_events)}")

    # ---- DRY-RUN ----
    if not arguments.apply:
        print("\n=== SAMPLE active windows (first 12) ===")
        for ev in active_events[:12]:
            print(f"  {ev['person_id']}: {ev['event_label_vi']}")
        print("\n=== SAMPLE floruit (first 8) ===")
        for ev in floruit_events[:8]:
            print(f"  {ev['person_id']}: {ev['event_label_vi']}")
        log = {
            'date': datetime.now().isoformat(),
            'action': 'dry-run',
            'active_events': len(active_events),
            'floruit_events': len(floruit_events),
            'total_new_events': len(active_events) + len(floruit_events),
            'persons_analyzed': len(rows),
        }
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        conn.close()
        return

    # ---- APPLY ----
    inserted = 0
    for ev in active_events + floruit_events:
        c.execute(f"""
            INSERT OR IGNORE INTO {EVENTS_TABLE}
            (person_id, event_type, event_id, event_label_vi, event_year, source, source_ref, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ev['person_id'],
            ev['event_type'],
            ev['event_id'],
            ev['event_label_vi'],
            ev['event_year'],
            ev['source'],
            ev['source_ref'],
            ev['confidence'],
        ))
        inserted += 1
    conn.commit()

    # Verify
    c.execute("SELECT event_type, COUNT(*) FROM vn_person_events WHERE source = ? GROUP BY event_type", (SOURCE,))
    print(f"\nInserted: {inserted}")
    print(f"{SOURCE} rows by type:")
    for t, n in c.fetchall():
        print(f"  {t}: {n}")
    c.execute("SELECT COUNT(*) FROM vn_person_events")
    print(f"Total vn_person_events: {c.fetchone()[0]}")

    log = {
        'date': datetime.now().isoformat(),
        'action': 'apply',
        'source': SOURCE,
        'active_events_inserted': len(active_events),
        'floruit_events_inserted': len(floruit_events),
        'total_inserted': len(active_events) + len(floruit_events),
        'persons_analyzed': len(rows),
    }
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nLog file written: {LOG_PATH}")
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='T81 Active Period / Flourished')
    parser.add_argument('--apply', action='store_true', help='Insert events into DB')
    parser.add_argument('--revert', action='store_true', help='DELETE source=dila_active_regex')
    parser.add_argument('--stats', action='store_true', help='Show stats and exit')
    args = parser.parse_args()
    run(args)
