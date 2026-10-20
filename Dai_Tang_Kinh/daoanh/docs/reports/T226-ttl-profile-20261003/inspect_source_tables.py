import sqlite3
c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True)
for row in c.execute("select name from sqlite_master where type='table'"):
 n=row[0]
 if any(x in n.lower() for x in ['marcus','claim','relation','person','edge']):
  print(n,[(r[1],r[2]) for r in c.execute('pragma table_info('+n+')')])
