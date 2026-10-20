#!/usr/bin/env python3
"""Verify T79 apply results in vn_person_events."""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM vn_person_events')
print('Total vn_person_events:', c.fetchone()[0])

c.execute('SELECT source, COUNT(*) FROM vn_person_events GROUP BY source')
for r in c.fetchall():
    print(f'  source={r[0]}: {r[1]}')

c.execute("SELECT event_type, COUNT(*) FROM vn_person_events WHERE source='dila_person_regex' GROUP BY event_type")
print('dila_person_regex by type:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

c.execute("SELECT MIN(event_year), MAX(event_year), COUNT(DISTINCT person_id) FROM vn_person_events WHERE source='dila_person_regex'")
print('T79 year range / distinct persons:', c.fetchone())

print('\nSample T79 events:')
c.execute("SELECT person_id, event_type, event_year, confidence FROM vn_person_events WHERE source='dila_person_regex' LIMIT 8")
for r in c.fetchall():
    print(' ', r)
conn.close()
