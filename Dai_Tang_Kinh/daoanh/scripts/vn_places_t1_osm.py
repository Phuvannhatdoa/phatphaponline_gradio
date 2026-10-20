# -*- coding: utf-8 -*-
"""T242 — Tầng 1: OpenStreetMap Overpass GPS chùa VN → data/vn_places_t1_osm.json.

LUÔN lọc theo **area VN** (area["ISO3166-1"="VN"][admin_level=2]) —
KHÔNG dùng bbox thô (8–24N/102–110E) vì trộn Thái/Lào/Campuchia thổi số ~10×.

Chạy 3 query phụ rồi gộp (dedup theo type/id, giữ record đầu):
  Q1: amenity=place_of_worship + religion=buddhist
  Q2: amenity=place_of_worship (không lọc religion — tăng phủ)
  Q3: historic=temple
Centroid cho way/relation qua `out center tags;`.

Endpoint: overpass-api.de, fallback maps.mail.ru/osm/tools/overpass.

Chạy:  python scripts/vn_places_t1_osm.py --download
       python scripts/vn_places_t1_osm.py --download --limit 20
"""

import sys, io, os, json, time, argparse, ssl, urllib.request, urllib.parse

if getattr(sys.stdout, 'encoding', 'utf-8').lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'data', 'vn_places_t1_osm.json')
UA = 'PTDA-BuddhistGIS-T242/1.0 (phatphaponline.org; namthien@gmail.com)'

ENDPOINTS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.osm.jp/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
]

AREA = 'area["ISO3166-1"="VN"][admin_level=2]->.VN;'

QUERIES = {
    'osm_buddhist': """
        [out:json][timeout:90];
        %s
        ( node["amenity"="place_of_worship"]["religion"="buddhist"](area.VN);
          way["amenity"="place_of_worship"]["religion"="buddhist"](area.VN);
          relation["amenity"="place_of_worship"]["religion"="buddhist"](area.VN); );
        out center tags;
    """ % AREA,
    'osm_pow_all': """
        [out:json][timeout:90];
        %s
        ( node["amenity"="place_of_worship"](area.VN);
          way["amenity"="place_of_worship"](area.VN);
          relation["amenity"="place_of_worship"](area.VN); );
        out center tags;
    """ % AREA,
    'osm_historic_temple': """
        [out:json][timeout:90];
        %s
        ( node["historic"="temple"](area.VN);
          way["historic"="temple"](area.VN);
          relation["historic"="temple"](area.VN); );
        out center tags;
    """ % AREA,
}


class OverpassError(Exception):
    pass


# Số đếm baseline từ khảo sát ngày 2026-10-06 (lưu để đối chiếu session log)
SURVEY_COUNTS = {
    'node_buddhist': 966,
    'place_of_worship': 5044,
    'historic_temple': 3749,
}


def overpass_request(query):
    """POST query tới Overpass, thử lần lượt các endpoint + SSL-unverified. Trả dict JSON."""
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    last_err = None
    contexts = [None]
    try:
        contexts.append(ssl._create_unverified_context())
    except Exception:
        pass
    for ep in ENDPOINTS:
        for ctx in contexts:
            try:
                req = urllib.request.Request(ep, data=data, headers={
                    'User-Agent': UA,
                    'Content-Type': 'application/x-www-form-urlencoded',
                })
                with urllib.request.urlopen(req, timeout=150, context=ctx) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                last_err = e
                print(f'  [CẢNH BÁO] Endpoint {ep} (ssl={ctx is not None}) lỗi: {e}; thử kế')
    raise OverpassError(f'Toàn bộ endpoint Overpass đều lỗi: {last_err}')


def parse_overpass_elements(elements):
    """Từ elements (out center tags) → list record T1, lọc bớt tag rác."""
    out = []
    for el in elements:
        etype = el.get('type')
        eid = el.get('id')
        tags = el.get('tags') or {}
        name = tags.get('name') or ''
        name_en = tags.get('name:en') or tags.get('name:vi') or ''
        if not name:
            continue
        if 'lat' in el and 'lon' in el:
            lat, lon = el['lat'], el['lon']
        elif el.get('center') and 'lat' in el['center'] and 'lon' in el['center']:
            lat, lon = el['center']['lat'], el['center']['lon']
        else:
            continue
        out.append({
            'source': 'osm',
            'external_key': f'{etype}/{eid}',
            'name': name,
            'name_en': name_en,
            'lat': lat,
            'lon': lon,
            'religion': tags.get('religion', ''),
            'historic': tags.get('historic', ''),
            'addr_city': tags.get('addr:city', ''),
            'addr_district': tags.get('addr:district', ''),
            'addr_province': tags.get('addr:province', ''),
            'accuracy': 'osm_centroid',
        })
    return out


def main():
    ap = argparse.ArgumentParser(description='T242 Tầng 1 — Overpass chùa VN')
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--output', default=OUT)
    args = ap.parse_args()

    merged, seen = [], set()
    counts = {}
    for key, q in QUERIES.items():
        raw, err = None, None
        for attempt in range(3):
            try:
                raw = overpass_request(q)
                break
            except OverpassError as e:
                err = e
                time.sleep(4 * (attempt + 1))
        if raw is None:
            print(f'[LỖI] {key}: {err} — bỏ qua query này, vẫn dùng dữ liệu đã có')
            counts[key] = {'error': str(err)}
            continue
        elements = raw.get('elements', [])
        records = parse_overpass_elements(elements)
        counts[key] = {'elements': len(elements), 'records': len(records)}
        print(f'{key}: element={len(elements)} → record={len(records)}')
        for rec in records:
            if rec['external_key'] in seen:
                continue
            seen.add(rec['external_key'])
            merged.append(rec)

    if args.limit:
        merged = merged[:args.limit]
    print(f'Gộp sau dedup theo type/id: {len(merged)} record')
    if not merged:
        print('[LỖI] Không có record OSM nào — kiểm tra kết nối Overpass')
        sys.exit(1)

    payload = {
        'source': 'osm',
        'layer': 'T1',
        'count': len(merged),
        'downloaded_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'accuracy': 'osm_centroid',
        'survey_reference': SURVEY_COUNTS,
        'query_counts': counts,
        'records': merged,
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f'Đã ghi {len(merged)} record → {args.output}')


if __name__ == '__main__':
    main()