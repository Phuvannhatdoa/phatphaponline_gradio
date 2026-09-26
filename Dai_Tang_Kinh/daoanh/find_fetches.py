#!/usr/bin/env python3
import os
os.chdir('E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh')
with open('home.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()
lines = c.split('\n')
for i, line in enumerate(lines, 1):
    if 'fetch' in line.lower():
        print(f'Line {i}: {line[:200]}')