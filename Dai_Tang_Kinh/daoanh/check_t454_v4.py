#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check T454 place name data v4 - simplified"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# The key finding: note_vi column EXISTS
print('Key column: note_vi exists')

# Search for ANY rows with _Hu or _Ngoa in note_vi
print('\n=== ANY rows with _Hu or _Ngoa in note_vi ===')
cursor.execute("SELECT id, note_vi FROM namevi_map_places WHERE note_vi LIKE '%Hu%' OR note_vi LIKE '%Ngoa%'")
rows = cursor.fetchall()
print(f'Found {len(rows)} rows:')
for row in rows:
    print(f'  id={row[0]}: note_vi="{row[1]}"')

# Show a few sample rows from the full table to understand the data
print('\n=== Sample rows (first 10) ===')
cursor.execute('SELECT id, note_vi FROM namevi_map_places LIMIT 10')
rows = cursor.fetchall()
for row in rows:
    print(f'  id={row[0]}: note_vi="{row[1]}"')

# Check how many total have _ in note_vi
cursor.execute('SELECT COUNT(*) FROM namevi_map_places WHERE note_vi LIKE "%_%"')
count = cursor.fetchone()[0]
print(f'\nTotal rows with _ in note_vi: {count}')

# Check the specific 8 places from the task by searching name_vi
print('\n=== Search name_vi for the 8 examples ===')
# The task mentions these names exist somewhere
sample_names = [
    'Hoằng Phúc Tự _ Huý',
    'Chương Tín Tự _ Huý',
    'Giác Trí Tự _ Ngoa'
]
for name in sample_names:
    # Try searching in name_vi
    cursor.execute("SELECT id, name_vi, note_vi FROM namevi_map_places WHERE name_vi LIKE ?", (f'%{name}%',))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f'  Found: id={row[0]}: name_vi="{row[1]}", note_vi="{row[2]}"')
    else:
        print(f'  "{name}": NOT FOUND')

conn.close()