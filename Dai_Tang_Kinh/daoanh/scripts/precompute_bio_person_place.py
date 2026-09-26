"""T43 — Pre-compute Bio Person-Place cache.

Runs bio LIKE search for all 59K places once and stores results in
place_person_bio_cache table. Replaces real-time LIKE queries in API.

Usage:
  python precompute_bio_person_place.py            # full run
  python precompute_bio_person_place.py --refresh  # drop + rebuild
  python precompute_bio_person_place.py --sample N # test with N places
"""
import sys, os, io, re, time, sqlite3, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, 'data', 'lineage.db')
LOG_DIR = os.path.join(BASE, 'docs', 'sessions', '2026-08-25')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 't43_etl.log')

log_lines = []


def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)


def flush_log():
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))


def setup_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS place_person_bio_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_id TEXT NOT NULL,
        person_id TEXT NOT NULL,
        matched_variant TEXT,
        is_direct INTEGER DEFAULT 0,
        relation_hint TEXT,
        bio_snippet TEXT,
        confidence REAL DEFAULT 0.6,
        indexed_at TEXT DEFAULT (datetime('now')),
        UNIQUE(place_id, person_id)
    );
    CREATE INDEX IF NOT EXISTS idx_ppbc_place ON place_person_bio_cache(place_id);
    CREATE INDEX IF NOT EXISTS idx_ppbc_person ON place_person_bio_cache(person_id);
    """)
    conn.commit()
    log("DB schema ready: place_person_bio_cache")


DIRECT_KW = re.compile(
    r'(住持|方丈|住寺|主持|開山|開創|創建|開祖|開法|創始|出家|修行|掛錫|掛錫|結夏|安居|坐夏|弘法|講法|講經|'
    r'駐錫|常住|住持|任職|任住|庵主|寺主|寺長|堂主|'
    r'禪師.*住|師住|住此|此住|此寺|本寺)',
    re.IGNORECASE
)


def get_name_variants(place_row):
    """Build name variants for bio LIKE search, same logic as API."""
    variants = set()
    for col in ('name_zh', 'name_en'):
        val = place_row[col] if col in place_row.keys() else None
        if val and len(val) >= 2:
            variants.add(val)
    # Also try short name (remove 寺/觀/院 suffix)
    name_zh = place_row['name_zh'] if 'name_zh' in place_row.keys() else None
    if name_zh and len(name_zh) > 2:
        short = re.sub(r'[寺觀院庵堂塔宮林洞]$', '', name_zh)
        if short and len(short) >= 2:
            variants.add(short)
    return list(variants)


def extract_snippet(bio, variant, window=60):
    """Extract bio snippet around variant mention."""
    if not bio or not variant:
        return None
    idx = bio.find(variant)
    if idx < 0:
        return None
    start = max(0, idx - 20)
    end = min(len(bio), idx + window)
    snip = bio[start:end].strip()
    return snip if len(snip) > 5 else None


def process_place_in_memory(place, bio_people):
    """Search for place name variants in pre-loaded bio_people list.

    bio_people = [(person_id, name_zh, bio, dynasty), ...]
    Returns list of match dicts.
    """
    place_id = place['id']
    variants = get_name_variants(place)
    if not variants:
        return []

    results = []
    seen_pids = set()
    for pid, pname, bio, dynasty in bio_people:
        if not bio or pid in seen_pids:
            continue
        matched_variant = None
        for v in variants:
            if v in bio:
                matched_variant = v
                break
        if not matched_variant:
            continue
        seen_pids.add(pid)
        snippet = extract_snippet(bio, matched_variant)
        is_direct = 1 if (snippet and DIRECT_KW.search(snippet)) else 0
        results.append({
            'place_id': place_id,
            'person_id': pid,
            'matched_variant': matched_variant,
            'is_direct': is_direct,
            'relation_hint': '住持/修行' if is_direct else '提及',
            'bio_snippet': snippet[:200] if snippet else None,
            'confidence': 0.7 if is_direct else 0.6,
        })
    return results


def run_etl(sample=None, refresh=False):
    log("=== T43 Pre-compute Bio Person-Place ===")
    log(f"DB: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if refresh:
        log("--refresh: dropping place_person_bio_cache...")
        conn.execute("DROP TABLE IF EXISTS place_person_bio_cache")
        conn.commit()

    setup_db(conn)

    existing = conn.execute("SELECT COUNT(*) FROM place_person_bio_cache").fetchone()[0]
    if existing > 0 and not refresh:
        log(f"Cache already has {existing} rows. Use --refresh to rebuild.")
        conn.close()
        return existing

    # Load ALL bio people into memory once (avoid 59K SQL queries)
    log("Loading all bio people into memory...")
    t_load = time.time()
    bio_people = conn.execute(
        "SELECT id, name_zh, bio, dynasty FROM people WHERE bio IS NOT NULL AND bio != '' ORDER BY id"
    ).fetchall()
    bio_people = [(r['id'], r['name_zh'], r['bio'], r['dynasty']) for r in bio_people]
    log(f"  Loaded {len(bio_people)} persons with bio in {time.time()-t_load:.1f}s")

    # Get all places
    places = conn.execute(
        "SELECT id, name_zh, name_en FROM places_dila ORDER BY id"
    ).fetchall()
    total_places = len(places)
    if sample:
        places = places[:sample]
        log(f"Sample mode: processing {len(places)}/{total_places} places")
    else:
        log(f"Processing all {total_places} places...")

    inserted = 0
    places_with_matches = 0
    places_empty = 0
    batch = []
    BATCH_SIZE = 500

    t0 = time.time()
    for i, place in enumerate(places):
        matches = process_place_in_memory(place, bio_people)
        if matches:
            places_with_matches += 1
            for m in matches:
                batch.append((
                    m['place_id'], m['person_id'], m['matched_variant'],
                    m['is_direct'], m['relation_hint'], m['bio_snippet'], m['confidence']
                ))
        else:
            places_empty += 1

        if len(batch) >= BATCH_SIZE:
            conn.executemany(
                """INSERT OR IGNORE INTO place_person_bio_cache
                   (place_id, person_id, matched_variant, is_direct, relation_hint, bio_snippet, confidence)
                   VALUES (?,?,?,?,?,?,?)""",
                batch
            )
            conn.commit()
            inserted += len(batch)
            batch = []

        if (i + 1) % 5000 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(places) - i - 1) / rate if rate > 0 else 0
            log(f"  Progress: {i+1}/{len(places)} places | {inserted} cached | ETA: {eta:.0f}s")
            flush_log()

    if batch:
        conn.executemany(
            """INSERT OR IGNORE INTO place_person_bio_cache
               (place_id, person_id, matched_variant, is_direct, relation_hint, bio_snippet, confidence)
               VALUES (?,?,?,?,?,?,?)""",
            batch
        )
        conn.commit()
        inserted += len(batch)

    elapsed = time.time() - t0
    total_rows = conn.execute("SELECT COUNT(*) FROM place_person_bio_cache").fetchone()[0]
    unique_places_cached = conn.execute("SELECT COUNT(DISTINCT place_id) FROM place_person_bio_cache").fetchone()[0]
    unique_persons_cached = conn.execute("SELECT COUNT(DISTINCT person_id) FROM place_person_bio_cache").fetchone()[0]

    log("=== T43 Results ===")
    log(f"Places processed:           {len(places)}")
    log(f"Places with ≥1 bio person:  {places_with_matches}")
    log(f"Places with 0 bio persons:  {places_empty}")
    log(f"Coverage:                   {places_with_matches/len(places)*100:.1f}%")
    log(f"Inserted pairs:             {inserted}")
    log(f"Total cache rows:           {total_rows}")
    log(f"Unique places cached:       {unique_places_cached}")
    log(f"Unique persons cached:      {unique_persons_cached}")
    log(f"Elapsed:                    {elapsed:.1f}s")

    # Sample
    samples = conn.execute("""
        SELECT ppbc.place_id, pd.name_zh, ppbc.person_id, p.name_zh as pname,
               ppbc.is_direct, ppbc.matched_variant
        FROM place_person_bio_cache ppbc
        JOIN places_dila pd ON pd.id = ppbc.place_id
        JOIN people p ON p.id = ppbc.person_id
        WHERE ppbc.is_direct = 1
        LIMIT 8
    """).fetchall()
    log("Direct match samples:")
    for s in samples:
        log(f"  {s['place_id']} ({s['name_zh']}) ← {s['pname']} via '{s['matched_variant']}'")

    conn.close()
    flush_log()
    log(f"Log saved to: {LOG_PATH}")
    return total_rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true', help='Drop and rebuild cache')
    parser.add_argument('--sample', type=int, default=None, help='Process only N places (test mode)')
    args = parser.parse_args()
    total = run_etl(sample=args.sample, refresh=args.refresh)
    sys.exit(0 if total > 0 else 1)
