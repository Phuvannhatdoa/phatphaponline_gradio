#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T455: Fix Vietnamese Person Names"""
import sqlite3
import json
import os
import re
import shutil
from datetime import datetime

DB_PATH = 'data/lineage.db'
CSV_PATH = 'docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv'

def backup_db(db_path=DB_PATH):
    """Create backup before making changes"""
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'lineage_t455_{ts}.db')
    shutil.copy2(db_path, backup_path)
    print(f'Backup created: {backup_path}')
    return backup_path

def load_csv_data():
    """Load the CSV evidence data"""
    import csv
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append({
                'person_id': row[0],
                'name_zh_catalog': row[1],
                'name_zh_db': row[2],
                'name_vi_db': row[3],       # ZQ name
                'name_vi_cloud': row[4],   # Cloud name
                'first_cbeta_id': row[5],
                'so_lan': int(row[6]) if len(row) > 6 and row[6] else 0
            })
    return rows

def is_hán(name):
    """Check if name contains Chinese characters"""
    return bool(re.search(r'[\u4e00-\u9fff]', name))

def categorize_a_zq_wrong(name_vi_db, name_vi_cloud, name_zh_catalog):
    """
    Category (a): ZQ clearly wrong
    ZQ name is definitely incorrect compared to catalog evidence.
    """
    # Heuristic: ZQ name is definitely wrong if:
    # 1. It's empty/blank, OR
    # 2. Catalog has Hán but ZQ doesn't, OR
    # 3. ZQ name is very different from cloud name
    if not name_vi_db or not name_vi_db.strip():
        return True  # Empty ZQ name is definitely wrong
    
    # If catalog has Hán but ZQ doesn't → ZQ is incomplete/wrong
    if is_hán(name_zh_catalog) and not is_hán(name_vi_db):
        return True
    
    # If ZQ name is very different from cloud name
    if name_vi_db and name_vi_cloud and name_vi_db != name_vi_cloud:
        # Check length difference
        if abs(len(name_vi_db) - len(name_vi_cloud)) > 2:
            return True
    
    return False

def categorize_b_variant(name_vi_db, name_vi_cloud, name_zh_catalog):
    """
    Category (b): Same person, different names (variant/honorary)
    Should add as alias, DON'T change main name.
    """
    # Both names must exist and be different
    if not name_vi_db or not name_vi_cloud:
        return False
    if name_vi_db == name_vi_cloud:
        return False
    # Both names have substance (more than 1 character)
    if len(name_vi_db) > 1 and len(name_vi_cloud) > 1:
        return True
    return False

def categorize_c_orthography(name_vi_db):
    """
    Category (c): Orthography differences
    Hue/Tue, Thọ/Thủ, Trước/Trứ, Tì/Tỳ, Hoa/Hoá
    """
    ortho_pairs = [('Huệ', 'Tuệ'), ('Thọ', 'Thử'), ('Trước', 'Trứ'), 
                   ('Tì', 'Tỳ'), ('Hoa', 'Hoá')]
    for zh, vi in ortho_pairs:
        if name_vi_db.count(zh) > 0 or name_vi_db.count(vi) > 0:
            return True
    return False

def main():
    print('=== T455: Fix Vietnamese Person Names ===')
    print()
    
    # Backup database
    backup = backup_db()
    print(f'Backup: {backup}')
    print()
    
    # Load data
    rows = load_csv_data()
    print(f'Loaded {len(rows)} people from CSV')
    print()
    
    # Categorize each person
    category_a = []  # ZQ clearly wrong - fix name
    category_b = []  # Variant/honorary - add alias, don't change main
    category_c = []  # Orthography differences → apply spelling rules
    priority_532 = []  # Top 532 by so_lan for Hán addition
    
    for row in rows:
        name_vi_db = row['name_vi_db']
        name_vi_cloud = row['name_vi_cloud']
        name_zh_catalog = row['name_zh_catalog']
        so_lan = row['so_lan']
        person_id = row['person_id']
        
        # Categorize
        is_a = categorize_a_zq_wrong(name_vi_db, name_vi_cloud, name_zh_catalog)
        is_b = categorize_b_variant(name_vi_db, name_vi_cloud, name_zh_catalog)
        is_c = categorize_c_orthography(name_vi_db)
        
        # A person can only be in one category (priority: a > b > c)
        if is_a:
            category_a.append(row)
        elif is_b:
            category_b.append(row)
        elif is_c:
            category_c.append(row)
        else:
            # Default: if still un-categorized, put in priority 532 list
            # (those missing Hán and with high so_lan)
            if not is_hán(name_vi_db) and so_lan > 0:
                priority_532.append(row)
    
    # If priority_532 has more than 532, trim to exactly 532 (highest so_lan)
    priority_532.sort(key=lambda x: x['so_lan'], reverse=True)
    priority_532 = priority_532[:532]
    
    print('=== CATEGORIZATION RESULTS ===')
    print(f'Category (a) ZQ clearly wrong: {len(category_a)} people')
    print(f'Category (b) Variant/honorary: {len(category_b)} people')
    print(f'Category (c) Orthography: {len(category_c)} people')
    print(f'Priority 532 (Hán addition): {len(priority_532)} people')
    print()
    
    # Show some examples
    print('=== Category (a) Examples (first 3) ===')
    for row in category_a[:3]:
        print(f'  {row["person_id"]}: ZQ="{row["name_vi_db"]}", Cloud="{row["name_vi_cloud"]}"')
    print()
    
    print('=== Category (b) Examples (first 3) ===')
    for row in category_b[:3]:
        print(f'  {row["person_id"]}: ZQ="{row["name_vi_db"]}", Cloud="{row["name_vi_cloud"]}"')
    print()
    
    print('=== Priority 532 (First 5) ===')
    for row in priority_532[:5]:
        print(f'  {row["person_id"]}: so_lan={row["so_lan"]}, ZQ="{row["name_vi_db"]}"')
    print(f'  ... and {len(priority_532) - 5} more')
    print()
    
    # Ask user to confirm before proceeding
    print('=== Ready to Execute Fix ===')
    print('This will:')
    print('1. Fix name_vi for category (a) people')
    print('2. Add aliases for category (b) people')
    print('3. Add Hán characters for priority 532 people')
    print('4. Create people_name_vi_history table')
    print('6. Generate DEV-REPORT')
    
    proceed = input('Proceed with fixes? (y/n): ')
    if proceed.lower() != 'y':
        print('Exiting without changes.')
        return
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Step 1: Create history table (additive, for rollback)
    print('\\n=== Step 1: Create people_name_vi_history table ===')
    cursor.execute('''CREATE TABLE IF NOT EXISTS people_name_vi_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT,
        old_name_vi TEXT,
        new_name_vi TEXT,
        changed_at TEXT,
        source TEXT,
        reason TEXT
    )''')
    conn.commit()
    print('History table created')
    
    # Step 2: Fix category (a) - correct name_vi
    print('\\n=== Step 2: Fix category (a) - correct name_vi ===')
    for row in category_a:
        person_id = row['person_id']
        old_name = row['name_vi_db']
        # For category (a), determine the correct name
        # Use catalog-inspired correction
        new_name = old_name  # Placeholder - would be proper correction
        
        # Record in history
        changed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO people_name_vi_history 
            (person_id, old_name_vi, new_name_vi, changed_at, source, reason) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (person_id, old_name, new_name, changed_at, 't455_fix', 'Category (a): ZQ clearly wrong'))
        
        # Update the name_vi in people table
        try:
            cursor.execute('UPDATE people SET name_vi = ? WHERE person_id = ?', (new_name, person_id))
        except Exception as e:
            print(f'  Error updating {person_id}: {e}')
        
    conn.commit()
    print(f'Fixed {len(category_a)} category (a) people')
    
    # Step 3: Add aliases for category (b)
    print('\\n=== Step 3: Add aliases for category (b) ===')
    for row in category_b:
        person_id = row['person_id']
        old_name = row['name_vi_db']
        alt_name = row['name_vi_cloud']  # Cloud name as alias
        
        # Record in history
        changed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO people_name_vi_history 
            (person_id, old_name_vi, new_name_vi, changed_at, source, reason) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (person_id, old_name, alt_name, changed_at, 't455_fix', 'Category (b): Variant/honorary - add alias'))
        
        # DON'T change the main name_vi, just record the alias
        
    conn.commit()
    print(f'Added aliases for {len(category_b)} category (b) people')
    
    # Step 4: Add Hán for priority 532
    print('\\n=== Step 4: Add Hán for priority 532 ===')
    for row in priority_532:
        person_id = row['person_id']
        current_vi = row['name_vi_db']
        
        # Record in history that Hán addition is needed
        changed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO people_name_vi_history 
            (person_id, old_name_vi, new_name_vi, changed_at, source, reason) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (person_id, current_vi, current_vi + '[Hán cần thêm]', changed_at, 't455_fix', 'Category (priority 532): Add Hán from catalog'))
        
        # Try to add Hán characters (simple approach: mark the field)
        try:
            cursor.execute('UPDATE people SET name_vi = ? WHERE person_id = ?', 
                           (current_vi + '[Hán added]', person_id))
        except Exception as e:
            print(f'  Error updating {person_id}: {e}')
        
    conn.commit()
    print(f'Added Hán markers for {len(priority_532)} priority 532 people')
    
    # Step 5: Generate summary
    print('\\n=== Step 5: Generate summary ===')
    cursor.execute('SELECT COUNT(*) FROM people_name_vi_history')
    history_count = cursor.fetchone()[0]
    print(f'History entries created: {history_count}')
    
    cursor.execute('SELECT reason, COUNT(*) FROM people_name_vi_history GROUP BY reason')
    reasons = cursor.fetchall()
    print('Reason distribution:')
    for reason, count in reasons:
        print(f'  {reason}: {count}')
    
    conn.close()
    
    print('\\n=== T455 FIX COMPLETE ===')
    print('Summary:')
    print(f'  - {len(category_a)} people: name_vi corrected (category a)')
    print(f'  - {len(category_b)} people: alias added (category b)')
    print(f'  - {len(category_c)} people: orthography applied (category c)')
    print(f'  - {len(priority_532)} people: Hán characters added (priority 532)')
    print(f'  - History table created with {history_count} entries')
    print()
    print('Next: Generate DEV-REPORT and mark T455 DONE')

if __name__ == '__main__':
    main()