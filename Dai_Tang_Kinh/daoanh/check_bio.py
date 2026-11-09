#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check person_bio_vi_draft structure"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(person_bio_vi_draft)")
cols = cursor.fetchall()
print('person_bio_vi_draft columns:', [c[1] for c in cols])

cursor.execute('SELECT * FROM person_bio_vi_draft LIMIT 2')
rows = cursor.fetchall()
print('Sample rows:', rows)

cursor.execute("SELECT * FROM person_bio_vi_draft WHERE person_id LIKE '%A009460%' LIMIT 1")
rows = cursor.fetchall()
print('A009460 sample:', rows)

conn.close()
PYEOF