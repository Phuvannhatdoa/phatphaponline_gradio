#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T473 Step 3: Analyze t_month first/last reference system
"""

import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_FILE = r'data\lineage.db'

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check t_month structure
print("=== t_month structure ===")
cursor.execute("PRAGMA table_info(ddbc_t_month)")
for row in cursor.fetchall():
    print("  {}: {} {}".format(row['name'], row['type'], 'NOT NULL' if row['notnull'] else ''))

# Sample data
print("\n=== Sample t_month data (first 20) ===")
cursor.execute("""
    SELECT id, year, month, month_name, leap_month, era_id, first, last, ganzhi, start_from, status, eclipse
    FROM ddbc_t_month
    ORDER BY id
    LIMIT 20
""")
for row in cursor.fetchall():
    print("  id={}, year={}, month={}, leap={}, era_id={}, first={}, last={}, ganzhi={}, start_from={}, status={}, eclipse={}".format(
        row['id'], row['year'], row['month'], row['leap_month'], row['era_id'], row['first'], row['last'], row['ganzhi'], row['start_from'], row['status'], row['eclipse']))

# Check era 27 (Thành Hóa / 成化) - should be 1465-1487
print("\n=== Era 27 (Thanh Hoa / 成化) - expected 1465-1487 ===")
cursor.execute("""
    SELECT * FROM ddbc_t_month WHERE era_id = 27 ORDER BY year, month
""")
rows = cursor.fetchall()
for row in rows:
    print("  year={}, month={}, leap={}, first={}, last={}, ganzhi={}".format(
        row['year'], row['month'], row['leap_month'], row['first'], row['last'], row['ganzhi']))

# Check era 1 (Kiến Vũ / 建武) - Han dynasty
print("\n=== Era 1 (Kien Vu / 建武) - expected 25-56 AD ===")
cursor.execute("""
    SELECT * FROM ddbc_t_month WHERE era_id = 1 ORDER BY year, month
""")
rows = cursor.fetchall()
for row in rows:
    print("  year={}, month={}, leap={}, first={}, last={}, ganzhi={}".format(
        row['year'], row['month'], row['leap_month'], row['first'], row['last'], row['ganzhi']))

# Check era_id 100
print("\n=== Era 100 ===")
cursor.execute("""
    SELECT * FROM ddbc_t_month WHERE era_id = 100 ORDER BY year, month
""")
rows = cursor.fetchall()
for row in rows[:10]:
    print("  year={}, month={}, leap={}, first={}, last={}, ganzhi={}".format(
        row['year'], row['month'], row['leap_month'], row['first'], row['last'], row['ganzhi']))

# Check min/max first/last
print("\n=== first/last range ===")
cursor.execute("SELECT MIN(first), MAX(first), MIN(last), MAX(last) FROM ddbc_t_month")
min_first, max_first, min_last, max_last = cursor.fetchone()
print("  first: {} to {}".format(min_first, max_first))
print("  last: {} to {}".format(min_last, max_last))

# Check if first/last are JDN (Julian Day Number)
# JDN for 1473-01-01 (Gregorian) = 2255198
# JDN for 1465-01-01 = 2252265
# JDN for 25 AD = 1738291
print("\n=== JDN Reference ===")
print("  JDN for 1465-01-01 (Gregorian): 2252265")
print("  JDN for 1473-01-01 (Gregorian): 2255198")
print("  JDN for 25 AD (Gregorian): 1738291")
print("  JDN for 1 AD (Gregorian): 1721424")

# Check first few rows of era 27
print("\n=== Era 27 detail ===")
cursor.execute("""
    SELECT * FROM ddbc_t_month WHERE era_id = 27 ORDER BY year, month
""")
rows = cursor.fetchall()
for row in rows:
    diff = row['last'] - row['first']
    print("  year={}, month={}, first={}, last={}, diff={}".format(row['year'], row['month'], row['first'], row['last'], diff))

# Check if first/last match JDN for known dates
# Let's compute what JDN would be for the first month of era 27
print("\n=== Testing JDN hypothesis ===")
# If first/last are JDN, then for era 27 year 1 month 1:
# first should be around JDN for 1465-01-01 (Gregorian) = 2252265
# But we see first=1641025 for year=1, month=10

# Let's check what 1641025 corresponds to
# JDN 1641025 = ?
# JDN epoch is Jan 1, 4713 BC
# JDN 0 = Monday, Jan 1, 4713 BC (Julian)
# JDN 1641025 = ?
# Let's check: 1641025 + 4713*365.25 ≈ 1641025 + 1721600 ≈ 3,362,625 days from epoch
# That's about 9200 years... no that's wrong.

# Actually JDN for 1 AD Jan 1 = 1721424 (Gregorian)
# JDN 1641025 = 1721424 - 80399 = about 220 years before 1 AD
# That's around 219 BC

# Let's check if it's days since some epoch
print("\n=== Testing days since epoch ===")
# If first=1641025 corresponds to 1465 AD:
# Days from 1465-01-01 to some epoch
# 1465 * 365.25 = 535,000 days from year 0
# That's close to 1,641,025? No, 1.6M is much larger.

# Let's check: 1641025 / 365.25 = 4492 years from epoch
# 4492 - 1465 = 3027 BC? That doesn't match.

# Let's check Chinese calendar epoch
# Some systems use 2637 BC (Yellow Emperor)
# 1465 + 2637 = 4102 years * 365.25 = 1,498,000 days
# Still not 1,641,025

# Let's check if it's Julian Day Number but with different epoch
# JDN for 1465-01-01 (Julian calendar) = ?
# JDN for 1465-01-01 (Gregorian) = 2252265
# JDN for 1465-01-01 (Julian) = 2252265 - 9 = 2252256 (approx)
# 1641025 is much smaller

# Maybe it's days since 1 AD?
# 1465 * 365.25 = 535,000
# No.

# Let's check if first/last are RD (Rata Die) - days since 0001-01-01
# RD for 1465-01-01 = 535,000 approx
# Still not 1.6M

# Let's check if it's days since some Chinese epoch
# 1641025 / 365.25 = 4492.6 years
# If epoch is -2637 (2637 BC): 4492.6 - 2637 = 1855 AD - no
# If epoch is -4713 (Julian): 4492.6 - 4713 = -220 AD - no

# Let's try: maybe it's JDN - some offset
# 2252265 (JDN for 1465) - 1641025 = 611240
# 611240 / 365.25 = 1673 years
# That's 1465 - 1673 = -208 AD

# Let's check era 1 (25 AD)
cursor.execute("""
    SELECT * FROM ddbc_t_month WHERE era_id = 1 AND year = 1 AND month = 1
""")
row = cursor.fetchone()
if row:
    print("\n=== Era 1 year 1 month 1 ===")
    print("  first={}, last={}".format(row['first'], row['last']))
    # JDN for 25 AD = 1738291
    # If first=JDN: 1738291
    # Diff: 1738291 - row['first'] = ?

# Check era 27 year 9 month 1 (Thanh Hoa year 9 = 1473)
cursor.execute("""
    SELECT * FROM ddbc_t_month WHERE era_id = 27 AND year = 9 AND month = 1
""")
row = cursor.fetchone()
if row:
    print("\n=== Era 27 year 9 month 1 (Thanh Hoa year 9 = 1473) ===")
    print("  first={}, last={}".format(row['first'], row['last']))
    # JDN for 1473-01-01 = 2255198
    # Diff: 2255198 - row['first'] = ?

conn.close()