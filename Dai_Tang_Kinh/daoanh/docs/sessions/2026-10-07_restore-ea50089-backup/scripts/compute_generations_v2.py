# -*- coding: utf-8 -*-
"""T232: snapshot SQLite, tính từng người và xuất JSONL; không apply dữ liệu cũ."""
import argparse,json,sqlite3,sys,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src_python import generation_engine_v2 as g
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--person');ap.add_argument('--scope',choices=['dila','ttl'],default='ttl');ap.add_argument('--limit',type=int);ap.add_argument('--out',required=True);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    live=sqlite3.connect('file:'+str(ROOT/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True)
    snap=sqlite3.connect(out/'input-snapshot.db');live.backup(snap,pages=512);live.close();snap.row_factory=sqlite3.Row
    if a.person:ids=[a.person]
    elif a.scope=='ttl':
        ids=(r[0] for r in snap.execute("SELECT DISTINCT dila_id FROM vn_person_authority WHERE status='verified' AND dila_id GLOB 'A[0-9][0-9][0-9][0-9][0-9][0-9]' ORDER BY dila_id"))
    else:ids=(r[0] for r in snap.execute('SELECT id FROM people ORDER BY id'))
    counts=collections.Counter();processed=0
    with (out/'results.jsonl').open('w',encoding='utf8') as f:
        for aid in ids:
            if a.limit is not None and processed>=a.limit:break
            try:
                report=g.calculate_all(snap,aid)
                for r in report['results']:counts[r['status']]+=1
            except ValueError as e:report={'person_id':aid,'error':str(e)};counts['error']+=1
            f.write(g.canonical(report)+'\n');processed+=1
    summary={'algorithm':g.VERSION,'processed_people':processed,'statuses':dict(counts),'legacy_mutations':0,'scope':a.scope}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False));snap.close()
if __name__=='__main__':main()
