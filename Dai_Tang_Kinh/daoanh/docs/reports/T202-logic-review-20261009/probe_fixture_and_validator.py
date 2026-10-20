import json,sys,importlib.util,dataclasses
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import canonical_lock as cl
spec=importlib.util.spec_from_file_location('t202_unit_fixture',ROOT/'tests/test_t166_canonical_lock.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
con,tmp=mod._mkdb()
out={}
try:
    cl.safe_errors()
    cl.build_canonical_lock(con,'\u5c11\u6797\u5bfa')
    out['original_fixture_schema_errors']=cl.safe_errors()
    con.execute('ALTER TABLE places_dila RENAME COLUMN dila_id TO id')
    con.execute('DELETE FROM namevi_map_places')
    out['synthetic_invalid_name_results']={}
    for text in ['Th\u1eadp S?t H\u1ea3i','\u6cd5\u96c5','Th\u00c3\u00a1p','An']:
        con.execute('UPDATE canonical_decision SET canonical_name_vi=?',(text,))
        out['synthetic_invalid_name_results'][text]=[dataclasses.asdict(e) for e in cl.build_canonical_lock(con,'\u5c11\u6797\u5bfa')]
    out['corrected_fixture_schema_errors']=cl.safe_errors()
finally:
    con.close()
    Path(tmp).unlink(missing_ok=True)
print(json.dumps(out,ensure_ascii=False,indent=2))
