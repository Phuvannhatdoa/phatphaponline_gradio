"""
T31: BGIS GPS enrichment — spatial join BGIS monasteries ↔ DILA places.

SOURCE: BGIS 2006 Temple Data Version 1.1
  Edited by Jiang Wu (University of Arizona), GIS Editor: Lex Berman
  doi:10.7910/DVN/VAYEUZ  — distributed through BGIS, CHGIS, ECAI
  NOTE: YEAR_START = 2006 for all rows = publication year, NOT founding date.

WHAT THIS SCRIPT DOES:
  1. Load BGIS XLS (18,938 Buddhist sites with GPS)
  2. Spatial join ±0.5km against DILA places_dila with GPS
  3. Populate geo_cross_ref.bgis_id for matched places
  4. Optionally fill geo_lat/geo_long for 172 DILA places missing GPS

Usage:
  python scripts/bgis_spatial_join.py [--dry-run] [--radius 0.5] [--verbose]
"""

import sys, os, math, sqlite3, datetime, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BGIS_XLS = os.path.join(BASE_DIR, 'data', 'dila_import', 'Bgis', 'BGIS_v1-1_20130306.xls')
DB_PATH  = os.path.join(BASE_DIR, 'data', 'lineage.db')

# ── field indices in the XLS (verified from inspect_bgis.py) ──────────────────
F = {
    'BGIS_ID':   1,
    'NM_HZ':     3,
    'NM_ENG':    2,
    'TYPE_ENG':  4,
    'TYPE_HZ':   5,
    'PROV_HZ':   7,
    'CITY_HZ':   9,
    'YEAR_START':29,
    'LAT':       39,   # NEW_LAT
    'LNG':       40,   # NEW_LONG
}

MONASTERY_TYPES = {'monastery', 'temple', 'chapel', 'cave', 'Shrine', 'hall', 'house'}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(min(a, 1.0)))


def load_bgis(xls_path):
    try:
        import xlrd
    except ImportError:
        print("ERROR: xlrd not installed. Run: pip install xlrd", file=sys.stderr)
        sys.exit(1)

    wb = xlrd.open_workbook(xls_path, encoding_override='gbk')
    ws = wb.sheet_by_index(0)
    records = []
    for r in range(1, ws.nrows):
        try:
            lat = float(ws.cell_value(r, F['LAT']))
            lng = float(ws.cell_value(r, F['LNG']))
        except (ValueError, TypeError):
            continue
        if lat < 10 or lng < 70:
            continue
        typ = str(ws.cell_value(r, F['TYPE_ENG']) or '').strip()
        records.append({
            'bgis_id': str(int(ws.cell_value(r, F['BGIS_ID']))),
            'nm_hz':   str(ws.cell_value(r, F['NM_HZ']) or '').strip(),
            'nm_eng':  str(ws.cell_value(r, F['NM_ENG']) or '').strip(),
            'type':    typ,
            'prov':    str(ws.cell_value(r, F['PROV_HZ']) or '').strip(),
            'lat':     lat,
            'lng':     lng,
        })
    return records


def load_dila_places(conn, category_filter='%寺廟%'):
    """Load DILA places with GPS from places_dila."""
    rows = conn.execute("""
        SELECT id, name_zh, geo_lat, geo_long, note_category
        FROM places_dila
        WHERE geo_lat IS NOT NULL AND geo_lat != ''
        AND note_category LIKE ?
    """, (category_filter,)).fetchall()
    result = []
    for (pid, nm, lat, lng, cat) in rows:
        try:
            result.append({
                'dila_id': pid,
                'name_zh': nm or '',
                'lat': float(lat),
                'lng': float(lng),
                'cat': cat or '',
            })
        except (ValueError, TypeError):
            continue
    return result


def load_dila_no_gps(conn, category_filter='%寺廟%'):
    """Load DILA places WITHOUT GPS — candidates for GPS enrichment."""
    rows = conn.execute("""
        SELECT id, name_zh, note_category
        FROM places_dila
        WHERE (geo_lat IS NULL OR geo_lat = '')
        AND note_category LIKE ?
    """, (category_filter,)).fetchall()
    return [{'dila_id': r[0], 'name_zh': r[1] or '', 'cat': r[2] or ''} for r in rows]


def spatial_join(bgis_records, dila_places, radius_km=0.5, verbose=False):
    """
    For each BGIS record, find the nearest DILA place within radius_km.
    Returns list of match dicts, one per unique DILA place (best BGIS match).
    """
    if not bgis_records or not dila_places:
        return []

    # Build a simple bounding-box pre-filter bucket
    from collections import defaultdict
    BUCKET_SIZE = 0.5  # degrees, ~55km
    dila_bucket = defaultdict(list)
    for d in dila_places:
        bk = (int(d['lat'] / BUCKET_SIZE), int(d['lng'] / BUCKET_SIZE))
        dila_bucket[bk].append(d)

    matches = {}  # dila_id → best match

    for bg in bgis_records:
        blat, blng = bg['lat'], bg['lng']
        # Check neighbouring buckets
        bl = int(blat / BUCKET_SIZE)
        blo = int(blng / BUCKET_SIZE)
        candidates = []
        for dl in [bl-1, bl, bl+1]:
            for dlo in [blo-1, blo, blo+1]:
                candidates.extend(dila_bucket.get((dl, dlo), []))

        best_dist, best_dila = 999.0, None
        for d in candidates:
            dist = haversine_km(blat, blng, d['lat'], d['lng'])
            if dist < best_dist:
                best_dist, best_dila = dist, d

        if best_dist <= radius_km and best_dila:
            did = best_dila['dila_id']
            sim = name_similarity(best_dila['name_zh'], bg['nm_hz'])
            if did not in matches or matches[did]['dist_km'] > best_dist:
                matches[did] = {
                    'dila_id': did,
                    'dila_name': best_dila['name_zh'],
                    'bgis_id': bg['bgis_id'],
                    'bgis_name': bg['nm_hz'],
                    'bgis_type': bg['type'],
                    'bgis_prov': bg['prov'],
                    'dist_km': best_dist,
                    'name_sim': sim,
                }
            if verbose:
                print(f"  MATCH {best_dist:.3f}km: DILA '{best_dila['name_zh']}' ↔ BGIS '{bg['nm_hz']}'")

    return list(matches.values())


# Common simplified→traditional mappings for Buddhist place names
_SIMP_TO_TRAD = str.maketrans(
    '宝莲禅华广兴灵寿观释净明觉万灵总觉极乐弥陀弥勒药师阿弥陀佛罗汉长庆应觉元净'
    '龙凤灵祥慈济远通兴达隆复兴福庆庄严众远澳门东西南北中',
    '寶蓮禪華廣興靈壽觀釋淨明覺萬靈總覺極樂彌陀彌勒藥師阿彌陀佛羅漢長慶應覺元淨'
    '龍鳳靈祥慈濟遠通興達隆復興福慶莊嚴眾遠澳門東西南北中'
)

def simp_to_trad(s):
    """Simple character-level simplified→traditional for common Buddhist names."""
    return (s or '').translate(_SIMP_TO_TRAD)

def name_similarity(a, b):
    """Name similarity after simplified→traditional normalization."""
    a = simp_to_trad((a or '').strip())
    b = simp_to_trad((b or '').strip())
    if not a or not b:
        return 0.0
    # Character set overlap
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    overlap = len(set_a & set_b)
    union = len(set_a | set_b)
    jaccard = overlap / union
    # Also check leading shared chars (order matters for Chinese names)
    shared_seq = sum(1 for ca, cb in zip(a, b) if ca == cb)
    seq_ratio = shared_seq / max(len(a), len(b))
    return max(jaccard, seq_ratio)


def main():
    parser = argparse.ArgumentParser(description='BGIS GPS spatial join → DILA places_dila')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to DB')
    parser.add_argument('--radius', type=float, default=0.5, help='Match radius in km (default 0.5)')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--fill-gps', action='store_true', help='Also fill missing GPS for no-GPS DILA places')
    args = parser.parse_args()

    print(f"=== BGIS Spatial Join ETL  (radius={args.radius}km) ===")
    print(f"XLS: {BGIS_XLS}")

    # ── Load BGIS ──────────────────────────────────────────────────────────────
    print("\n[1] Loading BGIS XLS...")
    bgis = load_bgis(BGIS_XLS)
    bgis_temple = [b for b in bgis if b['type'] in MONASTERY_TYPES]
    print(f"  Total BGIS: {len(bgis)} | Temple types only: {len(bgis_temple)}")

    # ── Load DILA ─────────────────────────────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    print("\n[2] Loading DILA places (寺廟 category, with GPS)...")
    dila_places = load_dila_places(conn)
    print(f"  DILA places with GPS: {len(dila_places)}")

    dila_no_gps = load_dila_no_gps(conn)
    print(f"  DILA places without GPS: {len(dila_no_gps)}")

    # ── Already mapped ─────────────────────────────────────────────────────────
    already = {r[0] for r in conn.execute(
        "SELECT dila_id FROM geo_cross_ref WHERE bgis_id IS NOT NULL AND bgis_id != ''"
    ).fetchall()}
    print(f"  Already have bgis_id: {len(already)}")

    # ── Spatial join ─────────────────────────────────────────────────────────
    print(f"\n[3] Spatial join (radius={args.radius}km)...")
    matches = spatial_join(bgis_temple, dila_places, radius_km=args.radius, verbose=args.verbose)
    new_matches = [m for m in matches if m['dila_id'] not in already]
    print(f"  Total matches: {len(matches)}")
    print(f"  New (not yet in geo_cross_ref): {len(new_matches)}")

    # ── Sample for review ─────────────────────────────────────────────────────
    print(f"\n[4] Sample of top 30 new matches (review for accuracy):")
    import random
    sample = sorted(new_matches, key=lambda x: x['dist_km'])[:30]
    for m in sample:
        sim = m.get('name_sim', name_similarity(m['dila_name'], m['bgis_name']))
        flag = '' if sim >= 0.3 else ' ⚠️ name mismatch'
        print(f"  {m['dist_km']:.3f}km | DILA '{m['dila_name']}' ↔ BGIS '{m['bgis_name']}' [{m['bgis_type']}] sim={sim:.2f}{flag}")

    name_mismatch = sum(1 for m in new_matches if m.get('name_sim', 0) < 0.3)
    print(f"\n  Name similarity <30%: {name_mismatch}/{len(new_matches)} ({name_mismatch/max(1,len(new_matches))*100:.0f}%)")

    if args.dry_run:
        print("\n[DRY RUN] No changes written to DB.")
        conn.close()
        return

    # ── Backup ────────────────────────────────────────────────────────────────
    today = datetime.date.today().isoformat()
    backup = DB_PATH + f'.bak.{today}'
    if not os.path.exists(backup):
        import shutil
        shutil.copy(DB_PATH, backup)
        print(f"\n[5] Backup created: {backup}")
    else:
        print(f"\n[5] Backup already exists: {backup}")

    # ── Insert into geo_cross_ref ─────────────────────────────────────────────
    # NOTE: BGIS coordinates are frequently county/town centroids — verified
    # 2026-08-24 that 83.5% of BGIS rows SHARE a coordinate with ≥1 other
    # temple (some centroids shared by 100+ entries). Distance alone is NOT
    # a reliable match signal here. Name similarity is now a hard gate.
    NAME_SIM_THRESHOLD = 0.4
    inserted = 0
    updated = 0
    skipped_low_sim = 0
    for m in new_matches:
        sim = m.get('name_sim', name_similarity(m['dila_name'], m['bgis_name']))
        if sim < NAME_SIM_THRESHOLD:
            skipped_low_sim += 1
            continue  # cannot trust proximity alone given centroid geocoding
        conf = 'bgis_spatial_verified' if sim >= 0.6 else 'bgis_spatial_likely'

        note = (f"bgis_spatial_join ±{m['dist_km']:.3f}km sim={sim:.2f}"
                f" BGIS '{m['bgis_name']}' [{m['bgis_type']}]")
        # Insert or update
        existing = conn.execute(
            "SELECT id, bgis_id FROM geo_cross_ref WHERE dila_id = ?", (m['dila_id'],)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE geo_cross_ref SET bgis_id=?, notes=? WHERE dila_id=?",
                (m['bgis_id'], note, m['dila_id'])
            )
            updated += 1
        else:
            conn.execute("""
                INSERT INTO geo_cross_ref
                (dila_id, bgis_id, confidence, mapped_by, notes, created_at)
                VALUES (?, ?, ?, 'bgis_spatial_join', ?, datetime('now'))
            """, (m['dila_id'], m['bgis_id'], conf, note))
            inserted += 1

    conn.commit()
    print(f"\n[6] geo_cross_ref: inserted={inserted}, updated={updated}, "
          f"skipped(sim<{NAME_SIM_THRESHOLD})={skipped_low_sim}")

    # ── GPS fill for missing-GPS DILA places ─────────────────────────────────
    if args.fill_gps and dila_no_gps:
        print(f"\n[7] GPS fill for {len(dila_no_gps)} DILA places missing GPS...")
        filled = 0
        for d in dila_no_gps:
            # Find best BGIS match by name
            best_sim, best_bg = 0.0, None
            for bg in bgis_temple:
                sim = name_similarity(d['name_zh'], bg['nm_hz'])
                if sim > best_sim:
                    best_sim, best_bg = sim, bg
            if best_sim >= 0.5 and best_bg:
                conn.execute(
                    "UPDATE places_dila SET geo_lat=?, geo_long=? WHERE id=?",
                    (best_bg['lat'], best_bg['lng'], d['dila_id'])
                )
                print(f"  GPS filled: {d['dila_id']} '{d['name_zh']}' ← BGIS '{best_bg['nm_hz']}' sim={best_sim:.2f}")
                filled += 1
        conn.commit()
        print(f"  GPS filled for {filled} DILA places")

    conn.close()
    print(f"\n=== Done. Check geo_cross_ref for bgis_id entries. ===")


if __name__ == '__main__':
    main()
