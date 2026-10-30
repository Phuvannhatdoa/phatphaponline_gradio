# -*- coding: utf-8 -*-
"""Khảo sát schema `people` (cột id/dila) + bảng lịch sử tên."""
import os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)

cols = [(r[1], r[2]) for r in conn.execute("PRAGMA table_info(people)")]
print("people columns (%d):" % len(cols))
print("  ", ", ".join(c[0] for c in cols))
print()
idcols = [c[0] for c in cols if c[0].lower() in ("id", "dila_id", "person_id")]
print("cột định danh:", idcols)

print()
for pid in ["A000095", "A001301", "A001482"]:
    for ic in idcols:
        try:
            r = conn.execute(
                "SELECT id, name_zh, name_vi, source_id FROM people WHERE %s = ?" % ic,
                (pid,)).fetchone()
        except Exception as e:
            print("   ERR", ic, e); continue
        if r:
            print("   [%s] %s | zh=%s | vi=%s | source_id=%s" % (ic, pid, r[1], r[2], r[3]))
            break

print()
print("=== source_id distribution cho name_vi (top) ===")
for r in conn.execute(
    "SELECT source_id, COUNT(*) FROM people WHERE name_vi IS NOT NULL GROUP BY source_id ORDER BY 2 DESC LIMIT 8"):
    print("   source_id=%s : %s" % (r[0], r[1]))

n_han = 0
for (nv,) in conn.execute("SELECT name_vi FROM people WHERE name_vi IS NOT NULL"):
    if any(0x4E00 <= ord(c) <= 0x9FFF for c in nv):
        n_han += 1
print()
print("people còn Hán trong name_vi:", n_han)
print("people có name_vi:", conn.execute(
    "SELECT COUNT(*) FROM people WHERE name_vi IS NOT NULL AND name_vi <> ''").fetchone()[0])
conn.close()
