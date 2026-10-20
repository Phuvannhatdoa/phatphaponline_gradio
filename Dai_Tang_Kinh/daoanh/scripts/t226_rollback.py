# -*- coding: utf-8 -*-
"""T226: hoàn tác file-level có checksum; không xóa TTL/staging hoặc ghi DB."""
import argparse,hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
REPORT=BASE/'docs/reports/T226-ttl-profile-20261003'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def within(raw):
 p=(BASE/raw).resolve()
 if BASE.resolve() not in p.parents:raise ValueError('Đường dẫn ngoài workspace: '+str(raw))
 return p
def run(apply=False):
 data=json.loads((REPORT/'rollback-manifest.json').read_text(encoding='utf8'))
 prepared=[]
 for row in data['files']:
  target=within(row['path'])
  if not target.is_file() or sha(target.read_bytes())!=row['after_sha256']:raise ValueError('File đã thay đổi; dừng để không mất WIP: '+row['path'])
  backup=None
  if row.get('backup'):
   backup=within(row['backup']).read_bytes()
   if sha(backup)!=row['before_sha256']:raise ValueError('Backup sai checksum: '+row['path'])
  prepared.append((target,backup))
 print('Guard PASS:',len(prepared),'files; DB/TTL active/staging giữ nguyên.')
 if apply:
  for target,backup in prepared:
   if backup is None:target.unlink()
   else:target.write_bytes(backup)
  print('Đã hoàn tác code. Restart main bằng Administrator nếu đã deploy; cập nhật task/docs riêng.')
 else:print('Dry-run; thêm --apply để thực hiện.')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 try:run(args.apply)
 except (ValueError,OSError) as e:print('Không rollback: '+str(e),file=sys.stderr);sys.exit(1)
