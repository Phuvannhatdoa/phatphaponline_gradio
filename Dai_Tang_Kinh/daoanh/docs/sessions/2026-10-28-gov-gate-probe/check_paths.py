# -*- coding: utf-8 -*-
"""Check paths for probe."""
import os
DAOANH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
print('DAOANH:', DAOANH)
print('DB file:', os.path.join(DAOANH, 'data/lineage.db'))
print('exists:', os.path.isfile(os.path.join(DAOANH, 'data/lineage.db')))
print('PROBE_DB:', os.path.join(DAOANH, 'docs', 'sessions', '2026-10-28-gov-gate-probe', 'probe.db'))
print('test file:', os.path.join(DAOANH, 'tests', 'test_b25_authority_contract.py'))
print('lineage.db table names:')
import sqlite3
con = sqlite3.connect(os.path.join(DAOANH, 'data/lineage.db'), uri=True)
for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_sources'"):
    print('  found data_sources')
print('count rows:', con.execute("SELECT COUNT(*) FROM data_sources").fetchone()[0])
con.close()
