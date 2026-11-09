#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check T454 place name data"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# Check the 8 places - first check actual columns
cursor.execute('PRAGMA table_info(namevi_map_places)')
cols = cursor.fetchall()
print('=== Table columns ===')
for col in cols:
    print(f'  {col[1]}')  # col[1] is the name

# Check the 8 places
places = [
    'PL000000042180', 'PL000000013217', 'PL000000042305',
    'PL000000055653', 'PL000000042255'
]

print('\n=== Checking namevi_map_places for the 8 places ===')
# Use the actual column name from the table info
name_col = cols[2][1] if len(cols) > 2 else 'name_vi'  # fallback
id_col = cols[0][1] if cols else 'place_id'  # fallback

for pid in places:
    cursor.execute(f'SELECT {id_col}, {name_col}, dila_id FROM namevi_map_places WHERE {id_col} = ?', (pid,))
    row = cursor.fetchone()
    if row:
        print(f'{row[0]}: name_vi="{row[1]}", dila_id={row[2]}')
    else:
        print(f'{pid}: NOT FOUND')

# Check how many total rows with _ in name_vi
cursor.execute(f'SELECT COUNT(*) FROM namevi_map_places WHERE instr({name_col}, "_")>0')
count = cursor.fetchone()[0]
print(f'\nTotal rows with "_" in {name_col}: {count}')

conn.close()