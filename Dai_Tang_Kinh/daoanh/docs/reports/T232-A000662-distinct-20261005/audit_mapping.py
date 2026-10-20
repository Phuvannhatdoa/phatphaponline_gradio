import json,sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[3];c=sqlite3.connect((root/'data/lineage.db').resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
queries={
 'ttl_mapping':("SELECT * FROM ttl_mapping WHERE dila_id=? OR ttl_filename LIKE '%Minh-Hai%'",('A000662',)),
 'ttl_master':("SELECT id,monk_id,name_vi,dila_id,filename FROM ttl_master WHERE dila_id=? OR filename LIKE '%Minh-Hai%'",('A000662',)),
 'name_vi_map':("SELECT id,name_vi,name_vi_final,name_zh,dila_id,source,confidence FROM name_vi_map WHERE dila_id=? OR name_vi LIKE '%Minh Hải Pháp Bảo%' OR name_vi_final LIKE '%Minh Hải Pháp Bảo%'",('A000662',)),
 'canon_author_mapping':("SELECT id,work_id,author_name_vi,author_name_zh,author_dila_id,author_role,verified_source FROM canon_author_mapping WHERE author_dila_id=?",('A000662',))}
result={}
for key,(sql,args) in queries.items():result[key]=[dict(row) for row in c.execute(sql,args)]
(Path(__file__).parent/'mapping-inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));c.close()
