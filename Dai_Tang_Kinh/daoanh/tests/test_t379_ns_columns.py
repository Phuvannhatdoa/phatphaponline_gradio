#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T379 (rebuild-gen-tables follow-up) — test cột teacher_ns/disciple_ns mới
thêm vào lineage_edge_consensus (Phương án A, additive, xem
docs/design/T379-lineage-edge-consensus-ns-design.md và
scripts/t379_add_ns_columns.py).

Migration này KHÔNG insert cạnh mới nào (Bước 7 ràng buộc cứng) — mọi dòng
hiện có phải nhận ns='DILA' qua ALTER TABLE ... DEFAULT.

Usage: python -m pytest tests/test_t379_ns_columns.py -v
"""
import os
import sqlite3
import pytest

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
TABLE = 'lineage_edge_consensus'


@pytest.fixture(scope='module')
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_ns_columns_exist(db):
    cols = {r[1] for r in db.execute(f"PRAGMA table_info({TABLE})").fetchall()}
    assert 'teacher_ns' in cols, "Thiếu cột teacher_ns"
    assert 'disciple_ns' in cols, "Thiếu cột disciple_ns"


def test_ns_default_is_dila_for_all_existing_rows(db):
    """Migration T379 additive KHÔNG insert cạnh mới -> mọi dòng phải là DILA/DILA."""
    total = db.execute(f"SELECT COUNT(*) n FROM {TABLE}").fetchone()['n']
    both_dila = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE teacher_ns='DILA' AND disciple_ns='DILA'"
    ).fetchone()['n']
    non_dila = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE teacher_ns!='DILA' OR disciple_ns!='DILA'"
    ).fetchone()['n']
    assert non_dila == 0, f"{non_dila} dòng có ns != 'DILA' — không mong đợi ở bước này"
    assert both_dila == total, f"both_dila={both_dila} != total={total}"


def test_ns_columns_not_null(db):
    n = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE teacher_ns IS NULL OR disciple_ns IS NULL"
    ).fetchone()['n']
    assert n == 0, f"{n} dòng có teacher_ns/disciple_ns NULL"


def test_unique_index_ns_key_exists(db):
    """idx_lec_ns_key — tên + thứ tự cột theo lệnh chốt Admin (xem docstring
    scripts/t379_add_ns_columns.py), KHÁC thứ tự đề xuất trong design doc §1/§2."""
    row = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND name=?",
        (TABLE, 'idx_lec_ns_key')
    ).fetchone()
    assert row is not None, "Thiếu index idx_lec_ns_key"
    sql = (row['sql'] or '').replace(' ', '').replace('\n', '')
    assert 'teacher_ns,disciple_ns,teacher_id,disciple_id,relation_type' in sql, (
        f"Thứ tự cột index sai: {row['sql']}"
    )
    assert 'UNIQUE' in (row['sql'] or '').upper()


def test_secondary_ns_indexes_exist(db):
    names = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (TABLE,)
    ).fetchall()}
    assert 'idx_lec_teacher_ns' in names
    assert 'idx_lec_disciple_ns' in names


def test_old_unique_constraint_still_present(db):
    """Constraint cũ (teacher_id, disciple_id, relation_type) PHẢI vẫn còn —
    bảng KHÔNG rebuild (Phương án A, không rebuild bảng)."""
    names = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (TABLE,)
    ).fetchall()}
    autoindexes = [n for n in names if n.startswith('sqlite_autoindex_')]
    assert autoindexes, "Không tìm thấy UNIQUE constraint gốc (sqlite_autoindex)"


def test_row_count_unchanged(db):
    """Additive thuần — tổng số dòng phải đúng 23411 (số đo Bước 2, không đổi)."""
    n = db.execute(f"SELECT COUNT(*) n FROM {TABLE}").fetchone()['n']
    assert n == 23411, f"Row count thay đổi: {n} (kỳ vọng 23411, migration là additive)"


def test_integrity_check_ok(db):
    qc = db.execute('PRAGMA integrity_check').fetchone()[0]
    assert qc == 'ok', f"integrity_check: {qc}"
