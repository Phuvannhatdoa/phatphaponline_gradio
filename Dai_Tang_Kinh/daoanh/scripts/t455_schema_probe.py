# -*- coding: utf-8 -*-
"""Khảo sát schema `people` + các bảng lịch sử tên, để chuẩn bị T455 phương án A."""
import os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)

print("=== people: cột liên quan tên ===")
for r in conn.execute("PRAGMA table_info(people)"):
    n, t = r[1], r[2]
    if any(k in n.lower() for k in ["name", "source", "vn_", "review", "status"]):
        print("   %-24s %-14s null=%s default=%s" % (n, t, r[3], r[4]))

print()
print("=== bảng lịch sử tên đã có ===")
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
for t in tables:
    if "history" in t.lower() or "alias" in t.lower():
        try:
            n = conn.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        except Exception:
            n = "?"
        cols = [c[1] for c in conn.execute("PRAGMA table_info(%s)" % t)]
        print("   %-34s rows=%-8s cols=%s" % (t, n, cols[:9]))

print()
print("=== people_name_vi_history tồn tại? ===")
print("   ", "people_name_vi_history" in tables)

print()
print("=== vài dòng people mẫu (có name_vi khác lô) ===")
for pid in ["A000095", "A001301", "A001482"]:
    r = conn.execute(
        "SELECT id, dila_id, name_zh, name_vi FROM people WHERE dila_id = ? OR id = ? LIMIT 1",
        (pid, pid)).fetchone()
    print("   ", r)

print()
print("=== tổng số people có name_vi ===")
print("   ", conn.execute("SELECT COUNT(*) FROM people WHERE name_vi IS NOT NULL AND name_vi <> ''").fetchone()[0])
print("=== số people còn Hán trong name_vi ===")
han = 0
for (nv,) in conn.execute("SELECT name_vi FROM people WHERE name_vi IS NOT NULL"):
    if any(0x4E00 <= ord(c) <= 0x9FFF for c in nv):
        han += 1
print("   ", han)
conn.close()
