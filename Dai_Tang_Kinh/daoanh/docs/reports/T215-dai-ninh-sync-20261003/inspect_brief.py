import sqlite3,json
from pathlib import Path
D=Path.cwd()/'daoanh';O=D/'docs/reports/T215-dai-ninh-sync-20261003';c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
queries={
'authority':("select * from vn_person_authority where id in ('dao_ninh_dao_khoan','thach_suong_so_vien')",()),
'relations':("select * from vn_person_relations where person_id='dao_ninh_dao_khoan'",()),
'assertions':("select * from lineage_edge_assertions where object_person_id='A020545' or (source_code='TTL' and ref in ('TS-Dai-Ninh-Dao-Khoan','TS-Dao-Ninh-Dao-Khoan'))",()),
'consensus':("select * from lineage_edge_consensus where disciple_id='A020545'",()),
'people':("select * from people where id in ('A020545','A001439')",())}
a={k:[dict(r) for r in c.execute(*v)] for k,v in queries.items()};(O/'inspection-before.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
print('ASSERTIONS',json.dumps(a['assertions'],ensure_ascii=False));print('CONSENSUS',json.dumps(a['consensus'],ensure_ascii=False));print('PEOPLE',json.dumps([{k:r[k] for k in ['id','name_zh','name_vi','birth_year','death_year']} for r in a['people']],ensure_ascii=False));c.close()
