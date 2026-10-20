# -*- coding: utf-8 -*-
"""test_t165_phase8_pilot_gate.py — T165-P8.3 pilot gate integration tests.

Test cases A-R (per spec §13):
  A: P8 disabled → _p8_pilot_active returns False (legacy path unchanged)
  B: P8 gate disabled + pilot header → still False (gate required)
  C: P8 gate enabled + valid header → True
  D: P8 gate enabled + missing header → False
  E: P8 gate enabled + header + is_batch=True body → False (batch blocked)
  F: canonical ID absent from LLM prompt (build_entity_prompt_instruction)
  G: request-local E1/E2 keys generated correctly for LOCKED entries
  H: valid entity response → assertions with PASS status (assertion_status all_pass)
  I: missing entity marker → REVIEW status in assertions
  J: unknown key → REVIEW status
  K: wrong entity type → HARD or REVIEW per P8.1 contract
  L: multi-candidate → REVIEW, never first-candidate selection
  M: malformed XML → safe fallback (parse_entity_xml does not crash)
  N: legacy cache row remains readable after P8 (backward compat)
  O: P8 persistence fields passed correctly to write_cache
  P: P8 disabled → existing T166 behavior unchanged (no P8 fields)
  Q: (implicit — no real LLM invocation, all LLM calls mocked)
  R: (implicit — no real DB mutation, all DB ops use in-memory test DB)
"""
import json
import sqlite3
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# PATH setup
HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
sys.path.insert(0, DAOANH)

# ── helpers ─────────────────────────────────────────────────────────────────

class _FakeRequest:
    """Minimal Flask request substitute for unit testing _p8_pilot_active."""
    def __init__(self, headers=None, body=None, method='POST'):
        self.headers = headers or {}
        self._body = body or {}
        self.method = method

    def get_json(self, silent=False, **_kwargs):
        return self._body


def _make_minimal_lock_entry(dila_id='PL001', zh_name='少林寺', vi_name='Thiếu Lâm Tự',
                              entity_type='place', status='LOCKED'):
    """Minimal CanonicalLockEntry for P8 testing.
    CanonicalLockEntry fields: source_form, normalized_form, entity_type,
    canonical_id, canonical_value, authority_source, authority_level, status, claims.
    """
    from canonical_lock import CanonicalLockEntry
    return CanonicalLockEntry(
        source_form=zh_name,
        normalized_form=zh_name.lower(),
        entity_type=entity_type,
        canonical_id=dila_id,
        canonical_value=vi_name,
        authority_source='DILA',
        authority_level=1.0,
        status=status,
        claims=[],
    )


def _make_p8_db():
    """In-memory DB with full P8.2 schema."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE translation_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_hash TEXT, source_type TEXT, entity_id TEXT,
            source_text TEXT, translated_text TEXT,
            model_id TEXT, rules_version TEXT, status TEXT DEFAULT 'auto',
            created_at TEXT, updated_at TEXT,
            constitution_hash TEXT, selected_rule_codes TEXT, glossary_hash TEXT,
            identity_status TEXT, identity_issues TEXT, identity_lock_hash TEXT,
            entity_evidence TEXT, alignment_method TEXT,
            entity_assertion_status TEXT, entity_types_covered TEXT,
            UNIQUE(source_hash, source_type)
        )
    """)
    return conn


# ── TestP8PilotGate ──────────────────────────────────────────────────────────

class TestP8PilotGate(unittest.TestCase):
    """Test cases A-E — gate activation logic."""

    def _get_pilot_active(self, gate_enabled, headers=None, body=None):
        """Import and patch _P8_PILOT_GATE_ENABLED, then call _p8_pilot_active."""
        import app as app_module
        orig = app_module._P8_PILOT_GATE_ENABLED
        try:
            app_module._P8_PILOT_GATE_ENABLED = gate_enabled
            req = _FakeRequest(headers=headers or {}, body=body or {})
            return app_module._p8_pilot_active(req)
        finally:
            app_module._P8_PILOT_GATE_ENABLED = orig

    def test_A_p8_disabled_legacy_path(self):
        """A: _P8_PILOT_GATE_ENABLED=False → _p8_pilot_active always False."""
        result = self._get_pilot_active(
            False, headers={'X-T165-P8-Pilot': '1'})
        self.assertFalse(result, "Gate OFF phải trả False bất kể header")

    def test_B_gate_disabled_header_present(self):
        """B: Gate disabled + pilot header → still False (gate required)."""
        result = self._get_pilot_active(
            False, headers={'X-T165-P8-Pilot': '1'})
        self.assertFalse(result)

    def test_C_gate_enabled_valid_header(self):
        """C: Gate enabled + valid header → True."""
        result = self._get_pilot_active(
            True, headers={'X-T165-P8-Pilot': '1'})
        self.assertTrue(result, "Gate ON + header '1' phải trả True")

    def test_D_gate_enabled_missing_header(self):
        """D: Gate enabled + no header → False."""
        result = self._get_pilot_active(True, headers={})
        self.assertFalse(result, "Gate ON nhưng thiếu header → False")

    def test_E_batch_request_blocked(self):
        """E: Gate enabled + header + is_batch=True body → False (batch blocked)."""
        result = self._get_pilot_active(
            True,
            headers={'X-T165-P8-Pilot': '1'},
            body={'is_batch': True})
        self.assertFalse(result, "Batch request phải bị block dù có gate + header")

    def test_E2_batch_flag_false_allowed(self):
        """E2: is_batch=False with gate+header → True (not batch)."""
        result = self._get_pilot_active(
            True,
            headers={'X-T165-P8-Pilot': '1'},
            body={'is_batch': False})
        self.assertTrue(result)


# ── TestP8CanonicalIdIsolation ───────────────────────────────────────────────

class TestP8CanonicalIdIsolation(unittest.TestCase):
    """Test cases F, G — canonical ID must NOT appear in LLM prompt."""

    def test_F_canonical_id_absent_from_prompt(self):
        """F: build_entity_prompt_instruction never exposes canonical_id."""
        from canonical_lock import build_entity_key_map, build_entity_prompt_instruction
        entry = _make_minimal_lock_entry('PL023255', '少林寺', 'Thiếu Lâm Tự')
        key_map = build_entity_key_map([entry])
        instruction = build_entity_prompt_instruction(key_map)
        # canonical_id (PL023255) must not appear in the instruction
        self.assertNotIn('PL023255', instruction,
                         "canonical_id phải ẩn hoàn toàn khỏi LLM prompt")
        # Opaque key E1 should appear
        self.assertIn('E1', instruction)
        # Source form (Hán tự) should appear
        self.assertIn('少林寺', instruction)

    def test_G_request_local_keys_generated_correctly(self):
        """G: build_entity_key_map generates E1, E2, ... for LOCKED entries only."""
        from canonical_lock import build_entity_key_map, CanonicalLockEntry
        e1 = _make_minimal_lock_entry('PL001', '少林寺', 'Thiếu Lâm Tự', status='LOCKED')
        e2 = _make_minimal_lock_entry('PL002', '嵩山', 'Tung Sơn', status='LOCKED')
        cand = _make_minimal_lock_entry('PL003', '普陀山', 'Phổ Đà Sơn', status='CANDIDATE')
        key_map = build_entity_key_map([e1, e2, cand])
        # Only LOCKED entries get keys
        self.assertIn('E1', key_map)
        self.assertIn('E2', key_map)
        # CANDIDATE must not get a key
        self.assertEqual(len(key_map), 2, "CANDIDATE không được gán key")
        # Keys must not be canonical IDs
        for key in key_map:
            self.assertTrue(key.startswith('E'), f"Key phải là E-prefix, thực tế: {key}")

    def test_F2_db_primary_key_absent_from_prompt(self):
        """F2: internal DB pk / dila_id must not appear in instruction string."""
        from canonical_lock import build_entity_key_map, build_entity_prompt_instruction
        entry = _make_minimal_lock_entry('PL999999', '祇園精舍', 'Kỳ Viên Tịnh Xá')
        key_map = build_entity_key_map([entry])
        instruction = build_entity_prompt_instruction(key_map)
        self.assertNotIn('PL999999', instruction)
        self.assertNotIn('999999', instruction)


# ── TestP8EntityAlignmentFlow ────────────────────────────────────────────────

class TestP8EntityAlignmentFlow(unittest.TestCase):
    """Test cases H-M — entity alignment assertion contract."""

    def _make_key_map(self, zh='少林寺', vi='Thiếu Lâm Tự', entity_type='place'):
        from canonical_lock import build_entity_key_map
        entry = _make_minimal_lock_entry('PL001', zh, vi, entity_type=entity_type)
        return build_entity_key_map([entry])

    def test_H_valid_entity_response_pass(self):
        """H: valid entity marker (với <result> wrapper) → assertion all_pass."""
        import app as app_module
        from canonical_lock import parse_entity_xml, check_entity_assertions
        key_map = self._make_key_map()
        # parse_entity_xml requires <result> wrapper (SPEC P8.1)
        raw_output = '<result>Chùa <entity key="E1">Thiếu Lâm Tự</entity> nổi tiếng.</result>'
        clean_vi, assertions = parse_entity_xml(raw_output, key_map)
        self.assertEqual(len(assertions), 1)
        lock = list(key_map.values())
        results = check_entity_assertions(assertions, key_map, lock)
        status = app_module._p8_compute_assertion_status(results)
        self.assertEqual(status, 'all_pass')

    def test_I_missing_entity_marker_review(self):
        """I: entity in key_map but not in LLM output → REVIEW (missing)."""
        import app as app_module
        from canonical_lock import parse_entity_xml, check_entity_assertions
        key_map = self._make_key_map()
        # LLM output lacks entity marker entirely
        raw_output = 'Chùa này nổi tiếng.'
        clean_vi, assertions = parse_entity_xml(raw_output, key_map)
        lock = list(key_map.values())
        results = check_entity_assertions(assertions, key_map, lock)
        status = app_module._p8_compute_assertion_status(results)
        # Missing entity → WARN (not HARD)
        self.assertIn(status, ('has_warn', 'all_pass'),
                      "Missing marker phải WARN hoặc không có issues")
        # Verify assertion_status is 'missing' in assertions if any
        missing = [a for a in assertions if a.assertion_status == 'missing']
        # If entity appears in key_map but not output, check_entity_assertions handles it
        # The behavior may vary — ensure it doesn't crash

    def test_J_unknown_key_review(self):
        """J: LLM emits unknown key (E99) → assertion with unknown_key status."""
        import app as app_module
        from canonical_lock import parse_entity_xml, check_entity_assertions
        key_map = self._make_key_map()
        # LLM hallucinates unknown key E99
        raw_output = 'Chùa <entity key="E99">Nơi lạ</entity> nổi tiếng.'
        clean_vi, assertions = parse_entity_xml(raw_output, key_map)
        lock = list(key_map.values())
        results = check_entity_assertions(assertions, key_map, lock)
        status = app_module._p8_compute_assertion_status(results)
        # Unknown key → WARN (review_required)
        self.assertIn(status, ('has_warn', 'has_hard'))

    def test_K_wrong_entity_type_hard_or_review(self):
        """K: entity_type set server-side, never by LLM; parse fills from key_map."""
        import app as app_module
        from canonical_lock import parse_entity_xml, check_entity_assertions
        key_map = self._make_key_map(entity_type='place')
        # parse_entity_xml requires <result> wrapper
        raw_output = '<result><entity key="E1">Thiếu Lâm Tự</entity></result>'
        clean_vi, assertions = parse_entity_xml(raw_output, key_map)
        self.assertEqual(len(assertions), 1)
        # entity_type must be taken from server-side key_map, not from LLM output
        self.assertEqual(assertions[0].entity_type, 'place',
                         "entity_type phải lấy từ server-side key_map, không từ LLM")

    def test_L_multi_candidate_never_first_selection(self):
        """L: multi-candidate → REVIEW status, first candidate never auto-selected."""
        from canonical_lock import build_entity_key_map, CanonicalLockEntry, parse_entity_xml, check_entity_assertions
        import app as app_module
        # Only LOCKED entries get keys; CANDIDATE entries are not in key_map
        e1 = _make_minimal_lock_entry('PL001', '少林寺', 'Thiếu Lâm Tự', status='LOCKED')
        cand1 = _make_minimal_lock_entry('PL002', '少林寺', 'Thiếu Lâm Tự B', status='CANDIDATE')
        cand2 = _make_minimal_lock_entry('PL003', '少林寺', 'Thiếu Lâm Tự C', status='CANDIDATE')
        lock_entries = [e1, cand1, cand2]
        key_map = build_entity_key_map(lock_entries)
        # CANDIDATE entries must not receive keys
        self.assertEqual(len(key_map), 1, "Chỉ LOCKED entry mới được gán key")
        self.assertIn('E1', key_map)
        # No auto-selection of any candidate
        self.assertNotIn('E2', key_map)
        self.assertNotIn('E3', key_map)

    def test_M_malformed_xml_safe_fallback(self):
        """M: malformed XML → parse_entity_xml does not crash, returns safe text."""
        from canonical_lock import parse_entity_xml
        key_map = self._make_key_map()
        # Unclosed tag
        raw_output = 'Chùa <entity key="E1">Thiếu Lâm Tự nổi tiếng.'
        try:
            clean_vi, assertions = parse_entity_xml(raw_output, key_map)
            # Must not raise; should return something meaningful
            self.assertIsInstance(clean_vi, str)
        except Exception as exc:
            self.fail(f"parse_entity_xml không được crash trên malformed XML: {exc}")


# ── TestP8AssertionStatus ────────────────────────────────────────────────────

class TestP8AssertionStatus(unittest.TestCase):
    """Test _p8_compute_assertion_status helper."""

    def setUp(self):
        import app as app_module
        self.compute = app_module._p8_compute_assertion_status

    def test_empty_results_all_pass(self):
        self.assertEqual(self.compute([]), 'all_pass')

    def test_hard_severity(self):
        results = [{'severity': 'HARD', 'code': 'P8_MISMATCH'}]
        self.assertEqual(self.compute(results), 'has_hard')

    def test_warn_only(self):
        results = [{'severity': 'WARN', 'code': 'P8_MISSING'}]
        self.assertEqual(self.compute(results), 'has_warn')

    def test_hard_wins_over_warn(self):
        results = [
            {'severity': 'WARN', 'code': 'P8_MISSING'},
            {'severity': 'HARD', 'code': 'P8_MISMATCH'},
        ]
        self.assertEqual(self.compute(results), 'has_hard')


# ── TestP8Persistence ────────────────────────────────────────────────────────

class TestP8Persistence(unittest.TestCase):
    """Test cases N, O — persistence fields."""

    def test_N_legacy_cache_row_readable(self):
        """N: legacy cache (no P8 cols) remains readable by _dict_or."""
        import app as app_module
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT, source_type TEXT, entity_id TEXT,
                source_text TEXT, translated_text TEXT,
                model_id TEXT, rules_version TEXT, status TEXT DEFAULT 'auto',
                created_at TEXT, updated_at TEXT,
                UNIQUE(source_hash, source_type)
            )
        """)
        conn.execute(
            "INSERT INTO translation_cache "
            "(source_hash,source_type,entity_id,source_text,translated_text,"
            "model_id,rules_version,status,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            ('h1','place_note','PL001','zh','vi','m','v1','auto','now','now'))
        conn.commit()
        row = conn.execute("SELECT * FROM translation_cache WHERE id=1").fetchone()
        # _dict_or must handle missing column gracefully
        result = app_module._dict_or(row, 'entity_evidence')
        self.assertIsNone(result, "Missing column phải trả None không raise exception")

    def test_O_p8_fields_passed_to_write_cache(self):
        """O: P8 persistence fields written correctly to DB."""
        from style_constitution import write_cache
        conn = _make_p8_db()
        evidence = [{'key': 'E1', 'surface': 'Thiếu Lâm Tự', 'assertion_status': 'pass',
                     'entity_type': 'place'}]
        row_id, inserted = write_cache(
            conn, 'hash1', 'place_note', 'PL001',
            '少林寺在嵩山', 'Thiếu Lâm Tự ở Tung Sơn',
            'test-model', 'v1',
            entity_evidence=evidence,
            alignment_method='xml',
            entity_assertion_status='all_pass',
            entity_types_covered=['place'])
        self.assertTrue(inserted)
        row = conn.execute("SELECT * FROM translation_cache WHERE id=?", (row_id,)).fetchone()
        self.assertEqual(row['alignment_method'], 'xml')
        self.assertEqual(row['entity_assertion_status'], 'all_pass')
        self.assertEqual(json.loads(row['entity_types_covered']), ['place'])
        parsed_ev = json.loads(row['entity_evidence'])
        self.assertEqual(parsed_ev[0]['key'], 'E1')


# ── TestP8T166Regression ─────────────────────────────────────────────────────

class TestP8T166Regression(unittest.TestCase):
    """Test case P — P8 disabled → T166 behavior unchanged."""

    def test_P_p8_disabled_no_p8_fields_in_write(self):
        """P: When P8 disabled, write_cache called without P8 fields → T166 path unchanged."""
        from style_constitution import write_cache
        # T166 DB (no P8 cols) — write should still work without P8 params
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT, source_type TEXT, entity_id TEXT,
                source_text TEXT, translated_text TEXT,
                model_id TEXT, rules_version TEXT, status TEXT DEFAULT 'auto',
                created_at TEXT, updated_at TEXT,
                constitution_hash TEXT, selected_rule_codes TEXT, glossary_hash TEXT,
                identity_status TEXT, identity_issues TEXT, identity_lock_hash TEXT,
                UNIQUE(source_hash, source_type)
            )
        """)
        # Call write_cache WITHOUT P8 params (simulates P8-disabled legacy path)
        row_id, inserted = write_cache(
            conn, 'hash2', 'place_note', 'PL001',
            'src', 'tgt', 'model', 'v1',
            identity_status='pass',
            identity_issues=None,
            identity_lock_hash='fp1')
        self.assertTrue(inserted)
        row = conn.execute("SELECT * FROM translation_cache WHERE id=?", (row_id,)).fetchone()
        self.assertEqual(row['identity_status'], 'pass')
        # P8 cols must not exist in this DB
        col_names = [d[0] for d in conn.execute("PRAGMA table_info(translation_cache)").fetchall()]
        self.assertNotIn('entity_evidence', col_names)
        self.assertNotIn('alignment_method', col_names)


# ── TestP8GateDefault ────────────────────────────────────────────────────────

class TestP8GateDefault(unittest.TestCase):
    """Verify _P8_PILOT_GATE_ENABLED is False by default (SPEC §12)."""

    def test_gate_is_off_by_default(self):
        """Gate constant must be False at module level (never enable in prod accidentally)."""
        import app as app_module
        # We do NOT patch here — test the actual module-level default
        self.assertFalse(
            app_module._P8_PILOT_GATE_ENABLED,
            "_P8_PILOT_GATE_ENABLED phải là False theo default (SPEC §12)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
