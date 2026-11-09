#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T455 Categorization with Admin decisions"""
import csv
import re
from collections import Counter

with open('docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

print('=== T455 CATEGORIZATION WITH ADMIN DECISIONS ===')
print(f'Total: {len(rows)} people')
print()

# Category (a): ZQ clearly wrong
# Simple heuristic: if name_vi_db_ZQ is very different from name_vi_catalog AND very short/odd
# From the task: examples like "Di Lac Bo Tat", "Vương Chùm", "Chờ Ngạc Vân", "Lã Dì Giản"
# These are cases where ZQ name is demonstrably incorrect

# Let me look at specific patterns from the task description
# The task mentions these as category (a): "Di Lắc Bồ Tát", "Vương Chùm", "Chờ Ngạc Vân", "Lã Dì Giản"
# These seem to be cases where ZQ made obvious errors

print('=== Category (a): ZQ clearly wrong ===')
# Let me check people with very short ZQ names or obvious mismatches
# From earlier analysis: 17 people have Hán in ZQ name, 777 don't
# For category (a), we need ZQ name that is clearly wrong

# Let me look at the examples mentioned in the task
# "Di Lắc Bồ Tát", "Vương Chùm", "Chờ Ngạc Vân", "Lã Dì Giản"
# These are probably people where ZQ name doesn't match catalog at all

# Let me search for people with very short ZQ names (< 3 chars) as these are likely category (a)
short_vi_zq = [(row[0], row[3], row[4], row[1]) for row in rows if row[3] and len(row[3]) < 3]
print(f'People with very short ZQ name (< 3 chars): {len(short_vi_zq)}')
for item in short_vi_zq[:10]:
    print(f'  {item[0]}: ZQ="{item[1]}", Cloud="{item[2]}", Catalog="{item[3]}"')

# Also check for people where ZQ name is completely different from catalog
print()
print('People where ZQ name != Cloud name AND ZQ name is short or suspicious:')
count_a = 0
for row in rows:
    pid = row[0]
    vi_zq = row[3]
    vi_cloud = row[4]
    zh_catalog = row[1]
    # Check if ZQ name is very different from catalog and cloud
    if vi_zq and vi_zq != vi_cloud and (len(vi_zq) < 3 or vi_zq.count(' ') > 0):
        # Very short ZQ name or has spaces - likely category (a)
        print(f'  {pid}: ZQ="{vi_zq}", Cloud="{vi_cloud}", Catalog="{zh_catalog}"')
        count_a += 1
        if count_a >= 15: break

print(f'\\nEstimated category (a) count: {count_a} (need manual review for exact count)')
print()

# Category (b): Same person, different names (variant/honorary)
# These are people where the catalog Hán is the same but Vietnamese names differ,
# or where ZQ name is a known variant of the DB name
print('=== Category (b): Variant/honorary names ===')
# From the task: "范寄東/范古農, 覺音/佛音, 了參/葉均" - these are variant names
# Same person, different name forms

# Look for people where the catalog Hán is the same but ZQ/DB names differ
# Or where there are known variant patterns
# Let's check people with the same first_cbeta_id but different names
from collections import Counter
first_cb_counts = Counter()
for row in rows:
    first_cb_counts[row[5]] += 1  # first_cbeta_id

# People with multiple entries under same cbeta_id
print(f'People with same first_cbeta_id:')
for cb_id, count in first_cb_counts.most_common(10):
    if count > 1:
        print(f'  {cb_id}: {count} people')
        # Show a few
        matches = [row for row in rows if row[5] == cb_id][:3]
        for m in matches:
            print(f'    {m[0]}: ZQ="{m[3]}", DB="{m[4]}", Catalog="{m[1]}"')

print()
print('=== Category (c): Orthography differences ===')
# Hue/Tue, Thọ/Thủ, Trước/Trứ, Tì/Tỳ, Hoa/Hoá
# These are spelling variations that should follow project rules

# Check for orthography pairs in the data
ortho_pairs = [('Huệ', 'Tuệ'), ('Thọ', 'Thử'), ('Trước', 'Trứ'), ('Tì', 'Tỳ'), ('Hoa', 'Hoá')]
ortho_count = Counter()
for row in rows:
    vi_zq = row[3]
    for zh, vi in ortho_pairs:
        if vi_zq.count(zh) > 0 or vi_zq.count(vi) > 0:
            ortho_count[(zh, vi)] += 1

print(f'People with potential orthography issues: {sum(ortho_count.values())}')
for pair, count in ortho_count.most_common():
    print(f'  Pair {pair}: {count} people')

print()
print('=== PRIORITIZATION by so_lan (for 532 people) ===')
# The 532 priority people should be those with highest so_lan
# Let me sort by so_lan and pick top 532
so_lan_sorted = sorted(rows, key=lambda x: int(x[6]), reverse=True)
print(f'Top 10 by so_lan:')
for i, row in enumerate(so_lan_sorted[:10]):
    has_han = bool(re.search(r'[\u4e00-\u9fff]', row[3]))
    print(f'  {i+1}. {row[0]}: so_lan={row[6]}, Hán in ZQ={has_han}, ZQ="{row[3]}"')

print()
print('=== SUMMARY ===')
print(f'Total: 794 people')
print(f'Category (a) ZQ clearly wrong: needs manual review, estimate ~{count_a if count_a else "need count"}')
print(f'Category (b) Variant/honorary: same person, different names → add alias')
print(f'Category (c) Orthography: Hue/Tue, Thọ/Thủ, etc. → follow project rules')
print(f'Priority 532: based on so_lan frequency (highest first)')
print(f'Q3c: Create people_name_vi_history table: YES')