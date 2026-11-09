import hashlib
import os
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
    
print '=== CREATE TABLE statements ==='

for t in sorted(create_counts.keys()):
    print '  {0}: {1}'.format(t, create_counts[t])

# Count INSERT INTO
insert_count = len(re.findall(r'INSERT INTO\s+\`\w+\`', content))
print 'INSERT INTO statements: {0}'.format(insert_count)

# Count lines
lines = content.splitlines()
print 'Total lines: {0}'.format(len(lines))

# Count specific table CREATE statements
for term in ['t_dynasty', 't_emperor', 't_era', 't_month']:
    count = content.count('CREATE TABLE \`{0}\`'.format(term))
    if count > 0:
        print '{0} CREATE TABLE: {1}'.format(term, count)

# INSERT INTO for these tables
for term in ['t_dynasty', 't_emperor', 't_era', 't_month']:
    count = content.count('INSERT INTO \u0060{0}\`'.format(term))
    if count > 0:
        print 'INSERT INTO {0}: {1} times'.format(term, count)
"