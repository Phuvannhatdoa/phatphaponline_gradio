import sqlite3, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')
cols = conn.execute('PRAGMA table_info(keyword_map)').fetchall()
print('keyword_map schema:')
for c in cols:
    nn = ' NOT NULL' if c[3] else ''
    print(f'  {c[1]} ({c[2]}){nn} default={c[4]}')
total = conn.execute('SELECT COUNT(*) FROM keyword_map').fetchone()[0]
print(f'\nTotal rows: {total}')
cats = conn.execute('SELECT category, COUNT(*) FROM keyword_map GROUP BY category ORDER BY COUNT(*) DESC').fetchall()
print('By category:')
for c in cats:
    print(f'  {c[0]}: {c[1]}')
print('\nSample 5 rows:')
for r in conn.execute('SELECT * FROM keyword_map LIMIT 5').fetchall():
    print(f'  {r}')
conn.close()
