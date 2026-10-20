import sys,runpy
from pathlib import Path
D=Path.cwd()/'daoanh';sys.path.insert(0,str(D/'data/backups/T215-fix-sync-20261002/python-deps'))
a=runpy.run_path(str(D/'scripts/audit_ttl_lineage_local.py'));a['run'].__globals__['OUT']=D/'docs/reports/T215-closeout-20261003/after-audit';a['run']()
