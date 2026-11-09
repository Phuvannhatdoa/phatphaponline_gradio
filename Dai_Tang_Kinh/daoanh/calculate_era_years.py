#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T473 Step 5: Calculate start/end years for eras and dynasties from t_month
"""

import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_FILE = r'data\lineage.db'

# JDN to Gregorian date conversion
def jdn_to_gregorian(jdn):
    """Convert Julian Day Number to Gregorian date (year, month, day)"""
    # Algorithm from Fliegel & Van Flandern
    jdn = int(jdn) + 32044
    g = jdn // 146097
    dg = jdn % 146097
    c = (dg // 36524 + 1) * 3 // 4
    dc = dg - c * 36524
    b = dc // 1461
    db = dc % 1461
    a = (db // 365 + 1) * 3 // 4
    da = db - a * 365
    y = g * 400 + c * 100 + b * 4 + a
    m = (da * 5 + 308) // 153 - 2
    d = da - (m + 4) * 153 // 5 + 122
    year = y - 4800 + (m + 2) // 12
    month = (m + 2) % 12 + 1
    day = d + 1
    return year, month, day

def jdn_to_julian(jdn):
    """Convert Julian Day Number to Julian calendar date"""
    jdn = int(jdn) + 32082
    d = jdn // 1461 * 4
    jdn = jdn % 1461
    if jdn >= 1096:
        jdn -= 1096
        d += 3
    else:
        d += jdn // 365
    jdn = jdn % 365
    m = (jdn * 5 + 308) // 153 - 2
    day = jdn - (m + 4) * 153 // 5 + 122
    year = d // 4
    month = (m + 2) % 12 + 1
    if month <= 2:
        year += 1
    return year, month, day

# Test with known values
print("=== JDN Conversion Test ===")
# JDN for 25 AD Feb 15 (Julian) ≈ 1730236
y, m, d = jdn_to_julian(1730236)
print("JDN 1730236 -> Julian: {}-{:02d}-{:02d}".format(y, m, d))

y, m, d = jdn_to_gregorian(1730236 + 2)  # Adjust for Gregorian
print("JDN 1730238 -> Gregorian: {}-{:02d}-{:02d}".format(y, m, d))

# JDN for 1465 Jan 1 (Gregorian) = 2252265
y, m, d = jdn_to_gregorian(2252265)
print("JDN 2252265 -> Gregorian: {}-{:02d}-{:02d}".format(y, m, d))

# JDN for 1473 Jan 1 (Gregorian) = 2255198
y, m, d = jdn_to_gregorian(2255198)
print("JDN 2255198 -> Gregorian: {}-{:02d}-{:02d}".format(y, m, d))

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get min/max first for each era (year 1 month 1 to last year last month)
print("\n=== Calculating era year ranges from t_month ===")
cursor.execute("""
    SELECT 
        m.era_id,
        MIN(m.first) as era_start_jdn,
        MAX(m.last) as era_end_jdn,
        MIN(m.year) as min_year,
        MAX(m.year) as max_year
    FROM ddbc_t_month m
    GROUP BY m.era_id
    ORDER BY era_start_jdn
""")
era_ranges = cursor.fetchall()

# Get era names
print("\n=== Era ranges (first 30) ===")
for era in era_ranges[:30]:
    era_id = era['era_id']
    cursor.execute("SELECT name FROM ddbc_t_era_names WHERE era_id = ? AND language_id = 1 AND ranking = 0", (era_id,))
    name_row = cursor.fetchone()
    era_name = name_row['name'] if name_row else 'Unknown'
    
    start_y, start_m, start_d = jdn_to_gregorian(era['era_start_jdn'])
    end_y, end_m, end_d = jdn_to_gregorian(era['era_end_jdn'])
    
    print("  era_id={:4d} {:12s} JDN {:8d}-{:8d} -> Gregorian {}-{:02d}-{:02d} to {}-{:02d}-{:02d} (years {}-{})".format(
        era_id, era_name, era['era_start_jdn'], era['era_end_jdn'],
        start_y, start_m, start_d, end_y, end_m, end_d,
        era['min_year'], era['max_year']))

# Check specific known eras
print("\n=== Known eras verification ===")
known_eras = {
    1: "Kien Vu (建武) - 25-56 AD",
    27: "Dien Hy (延熹) - 158-167 AD", 
    642: "Thanh Hoa (成化) - 1465-1487 AD",
}
for era_id, desc in known_eras.items():
    cursor.execute("SELECT MIN(first) as start_jdn, MAX(last) as end_jdn FROM ddbc_t_month WHERE era_id = ?", (era_id,))
    row = cursor.fetchone()
    if row and row['start_jdn']:
        start_y, start_m, start_d = jdn_to_gregorian(row['start_jdn'])
        end_y, end_m, end_d = jdn_to_gregorian(row['end_jdn'])
        print("  {}: JDN {}->{} = Gregorian {}-{:02d}-{:02d} to {}-{:02d}-{:02d}".format(
            desc, row['start_jdn'], row['end_jdn'], start_y, start_m, start_d, end_y, end_m, end_d))

# Calculate dynasty ranges
print("\n=== Dynasty ranges ===")
cursor.execute("""
    SELECT 
        d.id as dynasty_id,
        d.type,
        MIN(m.first) as dynasty_start_jdn,
        MAX(m.last) as dynasty_end_jdn
    FROM ddbc_t_dynasty d
    JOIN ddbc_t_emperor e ON d.id = e.dynasty_id
    JOIN ddbc_t_era er ON e.id = er.emperor_id
    JOIN ddbc_t_month m ON er.id = m.era_id
    GROUP BY d.id
    ORDER BY dynasty_start_jdn
""")
dynasty_ranges = cursor.fetchall()

for dyn in dynasty_ranges:
    cursor.execute("SELECT name FROM ddbc_t_dynasty_names WHERE dynasty_id = ? AND language_id = 1 AND ranking = 0", (dyn['dynasty_id'],))
    name_row = cursor.fetchone()
    dyn_name = name_row['name'] if name_row else 'Unknown'
    
    start_y, start_m, start_d = jdn_to_gregorian(dyn['dynasty_start_jdn'])
    end_y, end_m, end_d = jdn_to_gregorian(dyn['dynasty_end_jdn'])
    
    print("  dynasty_id={:3d} {:10s} type={:8s} JDN {}->{} -> Gregorian {}-{:02d}-{:02d} to {}-{:02d}-{:02d}".format(
        dyn['dynasty_id'], dyn_name, dyn['type'], dyn['dynasty_start_jdn'], dyn['dynasty_end_jdn'],
        start_y, start_m, start_d, end_y, end_m, end_d))

conn.close()