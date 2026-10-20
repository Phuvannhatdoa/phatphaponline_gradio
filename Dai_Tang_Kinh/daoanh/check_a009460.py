import sqlite3
DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
c = sqlite3.connect('file:' + DB.replace('\\','/') + '?mode=ro', uri=True)
c.row_factory = sqlite3.Row

# Check if there's a DILA_XML record
row = c.execute("SELECT * FROM dila_xml WHERE id=?", ('A009460',)).fetchone()
if row:
    print('Found in dila_xml:', dict(row))
else:
    print('Not in dila_xml table')

# Check tables
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%dila%'").fetchall()
print('DILA tables:', tables)

# Check if people_full exists
row = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='people_full'").fetchone()
print('people_full table:', row)

# Check if DILA_XML source exists in records
row = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dila_xml'").fetchone()
print('dila_xml table:', row)