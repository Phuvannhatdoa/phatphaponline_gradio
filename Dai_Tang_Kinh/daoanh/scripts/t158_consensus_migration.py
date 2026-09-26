"""T158 — Tạo bảng lineage_edge_consensus và backfill từ lineage_edge_assertions.

Modes:
  --stats   Thống kê hiện tại (không thay đổi DB)
  --apply   Tạo bảng + backfill (idempotent: CREATE TABLE IF NOT EXISTS)
  --revert  DROP bảng (chỉ khi bảng do migration này tạo)

Quy tắc:
  - is_default_visible=1 khi: agreeing_source_count >= 2 VÀ opposite_source_count=0
  - source_badge: "N/4: Source1, Source2" format (4 = tổng số nguồn tiềm năng)
  - relation_type: 'dharma_transmission' (canonical cho cả da:isTeacherOf + dila:teacher_of)
  - Zero-DROP trên bảng hiện có. Bảng lineage_edge_consensus là additive.
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
TABLE = 'lineage_edge_consensus'
MARKER = 'T158_MIGRATION'

DDL_TABLE = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id           TEXT NOT NULL,
    disciple_id          TEXT NOT NULL,
    relation_type        TEXT NOT NULL DEFAULT 'dharma_transmission',
    dila_asserted        INTEGER NOT NULL DEFAULT 0,
    marcus_asserted      INTEGER NOT NULL DEFAULT 0,
    ttl_asserted         INTEGER NOT NULL DEFAULT 0,
    lineage_asserted     INTEGER NOT NULL DEFAULT 0,
    agreeing_source_count INTEGER NOT NULL DEFAULT 0,
    opposite_source_count INTEGER NOT NULL DEFAULT 0,
    consensus_status     TEXT NOT NULL DEFAULT 'single_source',
    is_default_visible   INTEGER NOT NULL DEFAULT 0,
    human_override       TEXT DEFAULT NULL,
    source_badge         TEXT DEFAULT NULL,
    migration_marker     TEXT DEFAULT '{MARKER}',
    created_at           TEXT DEFAULT (datetime('now')),
    updated_at           TEXT DEFAULT (datetime('now')),
    UNIQUE(teacher_id, disciple_id, relation_type)
)
"""
DDL_IDX1 = f"CREATE INDEX IF NOT EXISTS idx_lec_teacher ON {TABLE}(teacher_id, is_default_visible)"
DDL_IDX2 = f"CREATE INDEX IF NOT EXISTS idx_lec_disciple ON {TABLE}(disciple_id, is_default_visible)"
DDL_IDX3 = f"CREATE INDEX IF NOT EXISTS idx_lec_visible ON {TABLE}(is_default_visible, relation_type)"

BACKFILL_SQL = f"""
INSERT OR IGNORE INTO {TABLE}
(teacher_id, disciple_id, relation_type,
 dila_asserted, marcus_asserted, ttl_asserted, lineage_asserted,
 agreeing_source_count, opposite_source_count,
 consensus_status, is_default_visible, human_override, source_badge)
WITH fwd AS (
    SELECT
        subject_person_id AS teacher_id,
        object_person_id  AS disciple_id,
        MAX(CASE WHEN source_code='DILA'   THEN 1 ELSE 0 END) dila_v,
        MAX(CASE WHEN source_code='MARCUS' THEN 1 ELSE 0 END) marc_v,
        COUNT(DISTINCT source_code) AS n_sources
    FROM lineage_edge_assertions
    WHERE status='active'
    GROUP BY subject_person_id, object_person_id
),
opp AS (
    SELECT
        object_person_id  AS teacher_id,
        subject_person_id AS disciple_id,
        COUNT(DISTINCT source_code) AS opp_n
    FROM lineage_edge_assertions
    WHERE status='active'
    GROUP BY object_person_id, subject_person_id
)
SELECT
    f.teacher_id,
    f.disciple_id,
    'dharma_transmission',
    f.dila_v, f.marc_v, 0, 0,
    f.n_sources,
    COALESCE(o.opp_n, 0),
    CASE
        WHEN COALESCE(o.opp_n, 0) > 0 THEN 'conflicted'
        WHEN f.n_sources >= 2           THEN 'confirmed_2plus'
        ELSE                                 'single_source'
    END,
    CASE
        WHEN COALESCE(o.opp_n, 0) > 0 THEN 0
        WHEN f.n_sources >= 2           THEN 1
        ELSE                                 0
    END,
    NULL,
    CAST(f.n_sources AS TEXT) || '/4: ' ||
    CASE
        WHEN f.marc_v=1 AND f.dila_v=1 THEN 'Marcus, DILA'
        WHEN f.marc_v=1                 THEN 'Marcus'
        WHEN f.dila_v=1                 THEN 'DILA'
        ELSE                                 '?'
    END
FROM fwd f
LEFT JOIN opp o ON o.teacher_id=f.teacher_id AND o.disciple_id=f.disciple_id
"""


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def do_stats(conn):
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
    ).fetchone()
    print(f'Table {TABLE}: {"EXISTS" if exists else "NOT EXISTS"}')
    if exists:
        counts = conn.execute(f"""
            SELECT consensus_status, COUNT(*) n, SUM(is_default_visible) vis
            FROM {TABLE} GROUP BY consensus_status
        """).fetchall()
        total = 0
        for r in counts:
            print(f'  {r["consensus_status"]}: {r["n"]} rows, {r["vis"] or 0} visible')
            total += r['n']
        print(f'  TOTAL: {total}')
    else:
        print('\nPreview (from lineage_edge_assertions):')
        r2 = conn.execute("""
            SELECT
                SUM(CASE WHEN src_count>=2 THEN 1 ELSE 0 END) confirmed,
                SUM(CASE WHEN src_count=1 THEN 1 ELSE 0 END) single
            FROM (
                SELECT subject_person_id, object_person_id, COUNT(DISTINCT source_code) src_count
                FROM lineage_edge_assertions WHERE status='active'
                GROUP BY subject_person_id, object_person_id
            )
        """).fetchone()
        print(f'  Sẽ tạo: confirmed_2plus={r2["confirmed"]}, single_source={r2["single"]}')

    # Check test case A001060->A021462
    if exists:
        tc = conn.execute(
            f"SELECT * FROM {TABLE} WHERE teacher_id='A001060' AND disciple_id='A021462'"
        ).fetchone()
        if tc:
            print(f'\nTest case A001060->A021462: {tc["consensus_status"]} '
                  f'is_visible={tc["is_default_visible"]} badge={tc["source_badge"]}')
        else:
            print('\nTest case A001060->A021462: NOT IN TABLE')


def do_apply(conn):
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
    ).fetchone()
    if not exists:
        print(f'Creating table {TABLE}...')
        conn.execute(DDL_TABLE)
        conn.execute(DDL_IDX1)
        conn.execute(DDL_IDX2)
        conn.execute(DDL_IDX3)
        conn.commit()
        print('  Table + indexes created.')
    else:
        print(f'Table {TABLE} already exists — backfilling only (INSERT OR IGNORE).')

    print('Backfilling from lineage_edge_assertions...')
    conn.execute(BACKFILL_SQL)
    conn.commit()
    n = conn.execute(f"SELECT COUNT(*) n FROM {TABLE}").fetchone()['n']
    print(f'  Done. {TABLE} now has {n} rows.')
    do_stats(conn)


def do_revert(conn):
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
    ).fetchone()
    if not exists:
        print(f'Table {TABLE} does not exist — nothing to revert.')
        return
    marker_col = conn.execute(
        "SELECT name FROM pragma_table_info(?) WHERE name='migration_marker'", (TABLE,)
    ).fetchone()
    if not marker_col:
        print(f'WARNING: {TABLE} exists but has no migration_marker column. Refusing DROP to avoid destroying manual data.')
        return
    print(f'Dropping {TABLE}...')
    conn.execute(f"DROP TABLE {TABLE}")
    conn.commit()
    print('  Done.')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else '--stats'
    conn = _connect()
    try:
        if mode == '--stats':
            do_stats(conn)
        elif mode == '--apply':
            do_apply(conn)
        elif mode == '--revert':
            do_revert(conn)
        else:
            print(f'Unknown mode: {mode}. Use --stats / --apply / --revert')
    finally:
        conn.close()
