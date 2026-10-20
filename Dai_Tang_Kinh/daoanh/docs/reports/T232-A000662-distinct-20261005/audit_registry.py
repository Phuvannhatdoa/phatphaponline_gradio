import json,sqlite3,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from src_python import generation_engine_v2 as g
c=sqlite3.connect((root/'data/lineage.db').resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
r=c.execute('SELECT * FROM people WHERE id=?',('A000662',)).fetchone()
result={'dila':{k:r[k] for k in r.keys() if k in ['id','name_zh','name_vi','dynasty','birth','death','birth_year','death_year','bio_zh']},'identity':g.identity(c,'A000662'),'chucthanh':next(x for x in g.schemes(c) if x['id']=='linji_chucthanh'),'tables':[]}
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%identity%' OR name LIKE '%map%' OR name LIKE '%crosswalk%' OR name LIKE '%ttl%')"):
 name=row[0];cols=[x[1] for x in c.execute('PRAGMA table_info("'+name.replace('"','""')+'")')];result['tables'].append({'name':name,'cols':cols})
(Path(__file__).parent/'inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));c.close()
