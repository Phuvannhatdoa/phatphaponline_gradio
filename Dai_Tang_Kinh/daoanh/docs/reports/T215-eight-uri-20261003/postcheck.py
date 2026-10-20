import json,hashlib,re,sys,sqlite3
from pathlib import Path
D=Path.cwd()/'daoanh'; O=D/'docs/reports/T215-eight-uri-20261003';B=D/'data/backups/T215-eight-uri-20261003'
sys.path.insert(0,str(D/'data/backups/T215-fix-sync-20261002/python-deps'))
from rdflib import Graph
m=json.loads((B/'manifest.json').read_text(encoding='utf-8'));cases=json.loads((O/'cases.json').read_text(encoding='utf-8'));changes={x['file']:x for x in m['changes']};results=[]
for c in cases['cases']:
 p=D/'data/ttl'/c['file']
 if not p.exists():assert not c['exists'];results.append({'file':c['file'],'exists':False});continue
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();before=(B/c['file']).read_bytes()
 assert h==(changes[c['file']]['after_sha256'] if c['file'] in changes else c['before_sha256'])
 print('CHECK',p.name,flush=True);g=Graph().parse(data=raw.decode('utf-8-sig'),format='turtle');old=before.decode('utf-8-sig')
 c['biography_openings']=[x.strip()[:220] for x in re.findall(r'biographicalNote\s+"""(.*?)"""@vi',old,re.S)]
 c['monk_blocks']=len(re.findall(r'a\s+<bkg:Monk>',old));c['applied']=c['file'] in changes
 results.append({'file':c['file'],'rdf_triples':len(g),'hash_verified':True,'modified':c['file'] in changes,'monk_blocks_before':c['monk_blocks'],'generation_preserved':re.findall(r'generationOrder\s+(\d+)',old)==re.findall(r'generationOrder\s+(\d+)',raw.decode('utf-8-sig'))})
# Read-only DB, chụp lại đúng phạm vi để so sánh. Không tạo bất cứ connection ghi nào.
con=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
fns=[x['file'][:-4] for x in cases['cases']]+['TS-Dao-Ninh-Dao-Khoan']
rows=[dict(r) for r in con.execute('select id,name_vi,name_zh,dila_id,status,ttl_filename from vn_person_authority where ttl_filename in ('+','.join('?' for _ in fns)+')',fns)]
con.close();old=json.loads((O/'db-mapping-before.json').read_text(encoding='utf-8'));assert rows==old
(O/'db-mapping-after.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');(O/'postcheck.json').write_text(json.dumps({'files':results,'db_snapshot_unchanged':True,'db_write_connections':0},ensure_ascii=False,indent=2),encoding='utf-8');(O/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checked':len(results),'rdf_pass':sum('rdf_triples' in x for x in results),'modified':sum(x.get('modified',False) for x in results),'db_snapshot_unchanged':True},ensure_ascii=False))
