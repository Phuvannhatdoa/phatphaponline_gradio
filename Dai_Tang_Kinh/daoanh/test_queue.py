#!/usr/bin/env python3
import re
import sqlite3 as sql
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SQLITE_DB = os.path.join(DATA_DIR, 'lineage.db')
TTL_OLD_DIR = os.path.join(DATA_DIR, 'ttl', 'old')

def get_db():
    conn = sql.connect(SQLITE_DB)
    conn.row_factory = sql.Row
    return conn

# Test 1: List TTL files
print("=== TTL Files ===")
files = [f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')]
print(files)

# Test 2: Extract ID from first file
print("\n=== Extract ID ===")
filename = files[0]
print(f"File: {filename}")

with open(os.path.join(TTL_OLD_DIR, filename), 'r') as f:
    content = f.read()

match = re.search(r'<ex:monk/([^>]+)>', content)
if match:
    monk_id = match.group(1)
    print(f"Monk ID from TTL: {monk_id}")
    
    # Try to find in DB
    conn = get_db()
    name_search = monk_id.replace('_', ' ').title()
    print(f"Searching for: {name_search}")
    
    row = conn.execute(
        "SELECT id, name_vi, name_zh, sect FROM people WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 3",
        (f"%{name_search}%", f"%{monk_id}%")
    ).fetchall()
    print("DB Results:")
    for r in row:
        print(f"  {r['id']}: {r['name_vi']} ({r['name_zh']}) - {r['sect']}")
    conn.close()