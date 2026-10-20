"""
t39_wikidata_p571_download.py — T39 Phase 1: Download Wikidata P571 Buddhist temples
======================================================================================
Query Wikidata SPARQL endpoint cho tất cả Buddhist temples tại China có P571 (inception).

Output: data/t39_wikidata_p571_raw.json
Format: list of {qid, label_zh, label_en, lat, lon, year}

Cách dùng:
    python scripts/t39_wikidata_p571_download.py
    python scripts/t39_wikidata_p571_download.py --dry-run   # chỉ in SPARQL, không query
    python scripts/t39_wikidata_p571_download.py --limit 100 # test với 100 items
"""
import argparse, json, re, sys, io, time
import urllib.request, urllib.parse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ENDPOINT = 'https://query.wikidata.org/sparql'
OUTPUT = Path('data/t39_wikidata_p571_raw.json')

# Buddhist temple classes on Wikidata
# Q44613 = Buddhist temple, Q5393308 = Buddhist monastery
SPARQL_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?itemLabelEn ?lat ?lon ?inception WHERE {{
  {{
    ?item wdt:P31/wdt:P279* wd:Q44613 .
  }}
  UNION
  {{
    ?item wdt:P31 wd:Q44613 .
  }}
  UNION
  {{
    ?item wdt:P31/wdt:P279* wd:Q5393308 .
  }}
  ?item wdt:P571 ?inception .
  ?item wdt:P17 wd:Q148 .
  ?item wdt:P625 ?coord .
  BIND(geof:latitude(?coord) AS ?lat)
  BIND(geof:longitude(?coord) AS ?lon)
  SERVICE wikibase:label {{
    bd:serviceParam wikibase:language "zh,zh-hans,zh-hant,en".
    ?item rdfs:label ?itemLabel .
  }}
  OPTIONAL {{
    SERVICE wikibase:label {{
      bd:serviceParam wikibase:language "en".
      ?item rdfs:label ?itemLabelEn .
    }}
  }}
}}{limit_clause}
"""


def extract_qid(uri: str) -> str:
    m = re.search(r'Q(\d+)$', uri)
    return f'Q{m.group(1)}' if m else uri


def parse_year(inception_str: str) -> int | None:
    """Wikidata inception là ISO 8601: '+1093-01-01T00:00:00Z' hoặc '1093-01-01T00:00:00Z'"""
    m = re.search(r'[+-]?(\d{1,4})-\d{2}-\d{2}', inception_str)
    if not m:
        return None
    year = int(m.group(1))
    # BCE dates có prefix '-'
    if inception_str.startswith('-') or inception_str.startswith('+-'):
        year = -year
    if year < 50 or year > 2000:
        return None
    return year


def run_sparql(sparql: str, timeout: int = 120) -> dict:
    headers = {
        'Accept': 'application/sparql-results+json',
        'User-Agent': 'DaoAnh-T39-Bot/1.0 (Buddhist GIS; contact: namthien@gmail.com)',
    }
    data = urllib.parse.urlencode({'query': sparql, 'format': 'json'}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='In SPARQL ra, không query')
    parser.add_argument('--limit', type=int, default=0, help='Giới hạn số kết quả (0 = không giới hạn)')
    args = parser.parse_args()

    limit_clause = f'\nLIMIT {args.limit}' if args.limit else ''
    sparql = SPARQL_QUERY.format(limit_clause=limit_clause)

    if args.dry_run:
        print('=== SPARQL Query ===')
        print(sparql)
        return

    print(f'[T39] Querying Wikidata SPARQL: {ENDPOINT}')
    print(f'[T39] Limit: {args.limit if args.limit else "none"}')
    print('[T39] Sending request (có thể mất 30-60s)...')

    start = time.time()
    try:
        result = run_sparql(sparql, timeout=180)
    except Exception as e:
        print(f'[ERROR] SPARQL query failed: {e}')
        sys.exit(1)

    elapsed = time.time() - start
    bindings = result.get('results', {}).get('bindings', [])
    print(f'[T39] Done in {elapsed:.1f}s — {len(bindings)} raw rows')

    # Parse + deduplicate by QID (take first inception per QID)
    seen_qid: dict[str, dict] = {}
    skipped_year = 0
    skipped_coords = 0

    for b in bindings:
        qid = extract_qid(b['item']['value'])
        if qid in seen_qid:
            continue

        try:
            lat = float(b['lat']['value'])
            lon = float(b['lon']['value'])
        except (KeyError, ValueError):
            skipped_coords += 1
            continue

        year = parse_year(b['inception']['value'])
        if year is None:
            skipped_year += 1
            continue

        seen_qid[qid] = {
            'qid': qid,
            'label_zh': b.get('itemLabel', {}).get('value', ''),
            'label_en': b.get('itemLabelEn', {}).get('value', ''),
            'lat': lat,
            'lon': lon,
            'year': year,
            'inception_raw': b['inception']['value'],
        }

    items = list(seen_qid.values())
    print(f'[T39] Unique items với valid year+coords: {len(items)}')
    print(f'[T39] Skipped (no valid year): {skipped_year}')
    print(f'[T39] Skipped (no coords): {skipped_coords}')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        'meta': {
            'query_date': '2026-08-25',
            'endpoint': ENDPOINT,
            'total_raw': len(bindings),
            'total_valid': len(items),
            'skipped_year': skipped_year,
            'skipped_coords': skipped_coords,
        },
        'items': items,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[T39] Saved to {OUTPUT}')

    # Quick stats
    years = [i['year'] for i in items]
    if years:
        print(f'[T39] Year range: {min(years)} – {max(years)}')
        by_century = {}
        for y in years:
            c = (y // 100) * 100
            by_century[c] = by_century.get(c, 0) + 1
        for c in sorted(by_century):
            print(f'       {c:4d}s: {by_century[c]:4d}')


if __name__ == '__main__':
    main()
