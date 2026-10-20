import sqlite3
DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
c = sqlite3.connect('file:' + DB.replace('\\','/') + '?mode=ro', uri=True)
c.row_factory = sqlite3.Row

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(t['name'])