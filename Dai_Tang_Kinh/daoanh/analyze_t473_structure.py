#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T473: Analyze SQL file structure"""
import re

fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'

with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Count CREATE TABLE
create_matches = re.findall(r'CREATE TABLE\s+\`(\w+)\`', content)
create_counts = {}
for t in set(create_matches):
    count = content.count(f'CREATE TABLE \`{t}\`')
    create_counts[t] = count
    
print('CREATE TABLE statements:')
for t in sorted(create_counts.keys()):
    print(f'  {t}: {create_counts[t]}')

# Count INSERT INTO
insert_count = len(re.findall(r'INSERT INTO\s+\`\w+\`', content))
print(f'INSERT INTO statements: {insert_count}')

# Count lines
lines = content.splitlines()
print(f'Total lines: {len(lines)}')

# Count specific table CREATE statements
for term in ['t_dynasty', 't_emperor', 't_era', 't_month']:
    count = content.count(f'CREATE TABLE \`{term}\`')
    if count > 0:
        print(f'{term} CREATE TABLE: {count} times')

# INSERT INTO for these tables
for term in ['t_dynasty', 't_emperor', 't_era', 't_month']:
    count = content.count(f'INSERT INTO \`{term}\`')
    if count > 0:
        print(f'INSERT INTO {term}: {times} times')
"