import sqlite3,json,runpy,hashlib
from pathlib import Path
D=Path.cwd()/'daoanh';B=D/'data/backups/T215-dai-ninh-sync-20261003';O=D/'docs/reports/T215-dai-ninh-sync-20261003'
func=runpy.run_path(str(B/'sync_case.py'));c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
r=json.loads((B/'sync-report.json').read_text(encoding='utf-8'));assert r['committed'];assert func['snap'](c)==r['after'];c.close()
api=json.loads((O/'api-after.json').read_text(encoding='utf-8'));center=api['center'];assert center['id']=='A020545' and center['name_vi']=='Đại Ninh Đạo Khoan' and center['name_zh']=='大寧道寬'
db=r['after']['vn_person_authority'][0];assert center['display_name']['biographical_note_vi']==db['biographical_note_vi'];assert center['display_name']['dharma_lineage']==db['dharma_lineage'];assert center['display_name']['generation_order']==45
edges=[x for x in api['edges'] if x['from']=='A001439' and x['to']=='A020545'];assert len(edges)==1 and set(x['source_code'] for x in edges[0]['sources'])=={'DILA','MARCUS','TTL'}
assert not any(x['from']==x['to'] for x in api['edges']);assert hashlib.sha256((D/'data/ttl/TS-Dai-Ninh-Dao-Khoan.ttl').read_bytes()).hexdigest()==r['ttl_sha256']
v={'db_readback':'PASS','api_metadata_bio_lineage':'PASS','generation':45,'teacher_id':'A001439','disciple_id':'A020545','api_edge_count':1,'source_badge':edges[0]['source_badge'],'source_edges_unchanged':True,'ttl_unchanged_during_db_sync':True,'rollback_simulation':r['rollback_test']};(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(v,ensure_ascii=False))
