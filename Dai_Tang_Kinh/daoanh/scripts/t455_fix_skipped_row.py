# -*- coding: utf-8 -*-
"""T455 — sửa dòng lịch sử của A001428 (bị bỏ qua khi UPDATE) cho đúng thực tế.

UPDATE dùng điều kiện `AND name_vi = <CSV>` nên A001428 không bị ghi đè
(DB đang là 'Di Lặc Bồ Tát' — đúng chính tả + đủ 'Bồ Tát'; Cloud 'Di Lặc' làm mất tôn kính).
Sửa lịch sử: action='skipped_kept', name_vi_new = giá trị thực tế trong DB.
"""
import os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
BATCH = "T455-planA-20261030"

conn = sqlite3.connect(DB)
row = conn.execute(
    "SELECT id, name_vi_old, name_vi_new FROM people_name_vi_history "
    "WHERE batch_id = ? AND person_id = 'A001428'", (BATCH,)).fetchone()
print("lịch sử trước:", row)
cur = conn.execute("SELECT name_vi FROM people WHERE id = 'A001428'").fetchone()
print("DB hiện tại  :", cur)
if row and cur and row[2] != cur[0]:
    conn.execute(
        "UPDATE people_name_vi_history SET name_vi_new = ?, action = 'skipped_kept', "
        "reason = 'DB da doi sau khi do CSV (khac dau) va gia tri hien tai tot hon Cloud - giu nguyen, khong ghi de' "
        "WHERE id = ?", (cur[0], row[0]))
    conn.commit()
    print("→ đã cập nhật lịch sử")
print("lịch sử sau  :", conn.execute(
    "SELECT id, name_vi_old, name_vi_new, action FROM people_name_vi_history "
    "WHERE batch_id = ? AND person_id = 'A001428'", (BATCH,)).fetchone())
print()
print("theo action sau khi sửa:", conn.execute(
    "SELECT action, COUNT(*) FROM people_name_vi_history WHERE batch_id = ? GROUP BY 1",
    (BATCH,)).fetchall())
conn.close()
