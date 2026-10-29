# -*- coding: utf-8 -*-
import sqlite3, os, datetime
DB = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data/lineage.db"
conn = sqlite3.connect(DB, uri=True)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", [t for t in tables if 't457' in t or 'nexus' in t.lower() or 'bio' in t.lower()])
cnt = conn.execute("SELECT COUNT(*) FROM dila_bio_nexus").fetchone()[0]
print("dila_bio_nexus rows:", cnt)
print("book groups:", conn.execute("SELECT book, COUNT(*) FROM dila_bio_nexus GROUP BY book").fetchall())
print("with_year:", conn.execute("SELECT COUNT(*) FROM dila_bio_nexus WHERE year_from IS NOT NULL").fetchone()[0])
print("link person count:", conn.execute("SELECT COUNT(*) FROM dila_bio_nexus_person").fetchone()[0])
print("link place count:", conn.execute("SELECT COUNT(*) FROM dila_bio_nexus_place").fetchone()[0])
conn.close()

# Ghi ROLLBACK
ROLLBACK = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs/ROLLBACK.md"
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(ROLLBACK, "a", encoding="utf-8") as f:
    f.write(f"\n### T457 — import DILA bio nexus (2026-10-29)\n")
    f.write(f"- Apply: INSERT INTO dila_bio_nexus (+ link tables dila_bio_nexus_person/place) từ staging_v4\n")
    f.write(f"- Revert: DROP TABLE dila_bio_nexus (+ link + indexes)\n")
    f.write(f"- Backup: E:\\Backup 2025\\QuaiTieuTu\\Anan Son\\phatphaponline_gradio\\truyenthua\\visjs-app\\Dai_Tang_Kinh\\daoanh\\data\\backups\\lineage_t457_20261029_094901.db\n")
print("ROLLBACK ghi chú xong")
