import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'daoanh/data/backups/T215-fix-sync-20261002/python-deps'))
from rdflib import Graph
for p in (Path.cwd()/'daoanh/docs/reports/T215-eight-uri-20261003/prepared').glob('*.ttl'):
 try:Graph().parse(data=p.read_text(encoding='utf-8-sig'),format='turtle');print(p.name,'OK')
 except Exception as e:print(p.name,str(e),repr(e.args),getattr(e,'_i',None))
