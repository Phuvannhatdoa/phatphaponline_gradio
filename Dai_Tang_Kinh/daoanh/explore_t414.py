#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Explore T414 data structures"""
import sqlite3
import json
import os

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# Check the tables related to transmission
print('=== Tables ===')
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(f'  {t[0]}')

# Check lineage_primary_teacher
print('\n=== lineage_primary_teacher sample ===')
cursor.execute('SELECT * FROM lineage_primary_teacher LIMIT 5')
rows = cursor.fetchall()
col_names = [desc[0] for desc in cursor.description]
print(f'Columns: {col_names}')
for row in rows:
    print(f'  {row}')

# Check Marcus subtype
print('\n=== Marcus subtype check ===')
cursor.execute('SELECT COUNT(*) FROM marcus WHERE marcus_subtype = ?', ('dharma_transmission',))
count = cursor.fetchone()[0]
print(f'Marcus dharma_transmission: {count}')

cursor.execute('SELECT marcus_subtype, COUNT(*) FROM marcus GROUP BY marcus_subtype')
rows = cursor.fetchall()
for row in rows:
    print(f'  {row[0]}: {row[1]}')

# Check for TTL-related tables
print('\n=== Tables with "lineage" or "teacher" ===')
for table in tables:
    tname = table[0]
    if 'lineage' in tname.lower() or 'teacher' in tname.lower() or 'transmission' in tname.lower():
        print(f'  {tname}')

# Check marcus table structure
print('\n=== marcus table columns ===')
cursor.execute('PRAGMA table_info(marcus)')
cols = cursor.fetchall()
for col in cols:
    print(f'  {col[1]} ({col[2]})')

# Check if there's a relation_kind column anywhere
print('\n=== Searching for relation_kind ===')
for table in [t[0] for t in tables]:
    try:
        cursor.execute(f'PRAGMA table_info({table})')
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        if 'relation_kind' in col_names:
            print(f'  {table} has relation_kind column')
    except:
        pass

conn.close()
print('\n=== Exploration complete ===')
PYEOF