# -*- coding: utf-8 -*-
"""
T217 — VNPA ETL Preservation Guard: isolated test suite.

Tests:
  A. dila_id: existing non-empty + incoming NULL   → preserve existing
  B. dila_id: existing non-empty + incoming ''     → preserve existing
  C. dila_id: existing NULL     + incoming non-empty → accept incoming
  D. dila_id: same value in both                  → unchanged
  E. dila_id: conflict (A123 vs A999)             → preserve existing, log
  F. dila_id: duplicate dila_id groups intact
  G. 33 T215 restored rows survive ETL rerun
  H. 4 T212 deleted aliases NOT resurrected
  I. Idempotency: run ETL twice → same result
  J. Transaction rollback on simulated failure
  K. No fuzzy/name-only matching
  L. Row-count sanity
  M. Existing unrelated rows preserved per ETL contract
  (Integration) G+H via actual ETL subprocess
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

# -- Paths -------------------------------------------------------------------
_HERE   = os.path.dirname(os.path.abspath(__file__))
_ROOT   = os.path.dirname(_HERE)                         # daoanh/
_SCRIPTS = os.path.join(_ROOT, 'scripts')
_ETL    = os.path.join(_SCRIPTS, 'etl_ttl_person_authority.py')
_PROD_DB = os.path.join(_ROOT, 'data', 'lineage.db')

# T215 33 rows that must survive ETL rerun
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

# T212 intentionally deleted aliases (must NOT be resurrected)
T212_DELETED = ['alias_A009319','alias_A010534','alias_A020120','alias_A044094']

# Minimal schema for unit-test DB
_VNPA_DDL = """
CREATE TABLE IF NOT EXISTS vn_person_authority (
    id TEXT PRIMARY KEY,
    ttl_filename TEXT,
    name_vi TEXT,
    dila_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# ---------------------------------------------------------------------------
# Helper: simulate the preservation logic extracted from etl_ttl_person_authority.py
# This mirrors the exact algorithm — do NOT drift from the ETL implementation.
# ---------------------------------------------------------------------------

def _snapshot(conn):
    """Snapshot curated fields before DELETE."""
    curated_dila   = {}
    curated_status = {}
    for r in conn.execute("SELECT id, dila_id, status FROM vn_person_authority"):
        if r['dila_id'] and r['dila_id'] != '':
            curated_dila[r['id']] = r['dila_id']
        if r['status'] and r['status'] != 'pending':
            curated_status[r['id']] = r['status']
    return curated_dila, curated_status


def _restore(conn, curated_dila, curated_status):
    """Restore curated fields after INSERT. Returns (restored_dila, conflict_dila, restored_status)."""
    restored_dila = conflict_dila = restored_status = 0
    for row_id, old_dila in curated_dila.items():
        cur = conn.execute(
            "SELECT dila_id FROM vn_person_authority WHERE id=?", (row_id,)
        ).fetchone()
        if cur is None:
            continue
        new_dila = cur['dila_id'] if cur['dila_id'] else ''
        if new_dila != old_dila:
            if new_dila and new_dila != '':
                conflict_dila += 1
            conn.execute(
                "UPDATE vn_person_authority SET dila_id=? WHERE id=?",
                (old_dila, row_id)
            )
            restored_dila += 1
    for row_id, old_status in curated_status.items():
        cur = conn.execute(
            "SELECT status FROM vn_person_authority WHERE id=?", (row_id,)
        ).fetchone()
        if cur is None:
            continue
        if cur['status'] != old_status:
            conn.execute(
                "UPDATE vn_person_authority SET status=? WHERE id=?",
                (old_status, row_id)
            )
            restored_status += 1
    conn.commit()
    return restored_dila, conflict_dila, restored_status


def _make_db(rows):
    """Create in-memory SQLite DB, insert rows, return connection."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(_VNPA_DDL)
    for r in rows:
        conn.execute(
            "INSERT INTO vn_person_authority (id, ttl_filename, name_vi, dila_id, status) VALUES (?,?,?,?,?)",
            (r['id'], r.get('ttl', r['id']), r.get('name', ''), r.get('dila_id'), r.get('status', 'pending'))
        )
    conn.commit()
    return conn


def _simulate_etl(conn, incoming_rows):
    """
    Simulate ETL: snapshot → DELETE → INSERT incoming → restore.
    incoming_rows: list of {id, dila_id, status}.
    """
    curated_dila, curated_status = _snapshot(conn)
    conn.execute("DELETE FROM vn_person_authority")
    conn.commit()
    for r in incoming_rows:
        conn.execute(
            "INSERT INTO vn_person_authority (id, dila_id, status) VALUES (?,?,?)",
            (r['id'], r.get('dila_id'), r.get('status', 'pending'))
        )
    conn.commit()
    return _restore(conn, curated_dila, curated_status)


def _get(conn, row_id, field):
    r = conn.execute(f"SELECT {field} FROM vn_person_authority WHERE id=?", (row_id,)).fetchone()
    return r[field] if r else None


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestPreservationLogic(unittest.TestCase):

    # A. existing non-empty + incoming NULL → preserve existing
    def test_A_preserve_over_incoming_null(self):
        conn = _make_db([{'id': 'monk_a', 'dila_id': 'A123', 'status': 'verified'}])
        _simulate_etl(conn, [{'id': 'monk_a', 'dila_id': None}])
        self.assertEqual(_get(conn, 'monk_a', 'dila_id'), 'A123')

    # B. existing non-empty + incoming '' → preserve existing
    def test_B_preserve_over_incoming_empty(self):
        conn = _make_db([{'id': 'monk_b', 'dila_id': 'A123'}])
        _simulate_etl(conn, [{'id': 'monk_b', 'dila_id': ''}])
        self.assertEqual(_get(conn, 'monk_b', 'dila_id'), 'A123')

    # C. existing NULL + incoming non-empty → accept incoming
    def test_C_accept_incoming_when_existing_null(self):
        conn = _make_db([{'id': 'monk_c', 'dila_id': None}])
        _simulate_etl(conn, [{'id': 'monk_c', 'dila_id': 'A123'}])
        self.assertEqual(_get(conn, 'monk_c', 'dila_id'), 'A123')

    # D. same value → unchanged
    def test_D_same_value_unchanged(self):
        conn = _make_db([{'id': 'monk_d', 'dila_id': 'A123'}])
        rd, cd, rs = _simulate_etl(conn, [{'id': 'monk_d', 'dila_id': 'A123'}])
        self.assertEqual(_get(conn, 'monk_d', 'dila_id'), 'A123')
        self.assertEqual(cd, 0)  # No conflict

    # E. conflict: existing A123, incoming A999 → preserve curated A123
    def test_E_conflict_preserves_curated(self):
        conn = _make_db([{'id': 'monk_e', 'dila_id': 'A123'}])
        rd, cd, rs = _simulate_etl(conn, [{'id': 'monk_e', 'dila_id': 'A999'}])
        self.assertEqual(_get(conn, 'monk_e', 'dila_id'), 'A123')
        self.assertEqual(cd, 1)  # Conflict logged

    # F. duplicate dila_id groups intact
    def test_F_duplicate_dila_id_group(self):
        conn = _make_db([
            {'id': 'monk_f1', 'dila_id': 'A047679'},
            {'id': 'monk_f2', 'dila_id': 'A047679'},
        ])
        _simulate_etl(conn, [
            {'id': 'monk_f1', 'dila_id': None},
            {'id': 'monk_f2', 'dila_id': None},
        ])
        self.assertEqual(_get(conn, 'monk_f1', 'dila_id'), 'A047679')
        self.assertEqual(_get(conn, 'monk_f2', 'dila_id'), 'A047679')

    # H. T212 deleted aliases NOT resurrected by restore
    def test_H_deleted_rows_not_resurrected(self):
        # Pre-ETL state: has alias row with curated dila_id
        conn = _make_db([
            {'id': 'alias_A009319', 'dila_id': 'A009319', 'status': 'alias_vi_suffix'},
            {'id': 'real_monk',    'dila_id': 'A111111', 'status': 'verified'},
        ])
        # ETL only creates real_monk (alias is not from TTL)
        _simulate_etl(conn, [{'id': 'real_monk', 'dila_id': None}])
        # alias_A009319 must NOT be in DB
        self.assertIsNone(_get(conn, 'alias_A009319', 'dila_id'))
        # real_monk dila_id must be preserved
        self.assertEqual(_get(conn, 'real_monk', 'dila_id'), 'A111111')

    # I. Idempotency: run ETL-simulate twice → same result
    def test_I_idempotency(self):
        conn = _make_db([{'id': 'monk_i', 'dila_id': 'A123', 'status': 'verified'}])
        _simulate_etl(conn, [{'id': 'monk_i', 'dila_id': None}])
        first_dila = _get(conn, 'monk_i', 'dila_id')
        first_status = _get(conn, 'monk_i', 'status')
        _simulate_etl(conn, [{'id': 'monk_i', 'dila_id': None}])
        self.assertEqual(_get(conn, 'monk_i', 'dila_id'), first_dila)
        self.assertEqual(_get(conn, 'monk_i', 'status'), first_status)

    # J. Transaction rollback: simulate failure mid-restore
    def test_J_transaction_rollback_simulation(self):
        conn = _make_db([{'id': 'monk_j', 'dila_id': 'A123'}])
        curated_dila, curated_status = _snapshot(conn)
        conn.execute("DELETE FROM vn_person_authority")
        conn.execute("INSERT INTO vn_person_authority (id, dila_id) VALUES ('monk_j', '')")
        conn.commit()
        # Simulate failure: try to restore inside a savepoint
        try:
            conn.execute("SAVEPOINT sp_test")
            conn.execute("UPDATE vn_person_authority SET dila_id=? WHERE id=?", ('A123', 'monk_j'))
            # Simulate error
            raise RuntimeError("simulated failure")
        except RuntimeError:
            conn.execute("ROLLBACK TO SAVEPOINT sp_test")
            conn.execute("RELEASE SAVEPOINT sp_test")
        # After rollback, dila_id is still '' (not yet restored)
        self.assertEqual(_get(conn, 'monk_j', 'dila_id'), '')

    # K. No fuzzy/name-only matching: row identified strictly by PK
    def test_K_no_fuzzy_matching(self):
        # Two monks with same name but different PKs — must not interfere
        conn = _make_db([
            {'id': 'monk_k1', 'name': 'Đại Hải', 'dila_id': 'A111'},
            {'id': 'monk_k2', 'name': 'Đại Hải', 'dila_id': 'A222'},
        ])
        _simulate_etl(conn, [
            {'id': 'monk_k1', 'dila_id': None},
            {'id': 'monk_k2', 'dila_id': None},
        ])
        self.assertEqual(_get(conn, 'monk_k1', 'dila_id'), 'A111')
        self.assertEqual(_get(conn, 'monk_k2', 'dila_id'), 'A222')

    # L. Row-count sanity: no duplicate explosion
    def test_L_row_count_sanity(self):
        conn = _make_db([
            {'id': 'monk_l1', 'dila_id': 'A111'},
            {'id': 'monk_l2', 'dila_id': 'A222'},
        ])
        _simulate_etl(conn, [
            {'id': 'monk_l1', 'dila_id': None},
            {'id': 'monk_l2', 'dila_id': None},
        ])
        count = conn.execute("SELECT COUNT(*) FROM vn_person_authority").fetchone()[0]
        self.assertEqual(count, 2)

    # M. Existing non-curated rows handled per ETL contract (new rows pass through)
    def test_M_new_rows_passthrough(self):
        conn = _make_db([{'id': 'old_monk', 'dila_id': 'A111'}])
        _simulate_etl(conn, [
            {'id': 'old_monk', 'dila_id': None},
            {'id': 'new_monk', 'dila_id': 'A999'},  # new row with incoming dila_id
        ])
        self.assertEqual(_get(conn, 'old_monk', 'dila_id'), 'A111')  # preserved
        self.assertEqual(_get(conn, 'new_monk', 'dila_id'), 'A999')  # pass-through


class TestStatusPreservation(unittest.TestCase):

    def test_status_preserved_when_etl_resets_to_pending(self):
        conn = _make_db([{'id': 'monk_s', 'dila_id': 'A123', 'status': 'verified'}])
        _, _, rs = _simulate_etl(conn, [{'id': 'monk_s', 'dila_id': 'A123', 'status': 'pending'}])
        self.assertEqual(_get(conn, 'monk_s', 'status'), 'verified')
        self.assertEqual(rs, 1)

    def test_auto_ttl_status_preserved(self):
        conn = _make_db([{'id': 'monk_at', 'dila_id': 'A123', 'status': 'auto_ttl'}])
        _simulate_etl(conn, [{'id': 'monk_at', 'dila_id': 'A123', 'status': 'pending'}])
        self.assertEqual(_get(conn, 'monk_at', 'status'), 'auto_ttl')

    def test_pending_status_not_preserved_over_incoming_pending(self):
        conn = _make_db([{'id': 'monk_p', 'dila_id': 'A123', 'status': 'pending'}])
        _, _, rs = _simulate_etl(conn, [{'id': 'monk_p', 'dila_id': 'A123', 'status': 'pending'}])
        self.assertEqual(_get(conn, 'monk_p', 'status'), 'pending')
        self.assertEqual(rs, 0)  # Nothing to restore for 'pending'


# ---------------------------------------------------------------------------
# Integration test: run actual ETL against a DB copy
# Requires TTL files present (data/ttl/old/*.ttl) and rdflib installed.
# ---------------------------------------------------------------------------

@unittest.skipUnless(
    os.path.isfile(_ETL) and os.path.isfile(_PROD_DB),
    "ETL script or production DB not found"
)
class TestETLIntegration(unittest.TestCase):
    # [T222] SHA captured once at class setup — detects mutations DURING this run only.
    # Hardcoded expected SHA was unstable: Flask app writes to DB between sessions.
    # This design is strictly more correct than a stale hardcoded value.
    sha_before: str = ''

    @classmethod
    def setUpClass(cls):
        import hashlib
        h = hashlib.sha256()
        with open(_PROD_DB, 'rb') as f:
            for chunk in iter(lambda: f.read(8 << 20), b''):
                h.update(chunk)
        cls.sha_before = h.hexdigest()

    def _run_etl(self, db_path):
        """Run ETL against a given DB path. Returns (returncode, stdout, stderr)."""
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', _ETL,
             f'--db={db_path}', '--skip-preflight'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=_ROOT, env=env
        )
        return result.returncode, result.stdout, result.stderr

    def test_G_t215_33_rows_survive_etl_rerun(self):
        """G. 33 T215-restored dila_ids must survive a full ETL rerun on DB copy."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            tmp_db = f.name
        try:
            shutil.copy2(_PROD_DB, tmp_db)
            # Verify baseline: 33/33 present in copy
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row
            before = {}
            for rid in T215_IDS:
                r = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id=?", (rid,)).fetchone()
                before[rid] = r['dila_id'] if r else None
            conn.close()
            missing_before = [rid for rid, v in before.items() if not v]
            if missing_before:
                self.fail(f"DATA REGRESSION: {len(missing_before)} T215 rows already missing "
                          f"before ETL: {missing_before[:5]}")
            # Run ETL
            rc, stdout, stderr = self._run_etl(tmp_db)
            self.assertEqual(rc, 0, f"ETL failed (rc={rc}).\nstdout:\n{stdout}\nstderr:\n{stderr}")
            # Check 33/33 still present
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row
            after = {}
            for rid in T215_IDS:
                r = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id=?", (rid,)).fetchone()
                after[rid] = r['dila_id'] if r else None
            conn.close()
            changed = [(rid, before[rid], after[rid]) for rid in T215_IDS
                       if after[rid] != before[rid]]
            self.assertEqual(len(changed), 0,
                             f"T215 rows changed after ETL rerun:\n"
                             + "\n".join(f"  {rid}: {b!r}→{a!r}" for rid, b, a in changed))
        finally:
            os.unlink(tmp_db)

    def test_H_t212_deleted_aliases_not_resurrected(self):
        """H. 4 T212 deleted aliases must NOT appear after ETL rerun."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            tmp_db = f.name
        try:
            shutil.copy2(_PROD_DB, tmp_db)
            rc, stdout, stderr = self._run_etl(tmp_db)
            self.assertEqual(rc, 0, f"ETL failed (rc={rc}).\nstdout:\n{stdout}")
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row
            for alias_id in T212_DELETED:
                r = conn.execute(
                    "SELECT id FROM vn_person_authority WHERE id=?", (alias_id,)
                ).fetchone()
                self.assertIsNone(r, f"T212 alias {alias_id!r} was RESURRECTED by ETL!")
            conn.close()
        finally:
            os.unlink(tmp_db)

    def test_I_idempotency_integration(self):
        """I. Running ETL twice produces same dila_id state."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            tmp_db = f.name
        try:
            shutil.copy2(_PROD_DB, tmp_db)
            # First run
            rc1, _, _ = self._run_etl(tmp_db)
            self.assertEqual(rc1, 0)
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row
            after_1 = {r['id']: r['dila_id']
                       for r in conn.execute("SELECT id, dila_id FROM vn_person_authority")}
            conn.close()
            # Second run
            rc2, _, _ = self._run_etl(tmp_db)
            self.assertEqual(rc2, 0)
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row
            after_2 = {r['id']: r['dila_id']
                       for r in conn.execute("SELECT id, dila_id FROM vn_person_authority")}
            conn.close()
            # Compare — same ids, same dila_ids
            diff = {k for k in set(after_1) | set(after_2) if after_1.get(k) != after_2.get(k)}
            self.assertEqual(len(diff), 0,
                             f"ETL not idempotent: {len(diff)} rows differ after 2nd run: "
                             + str(sorted(diff)[:10]))
        finally:
            os.unlink(tmp_db)

    def test_production_db_unchanged(self):
        """Production DB must remain byte-for-byte identical within this test run.

        Compares SHA captured at setUpClass (before any test) against SHA recomputed
        now (after all ETL copy-tests ran). Detects accidental production writes by
        T217 tests themselves. Does NOT detect app-activity writes between sessions
        (Flask legitimately writes to DB — that is not our concern here).
        """
        import hashlib
        h = hashlib.sha256()
        with open(_PROD_DB, 'rb') as f:
            for chunk in iter(lambda: f.read(8 << 20), b''):
                h.update(chunk)
        sha_after = h.hexdigest()
        self.assertNotEqual(self.sha_before, '', "SHA before should be set by setUpClass")
        self.assertEqual(sha_after, self.sha_before,
                         f"CRITICAL: production DB was mutated DURING this test run!\n"
                         f"SHA before tests: {self.sha_before}\n"
                         f"SHA after tests : {sha_after}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
