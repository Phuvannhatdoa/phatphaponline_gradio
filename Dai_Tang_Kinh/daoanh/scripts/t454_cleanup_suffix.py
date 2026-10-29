#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T454 - Clean _Hu/_-Ngoa suffix from name_vi, move to note_vi"""
import sqlite3
import json
import csv
import os
from datetime import datetime

DB_PATH = 'data/lineage.db'

def backup_db(db_path=DB_PATH):
    """Create backup before making changes"""
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'lineage_t454_{ts}.db')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f'Backup created: {backup_path}')
    return backup_path

def get_db_columns():
    """Get actual column names from the database"""
    cursor = sqlite3.connect(DB_PATH).cursor()
    cursor.execute('PRAGMA table_info(namevi_map_places)')
    cols = cursor.fetchall()
    return [c[1] for c in cols]

def find_suffix_rows(conn):
    """Find all rows with _Hu or _Ngoa in note_vi"""
    cursor = conn.cursor()
    # Search for _Hu pattern (note: _ is wildcard in SQL LIKE, so escape it)
    cursor.execute("SELECT id, name_vi, note_vi FROM namevi_map_places WHERE note_vi LIKE '%_Hu%' OR note_vi LIKE '%_Ngoa%'")
    rows = cursor.fetchall()
    return rows

def clean_suffix_from_name_vi(name_vi):
    """Remove _Hu or _ Ngoa suffix from name_vi"""
    import re
    # Remove " _Hu" or "_Hu" or " _Ngoa" or "_Ngoa" at the end
    # Patterns: " Huý", "_Huý", " Ngoa", "_Ngoa" at end
    # Note: The actual Vietnamese characters might vary
    patterns = [
        r' _Huý$', r'_Huý$', r' _Hu$', r'_Hu$',
        r' _Ngoa$', r'_Ngoa$',
    ]
    cleaned = name_vi
    for p in patterns:
        cleaned = re.sub(p, '', cleaned)
    return cleaned.strip()

def main():
    print('=== T454: Clean _Hu/-Ngoa Suffix from name_vi ===')
    print()
    
    # Backup database
    backup = backup_db()
    print()
    
    # Get column info
    cols = get_db_columns()
    print(f'Table columns: {cols}')
    print()
    
    # Find rows with suffixes
    conn = sqlite3.connect('data/lineage.db')
    rows = find_suffix_rows(conn)
    print(f'Found {len(rows)} rows with _Hu or _Ngoa in note_vi')
    print()
    
    # Show all rows
    print('=== All rows with suffixes ===')
    for row in rows:
        print(f'  id={row[0]}: name_vi="{row[1]}", note_vi="{row[2]}"')
    print()
    
    # Check if any rows have suffix in name_vi (not note_vi)
    print('=== Checking name_vi for suffixes ===')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name_vi FROM namevi_map_places')
    all_rows = cursor.fetchall()
    suffix_in_name_vi = []
    for row in all_rows:
        name = row[1]
        if name and ('_Hu' in name or '_Ngoa' in name or ' _Hu' in name or ' _Ngoa' in name):
            suffix_in_name_vi.append((row[0], name))
    print(f'Rows with suffix in name_vi: {len(suffix_in_name_vi)}')
    for r in suffix_in_name_vi[:10]:
        print(f'  id={r[0]}: name_vi="{r[1]}"')
    if len(suffix_in_name_vi) > 10:
        print(f'  ... and {len(suffix_in_name_vi) - 10} more')
    print()
    
    # Summarize
    print('=== Summary ===')
    print(f'Total rows in table: need to check')
    print(f'Rows with suffix in note_vi: {len(rows)}')
    print(f'Rows with suffix in name_vi: {len(suffix_in_name_vi)}')
    print()
    print('=== Recommendation ===')
    print('1. The suffix _Hu/-Ngoa is stored in note_vi column')
    print('2. name_vi may or may not contain the suffix')
    print('2. To clean: strip suffix from name_vi if present, keep note_vi as-is')
    print('3. Or: move suffix from name_vi to note_vi if in name_vi')
    print()
    
    conn.close()
    
    # Ask user what to do
    print('=== Action ===')
    print('1. Show all data and exit (no changes)')
    print('2. Create backup and propose UPDATE script')
    print('3. Exit without changes')
    
    choice = input('Choose (1-3): ')
    if choice == '1':
        print('Exiting without changes.')
    elif choice == '2':
        print('\\n=== Proposed UPDATE script ===')
        print('Would need to:')
        print('1. For each row: strip _Hu/-Ngoa from name_vi if present')
        print('2. Keep note_vi as-is (suffix already stored there)')
        print('3. Generate CSV backup of changes')
        print('4. Apply with --apply flag after Admin review')
    elif choice == '3':
        print('Exiting without changes.')

if __name__ == '__main__':
    main()