import json,sqlite3,sys,tempfile,subprocess,os
from pathlib import Path
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root))
from src_python.codex_namevi import SCHEMA,PROMPT,dump
c=sqlite3.connect(root/'data/lineage.db');c.row_factory=sqlite3.Row
r=c.execute('SELECT input_json FROM codex_name_request WHERE run_id=? ORDER BY custom_id LIMIT 1',('616ff1e05ab442819bc166fe6cfafb0d',)).fetchone();c.close()
work=Path(tempfile.mkdtemp(prefix='daoanh_codex_names_'))
(work/'schema.json').write_text(json.dumps(SCHEMA),encoding='utf8')
env={k:v for k,v in os.environ.items() if k.upper() not in ('OPENAI_API_KEY','CODEX_API_KEY','ANTHROPIC_API_KEY','OPENAI_BASE_URL')}
args=['codex','exec','--ignore-user-config','-c','forced_login_method="chatgpt"','-m','gpt-6.1-sol','-s','read-only','--skip-git-repo-check','--ephemeral','--json','-C',str(work),'--output-schema',str(work/'schema.json'),'-o',str(work/'result.json'),'-']
prompt=PROMPT+'\nDo not use tools or read files. Only return the JSON for these records:\n'+dump({'records':json.loads(r[0])})
p=subprocess.run(args,input=prompt,encoding='utf8',env=env,capture_output=True,timeout=300)
out=Path(__file__).parent
(out/'probe-events.jsonl').write_text(p.stdout,encoding='utf8');(out/'probe-stderr.log').write_text(p.stderr,encoding='utf8')
if (work/'result.json').exists():(out/'probe-result.json').write_bytes((work/'result.json').read_bytes())
(out/'probe-status.json').write_text(json.dumps({'exit_code':p.returncode,'work':str(work),'transport':'codex_chatgpt_session','model_requested':'gpt-6.1-sol','records':len(json.loads(r[0]))}),encoding='utf8')
print(json.dumps({'exit_code':p.returncode,'output':(work/'result.json').exists()}))
