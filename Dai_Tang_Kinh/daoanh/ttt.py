import sqlite3
conn = sqlite3.connect('data/lineage.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', tables)
for t in tables:
    tname = t[0]
    cols = [d[0] for d in conn.execute("SELECT * FROM " + tname + " LIMIT 1").description]
    print(f'Columns in {tname}:', cols)
    r = conn.execute("SELECT * FROM " + tname + " LIMIT 3").fetchall()
    print('Sample:', r)
conn.close()