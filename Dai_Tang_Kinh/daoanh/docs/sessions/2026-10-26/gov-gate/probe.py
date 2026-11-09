# -*- coding: utf-8 -*-
"""Probe: chứng minh gate test_e_all_sources_license_unverified bắt được lỗi chính sách.
Chỉ tạo bản sao DB trong thư mục này; KHÔNG ghi data/lineage.db.
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(DAOANH, 'tests'))
sys.path.insert(0, DAOANH)
import test_b25_authority_contract as t  # noqa: E402

SRC = os.path.join(DAOANH, 'data', 'lineage.db')

def make_copy(name):
    dst = os.path.join(HERE, name)
    if os.path.exists(dst):
        os.unlink(dst)
    src = sqlite3.connect('file:' + SRC.replace('\\', '/') + '?mode=ro', uri=True)
    d = sqlite3.connect(dst)
    src.backup(d)
    d.close()
    src.close()
    return dst

CASES = [
    ('baseline_no_change', None),
    ('wikidata_verified_and_commercial', "UPDATE data_sources SET license_verified=1, data_commercial=1 WHERE source_code='Wikidata'"),
    ('wikidata_verified_only', "UPDATE data_sources SET license_verified=1 WHERE source_code='Wikidata'"),
    ('cbeta_commercial_allowed', "UPDATE data_sources SET data_commercial=1 WHERE source_code='CBETA'"),
    ('wikidata_in_allowlist_commercial', "UPDATE data_sources SET license_verified=1, data_commercial=1 WHERE source_code='Wikidata'"),
    ('unverified_backfilled_license', "UPDATE data_sources SET license_spdx='CC-BY-4.0' WHERE source_code='DILA'"),
]

for name, sql in CASES:
    path = make_copy('probe_%s.db' % name)
    if sql:
        c = sqlite3.connect(path)
        c.execute(sql)
        c.commit()
        c.close()
    # Case đặc biệt: giả lập Admin lỡ đưa Wikidata (thương mại) vào danh sách duyệt -> rule 2 phải bắt.
    t.VERIFIED_SOURCES = {'CBETA', 'Wikidata'} if name == 'wikidata_in_allowlist_commercial' else {'CBETA'}
    try:
        t.test_e_all_sources_license_unverified(path)
        verdict = 'PASS (gate KHÔNG bắt)'
    except AssertionError as e:
        verdict = 'FAIL (gate BẮT được) -> ' + str(e)
    print('[%s] %s' % (name, verdict))
    os.unlink(path)
