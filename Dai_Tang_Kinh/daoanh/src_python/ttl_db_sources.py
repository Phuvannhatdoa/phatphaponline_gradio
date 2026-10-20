# -*- coding: utf-8 -*-
"""T227: kho nguồn additive. XML/TTL được lưu từng record, bảng cũ bất biến."""
import json, hashlib, sqlite3, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
from src_python import ttl_profile_v2 as m
TABLE='ttl_v2_source_records'
RUNS='ttl_v2_source_import_runs'
SCHEMA='''
CREATE TABLE IF NOT EXISTS ttl_v2_source_import_runs (
 id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
 finished_at TEXT, metadata_json TEXT NOT NULL, counts_json TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ttl_v2_one_source_import ON ttl_v2_source_import_runs(status) WHERE status='in_progress';
CREATE TABLE IF NOT EXISTS ttl_v2_source_records (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, record_id TEXT NOT NULL,
 source_group TEXT NOT NULL, filename TEXT NOT NULL, version TEXT NOT NULL,
 sha256 TEXT NOT NULL, raw_text TEXT NOT NULL, parse_status TEXT NOT NULL,
 main_slug TEXT, metadata_json TEXT NOT NULL, import_run_id TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(kind,record_id,source_group,version,sha256)
);
CREATE INDEX IF NOT EXISTS idx_ttl_v2_source_lookup ON ttl_v2_source_records(kind,record_id,source_group,id);
CREATE INDEX IF NOT EXISTS idx_ttl_v2_source_slug ON ttl_v2_source_records(kind,main_slug,source_group,id);
'''
def file_digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def import_sources(conn,archive,ttl_dir,quarantine_dir,run_id,version='2026-09',manifest=None):
 """Chỉ INSERT kho nguồn mới; không UPDATE people/lineage/VN tables."""
 conn.executescript(SCHEMA)
 stamp=m.now();counts={'xml':0,'ttl_active':0,'ttl_quarantine':0,'ttl_valid':0,'ttl_needs_review':0,'inserted':0}
 archive=Path(archive);archive_sha=file_digest(archive)
 metadata={'archive':str(archive),'archive_sha256':archive_sha,'version':version,'ttl_dir':str(ttl_dir),'quarantine_dir':str(quarantine_dir)}
 conn.execute('INSERT INTO '+RUNS+'(id,status,started_at,metadata_json) VALUES (?,?,?,?)',(run_id,'in_progress',stamp,json.dumps(metadata,ensure_ascii=False)));conn.commit()
 def put(kind,rid,group,filename,edition,raw,status,slug='',extra=None):
  digest=m.digest(raw)
  cur=conn.execute('INSERT OR IGNORE INTO '+TABLE+'(kind,record_id,source_group,filename,version,sha256,raw_text,parse_status,main_slug,metadata_json,import_run_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(kind,record_id,source_group,version,sha256) DO UPDATE SET import_run_id=excluded.import_run_id,created_at=excluded.created_at WHERE (SELECT status FROM ttl_v2_source_import_runs WHERE id=ttl_v2_source_records.import_run_id)=?',(kind,rid,group,filename,edition,digest,raw,status,slug,json.dumps(extra or {},ensure_ascii=False),run_id,stamp,'failed'))
  counts['inserted']+=cur.rowcount
  if manifest:manifest.write(json.dumps({'kind':kind,'record_id':rid,'group':group,'sha256':digest,'status':status,'inserted':bool(cur.rowcount)},ensure_ascii=False)+'\n')
  if sum(counts[k] for k in ('xml','ttl_active','ttl_quarantine'))%200==0:conn.commit()
 try:
  with zipfile.ZipFile(archive) as z:
   entry=next((n for n in z.namelist() if n.endswith('Person_Authority.xml')),None)
   if not entry:raise ValueError('Archive không có Person_Authority.xml.')
   with z.open(entry) as stream:
    stack=[]
    for event,node in ET.iterparse(stream,events=('start','end')):
     if event=='start':stack.append(node);continue
     if node.tag=='{http://www.tei-c.org/ns/1.0}person':
      aid=node.get('{http://www.w3.org/XML/1998/namespace}id','')
      if aid:
       counts['xml']+=1
       put('DILA_XML',aid,'authority',entry,version,ET.tostring(node,encoding='unicode'),'valid',extra={'archive_sha256':archive_sha,'record_serialization':'ElementTree TEI element; original archive retained'})
      if len(stack)>1:stack[-2].remove(node)
     stack.pop()
  for group,directory in [('active',Path(ttl_dir)),('quarantine',Path(quarantine_dir))]:
   paths=sorted(directory.glob('*.ttl')) if group=='active' else sorted(directory.rglob('*.ttl'))
   for file in paths:
    raw=file.read_bytes().decode('utf-8');counts['ttl_'+group]+=1;slug='';extra={};status='quarantined' if group=='quarantine' else 'needs_review'
    if group=='active':
     try:
      p=m.import_legacy(raw,file.name);slug=p['person']['legacy_slug'];check=m.validate(p);status='valid' if check['conforms'] else 'needs_review'
      extra={'person':p['person'],'validation':check,'source_rdf_triples':p['migration']['source_rdf_triples']}
     except Exception as e:extra={'error':str(e)[:1000]}
     counts['ttl_valid' if status=='valid' else 'ttl_needs_review']+=1
    else:extra={'note':'Nguồn cách ly được bảo toàn, không đưa thành hồ sơ active.'}
    put('TTL',file.name if group=='active' else file.relative_to(directory).as_posix(),group,file.name,'sha256:'+m.digest(raw),raw,status,slug,extra)
  conn.execute('UPDATE '+RUNS+' SET status=?,finished_at=?,counts_json=? WHERE id=?',('completed',m.now(),json.dumps(counts),run_id));conn.commit()
  return counts
 except Exception as e:
  conn.rollback();conn.execute('UPDATE '+RUNS+' SET status=?,finished_at=?,counts_json=? WHERE id=?',('failed',m.now(),json.dumps({'counts':counts,'error':str(e)}),run_id));conn.commit();raise

def available(conn):return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone() is not None

def latest(conn,kind,record_id=None,slug=None,group=None):
 if not available(conn):return None
 sql='SELECT s.* FROM '+TABLE+' s JOIN '+RUNS+' r ON r.id=s.import_run_id WHERE r.status=? AND s.kind=?';args=['completed',kind]
 for col,val in [('record_id',record_id),('main_slug',slug),('source_group',group)]:
  if val is not None:sql+=' AND s.'+col+'=?';args.append(val)
 return conn.execute(sql+' ORDER BY s.id DESC LIMIT 1',args).fetchone()

def iter_group(conn,group):
 if not available(conn):raise ValueError('Chưa nhập nguyên văn nguồn vào kho DB v2.')
 sql='SELECT s.* FROM '+TABLE+' s JOIN (SELECT max(s.id) id FROM '+TABLE+' s JOIN '+RUNS+' r ON r.id=s.import_run_id WHERE s.kind=? AND s.source_group=? AND r.status=? GROUP BY s.record_id) x ON x.id=s.id ORDER BY s.filename'
 yield from conn.execute(sql,('TTL',group,'completed'))

def iter_ttl(conn):yield from iter_group(conn,'active')
