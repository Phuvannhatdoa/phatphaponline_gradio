import sqlite3
conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')

# Check what is_primary values we get from the JOIN
print('--- JOIN test (correct indices) ---')
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
    print(f"  id={r[0]} teacher={r[1]} disciple={r[2]} is_primary={r[5]} ttl={r[3]} agreeing={r[4]}")

# Also check without ORDER BY
print('\\n--- JOIN test no ORDER ---')
rows5 = conn.execute("""
    SELECT c.id, c.teacher_id, c.disciple_id, c.ttl_asserted, c.agreeing_source_count,
           COALESCE(lpt.is_primary, 0) AS is_primary_val
    FROM lineage_edge_consensus c
    LEFT JOIN lineage_primary_teacher lpt
       ON lpt.teacher_id=c.teacher_id AND lpt.disciple_id=c.disciple_id
    WHERE c.disciple_id='A001984' AND c.relation_type='dharma_transmission'
""").fetchall()
for r in rows5:
    print(f"  id={r[0]} teacher={r[1]} disciple={r[2]} is_primary={r[5]} ttl={r[3]} agreeing={r[4]}")

conn.close()