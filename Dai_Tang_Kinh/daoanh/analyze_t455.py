#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analyze T455 name standardization data"""
import csv
import re
from collections import Counter

with open('docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

print('=== T455 DATA ANALYSIS ===')
print(f'Total people: {len(rows)}')
print()

# Check name_vi_db_ZQ vs name_vi_cloud
same = 0
diff = 0
for row in rows:
    if row[3] == row[4]:
        same += 1
    else:
        diff += 1
print(f'same (ZQ == Cloud): {same}')
print(f'diff (ZQ != Cloud): {diff}')
print()

# Check Hán presence in name_vi_db_ZQ
has_han = 0
no_han = 0
for row in rows:
    vi = row[3]
    if re.search(r'[\u4e00-\u9fff]', vi):
        has_han += 1
    else:
        no_han += 1
print(f'name_vi_db_ZQ contains Hán: {has_han}')
print(f'name_vi_db_ZQ NO Hán: {no_han}')
print()

# so_lan distribution
so_lan_vals = Counter(int(row[6]) for row in rows)
print('so_lan distribution (top 15):')
for k, v in so_lan_vals.most_common(15):
    print(f'  {k} appearances: {v} people')
print()

# Examples of different names
print('=== Examples where ZQ != Cloud ===')
count = 0
for row in rows:
    if row[3] != row[4] and len(row[3]) > 0 and count < 15:
        pid = row[0]
        vi_zq = row[3]
        vi_cloud = row[4]
        zh_cat = row[1]
        print(f'  {pid}: ZQ={vi_zq.encode("unicode_escape").decode()}, Cloud={vi_cloud.encode("unicode_escape").decode()}, Catalog={zh_cat.encode("unicode_escape").decode()}')
        count += 1
print()

# Check people with NO Hán in name_vi_db_ZQ but have Hán in catalog
print('=== People with Hán in catalog but NO Hán in DB name_vi ===')
count = 0
for row in rows:
    vi_zq = row[3]
    zh_catalog = row[1]
    if re.search(r'[\u4e00-\u9fff]', zh_catalog) and not re.search(r'[\u4e00-\u9fff]', vi_zq) and len(vi_zq) > 0 and count < 10:
        pid = row[0]
        print(f'  {pid}: Catalog={zh_catalog.encode("unicode_escape").decode()}, ZQ name={vi_zq.encode("unicode_escape").decode()}')
        count += 1
print()

# Check so_lan for people with missing Hán
print('=== so_lan for people missing Hán in ZQ name ===')
so_lan_missing_han = Counter()
for row in rows:
    vi_zq = row[3]
    zh_catalog = row[1]
    if re.search(r'[\u4e00-\u9fff]', zh_catalog) and not re.search(r'[\u4e00-\u9fff]', vi_zq):
        so_lan_missing_han[int(row[6])] += 1
for k, v in so_lan_missing_han.most_common(10):
    print(f'  {k} appearances: {v} people')