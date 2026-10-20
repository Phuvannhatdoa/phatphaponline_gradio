import json,sqlite3,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src_python.ttl_db_export import raw_dila
c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);c.row_factory=sqlite3.Row
for name in ['菩提達磨','惠能','慧能','義玄','存獎','方會','明海']:
 print(name,[dict(r) for r in c.execute('SELECT id,name_zh,name_vi FROM people WHERE name_zh=?',(name,))])
for aid in ['A001361','A004980']:
 r=raw_dila(c,aid);print(aid,r['version'],r['sha256']);print(r['raw_text'][:2500])
print('indices', [dict(r) for r in c.execute('pragma index_list(lineage_edge_assertions)')])
