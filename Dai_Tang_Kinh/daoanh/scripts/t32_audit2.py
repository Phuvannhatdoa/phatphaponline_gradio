import sqlite3, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)

# 1. What note_category values contain 寺?
print('=== note_category containing 寺 ===')
rows = conn.execute("""
    SELECT DISTINCT note_category FROM places_dila
    WHERE note_category LIKE '%寺%'
""").fetchall()
for r in rows:
    print(f'  [{r[0]}]')

# 2. How many 寺廟 places have notes > 30 chars AND no timeline?
print('\n=== 寺廟 places with notes but no timeline ===')
for cat_pat in ['%寺廟%', '%寺庙%', '%寺%']:
    cnt = conn.execute("""
        SELECT COUNT(*) FROM places_dila pd
        WHERE pd.note_category LIKE ?
        AND pd.note IS NOT NULL AND length(pd.note) > 30
        AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
    """, (cat_pat,)).fetchone()[0]
    print(f'  LIKE "{cat_pat}": {cnt}')

# 3. Sample 寺 places with notes but no timeline
print('\n=== SAMPLE 寺 PLACES WITH NOTES, NO TIMELINE ===')
rows = conn.execute("""
    SELECT pd.id, pd.name_zh, pd.note_category, substr(pd.note, 1, 300)
    FROM places_dila pd
    WHERE pd.note_category LIKE '%寺%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
    AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
    LIMIT 10
""").fetchall()
for r in rows:
    print(f'--- {r[0]} | {r[1]} | cat=[{r[2]}]')
    print(f'  {r[3]}')
    print()

# 4. Check how many total 寺 places with notes
print('=== TOTAL 寺 PLACES WITH NOTES ===')
cnt_all = conn.execute("""
    SELECT COUNT(*) FROM places_dila pd
    WHERE pd.note_category LIKE '%寺%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
""").fetchone()[0]
cnt_has_timeline = conn.execute("""
    SELECT COUNT(*) FROM places_dila pd
    WHERE pd.note_category LIKE '%寺%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
    AND EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
""").fetchone()[0]
print(f'  Total with notes: {cnt_all}')
print(f'  Already has timeline: {cnt_has_timeline}')
print(f'  Missing: {cnt_all - cnt_has_timeline}')

# 5. What existing timeline sources cover? Show sample of what was extracted
print('\n=== SAMPLE EXTRACTED TIMELINE EVENTS ===')
rows = conn.execute("""
    SELECT pt.dila_id, pt.year, pt.label_zh, pt.source, pt.confidence
    FROM place_timeline_events pt
    WHERE pt.source = 'dila_note'
    LIMIT 5
""").fetchall()
for r in rows:
    print(f'  {r[0]}: year={r[1]}, label={r[2]}, source={r[3]}, conf={r[4]}')

# 6. Check what the ETL script already extracted
print('\n=== EXISTING ETL SCRIPTS ===')
import os
scripts_dir = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\scripts'
for f in os.listdir(scripts_dir):
    if 'dila' in f.lower() or 'era' in f.lower() or 'timeline' in f.lower() or 't21' in f.lower():
        print(f'  {f}')

conn.close()
