"""
T165-P8.1 Unit Tests — Entity Alignment Core Contract
Không dùng LLM, không dùng DB, không dùng network, không dùng production data.
Tất cả fixtures là deterministic và minimal.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from canonical_lock import (
    CanonicalLockEntry,
    EntityAssertion,
    build_entity_key_map,
    build_entity_prompt_instruction,
    parse_entity_xml,
    check_entity_assertions,
    post_assert,
    normalize_vi,
    P8_MAX_ENTITY_KEYS,
)


# ---------------------------------------------------------------------------
# Fixtures nhỏ, deterministic
# ---------------------------------------------------------------------------

def _place(
    source_form: str = '少林寺',
    canonical_value: str = 'Thiếu Lâm Tự',
    canonical_id: str = 'PL000000023255',
    authority_level: float = 0.9,
) -> CanonicalLockEntry:
    return CanonicalLockEntry(
        source_form=source_form,
        normalized_form=normalize_vi(canonical_value),
        entity_type='PLACE',
        canonical_id=canonical_id,
        canonical_value=canonical_value,
        authority_source='namevi_map_places.reviewed',
        authority_level=authority_level,
        status='LOCKED',
        claims=[],
    )


def _person(
    source_form: str = '懷海',
    canonical_value: str = 'Bách Trượng Hoài Hải',
    canonical_id: str = 'AB000001',
    authority_level: float = 1.0,
) -> CanonicalLockEntry:
    return CanonicalLockEntry(
        source_form=source_form,
        normalized_form=normalize_vi(canonical_value),
        entity_type='PERSON',
        canonical_id=canonical_id,
        canonical_value=canonical_value,
        authority_source='person_display_names.verified',
        authority_level=authority_level,
        status='LOCKED',
        claims=[],
    )


def _conflict(source_form: str = '少林寺') -> CanonicalLockEntry:
    """CONFLICT — không bao giờ được gán key trong P8."""
    return CanonicalLockEntry(
        source_form=source_form,
        normalized_form='thieu lam tu',
        entity_type='UNKNOWN',
        canonical_id='',
        canonical_value='',
        authority_source='CONFLICT',
        authority_level=0.5,
        status='CONFLICT',
        claims=[
            {'source': 'src_a', 'value': 'Thiếu Lâm Tự'},
            {'source': 'src_b', 'value': 'Ít Lâm Tự'},
        ],
    )


def _candidate(source_form: str = '禪') -> CanonicalLockEntry:
    return CanonicalLockEntry(
        source_form=source_form,
        normalized_form='thien',
        entity_type='BUDDHIST_TERM',
        canonical_id='',
        canonical_value='Thiền',
        authority_source='translation_glossary',
        authority_level=0.7,
        status='CANDIDATE',
        claims=[],
    )


# ===========================================================================
# build_entity_key_map
# ===========================================================================

class TestBuildEntityKeyMap:
    def test_locked_gets_key(self):
        km = build_entity_key_map([_place()])
        assert 'E1' in km
        assert km['E1'].source_form == '少林寺'

    def test_candidate_excluded(self):
        km = build_entity_key_map([_candidate()])
        assert len(km) == 0

    def test_conflict_excluded(self):
        km = build_entity_key_map([_conflict()])
        assert len(km) == 0

    def test_keys_ascending(self):
        km = build_entity_key_map([_place(), _person()])
        assert set(km.keys()) == {'E1', 'E2'}

    def test_canonical_id_preserved(self):
        km = build_entity_key_map([_place(canonical_id='PL000000023255')])
        assert km['E1'].canonical_id == 'PL000000023255'

    def test_max_keys_respected(self):
        entries = [
            CanonicalLockEntry(
                source_form=f'X{i}', normalized_form=f'x{i}', entity_type='PLACE',
                canonical_id=f'PL{i:08d}', canonical_value=f'Tự {i}',
                authority_source='test', authority_level=0.9, status='LOCKED', claims=[],
            )
            for i in range(15)
        ]
        km = build_entity_key_map(entries)
        assert len(km) == P8_MAX_ENTITY_KEYS

    def test_sorted_by_authority_level_desc(self):
        low = _place(source_form='A', authority_level=0.5)
        high = _person(source_form='B', authority_level=1.0)
        km = build_entity_key_map([low, high])
        assert km['E1'].source_form == 'B'

    def test_keys_not_canonical_ids(self):
        km = build_entity_key_map([_place(canonical_id='PL000000023255')])
        for key in km:
            assert not key.startswith('PL')
            assert key.startswith('E')

    def test_empty_lock(self):
        assert build_entity_key_map([]) == {}

    def test_only_locked_gets_key_mixed(self):
        lock = [_place(), _conflict(), _candidate()]
        km = build_entity_key_map(lock)
        assert len(km) == 1
        assert km['E1'].source_form == '少林寺'


# ===========================================================================
# build_entity_prompt_instruction
# ===========================================================================

class TestBuildEntityPromptInstruction:
    def test_empty_keymap_returns_empty(self):
        assert build_entity_prompt_instruction({}) == ''

    def test_contains_entity_keys(self):
        km = build_entity_key_map([_place()])
        instr = build_entity_prompt_instruction(km)
        assert 'E1' in instr
        assert '少林寺' in instr
        assert 'PLACE' in instr

    def test_no_canonical_id_in_instruction(self):
        """Canonical ID KHÔNG được xuất hiện trong prompt-facing instruction."""
        km = build_entity_key_map([_place(canonical_id='PL000000023255')])
        instr = build_entity_prompt_instruction(km)
        assert 'PL000000023255' not in instr

    def test_result_wrapper_instructed(self):
        km = build_entity_key_map([_place()])
        instr = build_entity_prompt_instruction(km)
        assert 'result' in instr.lower()

    def test_multiple_entities_all_listed(self):
        km = build_entity_key_map([_place(), _person()])
        instr = build_entity_prompt_instruction(km)
        assert 'E1' in instr
        assert 'E2' in instr
        assert '少林寺' in instr
        assert '懷海' in instr


# ===========================================================================
# parse_entity_xml — Test cases A–L + thêm
# ===========================================================================

class TestParseEntityXml:

    # A: no entity tags in output
    def test_A_no_entities(self):
        output = '<result>Ông đến chùa để tu học.</result>'
        plain, assertions = parse_entity_xml(output, {})
        assert assertions == []
        assert 'chùa' in plain
        assert '<' not in plain

    # B: one valid entity, XML well-formed
    def test_B_one_valid_entity(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key="E1">Thiếu Lâm Tự</entity> để tu học.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert len(assertions) == 1
        assert assertions[0].key == 'E1'
        assert assertions[0].target_surface == 'Thiếu Lâm Tự'
        assert assertions[0].source_form == '少林寺'
        assert 'entity' not in plain.lower()
        assert 'Thiếu Lâm Tự' in plain

    # C: multiple valid entities
    def test_C_multiple_valid_entities(self):
        km = build_entity_key_map([_place(), _person()])
        output = (
            '<result>Ông đến <entity key="E1">Thiếu Lâm Tự</entity> '
            'gặp <entity key="E2">Bách Trượng Hoài Hải</entity>.</result>'
        )
        plain, assertions = parse_entity_xml(output, km)
        assert len(assertions) == 2
        assert {a.key for a in assertions} == {'E1', 'E2'}

    # D: unknown key
    def test_D_unknown_key(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key="E9">Chùa Lạ</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert len(assertions) == 1
        assert assertions[0].assertion_status == 'unknown_key'
        assert assertions[0].canonical_id == ''

    # E: missing expected marker
    def test_E_missing_expected_marker(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến chùa này để tu học.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert assertions == []
        issues = check_entity_assertions(assertions, km, [_place()])
        missing = [i for i in issues if i['assertion_status'] == 'missing']
        assert len(missing) == 1

    # F: entity_type comes from server (NOT from LLM)
    def test_F_entity_type_from_server_authority(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert len(assertions) == 1
        assert assertions[0].entity_type == 'PLACE'
        assert assertions[0].canonical_id == 'PL000000023255'

    # G: mismatch
    def test_G_mismatch_wrong_surface(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key="E1">Thiếu Lâm Sơn</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        issues = check_entity_assertions(assertions, km, [_place()])
        mismatch = [i for i in issues if i['code'] == 'P8_MISMATCH']
        assert len(mismatch) == 1
        assert mismatch[0]['severity'] == 'HARD'
        assert assertions[0].assertion_status == 'mismatch'

    # H: malformed — no <result> wrapper
    def test_H_malformed_no_result_wrapper(self):
        km = build_entity_key_map([_place()])
        output = 'Ông đến Thiếu Lâm Tự để tu học.'
        plain, assertions = parse_entity_xml(output, km)
        assert assertions == []
        assert plain == output

    # I: overlapping nested markers
    def test_I_overlapping_markers(self):
        km = build_entity_key_map([_place(), _person()])
        output = '<result>Ông <entity key="E1">Thiếu <entity key="E2">Lâm</entity> Tự</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert any(a.assertion_status == 'overlap' for a in assertions)

    # J: hallucinated unknown key
    def test_J_hallucinated_unknown_key(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key="E99">Bí Địa</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert assertions[0].assertion_status == 'unknown_key'
        assert assertions[0].canonical_id == ''

    # K: legacy plain-string (no entity tags, no result wrapper)
    def test_K_legacy_plain_string(self):
        plain, assertions = parse_entity_xml('Thiếu Lâm Tự là ngôi chùa lớn.', {})
        assert assertions == []
        assert 'Thiếu Lâm Tự' in plain

    # L: tolerance — missing quotes on key attr
    def test_L_tolerance_missing_quotes(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key=E1>Thiếu Lâm Tự</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert len(assertions) == 1
        assert assertions[0].key == 'E1'

    def test_tags_stripped_from_plain_text(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông <entity key="E1">Thiếu Lâm Tự</entity> tu.</result>'
        plain, _ = parse_entity_xml(output, km)
        assert '<entity' not in plain
        assert '</entity>' not in plain
        assert 'Thiếu Lâm Tự' in plain

    def test_repeated_entity_two_occurrences(self):
        km = build_entity_key_map([_place()])
        output = (
            '<result>Ông đến <entity key="E1">Thiếu Lâm Tự</entity> '
            'rồi quay lại <entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        )
        plain, assertions = parse_entity_xml(output, km)
        assert len(assertions) == 2
        assert all(a.key == 'E1' for a in assertions)

    def test_html_entity_decoded_in_surface(self):
        km = build_entity_key_map([_place(canonical_value='A & B', source_form='X')])
        # Rebuild with exact canonical value
        km['E1'] = CanonicalLockEntry(
            source_form='X', normalized_form='a & b', entity_type='PLACE',
            canonical_id='T001', canonical_value='A & B',
            authority_source='test', authority_level=1.0, status='LOCKED', claims=[],
        )
        output = '<result>Ông đến <entity key="E1">A &amp; B</entity>.</result>'
        plain, assertions = parse_entity_xml(output, km)
        assert assertions[0].target_surface == 'A & B'


# ===========================================================================
# check_entity_assertions
# ===========================================================================

class TestCheckEntityAssertions:

    def test_pass_single_match(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông đến <entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        issues = check_entity_assertions(assertions, km, [_place()])
        hard = [i for i in issues if i['severity'] == 'HARD']
        assert hard == []
        assert assertions[0].assertion_status == 'pass'

    def test_case_insensitive_pass(self):
        km = build_entity_key_map([_place(canonical_value='Thiếu Lâm Tự')])
        output = '<result>Ông đến <entity key="E1">thiếu lâm tự</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        issues = check_entity_assertions(assertions, km, [_place()])
        hard = [i for i in issues if i['severity'] == 'HARD']
        assert hard == []

    def test_repeated_all_pass(self):
        km = build_entity_key_map([_place()])
        output = (
            '<result><entity key="E1">Thiếu Lâm Tự</entity> '
            'và <entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        )
        _, assertions = parse_entity_xml(output, km)
        issues = check_entity_assertions(assertions, km, [_place()])
        assert all(a.assertion_status == 'repeated_pass' for a in assertions)
        assert not any(i['severity'] == 'HARD' for i in issues)

    def test_repeated_one_fail(self):
        km = build_entity_key_map([_place()])
        output = (
            '<result><entity key="E1">Thiếu Lâm Tự</entity> '
            'và <entity key="E1">Thiếu Lâm Sơn</entity>.</result>'
        )
        _, assertions = parse_entity_xml(output, km)
        issues = check_entity_assertions(assertions, km, [_place()])
        hard = [i for i in issues if i['severity'] == 'HARD']
        assert len(hard) > 0

    def test_multi_candidate_conflict_review(self):
        conflict = _conflict()
        km = build_entity_key_map([conflict])  # CONFLICT → km = {}
        issues = check_entity_assertions([], km, [conflict])
        mc = [i for i in issues if i['code'] == 'P8_MULTI_CANDIDATE']
        assert len(mc) == 1
        assert mc[0]['severity'] == 'WARN'
        assert len(mc[0]['candidates']) == 2

    def test_missing_marker_warn(self):
        km = build_entity_key_map([_place()])
        issues = check_entity_assertions([], km, [_place()])
        missing = [i for i in issues if i['code'] == 'P8_MISSING_MARKER']
        assert len(missing) == 1
        assert missing[0]['severity'] == 'WARN'

    def test_unknown_key_warn(self):
        km = build_entity_key_map([_place()])
        output = '<result>Ông <entity key="E99">X</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        issues = check_entity_assertions(assertions, km, [_place()])
        uk = [i for i in issues if i['code'] == 'P8_UNKNOWN_KEY']
        assert len(uk) >= 1
        assert uk[0]['severity'] == 'WARN'


# ===========================================================================
# Canonical ID isolation (bắt buộc)
# ===========================================================================

class TestCanonicalIdIsolation:

    def test_canonical_id_not_in_prompt_instruction(self):
        """Canonical ID KHÔNG BAO GIỜ xuất hiện trong LLM-facing prompt."""
        entry = _place(canonical_id='PL000000023255')
        km = build_entity_key_map([entry])
        instr = build_entity_prompt_instruction(km)
        assert 'PL000000023255' not in instr

    def test_canonical_id_from_server_not_output(self):
        """canonical_id trong assertion luôn từ server key_map, không từ output LLM."""
        km = build_entity_key_map([_place(canonical_id='PL000000023255')])
        output = '<result>Ông đến <entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        assert assertions[0].canonical_id == 'PL000000023255'
        assert 'PL000000023255' not in output

    def test_unknown_key_has_empty_canonical_id(self):
        """Key không hợp lệ → canonical_id rỗng."""
        km = build_entity_key_map([_place()])
        output = '<result>Ông <entity key="E99">Bí Địa</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        assert assertions[0].canonical_id == ''

    def test_entity_type_never_from_llm(self):
        """entity_type luôn từ CanonicalLockEntry (server), không từ LLM output."""
        km = build_entity_key_map([_place()])
        output = '<result><entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        assert assertions[0].entity_type == 'PLACE'

    def test_canonical_value_never_from_llm(self):
        """canonical_value trong assertion luôn từ server, không thể LLM overwrite."""
        km = build_entity_key_map([_place(canonical_value='Thiếu Lâm Tự')])
        output = '<result><entity key="E1">XYZ Injected Value</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        assert assertions[0].canonical_value == 'Thiếu Lâm Tự'
        assert assertions[0].target_surface == 'XYZ Injected Value'


# ===========================================================================
# Multi-candidate preservation (bắt buộc)
# ===========================================================================

class TestMultiCandidatePreservation:

    def test_conflict_never_assigned_key(self):
        """少林寺 CONFLICT → không có key → không auto-resolve."""
        conflict = _conflict(source_form='少林寺')
        km = build_entity_key_map([conflict])
        assert len(km) == 0

    def test_conflict_triggers_review_warn(self):
        conflict = _conflict(source_form='少林寺')
        issues = check_entity_assertions([], {}, [conflict])
        mc = [i for i in issues if i['code'] == 'P8_MULTI_CANDIDATE']
        assert len(mc) == 1

    def test_candidates_preserved_not_discarded(self):
        """Candidates list preserved in issue — không silently discard."""
        conflict = _conflict()
        issues = check_entity_assertions([], {}, [conflict])
        mc = [i for i in issues if i['code'] == 'P8_MULTI_CANDIDATE']
        assert mc[0]['candidates'] is not None
        assert len(mc[0]['candidates']) >= 2

    def test_no_first_candidate_selection(self):
        """Không được tự chọn candidate đầu tiên khi có CONFLICT."""
        conflict = _conflict(source_form='少林寺')
        km = build_entity_key_map([conflict])
        assert '少林寺' not in [e.source_form for e in km.values()]


# ===========================================================================
# Backward compatibility / Legacy path
# ===========================================================================

class TestBackwardCompatibility:

    def test_post_assert_without_entity_assertions(self):
        """post_assert(lock, output) không có entity_assertions → hành vi T166 cũ."""
        entry = _place()
        status, issues = post_assert([entry], 'Thiếu Lâm Tự')
        assert status in ('pass', 'review_required', 'failed')

    def test_post_assert_with_empty_entity_assertions(self):
        """entity_assertions=[] → không thêm P8 issues."""
        entry = _place()
        status, issues = post_assert([entry], 'Thiếu Lâm Tự', entity_assertions=[])
        p8_issues = [i for i in issues if str(i.get('code', '')).startswith('P8_')]
        assert p8_issues == []

    def test_malformed_xml_returns_raw_output(self):
        """Malformed XML → trả nguyên raw output, không crash."""
        output = 'Ông đến Thiếu Lâm Tự để tu học.'
        plain, assertions = parse_entity_xml(output, {})
        assert plain == output
        assert assertions == []

    def test_empty_key_map_empty_instruction(self):
        """empty key_map (no LOCKED) → empty instruction → không inject vào prompt."""
        assert build_entity_prompt_instruction({}) == ''

    def test_post_assert_with_pass_entity_assertions(self):
        """pass assertions → không thêm HARD issue."""
        km = build_entity_key_map([_place()])
        output = '<result><entity key="E1">Thiếu Lâm Tự</entity>.</result>'
        _, assertions = parse_entity_xml(output, km)
        check_entity_assertions(assertions, km, [_place()])
        status, issues = post_assert([_place()], 'Thiếu Lâm Tự', entity_assertions=assertions)
        p8_hard = [i for i in issues if str(i.get('code', '')).startswith('P8_') and i.get('severity') == 'HARD']
        assert p8_hard == []


# ===========================================================================
# Deterministic key assignment
# ===========================================================================

class TestDeterministicKeys:

    def test_same_input_same_keys(self):
        entries = [_place(), _person()]
        km1 = build_entity_key_map(entries)
        km2 = build_entity_key_map(entries)
        assert list(km1.keys()) == list(km2.keys())
        assert [e.canonical_id for e in km1.values()] == [e.canonical_id for e in km2.values()]

    def test_keys_start_at_e1(self):
        km = build_entity_key_map([_place()])
        assert 'E1' in km
        assert 'E0' not in km

    def test_keys_contiguous(self):
        entries = [_place(), _person()]
        km = build_entity_key_map(entries)
        n = len(km)
        for i in range(1, n + 1):
            assert f'E{i}' in km
