import re

def mysql_type_to_sqlite(mysql_type: str) -> str:
    mysql_type = mysql_type.upper()
    if 'TINYINT' in mysql_type or 'SMALLINT' in mysql_type or 'MEDIUMINT' in mysql_type or 'INT' in mysql_type:
        return 'INTEGER'
    elif 'BIGINT' in mysql_type:
        return 'INTEGER'
    elif 'CHAR' in mysql_type or 'TEXT' in mysql_type or 'ENUM' in mysql_type:
        return 'TEXT'
    elif 'FLOAT' in mysql_type or 'DOUBLE' in mysql_type or 'DECIMAL' in mysql_type:
        return 'REAL'
    elif 'DATE' in mysql_type or 'TIME' in mysql_type or 'DATETIME' in mysql_type:
        return 'TEXT'
    elif 'BLOB' in mysql_type:
        return 'BLOB'
    else:
        return 'TEXT'

# Test with t_emperor_comments
mysql_ddl = """CREATE TABLE `t_emperor_comments` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `emperor_id` smallint(5) unsigned NOT NULL,
  `comment` text NOT NULL,
  PRIMARY KEY (`id`),
  KEY `emperor_id` (`emperor_id`),
  CONSTRAINT `t_emperor_comments_ibfk_1` FOREIGN KEY (`emperor_id`) REFERENCES `t_emperor` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

# Extract column definitions
start = mysql_ddl.find('(')
end = mysql_ddl.rfind(')')
columns_text = mysql_ddl[start+1:end]

print("columns_text:")
print(columns_text)
print()

lines = [l.strip() for l in columns_text.split('\n') if l.strip()]
columns = []
primary_keys = []
has_auto_increment_pk = False

for line in lines:
    line = line.rstrip(',')
    upper_line = line.upper()
    
    print("Processing: {}".format(line))
    print("  upper: {}".format(upper_line))
    print("  starts with PRIMARY KEY: {}".format(upper_line.startswith('PRIMARY KEY')))
    print("  starts with KEY: {}".format(upper_line.startswith('KEY ')))
    print("  starts with CONSTRAINT: {}".format(upper_line.startswith('CONSTRAINT')))
    print("  starts with FOREIGN KEY: {}".format(upper_line.startswith('FOREIGN KEY')))
    
    # Skip table-level constraints and indexes
    if (upper_line.startswith('PRIMARY KEY') or 
        upper_line.startswith('KEY ') or 
        upper_line.startswith('INDEX ') or 
        upper_line.startswith('UNIQUE ') or
        upper_line.startswith('CONSTRAINT') or
        upper_line.startswith('FOREIGN KEY') or
        upper_line.startswith('CHECK ')):
        # Extract primary key columns if PRIMARY KEY
        if upper_line.startswith('PRIMARY KEY'):
            pk_match = re.search(r'PRIMARY KEY\s*\(([^)]+)\)', line, re.IGNORECASE)
            if pk_match:
                pk_cols = [c.strip('` ') for c in pk_match.group(1).split(',')]
                primary_keys.extend(pk_cols)
                print("  Found PK: {}".format(pk_cols))
        print("  SKIPPED")
        continue
    
    # Column definition: `name` type [NOT NULL] [AUTO_INCREMENT] [DEFAULT ...]
    match = re.match(r'`(\w+)`\s+([^,\s]+)', line)
    if match:
        col_name = match.group(1)
        col_type = match.group(2)
        sqlite_type = mysql_type_to_sqlite(col_type)
        
        col_def = '`{}` {}'.format(col_name, sqlite_type)
        if 'NOT NULL' in upper_line:
            col_def += ' NOT NULL'
        if 'AUTO_INCREMENT' in upper_line:
            if col_name in primary_keys:
                col_def += ' PRIMARY KEY'
            else:
                col_def += ' PRIMARY KEY'
                has_auto_increment_pk = True
        columns.append(col_def)
        print("  ADDED COLUMN: {}".format(col_def))
    else:
        print("  NO MATCH for column regex")

print()
print("Final columns: {}".format(columns))
print("Primary keys: {}".format(primary_keys))