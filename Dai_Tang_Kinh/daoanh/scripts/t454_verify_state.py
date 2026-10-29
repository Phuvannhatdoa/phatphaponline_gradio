# -*- coding: utf-8 -*-
import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
print("=== LIKE co '_' wildcard (false positive) ===")
rows = conn.execute(
    "SELECT id, dila_id, name_vi, note_vi FROM namevi_map_places "
    "WHERE name_vi LIKE '%_ Huý%' OR name_vi LIKE '%_ Ngoa%'"
).fetchall()
for r in rows:
    print(r)
print()
print("=== LIKE voi ESCAPE (dung) ===")
rows2 = conn.execute(
    "SELECT id, dila_id, name_vi, note_vi FROM namevi_map_places "
    "WHERE name_vi LIKE '%\\_ Huý%' ESCAPE '\\' OR name_vi LIKE '%\\_ Ngoa%' ESCAPE '\\'"
).fetchall()
print("so dong con suffix that:", len(rows2))
for r in rows2:
    print(r)
conn.close()
