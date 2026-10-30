# -*- coding: utf-8 -*-
"""Lấy ví dụ thật từ 3 lô T455 để giải thích cho Admin."""
import csv, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
D = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-28-t455")

for lot in ["A", "B", "C"]:
    p = os.path.join(D, "name_vi_mismatch_%s.csv" % lot)
    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print("=" * 78)
    print("LÔ %s — %d dòng" % (lot, len(rows)))
    print("=" * 78)
    # sắp theo so_lan giảm dần (người xuất hiện nhiều nhất trong kinh lục)
    rows.sort(key=lambda r: -int(r.get("so_lan") or 0))
    for r in rows[:8]:
        print("  %-9s Hán=%-8s ZQ=%-22s Cloud=%-22s x%s" % (
            r["person_id"], r["name_zh_catalog"][:8], r["name_vi_db_ZQ"][:22],
            r["name_vi_cloud"][:22], r["so_lan"]))
    # đếm có chữ Hán sót
    han = sum(1 for r in rows if any(0x4E00 <= ord(c) <= 0x9FFF for c in r["name_vi_db_ZQ"]))
    print("  >> còn sót chữ Hán trong name_vi: %d/%d" % (han, len(rows)))
    print()
