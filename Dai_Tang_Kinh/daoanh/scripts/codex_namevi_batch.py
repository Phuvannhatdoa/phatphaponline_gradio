# -*- coding: utf-8 -*-
"""T233: prepare → submit → collect; resume/idempotent, không ghi tên chính."""
import argparse,json,os,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src_python import codex_namevi as m

def api_key():
 key=os.getenv('OPENAI_API_KEY','').strip()
 if key:return key
 env=ROOT/'.env'
 if env.exists():
  for line in env.read_text(encoding='utf-8-sig').splitlines():
   if line.strip().startswith('OPENAI_API_KEY='):
    return line.split('=',1)[1].strip().strip('"').strip("'")
 return ''

def session():
 raise ValueError("paid_api_disabled_use_codex_chatgpt_session")
 key=api_key()
 if not key:raise ValueError('missing_openai_api_key')
 import requests
 s=requests.Session();s.headers['Authorization']='Bearer '+key;return s

def checked(response):
 if not response.ok:raise ValueError('openai_http_'+str(response.status_code))
 return response.json()

def submit(c,folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'));run=manifest['run_id']
 job=c.execute('SELECT * FROM codex_name_job WHERE id=?',(run,)).fetchone()
 if not job or job['status'] not in ('prepared','uploaded'):raise ValueError('job_not_prepared_or_already_submitted')
 if m.file_sha(folder/'requests.jsonl')!=manifest['file_sha256']:raise ValueError('input_file_changed')
 if manifest['requests']==0:raise ValueError('nothing_to_submit')
 # SDK không bắt buộc: Responses/Files/Batch chuẩn, endpoint cố định.
 s=session();file_id=job['input_file_id']
 if not file_id:
  with (folder/'requests.jsonl').open('rb') as f:
   uploaded=checked(s.post('https://api.openai.com/v1/files',data={'purpose':'batch'},files={'file':('requests.jsonl',f,'application/jsonl')},timeout=180))
  file_id=uploaded['id'];c.execute('UPDATE codex_name_job SET status=?,input_file_id=? WHERE id=?',('uploaded',file_id,run));c.commit()
 response=checked(s.post('https://api.openai.com/v1/batches',json={'input_file_id':file_id,'endpoint':'/v1/responses','completion_window':'24h','metadata':{'project':'daoanh','run_id':run,'prompt_version':m.PROMPT_VERSION}},headers={'Idempotency-Key':'daoanh-codex-'+run},timeout=60))
 c.execute('UPDATE codex_name_job SET status=?,batch_id=? WHERE id=?',(response['status'],response['id'],run));c.commit()
 (folder/'batch.json').write_text(json.dumps(response,indent=2),encoding='utf8');return {'run_id':run,'batch_id':response['id'],'status':response['status']}

def collect(c,folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'));run=manifest['run_id']
 job=c.execute('SELECT * FROM codex_name_job WHERE id=?',(run,)).fetchone()
 if not job or not job['batch_id']:raise ValueError('job_not_submitted')
 s=session();batch=checked(s.get('https://api.openai.com/v1/batches/'+job['batch_id'],timeout=60))
 c.execute('UPDATE codex_name_job SET status=? WHERE id=?',(batch['status'],run));c.commit()
 if batch['status'] not in ('completed','expired','cancelled'):return {'run_id':run,'status':batch['status']}
 imported=errors=0
 if batch.get('output_file_id'):
  file=folder/'output.jsonl'
  if not file.exists():
   response=s.get('https://api.openai.com/v1/files/'+batch['output_file_id']+'/content',stream=True,timeout=180)
   if not response.ok:raise ValueError('output_download_http_'+str(response.status_code))
   partial=folder/'output.partial.jsonl'
   with partial.open('wb') as f:
    for chunk in response.iter_content(1048576):f.write(chunk)
   # Windows rename có thể bị chặn; giữ partial và báo lỗi, không coi là xong.
   partial.rename(file)
  with file.open(encoding='utf8') as f:
   for line in f:
    row=json.loads(line);custom=row.get('custom_id','')
    try:
     if row.get('error') or row.get('response',{}).get('status_code')!=200:raise ValueError('request_failed')
     result=m.ingest(c,run,custom,row['response']['body']);imported+=result['inserted']
    except ValueError as e:
     errors+=1;c.execute('UPDATE codex_name_request SET status=?,error_code=? WHERE run_id=? AND custom_id=?',('needs_review',str(e)[:160],run,custom));c.commit()
 if batch.get('error_file_id'):
  errors+=batch.get('request_counts',{}).get('failed',0)
 summary={'run_id':run,'status':batch['status'],'new_names_imported':imported,'request_errors':errors,
  'ingested_requests':c.execute("SELECT count(*) FROM codex_name_request WHERE run_id=? AND status='ingested'",(run,)).fetchone()[0],
  'total_requests':manifest['requests'],'legacy_mutations':0}
 # Remote completed does not mean every ID was ingested; keep explicit local status.
 local='done' if summary['ingested_requests']==manifest['requests'] else 'needs_review'
 c.execute('UPDATE codex_name_job SET status=? WHERE id=?',(local,run));c.commit();summary['local_status']=local
 (folder/'collect-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');return summary

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','prepare','submit','collect','status']);p.add_argument('--folder');p.add_argument('--backup');a=p.parse_args()
 c=sqlite3.connect(ROOT/'data/lineage.db',timeout=30);c.row_factory=sqlite3.Row
 if a.action=='install':
  if not a.backup:raise ValueError('install_needs_backup_path')
  backup=Path(a.backup)
  if backup.exists():raise ValueError('backup_already_exists')
  backup.parent.mkdir(parents=True,exist_ok=True);snap=sqlite3.connect(backup);c.backup(snap,pages=512);snap.close();m.ensure(c);print('Installed additive Codex tables; legacy names unchanged.')
 elif a.action=='status':print(json.dumps(dict(m.stats(c),model=m.MODEL,api_key_configured=bool(api_key())),ensure_ascii=False))
 elif a.action=='prepare':print(json.dumps(m.prepare(c,a.folder),ensure_ascii=False))
 elif a.action=='submit':print(json.dumps(submit(c,a.folder)))
 elif a.action=='collect':print(json.dumps(collect(c,a.folder)))
 c.close()
if __name__=='__main__':
 try:main()
 except Exception as e:print('Codex namevi:',str(e)[:180],file=sys.stderr);sys.exit(1)
