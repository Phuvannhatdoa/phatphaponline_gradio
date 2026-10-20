# -*- coding: utf-8 -*-
"""T227: rollback có checksum, code riêng hoặc kho nguồn additive riêng."""
import argparse,hashlib,json,sqlite3,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];REPORT=BASE/'docs/reports/T227-db-ttl-export-20261004'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def within(raw):
 p=(BASE/raw).resolve()
 if BASE.resolve() not in p.parents:raise ValueError('Đường dẫn ngoài workspace.')
 return p
def run(code=False,sources=False,apply=False):
 manifest=json.loads((REPORT/'rollback-manifest.json').read_text(encoding='utf8'))
 if code:
  prepared=[]
  for row in manifest['files']:
   dest=within(row['path'])
   if not dest.is_file() or digest(dest.read_bytes())!=row['after_sha256']:raise ValueError('File đã đổi; giữ WIP: '+row['path'])
   raw=within(row['backup']).read_bytes() if row.get('backup') else None
   if raw is not None and digest(raw)!=row['before_sha256']:raise ValueError('Backup sai checksum: '+row['path'])
   prepared.append((dest,raw))
  print('Code guard PASS:',len(prepared),'files.')
  if apply:
   for dest,raw in prepared:
    if raw is None:dest.unlink()
    else:dest.write_bytes(raw)
 if sources:
  conn=sqlite3.connect(BASE/'data/lineage.db',timeout=60)
  try:
   conn.execute('BEGIN IMMEDIATE');run_id=manifest['source_import_run_id']
   # Không xóa khi một lần import mới có thể đang dùng kho nguồn của đợt này.
   others=conn.execute('SELECT count(*) FROM ttl_v2_source_import_runs WHERE id!=?',(run_id,)).fetchone()[0]
   if others:raise ValueError('Đã có import nguồn khác; cần rollback theo diff, không xóa kho dùng chung.')
   count=conn.execute('SELECT count(*) FROM ttl_v2_source_records WHERE import_run_id=?',(run_id,)).fetchone()[0]
   if count!=manifest['source_records_inserted']:raise ValueError('Kho nguồn đã đổi; dừng để kiểm tra.')
   print('Kho nguồn guard PASS:',count,'records. Bảng people/VN/lineage không bị sửa.')
   if apply:
    conn.execute('DELETE FROM ttl_v2_source_records WHERE import_run_id=?',(run_id,));conn.execute('DELETE FROM ttl_v2_source_import_runs WHERE id=?',(run_id,));conn.commit()
   else:conn.rollback()
  except Exception:conn.rollback();raise
  finally:conn.close()
 print('Đã áp rollback.' if apply else 'Dry-run; thêm --apply để áp. DB backup, XML/TTL gốc và các gói xuất được giữ.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--code',action='store_true');p.add_argument('--sources-db',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
 try:
  if not (a.code or a.sources_db):raise ValueError('Chọn --code hoặc --sources-db.')
  run(a.code,a.sources_db,a.apply)
 except (ValueError,OSError,sqlite3.Error) as e:print('Không rollback: '+str(e),file=sys.stderr);sys.exit(1)
