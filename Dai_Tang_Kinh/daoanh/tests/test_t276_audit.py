# -*- coding: utf-8 -*-
"""T276: test thống kê, cờ provisional, migrate và xuất CSV của side-car (DB tạm, không đụng DB thật)."""
import csv
import importlib
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))


def _make_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE person_groq_audit (
      id TEXT PRIMARY KEY, dict_vi TEXT, groq_trans_vi TEXT, final_vi TEXT,
      needs_review INTEGER DEFAULT 0, review_status TEXT DEFAULT 'pending',
      diff_type TEXT, batch_id TEXT, checked_at TIMESTAMP
    );
    CREATE TABLE place_groq_audit (
      id INTEGER PRIMARY KEY, dict_vi TEXT, groq_trans_vi TEXT,
      needs_review INTEGER DEFAULT 0, review_status TEXT DEFAULT 'pending',
      diff_type TEXT, batch_id TEXT, checked_at TIMESTAMP
    );
    INSERT INTO person_groq_audit (id, review_status, needs_review, batch_id, checked_at) VALUES
      ('A1', 'auto_verified', 0, 'B1', '2026-10-10 10:00:00'),
      ('A2', 'auto_verified_sanskrit', 0, 'B1', '2026-10-10 10:00:01'),
      ('A3', 'conflict', 1, 'B1', '2026-10-10 10:00:02'),
      ('A4', 'api_error', 1, 'B2', '2026-10-10 11:00:00'),
      ('A5', 'verified', 0, 'B2', '2026-10-10 11:00:01');
    INSERT INTO place_groq_audit (id, review_status, needs_review, batch_id, checked_at) VALUES
      (1, 'auto_taxonomy_aligned', 0, 'P1', '2026-10-10 09:00:00');
    """)
    con.commit()
    con.close()


@pytest.fixture
def env(monkeypatch):
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, 'test.db')
    _make_db(db)
    monkeypatch.setenv('T276_DB', db)
    import t276_audit_stats as m
    importlib.reload(m)
    m.DB_PATH = db
    m.BACK_DIR = Path(tmp) / 'backups'
    m.EVID_DIR = Path(tmp) / 'evidence'
    return m, db


def test_provisional_counts_auto_only(env):
    m, db = env
    res = m.collect()
    p = res['tables']['person_groq_audit']
    assert p['total'] == 5
    # 2 dòng auto_* chưa được Admin kiểm (cột admin_checked chưa có → coi là 0)
    assert p['provisional'] == 2
    assert p['needs_review'] == 2
    assert p['api_error'] == 1
    assert p['last_batch_id'] == 'B2'
    assert res['tables']['place_groq_audit']['provisional'] == 1


def test_admin_checked_removes_provisional(env):
    m, db = env
    assert m.migrate_apply() == 0
    con = sqlite3.connect(db)
    con.execute("UPDATE person_groq_audit SET admin_checked = 1 WHERE id = 'A1'")
    con.commit(); con.close()
    p = m.collect()['tables']['person_groq_audit']
    assert p['provisional'] == 1
    assert p['admin_checked_col'] is True


def test_migrate_is_idempotent_and_backs_up(env):
    m, db = env
    assert m.migrate_apply() == 0
    bak = list(m.BACK_DIR.glob('lineage.T276-audit-*.db'))
    assert len(bak) == 1, bak
    # chạy lần hai: không thêm cột lần nữa
    assert all(sql.startswith('BỎ QUA') for _, sql in m.migrate_plan())
    # lần hai không có gì để thêm: không tạo backup mới, không ALTER
    assert m.migrate_apply() == 0
    assert len(list(m.BACK_DIR.glob('lineage.T276-audit-*.db'))) == 1


def test_revert_drops_column(env):
    m, db = env
    m.migrate_apply()
    assert m.migrate_revert() == 0
    cols = [r[1] for r in sqlite3.connect(db).execute('PRAGMA table_info(person_groq_audit)')]
    assert 'admin_checked' not in cols


def test_export_csv_has_provisional_column(env):
    m, db = env
    out = Path(m.EVID_DIR) / 'person.csv'
    n = m.export_csv('person_groq_audit', out)
    assert n == 5
    rows = list(csv.DictReader(open(out, encoding='utf-8')))
    prov = {r['id']: r['provisional'] for r in rows}
    assert prov['A1'] == '1' and prov['A2'] == '1'
    assert prov['A3'] == '0' and prov['A5'] == '0'


def test_missing_db_is_reported_not_crash(monkeypatch):
    monkeypatch.setenv('T276_DB', os.path.join(tempfile.mkdtemp(), 'nope.db'))
    import t276_audit_stats as m
    importlib.reload(m)
    m.DB_PATH = os.path.join(tempfile.mkdtemp(), 'nope.db')
    res = m.collect()
    assert res['ok'] is False
