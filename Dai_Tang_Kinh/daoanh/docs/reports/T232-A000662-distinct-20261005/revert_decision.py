import argparse,json,sqlite3,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from src_python import generation_engine_v2 as g
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
folder=Path(__file__).parent
before=json.loads((root/'data/backups/T232-A000662-distinct-20261005/scheme-before.json').read_text(encoding='utf8'));after=json.loads((folder/'scheme-after.json').read_text(encoding='utf8'))
c=sqlite3.connect((root/'data/lineage.db').resolve().as_uri()+'?mode='+('rw' if args.apply else 'ro'),uri=True,timeout=30);c.row_factory=sqlite3.Row
current=next(x for x in g.schemes(c) if x['id']=='linji_chucthanh')
if current['_revision']!=after['_revision'] or current['_sha256']!=after['_sha256']:raise ValueError('Có revision mới của phiên khác; không hoàn tác đè.')
g.validate_scheme(c,before)
result={'dry_run':not args.apply,'scheme':'linji_chucthanh','expected_revision':after['_revision'],'restore_as_new_revision':True,'legacy_mutations':0,'audit_revision_retained':True}
if args.apply:result['new_revision']=g.save_scheme(c,before,after['_revision'])['_revision']
print(json.dumps(result));c.close()
