#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Categorize T455 name mismatches"""
import csv
import re

with open('docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

print('=== CATEGORIZATION ANALYSIS ===')
print(f'Total: {len(rows)} people')
print()

# Category (a): ZQ clearly wrong
# Examples from task: "Di Lac Bo Tat", "Wang Chum", "Cho Ngac Van", "La Di Jian"
# These are cases where ZQ name is definitely wrong compared to catalog

# Category (b): Same person, different names (variant/honorary)
# Examples: "Fan Zhi Dong/Fan Gu Nong", "Jue Yin/Fo Yin", "Lao Can/Ye Jun"
# These should NOT be fixed, just add alias

# Category (c): Different due to orthography rules
# Examples: Hue/Tue, Tho/Thu, Truoc/Trus, Ti/Ty, hoa/Hoa
# Follow project spelling rules

# Let me look at some specific cases to categorize

print('=== Category (a): ZQ clearly wrong (need correction) ===')
# These are cases where the ZQ name is demonstrably incorrect 
# compared to the DILA catalog and common sense

count_a = 0
for row in rows:
    pid = row[0]
    vi_zq = row[3]
    vi_cloud = row[4]
    zh_catalog = row[1]
    # Check if ZQ name is very different from catalog and cloud
    # Simple heuristic: if ZQ name is very short, or has obvious errors
    if vi_zq and len(vi_zq) < 3 and vi_zq != vi_cloud:
        # Very short ZQ name - likely wrong
        print(f'  {pid}: ZQ="{vi_zq}", Cloud="{vi_cloud}", Catalog="{zh_catalog}"')
        count_a += 1
        if count_a >= 10: break

print(f'\\nEstimated category (a) count: need manual review')
print()

# Look at people with very short ZQ names (likely category a)
short_vi_zq = [(row[0], row[3], row[4], row[1]) for row in rows if row[3] and len(row[3]) < 3]
print(f'People with very short ZQ name (< 3 chars): {len(short_vi_zq)}')
for item in short_vi_zq[:15]:
    print(f'  {item[0]}: ZQ="{item[1]}", Cloud="{item[2]}", Catalog="{item[3]}"')
print()

# Category (b): Variant/honorary names - same person, different names
# These often have the same Hán character but different Vietnamese readings
print('=== Category (b): Variant/honorary names ===')
# Look for people where catalog Hán is same but Vietnamese names differ
# or where ZQ name is a known variant

# Let's check some specific well-known cases from the data
# A001713: Huệ Uyển (ZQ) vs Tuệ Uyển (DB) - already noted in T453
# A000457: Lã Di Giản (ZQ) vs Lã Dì Giản (DB) - noted as ZQ error

print('\\n=== Checking for category (b) variants ===')
# Look for people with same catalog Hán but different ZQ/DB names
# or known variant patterns

# From task mentions: "范寄東/范古農, 覺音/佛音, 了參/葉均" - these are variant names
# Let me search for patterns

count_b = 0
for row in rows:
    pid = row[0]
    vi_zq = row[3]
    vi_db_zq_orig = row[3]  # same as vi_zq since this is DB ZQ
    zh_catalog = row[1]
    # Check if ZQ name looks like a variant (different reading of same Hán)
    # or if there's a known pattern
    if re.search(r'(音|參|均|東|農|廉)', vi_zq) or re.search(r'(音|參|均|東|農|廉)', zh_catalog):
        # Might be variant - but need manual check
        pass

print(f'Checking variant patterns... (manual review needed)')
print()

# Category (c): Orthography differences
# Hue/Tue, Tho/Thu, Truoc/Trus, Ti/Ty, hoa/Hoa
print('=== Category (c): Orthography differences ===')
ortho_examples = []
for row in rows:
    vi_zq = row[3]
    # Check for common orthography pairs
    ortho_pairs = [('Huệ', 'Tuệ'), ('Thọ', 'Thử'), ('Trước', 'Trứ'), ('Tì', 'Tỳ'), ('Hoa', 'Hoá')]
    for zh, vi in ortho_pairs:
        if vi_zq.count(zh) > 0 or vi_zq.count(vi) > 0:
            ortho_examples.append((row[0], vi_zq, zh, vi))
            break

print(f'People with potential orthography issues: {len(ortho_examples)}')
for item in ortho_examples[:10]:
    print(f'  {item[0]}: ZQ="{item[1]}", ortho pair: "{item[2]}"/"{item[3]}"')
print()

# Now let's count people missing Hán and need it added
print('=== People missing Hán who SHOULD have it ===')
# These are people where the catalog has Hán but DB name_vi doesn't
needs_han = 0
for row in rows:
    vi_zq = row[3]
    zh_catalog = row[1]
    if re.search(r'[\u4e00-\u9fff]', zh_catalog) and not re.search(r'[\u4e00-\u9fff]', vi_zq):
        needs_han += 1

print(f'People with Hán in catalog but NO Hán in ZQ name: {needs_han}')
print(f'Task mentions 532 people need Hán added')
print(f'Difference: {needs_han - 532} (may be category b variants)')
print()

# Let me check the 532 specifically - perhaps they're the ones with higher so_lan
print('=== so_lan for the 532 priority people ===')
# People who likely need Hán added (higher frequency = more important)
# The task says "ưu tiên lô có số lần xuất hiện cao (cột so_lan)"
so_lan_sorted = sorted(rows, key=lambda x: int(x[6]), reverse=True)
print(f'Top 20 by so_lan (most frequent in catalog):')
for i, row in enumerate(so_lan_sorted[:20]):
    has_han = bool(re.search(r'[\u4e00-\u9fff]', row[3]))
    print(f'  {i+1}. {row[0]}: so_lan={row[6]}, Hán in ZQ={has_han}, ZQ="{row[3]}"')