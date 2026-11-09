import sqlite3
conn = sqlite3.connect(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db')
# Check if table has rows
count = conn.execute("SELECT COUNT(*) FROM lineage_primary_teacher").fetchone()[0]
print(f'lineage_primary_teacher count: {count}')

# Check specific records
rows = conn.execute("SELECT * FROM lineage_primary_teacher WHERE teacher_id='A001897'").fetchall()
print(f'A001897 rows: {rows}')

rows = conn.execute("SELECT * FROM lineage_primary_teacher WHERE disciple_id='A001984'").fetchall()
print(f'A001984 rows: {rows}')

# Check A010527
rows = conn.execute("SELECT * FROM lineage_primary_teacher WHERE teacher_id='A010527'").fetchall()
print(f'A010527 rows: {rows}')

conn.close()