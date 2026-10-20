"""
T368 - Phase 4a: Tao 4 bang moi cho Person Activity / Passage Mention / Merge Log / Lineage Unified.

Idempotent: dung CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS,
chay nhieu lan khong gay loi, khong dung lai (no-op) voi report ro rang.

Usage:
    python -X utf8 scripts/t368_create_tables.py --db data/lineage.db [--dry-run]
"""
import argparse
import sqlite3
import os
import sys

TABLES = {
    "person_activity": """
        CREATE TABLE IF NOT EXISTS person_activity (
            id TEXT PRIMARY KEY,
            person_id TEXT NOT NULL,
            place_id TEXT,
            activity_type TEXT NOT NULL CHECK (activity_type IN ('birth','death','ordained','active_at','work')),
            year_start INTEGER,
            year_end INTEGER,
            source TEXT,
            confidence REAL DEFAULT 0.8,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES vn_person_authority(id),
            FOREIGN KEY (place_id) REFERENCES places(id)
        )
    """,
    "passage_entity_mention": """
        CREATE TABLE IF NOT EXISTS passage_entity_mention (
            id TEXT PRIMARY KEY,
            person_id TEXT NOT NULL,
            cbeta_passage_id TEXT NOT NULL,
            mention_type TEXT,
            context TEXT,
            source TEXT,
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES vn_person_authority(id)
        )
    """,
    "entity_merge_log": """
        CREATE TABLE IF NOT EXISTS entity_merge_log (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_ids TEXT NOT NULL,
            decision TEXT,
            reason TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "dharma_lineage_unified": """
        CREATE TABLE IF NOT EXISTS dharma_lineage_unified (
            id TEXT PRIMARY KEY,
            teacher_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            source TEXT,
            confidence REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES vn_person_authority(id),
            FOREIGN KEY (student_id) REFERENCES vn_person_authority(id),
            UNIQUE (teacher_id, student_id, source)
        )
    """,
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_person_activity_person_id ON person_activity(person_id)",
    "CREATE INDEX IF NOT EXISTS idx_person_activity_activity_type ON person_activity(activity_type)",
    "CREATE INDEX IF NOT EXISTS idx_passage_entity_mention_person_id ON passage_entity_mention(person_id)",
    "CREATE INDEX IF NOT EXISTS idx_passage_entity_mention_cbeta_passage_id ON passage_entity_mention(cbeta_passage_id)",
    "CREATE INDEX IF NOT EXISTS idx_entity_merge_log_entity_type ON entity_merge_log(entity_type)",
]


def table_exists(cur, name):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def create_tables(db_path, dry_run=False):
    if not os.path.exists(db_path):
        print(f"LOI: khong tim thay DB tai {db_path}")
        return False

    # Kiem tra FK target ton tai truoc khi tao (person_activity, dharma_lineage_unified can vn_person_authority; person_activity can places)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    missing_fk_targets = [t for t in ("vn_person_authority", "places") if not table_exists(cur, t)]
    if missing_fk_targets:
        print(f"LOI: bang FK target bi thieu: {missing_fk_targets}. Dung lai, khong tao bang moi.")
        conn.close()
        return False

    before = {name: table_exists(cur, name) for name in TABLES}
    print("Trang thai truoc khi migrate:")
    for name, exists in before.items():
        print(f"  {name}: {'DA TON TAI (no-op)' if exists else 'chua co, se tao moi'}")

    if dry_run:
        print("\n[DRY-RUN] Khong ghi DB. Cac lenh se chay:")
        for name, ddl in TABLES.items():
            print(f"-- {name} --\n{ddl.strip()}")
        for idx in INDEXES:
            print(idx)
        conn.close()
        return True

    try:
        for name, ddl in TABLES.items():
            cur.execute(ddl)
        for idx in INDEXES:
            cur.execute(idx)
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"LOI khi tao bang: {e}")
        return False

    after = {name: table_exists(cur, name) for name in TABLES}
    conn.close()

    print("\nTrang thai sau khi migrate:")
    ok = True
    for name, exists in after.items():
        print(f"  {name}: {'OK' if exists else 'THIEU'}")
        ok = ok and exists
    if ok:
        print("\n[OK] 4 bang da san sang (tao moi hoac da ton tai tu truoc).")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/lineage.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    success = create_tables(args.db, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
