import sqlite3
conn = sqlite3.connect('data/lineage.db')
gcr = conn.execute('SELECT COUNT(*) FROM geo_cross_ref').fetchone()[0]
print('geo_cross_ref rows:', gcr)
gcr_wd = conn.execute('SELECT COUNT(*) FROM geo_cross_ref WHERE wikidata_qid IS NOT NULL').fetchone()[0]
print('geo_cross_ref with wikidata_qid:', gcr_wd)
rows = conn.execute('SELECT dila_id, wikidata_qid FROM geo_cross_ref WHERE wikidata_qid IS NOT NULL LIMIT 5').fetchall()
for r in rows:
    print('  ', r)
pte = conn.execute('SELECT COUNT(*) FROM place_timeline_events').fetchone()[0]
print('place_timeline_events rows:', pte)
pte_wd = conn.execute("SELECT COUNT(*) FROM place_timeline_events WHERE source='wikidata'").fetchone()[0]
print('place_timeline_events wikidata:', pte_wd)
pd = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
print('places_dila total:', pd)
conn.close()