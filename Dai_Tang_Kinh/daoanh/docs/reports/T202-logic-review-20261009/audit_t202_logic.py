import json, sqlite3, sys, dataclasses
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import canonical_lock as cl
import vnpa_lookup as vl
con = sqlite3.connect((ROOT / 'data/lineage.db').as_uri() + '?mode=ro', uri=True)
con.row_factory = sqlite3.Row
con.execute('BEGIN')
def rows(sql, args=()): return [dict(r) for r in con.execute(sql, args)]
def selected(table, ids, wanted):
    columns = {r['name'] for r in con.execute('PRAGMA table_info(' + table + ')')}
    cols = [c for c in wanted if c in columns]
    key = 'entity_ref' if table == 'canonical_decision' else 'id'
    return rows('SELECT ' + ','.join(cols) + ' FROM ' + table + ' WHERE ' + key + ' IN (' + ','.join('?' for _ in ids) + ')', ids)
ids = ['A004981','A008471','A047679','A021395','A010511','A009319','A020647','A001984']
out = {'mode': 'read-only transaction', 'vnpa_count': rows('SELECT COUNT(*) AS n FROM vn_person_authority'),
'duplicates': rows("SELECT dila_id,COUNT(*) AS n FROM vn_person_authority WHERE dila_id IS NOT NULL AND dila_id != '' GROUP BY dila_id HAVING COUNT(*) > 1 ORDER BY dila_id"),
'unmapped': rows("SELECT CASE WHEN dila_id IS NULL THEN 'NULL' ELSE 'empty' END AS kind,status,COUNT(*) AS n FROM vn_person_authority WHERE dila_id IS NULL OR dila_id='' GROUP BY kind,status"),
'canonical': selected('canonical_decision',['PL000000000314','PL000000000001','A001984'],['entity_ref','canonical_name_vi','authority_rank','confidence','verification_status']),
'places': selected('places_dila',['PL000000000314','PL000000000001'],['id','name','name_zh','pinyin','location']),
'people': selected('people',ids,['id','name_zh','name_vi','dynasty','birth_year','death_year']),
'vnpa_cases': rows('SELECT id,name_vi,name_zh,dila_id,status,ttl_filename FROM vn_person_authority WHERE dila_id IN (' + ','.join('?' for _ in ids) + ') ORDER BY dila_id,id',ids),
'validator': {s: cl.is_valid_vi(s) for s in ['An','\u6cd5\u96c5','Th\u1eadp S?t H\u1ea3i','Th? S?t H?i','Th\u00c3\u00a1p','Quy S\u01a1n Linh H\u1ef1u']}}
out['lock'] = {}
for r in out['people']:
    if r['id'] == 'A001984': out['lock'][r['name_zh']] = [dataclasses.asdict(e) for e in cl.build_canonical_lock(con,r['name_zh'])]
for r in out['places']:
    out['lock'][r['name_zh']] = [dataclasses.asdict(e) for e in cl.build_canonical_lock(con,r['name_zh'] or '')]
out['unmapped_search'] = rows("SELECT id,name_vi,dila_id,status,ttl_filename FROM vn_person_authority WHERE name_vi LIKE ? AND (dila_id IS NULL OR dila_id='') LIMIT 5",('%Minh H%Ph%o%',))
con.rollback()
con.close()
print(json.dumps(out,ensure_ascii=False,indent=2))
