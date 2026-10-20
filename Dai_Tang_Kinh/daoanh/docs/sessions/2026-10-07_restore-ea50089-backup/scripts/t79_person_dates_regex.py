#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T79 — Person Birth/Death Date Extraction từ DILA Notes
Script ETL chính: extract birth/death years từ 48,673 persons bio column
"""

import sys
import os
import re
import json
import argparse
import sqlite3
from datetime import datetime

# ---------------------------------------------------
# Configuration — absolute paths for Windows
# ---------------------------------------------------
DB_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
PEOPLE_TABLE = 'people'
EVENTS_TABLE = 'vn_person_events'

VALID_YEAR_RANGE = (100, 2000)

# Context keywords that strongly signal death
DEATH_CONTEXT_RE = re.compile(r'示寂|圓寂|入寂|寂於|卒於|薨|歿|圓寂')

# Parenthetical CE year: （1053） / （1238-1319） / （1043-1118）
PAREN_YEAR_RE = re.compile(r'[（(]\s*(\d{3,4})\s*(?:[-–至]\s*(\d{3,4}))?\s*[）)]')

# Explicit death sentence: XX年（YYYY）示寂 / 示寂於（YYYY） / （YYYY）示寂
DEATH_YEAR_RE = re.compile(
    r'(?:示寂|圓寂|入寂|寂於|卒於|薨)\s*(?:於)?\s*[（(]?\s*(\d{3,4})\s*[）)]?\s*年?(?:示寂|圓寂|入寂)?'
)

# Birth explicit
BIRTH_YEAR_RE = re.compile(
    r'(?:生於|生卒年|誕生|生[於的]?)\s*[（(]\s*(\d{3,4})\s*[）)]'
)


def _clean_year(s):
    if not s:
        return None
    try:
        y = int(s)
    except (ValueError, TypeError):
        return None
    y_min, y_max = VALID_YEAR_RANGE
    if y_min <= y <= y_max:
        return y
    return None


def extract_birth_year(bio_text):
    """Extract birth year with contextual confidence."""
    text = bio_text or ''
    results = []
    # Explicit birth pattern
    for m in BIRTH_YEAR_RE.finditer(text):
        y = _clean_year(m.group(1))
        if y:
            results.append({'year': y, 'confidence': 0.85, 'source_pattern': 'birth_explicit'})
    if results:
        return results
    return []


def extract_death_year(bio_text):
    """Extract death year, highest-confidence (precision) first.

    Priority:
    1. （YYYY）示寂       -- paren immediately before a death keyword   [0.92]
    2. 示寂於（YYYY）     -- death keyword immediately before paren      [0.85]
    Only one year is returned to avoid false positives from distant
    parenthetical years that happen to appear in the same paragraph.
    """
    text = bio_text or ''
    results = []

    # Pattern 1: （YYYY）示寂  -- year closest-before a death keyword
    death_kw = DEATH_CONTEXT_RE.search(text)
    if death_kw:
        # find the last parenthetical year that starts before the death keyword
        best = None
        for m in PAREN_YEAR_RE.finditer(text):
            if m.start() < death_kw.start():
                y = _clean_year(m.group(1))
                if y is not None:
                    best = (m, y)
        if best is not None:
            m, y = best
            # require the paren to be reasonably close (within 30 chars) to the death keyword
            if death_kw.start() - m.end() <= 30:
                results.append({'year': y, 'confidence': 0.92, 'source_pattern': 'death_paren_before'})
                return results

    # Pattern 2: 示寂於（YYYY） -- death keyword before paren
    m2 = re.search(r'(?:示寂|圓寂|入寂|寂於|卒於)[於的]?\s*[（(]\s*(\d{3,4})\s*[）)]', text)
    if m2:
        y = _clean_year(m2.group(1))
        if y:
            results.append({'year': y, 'confidence': 0.85, 'source_pattern': 'death_kw_before'})

    return results


def extract_years_from_note(note_text, patterns):
    """Keep for backward compatibility; not used by main extraction."""
    results = []
    for pattern, confidence in patterns:
        matches = re.findall(pattern, note_text or '')
        for year_str in matches:
            try:
                year = int(year_str)
                y_min, y_max = VALID_YEAR_RANGE
                if y_min <= year <= y_max:
                    results.append({
                        'year': year,
                        'confidence': confidence,
                        'source_pattern': pattern
                    })
            except ValueError:
                continue
    return results


def insert_events(conn, events, table=EVENTS_TABLE):
    """Insert events into vn_person_events table."""
    cursor = conn.cursor()

    for event in events:
        cursor.execute(f"""
            INSERT OR IGNORE INTO {table}
            (person_id, event_type, event_id, event_label_vi, event_year, source, source_ref, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['person_id'],
            event['event_type'],
            event.get('event_id', ''),
            event.get('event_label_vi', event['event_type']),
            event['year'],
            event['source'],
            event.get('source_ref', ''),
            event['confidence']
        ))
    
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description='T79 Person Birth/Death Date Extraction')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                       help='Count events only, do not insert')
    group.add_argument('--apply', action='store_true',
                       help='Insert events into database')
    group.add_argument('--revert', action='store_true',
                       help='Rollback: DELETE events inserted by this script')
    group.add_argument('--stats', action='store_true',
                       help='Show statistics only, exit immediately')
    args = parser.parse_args()
    
    # ---- REVERT MODE ----
    if args.revert:
        print(">>> REVERT MODE: Deleting events with source='dila_person_regex'...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vn_person_events WHERE source = 'dila_person_regex'")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) as total FROM vn_person_events")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source")
        stats = cursor.fetchall()
        
        print(f"Total vn_person_events after revert: {total}")
        print("Events by source:")
        for s, c in stats:
            print(f"  {s}: {c}")
        
        log_data = {
            'date': datetime.now().isoformat(),
            'action': 'revert',
            'events_deleted': total - 45,
            'vn_person_events_total': total
        }
        with open(os.path.join(_PROJECT_ROOT if _PROJECT_ROOT else 'data', 't79_revert_log.json'), 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print("Revert log written.")
        conn.close()
        return
    
    # ---- GET EXISTING EVENTS ----
    existing_ids = set()
    if args.apply:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT person_id FROM vn_person_events WHERE source = 'dila_person_regex'")
            existing_rows = cursor.fetchall()
            existing_ids = set([row[0] for row in existing_rows])
            print(f"Existing dila_person_regex events: {len(existing_ids)}")
        except sqlite3.OperationalError as e:
            print(f"Note: may need to add source column: {e}")
            existing_ids = set()
    else:
        conn = sqlite3.connect(DB_PATH)
    
    # ---- READ PERSONS WITH BIO ----
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, bio FROM {PEOPLE_TABLE} WHERE bio IS NOT NULL AND bio != ''")
    persons = cursor.fetchall()
    
    total_persons = len(persons)
    print(f"TOTAL persons with bio to analyze: {total_persons}")
    
    # Also check people without bio
    cursor.execute(f"SELECT COUNT(*) FROM {PEOPLE_TABLE} WHERE bio IS NULL OR bio = ''")
    no_bio = cursor.fetchone()[0]
    print(f"People without bio: {no_bio} ({no_bio/total_persons*100:.1f}%)")
    
    birth_events = []
    death_events = []
    
    # Progress display
    batch_size = 50
    for i, (person_id, bio_text) in enumerate(persons):
        # Extract birth year
        birth_matches = extract_birth_year(bio_text)
        for match in birth_matches:
            event = {
                'person_id': person_id,
                'event_type': 'birth',
                'year': match['year'],
                'confidence': match['confidence'],
                'source': 'dila_person_regex',
                'source_ref': match['source_pattern']
            }
            if args.apply and event['person_id'] in existing_ids:
                pass
            birth_events.append(event)
        
        # Extract death year
        death_matches = extract_death_year(bio_text)
        for match in death_matches:
            event = {
                'person_id': person_id,
                'event_type': 'death',
                'year': match['year'],
                'confidence': match['confidence'],
                'source': 'dila_person_regex',
                'source_ref': match['source_pattern']
            }
            if args.apply and event['person_id'] in existing_ids:
                pass
            death_events.append(event)
        
        # Progress display
        if (i + 1) % batch_size == 0:
            print(f"  Processed {i+1}/{total_persons} persons... (birth: {len(birth_events)}, death: {len(death_events)})")
    
    print(f"\n=== EXTRACTION SUMMARY ===")
    print(f"Birth events found: {len(birth_events)}")
    print(f"Death events found: {len(death_events)}")
    print(f"Total new events: {len(birth_events) + len(death_events)}")
    
    # ---- STATS MODE ----
    if args.stats:
        print("\n>>> Statistics mode only. Exiting.")
        conn.close()
        return
    
    # ---- INSERT MODE (--apply) ----
    if args.apply:
        print(">>> Applying events to database...")
        insert_events(conn, birth_events, table=EVENTS_TABLE)
        insert_events(conn, death_events, table=EVENTS_TABLE)
        print(f"Inserted {len(birth_events)} birth events and {len(death_events)} death events.")
        
        # Verify
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT source, COUNT(*) FROM {EVENTS_TABLE} GROUP BY source")
            src_stats = cursor.fetchall()
            print("\n=== vn_person_events BY SOURCE ===")
            for s, c in src_stats:
                print(f"  {s}: {c} events")
            
            cursor.execute(f"SELECT COUNT(*) as total FROM {EVENTS_TABLE}")
            total = cursor.fetchone()[0]
            print(f"\nTotal {EVENTS_TABLE}: {total}")
        except Exception as e:
            print(f"Verification error: {e}")
        
        # Generate log
        log_data = {
            'date': datetime.now().isoformat(),
            'action': 'apply',
            'birth_events_inserted': len(birth_events),
            'death_events_inserted': len(death_events),
            'vn_person_events_total': total if 'total' in dir() else '?',
            'persons_analyzed': total_persons,
            'new_events': len(birth_events) + len(death_events)
        }
        log_dir = os.path.dirname(DB_PATH)
        with open(os.path.join(log_dir, 't79_person_dates_log.json'), 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"\nLog file written: data/t79_person_dates_log.json")
        
        conn.close()
        return
    
    # ---- DRY-RUN MODE (default when --dry-run) ----
    if args.dry_run:
        print(">>> DRY-RUN MODE: Counting events only (not inserting).")
        print(f"Birth events would be inserted: {len(birth_events)}")
        print(f"Death events would be inserted: {len(death_events)}")
        print(f"Total new events: {len(birth_events) + len(death_events)}")
        
        log_data = {
            'date': datetime.now().isoformat(),
            'action': 'dry-run',
            'birth_events_count': len(birth_events),
            'death_events_count': len(death_events),
            'total_new_events': len(birth_events) + len(death_events),
            'persons_analyzed': total_persons
        }
        log_dir = os.path.dirname(DB_PATH)
        with open(os.path.join(log_dir, 't79_dry_run_log.json'), 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"Dry-run log written: data/t79_dry_run_log.json")
        
        conn.close()
        return
    
    conn.close()
    print("No valid mode specified.")


if __name__ == '__main__':
    main()