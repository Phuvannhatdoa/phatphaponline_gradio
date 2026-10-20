# -*- coding: utf-8 -*-
"""T242 — Tầng 0: Wikidata GPS chùa Việt Nam (SPARQL → data/vn_places_t0_wikidata.json).

Nguồn: Wikidata P625 (tọa độ), truy vấn entity P17=Q881 (Việt Nam),
P31/P279* thuộc nhóm temple/place_of_worship/shrine, có tọa độ.

Sau khi lấy, lọc theo label tiếng Việt chứa "chùa/thiền viện/tổ đình/tự viện"
để giữ đúng mục tiêu "GPS chùa VN" (không bắt nhà thờ / đền / thành cổ).

Chạy:  python scripts/vn_places_t0_wikidata.py --download
       python scripts/vn_places_t0_wikidata.py --download --limit 20   (thử nhỏ)

Output: data/vn_places_t0_wikidata.json (không commit — data/ bị gitignore).
Đặc tả: tasks/T242-vn-temple-gps-t0t1-implementation.md.
"""

import sys, io, os, json, time, argparse, re, unicodedata, urllib.request, urllib.parse

if getattr(sys.stdout, 'encoding', 'utf-8').lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'data', 'vn_places_t0_wikidata.json')
SPARQL_URL = 'https://query.wikidata.org/sparql'
UA = 'PTDA-BuddhistGIS-T242/1.0 (phatphaponline.org; namthien@gmail.com)'

# Temple-family classes: place_of_worship / temple / shrine
SPARQL_Q = """
SELECT ?item ?coord ?adminLabel ?label_vi ?label_en ?label_zh WHERE {
  VALUES ?class { wd:Q1370598 wd:Q44539 wd:Q16970 }
  ?item wdt:P31/wdt:P279* ?class .
  ?item wdt:P17 wd:Q881 .
  ?item wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P131 ?admin . }
  OPTIONAL { ?item rdfs:label ?label_vi . FILTER(LANG(?label_vi) = "vi") }
  OPTIONAL { ?item rdfs:label ?label_en . FILTER(LANG(?label_en) = "en") }
  OPTIONAL { ?item rdfs:label ?label_zh . FILTER(LANG(?label_zh) = "zh") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "vi,en,zh". }
}
"""

# Từ khoá nhận diện chùa / tổ đình / thiền viện / tự viện trong label
CHUA_RE = re.compile(r'(ch[ùu]a|thi[e]?n[  ]?vi[e]?n|t[ôo][  ]?d[ìi]nh|t[ựu][  ]?vi[e]?n)',
                     re.IGNORECASE | re.UNICODE)

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


def classify_note_category(name):
    for rx, cat in NOTE_CATEGORY_RULES:
        if rx.search(name or ''):
            return cat
    return 'chùa'


def normalize_name_key(s):
    """Chuẩn hoá tên để khớp tên (trùng key = nghi trùng chùa)."""
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    s = re.sub(r'\b(chua|tu|thien vien|to dinh|tu vien)\b', '', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).lower().strip()


def sparql_download():
    """Chạy SPARQL, trả list binding raw (hoặc None nếu lỗi)."""
    params = urllib.parse.urlencode({'query': SPARQL_Q, 'format': 'json'})
    url = f'{SPARQL_URL}?{params}'
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/sparql-results+json',
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'[LỖI] Không tải được từ Wikidata SPARQL: {e}')
        return None
    return raw.get('results', {}).get('bindings', [])


def parse_coord_wkt(wkt):
    """'Point(105.96 21.10)' → (lat, lon). Trả None nếu không parse được."""
    try:
        m = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', wkt or '', re.I)
        lon, lat = float(m.group(1)), float(m.group(2))
        return lat, lon
    except Exception:
        return None


def parse_sparql_bindings(bindings):
    """Từ binding raw → list record T0 (dedup theo QID, lọc chùa label vi/en/zh)."""
    items = {}  # qid → record
    for b in bindings:
        qid_full = (b.get('item') or {}).get('value', '')
        qid = qid_full.rsplit('/', 1)[-1] if '/' in qid_full else qid_full
        if not qid:
            continue
        rec = items.setdefault(qid, {
            'source': 'wikidata',
            'external_key': qid,
            'name_vi': '', 'name_en': '', 'name_zh': '',
            'admin': '', 'lat': None, 'lon': None,
            'accuracy': 'dila_exact',
        })
        label_vi = (b.get('label_vi') or {}).get('value', '')
        label_en = (b.get('label_en') or {}).get('value', '')
        label_zh = (b.get('label_zh') or {}).get('value', '')
        if label_vi and not rec['name_vi']:
            rec['name_vi'] = label_vi
        if label_en and not rec['name_en']:
            rec['name_en'] = label_en
        if label_zh and not rec['name_zh']:
            rec['name_zh'] = label_zh
        admin = (b.get('adminLabel') or {}).get('value', '')
        if admin and not rec['admin']:
            rec['admin'] = admin
        coord = parse_coord_wkt((b.get('coord') or {}).get('value', ''))
        if coord:
            rec['lat'], rec['lon'] = coord

    # Lọc: phải có tọa độ + label (vi|en|zh) khớp từ khoá chùa
    out = []
    for qid, rec in items.items():
        labels = ' '.join(v for v in (rec['name_vi'], rec['name_en'], rec['name_zh']) if v)
        if rec['lat'] is None:
            continue
        if not CHUA_RE.search(labels):
            continue
        rec['note_category'] = classify_note_category(rec['name_vi'] or rec['name_en'] or '')
        rec['listbibl'] = f'Wikidata (CC0) QID={qid}'
        rec['name_key'] = normalize_name_key(rec['name_vi'] or rec['name_en'] or '')
        out.append(rec)
    out.sort(key=lambda r: r['external_key'])
    return out


def main():
    ap = argparse.ArgumentParser(description='T242 Tầng 0 — Wikidata chùa VN')
    ap.add_argument('--download', action='store_true', help='Tải SPARQL → JSON')
    ap.add_argument('--limit', type=int, default=0, help='Giới hạn record (0 = hết)')
    ap.add_argument('--output', default=OUT)
    args = ap.parse_args()

    bindings = sparql_download()
    if bindings is None:
        sys.exit(1)
    print(f'Tải SPARQL xong: {len(bindings)} binding thô (nhiều row/QID do label nhiều ngôn ngữ)')

    records = parse_sparql_bindings(bindings)
    if args.limit:
        records = records[:args.limit]
    print(f'Chùa VN sau lọc label + có tọa độ: {len(records)} record')

    payload = {
        'source': 'wikidata',
        'layer': 'T0',
        'count': len(records),
        'downloaded_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'accuracy': 'dila_exact',
        'records': records,
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f'Đã ghi {len(records)} record → {args.output}')


if __name__ == '__main__':
    main()