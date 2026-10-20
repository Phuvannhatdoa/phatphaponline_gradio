# Read-only verification, full source-table fingerprints vs consistent pre-T232 snapshot.
import sys,json,sqlite3,hashlib
from pathlib import Path
from flask import Flask,Blueprint
base=Path(__file__).resolve().parents[3];sys.path.insert(0,str(base))
from src_python import generation_engine_v2 as g,codex_namevi as m
from api_codex_namevi import register_codex_name_routes
r=Path(__file__).parent
def conn(file):
 c=sqlite3.connect('file:'+str(file).replace('\\','/')+'?mode=ro',uri=True,timeout=30);c.row_factory=sqlite3.Row;return c
current=conn(base/'data/lineage.db');old=conn(base/'data/backups/T232-generation-engine-20261004/db-install/lineage-before.db')
def fingerprint(c,t):
 h=hashlib.sha256();n=0
 for row in c.execute('SELECT * FROM '+t+' ORDER BY rowid'):
  h.update(json.dumps(list(row),ensure_ascii=False,separators=(',',':'),default=str).encode('utf8'));h.update(b'\n');n+=1
 return {'rows':n,'sha256':h.hexdigest()}
source={}
for t in ['people','vn_person_authority','vn_person_relations','lineage_edge_assertions','person_gen_computed']:
 before=fingerprint(old,t);after=fingerprint(current,t);source[t]={'before':before,'after':after,'unchanged':before==after}
old.close()
name_old=conn(base/'data/backups/T233-codex-namevi-20261004/lineage-before.db')
if g.table(name_old,'ai_person_name') and g.table(current,'ai_person_name'):
 before=fingerprint(name_old,'ai_person_name');after=fingerprint(current,'ai_person_name');source['ai_person_name']={'before':before,'after':after,'unchanged':before==after,'baseline':'pre-T233'}
name_old.close()
app=Flask(__name__);bp=Blueprint('read_only_codex',__name__,url_prefix='/daoanh/api/admin/ttl_v2');register_codex_name_routes(bp,base,lambda:conn(base/'data/lineage.db'),lambda token:token=='review-only-fixture');app.register_blueprint(bp);client=app.test_client();headers={'X-Session-Token':'review-only-fixture'}
status=client.get('/daoanh/api/admin/ttl_v2/codex_name/status',headers=headers);assert status.status_code==200
listing=client.get('/daoanh/api/admin/ttl_v2/codex_name/list?page=2',headers=headers);assert listing.status_code==200 and listing.json['total']==48673 and len(listing.json['items'])==50
lookup=client.post('/daoanh/api/admin/ttl_v2/codex_name/lookup',json={'ids':['A004980','A000662']},headers=headers);assert lookup.status_code==200 and lookup.json['items']==[]
submit=client.post('/daoanh/api/admin/ttl_v2/codex_name/job',json={'action':'submit','run_id':'616ff1e05ab442819bc166fe6cfafb0d'},headers=headers);assert submit.status_code==409
manifest=json.loads((base/'data/codex_names/23300000000000000000000000000001/manifest.json').read_text(encoding='utf8'));assert m.file_sha(base/'data/codex_names/23300000000000000000000000000001/requests.jsonl')==manifest['file_sha256']
result={'source_tables':source,'all_source_tables_unchanged':all(x['unchanged'] for x in source.values()),'codex':status.json,'manifest':manifest,'admin_contract':'auth fixture + actual read-only DB; no remote call','missing_key_submit_status':submit.status_code,'list_page2_ids':[listing.json['items'][0]['dila_id'],listing.json['items'][-1]['dila_id']],'generation_schemes':len(g.schemes(current))}
(r/'db-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
with (r/'live-generation-results.jsonl').open('w',encoding='utf8') as f:
 for aid in ['A001719','A003627','A004980','A044921','A009489','A003703','A000174','A001984','A000662']:
  report=g.calculate_all(current,aid);f.write(g.canonical(report)+'\n');print(aid,[(x['scheme_id'],x['number'],x['status'],x['candidates']) for x in report['results']])
current.close();print('Source tables unchanged:',result['all_source_tables_unchanged'],'Codex stored',status.json['done'],'ready people',manifest['requested_people'])
