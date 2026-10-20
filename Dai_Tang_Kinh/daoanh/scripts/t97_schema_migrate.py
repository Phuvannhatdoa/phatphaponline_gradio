"""
T97 Schema Migration — Time Mention + Event Evidence tables
Usage:
    python scripts/t97_schema_migrate.py --apply    # create tables
    python scripts/t97_schema_migrate.py --revert   # drop tables (safe — only T97 tables)
    python scripts/t97_schema_migrate.py            # dry-run (print DDL)
"""
import sqlite3, sys, os, shutil
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

TABLES = {
    'time_mentions': """
        CREATE TABLE IF NOT EXISTS time_mentions (
            mention_id   TEXT PRIMARY KEY,
            source_table TEXT NOT NULL,
            source_record_id TEXT NOT NULL,
            raw_time_zh  TEXT NOT NULL,
            normalized_start INTEGER,
            normalized_end   INTEGER,
            precision    TEXT NOT NULL
                CHECK(precision IN ('exact_day','month','year','year_range',
                                    'reign_era','dynasty_period','relative','unknown')),
            time_authority_id TEXT,
            extraction_method TEXT NOT NULL
                CHECK(extraction_method IN ('regex_rule','authority_mapping',
                                            'editorial','imported')),
            confidence   REAL DEFAULT 0.8,
            created_at   TEXT DEFAULT (datetime('now'))
        )
    """,
    'events': """
        CREATE TABLE IF NOT EXISTS events (
            event_id     TEXT PRIMARY KEY,
            event_type   TEXT,
            title_zh     TEXT,
            title_vi     TEXT,
            start_year   INTEGER,
            end_year     INTEGER,
            precision    TEXT,
            extraction_method TEXT,
            review_status TEXT NOT NULL DEFAULT 'candidate'
                CHECK(review_status IN ('candidate','reviewed','disputed','rejected')),
            confidence   REAL DEFAULT 0.5,
            notes        TEXT,
            created_at   TEXT DEFAULT (datetime('now')),
            updated_at   TEXT DEFAULT (datetime('now'))
        )
    """,
    'event_entities': """
        CREATE TABLE IF NOT EXISTS event_entities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id    TEXT NOT NULL,
            entity_id   TEXT NOT NULL,
            entity_type TEXT NOT NULL
                CHECK(entity_type IN ('place','person','text','institution')),
            role        TEXT,
            UNIQUE(event_id, entity_id, entity_type)
        )
    """,
    'event_evidence': """
        CREATE TABLE IF NOT EXISTS event_evidence (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id     TEXT NOT NULL,
            time_mention_id TEXT,
            source_record TEXT NOT NULL,
            source_table  TEXT,
            exact_span    TEXT,
            source_ref    TEXT,
            evidence_type TEXT,
            reviewer_note TEXT,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """,
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_time_mentions_src ON time_mentions(source_table, source_record_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_status ON events(review_status)",
    "CREATE INDEX IF NOT EXISTS idx_event_entities_event ON event_entities(event_id)",
    "CREATE INDEX IF NOT EXISTS idx_event_evidence_event ON event_evidence(event_id)",
]

REVERT_TABLES = ['event_evidence', 'event_entities', 'events', 'time_mentions']


def backup_db():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = DB.replace('.db', f'.backup_t97_{ts}')
    shutil.copy2(DB, dest)
    print(f'[backup] {dest}')
    return dest


def apply():
    backup_db()
    conn = sqlite3.connect(DB)
    for name, ddl in TABLES.items():
        conn.execute(ddl)
        print(f'[OK] CREATE TABLE IF NOT EXISTS {name}')
    for idx in INDEXES:
        conn.execute(idx)
    conn.commit()
    conn.close()
    print('[OK] T97 schema applied.')


def revert():
    conn = sqlite3.connect(DB)
    for t in REVERT_TABLES:
        conn.execute(f'DROP TABLE IF EXISTS {t}')
        print(f'[drop] {t}')
    conn.commit()
    conn.close()
    print('[OK] T97 tables dropped.')


def dryrun():
    for name, ddl in TABLES.items():
        print(f'-- {name}')
        print(ddl.strip())
        print()
    print('-- Indexes:')
    for idx in INDEXES:
        print(idx)


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    if arg == '--apply':
        apply()
    elif arg == '--revert':
        revert()
    else:
        dryrun()
        print('\nRun with --apply to create tables, --revert to drop them.')
