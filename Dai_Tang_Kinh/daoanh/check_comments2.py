import re

fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Check t_emperor_comments
tables = ['t_emperor_comments', 't_era_comments']
for table in tables:
    pattern = 'CREATE TABLE `' + table + '`'
    pos = content.find(pattern)
    if pos >= 0:
        end = content.find(');', pos)
        if end >= 0:
            snippet = content[pos:end+2]
            # Write to file
            with open('{}.txt'.format(table), 'w', encoding='utf-8') as out:
                out.write(snippet)
            print('{} written to file'.format(table))
        else:
            end = content.find(') ENGINE', pos)
            if end >= 0:
                snippet = content[pos:end+50]
                with open('{}.txt'.format(table), 'w', encoding='utf-8') as out:
                    out.write(snippet)
                print('{} written to file (alt)'.format(table))
    else:
        print('{} NOT FOUND'.format(table))