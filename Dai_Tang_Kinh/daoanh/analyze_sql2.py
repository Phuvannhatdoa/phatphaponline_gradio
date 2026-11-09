import re
fpath = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Try different patterns
print('=== Checking CREATE TABLE patterns ===')
# Pattern 1: backtick
create_matches = re.findall(r'CREATE TABLE\s+\`(\w+)\`', content)
print('Pattern 1 (backtick):', create_matches)

# Pattern 2: without backtick
create_matches2 = re.findall(r'CREATE TABLE\s+(\w+)', content)
print('Pattern 2 (no backtick):', create_matches2[:20])

# Pattern 3: with escaped backtick
create_matches3 = re.findall(r'CREATE TABLE\s+`(\w+)`', content)
print('Pattern 3 (single backtick):', create_matches3)

# Count lines
lines = content.splitlines()
print('Total lines:', len(lines))
print('First 15 lines:')
for i, line in enumerate(lines[:15]):
    print('  {}: {}'.format(i+1, line[:120]))

# Check for INSERT
insert_matches = re.findall(r'INSERT INTO\s+(\w+)', content)
print('INSERT matches:', insert_matches)