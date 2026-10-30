# -*- coding: utf-8 -*-
"""T455 — probe nguồn tên Việt (entity_claims.source_id) + FTS cần rebuild sau khi đổi name_vi."""
import os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]

print("=== bảng có 'claim' hoặc 'source' ===")
for t in tables:
    if "claim" in t.lower() or "source" in t.lower():
        cols = [c[1] for c in conn.execute("PRAGMA table_info(%s)" % t)]
        try:
            n = conn.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        except Exception:
            n = "?"
        print("   %-32s rows=%-9s cols=%s" % (t, n, cols[:10]))

print()
if "entity_claims" in tables:
    print("=== entity_claims: source_id + claim_type ===")
    for r in conn.execute(
        "SELECT claim_type, source_id, COUNT(*) FROM entity_claims GROUP BY 1,2 ORDER BY 3 DESC LIMIT 14"):
        print("   %-26s source_id=%-4s %s" % (r[0], r[1], r[2]))

print()
print("=== FTS / bảng search liên quan people ===")
for t in tables:
    if "fts" in t.lower() or "search" in t.lower():
        cols = [c[1] for c in conn.execute("PRAGMA table_info(%s)" % t)]
        print("   %-34s cols=%s" % (t, cols[:9]))

print()
print("=== people: name_zh Hán vs Latin (A000095) + 3 dòng lô A ===")
for pid in ["A000095", "A010057", "A001310"]:
    r = conn.execute("SELECT id, name_zh, name_vi, source_origin, source_id FROM people WHERE id = ?", (pid,)).fetchone()
    print("   ", r)
conn.close()
