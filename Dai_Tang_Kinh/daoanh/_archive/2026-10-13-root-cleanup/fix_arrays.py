#!/usr/bin/env python3
"""Fix the reset arrays in places.html to include all 15 tabs."""
import re

filepath = 'places.html'

with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Fix 1: Replace the array in selectItem (first occurrence)
old1 = "['cbeta','graph','persons','lineage','timeline'].forEach(t => {"
new1 = "['cbeta','daitang','graph','persons','lineage','timeline','giaoly','thuvien','nghile','giaoduc','sukien','bandoo','dulieu','hinhanh','nghethuat'].forEach(t => {"

# Fix 2: Replace the array in selectPerson (second occurrence)
# Find the second occurrence by looking after the first
idx1 = content.find(old1)
idx2 = content.find(old1, idx1 + 1) if idx1 >= 0 else -1

if idx1 >= 0:
    content = content.replace(old1, new1, 1)
    print(f"Replaced first occurrence at index {idx1}")
else:
    print("First occurrence not found")

if idx2 >= 0:
    # Need to find the exact old string at idx2
    old2 = content[idx2:idx2+len(old1)]
    new2 = new1
    content = content.replace(old2, new2, 1)
    print(f"Replaced second occurrence at index {idx2}")
else:
    print("Second occurrence not found")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing arrays")