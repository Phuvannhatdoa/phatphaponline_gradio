import sqlite3,json,zipfile,xml.etree.ElementTree as E,re,hashlib
from pathlib import Path
D=Path.cwd()/'daoanh';O=D/'docs/reports/T215-closeout-20261003';c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
queries={
'authority':"select * from vn_person_authority where id in ('phuc_chau_dai_an','phuoc_chau_dai_an','bach_truong_hoai_hai','thach_cuu','ma_to_dao_nhat','dao_ninh_dao_khoan','phong_huyet_dien_chieu','nam_vien_hue_ngung')",
'relations':"select * from vn_person_relations where person_id in ('phuc_chau_dai_an','phuoc_chau_dai_an','thach_cuu','phong_huyet_dien_chieu')",
'assertions':"select * from lineage_edge_assertions where object_person_id in ('A003636','A019919','A004981') or (source_code='TTL' and ref in ('TS-Linh-Cuu','TS-Thach-Cuu','TS-Phuoc-Chau-Dai-An','TS-Di-Phong-Kinh-Ninh','TS-Dot-Khong-Tri-Ban','TS-Dai-Xa-Nhu-Truong','TS-Minh-Hoang-Tu-Dung','TS-Tuyet-Giau-Chon-Phac','TS-Truong-Vien','TS-Phuc-Chau-Dai-An'))",
'consensus':"select * from lineage_edge_consensus where disciple_id in ('A003636','A019919','A004981')"}
a={k:[dict(r) for r in c.execute(q)] for k,q in queries.items()};(O/'inspection.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8');print('authority',[(r['id'],r['dila_id'],r['generation_order'],r['ttl_filename']) for r in a['authority']]);print('relations',a['relations']);print('assertions',[(r['id'],r['source_code'],r['subject_person_id'],r['object_person_id'],r['ref'],r['status']) for r in a['assertions']]);c.close()
ids={'A003636','A001897','A019919','A003623','A004981','A004018','A038890'};records={};n={'t':'http://www.tei-c.org/ns/1.0'};p=D/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
with zipfile.ZipFile(p) as z:
 name=next(x for x in z.namelist() if x.endswith('Buddhist_Studies_Person_Authority.xml'))
 with z.open(name) as f:
  for _,e in E.iterparse(f,events=('end',)):
   if e.tag.split('}')[-1]!='person':continue
   aid=e.get('{http://www.w3.org/XML/1998/namespace}id')
   if aid in ids:records[aid]={'names':[''.join(x.itertext()).strip() for x in e.findall('t:persName',n)],'relations':[dict(x.attrib) for x in e.findall('.//t:relation',n)],'xml':E.tostring(e,encoding='unicode')}
   e.clear()
(O/'dila-evidence.json').write_text(json.dumps({'records':records,'archive_sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'source':'https://authority.dila.edu.tw/downloads/authority_person.2026-09.zip'},ensure_ascii=False,indent=2),encoding='utf-8')
print('DILA',[(k,v['names'],[x for x in v['relations'] if x.get('type')=='teacher']) for k,v in records.items()])
