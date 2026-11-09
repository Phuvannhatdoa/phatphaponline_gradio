import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for name, fpath in [
    ('Japanese', r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time_japanese.sql'),
    ('Korean', r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time_korean.sql')
]:
    print('\n=== {} ==='.format(name))
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    print('File size (chars):', len(content))
    print('Lines:', len(content.splitlines()))
    
    # Count CREATE TABLE
    create_matches = re.findall(r'CREATE TABLE\s+\`(\w+)\`', content)
    print('CREATE TABLE:', set(create_matches))
    
    # Count INSERT
    tables = ['t_dynasty', 't_dynasty_names', 't_dynasty_comments',
              't_emperor', 't_emperor_names', 't_emperor_comments',
              't_era', 't_era_names', 't_era_comments',
              't_month', 't_month_comments', 't_month_names',
              't_by_year', 'c_languages', 't_day_comments']
    
    for table in tables:
        insert_pattern = 'INSERT INTO `' + table + '` VALUES '
        pos = content.find(insert_pattern)
        if pos >= 0:
            end = content.find(';', pos)
            insert_text = content[pos:end]
            row_count = insert_text.count('),(')
            if row_count > 0:
                print('  {}: ~{} rows'.format(table, row_count + 1))
            else:
                print('  {}: 1 row'.format(table))
        else:
            print('  {}: NOT FOUND'.format(table))