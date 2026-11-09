import sqlite3
conn = sqlite3.connect('data/lineage.db')
# Check dila_bio_nexus
try:
    cur = conn.execute("SELECT * FROM dila_bio_nexus LIMIT 1")
    rows = cur.fetchall()
    if rows:
        cols = [d[0] for d in cur.description]
        print('dila_bio_nexus exists, columns:', cols)
    else:
        print('dila_bio_nexus exists but empty')
except Exception as e:
    print('dila_bio_nexus NOT FOUND:', e)
# Check nexus_events count
count = conn.execute("SELECT COUNT(*) FROM nexus_events").fetchone()[0]
print('nexus_events count:', count)
# Check nexus_events with event_year
with_year = conn.execute("SELECT COUNT(*) FROM nexus_events WHERE event_year IS NOT NULL").fetchone()[0]
print('nexus_events with event_year:', with_year)
conn.close()