#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""List task statuses"""
import os
import glob

# Find all T*.md task files
tasks = glob.glob('tasks/T*.md')
undone = []

for task in tasks:
    with open(task, 'r', encoding='utf-8') as f:
        content = f.read()
        # Extract status
        for line in content.split('\n'):
            if 'status:' in line:
                status = line.strip()
                # Extract task ID from filename
                tid = os.path.basename(task).replace('.md', '')
                undone.append((tid, status))
                break

# Print status summary
print('=== TASK STATUS SUMMARY ===')
for tid, status in sorted(undone):
    print(f'  {tid}: {status}')

print(f'\\nTotal tasks found: {len(undone)}')
PYEOF