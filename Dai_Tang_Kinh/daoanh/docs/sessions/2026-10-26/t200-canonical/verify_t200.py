# -*- coding: utf-8 -*-
"""Verify T200 canonical row (read-only). Chạy: python -X utf8 verify_t200.py"""
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
DAOANH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
DB = os.path.join(DAOANH, 'data', 'lineage.db')
BK = os.path.join(DAOANH, 'data', 'backups', 'lineage_t200_20261028_115712.db')

c = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
print('BACKUP exists=%s size=%d' % (os.path.exists(BK), os.path.getsize(BK)))
b = sqlite3.connect('file:%s?mode=ro' % BK.replace('\\', '/'), uri=True)
print('BACKUP rows=%d' % b.execute('SELECT COUNT(*) FROM vn_person_authority').fetchone()[0])
print('LIVE rows=%d' % c.execute('SELECT COUNT(*) FROM vn_person_authority').fetchone()[0])
print('A001984 rows:')
for r in c.execute("SELECT id,name_vi,name_zh,dila_id,status,ttl_filename,entity_type "
                   "FROM vn_person_authority WHERE dila_id='A001984' ORDER BY id"):
    print('  ', r)
alias = c.execute("SELECT name_vi FROM vn_person_authority WHERE id='alias_A001984'").fetchone()
print('alias intact: %s' % (alias and alias[0] == 'Linh Hựu'))
rank = ("CASE status WHEN 'verified' THEN 0 WHEN 'pending' THEN 1 WHEN 'auto_ttl' THEN 2 "
        "WHEN 'alias_vi_suffix' THEN 3 WHEN 'alias_zh_match' THEN 4 ELSE 5 END")
print('LOOKUP winner:', c.execute("SELECT id,name_vi,status FROM vn_person_authority "
                                  "WHERE dila_id='A001984' ORDER BY %s ASC, id ASC LIMIT 1" % rank).fetchone())
