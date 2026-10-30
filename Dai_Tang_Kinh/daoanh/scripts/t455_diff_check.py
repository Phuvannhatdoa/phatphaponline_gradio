# -*- coding: utf-8 -*-
"""T455 — điểm lệch giữa CSV và DB (A001428) + đếm chính xác dòng sẽ bị bỏ qua."""
import csv, os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
PROP = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions",
                    "2026-10-30-t455-apply", "t455_proposal_planA.csv")

conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
with open(PROP, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

skip = []
for r in rows:
    if r["action"] != "updated":
        continue
    db = conn.execute("SELECT name_vi, name_zh FROM people WHERE id = ?", (r["person_id"],)).fetchone()
    if db is None:
        skip.append((r, "KHÔNG có trong people"))
    elif db[0] != r["name_vi_old_ZQ"]:
        skip.append((r, "DB=%r CSV=%r" % (db[0], r["name_vi_old_ZQ"])))

print("=== dòng 'updated' KHÔNG khớp DB (sẽ bị bỏ qua, an toàn) ===")
for r, why in skip:
    print("  lot %s  %-9s  %s" % (r["lot"], r["person_id"], why))
    print("      Hán=%s | đề xuất mới = %s" % (r["name_zh_catalog"], r["name_vi_new"]))
print("tổng:", len(skip), "/", sum(1 for r in rows if r["action"] == "updated"), "dòng updated")

print()
print("=== kiểm tra lịch sử: dòng nào có 'Di Lặc/Di Lắc Bồ Tát' ===")
for r in rows:
    if "Bồ Tát" in r["name_vi_old_ZQ"] and r["lot"] == "C":
        db = conn.execute("SELECT name_vi FROM people WHERE id = ?", (r["person_id"],)).fetchone()
        print("   %s lot=%s ZQ=%r Cloud=%r -> %r | DB=%r" % (
            r["person_id"], r["lot"], r["name_vi_old_ZQ"], r["name_vi_cloud"],
            r["name_vi_new"], db[0] if db else None))
conn.close()
