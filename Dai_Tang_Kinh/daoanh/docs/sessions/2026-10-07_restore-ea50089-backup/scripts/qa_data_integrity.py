import sqlite3
db = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')
tables = ['people', 'marcus_networks', 'lineage_edge_assertions', 'entity_claims', 'events', 'places_dila', 'translation_cache']
for t in tables:
    try:
        n = db.execute('select count(*) from %s' % t).fetchone()[0]
        print('%-28s %9d' % (t, n))
    except Exception as e:
        print(t, 'ERR', e)
rows = db.execute('select source_type, count(*) from translation_cache group by source_type').fetchall()
print('translation_cache by source_type:', dict(rows))
db.close()