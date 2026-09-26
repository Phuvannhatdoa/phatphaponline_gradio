#!/usr/bin/env python3
"""Check home.html for search/autocomplete functionality."""
import sys

filepath = 'home.html'

try:
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

keywords = ['<input', 'search', 'autocomplete', 'type text', 'type search']
for kw in keywords:
    count = content.lower().count(kw.lower())
    if count > 0:
        print(f'{kw}: {count} occurrences')

print(f"\nFile length: {len(content)}")
print("First 500 chars:")
try:
    print(content[:500])
except:
    print("Cannot print first 500 chars due to encoding")