#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check lineage_edge_assertions structure"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# Check lineage_edge_assertions
cursor.execute("PRAGMA table_info(lineage_edge_assertions)")
cols = cursor.fetchall()
print('lineage_edge_assertions columns:', [c[1] for c in cols])

# Check sample rows
cursor.execute('SELECT * FROM lineage_edge_assertions LIMIT 3')
rows = cursor.fetchall()
print('Sample rows:', rows)

# Check v_tree_dila
cursor.execute("PRAGMA table_info(v_tree_dila)")
cols = cursor.fetchall()
print('v_tree_dila columns:', [c[1] for c in cols])

cursor.execute('SELECT * FROM v_tree_dila LIMIT 3')
rows = cursor.fetchall()
print('v_tree_dila sample rows:', rows)

conn.close()