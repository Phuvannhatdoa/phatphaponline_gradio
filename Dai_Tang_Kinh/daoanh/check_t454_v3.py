#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check T454 place name data v3"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# Get actual column names
cols = cursor.execute('PRAGMA table_info(namevi_map_places)').fetchall()
col_names = [c[1] for c in cols]
print('Table columns:', col_names)

id_col = col_names[0]  # 'namevi_map_places'.id
name_col = col_names[1]  # 'namevi_map_places'.name_vi

# The key finding: note_vi column EXISTS at index 8
note_col = col_names[8]  # 'namevi_map_places'.note_vi
print(f'\nKey column: note_vi = {note_col}')

# Search for the exact examples from the task description
print('\n=== Searching for task examples in note_vi ===')
samples = [
    'Chương Tín Tự _ Huý',
    'Giác Trí Tự _ Ngoa', 
    'Hoằng Phúc Tự _ Huý',
    'Nguyên Bí Tháp _ Huý',
    'Nguyên Pháp Tự _ Huý'
]

for sample in samples:
    cursor.execute(f'SELECT {id_col}, {name_col}, {note_col} FROM namevi_map_places WHERE {note_col} = ?', (sample,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f'  Found: {row[0]}: name_vi="{row[1]}", note_vi="{row[2]}"')
    else:
        print(f'  {sample}: NOT FOUND in note_vi')

# Search for ANY rows with _Hu or _Ngoa in note_vi
print('\n=== ANY rows with _Hu or _Ngoa in note_vi ===')
cursor.execute(f"SELECT {id_col}, {name_col}, {note_col} FROM namevi_map_places WHERE {note_col} LIKE '%Hu%' OR {note_col} LIKE '%Ngoa%'")
rows = cursor.fetchall()
print(f'Found {len(rows)} rows:')
for row in rows:
    print(f'  {row[0]}: name_vi="{row[1]}", note_vi="{row[2]}"')

# Also check name_vi column
print('\n=== Search in name_vi column ===')
cursor.execute(f"SELECT {id_col}, {name_col}, {note_col} FROM namevi_map_places WHERE {name_col} LIKE '%Hu%' OR {name_col} LIKE '%Ngoa%'")
rows = cursor.fetchall()
print(f'Found {len(rows)} rows in name_vi:')
for row in rows:
    print(f'  {row[0]}: name_vi="{row[1]}", note_vi="{row[2]}"')

conn.close()