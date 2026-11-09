import sqlite3

conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')

# Find cases where lineage_primary_teacher.is_primary=1 differs from the "latest" DILA edge
# (i.e., there are multiple edges for the same disciple, and is_primary=1 is not the highest ID)

# Step 1: Find all disciples with multiple edges in lineage_edge_consensus
disciple_edges = conn.execute("""
    SELECT disciple_id, COUNT(*) as edge_count
    FROM lineage_edge_consensus
    WHERE relation_type='dharma_transmission'
    GROUP BY disciple_id
    HAVING edge_count > 1
    ORDER BY disciple_id
""").fetchall()

print(f'Disciples with multiple edges: {len(disciple_edges)}')
print()

# Step 2: For each such disciple, check lineage_primary_teacher is_primary values
cases_found = 0
test_cases = []

for disc_row in disciple_edges:
    did = disc_row[0]
    edge_count = disc_row[1]
    
    # Get all edges for this disciple
    edges = conn.execute("""
        SELECT id, teacher_id, dila_asserted, ttl_asserted, agreeing_source_count
        FROM lineage_edge_consensus
        WHERE disciple_id=? AND relation_type='dharma_transmission'
        ORDER BY id DESC
    """, (did,)).fetchall()
    
    # Get lineage_primary_teacher entries for this disciple
    pt_entries = conn.execute("""
        SELECT teacher_id, is_primary, evidence_source
        FROM lineage_primary_teacher
        WHERE disciple_id=?
    """, (did,)).fetchall()
    
    # Get the "latest" DILA edge (highest id)
    latest_edge = edges[0] if edges else None
    latest_teacher = latest_edge[1] if latest_edge else None
    
    # Check if any PT entry has is_primary=1 different from latest teacher
    has_primary_1_diff = False
    pt_is_primary_1_teachers = []
    for pt in pt_entries:
        if pt[1] == 1:  # is_primary=1
            pt_is_primary_1_teachers.append(pt[0])
            if pt[0] != latest_teacher:
                has_primary_1_diff = True
    
    if has_primary_1_diff or len(pt_is_primary_1_teachers) > 0:
        # Get teacher names
        teachers_info = []
        for pt in pt_entries:
            tname = conn.execute("SELECT name_vi FROM people WHERE id=?", (pt[0],)).fetchone()
            teachers_info.append(f"teacher={pt[0]}({pt[0]}) name={tname[0] if tname else 'N/A'} is_primary={pt[1]} evidence={pt[2]}")
        
        latest_teacher_name = conn.execute("SELECT name_vi FROM people WHERE id=?", (latest_teacher,)).fetchone()
        
        print(f"Disciple: A{did} ({len(edges)} edges)")
        print(f"  Latest DILA edge (id highest): teacher=A{latest_teacher_name[0] if latest_teacher_name else 'N/A'} ({latest_teacher})")
        print(f"  lineage_primary_teacher entries: {len(pt_entries)}")
        for t in teachers_info:
            print(f"    {t}")
        print(f"  is_primary=1 differs from latest DILA edge: {has_primary_1_diff}")
        print()
        
        test_cases.append({
            'disciple': did,
            'latest_teacher': latest_teacher,
            'primary_1_teachers': pt_is_primary_1_teachers,
            'has_diff': has_primary_1_diff
        })
        cases_found += 1
    
    if cases_found >= 7:  # A001984 + 6 more
        break

conn.close()
print(f"Total test cases found: {cases_found}")