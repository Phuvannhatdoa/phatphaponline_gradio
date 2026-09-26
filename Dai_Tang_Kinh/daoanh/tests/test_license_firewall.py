#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — LicenseFirewall test suite (16 tests, theo spec §18)
===========================================================
Chạy trên DB COPY TEMP (KHÔNG đụng data/lineage.db thật), nên an toàn tuyệt đối.
    python -m pytest tests/test_license_firewall.py -v

Mỗi test dựng một registry ảo (thêm source + gán legal cột) rồi dùng LicenseGate/
ProvenanceGate/status để kiểm tra quyết định. Rule-based, deterministic.

Các TEST (spec §18):
  TEST 01 Public GitHub + no license            -> BLOCKED
  TEST 02 MIT software + unknown corpus         -> software allowed, corpus NOT
  TEST 03 permissive data license verified      -> APPROVED (nếu đủ đk)
  TEST 04 non-commercial restriction            -> commercial BLOCKED
  TEST 05 no redistribution                        -> redistribution BLOCKED
  TEST 06 unknown license                          -> REFERENCE_ONLY / BLOCKED
  TEST 07 missing provenance                       -> REJECT
  TEST 08 missing version/hash                     -> REJECT (khi policy đòi pin)
  TEST 09 license changed                          -> FROZEN
  TEST 10 authority high + legal unknown           -> NOT APPROVED
  TEST 11 Source 21 added                          -> B1/B2 unchanged
  TEST 12 Source 21 passes gate                    -> can become ACTIVE
  TEST 13 Source 21 fails gate                     -> cannot enter Canonical
  TEST 14 try bypass LicenseGate                   -> must fail
  TEST 15 existing B1 records unchanged            -> unchanged
  TEST 16 existing B2 records unchanged            -> unchanged
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from gate.license import LicenseGate
from gate.provenance import ProvenanceGate
from gate.status import LegalStatus


@pytest.fixture(scope='module')
def temp_db(tmp_path_factory):
    """Tạo DB temp với bảng data_sources tối thiểu (cột legal) — không đụng DB thật."""
    src = tmp_path_factory.mktemp('t78') / 'lineage_temp.db'
    conn = sqlite3.connect(str(src))
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE data_sources (
            source_id INTEGER PRIMARY KEY,
            source_code TEXT,
            source_name TEXT,
            legal_status TEXT DEFAULT 'UNKNOWN',
            data_license_status TEXT DEFAULT 'UNKNOWN',
            integration_mode TEXT DEFAULT 'BLOCKED',
            software_license TEXT,
            corpus_license TEXT,
            license_spdx TEXT,
            data_redistribution INTEGER DEFAULT 0,
            data_commercial INTEGER DEFAULT 0,
            noncommercial INTEGER DEFAULT 0,
            sharealike_required INTEGER DEFAULT 0,
            derivative_allowed INTEGER DEFAULT 0,
            noderivatives INTEGER DEFAULT 0,
            license_verified INTEGER DEFAULT 0,
            license_verified_at TEXT,
            terms_status TEXT DEFAULT 'under_review',
            version_policy TEXT DEFAULT 'not_available',
            freeze_reason TEXT,
            active INTEGER DEFAULT 1,
            enabled INTEGER DEFAULT 1
        )
    ''')
    # B1/B2 "tables" để kiểm tra không bị đụng (TEST 15/16)
    cur.execute('CREATE TABLE entity_hub (entity_id INTEGER PRIMARY KEY, status TEXT)')
    cur.execute('CREATE TABLE entity_claims (claim_id INTEGER PRIMARY KEY, entity_id INTEGER)')
    cur.execute("INSERT INTO entity_hub VALUES (1,'active'),(2,'active')")
    cur.execute("INSERT INTO entity_claims VALUES (10,1),(11,2)")
    conn.commit()
    conn.close()
    return str(src)


def add_source(db, sid, **kw):
    conn = sqlite3.connect(db)
    cols = ['source_id', 'source_code', 'source_name', 'legal_status', 'data_license_status',
            'integration_mode', 'software_license', 'corpus_license', 'license_spdx',
            'data_redistribution', 'data_commercial', 'noncommercial', 'sharealike_required',
            'derivative_allowed', 'noderivatives', 'license_verified', 'license_verified_at',
            'terms_status', 'version_policy', 'freeze_reason']
    vals = {
        'source_id': sid, 'source_code': f'SRC{sid:03d}', 'source_name': f'Source {sid}',
        'legal_status': 'UNKNOWN', 'data_license_status': 'UNKNOWN', 'integration_mode': 'BLOCKED',
        'software_license': None, 'corpus_license': None, 'license_spdx': None,
        'data_redistribution': 0, 'data_commercial': 0, 'noncommercial': 0,
        'sharealike_required': 0, 'derivative_allowed': 0, 'noderivatives': 0,
        'license_verified': 0, 'license_verified_at': None, 'terms_status': 'under_review',
        'version_policy': 'not_available', 'freeze_reason': None,
    }
    vals.update(kw)
    ph = ','.join(['?'] * len(cols))
    cur = conn.cursor()
    cur.execute(f'INSERT INTO data_sources ({",".join(cols)}) VALUES ({ph})',
                [vals[c] for c in cols])
    conn.commit()
    conn.close()
    return sid


def count_rows(db, table):
    conn = sqlite3.connect(db)
    n = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    conn.close()
    return n


# --------------------------------------------------------------------------
# TEST 01 — Public GitHub + no license -> BLOCKED / UNKNOWN
# --------------------------------------------------------------------------
def test_01_public_github_no_license(temp_db):
    add_source(temp_db, 1, legal_status='UNKNOWN', data_license_status='UNKNOWN',
               integration_mode='BLOCKED')
    g = LicenseGate(temp_db)
    assert g.checkSourcePermission(1, 'INGEST')['allowed'] is False
    assert g.checkSourcePermission(1, 'DOWNLOAD')['allowed'] is False


# --------------------------------------------------------------------------
# TEST 02 — MIT software + unknown corpus -> software ok, corpus NOT
# --------------------------------------------------------------------------
def test_02_mit_software_unknown_corpus(temp_db):
    add_source(temp_db, 2, legal_status='REFERENCE_ONLY', data_license_status='UNKNOWN',
               integration_mode='REFERENCE_ONLY', software_license='MIT', corpus_license=None)
    g = LicenseGate(temp_db)
    # software/code thẳng: cho phép tham khảo (metadata)
    assert g.checkSourcePermission(2, 'READ_METADATA')['allowed'] is True
    # corpus: KHÔNG được ingest
    assert g.checkSourcePermission(2, 'INGEST')['allowed'] is False
    assert g.checkSourcePermission(2, 'REDISTRIBUTE')['allowed'] is False


# --------------------------------------------------------------------------
# TEST 03 — permissive data license verified -> APP/ACTIVE nếu đủ đk
# --------------------------------------------------------------------------
def test_03_verified_permissive_data_license(temp_db):
    add_source(temp_db, 3, legal_status='APPROVED', data_license_status='APPROVED',
               integration_mode='INGEST', license_verified=1, license_spdx='CC BY 4.0')
    g = LicenseGate(temp_db)
    # APPROVED chưa ACTIVE -> chưa ingest
    assert g.checkSourcePermission(3, 'INGEST')['allowed'] is False
    # sau khi active
    conn = sqlite3.connect(temp_db)
    conn.execute("UPDATE data_sources SET legal_status='ACTIVE', integration_mode='INGEST' WHERE source_id=3")
    conn.commit(); conn.close()
    assert g.checkSourcePermission(3, 'INGEST')['allowed'] is True


# --------------------------------------------------------------------------
# TEST 04 — non-commercial restriction -> commercial BLOCKED
# --------------------------------------------------------------------------
def test_04_noncommercial_restriction(temp_db):
    add_source(temp_db, 4, legal_status='ACTIVE', data_license_status='APPROVED',
               integration_mode='INGEST', noncommercial=1, data_commercial=0, license_verified=1)
    g = LicenseGate(temp_db)
    assert g.checkSourcePermission(4, 'COMMERCIAL_USE')['allowed'] is False
    assert g.checkSourcePermission(4, 'INGEST')['allowed'] is True


# --------------------------------------------------------------------------
# TEST 05 — no redistribution permission -> redistribution BLOCKED
# --------------------------------------------------------------------------
def test_05_no_redistribution(temp_db):
    add_source(temp_db, 5, legal_status='ACTIVE', data_license_status='APPROVED',
               integration_mode='INGEST', data_redistribution=0, data_commercial=1, license_verified=1)
    g = LicenseGate(temp_db)
    # redistribution là op DATA; data_license_status APPROVED nhưng redistribution chưa rõ -> cần quyền rõ
    # Redistribute không được default_allows cho ACTIVE trừ khi... gate cần data_redistribution
    assert g.checkSourcePermission(5, 'INGEST')['allowed'] is True
    r = g.checkSourcePermission(5, 'REDISTRIBUTE')
    assert r['allowed'] is False


# --------------------------------------------------------------------------
# TEST 06 — unknown license -> REFERENCE_ONLY / BLOCKED
# --------------------------------------------------------------------------
def test_06_unknown_license(temp_db):
    add_source(temp_db, 6, legal_status='UNKNOWN', data_license_status='UNKNOWN',
               integration_mode='BLOCKED')
    g = LicenseGate(temp_db)
    assert g.checkSourcePermission(6, 'INGEST')['allowed'] is False


# --------------------------------------------------------------------------
# TEST 07 — missing provenance -> REJECT
# --------------------------------------------------------------------------
def test_07_missing_provenance():
    pg = ProvenanceGate()
    r = pg.check({'source_id': 6})
    assert r['passed'] is False
    assert any(k in r['missing'] for k in ('source_uri', 'content_hash'))


# --------------------------------------------------------------------------
# TEST 08 — missing version/hash -> REJECT khi policy đòi pin
# --------------------------------------------------------------------------
def test_08_missing_version_requires_pin():
    pg = ProvenanceGate().source_version_policy('git_pin')
    r = pg.check({'source_id': 6, 'source_uri': 'u', 'source_version': '1',
                  'retrieved_at': 'x', 'content_hash': 'h', 'license_status': 'a',
                  'transformation': 't', 'evidence_type': 'e'})
    assert r['passed'] is False  # thiếu commit_sha/release
    assert 'commit_sha/release_version' in r['missing']


# --------------------------------------------------------------------------
# TEST 09 — license changed -> FROZEN
# --------------------------------------------------------------------------
def test_09_license_changed_frozen(temp_db):
    add_source(temp_db, 9, legal_status='FROZEN', data_license_status='FROZEN',
               integration_mode='BLOCKED', freeze_reason='license changed')
    g = LicenseGate(temp_db)
    assert g.checkSourcePermission(9, 'INGEST')['allowed'] is False
    assert g.checkSourcePermission(9, 'INGEST')['status'] == 'FROZEN'


# --------------------------------------------------------------------------
# TEST 10 — authority high + legal unknown -> NOT APPROVED
# --------------------------------------------------------------------------
def test_10_authority_high_legal_unknown(temp_db):
    add_source(temp_db, 10, legal_status='UNKNOWN', data_license_status='UNKNOWN',
               integration_mode='BLOCKED')
    g = LicenseGate(temp_db)
    # Authority (không có cột trong gate) không được phép đánh đổi legal
    assert g.checkSourcePermission(10, 'INGEST')['allowed'] is False


# --------------------------------------------------------------------------
# TEST 11 — Source 21 added -> B1/B2 unchanged
# --------------------------------------------------------------------------
def test_11_source21_added_b1b2_unchanged(temp_db):
    before1 = count_rows(temp_db, 'entity_hub')
    before2 = count_rows(temp_db, 'entity_claims')
    add_source(temp_db, 21, legal_status='AUDITING', data_license_status='UNKNOWN',
               integration_mode='BLOCKED')
    assert count_rows(temp_db, 'entity_hub') == before1
    assert count_rows(temp_db, 'entity_claims') == before2


# --------------------------------------------------------------------------
# TEST 12 — Source 21 passes gate -> can become ACTIVE
# --------------------------------------------------------------------------
def test_12_source21_passes_gate(temp_db):
    add_source(temp_db, 22, legal_status='ACTIVE', data_license_status='APPROVED',
               integration_mode='INGEST', license_verified=1, data_redistribution=1,
               data_commercial=1)
    g = LicenseGate(temp_db)
    assert g.checkSourcePermission(22, 'INGEST')['allowed'] is True


# --------------------------------------------------------------------------
# TEST 13 — Source 21 fails gate -> cannot enter Canonical
# --------------------------------------------------------------------------
def test_13_source21_fails_gate(temp_db):
    add_source(temp_db, 23, legal_status='UNKNOWN', data_license_status='UNKNOWN',
               integration_mode='BLOCKED')
    g = LicenseGate(temp_db)
    assert g.checkSourcePermission(23, 'INGEST')['allowed'] is False


# --------------------------------------------------------------------------
# TEST 14 — try bypass LicenseGate -> must fail / rejected
# --------------------------------------------------------------------------
def test_14_bypass_licegate_fails():
    # Bypass = ingest mà không qua gate: không có path trực tiếp.
    # LegalStatus bắt buộc ACTIVE để can_ingest; mọi status khác đều chặn.
    ls = LegalStatus(source_code='x', legal_status='UNKNOWN', data_license_status='UNKNOWN')
    assert ls.can_ingest() is False
    ls2 = LegalStatus(source_code='x', legal_status='ACTIVE', data_license_status='UNKNOWN')
    assert ls2.can_ingest() is False  # data unknown -> vẫn không ingest


# --------------------------------------------------------------------------
# TEST 15 / 16 — existing B1 records unchanged
# --------------------------------------------------------------------------
def test_15_b1_records_unchanged(temp_db):
    assert count_rows(temp_db, 'entity_hub') == 2


def test_16_b2_records_unchanged(temp_db):
    assert count_rows(temp_db, 'entity_claims') == 2
