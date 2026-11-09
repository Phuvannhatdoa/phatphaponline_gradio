import sqlite3
conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
if ('lineage_primary_teacher',) in [t[0] for t in tables]:
    count = conn.execute('SELECT COUNT(*) FROM lineage_primary_teacher').fetchone()[0]
    print(f'lineage_primary_teacher count: {count}')
    rows = conn.execute("SELECT * FROM lineage_primary_teacher WHERE teacher_id='A001897' OR disciple_id='A001984'").fetchall()
    print(f'A001897/A001984 rows:', rows)
else:
    print('lineage_primary_teacher table MISSING')
conn.close()