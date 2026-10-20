import sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from src_python.ttl_db_export import raw_dila
c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);c.row_factory=sqlite3.Row
for name in ['良价','文偃','文益','靈祐','慧寂']:
 print(name,[dict(r) for r in c.execute('SELECT id,name_zh,name_vi FROM people WHERE name_zh=?',(name,))])
