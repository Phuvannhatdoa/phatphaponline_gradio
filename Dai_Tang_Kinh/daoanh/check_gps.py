import sqlite3
conn = sqlite3.connect('data/lineage.db')
t = conn.execute('SELECT COUNT(*) FROM places_dila WHERE geo_lat IS NOT NULL AND geo_long IS NOT NULL AND geo_lat != 0 AND geo_long != 0 AND id NOT IN (SELECT dila_id FROM geo_cross_ref)').fetchone()[0]
print('DILA places with GPS not in geo_cross_ref:', t)
sample = conn.execute('SELECT id, name_zh, geo_lat, geo_long FROM places_dila WHERE geo_lat IS NOT NULL AND geo_long IS NOT NULL AND geo_lat != 0 AND geo_long != 0 AND id NOT IN (SELECT dila_id FROM geo_cross_ref) LIMIT 3').fetchall()
for r in sample:
    print('  id=', r[0], 'name_zh=', r[1], 'lat=', r[2], 'lng=', r[3])
conn.close()