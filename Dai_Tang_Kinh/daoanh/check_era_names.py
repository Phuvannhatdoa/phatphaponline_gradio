#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T473 Step 3: Check era names to identify era_id 27 and 730
"""

import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_FILE = r'data\lineage.db'

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check era 27
print("=== Era 27 ===")
cursor.execute("SELECT * FROM ddbc_t_era WHERE id = 27")
row = cursor.fetchone()
if row:
    print(dict(row))

cursor.execute("SELECT * FROM ddbc_t_era_names WHERE era_id = 27")
rows = cursor.fetchall()
for row in rows:
    print("  name: {}, lang: {}, ranking: {}".format(row['name'], row['language_id'], row['ranking']))

# Check era 730
print("\n=== Era 730 ===")
cursor.execute("SELECT * FROM ddbc_t_era WHERE id = 730")
row = cursor.fetchone()
if row:
    print(dict(row))

cursor.execute("SELECT * FROM ddbc_t_era_names WHERE era_id = 730")
rows = cursor.fetchall()
for row in rows:
    print("  name: {}, lang: {}, ranking: {}".format(row['name'], row['language_id'], row['ranking']))

# Check era 1
print("\n=== Era 1 ===")
cursor.execute("SELECT * FROM ddbc_t_era WHERE id = 1")
row = cursor.fetchone()
if row:
    print(dict(row))

cursor.execute("SELECT * FROM ddbc_t_era_names WHERE era_id = 1")
rows = cursor.fetchall()
for row in rows:
    print("  name: {}, lang: {}, ranking: {}".format(row['name'], row['language_id'], row['ranking']))

# Find Thành Hóa (成化)
print("\n=== Search for Thanh Hoa (成化) ===")
cursor.execute("""
    SELECT e.id, e.emperor_id, n.name, n.language_id, n.ranking
    FROM ddbc_t_era e
    JOIN ddbc_t_era_names n ON e.id = n.era_id
    WHERE n.name LIKE '%成化%' OR n.name LIKE '%Thanh Hoa%' OR n.name LIKE '%thanh hoa%'
""")
rows = cursor.fetchall()
for row in rows:
    print("  era_id={}, emperor_id={}, name={}, lang={}, ranking={}".format(row['id'], row['emperor_id'], row['name'], row['language_id'], row['ranking']))

# Find Kiến Vũ (建武)
print("\n=== Search for Kien Vu (建武) ===")
cursor.execute("""
    SELECT e.id, e.emperor_id, n.name, n.language_id, n.ranking
    FROM ddbc_t_era e
    JOIN ddbc_t_era_names n ON e.id = n.era_id
    WHERE n.name LIKE '%建武%' OR n.name LIKE '%Kien Vu%'
""")
rows = cursor.fetchall()
for row in rows:
    print("  era_id={}, emperor_id={}, name={}, lang={}, ranking={}".format(row['id'], row['emperor_id'], row['name'], row['language_id'], row['ranking']))

# Check all Chinese eras (language_id=1)
print("\n=== All Chinese eras (language_id=1) with ranking=0 ===")
cursor.execute("""
    SELECT e.id, e.emperor_id, n.name
    FROM ddbc_t_era e
    JOIN ddbc_t_era_names n ON e.id = n.era_id
    WHERE n.language_id = 1 AND n.ranking = 0
    ORDER BY e.id
""")
rows = cursor.fetchall()
for row in rows[:50]:
    print("  era_id={}, emperor_id={}, name={}".format(row['id'], row['emperor_id'], row['name']))
print("  ... ({} total)".format(len(rows)))

conn.close()