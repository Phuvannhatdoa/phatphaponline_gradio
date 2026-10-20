import json,sqlite3,importlib.util
from pathlib import Path
base=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('rollback_local',base/'scripts/rollback-name-generation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=sqlite3.connect('file:'+str(base/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);file=m.MANIFEST;value=json.loads(file.read_text(encoding='utf8'));value['db_fingerprints']={t:m.tablehash(c,t) for t in value['tables']};c.close();file.write_text(json.dumps(value,indent=2),encoding='utf8');print(json.dumps(value['db_fingerprints'],indent=2))
