import re
fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Get CREATE TABLE statements for key tables
tables = ['t_dynasty', 't_dynasty_names', 't_dynasty_comments',
          't_emperor', 't_emperor_names', 't_emperor_comments',
          't_era', 't_era_names', 't_era_comments',
          't_month', 't_month_names', 't_month_comments',
          't_by_year']

for table in tables:
    # Find CREATE TABLE
    pattern = 'CREATE TABLE `' + table + '`'
    pos = content.find(pattern)
    if pos >= 0:
        # Find the closing )
        end = content.find(')', pos)
        print('=== {} ==='.format(table))
        print(content[pos:end+1])
        print()
    else:
        print('{} NOT FOUND'.format(table))

# Also check t_month structure more carefully
pos = content.find('INSERT INTO `t_month`')
if pos >= 0:
    print('First t_month INSERT (first 500 chars):')
    snippet = content[pos:pos+500]
    # Replace non-ascii for display
    print(snippet.encode('ascii', 'replace').decode('ascii'))