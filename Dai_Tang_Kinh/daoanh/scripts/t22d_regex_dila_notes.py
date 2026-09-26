"""
T22d — Regex ETL: Founding Dates từ places_dila.note
Layer D của T22 founding-dates pipeline (không cần NLP/GPU).

Usage:
  python t22d_regex_dila_notes.py               # dry-run: count + top 30 samples
  python t22d_regex_dila_notes.py --apply       # insert vào place_timeline_events
  python t22d_regex_dila_notes.py --verbose     # dry-run + in từng match
  python t22d_regex_dila_notes.py --revert      # xóa tất cả rows source='dila_note_regex'
  python t22d_regex_dila_notes.py --stats       # thống kê theo pattern
"""

import sqlite3
import re
import json
import sys
import os
import argparse
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 't22d_regex_log.json')
SOURCE = 'dila_note_regex'

PATTERNS = [
    (r'始建.{0,15}公元\s*(\d{3,4})\s*年', 0.90, 'shijian_gongyan'),
    (r'公元\s*(\d{3,4})\s*年',              0.88, 'gongyan'),
    (r'西元\s*(\d{3,4})\s*年',              0.85, 'xiyuan'),
    (r'創建[於于]?\s*(\d{3,4})\s*年',       0.85, 'chuangjian'),
    (r'建[於于]\s*(\d{3,4})\s*年',          0.85, 'jian_yu'),
    (r'(\d{3,4})\s*年[建創興立][設造]?',    0.85, 'year_jian'),
    (r'(\d{3,4})\s*(?:AD|CE)\b',            0.80, 'ad_ce'),
]
COMPILED = [(re.compile(p), conf, name) for p, conf, name in PATTERNS]
RENOVATION = re.compile(r'重修|重建|重興|重創|重立|修葺|重塑')


def find_matches(dila_id: str, note: str) -> list[dict]:
    """Return list of {year, confidence, pattern_name, renovation} for a note."""
    results = []
    seen_years = set()
    for pat, base_conf, pat_name in COMPILED:
        for m in pat.finditer(note):
            year = int(m.group(1))
            if year < 1 or year > 2000:
                continue
            if year in seen_years:
                continue
            seen_years.add(year)
            # Check renovation context: window of 20 chars before match
            start = max(0, m.start() - 20)
            context = note[start: m.end() + 10]
            is_renovation = bool(RENOVATION.search(context))
            conf = base_conf * (0.7 if is_renovation else 1.0)
            results.append({
                'dila_id': dila_id,
                'year': year,
                'confidence': round(conf, 4),
                'pattern': pat_name,
                'renovation': is_renovation,
                'context': context.strip()[:80],
            })
            break  # one match per pattern per note (first year wins)
    return results


def run(apply=False, verbose=False, revert=False, stats=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if revert:
        c.execute(f"DELETE FROM place_timeline_events WHERE source = ?", (SOURCE,))
        deleted = conn.total_changes
        conn.commit()
        print(f"Reverted: {deleted} rows removed (source='{SOURCE}')")
        conn.close()
        return

    if stats:
        c.execute(
            "SELECT source_ref, COUNT(*), MIN(year), MAX(year) "
            "FROM place_timeline_events WHERE source=? GROUP BY source_ref ORDER BY 2 DESC",
            (SOURCE,)
        )
        rows = c.fetchall()
        if rows:
            print(f"{'Pattern':<20} {'Count':>6}  Year range")
            for r in rows:
                print(f"  {r[0]:<18} {r[1]:>6}  {r[2]}–{r[3]}")
        else:
            print(f"No rows with source='{SOURCE}'")
        conn.close()
        return

    c.execute(
        "SELECT id, note, name_zh FROM places_dila WHERE note IS NOT NULL AND note != ''"
    )
    all_notes = c.fetchall()

    all_matches = []
    pattern_counts = {}
    renovation_count = 0

    for dila_id, note, name_zh in all_notes:
        matches = find_matches(dila_id, note)
        for m in matches:
            m['name_zh'] = (name_zh or '')[:50]
            all_matches.append(m)
            pattern_counts[m['pattern']] = pattern_counts.get(m['pattern'], 0) + 1
            if m['renovation']:
                renovation_count += 1

    all_matches.sort(key=lambda x: (x['dila_id'], x['year']))

    print(f"Total matches found: {len(all_matches)}")
    print(f"Renovation context (confidence ×0.7): {renovation_count}")
    print(f"Pattern breakdown:")
    for p, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {p:<22} {cnt}")

    if verbose or not apply:
        print("\nTop 30 samples:")
        for m in all_matches[:30]:
            flag = ' [RENOVATION]' if m['renovation'] else ''
            print(f"  {m['dila_id']}  year={m['year']}  conf={m['confidence']}  "
                  f"pat={m['pattern']}{flag}  | {m['context'][:60]}")

    if not apply:
        print("\nDry-run complete. Use --apply to insert.")
        conn.close()
        return

    # Apply: delete existing dila_note_regex rows then reinsert (idempotent)
    c.execute("DELETE FROM place_timeline_events WHERE source = ?", (SOURCE,))
    deleted = conn.total_changes
    now = datetime.utcnow().isoformat()
    inserted = 0
    errors = []

    for m in all_matches:
        try:
            c.execute(
                "INSERT INTO place_timeline_events "
                "(dila_id, event_type, year, label_zh, source, source_ref, confidence, created_at) "
                "VALUES (?, 'founding', ?, ?, ?, ?, ?, ?)",
                (
                    m['dila_id'],
                    m['year'],
                    m['name_zh'],
                    SOURCE,
                    m['pattern'],
                    str(m['confidence']),
                    now,
                )
            )
            inserted += 1
        except Exception as e:
            errors.append({'dila_id': m['dila_id'], 'error': str(e)})

    conn.commit()
    conn.close()

    log = {
        'run_at': now,
        'deleted_previous': deleted,
        'inserted': inserted,
        'errors': len(errors),
        'renovation_flagged': renovation_count,
        'pattern_counts': pattern_counts,
        'sample': all_matches[:20],
        'error_list': errors[:10],
    }
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\nInserted {inserted} rows into place_timeline_events (source='{SOURCE}')")
    print(f"Deleted previous: {deleted}")
    print(f"Errors: {len(errors)}")
    print(f"Log: {LOG_PATH}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',   action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--revert',  action='store_true')
    parser.add_argument('--stats',   action='store_true')
    args = parser.parse_args()
    run(apply=args.apply, verbose=args.verbose, revert=args.revert, stats=args.stats)
