import sqlite3,sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(__import__('pathlib').Path.cwd()))
from src_python.ttl_db_export import raw_dila
c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);c.row_factory=sqlite3.Row
for aid in ['A009489','A003703','A010041','A000174','A008986','A001984','A009491']:
 r=raw_dila(c,aid);n=ET.fromstring(r['raw_text']);t='{http://www.tei-c.org/ns/1.0}'
 print(aid,r['sha256'],[''.join(x.itertext()).strip() for x in n.findall(t+'persName')]);print('\n'.join(''.join(x.itertext()).strip() for x in n.findall(t+'note') if x.get('type') in ('sect','concise')))
