#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check T454 place name data v2"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# The table has note_vi column - this is key for T454!
print('=== note_vi column EXISTS ===')
print('Column names:', [c[1] for c in cursor.execute('PRAGMA table_info(namevi_map_places)').fetchall()])

# Check the 8 places - use the actual column names from PRAGMA
# The first column is 'id', second is 'name_vi', third is 'name_zh', etc.
id_col = 'id'
name_col = 'name_vi'

# Search by LIKE for "_ Hu" and "_ Ngoa" patterns (note the _ is wildcard in SQL)
print('\n=== Search by LIKE for "_ Hu%" and "%_ Ngoa" ===')
# In SQL, _ is a single character wildcard, so we need to escape it or use different approach
cursor.execute("SELECT place_id, name_vi, note_vi FROM namevi_map_places WHERE name_vi LIKE '%_%' AND (name_vi LIKE '%Hu%' OR name_vi LIKE '%Ngoa%')")
rows = cursor.fetchall()
print(f'Found {len(rows)} rows:')
for row in rows:
    print(f'  {row[0]}: name_vi="{row[1]}", note_vi="{row[3]}"')

# Alternative: search for the exact patterns from the task
print('\n=== Search for exact patterns from task ===')
# The task mentions these exact examples:
# - Chương Tín Tự _ Huý
# - Giác Trí Tự _ Ngoa  
# - Hoằng Phúc Tự _ Huý
# - Nguyên Bí Tháp _ Huý
# - Nguyên Pháp Tự _ Huý

print('\n=== Checking specific examples ===')
samples = [
    'Chương Tín Tự _ Huý',
    'Giác Trí Tự _ Ngoa', 
    'Hoằng Phúc Tự _ Huý',
    'Nguyên Bí Tháp _ Huý',
    'Nguyên Pháp Tự _ Huý'
]
for sample in samples:
    # Escape the special SQL characters
    cursor.execute("SELECT place_id, name_vi, note_vi FROM namevi_map_places WHERE name_vi = ?", (sample,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f'  Found: {row[0]}: name_vi="{row[1]}", note_vi="{row[3]}"')
    else:
        print(f'  {sample}: NOT FOUND exact match')

# Check all rows with _ Hu or _ Ngoa pattern (using the note_vi column which we know exists)
print('\n=== All rows with note_vi containing Hu or Ngoa ===')
cursor.execute("SELECT place_id, name_vi, note_vi FROM namevi_map_places WHERE note_vi LIKE '%Hu%' OR note_vi LIKE '%Ngoa%'")
rows = cursor.fetchall()
print(f'Found {len(rows)} rows:')
for row in rows:
    print(f'  {row[0]}: name_vi="{row[1]}", note_vi="{row[2]}"')

conn.close()