# -*- coding: utf-8 -*-
"""T242 — Merge + validate T0/T1/T2 → places_vn (RAW) / places_vn_pending (STAGING).

Đặc tả: docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-vietnam-consolidated.md (M7-VN)
  places_vn 17 cột mirror DILA, ID 'VN'+10 số, bbox VN (lat 8-24, lon 102-110),
  3-Layer: places_vn (RAW) → places_vn_pending (STAGING) → places (FINAL, sau này).
  KHÔNG ghi đè places_dila / places / entity.

Nguồn record đọc từ data/*.json (phải chạy t0/t1/t2 + geocode trước):
  data/vn_places_t0_wikidata.json               → accuracy 'dila_exact'
  data/vn_places_t1_osm.json                    → accuracy 'osm_centroid'
  data/vn_places_t2_disantongiao_geocoded.json  → accuracy 'geocode_street'
  (records pending trong geocoded → places_vn_pending lý do no_gps)

Chạy:
  python scripts/vn_places_merge_validate.py --apply       # import DB
  python scripts/vn_places_merge_validate.py --dry-run     # chỉ báo cáo
  python scripts/vn_places_merge_validate.py --revert      # DROP 2 bảng + xoá source đăng ký

Idempotent (INSERT OR IGNORE theo PK id VN+10). Revert an toàn vì 2 bảng là mới
tạo trong build T242 (additive → drop không mất dữ liệu cũ).
"""

import sys, io, os, json, time, re, math, hashlib, argparse, sqlite3, unicodedata

if getattr(sys.stdout, 'encoding', 'utf-8').lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'data', 'lineage.db')
DATA = os.path.join(BASE, 'data')
REPORT = os.path.join(DATA, 'vn_places_merge_report.json')

T0 = os.path.join(DATA, 'vn_places_t0_wikidata.json')
T1 = os.path.join(DATA, 'vn_places_t1_osm.json')
T2G = os.path.join(DATA, 'vn_places_t2_disantongiao_geocoded.json')

# Bbox lãnh thổ VN (đặc tả M7-VN)
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 8.0, 24.0, 102.0, 110.0

# 17 cột theo đặc tả M7-VN (mirror DILA, raw_source thay raw_xml)
PLACES_VN_DDL = """
CREATE TABLE IF NOT EXISTS places_vn (
    id              TEXT PRIMARY KEY,
    name_vi         TEXT,
    name_zh         TEXT,
    district        TEXT,
    note_category   TEXT,
    listbibl        TEXT,
    geo_lat         REAL,
    geo_long        REAL,
    name_en         TEXT,
    name_other      TEXT,
    sect            TEXT,
    founding_year   TEXT,
    heritage_status TEXT,
    status          TEXT DEFAULT 'unknown',
    source          TEXT,
    accuracy        TEXT,
    raw_source      TEXT
);
"""

DATASET_SOURCES = [
    dict(name='WIKIDATA', source_type='knowledge_base',
         origin_url='https://www.wikidata.org', license='CC0 1.0',
         usage_level='GREEN', attribution_text='Wikidata contributors (CC0 1.0)',
         notes='T242 T0 - GPS chua VN P625 via SPARQL'),
    dict(name='OPENSTREETMAP', source_type='open_data',
         origin_url='https://www.openstreetmap.org', license='ODbL 1.0',
         usage_level='GREEN', attribution_text='OpenStreetMap contributors (ODbL)',
         notes='T242 T1 - Overpass area VN place_of_worship/historic=temple'),
    dict(name='DISANTONGIAO_VN', source_type='web_catalog',
         origin_url='https://disantongiao.vn/co-so-du-lieu-chua-viet.html',
         license='CC BY 4.0 (ghi ro nguon disantongiao.vn)', usage_level='YELLOW',
         attribution_text='disantongiao.vn',
         notes='YELLOW cho toi khi Admin xac minh trang dieu khoan cho phep su dung lai co ghi nguon'),
]
GEOCODER_SOURCES = {
    'nominatim': dict(name='OPENSTREETMAP_NOMINATIM', source_type='geocoder',
                      origin_url='https://nominatim.openstreetmap.org',
                      license='ODbL 1.0', usage_level='GREEN',
                      attribution_text='OpenStreetMap contributors (ODbL)',
                      notes='Nominatim free 1 req/s + cache geocode (T242 T2)'),
    'google': dict(name='GOOGLE_GEOCODING', source_type='geocoder',
                   origin_url='https://maps.googleapis.com/maps/api/geocode/json',
                   license='Google Maps Platform ToS', usage_level='YELLOW',
                   attribution_text='Google Geocoding API',
                   notes='quota free ~5000/thang; key tu env GOOGLE_MAPS_API_KEY, cache bat buoc'),
}

NOTE_CATEGORY_RULES = [
    (re.compile(r't[hôo][  ]?[dđ][ìi]nh', re.I | re.U), 'tổ đình'),
    (re.compile(r'thi[e]?n[  ]?vi[e]?n', re.I | re.U), 'thiền viện'),
    (re.compile(r't[ịi]nh x[áa]', re.I | re.U), 'tịnh xá'),
    (re.compile(r'ni[e]?m ph[ậa]t [dđ][ưu][ờo]ng', re.I | re.U), 'niệm Phật đường'),
    (re.compile(r'tu vi[e]?n', re.I | re.U), 'tu viện'),
    (re.compile(r't[ựu][  ]?vi[e]?n', re.I | re.U), 'tự viện'),
    (re.compile(r'[dđ][ềe]n', re.I | re.U), 'đền'),
    (re.compile(r'am( |$)', re.I | re.U), 'am'),
    (re.compile(r'th[áa]p( |$)', re.I | re.U), 'tháp'),
]


def normalize_name_key(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()


def classify_note_category(name):
    for rx, cat in NOTE_CATEGORY_RULES:
        if rx.search(name or ''):
            return cat
    return 'chùa'


def in_vietnam_bbox(lat, lon):
    if lat is None or lon is None:
        return False
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def make_id(source, external_key):
    """ID 'VN' + 10 chữ số, deterministic từ (source, external_key)."""
    digest = hashlib.md5(f'{source}:{external_key}'.encode('utf-8')).hexdigest()
    n = int(digest[:12], 16) % 10_000_000_000
    return 'VN' + f'{n:010d}'


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def haversine_m(lat1, lon1, lat2, lon2):
    return haversine_km(lat1, lon1, lat2, lon2) * 1000.0


def build_district(province, district):
    parts = ['Việt Nam']
    if province:
        parts.append(str(province).strip())
    if district:
        parts.append(str(district).strip())
    return '-'.join(parts)


def load_payload(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ── Row builders per layer ───────────────────────────────────────────────────

def row_from_t0(rec):
    return {
        'name_vi': rec.get('name_vi') or '',
        'name_en': rec.get('name_en') or '',
        'name_zh': rec.get('name_zh') or '',
        'district': build_district(rec.get('admin'), ''),
        'note_category': classify_note_category(rec.get('name_vi') or rec.get('name_en') or ''),
        'listbibl': rec.get('listbibl') or 'Wikidata (CC0)',
        'geo_lat': rec.get('lat'),
        'geo_long': rec.get('lon'),
        'source': 'wikidata',
        'accuracy': 'dila_exact',
        'raw_source': json.dumps({
            'external_key': rec.get('external_key'),
            'admin': rec.get('admin'),
            'url': f"https://www.wikidata.org/wiki/{rec.get('external_key')}",
        }, ensure_ascii=False),
    }


def row_from_t1(rec):
    province = rec.get('addr_province') or ''
    district = rec.get('addr_district') or rec.get('addr_city') or ''
    return {
        'name_vi': rec.get('name') or '',
        'name_en': rec.get('name_en') or '',
        'name_zh': '',
        'district': build_district(province, district),
        'note_category': classify_note_category(rec.get('name') or ''),
        'listbibl': 'OpenStreetMap (ODbL)',
        'geo_lat': rec.get('lat'),
        'geo_long': rec.get('lon'),
        'source': 'osm',
        'accuracy': rec.get('accuracy') or 'osm_centroid',
        'raw_source': json.dumps({
            'external_key': rec.get('external_key'),
            'religion': rec.get('religion'),
            'historic': rec.get('historic'),
        }, ensure_ascii=False),
    }


def row_from_t2(rec):
    return {
        'name_vi': rec.get('ten_chua') or '',
        'name_en': '',
        'name_zh': '',
        'district': build_district(rec.get('province'), rec.get('district')),
        'note_category': classify_note_category(rec.get('ten_chua') or ''),
        'listbibl': f"disantongiao.vn + geocoder {rec.get('geocode_provider', '?')}",
        'geo_lat': rec.get('geo_lat'),
        'geo_long': rec.get('geo_long'),
        'source': 'disantongiao',
        'accuracy': 'geocode_street',
        'raw_source': json.dumps({
            'external_key': rec.get('external_key'),
            'dia_chi': rec.get('dia_chi'),
            'query': rec.get('query'),
            'matched_name': rec.get('matched_name'),
            'geocode_provider': rec.get('geocode_provider'),
        }, ensure_ascii=False),
    }


def species_rows(rec, row):
    """Chuẩn bị hàng + id; trả (id, dict 17 cột) hoặc None nếu thiếu name/tọa độ."""
    name = (row.get('name_vi') or row.get('name_en') or '').strip()
    if not name:
        return None
    return make_id(rec.get('source', '?'), rec.get('external_key') or name), row


def dedupe_against(row, norm, lat, lon, placed, deduped_reasons):
    """Gộp trùng tên (trong 200m) — giữ record đầu (ưu tiên T0,T1,T2 theo thứ tự xử lý)."""
    prev = placed.get(norm)
    if prev is None:
        return False
    pl_lat, pl_lon = prev
    if lat is None or lon is None:
        deduped_reasons.append((norm, 'same_name_no_gps'))
        return True
    if haversine_m(lat, lon, pl_lat, pl_lon) < 200:
        deduped_reasons.append((norm, 'same_name_within_200m'))
        return True
    return False


# ── DB ───────────────────────────────────────────────────────────────────────

def register_sources(con, sources):
    inserted = 0
    for s in sources:
        cur = con.execute(
            "INSERT OR IGNORE INTO dataset_sources "
            "(name, source_type, origin_url, license, usage_level, attribution_text, notes) "
            "VALUES (?,?,?,?,?,?,?)",
            (s['name'], s['source_type'], s['origin_url'], s['license'],
             s['usage_level'], s['attribution_text'], s['notes']))
        inserted += cur.rowcount
    return inserted


def create_tables(con):
    con.executescript(PLACES_VN_DDL + PLACES_VN_DDL.replace('places_vn', 'places_vn_pending'))
    con.commit()


def apply(db_path, t0_path=T0, t1_path=T1, t2g_path=T2G, dry_run=False):
    """Merge 3 nguồn → places_vn / places_vn_pending. Trả báo cáo."""
    t0 = load_payload(t0_path).get('records', [])
    t1 = load_payload(t1_path).get('records', [])
    t2 = load_payload(t2g_path)

    report = {
        't0': len(t0), 't1': len(t1),
        't2_geocoded': len(t2.get('records', [])),
        't2_pending': len(t2.get('pending', [])),
        'provider': t2.get('provider', '?'),
        'inserted': 0, 'pending_inserted': 0, 'deduped': 0,
        'out_of_bbox': 0, 'deduped_reasons': [],
        'sources_registered': 0, 'tables_created': False,
    }

    con = sqlite3.connect(db_path) if not dry_run else None
    try:
        if con is not None:
            report['sources_registered'] = register_sources(con, DATASET_SOURCES)
            gc_src = GEOCODER_SOURCES.get(t2.get('provider', ''))
            if gc_src:
                report['sources_registered'] += register_sources(con, [gc_src])
            create_tables(con)
            report['tables_created'] = True

        placed = {}  # norm_name → (lat, lon)
        committed_rows = []       # → places_vn
        committed_pending = []    # → places_vn_pending
        deduped_reasons = report['deduped_reasons']

        def _emit(source_label, rec, row, out_of_bbox_reason=None, no_gps=False):
            nonlocal report
            name = (row.get('name_vi') or row.get('name_en') or '').strip()
            norm = normalize_name_key(name)
            lat, lon = row.get('geo_lat'), row.get('geo_long')
            if not no_gps and dedupe_against(row, norm, lat, lon, placed, deduped_reasons):
                report['deduped'] += 1
                return
            rid, prow = species_rows(rec, row)
            if rid is None:
                return
            if lat is not None and lon is not None and not no_gps:
                placed.setdefault(norm, (lat, lon))
            if no_gps or out_of_bbox_reason or not in_vietnam_bbox(lat, lon):
                prow['raw_source'] = json.dumps(
                    json.loads(prow['raw_source']) | {
                        'pending_reason': no_gps and 'no_gps' or (out_of_bbox_reason or 'out_of_bbox_vn')},
                    ensure_ascii=False)
                report['out_of_bbox'] += 1
                committed_pending.append((rid, prow))
                return
            committed_rows.append((rid, prow))

        for rec in t0:
            _emit('t0', rec, row_from_t0(rec))
        for rec in t1:
            _emit('t1', rec, row_from_t1(rec))
        for rec in t2.get('records', []):
            _emit('t2', rec, row_from_t2(rec))
        for rec in t2.get('pending', []):
            row = row_from_t2(rec)
            row['geo_lat'], row['geo_long'] = None, None
            _emit('t2', rec, row, no_gps=True)

        report['inserted'] = len(committed_rows)
        report['pending_inserted'] = len(committed_pending)

        if con is not None:
            con.executemany(
                "INSERT OR IGNORE INTO places_vn "
                "(id,name_vi,name_zh,district,note_category,listbibl,geo_lat,geo_long,"
                " name_en,name_other,sect,founding_year,heritage_status,status,source,accuracy,raw_source) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [(rid, r['name_vi'], r['name_zh'], r['district'], r['note_category'],
                  r['listbibl'], r['geo_lat'], r['geo_long'], r['name_en'], '',
                  '', '', '', 'unknown', r['source'], r['accuracy'], r['raw_source'])
                 for rid, r in committed_rows])
            con.executemany(
                "INSERT OR IGNORE INTO places_vn_pending "
                "(id,name_vi,name_zh,district,note_category,listbibl,geo_lat,geo_long,"
                " name_en,name_other,sect,founding_year,heritage_status,status,source,accuracy,raw_source) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [(rid, r['name_vi'], r['name_zh'], r['district'], r['note_category'],
                  r['listbibl'], r['geo_lat'], r['geo_long'], r['name_en'], '',
                  '', '', '', 'unknown', r['source'], r['accuracy'], r['raw_source'])
                 for rid, r in committed_pending])
            con.commit()
    finally:
        if con is not None:
            con.close()

    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def revert(db_path, sources=None):
    """DROP 2 bảng + xoá dataset_sources do T242 đăng ký. An toàn vì bảng mới tạo."""
    sources = sources or [s['name'] for s in DATASET_SOURCES] + [s['name'] for s in GEOCODER_SOURCES.values()]
    con = sqlite3.connect(db_path)
    out = {}

    def _has(t):
        cur = con.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?', (t,))
        return cur.fetchone()[0] > 0

    try:
        for t in ('places_vn', 'places_vn_pending'):
            if _has(t):
                con.execute(f'DROP TABLE {t}')
                out[t] = 'dropped'
            else:
                out[t] = 'absent'
        con.execute("DELETE FROM dataset_sources WHERE name IN (%s)" % ','.join('?' * len(sources)), sources)
        out['sources_deleted'] = con.total_changes
        con.commit()
    finally:
        con.close()
    return out


def main():
    ap = argparse.ArgumentParser(description='T242 — Merge T0/T1/T2 → places_vn')
    ap.add_argument('--apply', action='store_true', help='Import DB (mặc định)')
    ap.add_argument('--dry-run', action='store_true', help='Chỉ báo cáo, không ghi DB')
    ap.add_argument('--revert', action='store_true', help='DROP bảng + xoá source T242')
    ap.add_argument('--db', default=DB)
    args = ap.parse_args()

    if args.revert:
        out = revert(args.db)
        print('Revert xong:', out)
        return

    if args.dry_run:
        rep = apply(args.db, dry_run=True)
        print('[DRY-RUN] Không ghi DB:')
    else:
        rep = apply(args.db)
        print('[APPLY] Đã ghi DB:')
    print(json.dumps({k: v for k, v in rep.items() if k != 'deduped_reasons'},
                     ensure_ascii=False, indent=2))
    print('Dedupe mẫu:', rep['deduped_reasons'][:10])


if __name__ == '__main__':
    main()