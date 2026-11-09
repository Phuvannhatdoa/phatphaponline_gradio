#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check marcus_networks structure"""
import sqlite3

conn = sqlite3.connect('data/lineage.db')
cursor = conn.cursor()

# Check marcus_networks
cursor.execute("PRAGMA table_info(marcus_networks)")
cols = cursor.fetchall()
print('marcus_networks columns:', [c[1] for c in cols])

# Check lineage_primary_teacher
cursor.execute("PRAGMA table_info(lineage_primary_teacher)")
cols = cursor.fetchall()
print('lineage_primary_teacher columns:', [c[1] for c in cols])

# Check what tables have relation_kind
cursor.execute("SELECT name FROM sqlite_master WHERE sql LIKE '%relation_kind%'")
tables = cursor.fetchall()
print('Tables with relation_kind:', tables)

conn.close()