import sqlite3, os
p = os.path.join('data', 'lineage.db')
conn = sqlite3.connect('file:%s?mode=ro' % p.replace('\\', '/'), uri=True)
cur = conn.cursor()
cur.execute("""
SELECT teacher_id, disciple_id, dila_asserted, marcus_asserted, ttl_asserted,
       agreeing_source_count, consensus_status, source_badge
FROM lineage_edge_consensus
WHERE ttl_asserted = 1
LIMIT 8
""")
print('--- TTL edges (show red + agree) ---')
for r in cur.fetchall():
    print(r)

cur.execute("""
SELECT teacher_id, disciple_id, dila_asserted, marcus_asserted, ttl_asserted,
       agreeing_source_count, consensus_status
FROM lineage_edge_consensus
WHERE (dila_asserted + marcus_asserted + ttl_asserted) = 2
  AND teacher_id IN ('A004980','A009460')
""")
print('--- 2-source edges among the two test ids ---')
for r in cur.fetchall():
    print(r)

cur.execute("""
SELECT teacher_id, COUNT(*) c FROM lineage_edge_consensus
WHERE ttl_asserted = 1 GROUP BY teacher_id ORDER BY c DESC LIMIT 5
""")
print('--- teachers with most TTL edges ---')
for r in cur.fetchall():
    print(r)
conn.close()
