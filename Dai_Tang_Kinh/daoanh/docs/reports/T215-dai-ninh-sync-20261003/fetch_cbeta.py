import sys,json,hashlib
from pathlib import Path
D=Path.cwd()/'daoanh';sys.path.insert(0,str(D/'data/backups/T215-fix-sync-20261002/python-deps'))
import requests
B=D/'data/backups/T215-dai-ninh-sync-20261003';O=D/'docs/reports/T215-dai-ninh-sync-20261003';p=B/'X88n1667.xml';url='https://raw.githubusercontent.com/cbeta-org/xml-p5/master/X/X88/X88n1667.xml'
if not p.exists():
 with requests.get(url,stream=True,timeout=25) as r,p.open('wb') as f:
  r.raise_for_status()
  for chunk in r.iter_content(65536):
   if chunk:f.write(chunk)
t=p.read_text(encoding='utf-8');assert '突空智板' in t
out={'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checked':'2026-10-03','excerpt_xml':[s for s in t.splitlines() if any('n="0560a0'+str(i)+'"' in s for i in range(3,8))],'tri_ban_name_present':True,'dai_xa_ru_chang_present':'如長' in t,'tuyet_huu_present':'雪槱' in t,'correction':'0560a03 thuộc câu về chữ清 của phái箬庵通問, không phải ĐạiXa; không có如長 trong X1667. Không chứng minh nguyên nhân chưa có AuthorityID.'}
(O/'cbeta-evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
