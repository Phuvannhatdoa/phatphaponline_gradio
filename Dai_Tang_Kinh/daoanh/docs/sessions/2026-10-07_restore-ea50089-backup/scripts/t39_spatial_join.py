"""
t39_spatial_join.py — T39 Phase 2: Spatial join Wikidata items với DILA places
===============================================================================
Join: wikidata_item.{lat,lon} ↔ places_dila.{geo_lat,geo_long}
Filter: Haversine distance ≤ 0.5km AND name_similarity ≥ 0.4

Input:  data/t39_wikidata_p571_raw.json
        data/lineage.db (places_dila + place_timeline_events)
Output: data/t39_matched_pairs.json

Cách dùng:
    python scripts/t39_spatial_join.py
    python scripts/t39_spatial_join.py --radius 1.0      # mở rộng radius km
    python scripts/t39_spatial_join.py --min-sim 0.3     # giảm threshold
    python scripts/t39_spatial_join.py --report           # chỉ in stats, không save
"""
import argparse, json, math, re, sys, io, sqlite3
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

INPUT_JSON = Path('data/t39_wikidata_p571_raw.json')
OUTPUT_JSON = Path('data/t39_matched_pairs.json')
DB_PATH = 'data/lineage.db'


# ── Haversine ─────────────────────────────────────────────────────────────────
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ── Name similarity ────────────────────────────────────────────────────────────
def normalize_name(s: str) -> str:
    """Strip spaces, parentheses, direction suffixes for comparison."""
    s = re.sub(r'[（(][^）)]{0,10}[）)]', '', s)       # strip parens
    s = re.sub(r'[寺院庵堂塔祠廟観\s]', '', s)          # strip common suffixes & spaces
    return s.strip()


def char_overlap(a: str, b: str) -> float:
    """Fraction of unique chars in shorter string that appear in longer string."""
    if not a or not b:
        return 0.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if not shorter:
        return 0.0
    hits = sum(1 for c in set(shorter) if c in longer)
    return hits / len(set(shorter))


def name_sim(wikidata_zh: str, dila_zh: str, dila_vi: str) -> float:
    """Combined similarity: exact match, substring, char-overlap."""
    wn = normalize_name(wikidata_zh)
    dn = normalize_name(dila_zh)

    if not wn or not dn:
        return 0.0

    # Exact match after normalization
    if wn == dn:
        return 1.0

    # Substring containment
    if wn in dn or dn in wn:
        shorter = min(len(wn), len(dn))
        longer = max(len(wn), len(dn))
        return 0.7 + 0.3 * (shorter / longer)

    # Char overlap
    return char_overlap(wn, dn)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--radius', type=float, default=0.5, help='Max distance km (default 0.5)')
    parser.add_argument('--min-sim', type=float, default=0.4, help='Min name similarity (default 0.4)')
    parser.add_argument('--report', action='store_true', help='Stats only, không save')
    args = parser.parse_args()

    if not INPUT_JSON.exists():
        print(f'[ERROR] {INPUT_JSON} not found — chạy t39_wikidata_p571_download.py trước')
        sys.exit(1)

    data = json.loads(INPUT_JSON.read_text(encoding='utf-8'))
    wikidata_items = data['items']
    print(f'[T39] Wikidata items: {len(wikidata_items)}')

    # Load DILA places với GPS
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id AS place_id, p.name_zh, p.name_en,
               CAST(p.geo_lat AS REAL) AS lat, CAST(p.geo_long AS REAL) AS lon,
               ec.object_text AS name_vi
        FROM places_dila p
        LEFT JOIN entity_claims ec ON ec.entity_id = p.id
            AND ec.predicate = 'vietnameseName' AND ec.source_id = 5
        WHERE p.geo_lat IS NOT NULL AND p.geo_lat != ''
          AND p.geo_long IS NOT NULL AND p.geo_long != ''
          AND p.note_category LIKE '%寺廟%'
    """)
    dila_places = [dict(r) for r in cur.fetchall()]
    print(f'[T39] DILA temple places with GPS: {len(dila_places)}')

    # Already-imported Wikidata source_refs
    cur.execute("SELECT source_ref FROM place_timeline_events WHERE source='wikidata'")
    existing_refs = {r[0] for r in cur.fetchall()}
    print(f'[T39] Existing Wikidata entries in timeline: {len(existing_refs)}')

    # Also track dila_ids already in timeline (any source) to allow duplicates check
    cur.execute("SELECT DISTINCT dila_id FROM place_timeline_events WHERE source='wikidata'")
    existing_wikidata_dila_ids = {r[0] for r in cur.fetchall()}

    conn.close()

    # ── Spatial join ──────────────────────────────────────────────────────────
    matches = []
    multi_match_wikidata = 0  # wikidata items matching >1 DILA place
    already_imported = 0
    low_sim = 0
    too_far = 0

    for wi in wikidata_items:
        qid = wi['qid']
        source_ref = f"{qid}·P571"

        if source_ref in existing_refs:
            already_imported += 1
            continue

        w_lat, w_lon = wi['lat'], wi['lon']
        w_zh = wi.get('label_zh', '')

        candidates = []
        for dp in dila_places:
            d_lat, d_lon = dp['lat'], dp['lon']
            dist = haversine_km(w_lat, w_lon, d_lat, d_lon)
            if dist > args.radius:
                too_far += 1
                continue

            sim = name_sim(w_zh, dp.get('name_zh', ''), dp.get('name_vi', ''))
            if sim < args.min_sim:
                low_sim += 1
                continue

            candidates.append({
                'dila_id': dp['place_id'],
                'dila_name_zh': dp.get('name_zh', ''),
                'dila_name_vi': dp.get('name_vi', ''),
                'dist_km': round(dist, 4),
                'name_sim': round(sim, 4),
                'score': round(sim / (dist + 0.1), 4),  # composite rank score
            })

        if not candidates:
            continue

        if len(candidates) > 1:
            multi_match_wikidata += 1
            candidates.sort(key=lambda c: -c['score'])

        best = candidates[0]
        matches.append({
            'qid': qid,
            'source_ref': source_ref,
            'wikidata_label_zh': w_zh,
            'wikidata_label_en': wi.get('label_en', ''),
            'wikidata_lat': w_lat,
            'wikidata_lon': w_lon,
            'year': wi['year'],
            'inception_raw': wi.get('inception_raw', ''),
            'dila_id': best['dila_id'],
            'dila_name_zh': best['dila_name_zh'],
            'dila_name_vi': best['dila_name_vi'],
            'dist_km': best['dist_km'],
            'name_sim': best['name_sim'],
            'score': best['score'],
            'is_new_dila_id': best['dila_id'] not in existing_wikidata_dila_ids,
            'all_candidates': len(candidates),
        })

    # Dedup: if same dila_id matched by multiple wikidata items, take the best
    by_dila: dict[str, dict] = {}
    for m in matches:
        did = m['dila_id']
        if did not in by_dila or m['score'] > by_dila[did]['score']:
            by_dila[did] = m
    deduped = list(by_dila.values())
    new_dila = [m for m in deduped if m['is_new_dila_id']]

    print(f'[T39] ── Results ──────────────────────────────────')
    print(f'[T39] Matched pairs (before dila dedup): {len(matches)}')
    print(f'[T39] Unique DILA places matched: {len(deduped)}')
    print(f'[T39] NEW dila_ids (not yet in timeline): {len(new_dila)}')
    print(f'[T39] Already imported (skip): {already_imported}')
    print(f'[T39] Wikidata items with multiple DILA candidates: {multi_match_wikidata}')

    # Quality buckets
    high_conf = [m for m in deduped if m['name_sim'] >= 0.8]
    med_conf  = [m for m in deduped if 0.5 <= m['name_sim'] < 0.8]
    low_conf  = [m for m in deduped if m['name_sim'] < 0.5]
    print(f'[T39] High confidence (sim≥0.8): {len(high_conf)}')
    print(f'[T39] Med confidence (0.5≤sim<0.8): {len(med_conf)}')
    print(f'[T39] Low confidence (sim<0.5): {len(low_conf)}')

    # Sample matches
    print(f'\n[T39] Top 10 by score:')
    for m in sorted(deduped, key=lambda x: -x['score'])[:10]:
        print(f"  {m['qid']} {m['wikidata_label_zh'][:12]:12} → {m['dila_id']} {m['dila_name_zh'][:12]:12} "
              f"dist={m['dist_km']:.3f}km sim={m['name_sim']:.2f}")

    print(f'\n[T39] Low sim samples (potential FP):')
    for m in sorted(low_conf, key=lambda x: x['name_sim'])[:5]:
        print(f"  {m['qid']} {m['wikidata_label_zh'][:12]:12} → {m['dila_id']} {m['dila_name_zh'][:12]:12} "
              f"dist={m['dist_km']:.3f}km sim={m['name_sim']:.2f}")

    if args.report:
        return

    OUTPUT_JSON.write_text(json.dumps({
        'meta': {
            'radius_km': args.radius,
            'min_sim': args.min_sim,
            'total_matched': len(deduped),
            'new_dila_ids': len(new_dila),
            'high_conf': len(high_conf),
            'med_conf': len(med_conf),
            'low_conf': len(low_conf),
        },
        'matches': deduped,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n[T39] Saved {len(deduped)} matches to {OUTPUT_JSON}')


if __name__ == '__main__':
    main()
