# -*- coding: utf-8 -*-
"""Helper: chạy 1 lệnh, ghi stdout+stderr+exit code ra file UTF-8.
Usage: python -X utf8 run_capture.py <out_file> <cmd...>
"""
import subprocess
import sys

out_path = sys.argv[1]
cmd = sys.argv[2:]
p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                   shell=(sys.platform == 'win32' and cmd[0] == 'npm'))
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(p.stdout or '')
    f.write(p.stderr or '')
    f.write('\n=== EXIT CODE: %d ===\n' % p.returncode)
print('exit', p.returncode, '->', out_path)
