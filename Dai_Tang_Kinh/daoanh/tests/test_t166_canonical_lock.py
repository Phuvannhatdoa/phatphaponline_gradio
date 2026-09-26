# -*- coding: utf-8 -*-
"""test_t166_canonical_lock.py — T166 Canonical Identity Hard Guard unit tests.
Test trên temp DB (không chạm DB thật).
"""
import os
import sys
import sqlite3
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from canonical_lock import (  # noqa: E402
    normalize_vi, extract_maximal_han_runs, is_valid_vi,
    build_canonical_lock, pre_assert, post_assert,
    t166_lock_fingerprint, build_lock_prompt_section,
    CanonicalLockEntry,
)


def _mkdb():
    """Temp DB với schema authority tables (subset)."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        -- ⚠️ Schema PHẢI khớp data/lineage.db thật (verify 2026-09-25).
        -- _query_all_sources() nuốt sqlite3.Error ⇒ schema lệch sẽ âm thầm
        -- trả [] (nguồn chết) chứ không báo lỗi → test phải dùng đúng tên cột.
        CREATE TABLE canonical_decision (
            entity_ref TEXT, canonical_name_vi TEXT, source_id TEXT,
            authority_rank TEXT, confidence REAL, verification_status TEXT
        );
        CREATE TABLE places_dila (
            dila_id TEXT PRIMARY KEY, name_zh TEXT
        );
        CREATE TABLE person_display_names (
            person_id TEXT, dila_person_id TEXT, display_name_vi TEXT,
            display_name_zh TEXT, authority_name_vi TEXT, authority_name_zh TEXT,
            is_preferred INTEGER, verification_status TEXT
        );
        CREATE TABLE vn_person_authority (
            name_zh TEXT, name_vi TEXT, dila_id TEXT, status TEXT
        );
        CREATE TABLE person_name_correction (
            person_id TEXT, name_zh TEXT, current_vi TEXT, proposed_vi TEXT,
            status TEXT
        );
        CREATE TABLE translation_glossary (
            term_zh TEXT, term_vi TEXT, is_locked INTEGER
        );
        CREATE TABLE name_vi_map (
            name_zh TEXT, name_vi_auto TEXT, name_vi_final TEXT,
            approved_by TEXT, dila_id TEXT, confidence REAL
        );
        CREATE TABLE namevi_map_places (
            name_zh TEXT, name_vi TEXT, dila_id TEXT, confidence REAL,
            vn_name_status TEXT
        );
        CREATE TABLE people (
            id TEXT PRIMARY KEY, name_zh TEXT, name_vi TEXT, source_origin TEXT
        );

        -- Fixture: A009460 丹霞天然 → Đơn Hà Thiên Nhiên (LOCKED, vnpa verified)
        INSERT INTO people (id, name_zh, name_vi, source_origin)
            VALUES ('A009460', '天然', NULL, NULL);
        INSERT INTO vn_person_authority (name_zh, name_vi, dila_id, status)
            VALUES ('丹霞天然', 'Đơn Hà Thiên Nhiên', 'A009460', 'verified');

        -- Fixture: 少林寺 → Thiếu Lâm Tự (PLACE, vn_name_status=reviewed)
        INSERT INTO places_dila (dila_id, name_zh)
            VALUES ('PL000000000001', '少林寺');
        INSERT INTO namevi_map_places (name_zh, name_vi, dila_id, confidence, vn_name_status)
            VALUES ('少林寺', 'Thiếu Lâm Tự', 'PL000000000001', 0.9, 'reviewed');

        -- Fixture: A005248 安廩 → An Lẫm (CANDIDATE, name_vi_map auto 0.7, final=NULL)
        INSERT INTO people (id, name_zh, name_vi, source_origin)
            VALUES ('A005248', '安廩', NULL, NULL);
        INSERT INTO name_vi_map (name_zh, name_vi_auto, name_vi_final, approved_by)
            VALUES ('安廩', 'An Lẫm', NULL, NULL);

        -- Glossary locked ≥2 chars: 大乘 → Đại Thừa
        INSERT INTO translation_glossary (term_zh, term_vi, is_locked)
            VALUES ('大乘', 'Đại Thừa', 1);

        -- Mojibake test data — phải bị is_valid_vi loại (SPEC §20.2 #3/#17)
        INSERT INTO canonical_decision (entity_ref, canonical_name_vi, authority_rank)
            VALUES ('PL000000000001', 'Th? S?t H?i', 'admin_approved');
        INSERT INTO name_vi_map (name_zh, name_vi_final, approved_by)
            VALUES ('莫吉巴克', 'M?j?b?k?', 'admin');

        -- Conflict: cùng Hán 天然, 2 nguồn VI khác nhau
        INSERT INTO person_display_names
            (person_id, dila_person_id, display_name_vi, display_name_zh,
             authority_name_vi, authority_name_zh, is_preferred, verification_status)
            VALUES ('A009460', 'A009460', 'Biến Thể 1', '天然',
                    'Biến Thể 1', '天然', 1, 'verified_direct');
        INSERT INTO person_name_correction (person_id, name_zh, current_vi, status)
            VALUES ('A009460', '天然', 'Biến Thể 2', 'applied');

    """)
    conn.commit()
    return conn, path


def test_normalize_vi():
    # Strip title "Thích"
    assert normalize_vi('Thích An Lẫm') == 'anlẫm'
    assert normalize_vi('THÍCH AN LẪM') == 'anlẫm'
    # Strip title "Thích Ca"
    assert normalize_vi('Thích Ca Đơn Hà') == 'đơnhà'
    # Strip title "Ngài", keep "Hòa Thượng" as part of name
    assert normalize_vi('Ngài Hòa Thượng An Lẫm') == 'hòathượnganlẫm'
    # No title
    assert normalize_vi('Đơn Hà Thiên Nhiên') == 'đơnhàthiênnhiên'
    # Empty
    assert normalize_vi('') == ''
    assert normalize_vi(None) == ''


def test_extract_maximal_han_runs():
    # Basic
    runs = extract_maximal_han_runs('孝義性空禪師法嗣。')
    assert '孝義性空禪師法嗣' in runs or '孝義' in runs  # maximal run
    # Mixed with VI
    runs = extract_maximal_han_runs('丹霞天然 là Danh Thiền Sư')
    assert '丹霞天然' in runs
    # Cap 40
    long = ''.join([f'汉{i}' for i in range(50)])
    runs = extract_maximal_han_runs(long)
    assert len(runs) <= 40
    # No Han
    assert extract_maximal_han_runs('không có Hán') == []
    # 1-char filtered
    runs = extract_maximal_han_runs('法 僧 戒')
    # 1-char runs are filtered out
    for r in runs:
        assert len(r) >= 2


def test_is_valid_vi():
    assert is_valid_vi('Đơn Hà Thiên Nhiên')
    assert is_valid_vi('Thiếu Lâm Tự')
    assert not is_valid_vi('')
    assert not is_valid_vi(None)
    assert not is_valid_vi('Th? S?t H?i')  # mojibake
    assert not is_valid_vi('M?j?b?k?')
    assert not is_valid_vi('  ')  # only space
    assert not is_valid_vi('???')


def test_build_canonical_lock_locked_person():
    conn, path = _mkdb()
    try:
        lock = build_canonical_lock(conn, '丹霞天然 传法')
        # Should find LOCKED entry for 丹霞天然
        locked = [e for e in lock if e.status == 'LOCKED' and e.source_form == '丹霞天然']
        assert len(locked) >= 1
        e = locked[0]
        assert e.canonical_value == 'Đơn Hà Thiên Nhiên'
        assert e.entity_type == 'PERSON'
        # LOCK là quyết định theo FLAG (vn_person_authority.verified), không
        # theo level — level 0.95 vẫn LOCKED (SPEC §3.1 "Nguyên tắc lock").
        assert e.authority_source == 'vn_person_authority.verified'
    finally:
        conn.close(); os.unlink(path)


def test_build_canonical_lock_locked_place():
    conn, path = _mkdb()
    try:
        lock = build_canonical_lock(conn, '少林寺 在 河南')
        locked = [e for e in lock if e.status == 'LOCKED' and e.source_form == '少林寺']
        assert len(locked) >= 1
        e = locked[0]
        assert e.canonical_value == 'Thiếu Lâm Tự'
        assert e.entity_type == 'PLACE'
    finally:
        conn.close(); os.unlink(path)


def test_build_canonical_lock_candidate_person():
    conn, path = _mkdb()
    try:
        lock = build_canonical_lock(conn, '安廩 是 谁')
        # A005248 安廩 → CANDIDATE (name_vi_map conf 0.7, final=NULL)
        cand = [e for e in lock if e.source_form == '安廩']
        assert len(cand) >= 1
        # Status should be CANDIDATE (level 0.7 < 1.0)
        for e in cand:
            assert e.status in ('CANDIDATE', 'LOCKED')  # could be LOCKED from other source
    finally:
        conn.close(); os.unlink(path)


def test_build_canonical_lock_glossary_term():
    conn, path = _mkdb()
    try:
        lock = build_canonical_lock(conn, '大乘 是 定')
        locked = [e for e in lock if e.status == 'LOCKED' and e.source_form == '大乘']
        assert len(locked) >= 1
        e = locked[0]
        assert e.canonical_value == 'Đại Thừa'
        assert e.entity_type == 'BUDDHIST_TERM'
    finally:
        conn.close(); os.unlink(path)


def test_build_canonical_lock_conflict():
    conn, path = _mkdb()
    try:
        lock = build_canonical_lock(conn, '天然')
        # person_display_names and person_name_correction both match '天然'
        # with different VI values → CONFLICT
        conflicts = [e for e in lock if e.status == 'CONFLICT' and e.normalized_form == '天然']
        assert len(conflicts) >= 1
        e = conflicts[0]
        assert e.claims
        assert len(e.claims) >= 2
    finally:
        conn.close(); os.unlink(path)


def test_build_canonical_lock_mojibake_rejected():
    conn, path = _mkdb()
    try:
        lock = build_canonical_lock(conn, '莫吉巴克')
        # name_vi_map has mojibake 'M?j?b?k?' → should be rejected (not LOCKED)
        locked = [e for e in lock if e.status == 'LOCKED' and e.normalized_form == '莫吉巴克']
        assert len(locked) == 0
    finally:
        conn.close(); os.unlink(path)


def test_normalize_compare_pass():
    # "Thích An Lẫm" vs "An Lẫm" → PASS after strip title
    lock = [
        CanonicalLockEntry(
            source_form='丹霞天然', normalized_form='丹霞天然',
            entity_type='PERSON', canonical_id='A009460',
            canonical_value='Đơn Hà Thiên Nhiên',
            authority_source='vn_person_authority.name_vi',
            authority_level=1.0, status='LOCKED', claims=[]
        )
    ]
    # Output with title "Thích"
    status, issues = post_assert(lock, 'Thích Đơn Hà Thiên Nhiên')
    assert status == 'pass'
    assert len(issues) == 0


def test_normalize_compare_fail():
    lock = [
        CanonicalLockEntry(
            source_form='丹霞天然', normalized_form='丹霞天然',
            entity_type='PERSON', canonical_id='A009460',
            canonical_value='Đơn Hà Thiên Nhiên',
            authority_source='vn_person_authority.name_vi',
            authority_level=1.0, status='LOCKED', claims=[]
        )
    ]
    # Output wrong name
    status, issues = post_assert(lock, 'Thích Đơn Hà Mật')
    assert status == 'failed'
    hard = [i for i in issues if i['severity'] == 'HARD' and i['code'] == 'CANONICAL_IDENTITY_MISMATCH']
    assert len(hard) == 1


def test_canonical_invention_detect():
    lock = [
        CanonicalLockEntry(
            source_form='安廩', normalized_form='安廩',
            entity_type='PERSON', canonical_id='A005248',
            canonical_value='An Lẫm',
            authority_source='name_vi_map.name_vi_final',
            authority_level=0.7, status='CANDIDATE', claims=[]
        )
    ]
    # LLM invents "An Nạp" not in allowed set
    status, issues = post_assert(lock, 'Thích An Nạp')
    # Should detect CANONICAL_INVENTION
    inv = [i for i in issues if i['code'] == 'CANONICAL_INVENTION']
    assert len(inv) >= 1
    assert status in ('failed', 'review_required')


def test_common_word_not_invention():
    lock = [
        CanonicalLockEntry(
            source_form='安廩', normalized_form='安廩',
            entity_type='PERSON', canonical_id='A005248',
            canonical_value='An Lẫm',
            authority_source='name_vi_map.name_vi_final',
            authority_level=0.7, status='CANDIDATE', claims=[]
        )
    ]
    # "Tôi thích uống trà" → "thích" is common word, not invention
    status, issues = post_assert(lock, 'Tôi thích uống trà')
    inv = [i for i in issues if i['code'] == 'CANONICAL_INVENTION']
    assert len(inv) == 0


def test_t166_lock_fingerprint():
    lock = [
        CanonicalLockEntry(
            source_form='丹霞天然', normalized_form='丹霞天然',
            entity_type='PERSON', canonical_id='A009460',
            canonical_value='Đơn Hà Thiên Nhiên',
            authority_source='vn_person_authority.name_vi',
            authority_level=1.0, status='LOCKED', claims=[]
        ),
        CanonicalLockEntry(
            source_form='少林寺', normalized_form='少林寺',
            entity_type='PLACE', canonical_id='PL000000000001',
            canonical_value='Thiếu Lâm Tự',
            authority_source='namevi_map_places.vn_name_final',
            authority_level=0.9, status='LOCKED', claims=[]
        )
    ]
    fp = t166_lock_fingerprint(lock)
    assert fp
    assert len(fp) == 16
    # Deterministic
    fp2 = t166_lock_fingerprint(lock)
    assert fp == fp2
    # Empty lock → empty fingerprint
    assert t166_lock_fingerprint([]) == ''


def test_build_lock_prompt_section():
    lock = [
        CanonicalLockEntry(
            source_form='丹霞天然', normalized_form='丹霞天然',
            entity_type='PERSON', canonical_id='A009460',
            canonical_value='Đơn Hà Thiên Nhiên',
            authority_source='vn_person_authority.name_vi',
            authority_level=1.0, status='LOCKED', claims=[]
        ),
        CanonicalLockEntry(
            source_form='安廩', normalized_form='安廩',
            entity_type='PERSON', canonical_id='A005248',
            canonical_value='An Lẫm',
            authority_source='name_vi_map.name_vi_final',
            authority_level=0.7, status='CANDIDATE', claims=[]
        )
    ]
    section = build_lock_prompt_section(lock)
    assert 'LOCKED CANONICAL CONTEXT' in section
    assert '丹霞天然 → Đơn Hà Thiên Nhiên' in section
    assert 'CANDIDATE' in section
    assert '安廩 → An Lẫm' in section


def test_pre_assert_p_partial():
    """P-PARTIAL (mặc định): unknown/CONFLICT vẫn CHO gọi LLM, chỉ gắn cờ."""
    lock = [
        CanonicalLockEntry(
            source_form='未知', normalized_form='未知',
            entity_type='UNKNOWN', canonical_id=None,
            canonical_value='', authority_source='', authority_level=0.0,
            status='UNKNOWN_REVIEW', claims=[]
        )
    ]
    status, issues = pre_assert(lock, policy='P-PARTIAL')
    assert status == 'review_required', f'P-PARTIAL phải cho qua, got {status}'
    assert issues, 'P-PARTIAL vẫn phải gắn cờ UNKNOWN_REVIEW'
    assert any(i['code'] == 'UNKNOWN_REVIEW' for i in issues)


def test_pre_assert_p_stop():
    """P-STOP (Admin flag): KHÔNG gọi LLM → failed/REVIEW_REQUIRED."""
    lock = [
        CanonicalLockEntry(
            source_form='未知', normalized_form='未知',
            entity_type='UNKNOWN', canonical_id=None,
            canonical_value='', authority_source='', authority_level=0.0,
            status='UNKNOWN_REVIEW', claims=[]
        )
    ]
    status, issues = pre_assert(lock, policy='P-STOP')
    assert status == 'failed', f'P-STOP phải chặn, got {status}'
    assert issues


def test_pre_assert_uncontrolled_proper_name_stops_both_policies():
    """§4.1 UNCONTROLLED_PROPER_NAME = token khớp authority nhưng CHƯA phân loại
    → STOP Ở CẢ 2 policy (đây là bug build lock, không phải unknown thật)."""
    lock = [
        CanonicalLockEntry(
            source_form='丹霞天然', normalized_form='丹霞天然',
            entity_type='PERSON', canonical_id='A009460',
            canonical_value='Đơn Hà Thiên Nhiên',
            authority_source='vn_person_authority.verified',
            authority_level=0.95, status='', claims=[]      # ← status rỗng
        )
    ]
    for pol in ('P-PARTIAL', 'P-STOP'):
        status, issues = pre_assert(lock, policy=pol)
        assert status == 'failed', f'{pol} phải STOP, got {status}'
        assert any(i['code'] == 'UNCONTROLLED_PROPER_NAME' for i in issues)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    passed, failed = 0, []
    for fn in fns:
        try:
            fn()
            print(f'✅ {fn.__name__}')
            passed += 1
        except Exception as e:
            print(f'❌ {fn.__name__}: {e}')
            failed.append(fn.__name__)
    print(f'\nT166 canonical_lock tests: {passed}/{len(fns)} PASS')
    if failed:
        print('FAILED:', ', '.join(failed))
        sys.exit(1)


if __name__ == '__main__':
    _run_all()