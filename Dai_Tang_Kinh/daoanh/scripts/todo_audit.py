import sqlite3, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')

print('=== T27 DEPENDENCY CHECK ===')
for t in ['entity_hub', 'entity_claims', 'entity_source_ids', 'zqlocal_content']:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: {cnt} rows')
    except Exception as e:
        print(f'  {t}: MISSING - {e}')

print('\n=== T16 DEPENDENCY (raw_tei) ===')
try:
    cnt = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE raw_tei IS NOT NULL").fetchone()[0]
    print(f'  cbeta_catalog_vn with raw_tei: {cnt}')
except Exception as e:
    print(f'  raw_tei column: {e}')

print('\n=== T11 DEPENDENCY (passage_vi) ===')
try:
    cnt = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE passage_vi IS NOT NULL AND passage_vi != ''").fetchone()[0]
    print(f'  cbeta_catalog_vn with passage_vi: {cnt}')
except Exception as e:
    print(f'  passage_vi column: {e}')

print('\n=== KANRIPO STATE ===')
try:
    cnt = conn.execute('SELECT COUNT(*) FROM kanripo_catalog').fetchone()[0]
    print(f'  kanripo_catalog: {cnt} rows')
    rows = conn.execute('SELECT * FROM kanripo_catalog').fetchall()
    for r in rows:
        print(f'    {r}')
except Exception as e:
    print(f'  Error: {e}')

print('\n=== 84000/VRI STATE ===')
for t in ['eight_four_thousand', 'eight_four_thousand_place_map', 'vri_tipitaka_catalog', 'vri_place_mapping', 'vri_cached_texts']:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: {cnt} rows')
    except Exception as e:
        print(f'  {t}: {e}')

# Check all tables
print('\n=== ALL TABLES ===')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f'Total tables: {len(tables)}')
for t in tables:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
        if cnt > 0:
            print(f'  {t[0]}: {cnt}')
    except:
        pass

conn.close()
