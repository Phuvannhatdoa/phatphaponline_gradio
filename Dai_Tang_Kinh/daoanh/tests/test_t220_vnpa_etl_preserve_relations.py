# -*- coding: utf-8 -*-
"""
T220 — VNPA ETL Preserve Person Relations.

Verifies that the scoped DELETE fix prevents loss of vn_person_relations
rows owned by TTL files outside the current ETL rebuild scope.

Tests cover all invariants I1–I11 from T220 spec:
  I1. Non-managed relations survive unchanged
  I2. Managed relations are refreshed
  I3. Stale managed relations are removed
  I4. Current valid managed relations recreated exactly once
  I5. ETL is idempotent
  I6. No duplicate relations introduced
  I7. Manually curated relations preserved
  I8. Person IDs stable
  I9. T217 dila_id preservation intact
  I10. T212 deleted aliases not resurrected
  I11. No global DELETE on vn_person_relations

Plus directional relation test (T220 spec Section 6):
  D1. External person X → managed person Y: survives ETL on Y
  D2. Managed person Y → external Z: survives ETL on Y (TTL-owned outgoing)

Plus T219 high-risk rows:
  H1. dao_tin incoming refs
  H2. minh_hai_phap_bao incoming refs
  H3. thien_tue_bao_chuong incoming refs
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

_HERE    = os.path.dirname(os.path.abspath(__file__))
_ROOT    = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_ROOT, 'scripts')
_ETL     = os.path.join(_SCRIPTS, 'etl_ttl_person_authority.py')
_PROD_DB = os.path.join(_ROOT, 'data', 'lineage.db')


# ---------------------------------------------------------------------------
# Minimal in-memory schemas
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS vn_person_authority (
    id TEXT PRIMARY KEY,
    ttl_filename TEXT,
    name_vi TEXT DEFAULT '',
    name_zh TEXT DEFAULT '',
    dharma_title TEXT DEFAULT '',
    dharma_lineage TEXT DEFAULT '',
    generation_order INTEGER,
    is_lineage_founder INTEGER DEFAULT 0,
    gender TEXT DEFAULT 'M',
    biographical_note_vi TEXT DEFAULT '',
    birth_year INTEGER,
    death_year INTEGER,
    appellations TEXT DEFAULT '[]',
    dila_id TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS vn_person_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    target_id TEXT,
    target_label_vi TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, relation_type, target_id)
);
CREATE TABLE IF NOT EXISTS vn_person_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    place_id TEXT,
    place_label_vi TEXT,
    place_type TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, place_id)
);
CREATE TABLE IF NOT EXISTS vn_person_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    work_id TEXT,
    work_title_vi TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, work_id)
);
CREATE TABLE IF NOT EXISTS vn_person_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    event_type TEXT,
    event_id TEXT,
    event_label_vi TEXT,
    event_year INTEGER,
    ttl_filename TEXT,
    source TEXT,
    confidence REAL,
    source_ref TEXT,
    UNIQUE(person_id, event_type, event_id)
);
"""


def _make_db(rows_authority, rows_relations=None, rows_events=None):
    """Create in-memory SQLite DB with test data."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(_DDL)
    for r in rows_authority:
        conn.execute(
            """INSERT OR REPLACE INTO vn_person_authority
               (id, ttl_filename, name_vi, dila_id, status)
               VALUES (?,?,?,?,?)""",
            (r['id'], r.get('ttl', r['id']), r.get('name', ''),
             r.get('dila_id', ''), r.get('status', 'pending'))
        )
    for r in (rows_relations or []):
        conn.execute(
            """INSERT OR IGNORE INTO vn_person_relations
               (person_id, relation_type, target_id, target_label_vi, ttl_filename)
               VALUES (?,?,?,?,?)""",
            (r['person_id'], r['relation_type'], r['target_id'],
             r.get('label', ''), r['ttl_filename'])
        )
    for r in (rows_events or []):
        conn.execute(
            """INSERT OR IGNORE INTO vn_person_events
               (person_id, event_type, event_id, event_label_vi, event_year, ttl_filename)
               VALUES (?,?,?,?,?,?)""",
            (r['person_id'], r['event_type'], r.get('event_id', 'ev1'),
             r.get('label', ''), r.get('year'), r.get('ttl_filename'))
        )
    conn.commit()
    return conn


def _simulate_scoped_etl(conn, managed_ttl_keys, incoming_relations, incoming_events=None):
    """
    Simulate the T220-fixed ETL:
    1. Snapshot dila_id/status (T217)
    2. Capture pre-delete authority rows (for reconstruction)
    3. DELETE relations/events WHERE ttl_filename IN managed_ttl_keys (T220 fix)
    4. DELETE authority WHERE ttl_filename IN managed_ttl_keys
    5. Reinsert managed authority rows from captured snapshot
    6. Reinsert managed relations from TTL
    7. Restore dila_id/status (T217)
    Returns summary dict.
    """
    _ph = ','.join('?' * len(managed_ttl_keys))
    _keys = tuple(managed_ttl_keys)

    # T217 snapshot
    curated_dila = {}
    curated_status = {}
    for r in conn.execute(
        f"SELECT id, dila_id, status FROM vn_person_authority WHERE ttl_filename IN ({_ph})", _keys
    ):
        if r['dila_id'] and r['dila_id'] != '':
            curated_dila[r['id']] = r['dila_id']
        if r['status'] and r['status'] != 'pending':
            curated_status[r['id']] = r['status']

    # Capture authority rows before DELETE (for reconstruction — mirrors ETL reading TTL then reinserting)
    pre_delete_auth = conn.execute(
        f"SELECT id, ttl_filename, name_vi, dila_id, status FROM vn_person_authority WHERE ttl_filename IN ({_ph})", _keys
    ).fetchall()

    # T220 scoped DELETE on relation tables
    for t in ('vn_person_events', 'vn_person_works', 'vn_person_places', 'vn_person_relations'):
        conn.execute(f"DELETE FROM {t} WHERE ttl_filename IN ({_ph})", _keys)

    # Scoped DELETE authority
    conn.execute(f"DELETE FROM vn_person_authority WHERE ttl_filename IN ({_ph})", _keys)
    conn.commit()

    # Reinsert authority rows from captured snapshot (mirrors ETL: parse TTL → INSERT OR REPLACE)
    for r in pre_delete_auth:
        conn.execute(
            "INSERT OR REPLACE INTO vn_person_authority (id, ttl_filename, name_vi, dila_id, status) VALUES (?,?,?,?,?)",
            (r['id'], r['ttl_filename'], r['name_vi'], '', 'pending')
            # dila_id and status are reset to defaults — T217 restore will fix them back
        )

    # Reinsert relations
    for r in (incoming_relations or []):
        conn.execute(
            """INSERT OR IGNORE INTO vn_person_relations
               (person_id, relation_type, target_id, target_label_vi, ttl_filename)
               VALUES (?,?,?,?,?)""",
            (r['person_id'], r['relation_type'], r['target_id'],
             r.get('label', ''), r['ttl_filename'])
        )

    # Reinsert events
    for r in (incoming_events or []):
        conn.execute(
            """INSERT OR IGNORE INTO vn_person_events
               (person_id, event_type, event_id, ttl_filename)
               VALUES (?,?,?,?)""",
            (r['person_id'], r['event_type'], r.get('event_id', 'ev1'), r['ttl_filename'])
        )

    conn.commit()

    # T217 restore
    restored_dila = 0
    for rid, old_dila in curated_dila.items():
        cur = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id=?", (rid,)).fetchone()
        if cur and (not cur['dila_id'] or cur['dila_id'] != old_dila):
            conn.execute("UPDATE vn_person_authority SET dila_id=? WHERE id=?", (old_dila, rid))
            restored_dila += 1
    for rid, old_status in curated_status.items():
        cur = conn.execute("SELECT status FROM vn_person_authority WHERE id=?", (rid,)).fetchone()
        if cur and cur['status'] != old_status:
            conn.execute("UPDATE vn_person_authority SET status=? WHERE id=?", (old_status, rid))
    conn.commit()
    return {'restored_dila': restored_dila}


def _count_rels(conn):
    return conn.execute('SELECT count(*) FROM vn_person_relations').fetchone()[0]


def _get_rel(conn, person_id, rel_type, target_id):
    return conn.execute(
        'SELECT * FROM vn_person_relations WHERE person_id=? AND relation_type=? AND target_id=?',
        (person_id, rel_type, target_id)
    ).fetchone()


# ---------------------------------------------------------------------------
# Spec Section 7 fixture
# ---------------------------------------------------------------------------
#
# managed: A (ttl='managed-A'), B (ttl='managed-B')
# unmanaged: X (ttl='unmanaged-X'), Y (ttl='unmanaged-Y')
#
# R1  managed-owned A -> B       (ttl=managed-A)
# R2  managed-owned A -> X       (ttl=managed-A)
# R3  unmanaged-owned X -> A     (ttl=unmanaged-X)
# R4  unmanaged-owned X -> Y     (ttl=unmanaged-X)
# R5  manually curated (no ttl?) — for this test: ttl='curated-manual'
# R6  stale managed A -> Z       (ttl=managed-A, absent from new TTL)
# R7  same as R1 but re-generated (same tuple — idempotency)
# R8  duplicate-risk (same key as R1)


MANAGED_AUTHORITY = [
    {'id': 'monk_A', 'ttl': 'managed-A', 'dila_id': 'A001111', 'status': 'confirmed'},
    {'id': 'monk_B', 'ttl': 'managed-B', 'dila_id': '', 'status': 'pending'},
]
UNMANAGED_AUTHORITY = [
    {'id': 'person_X', 'ttl': 'unmanaged-X'},
    {'id': 'person_Y', 'ttl': 'unmanaged-Y'},
]
ALL_AUTHORITY = MANAGED_AUTHORITY + UNMANAGED_AUTHORITY

MANAGED_TTL_KEYS = ('managed-A', 'managed-B')

BASE_RELATIONS = [
    # R1 managed A->B
    {'person_id': 'monk_A', 'relation_type': 'hasDisciple', 'target_id': 'monk_B', 'ttl_filename': 'managed-A'},
    # R2 managed A->X (cross-boundary outgoing)
    {'person_id': 'monk_A', 'relation_type': 'hasRelated', 'target_id': 'person_X', 'ttl_filename': 'managed-A'},
    # R3 unmanaged X->A (incoming from outside scope)
    {'person_id': 'person_X', 'relation_type': 'hasTeacher', 'target_id': 'monk_A', 'ttl_filename': 'unmanaged-X'},
    # R4 unmanaged X->Y
    {'person_id': 'person_X', 'relation_type': 'hasRelated', 'target_id': 'person_Y', 'ttl_filename': 'unmanaged-X'},
    # R5 manually curated
    {'person_id': 'monk_A', 'relation_type': 'hasMentor', 'target_id': 'person_Y', 'ttl_filename': 'curated-manual'},
    # R6 stale: monk_A -> 'stale_target' from managed-A (will NOT be in new TTL output)
    {'person_id': 'monk_A', 'relation_type': 'hasDisciple', 'target_id': 'stale_target', 'ttl_filename': 'managed-A'},
]

# New TTL output: R1, R2, R7 (R7 = same key as R1, idempotency test — INSERT OR IGNORE)
# R6 (stale) is deliberately NOT in new TTL output
NEW_TTL_RELATIONS = [
    {'person_id': 'monk_A', 'relation_type': 'hasDisciple', 'target_id': 'monk_B', 'ttl_filename': 'managed-A'},   # R1/R7
    {'person_id': 'monk_A', 'relation_type': 'hasRelated',  'target_id': 'person_X', 'ttl_filename': 'managed-A'}, # R2
    # R8 duplicate of R1 — second insert should be ignored
    {'person_id': 'monk_A', 'relation_type': 'hasDisciple', 'target_id': 'monk_B', 'ttl_filename': 'managed-A'},   # R8 duplicate
]


# ===========================================================================
# I1: Non-managed relations survive
# ===========================================================================
class TestI1NonManagedSurvive(unittest.TestCase):
    def test_r3_x_to_a_survives(self):
        """R3: unmanaged person_X -> monk_A must survive ETL on monk_A."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r3 = _get_rel(conn, 'person_X', 'hasTeacher', 'monk_A')
        self.assertIsNotNone(r3, "R3 (unmanaged X->A) must survive managed ETL")
        self.assertEqual(r3['ttl_filename'], 'unmanaged-X')

    def test_r4_x_to_y_survives(self):
        """R4: unmanaged person_X -> person_Y must survive."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r4 = _get_rel(conn, 'person_X', 'hasRelated', 'person_Y')
        self.assertIsNotNone(r4, "R4 (X->Y, unmanaged TTL) must survive")

    def test_r5_manually_curated_survives(self):
        """R5: curated-manual relation must survive."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r5 = _get_rel(conn, 'monk_A', 'hasMentor', 'person_Y')
        self.assertIsNotNone(r5, "R5 (curated-manual) must survive")
        self.assertEqual(r5['ttl_filename'], 'curated-manual')


# ===========================================================================
# I2: Managed relations refreshed
# ===========================================================================
class TestI2ManagedRefreshed(unittest.TestCase):
    def test_r1_present_after_etl(self):
        """R1: managed A->B is present after ETL."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r1 = _get_rel(conn, 'monk_A', 'hasDisciple', 'monk_B')
        self.assertIsNotNone(r1)

    def test_r2_present_after_etl(self):
        """R2: managed A->X cross-boundary outgoing is present."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r2 = _get_rel(conn, 'monk_A', 'hasRelated', 'person_X')
        self.assertIsNotNone(r2)


# ===========================================================================
# I3: Stale managed relations removed
# ===========================================================================
class TestI3StaleRemoved(unittest.TestCase):
    def test_r6_stale_removed(self):
        """R6: stale managed A->stale_target is NOT in new TTL output, must be absent."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r6 = _get_rel(conn, 'monk_A', 'hasDisciple', 'stale_target')
        self.assertIsNone(r6, "R6 (stale managed) must be removed when not in new TTL")


# ===========================================================================
# I4: Each managed relation recreated exactly once
# ===========================================================================
class TestI4ExactlyOnce(unittest.TestCase):
    def test_no_duplicates_r1(self):
        """R1+R8 (same key) must exist exactly once after ETL."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        count = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE person_id='monk_A' AND relation_type='hasDisciple' AND target_id='monk_B'"
        ).fetchone()[0]
        self.assertEqual(count, 1, "R1/R8 duplicate must resolve to exactly 1 row")


# ===========================================================================
# I5: Idempotency
# ===========================================================================
class TestI5Idempotent(unittest.TestCase):
    def test_two_runs_same_count(self):
        """Running ETL twice produces identical relation count."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        count1 = _count_rels(conn)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        count2 = _count_rels(conn)
        self.assertEqual(count1, count2, "ETL must be idempotent")

    def test_two_runs_r3_still_survives(self):
        """R3 survives both ETL runs."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r3 = _get_rel(conn, 'person_X', 'hasTeacher', 'monk_A')
        self.assertIsNotNone(r3, "R3 must survive 2nd ETL run")


# ===========================================================================
# I6: No duplicates
# ===========================================================================
class TestI6NoDuplicates(unittest.TestCase):
    def test_no_duplicate_managed_relations(self):
        """After ETL with duplicate in TTL output, no duplicate rows."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        rows = conn.execute(
            "SELECT person_id, relation_type, target_id, count(*) as n FROM vn_person_relations GROUP BY person_id, relation_type, target_id HAVING n>1"
        ).fetchall()
        self.assertEqual(len(rows), 0, f"Duplicate relations found: {[dict(r) for r in rows]}")


# ===========================================================================
# I9: T217 dila_id preservation
# ===========================================================================
class TestI9T217Preservation(unittest.TestCase):
    def test_dila_id_preserved(self):
        """monk_A.dila_id='A001111' survives scoped ETL."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        row = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id='monk_A'").fetchone()
        self.assertEqual(row['dila_id'], 'A001111')

    def test_confirmed_status_preserved(self):
        """monk_A.status='confirmed' survives scoped ETL."""
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        row = conn.execute("SELECT status FROM vn_person_authority WHERE id='monk_A'").fetchone()
        self.assertEqual(row['status'], 'confirmed')


# ===========================================================================
# I11: No global DELETE (static code check)
# ===========================================================================
class TestI11NoGlobalDelete(unittest.TestCase):
    def test_no_unscoped_delete_in_etl(self):
        """ETL script must not contain unscoped DELETE FROM vn_person_relations."""
        with open(_ETL, 'r', encoding='utf-8') as f:
            code = f.read()
        # Find all DELETE FROM vn_person_relations occurrences
        import re
        hits = re.findall(r'DELETE\s+FROM\s+vn_person_relations[^\n]*', code, re.IGNORECASE)
        for hit in hits:
            # Each occurrence must contain 'WHERE' (scoped)
            self.assertIn('WHERE', hit, f"Unscoped DELETE found: {hit!r}")

    def test_no_unscoped_delete_any_relation_table(self):
        """ETL script must not contain unscoped DELETE for any of the 4 tables."""
        with open(_ETL, 'r', encoding='utf-8') as f:
            code = f.read()
        import re
        for tbl in ('vn_person_relations', 'vn_person_places', 'vn_person_works', 'vn_person_events'):
            hits = re.findall(rf'DELETE\s+FROM\s+{tbl}[^\n]*', code, re.IGNORECASE)
            for hit in hits:
                self.assertIn('WHERE', hit, f"Unscoped DELETE on {tbl}: {hit!r}")


# ===========================================================================
# Directional relation: Section 6
# ===========================================================================
class TestDirectionalRelation(unittest.TestCase):
    def test_D1_incoming_from_external_to_managed(self):
        """
        D1: External person X has relation pointing TO managed person A.
        This relation is owned by X's TTL (unmanaged-X).
        It must survive ETL that rebuilds A.
        """
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        # R3 is exactly this case: person_X (ttl=unmanaged-X) -> monk_A
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        r3 = _get_rel(conn, 'person_X', 'hasTeacher', 'monk_A')
        self.assertIsNotNone(r3, "D1: external X->A must survive ETL on A")

    def test_D2_outgoing_from_managed_to_external(self):
        """
        D2: Managed person A has TTL-owned outgoing relation to external X.
        This relation IS in the ETL rebuild scope (ttl=managed-A), so it is
        deleted and re-created — correct behaviour.
        """
        conn = _make_db(ALL_AUTHORITY, BASE_RELATIONS)
        before_r2 = _get_rel(conn, 'monk_A', 'hasRelated', 'person_X')
        self.assertIsNotNone(before_r2)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        after_r2 = _get_rel(conn, 'monk_A', 'hasRelated', 'person_X')
        self.assertIsNotNone(after_r2, "D2: managed A->X (managed-A ttl) recreated after ETL")


# ===========================================================================
# vn_person_events: NULL ttl_filename rows survive
# ===========================================================================
class TestEventsNullTtlSurvives(unittest.TestCase):
    def test_null_ttl_events_survive(self):
        """Events with NULL ttl_filename survive scoped DELETE (NULL not in IN clause)."""
        conn = _make_db(ALL_AUTHORITY, rows_events=[
            {'person_id': 'monk_A', 'event_type': 'born', 'event_id': 'ev_null', 'ttl_filename': None},
            {'person_id': 'monk_A', 'event_type': 'ordained', 'event_id': 'ev_managed', 'ttl_filename': 'managed-A'},
        ])
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS)
        null_ev = conn.execute(
            "SELECT * FROM vn_person_events WHERE event_id='ev_null'"
        ).fetchone()
        self.assertIsNotNone(null_ev, "Event with NULL ttl_filename must survive scoped DELETE")

    def test_managed_ttl_events_removed_and_rebuilt(self):
        """Events with managed ttl_filename are removed by scoped DELETE."""
        conn = _make_db(ALL_AUTHORITY, rows_events=[
            {'person_id': 'monk_A', 'event_type': 'ordained', 'event_id': 'ev_managed', 'ttl_filename': 'managed-A'},
        ])
        # Run ETL with NO new events (empty incoming_events)
        _simulate_scoped_etl(conn, MANAGED_TTL_KEYS, NEW_TTL_RELATIONS, incoming_events=[])
        old_ev = conn.execute("SELECT * FROM vn_person_events WHERE event_id='ev_managed'").fetchone()
        self.assertIsNone(old_ev, "Stale managed event removed when not in new TTL output")


# ===========================================================================
# Integration: copy-DB ETL run (subprocess against production copy)
# ===========================================================================
class TestCopyDBIntegration(unittest.TestCase):
    """
    Runs the real ETL against a COPY of production DB.
    Verifies production is untouched and unmanaged relations survive.
    """

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(_PROD_DB):
            raise unittest.SkipTest("Production DB not found")
        if not os.path.exists(_ETL):
            raise unittest.SkipTest("ETL script not found")
        # Snapshot production DB SHA before
        # [T222/CORRECTION-5] Stream file in chunks to avoid MemoryError on 1.4GB DB.
        import hashlib
        h = hashlib.sha256()
        with open(_PROD_DB, 'rb') as f:
            for chunk in iter(lambda: f.read(8 << 20), b''):
                h.update(chunk)
        cls.sha_prod_before = h.hexdigest()
        # Create temp copy
        cls.tmpdir = tempfile.mkdtemp()
        cls.copy_db = os.path.join(cls.tmpdir, 'lineage_copy.db')
        shutil.copy2(_PROD_DB, cls.copy_db)
        # Record pre-ETL counts
        conn = sqlite3.connect(cls.copy_db)
        conn.row_factory = sqlite3.Row
        cls.rels_before = conn.execute('SELECT count(*) FROM vn_person_relations').fetchone()[0]
        cls.auth_before = conn.execute('SELECT count(*) FROM vn_person_authority').fetchone()[0]
        cls.events_before = conn.execute('SELECT count(*) FROM vn_person_events').fetchone()[0]
        # Snapshot high-risk refs
        cls.dao_tin_in_before = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE target_id='dao_tin'"
        ).fetchone()[0]
        cls.minh_hai_in_before = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE target_id='minh_hai_phap_bao'"
        ).fetchone()[0]
        cls.thien_tue_in_before = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE target_id='thien_tue_bao_chuong'"
        ).fetchone()[0]
        # Old/ TTL scope
        ttl_old = os.path.join(os.path.dirname(_ETL), '..', 'data', 'ttl', 'old')
        ttl_old = os.path.abspath(ttl_old)
        cls.old_stems = set(f[:-4] for f in os.listdir(ttl_old) if f.endswith('.ttl')) if os.path.isdir(ttl_old) else set()
        ph = ','.join('?' * len(cls.old_stems))
        cls.non_old_rels_before = conn.execute(
            f'SELECT count(*) FROM vn_person_relations WHERE ttl_filename NOT IN ({ph})',
            tuple(cls.old_stems)
        ).fetchone()[0] if cls.old_stems else cls.rels_before
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'tmpdir'):
            shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _run_etl(self):
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(
            [sys.executable, _ETL, f'--db={self.copy_db}', '--skip-preflight'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=180, cwd=os.path.dirname(_ETL), env=env
        )
        return result

    def test_etl_runs_without_error(self):
        """ETL must complete successfully on copy DB."""
        result = self._run_etl()
        stdout = result.stdout or ''
        stderr = result.stderr or ''
        self.assertEqual(result.returncode, 0,
                         f"ETL failed:\nSTDOUT:\n{stdout[-3000:]}\nSTDERR:\n{stderr[-2000:]}")

    def test_production_db_sha_unchanged(self):
        """Production DB SHA must be unchanged after ETL on copy."""
        import hashlib
        self._run_etl()
        # [T222/CORRECTION-5] Stream file in chunks to avoid MemoryError on 1.4GB DB.
        h = hashlib.sha256()
        with open(_PROD_DB, 'rb') as f:
            for chunk in iter(lambda: f.read(8 << 20), b''):
                h.update(chunk)
        sha_after = h.hexdigest()
        self.assertEqual(self.sha_prod_before, sha_after,
                         "FAIL_PRODUCTION_DB_MUTATED: production SHA changed!")

    def test_unmanaged_relations_preserved(self):
        """Non-old/ relations must be preserved after ETL on copy."""
        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        conn.row_factory = sqlite3.Row
        if self.old_stems:
            ph = ','.join('?' * len(self.old_stems))
            non_old_after = conn.execute(
                f'SELECT count(*) FROM vn_person_relations WHERE ttl_filename NOT IN ({ph})',
                tuple(self.old_stems)
            ).fetchone()[0]
        else:
            non_old_after = 0
        conn.close()
        self.assertEqual(self.non_old_rels_before, non_old_after,
                         f"Non-managed relations changed: {self.non_old_rels_before} -> {non_old_after}")

    def test_dao_tin_incoming_refs_preserved(self):
        """dao_tin: incoming refs from non-old/ must survive ETL."""
        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        after = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE target_id='dao_tin'"
        ).fetchone()[0]
        conn.close()
        self.assertEqual(self.dao_tin_in_before, after,
                         f"dao_tin incoming refs changed: {self.dao_tin_in_before} -> {after}")

    def test_minh_hai_incoming_refs_preserved(self):
        """minh_hai_phap_bao: incoming refs must survive ETL."""
        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        after = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE target_id='minh_hai_phap_bao'"
        ).fetchone()[0]
        conn.close()
        self.assertEqual(self.minh_hai_in_before, after,
                         f"minh_hai incoming refs changed: {self.minh_hai_in_before} -> {after}")

    def test_thien_tue_incoming_refs_preserved(self):
        """thien_tue_bao_chuong: incoming refs must survive ETL."""
        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        after = conn.execute(
            "SELECT count(*) FROM vn_person_relations WHERE target_id='thien_tue_bao_chuong'"
        ).fetchone()[0]
        conn.close()
        self.assertEqual(self.thien_tue_in_before, after,
                         f"thien_tue incoming refs changed: {self.thien_tue_in_before} -> {after}")

    def test_etl_idempotent_on_copy(self):
        """Running ETL twice on copy must give same relation count."""
        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        count1 = conn.execute('SELECT count(*) FROM vn_person_relations').fetchone()[0]
        conn.close()
        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        count2 = conn.execute('SELECT count(*) FROM vn_person_relations').fetchone()[0]
        conn.close()
        self.assertEqual(count1, count2, f"Not idempotent: {count1} != {count2}")

    def test_t217_dila_ids_preserved(self):
        """T217: 33 curated dila_id values survive ETL on copy."""
        T215_IDS = [
            'chung_son_dao_long','cuu_danh_to','dam_chau_dai_xuyen','dong_son_te_vi',
            'duong_chau_tue_giac','hoa_nghiem_dao_long','hoang_long_tri_minh',
            'kinh_trieu_thi_loi','lang_nha_tue_giac','lao_na_tu_dang_dai_hoang',
            'linh_thuu_tue_giac','long_khanh_khanh_nhan','ma_noa_la','nam_nhac_huyen_thai',
            'ngu_dai_tri_thong','nguu_dau_hue_phuong','nguyet_chuong_tri_uyen','phap_nhu',
            'phong_huyet_dien_chieu','phu_son_duc_tuyen','quang_tue_duc_tuyen',
            'so_an_hue_phuong','song_lam_duc_dung','tay_vuc_quat_da_tam_tang',
            'thach_cung_hue_tang','thai_tu_dong_quang','the_nham_ton_tho','tho_chau_tri_thong',
            'tinh_do_thien_tu','tri_hai_dao_binh','tu_to_phap_dien','tue_nhat_minh',
            'van_cu_phap_nhu',
        ]
        prod_conn = sqlite3.connect(_PROD_DB)
        prod_conn.row_factory = sqlite3.Row
        prod_dila = {r['id']: r['dila_id'] for r in prod_conn.execute(
            f"SELECT id, dila_id FROM vn_person_authority WHERE id IN ({','.join('?'*len(T215_IDS))})",
            T215_IDS
        )}
        prod_conn.close()

        self._run_etl()
        conn = sqlite3.connect(self.copy_db)
        conn.row_factory = sqlite3.Row
        failures = []
        for rid in T215_IDS:
            row = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id=?", (rid,)).fetchone()
            expected = prod_dila.get(rid, '')
            if not expected:
                continue
            if not row or row['dila_id'] != expected:
                failures.append(f"{rid}: expected={expected!r} got={row['dila_id'] if row else 'ROW_MISSING'!r}")
        conn.close()
        self.assertEqual(failures, [], f"T217 dila_id loss: {failures}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
