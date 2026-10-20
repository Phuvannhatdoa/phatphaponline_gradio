"""
Test T368 - schema migration cho person_activity, passage_entity_mention,
entity_merge_log, dharma_lineage_unified.

Dung DB tam (fixture), KHONG dong vao data/lineage.db thuc te.
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import t368_create_tables as mig  # noqa: E402


@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_lineage.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Tao cac bang FK target toi thieu de migration khong bi tu choi
    cur.execute("CREATE TABLE vn_person_authority (id TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE places (id TEXT PRIMARY KEY)")
    cur.execute("INSERT INTO vn_person_authority (id) VALUES ('A000035')")
    cur.execute("INSERT INTO places (id) VALUES ('PL000000023255')")
    conn.commit()
    conn.close()
    return db_path


def test_create_tables_success(temp_db):
    assert mig.create_tables(temp_db) is True
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    for t in ("person_activity", "passage_entity_mention", "entity_merge_log", "dharma_lineage_unified"):
        assert mig.table_exists(cur, t), f"bang {t} phai ton tai sau migration"
    conn.close()


def test_create_tables_idempotent(temp_db):
    assert mig.create_tables(temp_db) is True
    # Chay lan 2 khong duoc loi, khong duoc tao trung
    assert mig.create_tables(temp_db) is True


def test_create_tables_missing_fk_target(tmp_path):
    db_path = str(tmp_path / "missing_fk.db")
    conn = sqlite3.connect(db_path)
    conn.close()
    # Khong co vn_person_authority / places -> phai that bai, khong tao bang
    assert mig.create_tables(db_path) is False
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    assert not mig.table_exists(cur, "person_activity")
    conn.close()


def test_activity_type_check_constraint(temp_db):
    mig.create_tables(temp_db)
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute(
            "INSERT INTO person_activity (id, person_id, activity_type) VALUES (?, ?, ?)",
            ("PA1", "A000035", "invalid_type"),
        )
    conn.rollback()
    # Gia tri hop le phai insert duoc
    cur.execute(
        "INSERT INTO person_activity (id, person_id, place_id, activity_type) VALUES (?, ?, ?, ?)",
        ("PA2", "A000035", "PL000000023255", "work"),
    )
    conn.commit()
    cur.execute("SELECT activity_type FROM person_activity WHERE id='PA2'")
    assert cur.fetchone()[0] == "work"
    conn.close()


def test_dharma_lineage_unique_constraint(temp_db):
    mig.create_tables(temp_db)
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO vn_person_authority (id) VALUES ('A000036')"
    )
    cur.execute(
        "INSERT INTO dharma_lineage_unified (id, teacher_id, student_id, source) VALUES (?, ?, ?, ?)",
        ("DLU1", "A000035", "A000036", "DILA"),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute(
            "INSERT INTO dharma_lineage_unified (id, teacher_id, student_id, source) VALUES (?, ?, ?, ?)",
            ("DLU2", "A000035", "A000036", "DILA"),
        )
    conn.rollback()
    conn.close()


def test_rollback_drops_only_t368_tables(temp_db):
    mig.create_tables(temp_db)
    conn = sqlite3.connect(temp_db)
    rollback_sql_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "t368_rollback.sql")
    with open(rollback_sql_path, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    cur = conn.cursor()
    for t in ("person_activity", "passage_entity_mention", "entity_merge_log", "dharma_lineage_unified"):
        assert not mig.table_exists(cur, t), f"{t} phai bi drop sau rollback"
    # Bang ngoai scope (vn_person_authority, places) khong bi dong
    for t in ("vn_person_authority", "places"):
        assert mig.table_exists(cur, t), f"{t} khong duoc dong boi rollback T368"
    conn.close()
