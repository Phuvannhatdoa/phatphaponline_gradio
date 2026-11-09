import os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh'
DEST = os.path.join(BASE, 'docs', 'sessions', '2026-10-30-t456')
os.makedirs(DEST, exist_ok=True)
for f in ['routes_lineage.py', 'core.py', 'index.html', 'app.py']:
    src = os.path.join(BASE, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(DEST, f))
        print('OK backup', f, '-> session dir')
