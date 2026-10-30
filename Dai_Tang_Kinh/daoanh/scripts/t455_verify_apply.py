# -*- coding: utf-8 -*-
"""T455 — verify sau apply (phương án A)."""
import os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
BATCH = "T455-planA-20261030"

conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)

print("=== 1. bảng lịch sử ===")
for r in conn.execute("PRAGMA table_info(people_name_vi_history)"):
    print("   %-14s %s" % (r[1], r[2]))
print("   tổng dòng lịch sử:", conn.execute("SELECT COUNT(*) FROM people_name_vi_history").fetchone()[0])
print("   của batch này     :", conn.execute(
    "SELECT COUNT(*) FROM people_name_vi_history WHERE batch_id = ?", (BATCH,)).fetchone()[0])
print("   theo action       :", conn.execute(
    "SELECT action, COUNT(*) FROM people_name_vi_history WHERE batch_id = ? GROUP BY 1",
    (BATCH,)).fetchall())
print("   theo lot          :", conn.execute(
    "SELECT lot, COUNT(*) FROM people_name_vi_history WHERE batch_id = ? GROUP BY 1",
    (BATCH,)).fetchall())

print()
print("=== 2. people.name_vi còn chữ Hán ===")
han = []
for pid, nv in conn.execute("SELECT id, name_vi FROM people WHERE name_vi IS NOT NULL"):
    if any(0x4E00 <= ord(c) <= 0x9FFF for c in nv):
        han.append((pid, nv))
print("   còn Hán:", len(han), "(trước apply: 422)")
in_batch = [h for h in han if conn.execute(
    "SELECT COUNT(*) FROM people_name_vi_history WHERE person_id = ? AND batch_id = ?",
    (h[0], BATCH)).fetchone()[0]]
print("   trong số đó thuộc batch này (chưa sửa được):", len(in_batch))
for p, n in in_batch[:6]:
    print("      %s  %r" % (p, n))

print()
print("=== 3. people.name_zh KHÔNG đổi ===")
print("   name_zh NULL:", conn.execute("SELECT COUNT(*) FROM people WHERE name_zh IS NULL").fetchone()[0])
print("   tổng people :", conn.execute("SELECT COUNT(*) FROM people").fetchone()[0])

print()
print("=== 4. source_id không đổi ===")
print("   ", conn.execute(
    "SELECT source_id, COUNT(*) FROM people GROUP BY source_id ORDER BY 2 DESC LIMIT 5").fetchall())

print()
print("=== 5. 8 dòng mẫu sau apply ===")
for r in conn.execute(
        "SELECT person_id, name_vi_old, name_vi_new, lot, action FROM people_name_vi_history "
        "WHERE batch_id = ? AND action = 'updated' ORDER BY id LIMIT 8", (BATCH,)):
    print("   %-9s %-22s -> %-22s lô %s" % (r[0], r[1][:22], r[2][:22], r[3]))

print()
print("=== 6. đối chiếu: name_vi DB khớp name_vi_new trong lịch sử? ===")
bad = conn.execute(
    "SELECT COUNT(*) FROM people_name_vi_history h JOIN people p ON p.id = h.person_id "
    "WHERE h.batch_id = ? AND h.action = 'updated' AND p.name_vi <> h.name_vi_new", (BATCH,)).fetchone()[0]
print("   số dòng lệch:", bad, "(0 = đúng)")

print()
print("=== 7. lô B: đã ghi chú alias, name_vi KHÔNG đổi ===")
b_chg = conn.execute(
    "SELECT COUNT(*) FROM people_name_vi_history h JOIN people p ON p.id = h.person_id "
    "WHERE h.batch_id = ? AND h.lot = 'B' AND p.name_vi <> h.name_vi_old", (BATCH,)).fetchone()[0]
print("   số dòng lô B bị đổi (phải = 0):", b_chg)
conn.close()
