import zipfile,xml.etree.ElementTree as E,json,re,sqlite3
from pathlib import Path
out=Path('daoanh/docs/reports/T215-eight-uri-20261003')
p=Path('daoanh/data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip')
found={}; ns={'t':'http://www.tei-c.org/ns/1.0'}
with zipfile.ZipFile(p) as z:
 name=next(n for n in z.namelist() if n.endswith('Buddhist_Studies_Person_Authority.xml'))
 with z.open(name) as f:
  for _,e in E.iterparse(f,events=('end',)):
   if e.tag.split('}')[-1]!='person':continue
   ident=e.attrib.get('{http://www.w3.org/XML/1998/namespace}id')
   names=[''.join(x.itertext()).strip() for x in e.findall('.//t:persName',ns)]
   if any(re.search('鏡寧|敬寧|智板|智本|突空|如長|如杖|子融|明弘|明宏|真璞|真樸|雪槱|靈臼|石臼|大寧道寬|福州大安',n) for n in names):
    found[ident]={'names':names,'xml':E.tostring(e,encoding='unicode')}
   e.clear()
(out/'dila-candidates.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in found.items():print(k,','.join(v['names']))
c=sqlite3.connect('file:daoanh/data/lineage.db?mode=ro',uri=True);c.row_factory=sqlite3.Row
rows=[dict(r) for r in c.execute("select id,name_vi,name_zh,dila_id,status,ttl_filename from vn_person_authority where ttl_filename in (?,?,?,?,?,?,?,?,?)",tuple(x[:-4] for x in ['TS-Phuoc-Chau-Dai-An.ttl','TS-Di-Phong-Kinh-Ninh.ttl','TS-Dot-Khong-Tri-Ban.ttl','TS-Dai-Ninh-Dao-Khoan.ttl','TS-Dai-Xa-Nhu-Truong.ttl','TS-Minh-Hoang-Tu-Dung.ttl','TS-Tuyet-Giau-Chon-Phac.ttl','TS-Linh-Cuu.ttl','TS-Dao-Ninh-Dao-Khoan.ttl']))]
print('LOCAL_AUTHORITY',json.dumps(rows,ensure_ascii=False))
(out/'db-mapping-before.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
