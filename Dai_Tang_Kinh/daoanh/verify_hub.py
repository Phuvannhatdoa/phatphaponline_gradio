import sqlite3

conn = sqlite3.connect('data/lineage.db')

# Quick verification
hub_ids = conn.execute('SELECT MIN(entity_id), MAX(entity_id), COUNT(*) FROM entity_hub').fetchone()
src_ids = conn.execute('SELECT MIN(entity_id), MAX(entity_id), COUNT(*) FROM entity_source_ids').fetchone()
orphan_count = conn.execute('SELECT COUNT(*) FROM entity_source_ids WHERE entity_id NOT IN (SELECT entity_id FROM entity_hub)').fetchone()[0]
verified = conn.execute('SELECT COUNT(*) FROM entity_source_ids WHERE verified = 1').fetchone()[0]
status_counts = conn.execute('SELECT match_status, COUNT(*) FROM entity_source_ids GROUP BY match_status').fetchall()

print(f"entity_hub: min={hub_ids[0]}, max={hub_ids[1]}, count={hub_ids[2]}")
print(f"entity_source_ids: min={src_ids[0]}, max={src_ids[1]}, count={src_ids[2]}")
print(f"Orphaned rows: {orphan_count}")
print(f"Verified rows: {verified}")
print(f"match_status distribution: {status_counts}")

conn.close()