"""T64b — Wikidata P571 Phase 2: name_zh match sau khi convert simplified→traditional.

Root cause của Phase 1 gap: Wikidata labels dùng giản thể (龙), DILA name_zh dùng phồn thể (龍).
Giải pháp: opencc s2t convert Wikidata label → exact match DILA name_zh.
Với ambiguous (>1 DILA cùng tên): dùng GPS để chọn gần nhất (nếu có).

Phụ thuộc: opencc  (pip install opencc-python-reimplemented)

Usage:
  python t64b_wikidata_name_match.py              # dry-run: count + top 30 mẫu
  python t64b_wikidata_name_match.py --apply      # insert vào place_timeline_events
"""

import sys, io, os, json, argparse, sqlite3, math
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import opencc
    CC = opencc.OpenCC('s2t')
except ImportError:
    print('ERROR: pip install opencc-python-reimplemented')
    sys.exit(1)

BASE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB    = os.path.join(BASE, 'data', 'lineage.db')
CACHE = os.path.join(BASE, 'data', 'wikidata_p571_temples.json')
LOG   = os.path.join(BASE, 'data', 't64b_import_log.json')

GPS_MAX_KM = 50.0   # GPS disambiguation ceiling — nếu DILA gần nhất > 50km thì skip


def dist_km(lat1, lon1, lat2, lon2):
    dlat = abs(lat1 - lat2) * 111.0
    dlon = abs(lon1 - lon2) * 96.0
    return math.sqrt(dlat**2 + dlon**2)


def build_name_index(conn):
    """DILA name_zh → list of (dila_id, geo_lat, geo_long)."""
    idx = {}
    rows = conn.execute(
        'SELECT id, name_zh, geo_lat, geo_long FROM places_dila WHERE name_zh IS NOT NULL'
    ).fetchall()
    for pid, nzh, lat, lon in rows:
        if nzh:
            idx.setdefault(nzh.strip(), []).append((pid, lat or 0.0, lon or 0.0))
    return idx


def load_existing_refs(conn):
    return {r[0] for r in conn.execute(
        "SELECT source_ref FROM place_timeline_events WHERE source='wikidata_p571'"
    ).fetchall()}


def find_matches(conn, temples):
    name_index    = build_name_index(conn)
    existing_refs = load_existing_refs(conn)
    gcr_qids      = {r[0] for r in conn.execute(
        'SELECT wikidata_qid FROM geo_cross_ref WHERE wikidata_qid IS NOT NULL'
    ).fetchall()}

    matches = []
    skipped_ambiguous = 0

    for t in temples:
        ref = f"{t['qid']}·P571"
        if ref in existing_refs:
            continue
        if t['qid'] in gcr_qids:
            continue
        label = (t.get('label') or '').strip()
        if not label:
            continue

        label_trad = CC.convert(label)
        dila_hits  = name_index.get(label_trad, [])
        if not dila_hits:
            continue

        wlat, wlon = t.get('lat'), t.get('lon')

        if len(dila_hits) == 1:
            dila_id, dlat, dlon = dila_hits[0]
            if wlat and dlat and (dlat != 0 or dlon != 0):
                km = dist_km(wlat, wlon, dlat, dlon)
                if km > GPS_MAX_KM:
                    # GPS mâu thuẫn — tên trùng, chùa khác vùng → skip
                    skipped_ambiguous += 1
                    continue
                conf   = 0.80
                method = f'name_s2t(1hit,{km:.1f}km)'
            else:
                # Không có GPS để kiểm tra — chỉ accept nếu tên dài ≥3 ký tự
                if len(label_trad) < 3:
                    skipped_ambiguous += 1
                    continue
                conf   = 0.65
                method = 'name_s2t(1hit,no-gps)'
            matches.append({
                'dila_id': dila_id, 'year': t['year'],
                'label_zh': label_trad, 'source_ref': ref,
                'confidence': conf, 'method': method
            })

        else:
            # Ambiguous: cần GPS để chọn
            if wlat is None:
                skipped_ambiguous += 1
                continue
            # Chọn DILA gần nhất
            best_id, best_km = None, float('inf')
            for pid, dlat, dlon in dila_hits:
                if dlat == 0 and dlon == 0:
                    continue
                km = dist_km(wlat, wlon, dlat, dlon)
                if km < best_km:
                    best_km, best_id = km, pid
            if best_id and best_km <= GPS_MAX_KM:
                matches.append({
                    'dila_id': best_id, 'year': t['year'],
                    'label_zh': label_trad, 'source_ref': ref,
                    'confidence': 0.72, 'method': f'name_s2t({len(dila_hits)}hits,gps{best_km:.1f}km)'
                })
            else:
                skipped_ambiguous += 1

    # Dedup: nếu cùng (dila_id, year) từ nhiều Wikidata QIDs → giữ conf cao nhất
    seen = {}
    for m in matches:
        key = (m['dila_id'], m['year'])
        if key not in seen or m['confidence'] > seen[key]['confidence']:
            seen[key] = m
    matches = list(seen.values())

    return matches, skipped_ambiguous


def insert_matches(conn, matches):
    now = datetime.now().isoformat(timespec='seconds')
    inserted = skipped = 0
    for m in matches:
        try:
            conn.execute("""
                INSERT INTO place_timeline_events
                    (dila_id, event_type, year, label_zh, source, source_ref, confidence, created_at)
                VALUES (?, 'founding', ?, ?, 'wikidata_p571', ?, ?, ?)
            """, (m['dila_id'], m['year'], m['label_zh'], m['source_ref'],
                  m['confidence'], now))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    return inserted, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',   action='store_true')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(CACHE):
        print(f'Cache không tồn tại: {CACHE}')
        print('Chạy t64_wikidata_p571_import.py --download trước.')
        sys.exit(1)

    cache   = json.load(open(CACHE, encoding='utf-8'))
    temples = cache['temples']
    print(f'Loaded {len(temples)} temples từ cache (downloaded {cache["downloaded_at"][:10]})\n')

    conn = sqlite3.connect(DB)
    matches, skipped_amb = find_matches(conn, temples)

    print(f'Matches tìm được: {len(matches)}')
    print(f'Bỏ qua (ambiguous, không GPS): {skipped_amb}')

    by_method = {}
    for m in matches:
        key = m['method'].split('(')[0]
        by_method[key] = by_method.get(key, 0) + 1
    for k, v in sorted(by_method.items()): print(f'  {k}: {v}')

    print(f'\n{"dila_id":<20} {"year":>5}  {"conf":>5}  {"method":<30}  label_zh')
    print('─' * 90)
    for m in matches[:30]:
        print(f'{m["dila_id"]:<20} {m["year"]:>5}  {m["confidence"]:>5.2f}  {m["method"]:<30}  {m["label_zh"]}')
    if len(matches) > 30:
        print(f'  ... ({len(matches)-30} more)')

    if not args.apply:
        print(f'\n[DRY RUN] {len(matches)} rows sẽ được insert. Chạy --apply để commit.')
        conn.close()
        return

    inserted, dup = insert_matches(conn, matches)

    total_tle  = conn.execute('SELECT count(*) FROM place_timeline_events').fetchone()[0]
    wp571      = conn.execute("SELECT count(*) FROM place_timeline_events WHERE source='wikidata_p571'").fetchone()[0]
    covered    = conn.execute('SELECT count(DISTINCT dila_id) FROM place_timeline_events').fetchone()[0]
    total_pl   = conn.execute('SELECT count(*) FROM places_dila').fetchone()[0]
    coverage   = 100.0 * covered / total_pl

    print(f'\n[APPLY] Inserted: {inserted} | Skipped (dup): {dup}')
    print(f'place_timeline_events total: {total_tle:,}')
    print(f'wikidata_p571 rows: {wp571}')
    print(f'Timeline coverage: {covered:,}/{total_pl:,} = {coverage:.2f}%')

    log = {
        'task': 'T64b', 'run_at': datetime.now().isoformat(),
        'cache_temples': len(temples),
        'matches_found': len(matches),
        'skipped_ambiguous': skipped_amb,
        'inserted': inserted, 'dup': dup,
        'total_tle': total_tle, 'wikidata_p571': wp571,
        'coverage_pct': round(coverage, 4)
    }
    with open(LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f'Log → {LOG}')

    conn.close()
    print('\nDone.')


if __name__ == '__main__':
    main()
