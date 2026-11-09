import sqlite3
import sys

src_path, dst_path = sys.argv[1], sys.argv[2]
src = sqlite3.connect(f'file:{src_path}?mode=ro', uri=True)
dst = sqlite3.connect(dst_path)
src.backup(dst)
dst.close()
src.close()
chk = sqlite3.connect(dst_path)
result = chk.execute('PRAGMA quick_check').fetchone()[0]
chk.close()
if result != 'ok':
    sys.exit(f'quick_check failed: {result}')
