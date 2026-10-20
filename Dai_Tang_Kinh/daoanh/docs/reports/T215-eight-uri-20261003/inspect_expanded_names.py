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
   if any(re.search('夷峰|夷峯|鏡寧|敬寧|智板|智本|突空|大舍|大社|大赦|如長|如杖|如章|子融|明弘|明宏|真璞|真樸|雪槱|靈臼|灵臼|石臼|大寧道寬|福州大安',n) for n in names):
    found[ident]={'names':names,'xml':E.tostring(e,encoding='unicode')}
   e.clear()
(out/'dila-expanded-candidates.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in found.items():print(k,','.join(v['names']))
