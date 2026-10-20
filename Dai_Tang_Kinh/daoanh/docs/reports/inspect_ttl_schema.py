import sqlite3,json
from pathlib import Path
c=sqlite3.connect('file:'+str(Path.cwd()/'daoanh/data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
names=[r[0] for r in c.execute('select name from sqlite_master where type=?',('table',))]
print([n for n in names if any(x in n for x in ['source','claim','identity'])])
for n in ['data_sources','dataset_sources','source_authority','entity_claims','person_dila_vi']:
 if n in names:print(n,[(r[1],r[2]) for r in c.execute('pragma table_info('+n+')')])
for n in ['data_sources','dataset_sources','source_authority']:
 if n in names:
  columns=[r[1] for r in c.execute('pragma table_info('+n+')')];want=[x for x in ['id','code','source_code','name','repository_url','source_version','schema_version','legal_status','integration_mode','license_verified','data_license','license_url','implemented'] if x in columns];print(n,json.dumps([dict(r) for r in c.execute('select '+','.join(want)+' from '+n)],ensure_ascii=False))
