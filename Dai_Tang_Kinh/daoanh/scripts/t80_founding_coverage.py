#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T80 — Founding Date Coverage: DILA regex phase 2
Extract thêm founding dates từ places_dila.note bằng pattern
「（YYYY）」(CE year trong ngoặc) gần từ-khóa founding (始建/創建/建於/開山...).

Chỉ insert cho các places CHƯA có sẵn event trong place_timeline_events
(additive — không đụng dữ liệu cũ).

Usage:
  python t80_founding_coverage.py               # dry-run
  python t80_founding_coverage.py --apply       # insert
  python t80_founding_coverage.py --revert      # xóa source='dila_founding_phase2'
  python t80_founding_coverage.py --stats       # thống kê
"""

import sqlite3
import re
import json
import os
import argparse
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
LOG_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\t80_founding_log.json'
SOURCE = 'dila_founding_phase2'

# Founding keywords (xây/創建 temples, palaces, bridges, etc.)
FOUNDING_KW = re.compile(
    r'建寺|創建|始建|開山|建廟|建塔|建於|所建|敕建|創立|建立|興建|起建|肇建|始創|建城|建都'
)

# Admin/political restructuring terms to EXCLUDE (not real founding)
ADMIN_KW = re.compile(r'建都|置縣|設州|析置|遷都|移治|改州|設[縣府郡]|置[館縣城]|分[郡縣州]', re.I)

# CE year in parentheses: （1053） / （1271-1295） / (1238-1319)
PAREN_YEAR = re.compile(r'[（(]\s*(\d{3,4})\s*(?:[-–至]\s*(\d{3,4}))?\s*[）)]')

# Two-year range parens （YYYY-YYYY） often = person life span or reign span (NOT founding)
TWO_YEAR_RANGE = re.compile(r'[（(]\s*\d{3,4}\s*[-–至]\s*\d{3,4}\s*[）)]')

VALID_RANGE = (100, 2000)

# Max distance (chars) between founding keyword and the parenthetical year
MAX_DIST = 90


def extract_founding(dila_id, name, note):
    """Return list of {dila_id, year, confidence, context} for a note."""
    if not note:
        return []
    m = FOUNDING_KW.search(note)
    if not m:
        return []
    # Skip if founding keyword is part of admin/political restructuring context within window
    admin_win = note[max(0, m.start() - 15): m.end() + 15]
    if ADMIN_KW.search(admin_win):
        return []
    results = []
    for pm in PAREN_YEAR.finditer(note):
        # year paren must come after the founding keyword
        if pm.start() < m.end():
            continue
        dist = pm.start() - m.end()
        if dist > MAX_DIST:
            continue
        # Skip two-year ranges （YYYY-YYYY） — usually life span / reign span
        if TWO_YEAR_RANGE.match(note[pm.start():pm.end()]):
            continue
        year = int(pm.group(1))
        if not (VALID_RANGE[0] <= year <= VALID_RANGE[1]):
            continue
        confidence = 0.90 if dist <= 30 else 0.80
        ctx_start = max(0, m.start() - 10)
        ctx = note[ctx_start:pm.end() + 5].strip()
        results.append({
            'dila_id': dila_id,
            'year': year,
            'confidence': confidence,
            'context': ctx[:80],
        })
        break  # one founding event per place
    return results


def run(apply=False, revert=False, stats=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if revert:
        c.execute("DELETE FROM place_timeline_events WHERE source = ?", (SOURCE,))
        deleted = conn.total_changes
        conn.commit()
        print(f"Reverted: {deleted} rows removed (source='{SOURCE}')")
        conn.close()
        return

    if stats:
        c.execute("SELECT source, COUNT(*) FROM place_timeline_events GROUP BY source")
        for r in c.fetchall():
            print(f"  {r[0]}: {r[1]}")
        c.execute("SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events")
        print(f"Distinct dila_id covered: {c.fetchone()[0]}")
        conn.close()
        return

    # Existing covered dila_ids (to be additive)
    c.execute("SELECT DISTINCT dila_id FROM place_timeline_events")
    existing = set(r[0] for r in c.fetchall())
    print(f"Places already with timeline event: {len(existing)}")

    c.execute("SELECT id, name, note FROM places_dila WHERE note IS NOT NULL AND note != ''")
    rows = c.fetchall()

    new_events = []
    for dila_id, name, note in rows:
        if dila_id in existing:
            continue  # additive only
        for ev in extract_founding(dila_id, name, note):
            ev['name'] = name
            new_events.append(ev)

    print(f"NEW founding events found (places not yet covered): {len(new_events)}")

    if not apply:
        print("\n=== SAMPLE (first 30) ===")
        for ev in new_events[:30]:
            print(f"  {ev['dila_id']} ({ev['name']}) -> {ev['year']} conf={ev['confidence']}: {ev['context']}")
        log = {
            'date': datetime.now().isoformat(),
            'action': 'dry-run',
            'new_events_found': len(new_events),
            'places_already_covered': len(existing),
        }
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        conn.close()
        return

    # ---- APPLY ----
    inserted = 0
    for ev in new_events:
        c.execute("""
            INSERT OR IGNORE INTO place_timeline_events
            (dila_id, event_type, year, label_zh, source, source_ref, confidence, created_at)
            VALUES (?, 'founding', ?, ?, ?, 'dila_founding_phase2', ?, ?)
        """, (
            ev['dila_id'],
            ev['year'],
            ev.get('name', ''),
            SOURCE,
            str(ev['confidence']),
            datetime.now().isoformat(),
        ))
        inserted += 1
    conn.commit()

    # verify
    c.execute("SELECT COUNT(*) FROM place_timeline_events WHERE source = ?", (SOURCE,))
    in_db = c.fetchone()[0]
    c.execute("SELECT DISTINCT dila_id FROM place_timeline_events")
    covered = len(set(r[0] for r in c.fetchall()))
    c.execute("SELECT COUNT(*) FROM places_dila WHERE note_category LIKE '%寺廟、佛塔、佛教文化地點%'")
    temples = c.fetchone()[0]

    print(f"\nInserted: {inserted} (source='{SOURCE}')")
    print(f"place_timeline_events rows with {SOURCE}: {in_db}")
    print(f"Distinct places covered: {covered}")
    print(f"Temple-category places: {temples}")
    print(f"Temple coverage (temple denominator): {covered/temples*100:.1f}%")

    log = {
        'date': datetime.now().isoformat(),
        'action': 'apply',
        'new_events_found': len(new_events),
        'rows_inserted': inserted,
        'distinct_places_covered': covered,
        'temple_denominator': temples,
        'temple_coverage_pct': round(covered / temples * 100, 1),
        'source': SOURCE,
    }
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nLog file written: {LOG_PATH}")
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='T80 Founding Date Coverage Phase 2')
    parser.add_argument('--apply', action='store_true', help='Insert events into DB')
    parser.add_argument('--revert', action='store_true', help='DELETE source=dila_founding_phase2')
    parser.add_argument('--stats', action='store_true', help='Show stats and exit')
    args = parser.parse_args()
    run(apply=args.apply, revert=args.revert, stats=args.stats)
