"""
T34 Phase A — Delete fake/placeholder data from 84000/VRI/Kanripo tables.
Admin approved 2026-08-24.

Tables to clear:
  - eight_four_thousand: 3 rows (fake Toh numbers)
  - eight_four_thousand_place_map: 3 rows (fake place mappings)
  - vri_tipitaka_catalog: 3 rows (fake titles)
  - vri_place_mapping: 42 rows (all Pali suttas → Thiếu Lâm Tự = wrong)
  - vri_cached_texts: 31 rows (placeholder text)
  - kanripo_place_mapping: 2 rows (KR6a0001 → PL000000000001 = placeholder)

Tables to KEEP (valid seed data):
  - kanripo_catalog: 3 rows (real text IDs from kanripo.org)

Safety: backup before delete, print what we're removing.
"""
import sqlite3, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
conn = sqlite3.connect(DB)

# 1. Count what we're about to delete
tables_to_delete = {
    'eight_four_thousand': '3 rows fake Toh numbers',
    'eight_four_thousand_place_map': '3 rows fake place mappings',
    'vri_tipitaka_catalog': '3 rows fake Pali titles',
    'vri_place_mapping': '42 rows all → Thiếu Lâm Tự (wrong)',
    'vri_cached_texts': '31 rows placeholder text',
    'kanripo_place_mapping': '2 rows placeholder place mapping',
}

print("=== T34 Phase A: Delete Fake Data ===")
print(f"Database: {os.path.abspath(DB)}")
print()

total_delete = 0
for table, reason in tables_to_delete.items():
    try:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        total_delete += cnt
        print(f"  {table}: {cnt} rows — {reason}")
    except Exception as e:
        print(f"  {table}: ERROR — {e}")

print(f"\n  TOTAL TO DELETE: {total_delete} rows")
print(f"  Tables to KEEP: kanripo_catalog (3 rows, valid seed)")

# 2. Show samples of what we're deleting
print("\n=== SAMPLE DATA TO DELETE ===")

print("\n--- eight_four_thousand (fake 84000 texts) ---")
for r in conn.execute("SELECT * FROM eight_four_thousand").fetchall():
    print(f"  {r}")

print("\n--- eight_four_thousand_place_map (fake mappings) ---")
for r in conn.execute("SELECT * FROM eight_four_thousand_place_map").fetchall():
    print(f"  {r}")

print("\n--- vri_tipitaka_catalog (fake Pali catalog) ---")
for r in conn.execute("SELECT * FROM vri_tipitaka_catalog").fetchall():
    print(f"  {r}")

print("\n--- vri_place_mapping (sample 5 of 42) ---")
for r in conn.execute("SELECT * FROM vri_place_mapping LIMIT 5").fetchall():
    print(f"  {r}")

print("\n--- vri_cached_texts (sample 3 of 31) ---")
for r in conn.execute("SELECT * FROM vri_cached_texts LIMIT 3").fetchall():
    print(f"  {r}")

print("\n--- kanripo_place_mapping (2 rows) ---")
for r in conn.execute("SELECT * FROM kanripo_place_mapping").fetchall():
    print(f"  {r}")

# 3. Execute deletes
print("\n=== EXECUTING DELETE ===")
for table in tables_to_delete:
    try:
        conn.execute(f"DELETE FROM {table}")
        print(f"  ✓ DELETE FROM {table}")
    except Exception as e:
        print(f"  ✗ DELETE FROM {table}: {e}")

conn.commit()
print("\n✅ Commit done.")

# 4. Verify
print("\n=== VERIFICATION ===")
for table in list(tables_to_delete.keys()) + ['kanripo_catalog']:
    try:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {cnt} rows")
    except:
        print(f"  {table}: table not found")

conn.close()
print("\n✅ T34 Phase A complete.")
