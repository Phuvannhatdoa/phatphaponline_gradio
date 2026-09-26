#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3, sys

conn = sqlite3.connect('data/lineage.db')
c = conn.cursor()
target = 'Thiếu Lâm Tự'

results = []

# 1. entity_hub - có canonical_label
c.execute("SELECT entity_id, canonical_label, entity_type FROM entity_hub WHERE canonical_label LIKE ?", (f'%{target}%',))
rows = c.fetchall()
results.append("=== entity_hub ===")
for r in rows:
    results.append(f"entity_id={r[0]}, label={r[1]}, type={r[2]}")

# 2. entity (DILA) - có dila_id
c.execute("SELECT entity_id, dila_id, entity_type, alias_vi FROM entity WHERE alias_vi LIKE ? OR dila_id LIKE ?", (f'%{target}%', f'%{target}%'))
rows2 = c.fetchall()
results.append("\n=== entity (DILA) ===")
for r in rows2:
    results.append(f"entity_id={r[0]}, dila_id={r[1]}, type={r[2]}, alias_vi={r[3]}")

# 3. entity_source_ids
c.execute("SELECT * FROM entity_source_ids WHERE source_entity_id LIKE ?", (f'%{target}%',))
rows3 = c.fetchall()
results.append("\n=== entity_source_ids ===")
for r in rows3:
    results.append(f"id={r[0]}, entity_id={r[1]}, source={r[2]}, source_entity_id={r[3]}, match_status={r[4]}, confidence={r[5]}, verified={r[6]}")

# 4. people (has name_vi, dynasty, source_origin)
c.execute("SELECT * FROM people WHERE name_vi LIKE ? OR dynasty LIKE ?", (f'%{target}%', f'%{target}%'))
rows4 = c.fetchall()
results.append("\n=== people ===")
for r in rows4:
    results.append(f"id={r[0]}, name_vi={r[1]}, dynasty={r[2]}, birth_year={r[3]}, death_year={r[4]}, source_origin={r[10]}")

# 5. lineage_chronology
c.execute("SELECT * FROM lineage_chronology WHERE dynasty LIKE ?", (f'%{target}%',))
rows5 = c.fetchall()
results.append("\n=== lineage_chronology ===")
for r in rows5:
    results.append(f"id={r[0]}, dynasty={r[1]}, time_from={r[2]}, time_to={r[3]}")

with open('entity_search_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

conn.close()
print('Da ghi ket qua entity_search_result.txt')