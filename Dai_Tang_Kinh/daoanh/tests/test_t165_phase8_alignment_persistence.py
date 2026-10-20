# -*- coding: utf-8 -*-
"""test_t165_phase8_alignment_persistence.py — T165-P8.2 persistence/cache/hash contract.

Test cases A-O:
  A: constitution_hash differs with alignment_method='xml' vs omitted
  B: constitution_hash SAME for alignment_method=None vs 'none' (mass-miss safe)
  C: write_cache round-trip stores entity_evidence + alignment_method
  D: write_cache round-trip stores entity_assertion_status + entity_types_covered
  E: write_cache — pre-P8 DB (no entity_evidence col) succeeds silently (backward compat)
  F: write_cache — pre-T166 DB (no identity_status col) still works (full backward compat)
  G: write_cache — pre-T165 DB (no constitution_hash col) still inserts legacy row
  H: write_cache edited-row guard works with P8 params passed
  I: entity_evidence serialized as JSON in DB
  J: entity_types_covered serialized as JSON in DB
  K: alignment_method='none' → constitution_hash equal to no alignment_method
  L: alignment_method='xml' + alignment_method='json' produce different hashes
  M: style_lock alignment_method param flows into lock dict + constitution_hash
  N: migration script _sql_plan() returns exactly 4 P8 cols for translation_cache
  O: migration script --stats runs without error on empty in-memory DB
"""
import json
import sqlite3
import sys
import os
import unittest

# PATH setup
HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
sys.path.insert(0, DAOANH)

# ── helpers ─────────────────────────────────────────────────────────────────

def _make_db_p8():
    """In-memory DB với đủ schema T165 + T166 + P8.2 (4 tier đầy đủ)."""
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
    conn.execute("""
        CREATE TABLE translation_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code TEXT, rule_text TEXT, status TEXT DEFAULT 'active',
            identity_lock_policy TEXT DEFAULT 'P-PARTIAL'
        )
    """)
    conn.execute("""
        CREATE TABLE translation_glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_zh TEXT, term_vi TEXT, is_locked INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE translation_exemplar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zh TEXT, vi TEXT, source_label TEXT, is_active INTEGER DEFAULT 1,
            length_zh INTEGER DEFAULT 0
        )
    """)
    return conn


def _make_db_t166():
    """In-memory DB T165+T166 nhưng KHÔNG có P8.2 cols."""
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
    conn.execute("CREATE TABLE translation_glossary (id INTEGER PRIMARY KEY, term_zh TEXT, term_vi TEXT, is_locked INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE translation_exemplar (id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT, is_active INTEGER DEFAULT 1, length_zh INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE translation_rules (id INTEGER PRIMARY KEY, rule_code TEXT, rule_text TEXT, status TEXT DEFAULT 'active')")
    return conn


def _make_db_t165():
    """In-memory DB T165 nhưng KHÔNG có T166/P8 cols."""
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
            UNIQUE(source_hash, source_type)
        )
    """)
    conn.execute("CREATE TABLE translation_glossary (id INTEGER PRIMARY KEY, term_zh TEXT, term_vi TEXT, is_locked INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE translation_exemplar (id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT, is_active INTEGER DEFAULT 1, length_zh INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE translation_rules (id INTEGER PRIMARY KEY, rule_code TEXT, rule_text TEXT, status TEXT DEFAULT 'active')")
    return conn


def _make_db_legacy():
    """In-memory DB không có cột T165 (legacy — pre-migration)."""
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
    return conn


def _minimal_lock(extra=None):
    """Lock tối giản cho constitution_hash test."""
    lock = {
        'rules': [],
        'glossary': [],
        'exemplar': [],
        'known_pending': [],
        'prompt_label': '',
        'json_mode': False,
        't166_lock_fingerprint': '',
        'extra_hash': [],
    }
    if extra:
        lock.update(extra)
    return lock


def _write(conn, **kwargs):
    """Wrapper tiện lợi cho write_cache."""
    from style_constitution import write_cache
    defaults = dict(
        src_hash='testhash', source_type='place', entity_id='E1',
        source_text='src', translated_text='tgt',
        model_id='test-model', rules_version='v1',
    )
    defaults.update(kwargs)
    return write_cache(conn, **defaults)


# ── Test classes ─────────────────────────────────────────────────────────────

class TestConstitutionHashP8(unittest.TestCase):
    """Test cases A, B, K, L — constitution_hash với alignment_method."""

    def setUp(self):
        from style_constitution import constitution_hash
        self.constitution_hash = constitution_hash

    def test_A_xml_differs_from_omitted(self):
        """A: alignment_method='xml' → hash khác với không có alignment_method."""
        lock_base = _minimal_lock()
        lock_xml = _minimal_lock({'alignment_method': 'xml'})
        h_base = self.constitution_hash(lock_base)
        h_xml = self.constitution_hash(lock_xml)
        self.assertNotEqual(h_base, h_xml,
                            "alignment_method='xml' phải tạo hash khác")

    def test_B_none_same_as_omitted(self):
        """B: alignment_method='none' → hash BẰNG với không có (mass-miss safe)."""
        lock_base = _minimal_lock()
        lock_none = _minimal_lock({'alignment_method': 'none'})
        h_base = self.constitution_hash(lock_base)
        h_none = self.constitution_hash(lock_none)
        self.assertEqual(h_base, h_none,
                         "alignment_method='none' phải cho hash bằng với omitted (mass-miss safe)")

    def test_K_none_equals_no_alignment(self):
        """K: alignment_method=None (Python None) → hash bằng với 'none'."""
        lock_none_str = _minimal_lock({'alignment_method': 'none'})
        lock_none_py = _minimal_lock({'alignment_method': None})
        h_str = self.constitution_hash(lock_none_str)
        h_py = self.constitution_hash(lock_none_py)
        self.assertEqual(h_str, h_py,
                         "alignment_method=None phải cho hash bằng 'none'")

    def test_L_xml_differs_from_json_method(self):
        """L: alignment_method='xml' vs 'json' → hash khác nhau."""
        lock_xml = _minimal_lock({'alignment_method': 'xml'})
        lock_json = _minimal_lock({'alignment_method': 'json'})
        h_xml = self.constitution_hash(lock_xml)
        h_json = self.constitution_hash(lock_json)
        self.assertNotEqual(h_xml, h_json,
                            "alignment_method='xml' vs 'json' phải cho hash khác nhau")


class TestWriteCacheP8(unittest.TestCase):
    """Test cases C, D, H, I, J — write_cache round-trip với P8.2 params."""

    def test_C_entity_evidence_alignment_method_stored(self):
        """C: write_cache lưu entity_evidence + alignment_method vào DB."""
        conn = _make_db_p8()
        evidence = [{'key': 'E1', 'surface': 'Thiếu Lâm Tự', 'assertion_status': 'pass'}]
        row_id, inserted = _write(
            conn,
            entity_evidence=evidence,
            alignment_method='xml',
        )
        self.assertTrue(inserted)
        row = conn.execute("SELECT * FROM translation_cache WHERE id=?", (row_id,)).fetchone()
        self.assertEqual(row['alignment_method'], 'xml')
        parsed = json.loads(row['entity_evidence'])
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['key'], 'E1')

    def test_D_assertion_status_types_covered_stored(self):
        """D: write_cache lưu entity_assertion_status + entity_types_covered."""
        conn = _make_db_p8()
        types_covered = ['place', 'person']
        row_id, inserted = _write(
            conn,
            entity_assertion_status='all_pass',
            entity_types_covered=types_covered,
        )
        self.assertTrue(inserted)
        row = conn.execute("SELECT * FROM translation_cache WHERE id=?", (row_id,)).fetchone()
        self.assertEqual(row['entity_assertion_status'], 'all_pass')
        parsed_types = json.loads(row['entity_types_covered'])
        self.assertEqual(sorted(parsed_types), ['person', 'place'])

    def test_H_edited_guard_works_with_p8_params(self):
        """H: edited-row guard vẫn hoạt động khi pass P8 params."""
        conn = _make_db_p8()
        conn.execute(
            "INSERT INTO translation_cache "
            "(source_hash, source_type, entity_id, source_text, translated_text, "
            "model_id, rules_version, status, created_at, updated_at, constitution_hash) "
            "VALUES ('testhash','place','E1','src','tgt','m','v1','edited','now','now','ch1')"
        )
        conn.commit()
        row_id, inserted = _write(
            conn, src_hash='testhash',
            entity_evidence=[{'key': 'E1'}],
            alignment_method='xml',
        )
        self.assertFalse(inserted, "edited row guard phải trả False")

    def test_I_entity_evidence_is_json_in_db(self):
        """I: entity_evidence được serialize thành JSON string trong DB."""
        conn = _make_db_p8()
        evidence = [{'key': 'E1', 'surface': '少林寺'}, {'key': 'E2', 'surface': '嵩山'}]
        row_id, _ = _write(conn, entity_evidence=evidence)
        raw = conn.execute(
            "SELECT entity_evidence FROM translation_cache WHERE id=?", (row_id,)
        ).fetchone()[0]
        self.assertIsInstance(raw, str, "entity_evidence phải là TEXT trong DB")
        parsed = json.loads(raw)
        self.assertEqual(len(parsed), 2)

    def test_J_entity_types_covered_is_json_in_db(self):
        """J: entity_types_covered được serialize thành JSON string trong DB."""
        conn = _make_db_p8()
        row_id, _ = _write(conn, entity_types_covered=['place'])
        raw = conn.execute(
            "SELECT entity_types_covered FROM translation_cache WHERE id=?", (row_id,)
        ).fetchone()[0]
        self.assertIsInstance(raw, str, "entity_types_covered phải là TEXT trong DB")
        self.assertEqual(json.loads(raw), ['place'])


class TestWriteCacheBackwardCompat(unittest.TestCase):
    """Test cases E, F, G — backward compatibility với DB chưa migrate."""

    def test_E_pre_p8_db_succeeds_silently(self):
        """E: DB T166 (không có entity_evidence col) → write_cache vẫn thành công."""
        conn = _make_db_t166()
        row_id, inserted = _write(
            conn,
            entity_evidence=[{'key': 'E1'}],
            alignment_method='xml',
            entity_assertion_status='all_pass',
        )
        self.assertTrue(inserted)
        self.assertIsNotNone(row_id)
        # P8 cols không tồn tại → không lưu được, nhưng KHÔNG raise error
        row = conn.execute("SELECT * FROM translation_cache WHERE id=?", (row_id,)).fetchone()
        self.assertEqual(row['identity_status'], None)

    def test_F_pre_t166_db_succeeds(self):
        """F: DB T165 (không có identity_status col) → write_cache vẫn thành công."""
        conn = _make_db_t165()
        row_id, inserted = _write(
            conn,
            identity_status='pass',
            entity_evidence=[{'key': 'E1'}],
            alignment_method='xml',
        )
        self.assertTrue(inserted)
        self.assertIsNotNone(row_id)
        row = conn.execute("SELECT * FROM translation_cache WHERE id=?", (row_id,)).fetchone()
        # Chỉ có constitution cols — không có identity / P8 cols
        self.assertIn('constitution_hash', row.keys())

    def test_G_legacy_db_no_constitution_hash_col_inserts(self):
        """G: DB legacy (không có constitution_hash) → insert thành công."""
        conn = _make_db_legacy()
        row_id, inserted = _write(
            conn,
            entity_evidence=[{'key': 'E1'}],
            alignment_method='xml',
        )
        self.assertTrue(inserted)
        self.assertIsNotNone(row_id)


class TestStyleLockP8(unittest.TestCase):
    """Test case M — style_lock với alignment_method param."""

    def _make_minimal_conn(self):
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE translation_rules (id INTEGER PRIMARY KEY, rule_code TEXT, rule_text TEXT, status TEXT DEFAULT 'active', priority INTEGER DEFAULT 0, labels TEXT, condition_zh INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE translation_glossary (id INTEGER PRIMARY KEY, term_zh TEXT, term_vi TEXT, is_locked INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE translation_exemplar (id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT, is_active INTEGER DEFAULT 1, length_zh INTEGER DEFAULT 0)")
        return conn

    def test_M_alignment_method_flows_into_lock_and_hash(self):
        """M: style_lock(alignment_method='xml') → lock['alignment_method']='xml' + hash khác."""
        from style_constitution import style_lock, constitution_hash
        conn = self._make_minimal_conn()
        lock_base = style_lock(conn)
        lock_xml = style_lock(conn, alignment_method='xml')
        self.assertEqual(lock_xml.get('alignment_method'), 'xml')
        h_base = lock_base['constitution_hash']
        h_xml = lock_xml['constitution_hash']
        self.assertNotEqual(h_base, h_xml,
                            "style_lock(alignment_method='xml') phải tạo hash khác")

    def test_M2_alignment_method_none_same_hash(self):
        """M2: style_lock(alignment_method=None) → hash bằng style_lock() mặc định."""
        from style_constitution import style_lock
        conn = self._make_minimal_conn()
        lock_base = style_lock(conn)
        lock_none = style_lock(conn, alignment_method=None)
        self.assertEqual(lock_base['constitution_hash'], lock_none['constitution_hash'])


class TestMigrationScript(unittest.TestCase):
    """Test cases N, O — migration script helpers."""

    def setUp(self):
        sys.path.insert(0, os.path.join(DAOANH, 'scripts'))
        import importlib
        self.migrate = importlib.import_module('t165_phase8_alignment_migrate')

    def test_N_sql_plan_has_4_p8_cols(self):
        """N: _sql_plan() trả về đúng 4 cột P8 cho translation_cache."""
        plan = self.migrate._sql_plan()
        tc_cols = [col for (table, col, ddl) in plan if table == 'translation_cache']
        self.assertEqual(len(tc_cols), 4, f"Phải có đúng 4 cột P8, thực tế: {tc_cols}")
        self.assertIn('entity_evidence', tc_cols)
        self.assertIn('alignment_method', tc_cols)
        self.assertIn('entity_assertion_status', tc_cols)
        self.assertIn('entity_types_covered', tc_cols)

    def test_O_stats_runs_without_error_on_empty_db(self):
        """O: _stats() chạy được trên DB rỗng (chưa có table) mà không crash."""
        conn = sqlite3.connect(':memory:')
        # Không tạo bảng — _stats phải handle gracefully
        try:
            self.migrate._stats(conn)
        except Exception as exc:
            self.fail(f"_stats() crash trên DB rỗng: {exc}")
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
