# -*- coding: utf-8 -*-
import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
print("DB exists:", os.path.exists(DB), os.path.getsize(DB) if os.path.exists(DB) else 0)
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
n = conn.execute(
    "SELECT COUNT(*) FROM namevi_map_places WHERE name_vi LIKE '%_ Huý%' OR name_vi LIKE '%_ Ngoa%'"
).fetchone()[0]
print("T454 con suffix rows:", n)
print("T457 dila_bio_nexus:", conn.execute("SELECT COUNT(*) FROM dila_bio_nexus").fetchone()[0])
print("T457 person link:", conn.execute("SELECT COUNT(*) FROM dila_bio_nexus_person").fetchone()[0])
print("T457 place link:", conn.execute("SELECT COUNT(*) FROM dila_bio_nexus_place").fetchone()[0])
conn.close()

tasks = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "tasks")
for f in sorted(os.listdir(tasks)):
    if f.startswith(("T45", "T46")):
        print("TASK:", f, os.path.getsize(os.path.join(tasks, f)))
