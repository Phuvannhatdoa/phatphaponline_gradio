import sqlite3,json,re
from pathlib import Path
D=Path.cwd()/'daoanh';c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
for q in ["select id,ttl_filename,name_vi,name_zh,dila_id,status,generation_order from vn_person_authority where dila_id in ('A003636','A001897','A019919','A020545') or id in ('phuoc_chau_dai_an','bach_truong_hoai_hai','thach_cuu','phong_huyet_dien_chieu')", "select * from lineage_edge_assertions where (source_code='TTL' and ref in ('TS-Linh-Cuu','TS-Thach-Cuu','TS-Phuoc-Chau-Dai-An','TS-Dai-Xa-Nhu-Truong','TS-Minh-Hoang-Tu-Dung','TS-Tuyet-Giau-Chon-Phac','TS-Di-Phong-Kinh-Ninh','TS-Dot-Khong-Tri-Ban')) or object_person_id='A003636'", "select * from lineage_edge_consensus where disciple_id='A003636'"]:
 print(json.dumps([dict(r) for r in c.execute(q)],ensure_ascii=False))
c.close()
for fn in ['TS-Truong-Vien.ttl','TS-Phuc-Chau-Dai-An.ttl','TS-Phong-Huyet-Dien-Chieu.ttl','TS-Thach-Cuu.ttl']:
 p=D/'data/ttl'/fn;print('FILE',fn,'EXISTS',p.exists())
 if p.exists():
  t=p.read_text(encoding='utf-8-sig');print(t[:450]);print('\n'.join(s for s in t.splitlines() if any(k in s for k in ['hasTeacher','hasDisciple','generationOrder'])))
