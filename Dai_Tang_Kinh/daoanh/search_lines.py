#!/usr/bin/env python3
with open('E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/home.html', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'search' in line.lower():
        print(f'Line {i}: {line.rstrip()[:200]}')
PYEOF