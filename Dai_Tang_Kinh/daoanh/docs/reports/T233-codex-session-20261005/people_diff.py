import json,sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[3]
c=sqlite3.connect((root/'data/lineage.db').resolve().as_uri()+'?mode=ro',uri=True)
c.execute('ATTACH DATABASE ? AS baseline',((root/'data/backups/T232-generation-engine-20261004/db-install/lineage-before.db').resolve().as_uri()+'?mode=ro',))
cols=[r[1] for r in c.execute('PRAGMA table_info(people)')]
def q(x):return '"'+x.replace('"','""')+'"'
counts=c.execute('SELECT '+','.join('sum(p.'+q(k)+' IS NOT b.'+q(k)+')' for k in cols)+' FROM people p JOIN baseline.people b ON p.id=b.id').fetchone()
changes={k:v for k,v in zip(cols,counts) if v}
samples={}
for k in changes:
 if k in ['raw_xml','biography','bio_zh','biographicalNote']:continue
 samples[k]=c.execute('SELECT p.id,b.'+q(k)+',p.'+q(k)+' FROM people p JOIN baseline.people b ON p.id=b.id WHERE p.'+q(k)+' IS NOT b.'+q(k)+' LIMIT 5').fetchall()
result={'field_change_counts':changes,'samples':samples,'read_only':True,'attribution':'Observed shared-DB changes; this read does not prove which external writer caused them.'}
(Path(__file__).parent/'people-diff.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));c.close()
