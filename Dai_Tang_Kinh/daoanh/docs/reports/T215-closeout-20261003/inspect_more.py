import sqlite3,json
from pathlib import Path
D=Path.cwd()/'daoanh';c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
for q in ["select id,dila_id,name_vi,name_zh,ttl_filename,generation_order from vn_person_authority where dila_id in ('A003623','A038890','A004982','A004981','A003636')", "select source_code,count(*) n from lineage_edge_assertions where subject_person_id='A038890' or object_person_id='A038890' group by source_code", "select id,name_zh,name_vi from people where id in ('A003623','A038890','A004982')"]:print(json.dumps([dict(r) for r in c.execute(q)],ensure_ascii=False))
