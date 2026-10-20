# -*- coding: utf-8 -*-
"""Tóm tắt cấu trúc từng file trong docs/integration để rà soát (chỉ đọc, không ghi file dự án)."""
import glob
import os
import re
import sys

BASE = os.path.join(os.path.dirname(__file__), '..', 'docs', 'integration')
start, end = int(sys.argv[1]), int(sys.argv[2])
files = sorted(glob.glob(os.path.join(BASE, '*.md')))[start:end]
for path in files:
    f = os.path.basename(path)
    t = open(path, encoding='utf-8', errors='ignore').read()
    lines = [l.rstrip() for l in t.split('\n') if l.strip()]
    title = next((l for l in lines if l.startswith('# ')), '')
    status = ''
    m = re.search(r'\*\*Status:\*\*\s*([^\n]{0,70})', t) or re.search(r'^status:\s*(\S+)', t, re.M)
    if m:
        status = m.group(1).strip()
    heads = [l[3:58] for l in lines if l.startswith('## ')]
    done = len(re.findall(r'- \[x\]', t, re.I))
    todo = len(re.findall(r'- \[ \]', t))
    print(f'### {f} | {len(t)}B | [x]{done} [ ]{todo} | {status}')
    print(f'   {title[:100]}')
    print('   H: ' + ' / '.join(heads[:14]))
