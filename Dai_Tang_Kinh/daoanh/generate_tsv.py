#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate TSV for T414"""
import sqlite3
import os
from collections import Counter
from datetime import datetime

DB_PATH = 'data/lineage.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT id, teacher_id, disciple_id, marcus_subtype, ttl_confirmed, conflict, notes, relation_kind FROM lineage_primary_teacher')
edges = cursor.fetchall()

# Statistics
marcus_counts = Counter()
dt_count = 0
for edge in edges:
    mar_sub = edge[3]
    if mar_sub:
        marcus_counts[mar_sub] += 1
    if mar_sub == 'dharma_transmission':
        dt_count += 1

# Write TSV
tsv_path = 'docs/evidence/' + datetime.now().strftime('%Y%m%d') + '_T414_transmission_dryrun.tsv'
os.makedirs('docs/evidence', exist_ok=True)
with open(tsv_path, 'w', encoding='utf-8') as f:
    f.write('edge_id\tteacher_id\tdisciple_id\trelation_kind\treason\tmarcus_subtype\tttl_confirmed\tconflict\nexisting_relation_kind\n')
    for edge in edges:
        eid, teacher_id, disciple_id, mar_sub, ttl_conf, conflict, notes, rel_kind = edge
        f.write(f'{eid}\t{teacher_id}\t{disciple_id}\t{rel_kind if rel_kind else ""}\t\"\n"\t{mar_sub if mar_sub else ""}\t{ttl_conf if ttl_conf else ""}\t{conflict if conflict else ""}\n')

conn.close()
print('TSV exported: ' + 'docs/evidence/' + datetime.now().strftime('%Y%m%d') + '_T414_transmission_dryrun.tsv')

# Print summary
print('Total edges: ' + str(len(edges)))
print('dharma_transmission count: ' + str(dt_count))
print('Marcus subtype distribution:')
for k, v in marcus_counts.most_common():
    print('  ' + k + ': ' + str(v))
PYEOF