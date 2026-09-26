#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T132 P7 §13 — Authority Contract Tests (A–J)
Dùng DB COPY thật (không fake), không ghi vào DB production.
Usage: python -m pytest tests/test_b25_authority_contract.py -v
"""
import os
import shutil
import sqlite3
import tempfile
import sys
import pytest

# Path setup
DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')

sys.path.insert(0, DAOANH)
from gate.license import LicenseGate
from gate.conflict_recorder import ConflictRecorder
from adapters.base import SourceAdapter, ExtractedEvidence


@pytest.fixture(scope='module')
def db_copy():
    """DB copy thật dùng trong toàn bộ test module — xóa sau khi xong."""
    tmp = tempfile.mktemp(suffix='.db', prefix='t132_test_')
    shutil.copy2(DB_PATH, tmp)
    yield tmp
    try:
        os.unlink(tmp)
    except OSError:
        pass


@pytest.fixture(scope='module')
def gate(db_copy):
    return LicenseGate(db_path=db_copy)


@pytest.fixture(scope='module')
def recorder(db_copy):
    return ConflictRecorder(db_path=db_copy)


# ── Case A: DILA-only entity claims ─────────────────────────────────────────

def test_a_dila_source_exists(db_copy):
    """A: DILA (source_id=1) có claims trong entity_claims."""
    c = sqlite3.connect(db_copy)
    cnt = c.execute('SELECT COUNT(*) FROM entity_claims WHERE source_id=1').fetchone()[0]
    c.close()
    assert cnt > 0, 'DILA phải có entity_claims'


# ── Case B: Entity có DILA + ZQLOCAL (2 nguồn) ──────────────────────────────

def test_b_multi_source_entity(db_copy):
    """B: Entity 100001 có claims từ cả DILA (1) và ZQLOCAL (5)."""
    c = sqlite3.connect(db_copy)
    sources = {r[0] for r in c.execute(
        'SELECT DISTINCT source_id FROM entity_claims WHERE entity_id=100001'
    )}
    c.close()
    assert 1 in sources, 'Entity 100001 phải có claim từ DILA'
    assert 5 in sources, 'Entity 100001 phải có claim từ ZQLOCAL'


# ── Case C: CHGIS (UNKNOWN) bị gate chặn data ops ───────────────────────────

def test_c_unknown_source_blocked_for_derive(gate):
    """C: CHGIS (UNKNOWN) không được phép DERIVE."""
    result = gate.can_quote(8)  # source_id=8 = CHGIS, UNKNOWN
    assert result['allowed'] is False, 'CHGIS UNKNOWN phải bị chặn DERIVE'
    assert result['status'] in ('UNKNOWN', 'BLOCKED', 'FROZEN')


def test_c_unknown_source_blocked_for_ingest(gate):
    """C: CHGIS (UNKNOWN) không được INGEST."""
    result = gate.checkSourcePermission(8, 'INGEST')
    assert result['allowed'] is False


# ── Case D: Conflicts tồn tại trong lineage_conflicts_v2 ────────────────────

def test_d_lineage_conflicts_exist(db_copy):
    """D: lineage_conflicts_v2 có genuine conflicts sau T157 B-2 fix."""
    c = sqlite3.connect(db_copy)
    cnt = c.execute('SELECT COUNT(*) FROM lineage_conflicts_v2').fetchone()[0]
    c.close()
    assert cnt > 10000, f'Phải có >10000 genuine conflicts, got {cnt}'
    assert cnt < 40328, f'Không được quá số cũ (40327 = pre-fix false conflicts), got {cnt}'


# ── Case E: license_verified=0 → license/usage_level = NULL (REVIEW_REQUIRED) ──

def test_e_license_not_backfilled(db_copy):
    """E: license col = NULL vì license_verified=0 cho tất cả nguồn."""
    c = sqlite3.connect(db_copy)
    cols = {r[1] for r in c.execute('PRAGMA table_info(entity_claims)')}
    assert 'license' in cols, 'entity_claims phải có cột license (T132 P1)'
    assert 'usage_level' in cols, 'entity_claims phải có cột usage_level (T132 P1)'
    # Tất cả sources có license_verified=0 → license nên là NULL
    non_null = c.execute(
        'SELECT COUNT(*) FROM entity_claims WHERE license IS NOT NULL'
    ).fetchone()[0]
    c.close()
    # Với license_verified=0 tất cả, không nên có value nào được backfill
    assert non_null == 0, f'Không nên backfill license khi license_verified=0, got {non_null} non-null rows'


def test_e_all_sources_license_unverified(db_copy):
    """E: Tất cả sources có license_verified=0 — REVIEW_REQUIRED."""
    c = sqlite3.connect(db_copy)
    verified = c.execute(
        'SELECT COUNT(*) FROM data_sources WHERE license_verified=1'
    ).fetchone()[0]
    c.close()
    assert verified == 0, 'Chưa có source nào verified — REVIEW_REQUIRED'


# ── Case F: source_id không tồn tại → gate chặn ────────────────────────────

def test_f_unknown_source_id_blocked(gate):
    """F: source_id không tồn tại → UNKNOWN → không cho truy cập."""
    result = gate.checkSourcePermission(9999, 'READ_METADATA')
    assert result['allowed'] is False
    assert result['status'] == 'UNKNOWN'


# ── Case G: Duplicate claims (same entity + source) ──────────────────────────

def test_g_duplicate_source_records(db_copy):
    """G: Entity 159162 có 5 claims từ source_id=1 — không tự gộp, giữ riêng."""
    c = sqlite3.connect(db_copy)
    cnt = c.execute(
        'SELECT COUNT(*) FROM entity_claims WHERE entity_id=159162 AND source_id=1'
    ).fetchone()[0]
    c.close()
    assert cnt >= 2, f'Entity 159162 phải có ≥2 claims từ DILA, got {cnt}'


# ── Case H: Same entity, diff labels from diff sources ───────────────────────

def test_h_two_source_claims_not_merged(db_copy):
    """H: Entity 100001 có DILA + ZQLOCAL labels — KHÔNG tự gộp."""
    c = sqlite3.connect(db_copy)
    rows = c.execute(
        'SELECT source_id, claim_type, object_text FROM entity_claims WHERE entity_id=100001'
    ).fetchall()
    c.close()
    sources = {r[0] for r in rows}
    assert len(sources) >= 2, 'Entity 100001 phải có claims từ ≥2 nguồn khác nhau'


# ── Case I: Adapter health_check = unknown ───────────────────────────────────

def test_i_default_adapter_health_unknown():
    """I: SourceAdapter skeleton trả health=unknown."""
    class MockAdapter(SourceAdapter):
        source_code = 'MOCK'
        def search(self, q, **kw): return []
        def resolve(self, rid, **kw): return None
        def get_provenance(self, ev): return {}

    a = MockAdapter()
    h = a.health_check()
    assert h['health'] == 'unknown'


def test_i_default_get_license_review_required():
    """I: get_license() mặc định trả REVIEW_REQUIRED."""
    class MockAdapter(SourceAdapter):
        source_code = 'MOCK'
        def search(self, q, **kw): return []
        def resolve(self, rid, **kw): return None
        def get_provenance(self, ev): return {}

    a = MockAdapter()
    lic = a.get_license()
    assert lic['license_status'] == 'REVIEW_REQUIRED'


# ── Case J: source_version NULL → staleness detectable ───────────────────────

def test_j_source_version_null_means_unknown(db_copy):
    """J: source_version NULL trong entity_claims = chưa track → staleness unknown."""
    c = sqlite3.connect(db_copy)
    cols = {r[1] for r in c.execute('PRAGMA table_info(entity_claims)')}
    assert 'source_version' in cols, 'entity_claims phải có cột source_version (T132 P1)'
    null_cnt = c.execute(
        'SELECT COUNT(*) FROM entity_claims WHERE source_version IS NULL'
    ).fetchone()[0]
    total = c.execute('SELECT COUNT(*) FROM entity_claims').fetchone()[0]
    c.close()
    # Tất cả nên là NULL vì không có source với version pinned
    assert null_cnt == total, f'Tất cả source_version phải NULL ban đầu: {null_cnt}/{total}'


# ── Extra: ConflictRecorder functional test ──────────────────────────────────

def test_conflict_recorder_insert(recorder):
    """ConflictRecorder: INSERT mới → True; INSERT IGNORE duplicate → False."""
    inserted = recorder.record(
        entity_ref='PL000000000001',
        field='name_vi',
        value_a='Test A',
        value_b='Test B',
        source_a='DILA',
        source_b='ZQLOCAL',
        notes='T132 test'
    )
    assert inserted is True, 'Lần đầu INSERT phải True'
    # Duplicate → IGNORE
    inserted2 = recorder.record(
        entity_ref='PL000000000001',
        field='name_vi',
        value_a='Test A',
        value_b='Test B',
        source_a='DILA',
        source_b='ZQLOCAL',
    )
    assert inserted2 is False, 'IGNORE duplicate phải False'


# ── Extra: gate.can_display / can_quote ──────────────────────────────────────

def test_p2_can_display_auditing(gate):
    """P2: can_display(DILA=1) = AUDITING cho phép READ_METADATA."""
    result = gate.can_display(1)  # DILA = AUDITING
    assert result['allowed'] is True, f'DILA AUDITING phải cho display: {result}'


def test_p2_can_quote_auditing_blocked(gate):
    """P2: can_quote(DILA=1) = AUDITING không cho phép DERIVE."""
    result = gate.can_quote(1)  # DILA = AUDITING, DERIVE không trong AUDITING set
    assert result['allowed'] is False, 'DILA AUDITING không được quote/derive'


# ── Extra: ExtractedEvidence license fields ──────────────────────────────────

def test_p3_extracted_evidence_license_fields():
    """P3: ExtractedEvidence có 3 fields license/license_status/source_version."""
    ev = ExtractedEvidence(
        source_code='DILA',
        claim_type='NAME',
        subject='A000001',
        predicate='name_zh',
        object_text='慧能',
    )
    assert ev.license is None, 'Default license = None'
    assert ev.license_status is None
    assert ev.source_version is None
    d = ev.to_dict()
    assert 'license' in d
    assert 'license_status' in d
    assert 'source_version' in d
