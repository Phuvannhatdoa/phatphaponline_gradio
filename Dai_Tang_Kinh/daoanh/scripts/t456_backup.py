# -*- coding: utf-8 -*-
"""T456 — backup routes_lineage.py + core.py + index.html trước khi sửa (file untracked → KHÔNG dùng git checkout)."""
import os, shutil, sys, datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
DEST = os.path.join(BASE, "docs", "sessions", "2026-10-30-t456")
os.makedirs(DEST, exist_ok=True)

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
for f in ["routes_lineage.py", "core.py", "index.html"]:
    src = os.path.join(BASE, f)
    if not os.path.exists(src):
        print("MISSING", f); continue
    shutil.copy2(src, os.path.join(DEST, "%s.bak-before-T456-%s" % (f, ts)))
    print("backup %-22s -> %s.bak-before-T456-%s (%d bytes)" % (
        f, f, ts, os.path.getsize(src)))
print("\nDEST:", DEST)

# kiểm tra places.html có hỗ trợ ?select= không (dùng cho click dòng địa danh)
ph = open(os.path.join(BASE, "places.html"), encoding="utf-8", errors="replace").read()
for kw in ["select=", "URLSearchParams", "?select", "get('select')", 'get("select")']:
    print("   places.html chứa %-18s : %s" % (kw, kw in ph))
