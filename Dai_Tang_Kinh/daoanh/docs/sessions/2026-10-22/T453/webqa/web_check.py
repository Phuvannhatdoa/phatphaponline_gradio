"""T453 web QA: tra TỪNG bộ trong 26 file DILA qua đúng API ô Search trang chủ (/daoanh/api/search?q=<mã>)."""
import json, glob, os, sys, urllib.request, urllib.parse, concurrent.futures as cf, time
base = sys.argv[1]
recs = {}
for f in glob.glob(os.path.join(base, 'data/dila_import/authority_catalog.2026-10/json/*.json')):
    recs.update(json.load(open(f, encoding='utf-8')))
def check(k):
    url = 'http://127.0.0.1:8080/daoanh/api/search?q=' + urllib.parse.quote(k)
    for _ in range(3):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=30))
            hit = [w for w in d.get('dila_works', []) if w['cbeta_id'] == k]
            if not hit: return k, 'MISSING', ''
            w = hit[0]
            if w['title_zh'] != recs[k]['title']: return k, 'TITLE_ZH_DIFF', w['title_zh']
            if not w.get('title_vi'): return k, 'NO_TITLE_VI', ''
            return k, 'OK', w['title_vi']
        except Exception as e:
            err = str(e); time.sleep(1)
    return k, 'ERROR', err
t = time.time()
with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(check, sorted(recs)))
from collections import Counter
c = Counter(r[1] for r in res)
print('tổng', len(res), dict(c), f'{time.time()-t:.0f}s')
for r in res:
    if r[1] != 'OK': print(r)
json.dump(res, open(os.path.join(os.path.dirname(__file__), 'web_check_result.json'), 'w', encoding='utf-8'), ensure_ascii=False)
