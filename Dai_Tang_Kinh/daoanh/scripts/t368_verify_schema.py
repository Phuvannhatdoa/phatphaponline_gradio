"""
T368 - Verify schema sau migration. Dung PRAGMA, khong doan.
"""
import argparse
import sqlite3
import sys


def verify_schema(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    checks = {}

    cur.execute("PRAGMA table_info(person_activity)")
    cols = [r[1] for r in cur.fetchall()]
    checks["person_activity_columns"] = all(
        c in cols for c in ["id", "person_id", "place_id", "activity_type", "year_start", "created_at"]
    )

    cur.execute("PRAGMA table_info(passage_entity_mention)")
    cols = [r[1] for r in cur.fetchall()]
    checks["passage_entity_mention_columns"] = all(
        c in cols for c in ["id", "person_id", "cbeta_passage_id", "mention_type", "created_at"]
    )

    cur.execute("PRAGMA table_info(entity_merge_log)")
    cols = [r[1] for r in cur.fetchall()]
    checks["entity_merge_log_columns"] = all(
        c in cols for c in ["id", "entity_type", "entity_ids", "decision", "created_at"]
    )

    cur.execute("PRAGMA table_info(dharma_lineage_unified)")
    cols = [r[1] for r in cur.fetchall()]
    checks["dharma_lineage_unified_columns"] = all(
        c in cols for c in ["id", "teacher_id", "student_id", "source", "confidence"]
    )

    cur.execute("PRAGMA index_list(person_activity)")
    checks["person_activity_indexes"] = len(cur.fetchall()) >= 2

    cur.execute("PRAGMA index_list(passage_entity_mention)")
    checks["passage_entity_mention_indexes"] = len(cur.fetchall()) >= 2

    # Check CHECK constraint tren activity_type bang cach thu insert gia tri khong hop le
    try:
        cur.execute(
            "INSERT INTO person_activity (id, person_id, place_id, activity_type, year_start, year_end, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("PA_TEST_9999", "A_TEST_9999", None, "invalid_type", None, None, "test"),
        )
        conn.rollback()
        checks["activity_type_check_constraint"] = False
    except sqlite3.IntegrityError:
        conn.rollback()
        checks["activity_type_check_constraint"] = True

    # Row count moi (phai = 0, chua import du lieu)
    for t in ("person_activity", "passage_entity_mention", "entity_merge_log", "dharma_lineage_unified"):
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        checks[f"{t}_zero_rows"] = cur.fetchone()[0] == 0

    conn.close()

    print("Ket qua xac minh schema T368:")
    for k, v in checks.items():
        print(f"  {'OK' if v else 'FAIL'} - {k}")
    return all(checks.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/lineage.db")
    args = parser.parse_args()
    ok = verify_schema(args.db)
    print("\nPASSED" if ok else "\nFAILED")
    sys.exit(0 if ok else 1)
