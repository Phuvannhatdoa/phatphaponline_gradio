# -*- coding: utf-8 -*-
"""T227: snapshot readonly, xuất từng hồ sơ/ZIP; không giữ corpus trong RAM."""
import json,sqlite3,zipfile
from pathlib import Path
from src_python.ttl_db_export import iter_identifiers,export
from src_python import ttl_db_sources as records
from src_python.ttl_profile_v2 import digest,now

def run(db_path,output,scope='ttl',limit=None,progress=None):
 db=Path(db_path).resolve();out=Path(output).resolve()
 if out.exists():raise ValueError('Output phải là thư mục mới để không ghi đè bản xuất trước.')
 if scope not in ('ttl','dila'):raise ValueError('Scope phải là ttl hoặc dila.')
 out.mkdir(parents=True,exist_ok=False)
 conn=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=60);conn.row_factory=sqlite3.Row;conn.execute('BEGIN')
 counts={'processed':0,'exported':0,'needs_review':0};started=now();evidence_counts={'active_needs_review':0,'quarantined':0}
 try:
  with (out/'manifest.jsonl').open('x',encoding='utf8') as manifest,(out/'source-evidence-manifest.jsonl').open('x',encoding='utf8') as evidence,zipfile.ZipFile(out/'ttl-v2.zip','x',compression=zipfile.ZIP_DEFLATED) as archive:
   def evidence_record(rec,group):
    name='source-evidence/'+group+'/'+str(rec['id'])+'-'+rec['sha256']+'.txt'
    if digest(rec['raw_text'])!=rec['sha256']:raise ValueError('SHA nguồn DB không khớp; không đóng gói nguồn hỏng.')
    archive.writestr(name,rec['raw_text'])
    evidence.write(json.dumps({'record_id':rec['record_id'],'filename':rec['filename'],'source_group':rec['source_group'],'status':rec['parse_status'],'sha256':rec['sha256'],'zip_entry':name,'note':'Nguyên văn nguồn, không phải hồ sơ TTL v2 đã xác minh'},ensure_ascii=False)+'\n');evidence.flush();evidence_counts[group]+=1
   for identifier,filename in iter_identifiers(conn,scope):
    if limit is not None and counts['processed']>=limit:break
    counts['processed']+=1;row={'identifier':identifier,'filename':filename}
    try:
     if Path(filename).name!=filename or '/' in filename or '\\' in filename:raise ValueError('Filename DB không an toàn.')
     result=export(conn,identifier);text=result['ttl']
     with (out/filename).open('x',encoding='utf8',newline='\n') as f:f.write(text)
     archive.writestr(filename,text)
     row.update(status='exported',sha256=digest(text),person_key=result['profile']['person']['key'],dila_id=result['profile']['person']['dila_id'],issues=result['issues'],assertions=len(result['profile']['assertions']))
     counts['exported']+=1
    except Exception as e:
     row.update(status='needs_review',error=str(e)[:1500]);counts['needs_review']+=1
     if scope=='ttl':
      rec=records.latest(conn,'TTL',identifier[4:],group='active')
      if rec:
       try:evidence_record(rec,'active_needs_review')
       except ValueError as e:row['source_evidence_error']=str(e)
    manifest.write(json.dumps(row,ensure_ascii=False)+'\n');manifest.flush()
    if progress:progress(dict(counts),filename)
   if scope=='ttl':
    for rec in records.iter_group(conn,'quarantine'):evidence_record(rec,'quarantined')
   archive.write(out/'source-evidence-manifest.jsonl','source-evidence-manifest.jsonl')
   summary={'source_evidence_counts':evidence_counts,'source_mode':'database','scope':scope,'started_at':started,'finished_at':now(),'counts':counts,'database_written':False,'active_ttl_written':False,'snapshot':'SQLite read transaction','zip':'ttl-v2.zip','limited':limit is not None}
   archive.write(out/'manifest.jsonl','manifest.jsonl')
   archive.writestr('summary.json',json.dumps(summary,ensure_ascii=False,indent=2))
  (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');return summary
 finally:conn.close()
