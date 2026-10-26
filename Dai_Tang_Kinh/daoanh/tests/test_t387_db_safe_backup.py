"""T387 — SQLite online backup / safe restore tests.

Chỉ dùng DB tạm trong tempdir. KHÔNG đọc/ghi `data/lineage.db`, KHÔNG SSH.
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import db_safe_backup as h  # noqa: E402


def make_wal_db(path, rows=200):
    """Tạo DB WAL, ghi dữ liệu nhưng KHÔNG checkpoint (dữ liệu còn trong -wal)."""
    con = sqlite3.connect(path)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)')
    con.executemany('INSERT INTO t (v) VALUES (?)', [('x%d' % i,) for i in range(rows)])
    con.commit()
    # Giữ connection mở trong lúc backup để WAL chưa checkpoint
    return con


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='t387-')
        self.dir = self.tmp.name
        self.db = os.path.join(self.dir, 'live.db')

    def tearDown(self):
        self.tmp.cleanup()

    def test_backup_of_wal_db_is_complete(self):
        con = make_wal_db(self.db)
        try:
            self.assertTrue(os.path.exists(self.db + '-wal'))
            out = os.path.join(self.dir, 'snap.db')
            res = h.backup_to(self.db, out)
            self.assertEqual(res, out)
            self.assertTrue(os.path.exists(out))

            bcon = sqlite3.connect(out)
            try:
                self.assertEqual(bcon.execute('PRAGMA quick_check').fetchone()[0], 'ok')
                # Toàn bộ 200 dòng phải có trong bản sao dù chưa checkpoint
                self.assertEqual(bcon.execute('SELECT COUNT(*) FROM t').fetchone()[0], 200)
            finally:
                bcon.close()
        finally:
            con.close()

    def test_verify_backup_ok_and_missing(self):
        con = make_wal_db(self.db, rows=5)
        con.close()
        out = os.path.join(self.dir, 'snap.db')
        self.assertIsNotNone(h.backup_to(self.db, out))

        ok, detail = h.verify_backup(out)
        self.assertTrue(ok, detail)
        self.assertEqual(detail, 'ok')

        ok, _ = h.verify_backup(os.path.join(self.dir, 'nope.db'))
        self.assertFalse(ok)

    def test_verify_backup_rejects_non_sqlite(self):
        bogus = os.path.join(self.dir, 'bogus.db')
        with open(bogus, 'wb') as f:
            f.write(b'not a database at all')
        ok, detail = h.verify_backup(bogus)
        self.assertFalse(ok)
        self.assertIn('SQLite', detail)

    def test_compress_writes_manifest(self):
        con = make_wal_db(self.db, rows=10)
        con.close()
        out = os.path.join(self.dir, 'snap.db')
        res = h.backup_to(self.db, out, compress=True)
        self.assertEqual(res, out)
        self.assertTrue(os.path.exists(out))
        manifest = out + '.manifest.json'
        self.assertTrue(os.path.exists(manifest))
        import json
        with open(manifest, encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('sha256_16', data)
        self.assertGreater(data['size_raw_bytes'], 0)

    def test_backup_missing_source_returns_none(self):
        self.assertIsNone(h.backup_to(os.path.join(self.dir, 'absent.db'),
                                      os.path.join(self.dir, 'out.db')))


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='t387-restore-')
        self.dir = self.tmp.name
        self.db = os.path.join(self.dir, 'live.db')
        con = make_wal_db(self.db, rows=20)
        con.close()
        self.backup = os.path.join(self.dir, 'snap.db')
        self.assertIsNotNone(h.backup_to(self.db, self.backup))

        # Làm DB "bẩn" sau khi chụp backup
        con = sqlite3.connect(self.db)
        con.execute("DELETE FROM t")
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_restore_refused_without_flag(self):
        self.assertFalse(h.restore_from(self.backup, self.db))
        con = sqlite3.connect(self.db)
        try:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM t').fetchone()[0], 0)
        finally:
            con.close()

    def test_restore_with_flag_restores_and_drops_wal(self):
        # Tạo WAL/SHM để kiểm chúng bị xoá sau restore
        con = sqlite3.connect(self.db)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute("INSERT INTO t (v) VALUES ('dirty')")
        con.commit()
        con.close()

        self.assertTrue(h.restore_from(self.backup, self.db,
                                       i_know_server_is_stopped=True))
        con = sqlite3.connect(self.db)
        try:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM t').fetchone()[0], 20)
            self.assertEqual(con.execute('PRAGMA quick_check').fetchone()[0], 'ok')
        finally:
            con.close()

    def test_restore_rejects_corrupt_backup(self):
        bad = os.path.join(self.dir, 'bad.db')
        with open(bad, 'wb') as f:
            f.write(b'garbage')
        self.assertFalse(h.restore_from(bad, self.db,
                                        i_know_server_is_stopped=True))


class PruneTests(unittest.TestCase):
    def test_prune_removes_old_named_backups(self):
        with tempfile.TemporaryDirectory(prefix='t387-prune-') as d:
            old = os.path.join(d, 'lineage_20200101.db')
            new = os.path.join(d, 'lineage_29990101.db')
            other = os.path.join(d, 'keepme.txt')
            for p in (old, new, other):
                with open(p, 'w') as f:
                    f.write('x')
            removed = h.prune_old_backups(d, keep_days=30)
            self.assertEqual(removed, 1)
            self.assertFalse(os.path.exists(old))
            self.assertTrue(os.path.exists(new))
            self.assertTrue(os.path.exists(other))


class GateTests(unittest.TestCase):
    def test_restore_gate_flag_documented(self):
        src = Path(h.__file__).read_text(encoding='utf-8')
        self.assertIn('--i-know-server-is-stopped', src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
