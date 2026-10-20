# -*- coding: utf-8 -*-
import sqlite3, os, glob
DB = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db"
c = sqlite3.connect(DB).cursor()
print("rows ds:", c.execute("SELECT COUNT(*) FROM data_sources").fetchone()[0])
print("sample:", c.execute("SELECT source_code, IFNULL(canonical_name,'NULL'), IFNULL(short_name,'NULL') FROM data_sources LIMIT 5").fetchall())
print("claims lic/usage non-null:", c.execute("SELECT COUNT(*) FROM entity_claims WHERE license IS NOT NULL OR usage_level IS NOT NULL").fetchone()[0])
cp = c.execute("PRAGMA table_info(conflict_pending)").fetchall()
print("conflict_pending cols:", [r[1] for r in cp])
print("conflict_pending needs_review:", c.execute("SELECT COUNT(*) FROM conflict_pending WHERE needs_review=1").fetchone()[0])
