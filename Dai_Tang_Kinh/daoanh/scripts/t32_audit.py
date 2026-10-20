import sqlite3, re, io, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)

# 1. Current timeline stats
total_events = conn.execute('SELECT COUNT(*) FROM place_timeline_events').fetchone()[0]
unique_places = conn.execute('SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events').fetchone()[0]
total_dila = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
print(f'Timeline: {total_events} events, {unique_places} places / {total_dila} DILA = {unique_places*100/total_dila:.1f}%')

# 2. Missing pool by category
print('\n=== MISSING POOL BY note_category ===')
cats = conn.execute("""
    SELECT note_category, COUNT(*) as cnt
    FROM places_dila pd
    WHERE note IS NOT NULL AND length(note) > 30
    AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
    GROUP BY note_category
    ORDER BY cnt DESC
""").fetchall()
for c in cats:
    print(f'  {c[0]}: {c[1]}')

# 3. Sample 15 missing 寺庙 places — show FULL note to understand patterns
print('\n=== SAMPLE 15 MISSING 寺庙 PLACES (full notes) ===')
rows = conn.execute("""
    SELECT pd.id, pd.name_zh, pd.note
    FROM places_dila pd
    WHERE pd.note_category LIKE '%寺庙%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
    AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
    ORDER BY RANDOM()
    LIMIT 15
""").fetchall()
for r in rows:
    print(f'--- {r[0]} | {r[1]}')
    print(f'  {r[2]}')
    print()

# 4. Check what year-like patterns exist in missing notes
print('=== YEAR PATTERNS IN MISSING NOTES ===')
missing_notes = conn.execute("""
    SELECT pd.id, pd.note
    FROM places_dila pd
    WHERE pd.note_category LIKE '%寺庙%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
    AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
""").fetchall()

# Check various year patterns
patterns = {
    'YYYY年': r'\d{3,4}年',
    'era+year': r'[元二三四五六七八九十百]+年',
    '朝代+year': r'[唐宋元明清漢晉隋南北梁陳魏趙宋齊][^\s]{0,6}年',
    '括号year': r'（\d{3,4}年）',
    'born/died': r'生[於于]|卒[於于]|圓寂|遷化|示寂',
    'temporal refs': r'初|末|中|間',
}
for name, pat in patterns.items():
    count = 0
    examples = []
    for (pid, note) in missing_notes:
        m = re.search(pat, note or '')
        if m:
            count += 1
            if len(examples) < 3:
                examples.append(f'{pid}: ...{note[max(0,m.start()-20):m.end()+20]}...')
    print(f'  {name}: {count}/{len(missing_notes)} notes match')
    for ex in examples:
        print(f'    {ex}')

# 5. Check what source data exists for timeline
print('\n=== EXISTING TIMELINE SOURCES ===')
sources = conn.execute("""
    SELECT source, COUNT(*) as cnt
    FROM place_timeline_events
    GROUP BY source ORDER BY cnt DESC
""").fetchall()
for s in sources:
    print(f'  {s[0]}: {s[1]}')

# 6. Check ETA table coverage
print('\n=== ERA TABLE COVERAGE ===')
from scripts.dila_era_name_extract import ERA_TABLE
print(f'ERA_TABLE has {len(ERA_TABLE)} era names')

# 7. Count missing notes with dynasty names
print('\n=== DYNASTY NAME HITS IN MISSING ===')
DYNASTIES = ['漢', '魏', '晉', '隋', '唐', '宋', '元', '明', '清', '民國']
for d in DYNASTIES:
    cnt = conn.execute("""
        SELECT COUNT(*) FROM places_dila pd
        WHERE pd.note_category LIKE '%寺庙%'
        AND pd.note LIKE ?
        AND pd.note IS NOT NULL AND length(pd.note) > 30
        AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
    """, (f'%{d}%',)).fetchone()[0]
    if cnt > 0:
        print(f'  {d}: {cnt}')

# 8. 地點 category with Buddhist keywords
print('\n=== 地點 + BUDDHIST KEYWORDS (secondary pool) ===')
diem_buddhist = conn.execute("""
    SELECT COUNT(*) FROM places_dila pd
    WHERE pd.note_category = '地點'
    AND (pd.note LIKE '%寺%' OR pd.note LIKE '%塔%' OR pd.note LIKE '%佛%')
    AND pd.note NOT LIKE '%故宮%' AND pd.note NOT LIKE '%皇%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
""").fetchone()[0]
diem_with_year = conn.execute("""
    SELECT COUNT(*) FROM places_dila pd
    WHERE pd.note_category = '地點'
    AND (pd.note LIKE '%寺%' OR pd.note LIKE '%塔%' OR pd.note LIKE '%佛%')
    AND pd.note NOT LIKE '%故宮%' AND pd.note NOT LIKE '%皇%'
    AND pd.note LIKE '%年%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
""").fetchone()[0]
print(f'  Buddhist 地點 total: {diem_buddhist}, with year: {diem_with_year}')

conn.close()
