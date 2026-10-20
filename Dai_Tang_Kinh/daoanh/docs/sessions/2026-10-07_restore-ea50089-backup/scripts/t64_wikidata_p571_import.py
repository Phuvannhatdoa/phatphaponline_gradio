"""T64 — Wikidata P571 Timeline Import: Buddhist temples in China with founding dates.

Workflow:
  python t64_wikidata_p571_import.py --download          # SPARQL → data/wikidata_p571_temples.json
  python t64_wikidata_p571_import.py --dry-run           # preview matches
  python t64_wikidata_p571_import.py --apply             # insert into place_timeline_events

Match methods (in order of confidence):
  A) geo_cross_ref QID join: Wikidata QID đã map vào DILA → conf 0.85
  B) GPS bounding box:       ±0.005° (~0.5km) → conf 0.72
"""

import sys, io, os, json, time, argparse, sqlite3, math, re, urllib.request, urllib.parse
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB      = os.path.join(BASE, 'data', 'lineage.db')
CACHE   = os.path.join(BASE, 'data', 'wikidata_p571_temples.json')
LOG     = os.path.join(BASE, 'data', 't64_import_log.json')

SPARQL_URL = 'https://query.wikidata.org/sparql'
SPARQL_Q = """
SELECT ?place ?placeLabel ?lat ?lon (YEAR(?inception) AS ?year) WHERE {
  ?place wdt:P31/wdt:P279* wd:Q44613 .
  ?place wdt:P17 wd:Q148 .
  ?place wdt:P571 ?inception .
  OPTIONAL {
    ?place wdt:P625 ?coord .
    BIND(geof:latitude(?coord) AS ?lat)
    BIND(geof:longitude(?coord) AS ?lon)
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "zh,en" }
}
"""


# ── Download ──────────────────────────────────────────────────────────────────

def sparql_download():
    print('Downloading from Wikidata SPARQL...')
    params = urllib.parse.urlencode({'query': SPARQL_Q, 'format': 'json'})
    url = f'{SPARQL_URL}?{params}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'PTDA-BuddhistGIS/1.0 (phatphaponline.org; namthien@gmail.com)',
        'Accept': 'application/sparql-results+json'
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'SPARQL error: {e}')
        return None

    results = raw.get('results', {}).get('bindings', [])
    print(f'Raw SPARQL results: {len(results)} rows')

    temples = []
    for r in results:
        qid_full = r.get('place', {}).get('value', '')
        qid = qid_full.rsplit('/', 1)[-1] if '/' in qid_full else qid_full
        label = r.get('placeLabel', {}).get('value', '')
        year_v = r.get('year', {}).get('value', '')
        lat_v  = r.get('lat', {}).get('value', '')
        lon_v  = r.get('lon', {}).get('value', '')
        try:
            year = int(float(year_v)) if year_v else None
        except ValueError:
            year = None
        try:
            lat = float(lat_v) if lat_v else None
            lon = float(lon_v) if lon_v else None
        except ValueError:
            lat = lon = None
        if qid and year is not None:
            temples.append({'qid': qid, 'label': label, 'year': year, 'lat': lat, 'lon': lon})

    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump({'downloaded_at': datetime.now().isoformat(), 'count': len(temples), 'temples': temples}, f, ensure_ascii=False, indent=2)
    print(f'Saved {len(temples)} temples → {CACHE}')
    return temples


# ── Match ─────────────────────────────────────────────────────────────────────

def load_cache():
    with open(CACHE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['temples']


def load_existing_refs(conn):
    """Set of source_refs already in place_timeline_events for wikidata_p571."""
    rows = conn.execute(
        "SELECT source_ref FROM place_timeline_events WHERE source='wikidata_p571'"
    ).fetchall()
    return {r[0] for r in rows}


def method_a_geo_cross_ref(conn, temples, existing_refs):
    """QID → dila_id via geo_cross_ref table."""
    qid_to_dila = {r[0]: r[1] for r in conn.execute(
        'SELECT wikidata_qid, dila_id FROM geo_cross_ref WHERE wikidata_qid IS NOT NULL'
    ).fetchall()}

    matches = []
    for t in temples:
        ref = f"{t['qid']}·P571"
        if ref in existing_refs:
            continue
        dila_id = qid_to_dila.get(t['qid'])
        if dila_id:
            matches.append({
                'dila_id': dila_id, 'year': t['year'],
                'label_zh': t['label'], 'source_ref': ref,
                'confidence': 0.85, 'method': 'A:geo_cross_ref'
            })
    return matches


def method_b_gps_spatial(conn, temples, existing_refs, matched_qids):
    """GPS bounding box ±0.005° (~0.5km)."""
    # Load all DILA places with GPS
    places = conn.execute(
        'SELECT id, name_zh, geo_lat, geo_long FROM places_dila WHERE geo_lat IS NOT NULL AND geo_lat != 0'
    ).fetchall()

    # Build a simple grid bucket for fast lookup
    # bucket key = (round(lat,1), round(lon,1))
    grid = {}
    for p in places:
        pid, pname, plat, plon = p
        key = (round(plat, 1), round(plon, 1))
        grid.setdefault(key, []).append(p)

    # Already have dila_ids from method A — avoid double-matching same place
    existing_dila_p571 = {r[0] for r in conn.execute(
        "SELECT dila_id FROM place_timeline_events WHERE source='wikidata_p571'"
    ).fetchall()}

    DELTA = 0.005  # ~0.5 km
    matches = []
    for t in temples:
        if t['qid'] in matched_qids:
            continue
        ref = f"{t['qid']}·P571"
        if ref in existing_refs:
            continue
        if t['lat'] is None or t['lon'] is None:
            continue

        lat, lon = t['lat'], t['lon']
        bucket_key = (round(lat, 1), round(lon, 1))
        candidates = []
        for dk in [(0,0),(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            bk = (round(bucket_key[0] + dk[0]*0.1, 1), round(bucket_key[1] + dk[1]*0.1, 1))
            candidates.extend(grid.get(bk, []))

        best = None
        best_dist = DELTA
        for pid, pname, plat, plon in candidates:
            dlat = abs(lat - plat)
            dlon = abs(lon - plon)
            dist = math.sqrt(dlat**2 + dlon**2)
            if dist < best_dist and pid not in existing_dila_p571:
                best_dist = dist
                best = pid

        if best:
            matches.append({
                'dila_id': best, 'year': t['year'],
                'label_zh': t['label'], 'source_ref': ref,
                'confidence': 0.72, 'method': f'B:gps({best_dist:.5f}°)'
            })
    return matches


def find_all_matches(conn, temples):
    existing_refs = load_existing_refs(conn)
    print(f'Existing wikidata_p571 source_refs: {len(existing_refs)}')

    matches_a = method_a_geo_cross_ref(conn, temples, existing_refs)
    matched_qids = {m['source_ref'].split('·')[0] for m in matches_a}
    print(f'Method A (geo_cross_ref): {len(matches_a)} new matches')

    matches_b = method_b_gps_spatial(conn, temples, existing_refs, matched_qids)
    print(f'Method B (GPS ±0.005°): {len(matches_b)} new matches')

    return matches_a + matches_b


# ── Insert ────────────────────────────────────────────────────────────────────

def insert_matches(conn, matches):
    now = datetime.now().isoformat(timespec='seconds')
    inserted = skipped = 0
    for m in matches:
        try:
            conn.execute("""
                INSERT INTO place_timeline_events
                    (dila_id, event_type, year, label_zh, source, source_ref, confidence, created_at)
                VALUES (?, 'founding', ?, ?, 'wikidata_p571', ?, ?, ?)
            """, (m['dila_id'], m['year'], m['label_zh'], m['source_ref'], m['confidence'], now))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    return inserted, skipped


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download',  action='store_true', help='SPARQL → cache JSON')
    parser.add_argument('--dry-run',   action='store_true', help='Preview matches, no DB write')
    parser.add_argument('--apply',     action='store_true', help='Insert matches into DB')
    parser.add_argument('--verbose',   action='store_true', help='Print each match')
    args = parser.parse_args()

    if args.download:
        sparql_download()
        return

    if not os.path.exists(CACHE):
        print(f'Cache not found: {CACHE}')
        print('Run with --download first.')
        return

    temples = load_cache()
    print(f'Loaded {len(temples)} temples from cache')
    with_gps = sum(1 for t in temples if t['lat'] is not None)
    print(f'  {with_gps} have GPS coords | year range: {min(t["year"] for t in temples)}–{max(t["year"] for t in temples)}\n')

    conn = sqlite3.connect(DB)
    matches = find_all_matches(conn, temples)
    total = len(matches)
    print(f'\nTotal new matches: {total}')

    if args.verbose or args.dry_run:
        print(f'\n{"dila_id":<20} {"year":>5}  {"conf":>5}  {"method":<22}  label_zh')
        print('─'*90)
        for m in matches[:50]:
            print(f'{m["dila_id"]:<20} {m["year"]:>5}  {m["confidence"]:>5.2f}  {m["method"]:<22}  {m["label_zh"][:30]}')
        if total > 50:
            print(f'  ... ({total-50} more)')

    if args.dry_run:
        print(f'\n[DRY RUN] {total} rows would be inserted. Run --apply to commit.')
        conn.close()
        return

    if not args.apply:
        print('\nRun --dry-run to preview, or --apply to insert.')
        conn.close()
        return

    inserted, skipped = insert_matches(conn, matches)

    # Stats after insert
    total_tle = conn.execute('SELECT count(*) FROM place_timeline_events').fetchone()[0]
    wp571 = conn.execute("SELECT count(*) FROM place_timeline_events WHERE source='wikidata_p571'").fetchone()[0]
    places_total = conn.execute('SELECT count(*) FROM places_dila').fetchone()[0]
    covered = conn.execute('SELECT count(DISTINCT dila_id) FROM place_timeline_events').fetchone()[0]
    coverage_pct = 100.0 * covered / places_total

    print(f'\n[APPLY] Inserted: {inserted} | Skipped (dup): {skipped}')
    print(f'place_timeline_events total: {total_tle:,}')
    print(f'wikidata_p571 rows: {wp571}')
    print(f'Timeline coverage: {covered:,}/{places_total:,} = {coverage_pct:.2f}%')

    log = {
        'task': 'T64', 'run_at': datetime.now().isoformat(),
        'cache_temples': len(temples),
        'matches_a': sum(1 for m in matches if m['method'].startswith('A')),
        'matches_b': sum(1 for m in matches if m['method'].startswith('B')),
        'inserted': inserted, 'skipped': skipped,
        'total_tle': total_tle, 'wikidata_p571': wp571,
        'coverage_pct': round(coverage_pct, 4)
    }
    with open(LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f'Log → {LOG}')

    conn.close()
    print('\nDone.')


if __name__ == '__main__':
    main()
