# -*- coding: utf-8 -*-
"""T233: dùng Codex đăng nhập ChatGPT; không đọc khóa API, không HTTP API, resumable."""
import argparse,json,os,shutil,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src_python import codex_namevi as m
TRANSPORT='codex_chatgpt_session'
SESSION_MODEL='gpt-6.1-sol'

def clean_env():
 return {k:v for k,v in os.environ.items() if k.upper() not in ('OPENAI_API_KEY','CODEX_API_KEY','ANTHROPIC_API_KEY','OPENAI_BASE_URL')}

def cli_status():
 exe=shutil.which('codex')
 if not exe:return {'available':False,'authenticated':False,'error':'codex_cli_missing'}
 try:
  auth=subprocess.run([exe,'login','status'],capture_output=True,text=True,encoding='utf8',env=clean_env(),timeout=15)
  message=(auth.stdout+auth.stderr).strip()
  version=subprocess.run([exe,'--version'],capture_output=True,text=True,encoding='utf8',env=clean_env(),timeout=15).stdout.strip()
  return {'available':True,'authenticated':auth.returncode==0 and 'Logged in using ChatGPT' in message,'auth_mode':'chatgpt' if 'Logged in using ChatGPT' in message else 'unsupported','cli_version':version,'exe':exe}
 except (OSError,subprocess.TimeoutExpired):return {'available':True,'authenticated':False,'error':'codex_auth_check_failed'}

def prepare(c,folder,group_size=256):
 return m.prepare(c,folder,group_size,model=SESSION_MODEL,transport=TRANSPORT)

def run(c,folder,max_groups=1,timeout=300):
 folder=Path(folder).resolve();manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'));run_id=manifest['run_id']
 job=c.execute('SELECT * FROM codex_name_job WHERE id=?',(run_id,)).fetchone()
 if not job or json.loads(job['metadata_json']).get('transport')!=TRANSPORT:raise ValueError('not_session_job')
 if job['status']=='rolled_back_session':raise ValueError('Job đã hoàn tác; chuẩn bị job mới.')
 if m.file_sha(folder/'requests.jsonl')!=manifest['file_sha256']:raise ValueError('input_file_changed')
 cli=cli_status()
 if not cli.get('authenticated'):raise ValueError('Cần Codex CLI đăng nhập ChatGPT; không chấp nhận API key.')
 # OS lock releases on process exit; keeps CLI and Admin from running the same job together.
 lock=(folder/'session.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
 try:
  if os.name=='nt':
   import msvcrt
   msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  else:
   import fcntl
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except OSError:lock.close();raise ValueError('session_job_already_running')
 processed=imported=0;error=None
 try:
  if (folder/'stop-requested').exists():(folder/'stop-requested').unlink()
  c.execute('UPDATE codex_name_job SET status=?,error_code=NULL WHERE id=?',('running_session',run_id));c.commit()
  pending=c.execute("SELECT custom_id FROM codex_name_request WHERE run_id=? AND status!='ingested' ORDER BY CAST(substr(custom_id,instr(custom_id,'-')+1) AS INTEGER)",(run_id,)).fetchall()
  for row in pending:
   if (folder/'stop-requested').exists():break
   if max_groups and processed>=max_groups:break
   custom=row[0];record=c.execute('SELECT * FROM codex_name_request WHERE run_id=? AND custom_id=?',(run_id,custom)).fetchone()
   records=json.loads(record['input_json'])
   if m.sha(records)!=record['input_sha256']:raise ValueError('input_manifest_tampered')
   work=folder/('group-'+custom.rsplit('-',1)[1]);work.mkdir(exist_ok=True)
   payload_file=work/'result.json';provenance_file=work/'provenance.json'
   if not payload_file.exists() or not provenance_file.exists():
    # Fresh workspace outside repo prevents loading unrelated project context.
    isolated=Path(tempfile.mkdtemp(prefix='daoanh_codex_session_'))
    schema=isolated/'schema.json';schema.write_text(json.dumps(m.SCHEMA),encoding='utf8')
    output=isolated/'result.json'
    prompt=m.PROMPT+'\nKhông dùng tools, không đọc file; chỉ trả JSON cho dữ liệu sau:\n'+m.dump({'records':records})
    args=[cli['exe'],'exec','--ignore-user-config','-c','forced_login_method="chatgpt"','-c','model_reasoning_effort="low"','-m',job['model'],'-s','read-only','--skip-git-repo-check','--ephemeral','--json','-C',str(isolated),'--output-schema',str(schema),'-o',str(output),'-']
    try:p=subprocess.run(args,input=prompt,encoding='utf8',capture_output=True,env=clean_env(),timeout=timeout)
    except subprocess.TimeoutExpired as e:
     for name,data in [('events.jsonl',e.stdout),('stderr.log',e.stderr)]:
      if data:(work/name).write_bytes(data if isinstance(data,bytes) else data.encode('utf8'))
     raise ValueError('codex_session_timeout_resume_later')
    (work/'events.jsonl').write_text(p.stdout,encoding='utf8');(work/'stderr.log').write_text(p.stderr,encoding='utf8')
    if p.returncode!=0 or not output.exists():raise ValueError('codex_session_failed_check_group_logs_no_api_fallback')
    payload=json.loads(output.read_text(encoding='utf8'));m.validate_output(records,payload)
    payload_file.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
    events=[json.loads(line) for line in p.stdout.splitlines() if line.startswith('{')]
    if not any(event.get('type')=='turn.completed' for event in events):raise ValueError('codex_turn_not_completed')
    provenance={'transport':TRANSPORT,'auth_mode':'chatgpt','cli_version':cli['cli_version'],'model_requested':job['model'],'artifact_sha256':m.sha(payload),'thread_id':next((e.get('thread_id') for e in events if e.get('type')=='thread.started'),None),'created_at':m.now()}
    provenance_file.write_text(json.dumps(provenance,indent=2),encoding='utf8')
   else:
    payload=json.loads(payload_file.read_text(encoding='utf8'));provenance=json.loads(provenance_file.read_text(encoding='utf8'))
   result=m.ingest_session(c,run_id,custom,payload,provenance);processed+=1;imported+=result['inserted']
   print(json.dumps({'run_id':run_id,'group':custom,'new_names':result['inserted'],'done':m.stats(c)['done'],'transport':TRANSPORT}),flush=True)
  remaining=c.execute("SELECT count(*) FROM codex_name_request WHERE run_id=? AND status!='ingested'",(run_id,)).fetchone()[0]
  status='done' if not remaining else 'paused_session'
 except Exception as e:
  error=str(e)[:180];status='blocked_session';raise
 finally:
  c.execute('UPDATE codex_name_job SET status=?,error_code=? WHERE id=?',(status,error,run_id));c.commit();lock.close()
  summary={'run_id':run_id,'status':status,'processed_groups':processed,'new_names':imported,'error':error,'transport':TRANSPORT,'paid_api_calls':0}
  (folder/'session-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 return summary

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['status','prepare','run']);p.add_argument('--folder');p.add_argument('--group-size',type=int,default=256);p.add_argument('--max-groups',type=int,default=1);p.add_argument('--timeout',type=int,default=300);a=p.parse_args()
 if a.max_groups<0 or a.timeout<30:raise ValueError('Giới hạn không hợp lệ.')
 if a.action=='status':
  status=cli_status();status.pop('exe',None);print(json.dumps(status));return
 c=sqlite3.connect(ROOT/'data/lineage.db',timeout=30);c.row_factory=sqlite3.Row
 try:
  if a.action=='prepare':result=prepare(c,a.folder,a.group_size)
  else:result=run(c,a.folder,a.max_groups,a.timeout)
  print(json.dumps(result,ensure_ascii=False),flush=True)
 finally:c.close()
if __name__=='__main__':
 try:main()
 except Exception as e:print('Codex session:',str(e)[:180],file=sys.stderr);sys.exit(1)
