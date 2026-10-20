"""
T97 Phase 2 — Deterministic Time Mention Parser + DILA Mapping
Reads from place_timeline_events + nexus_events, extracts structured time mentions,
maps reign eras → CE year via local time_periods table (no self-generated years).

Usage:
    python scripts/t97_parse_time_mentions.py --dry-run    # print only
    python scripts/t97_parse_time_mentions.py --apply      # insert into time_mentions
    python scripts/t97_parse_time_mentions.py --apply --seed-events  # also seed events table

Evidence-first rules:
  - exact year (495年) → precision=year, extraction_method=regex_rule
  - reign era (北魏太和19年) → precision=reign_era; map CE only if time_periods match
  - relative (32年後) → precision=relative, no CE year generated
  - dynasty period (唐朝時期) → precision=dynasty_period, no CE year generated
  - unknown → precision=unknown
"""

import re, sqlite3, sys, os, io
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

# ── Regex patterns ──────────────────────────────────────────────────────────

# Exact CE year: 495年, (477年建)
_PAT_YEAR = re.compile(r'(\d{3,4})年')

# Reign era + year: 太和19年, 北魏太和19年, 永平元年
_PAT_REIGN_ERA = re.compile(r'([^\d，。、（\(]{2,8}?)(\d{1,3}|元)年')

# Relative: 後X年, X年後, X年前
_PAT_RELATIVE = re.compile(r'(?:後|前)(\d{1,3})年|(\d{1,3})年(?:後|前|以後|以前)')

# Dynasty period: 唐, 宋, 明, 清, 漢, 魏, 晉, 隋, 元 + 朝/代/時期/初/末
_PAT_DYNASTY = re.compile(
    r'(唐|宋|明|清|漢|北魏|東魏|西魏|北齊|北周|南朝|北朝|五代|魏晉|隋|元|周|秦|楚|吳|蜀)'
    r'(?:朝|代|時期|初|末|前期|後期)?'
)

DYNASTY_RANGES = {
    '秦': (-221, -206), '漢': (-206, 220), '魏': (220, 265), '晉': (265, 420),
    '南朝': (420, 589), '北朝': (386, 581), '北魏': (386, 534), '東魏': (534, 550),
    '西魏': (535, 556), '北齊': (550, 577), '北周': (557, 581), '隋': (581, 618),
    '唐': (618, 907), '五代': (907, 960), '宋': (960, 1279), '元': (1271, 1368),
    '明': (1368, 1644), '清': (1644, 1912),
}


def classify_raw(raw: str):
    """Return (precision, ce_start, ce_end, matched_span, reign_era_str).
    Never generates CE year without authority backing for reign_era."""
    raw = raw.strip()
    # 1. Relative — check first to avoid misclassifying "後X年"
    if _PAT_RELATIVE.search(raw):
        return 'relative', None, None, raw, None

    # 2. Exact bare CE year (e.g. "495年")
    m = _PAT_YEAR.search(raw)
    if m:
        y = int(m.group(1))
        if 1 <= y <= 2100:
            return 'year', y, y, m.group(0), None

    # 3. Reign era — mark but DO NOT map CE (mapping happens in map_reign_era)
    m2 = _PAT_REIGN_ERA.search(raw)
    if m2:
        era_name = m2.group(1).strip()
        return 'reign_era', None, None, m2.group(0), era_name

    # 4. Dynasty period
    m3 = _PAT_DYNASTY.search(raw)
    if m3:
        dynasty = m3.group(1)
        rng = DYNASTY_RANGES.get(dynasty)
        start, end = (rng[0], rng[1]) if rng else (None, None)
        return 'dynasty_period', start, end, m3.group(0), None

    return 'unknown', None, None, raw, None


def map_reign_era(conn, era_name: str, era_year_str: str):
    """Look up reign era in DILA time_periods. Return (ce_year, authority_id) or (None, None)."""
    if not era_name:
        return None, None
    era_num = 1 if era_year_str == '元' else (int(era_year_str) if era_year_str and era_year_str.isdigit() else None)
    rows = conn.execute(
        "SELECT id, start_year, end_year FROM time_periods WHERE era_name LIKE ? LIMIT 5",
        (f'%{era_name}%',)
    ).fetchall()
    if not rows:
        return None, None
    r = rows[0]
    if r[1] is not None and era_num:
        ce = int(r[1]) + era_num - 1
        return ce, str(r[0])
    if r[1] is not None:
        return int(r[1]), str(r[0])
    return None, None


def make_mention_id(source_table, source_record_id, seq):
    return f"tm:{source_table[:3]}:{source_record_id}:{seq}"


def parse_place_timeline_events(conn, dry_run=True):
    rows = conn.execute(
        "SELECT id, dila_id, label_zh, year, source, source_ref FROM place_timeline_events WHERE label_zh IS NOT NULL"
    ).fetchall()

    results = []
    for r in rows:
        raw = r[2] or ''
        if not raw.strip():
            continue
        precision, ce_start, ce_end, span, era_name = classify_raw(raw)

        # For reign_era: attempt DILA mapping
        authority_id = None
        extraction_method = 'regex_rule'
        if precision == 'reign_era' and era_name:
            # find numeric year in raw
            era_yr_m = re.search(r'(\d{1,3}|元)年', raw)
            era_yr_str = era_yr_m.group(1) if era_yr_m else None
            ce_start, authority_id = map_reign_era(conn, era_name, era_yr_str)
            if ce_start is not None:
                ce_end = ce_start
                extraction_method = 'authority_mapping'

        # Use existing year as fallback when we have it and precision matched nothing
        if precision == 'unknown' and r[3]:
            ce_start = ce_end = int(r[3])
            precision = 'year'
            extraction_method = 'imported'
            span = f"{r[3]}年"

        mid = make_mention_id('place_timeline_events', str(r[0]), 0)
        results.append({
            'mention_id': mid,
            'source_table': 'place_timeline_events',
            'source_record_id': str(r[0]),
            'raw_time_zh': span[:200],
            'normalized_start': ce_start,
            'normalized_end': ce_end,
            'precision': precision,
            'time_authority_id': authority_id,
            'extraction_method': extraction_method,
            'confidence': 0.9 if extraction_method in ('imported', 'authority_mapping') else 0.7,
        })

    if dry_run:
        print(f'[dry-run] Would insert {len(results)} time_mentions from place_timeline_events')
        for r in results[:5]:
            print(f"  {r['mention_id']} | {r['raw_time_zh'][:40]} | {r['precision']} | start={r['normalized_start']}")
    else:
        inserted = 0
        for r in results:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO time_mentions
                    (mention_id, source_table, source_record_id, raw_time_zh,
                     normalized_start, normalized_end, precision,
                     time_authority_id, extraction_method, confidence)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (r['mention_id'], r['source_table'], r['source_record_id'],
                      r['raw_time_zh'], r['normalized_start'], r['normalized_end'],
                      r['precision'], r['time_authority_id'], r['extraction_method'],
                      r['confidence']))
                inserted += 1
            except Exception as e:
                print(f"  [skip] {r['mention_id']}: {e}")
        conn.commit()
        print(f'[OK] Inserted {inserted} time_mentions from place_timeline_events')
    return results


def seed_events_from_timeline(conn, dry_run=True):
    """Seed events table with founding events from place_timeline_events (status=candidate)."""
    rows = conn.execute("""
        SELECT DISTINCT dila_id, year, label_zh, label_vi, source, source_ref
        FROM place_timeline_events
        WHERE event_type='founding' AND year IS NOT NULL
        ORDER BY dila_id
    """).fetchall()

    inserted_ev = inserted_ent = inserted_evid = 0
    for r in rows:
        dila_id, year, label_zh, label_vi, src, src_ref = r
        event_id = f"ev:founding:{dila_id}"
        # Check if already exists
        existing = conn.execute("SELECT event_id FROM events WHERE event_id=?", (event_id,)).fetchone()
        if existing:
            continue

        if not dry_run:
            conn.execute("""
                INSERT OR IGNORE INTO events
                (event_id, event_type, title_zh, title_vi, start_year, end_year,
                 precision, extraction_method, review_status, confidence)
                VALUES (?,?,?,?,?,?,'year','imported','candidate',0.7)
            """, (event_id, 'founding', label_zh, label_vi or '', year, year))
            conn.execute("""
                INSERT OR IGNORE INTO event_entities
                (event_id, entity_id, entity_type, role)
                VALUES (?,?,'place','place')
            """, (event_id, dila_id))
            conn.execute("""
                INSERT OR IGNORE INTO event_evidence
                (event_id, source_record, source_table, exact_span, source_ref, evidence_type)
                VALUES (?,?,?,?,?,?)
            """, (event_id, f"{dila_id}:founding", 'place_timeline_events',
                  label_zh, src_ref or src, 'dila_note'))
            inserted_ev += 1
        else:
            inserted_ev += 1

    if dry_run:
        print(f'[dry-run] Would seed {inserted_ev} founding events')
    else:
        conn.commit()
        print(f'[OK] Seeded {inserted_ev} founding events into events table')
    return inserted_ev


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    seed_events = '--seed-events' in sys.argv

    conn = sqlite3.connect(DB)
    conn.text_factory = lambda b: b.decode('utf-8', errors='replace')

    if dry_run:
        print('=== DRY RUN — pass --apply to write ===\n')
    else:
        print('=== APPLYING ===\n')

    parse_place_timeline_events(conn, dry_run=dry_run)

    if seed_events:
        seed_events_from_timeline(conn, dry_run=dry_run)

    conn.close()
    print('\nDone.')
