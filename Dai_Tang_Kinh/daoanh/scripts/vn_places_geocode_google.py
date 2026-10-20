# -*- coding: utf-8 -*-
"""T242 — Geocode T2 (CSDL Chùa Việt) → data/vn_places_t2_disantongiao_geocoded.json.

Provider: đọc key từ env `GOOGLE_MAPS_API_KEY` (không hardcode, không commit) →
          dùng Google Geocoding API (region=vn).
          Không có key → fallback **Nominatim** của OSM (free, ODbL,
          User-Agent rõ ràng + 1.1s/request).

Cache: data/geocode_cache.json (md5(query) → kết quả) → không tốn quota khi chạy lại.

Chạy:  python scripts/vn_places_geocode_google.py
       python scripts/vn_places_geocode_google.py --limit 5
"""

import sys, io, os, json, time, hashlib, re, argparse, urllib.request, urllib.parse

if getattr(sys.stdout, 'encoding', 'utf-8').lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'data', 'vn_places_t2_disantongiao_raw.json')
OUT = os.path.join(BASE, 'data', 'vn_places_t2_disantongiao_geocoded.json')
CACHE = os.path.join(BASE, 'data', 'geocode_cache.json')

UA = 'PTDA-BuddhistGIS-T242/1.0 (phatphaponline.org; namthien@gmail.com)'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
GOOGLE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
NOMINATIM_DELAY = 1.1   # chính sách Nominatim: tối đa 1 req/s
GOOGLE_DELAY = 0.05     # task: ≥ 50ms/request

PROVINCE_ALIAS = {
    'hà nội': 'Hà Nội', 'hồ chí minh': 'TP Hồ Chí Minh', 'hcm': 'TP Hồ Chí Minh',
    'tp. hồ chí minh': 'TP Hồ Chí Minh', 'thành phố hồ chí minh': 'TP Hồ Chí Minh',
    'đà nẵng': 'Đà Nẵng', 'cần thơ': 'Cần Thơ',
}


def normalize_province(p):
    if not p:
        return p
    key = p.lower().strip()
    return PROVINCE_ALIAS.get(key, p)


class NominatimProvider:
    def __init__(self):
        self.delay = NOMINATIM_DELAY

    def name(self):
        return 'nominatim'

    def geocode(self, query):
        params = urllib.parse.urlencode({
            'format': 'jsonv2', 'limit': '1', 'countrycodes': 'vn', 'q': query,
        })
        req = urllib.request.Request(f'{NOMINATIM_URL}?{params}',
                                     headers={'User-Agent': UA, 'Accept-Language': 'vi,en'})
        time.sleep(self.delay)
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        if not data:
            return {'ok': False, 'status': 'ZERO_RESULTS'}
        hit = data[0]
        addr = hit.get('address') or {}
        province = addr.get('province') or addr.get('state') or addr.get('region') or ''
        district = addr.get('district') or addr.get('county') or ''
        return {
            'ok': True,
            'geo_lat': float(hit['lat']),
            'geo_long': float(hit['lon']),
            'geocode_confidence': hit.get('addresstype') or 'approximate',
            'province': normalize_province(province),
            'district': district,
            'matched_name': hit.get('display_name', ''),
        }


class GoogleProvider:
    def __init__(self, api_key):
        self.delay = GOOGLE_DELAY
        self.api_key = api_key

    def name(self):
        return 'google'

    def geocode(self, query):
        params = urllib.parse.urlencode({
            'address': query, 'key': self.api_key, 'region': 'vn', 'language': 'vi',
        })
        req = urllib.request.Request(f'{GOOGLE_URL}?{params}', headers={'User-Agent': UA})
        time.sleep(self.delay)
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        status = data.get('status', '')
        if status == 'ZERO_RESULTS':
            return {'ok': False, 'status': 'ZERO_RESULTS'}
        if status == 'OVER_QUERY_LIMIT':
            raise RuntimeError('Google Geocoding: OVER_QUERY_LIMIT — hết quota/giây, đổi key hoặc dùng Nominatim')
        if status == 'REQUEST_DENIED':
            raise RuntimeError(f'Google Geocoding: REQUEST_DENIED — {data.get("error_message", "")}')
        if status != 'OK' or not data.get('results'):
            return {'ok': False, 'status': status}
        hit = data['results'][0]
        comps = {c['types'][0]: c['long_name'] for c in hit.get('address_components', [])}
        province = comps.get('administrative_area_level_1', '')
        district = comps.get('administrative_area_level_2') or comps.get('locality', '')
        return {
            'ok': True,
            'geo_lat': hit['geometry']['location']['lat'],
            'geo_long': hit['geometry']['location']['lng'],
            'geocode_confidence': hit['geometry'].get('location_type', 'APPROXIMATE'),
            'province': normalize_province(province),
            'district': district,
            'matched_name': hit.get('formatted_address', ''),
        }


def build_query(rec):
    """Query chính: tên chùa + địa chỉ đầy đủ."""
    ten = rec.get('ten_chua', '') or ''
    dc = rec.get('dia_chi', '') or ''
    return f'{ten}, {dc}, Việt Nam'.strip(' ,')


def extract_province(dia_chi):
    """Trích tên Tỉnh/TP từ địa chỉ (VD 'tỉnh Tĩnh Gia'? thực tế 'tỉnh Thanh Hóa')."""
    s = dia_chi or ''
    m = re.search(r'(?i)tỉnh\s+([A-ZÀ-Ỹ][A-Za-zÀ-ỹ\s]+?)(?=[,;]|$)', s)
    if not m:
        m = re.search(r'(?i)(?:thành phố|tp\.?)\s*([A-ZÀ-Ỹ][A-Za-zÀ-ỹ\s]+?)(?=[,;]|$)', s)
    if m:
        return m.group(1).strip()
    return ''


def candidate_queries(rec):
    """Chuỗi fallback: 1) tên+địa chỉ, 2) tên+tỉnh, 3) tên+Việt Nam."""
    ten = (rec.get('ten_chua', '') or '').strip()
    if not ten:
        return []
    dc = (rec.get('dia_chi', '') or '').strip()
    province = extract_province(dc)
    qs = []
    if dc:
        qs.append(f'{ten}, {dc}, Việt Nam')
    if province:
        qs.append(f'{ten}, {province}, Việt Nam')
    qs.append(f'{ten}, Việt Nam')
    seen, out = set(), []
    for q in qs:
        qn = re.sub(r'\s+', ' ', q).strip(' ,')
        if qn and qn not in seen:
            seen.add(qn)
            out.append(qn)
    return out


def load_raw(raw_path):
    with open(raw_path, encoding='utf-8') as f:
        payload = json.load(f)
    return payload.get('records', [])


def load_cache(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache_path, cache):
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser(description='T242 — Geocode T2 disantongiao')
    ap.add_argument('--limit', type=int, default=0, help='Giới hạn record (0 = hết)')
    ap.add_argument('--output', default=OUT)
    ap.add_argument('--raw', default=RAW)
    ap.add_argument('--cache', default=CACHE)
    args = ap.parse_args()

    api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '') or ''
    provider = GoogleProvider(api_key) if api_key else NominatimProvider()
    print(f'Provider: {provider.name()}')
    if provider.name() == 'google':
        print('Chú ý: dùng Google Geocoding — cần Billing; cache đã bật để không gọi lại.')

    records = load_raw(args.raw)
    if not records:
        print('[LỖI] Không có record trong raw JSON — chạy vn_places_t2_disantongiao.py trước')
        sys.exit(1)
    if args.limit:
        records = records[:args.limit]

    cache = load_cache(args.cache)
    geocoded, pending, errors = [], [], []
    for i, rec in enumerate(records, 1):
        qs = candidate_queries(rec)
        if not qs:
            continue
        key = hashlib.md5(qs[0].encode('utf-8')).hexdigest()
        rec_out = {
            'source': 'disantongiao',
            'external_key': rec.get('external_key'),
            'ten_chua': rec.get('ten_chua'),
            'dia_chi': rec.get('dia_chi'),
            'query': qs[0],
        }
        if key in cache:
            meta = cache[key]
        else:
            hit = None
            used_query = ''
            for q in qs:
                try:
                    candidate = provider.geocode(q)
                except RuntimeError as e:
                    errors.append({'external_key': rec_out['external_key'], 'error': str(e)})
                    print(f'  [LỖI] {rec_out["ten_chua"]}: {e}')
                    candidate = {'ok': False, 'status': str(e)}
                except Exception as e:
                    errors.append({'external_key': rec_out['external_key'], 'error': str(e)})
                    print(f'  [CẢNH BÁO] {rec_out["ten_chua"]}: {e}')
                    candidate = {'ok': False, 'status': f'NETWORK_ERROR {e}'}
                if candidate.get('ok'):
                    hit = candidate
                    used_query = q
                    break
            if hit is None:
                hit = {'ok': False, 'status': 'ZERO_RESULTS'}
            hit['used_query'] = used_query
            meta = {'provider': provider.name(), 'hit': hit, 'used_query': used_query}
            cache[key] = meta
        hit = meta['hit']

        if hit.get('ok'):
            rec_out.update(hit)
            rec_out.pop('used_query', None)
            rec_out['geocode_provider'] = provider.name()
            rec_out['accuracy'] = 'geocode_street'
            geocoded.append(rec_out)
        else:
            rec_out['geocode_provider'] = provider.name()
            rec_out['pending_reason'] = hit.get('status', 'ZERO_RESULTS')
            pending.append(rec_out)

        if i % 10 == 0:
            save_cache(args.cache, cache)
            print(f'  ...{i}/{len(records)} (ok={len(geocoded)}, pending={len(pending)})')

    save_cache(args.cache, cache)
    payload = {
        'provider': provider.name(),
        'count': len(geocoded),
        'pending_count': len(pending),
        'error_count': len(errors),
        'geocoded_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'records': geocoded,
        'pending': pending,
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f'Geocode xong: ok={len(geocoded)}, pending={len(pending)}, lỗi={len(errors)}')
    print(f'Đã ghi → {args.output}; cache → {args.cache}')
    if pending:
        print('Pending (không geocode được):', [p['ten_chua'] for p in pending][:10])


if __name__ == '__main__':
    main()