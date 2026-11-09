import re

fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Get CREATE TABLE for t_emperor_comments
table_name = 't_emperor_comments'
pattern = 'CREATE TABLE `' + table_name + '`'
pos = content.find(pattern)
if pos >= 0:
    end = content.find(');', pos)
    if end >= 0:
        create_sql = content[pos:end+2]
        print("Found CREATE TABLE:")
        print(create_sql)
    else:
        print("No ); found")
else:
    print("NOT FOUND")