#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T473 Step 4: Cross-reference with era_year_jdn
"""

import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_FILE = r'data\lineage.db'

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check era_year_jdn structure
print("=== era_year_jdn structure ===")
cursor.execute("PRAGMA table_info(era_year_jdn)")
for row in cursor.fetchall():
    print("  {}: {} {}".format(row['name'], row['type'], 'NOT NULL' if row['notnull'] else ''))

print("\n=== era_year_jdn sample (first 20) ===")
cursor.execute("SELECT * FROM era_year_jdn ORDER BY jdn LIMIT 20")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== era_year_jdn count ===")
cursor.execute("SELECT COUNT(*) FROM era_year_jdn")
print("  Total rows: {}".format(cursor.fetchone()[0]))

# Check if era_year_jdn has era_id or era_name
print("\n=== Columns in era_year_jdn ===")
cursor.execute("PRAGMA table_info(era_year_jdn)")
cols = [row['name'] for row in cursor.fetchall()]
print(cols)

# Cross-reference: get era_id, era_name, and first/last for year 1 of each era
print("\n=== Cross-reference: era first month JDN vs era_year_jdn ===")
cursor.execute("""
    SELECT 
        e.id as era_id,
        n.name as era_name,
        m.year,
        m.month,
        m.first as t_month_first,
        m.last as t_month_last
    FROM ddbc_t_month m
    JOIN ddbc_t_era e ON m.era_id = e.id
    JOIN ddbc_t_era_names n ON e.id = n.era_id
    WHERE n.language_id = 1 AND n.ranking = 0
    AND m.year = 1 AND m.month = 1 AND m.leap_month = 0
    ORDER BY m.first
    LIMIT 30
""")
rows = cursor.fetchall()
for row in rows:
    print("  era_id={}, name={}, first={}, last={}".format(row['era_id'], row['era_name'], row['t_month_first'], row['t_month_last']))

# Now check era_year_jdn for matching eras
print("\n=== Checking era_year_jdn for matching era names ===")
cursor.execute("""
    SELECT DISTINCT era_name FROM era_year_jdn ORDER BY era_name
""")
rows = cursor.fetchall()
print("Total distinct era_names in era_year_jdn: {}".format(len(rows)))
for row in rows[:30]:
    print("  {}".format(row['era_name']))

# Check if we can match by name
print("\n=== Matching era names between ddbc_t_era_names (Chinese) and era_year_jdn ===")
cursor.execute("""
    SELECT 
        e.id as ddbc_era_id,
        n.name as ddbc_era_name,
        m.first as t_month_first_year1_month1
    FROM ddbc_t_era e
    JOIN ddbc_t_era_names n ON e.id = n.era_id
    JOIN ddbc_t_month m ON e.id = m.era_id
    WHERE n.language_id = 1 AND n.ranking = 0
    AND m.year = 1 AND m.month = 1 AND m.leap_month = 0
""")
ddbc_eras = {row['ddbc_era_name']: (row['ddbc_era_id'], row['t_month_first_year1_month1']) for row in cursor.fetchall()}

cursor.execute("SELECT DISTINCT era_name, MIN(jdn) as min_jdn FROM era_year_jdn GROUP BY era_name")
eyj_eras = {row['era_name']: row['min_jdn'] for row in cursor.fetchall()}

matched = 0
only_ddbc = 0
only_eyj = 0
discrepancies = []

for name, (eid, first) in ddbc_eras.items():
    if name in eyj_eras:
        matched += 1
        eyj_jdn = eyj_eras[name]
        diff = eyj_jdn - first
        if abs(diff) > 50:  # More than 50 days difference
            discrepancies.append((name, eid, first, eyj_jdn, diff))
    else:
        only_ddbc += 1

for name, jdn in eyj_eras.items():
    if name not in ddbc_eras:
        only_eyj += 1

print("Matched era names: {}".format(matched))
print("Only in ddbc: {}".format(only_ddbc))
print("Only in era_year_jdn: {}".format(only_eyj))

if discrepancies:
    print("\nDiscrepancies (>50 days):")
    for name, eid, first, eyj_jdn, diff in discrepancies[:20]:
        print("  {}: ddbc_first={}, eyj_jdn={}, diff={} days".format(name, first, eyj_jdn, diff))

# Show some matched ones with small differences
print("\nSample matched (small diff):")
count = 0
for name, (eid, first) in ddbc_eras.items():
    if name in eyj_eras:
        eyj_jdn = eyj_eras[name]
        diff = eyj_jdn - first
        if abs(diff) <= 50:
            print("  {}: ddbc_first={}, eyj_jdn={}, diff={}".format(name, first, eyj_jdn, diff))
            count += 1
            if count >= 10:
                break

conn.close()