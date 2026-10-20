# -*- coding: utf-8 -*-
"""Hoàn tác đúng run Codex session, chặn nếu gợi ý đã được session khác sửa."""
import argparse,json,re,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def rollback(c,run,apply=False):
 if not re.fullmatch('[a-f0-9]{32}',run):raise ValueError('Run ID không hợp lệ.')
 c.row_factory=sqlite3.Row
 job=c.execute('SELECT * FROM codex_name_job WHERE id=?',(run,)).fetchone()
 if not job or json.loads(job['metadata_json']).get('transport')!='codex_chatgpt_session':raise ValueError('Chỉ hoàn tác run Codex ChatGPT session.')
 if job['status']=='running_session':raise ValueError('Dừng runner và chờ nhóm hiện tại xong trước.')
 if job['status']=='rolled_back_session':return {'run_id':run,'already_reverted':True,'changes':0}
 if apply:c.execute('BEGIN IMMEDIATE')
 try:
  revisions=c.execute('SELECT * FROM codex_name_revision WHERE run_id=? ORDER BY created_at DESC,id DESC',(run,)).fetchall();plans=[];simulated={}
  for row in revisions:
   aid=row['dila_id'];after=json.loads(row['after_json']);before=json.loads(row['before_json']) if row['before_json'] else None
   if aid not in simulated:
    current=c.execute('SELECT * FROM codex_person_name WHERE dila_id=?',(aid,)).fetchone();simulated[aid]=dict(current) if current else None
   if simulated[aid]!=after:raise ValueError('Gợi ý đã đổi sau run; không ghi đè: '+aid)
   simulated[aid]=before;plans.append((aid,before))
  if apply:
   for aid,before in plans:
    if before:c.execute('INSERT OR REPLACE INTO codex_person_name VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',tuple(before[k] for k in ['dila_id','name_zh','name_vi','status','model','prompt_version','input_sha256','response_sha256','run_id','notes','output_json','created_at']))
    else:c.execute('DELETE FROM codex_person_name WHERE dila_id=?',(aid,))
   c.execute('UPDATE codex_name_job SET status=? WHERE id=?',('rolled_back_session',run));c.execute('UPDATE codex_name_request SET status=? WHERE run_id=?',('rolled_back_session',run));c.commit()
  return {'run_id':run,'changes':len(plans),'applied':apply,'legacy_mutations':0,'revision_audit_retained':True}
 except Exception:
  if apply:c.rollback()
  raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
 try:
  uri=(ROOT/'data/lineage.db').resolve().as_uri()+'?mode='+('rw' if a.apply else 'ro');c=sqlite3.connect(uri,uri=True,timeout=30)
  try:print(json.dumps(rollback(c,a.run,a.apply),ensure_ascii=False))
  finally:c.close()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
