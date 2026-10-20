# -*- coding: utf-8 -*-
"""VERIFY T130/T131 docs state (2026-09-18) — ground truth trước khi commit docs-only."""
import io, os, glob, subprocess

G = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app'
D = os.path.join(G, 'Dai_Tang_Kinh', 'daoanh')

def rd(rel):
    return io.open(os.path.join(D, rel), encoding='utf-8').read()

print('=== 1) audit report tồn tại? ===')
for f in sorted(glob.glob(os.path.join(D, 'docs', 'sessions', '*t130*t131*audit*'))):
    print('   CÓ:', os.path.basename(f), os.path.getsize(f), 'bytes')
if not glob.glob(os.path.join(D, 'docs', 'sessions', '*t130*t131*audit*')):
    print('   ⚠️ CHƯA có audit report file')

print()
print('=== 2) tasktodo.md rows T130/T131 — có marker AUDIT? ===')
c = rd('docs/tasktodo.md')
for i, l in enumerate(c.splitlines(), 1):
    if l.strip().startswith('**T130') or l.strip().startswith('**T131'):
        has_mark = 'AUDIT' in l or 'audit' in l or 'integration' in l
        print('   %4d| %s' % (i, l[:120]))
        print('        -> marker audit:', 'CÓ' if has_mark else 'CHƯA')

print()
print('=== 3) git status --short (docs-only so sánh) ===')
r = subprocess.run(['git', '-C', G, 'status', '--short'], capture_output=True, encoding='utf-8')
print(r.stdout)
