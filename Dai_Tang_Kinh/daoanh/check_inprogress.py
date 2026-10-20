with open('docs/tasktodo.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'IN_PROGRESS' in line or 'in_progress' in line:
        print('Line', i+1, ':', line.encode('ascii', 'replace').decode()[:150])