# -*- coding: utf-8 -*-
"""T227: nhập nguồn vào bảng additive sau SQLite consistent backup."""
import argparse,json,sqlite3,sys,uuid
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from src_python.ttl_db_sources import import_sources
from src_python.ttl_profile_v2 import now

def main():
 p=argparse.ArgumentParser();p.add_argument('--db',default=str(BASE/'data/lineage.db'));p.add_argument('--archive',default=str(BASE/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'));p.add_argument('--version',default='2026-09');p.add_argument('--output',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
 if not a.apply:raise ValueError('Dùng --apply để nhập nguồn additive; exporter riêng chỉ đọc DB.')
 db=Path(a.db).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
 backup=out/'lineage-before.db';source=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=60);dest=sqlite3.connect(backup)
 print('Đang tạo SQLite backup nhất quán...',flush=True);source.backup(dest,pages=2048,sleep=.01);dest.close();source.close()
 run_id='T227-'+uuid.uuid4().hex
 conn=sqlite3.connect(db,timeout=60);conn.row_factory=sqlite3.Row
 base_tables=['people','vn_person_authority','vn_person_relations','lineage_edge_assertions','person_gen_computed'];before={t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in base_tables}
 with (out/'import-manifest.jsonl').open('x',encoding='utf8') as f:counts=import_sources(conn,a.archive,BASE/'data/ttl',BASE/'data/ttl_quarantine',run_id,a.version,f)
 after={t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in base_tables};conn.close()
 result={'run_id':run_id,'finished_at':now(),'counts':counts,'backup':str(backup),'base_counts_before':before,'base_counts_after':after,'base_tables_written_by_importer':False,'new_tables':['ttl_v2_source_records','ttl_v2_source_import_runs']}
 (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:print('Không nhập nguồn: '+str(e),file=sys.stderr);sys.exit(1)
