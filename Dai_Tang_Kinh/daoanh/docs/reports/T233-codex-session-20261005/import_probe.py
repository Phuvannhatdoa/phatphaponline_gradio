import json,sqlite3,sys,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from src_python import codex_namevi as m
folder=Path(__file__).parent
payload=json.loads((folder/'probe-result.json').read_text(encoding='utf8'))
events=[json.loads(line) for line in (folder/'probe-events.jsonl').read_text(encoding='utf8').splitlines() if line.startswith('{')]
assert any(e.get('type')=='turn.completed' for e in events)
assert json.loads((folder/'probe-status.json').read_text())['exit_code']==0
c=sqlite3.connect(root/'data/lineage.db',timeout=30);c.row_factory=sqlite3.Row
request=c.execute('SELECT input_json FROM codex_name_request WHERE run_id=? ORDER BY custom_id LIMIT 1',('616ff1e05ab442819bc166fe6cfafb0d',)).fetchone();records=json.loads(request[0])
m.validate_output(records,payload)
run=uuid.uuid4().hex;custom=run+'-0';model='gpt-6.1-sol'
meta={'transport':'codex_chatgpt_session','requested_people':32,'requests':1,'sample':True,'artifact_folder':'docs/reports/T233-codex-session-20261005','prompt_sha256':m.sha(m.PROMPT)}
c.execute('INSERT INTO codex_name_job VALUES(?,?,?,?,?,?,?,?,?)',(run,m.now(),'prepared',model,m.PROMPT_VERSION,m.dump(meta),None,None,None))
c.execute('INSERT INTO codex_name_request VALUES(?,?,?,?,?,?)',(run,custom,m.dump(records),m.sha(records),'prepared',None));c.commit()
prov={'transport':'codex_chatgpt_session','auth_mode':'chatgpt','cli_version':'codex-cli 0.159.2','model_requested':model,'artifact_sha256':m.sha(payload),'thread_id':next(e['thread_id'] for e in events if e.get('type')=='thread.started')}
result=m.ingest_session(c,run,custom,payload,prov);c.execute('UPDATE codex_name_job SET status=? WHERE id=?',('done',run));c.commit()
result.update(run_id=run,stats=m.stats(c),provenance=prov)
(folder/'probe-import.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));c.close()
