import sqlite3
conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')

# Check lineage_edge_consensus for disciple A001984
rows = conn.execute("SELECT * FROM lineage_edge_consensus WHERE disciple_id='A001984' AND relation_type='dharma_transmission'").fetchall()
print(f'lineage_edge_consensus for A001984 (disciple): {len(rows)} rows')
for r in rows[:10]:
    print(f"  id={r[0]} teacher_id={r[1]} disciple_id={r[2]} source_badge={r[3]} ttl_asserted={r[4]} consensus_status={r[5]}")

# Check for teacher A001897
rows2 = conn.execute("SELECT * FROM lineage_edge_consensus WHERE teacher_id='A001897' AND relation_type='dharma_transmission'").fetchall()
print(f'\\nlineage_edge_consensus for A001897 (teacher): {len(rows2)} rows')
for r in rows2[:5]:
    print(f"  id={r[0]} teacher_id={r[1]} disciple_id={r[2]} source_badge={r[3]}")

# Check for A010527
rows3 = conn.execute("SELECT * FROM lineage_edge_consensus WHERE teacher_id='A010527' AND relation_type='dharma_transmission'").fetchall()
print(f'\\nlineage_edge_consensus for A010527 (teacher): {len(rows3)} rows')
for r in rows3[:5]:
    print(f"  id={r[0]} teacher_id={r[1]} disciple_id={r[2]} source_badge={r[3]}")

# Check what is_primary values we get from the JOIN
print('\\n--- JOIN test ---')
rows4 = conn.execute("""
    SELECT c.id, c.teacher_id, c.disciple_id, c.ttl_asserted, c.agreeing_source_count,
           COALESCE(lpt.is_primary, 0) AS is_primary_val
    FROM lineage_edge_consensus c
    LEFT JOIN lineage_primary_teacher lpt
       ON lpt.teacher_id=c.teacher_id AND lpt.disciple_id=c.disciple_id
    WHERE c.disciple_id='A001984' AND c.relation_type='dharma_transmission'
    ORDER BY is_primary_val DESC
""").fetchall()
for r in rows4:
    print(f"  id={r[0]} teacher={r[1]} is_primary={r[4]} ttl={r[3]} agreeing={r[5]}")

conn.close()