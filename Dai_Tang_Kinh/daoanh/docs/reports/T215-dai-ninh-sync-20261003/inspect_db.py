import sqlite3,json
from pathlib import Path
D=Path.cwd()/'daoanh';c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
for table in ['vn_person_authority','vn_person_relations','lineage_edge_assertions','lineage_edge_consensus','people']:
 print('SCHEMA',table,[(r['name'],r['type']) for r in c.execute('pragma table_info('+table+')')])
for q in ["select * from vn_person_authority where id in ('dao_ninh_dao_khoan','dai_ninh_dao_khoan','thach_suong_so_vien') or dila_id in ('A020545','A001439')", "select * from vn_person_relations where ttl_filename in ('TS-Dai-Ninh-Dao-Khoan','TS-Dao-Ninh-Dao-Khoan')", "select * from lineage_edge_assertions where (object_person_id='A020545') or (source_code='TTL' and ref in ('TS-Dai-Ninh-Dao-Khoan','TS-Dao-Ninh-Dao-Khoan'))", "select * from lineage_edge_consensus where disciple_id='A020545'", "select id,name_zh,name_vi,birth_year,death_year from people where id in ('A020545','A001439')"]:
 rr=[dict(r) for r in c.execute(q)];print('ROWS',json.dumps(rr,ensure_ascii=False))
c.close()
