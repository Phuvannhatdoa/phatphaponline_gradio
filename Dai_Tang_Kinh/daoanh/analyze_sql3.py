import re
fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Count INSERT INTO per table
tables = ['c_languages', 't_by_year', 't_day_comments', 't_dynasty', 't_dynasty_comments', 
          't_dynasty_names', 't_emperor', 't_emperor_comments', 't_emperor_names', 
          't_era', 't_era_comments', 't_era_names', 't_month', 't_month_comments']

for table in tables:
    count = content.count('INSERT INTO `' + table + '`')
    if count > 0:
        print('INSERT INTO `{0}`: {1} times'.format(table, count))

# Also check without backticks
for table in tables:
    count = content.count('INSERT INTO ' + table)
    if count > 0:
        print('INSERT INTO {0} (no backtick): {1} times'.format(table, count))

# Get first INSERT for t_dynasty
pos = content.find('INSERT INTO `t_dynasty`')
if pos >= 0:
    print('\nFirst t_dynasty INSERT (first 300 chars):')
    print(content[pos:pos+300])

# Get first INSERT for t_month
pos = content.find('INSERT INTO `t_month`')
if pos >= 0:
    print('\nFirst t_month INSERT (first 300 chars):')
    print(content[pos:pos+300])