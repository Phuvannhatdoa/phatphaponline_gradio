# -*- coding: utf-8 -*-
"""T455 — cấu trúc entity_claims NAME (source_id=5) cho 1 person + kiểm tra 24 dòng lô A."""
import os, sqlite3, sys, csv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
D = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-28-t455")
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)

print("=== entity_claims NAME cho A000095 / A010057 ===")
for pid in ["A000095", "A010057", "A001301"]:
    rows = conn.execute(
        "SELECT claim_id, entity_id, source_id, claim_type, subject, predicate, object_text, source_record_id "
        "FROM entity_claims WHERE entity_id = ? AND claim_type = 'NAME'", (pid,)).fetchall()
    print("  %s -> %d claim NAME" % (pid, len(rows)))
    for r in rows:
        print("      src=%s obj=%r pred=%r rec=%r" % (r[2], r[6], r[5], r[7]))

print()
print("=== 24 dòng lô A: name_zh DB vs catalog vs ZQ vs Cloud ===")
with open(os.path.join(D, "name_vi_mismatch_A.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
rows.sort(key=lambda r: -int(r.get("so_lan") or 0))
for r in rows:
    db = conn.execute("SELECT name_zh, name_vi FROM people WHERE id = ?", (r["person_id"],)).fetchone()
    han_zq = any(0x4E00 <= ord(c) <= 0x9FFF for c in r["name_vi_db_ZQ"])
    print("  %-9s so=%-4s cat=%-12s db_zh=%-12s ZQ=%-18s Cloud=%-18s %s" % (
        r["person_id"], r["so_lan"], r["name_zh_catalog"][:12],
        (db[0] or "")[:12], r["name_vi_db_ZQ"][:18], r["name_vi_cloud"][:18],
        "HAN" if han_zq else ""))
conn.close()
