import json,sqlite3,sys,datetime
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from src_python import codex_namevi as m
c=sqlite3.connect((root/'data/lineage.db').resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('BEGIN')
stat=m.stats(c);stale=unknown=bad_provenance=0
for r in c.execute('SELECT n.*,p.id AS pid,p.name_zh AS current_zh,p.dynasty FROM codex_person_name n LEFT JOIN people p ON p.id=n.dila_id'):
 if not r['pid']:unknown+=1;continue
 if m.record_hash({'dila_id':r['dila_id'],'name_zh':r['current_zh'],'dynasty':r['dynasty']})!=r['input_sha256']:stale+=1
 prov=json.loads(r['output_json']).get('provenance',{})
 if prov.get('transport')!='codex_chatgpt_session' or prov.get('auth_mode')!='chatgpt':bad_provenance+=1
run='39836c390adf4e9993649eacca7a546c';request_counts=dict(c.execute('SELECT status,count(*) FROM codex_name_request WHERE run_id=? GROUP BY status',(run,)))
result={'at':m.now(),'stats':stat,'full_job_request_states':request_counts,'unknown_ids':unknown,'stale_inputs':stale,'bad_session_provenance':bad_provenance,'paid_api_calls':0,'corpus_done':stat['done']==stat['total'] and not stale and not unknown and not bad_provenance}
assert not unknown and not stale and not bad_provenance
(Path(__file__).parent/'delivery-state.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));c.close()
