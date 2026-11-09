import re
import sys

# Force stdout to handle utf-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Get full CREATE TABLE for t_dynasty
tables = ['t_dynasty', 't_dynasty_names', 't_dynasty_comments',
          't_emperor', 't_emperor_names', 't_emperor_comments',
          't_era', 't_era_names', 't_era_comments',
          't_month', 't_month_comments',
          't_by_year']

for table in tables:
    pattern = 'CREATE TABLE `' + table + '`'
    pos = content.find(pattern)
    if pos >= 0:
        # Find the closing );
        end = content.find(');', pos)
        if end >= 0:
            print('=== {} ==='.format(table))
            print(content[pos:end+2])
            print()
        else:
            end = content.find(') ENGINE', pos)
            if end >= 0:
                print('=== {} ==='.format(table))
                print(content[pos:end+50])
                print()
    else:
        print('{} NOT FOUND'.format(table))

# Count total INSERT rows per table in main SQL
print("\n=== INSERT ROW COUNTS ===")
for table in tables:
    insert_pattern = 'INSERT INTO `' + table + '` VALUES '
    pos = content.find(insert_pattern)
    if pos >= 0:
        end = content.find(';', pos)
        insert_text = content[pos:end]
        row_count = insert_text.count('),(')
        if row_count > 0:
            print('{}: ~{} rows'.format(table, row_count + 1))
        else:
            print('{}: 1 row (or single row format)'.format(table))