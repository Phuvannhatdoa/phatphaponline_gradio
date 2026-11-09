#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T414 statistics"""
import sqlite3
import os
from collections import Counter

DB_PATH = 'data/lineage.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all edges
cursor.execute('SELECT id, teacher_id, disciple_id, marcus_subtype, ttl_confirmed, conflict, notes, relation_kind FROM lineage_primary_teacher')
edges = cursor.fetchall()
print(f'Total edges: {len(edges)}')

# Count by marcus_subtype
marcus_counts = Counter()
for edge in edges:
    mar_sub = edge[3]  # marcus_subtype
    if mar_sub:
        marcus_counts[mar_sub] += 1

print('Marcus subtype distribution:')
for k, v in marcus_counts.most_common(20):
    print(f'  {k}: {v}')

# Count edges with/without relation_kind
with_kind = sum(1 for e in edges if e[7])  # relation_kind is column 7
without_kind = len(edges) - with_kind
print(f'Edges with relation_kind: {with_kind}')
print(f'Edges without relation_kind: {without_kind}')

# Check marcus_subtype 'dharma_transmission' count
dt_count = sum(1 for e in edges if e[3] == 'dharma_transmission')
print(f'Edges with marcus_subtype dharma_transmission: {dt_count}')

# Check how many currently have relation_kind=unknown
unknown_count = sum(1 for e in edges if e[7] == 'unknown')
print(f'Edges currently with relation_kind=unknown: {unknown_count}')

# Check statistic distribution if relation_kind set
noi_phap = sum(1 for e in edges if e[7] == 'noi_phap')
khac = sum(1 for e in edges if e[7] == 'khac')
print(f'Edges with relation_kind=noi_phap: {noi_phap}')
print(f'Edges with relation_kind=khac: {khac}')

conn.close()
print('Statistics complete')
PYEOF