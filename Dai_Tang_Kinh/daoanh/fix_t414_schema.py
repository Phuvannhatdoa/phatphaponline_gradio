#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix T414 schema - add relation_kind column"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# Add relation_kind column to lineage_primary_teacher
try:
    cursor.execute('ALTER TABLE lineage_primary_teacher ADD COLUMN relation_kind TEXT')
    print('Added relation_kind column to lineage_primary_teacher')
    conn.commit()
except Exception as e:
    print('Column may already exist or error: ' + str(e))

# Check the column
cursor.execute('PRAGMA table_info(lineage_primary_teacher)')
cols = [c[1] for c in cursor.fetchall()]
print('lineage_primary_teacher columns:', cols)
print('relation_kind in columns: ' + str('relation_kind' in cols))

conn.close()
print('Schema fix complete')