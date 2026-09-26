#!/usr/bin/env python3
"""Revert old T79 events from vn_person_events."""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("DELETE FROM vn_person_events WHERE source = 'dila_person_regex'")
print(f'Deleted {c.rowcount} old T79 events')
conn.commit()

c.execute('SELECT COUNT(*) FROM vn_person_events')
print(f'Remaining: {c.fetchone()[0]} events')

c.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source")
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')
conn.close()
