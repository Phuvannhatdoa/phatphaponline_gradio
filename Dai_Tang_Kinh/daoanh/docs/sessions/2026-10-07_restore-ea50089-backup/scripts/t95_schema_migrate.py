# -*- coding: utf-8 -*-
"""
T95 Phase B — Schema dịch & alignment (additive, không đụng data cũ)

Mở rộng 3 bảng T94 (text_passages / translation_segments /
passage_translation_alignment) đang TRỐNG bằng các cột còn thiếu (spec T95), và
tạo mới 2 bảng job: translation_jobs + translation_job_items.

Usage:
    python scripts/t95_schema_migrate.py --dry-run    # xem SQL sẽ chạy
    python scripts/t95_schema_migrate.py --apply      # backup + áp dụng
    python scripts/t95_schema_migrate.py --verify     # kiểm tra schema
    python scripts/t95_schema_migrate.py --revert     # DROP tables/columns mới (hỏi xác nhận)

ROLLBACK:
    1) python scripts/t95_schema_migrate.py --revert   (nếu SQLite >= 3.35)
    2) hoặc restore backup: copy lineage.db.backup_t95_* → data/lineage.db

Ghi chú:
    - passage_id trên translation_segments được thêm dạng DEFAULT '' (SQLite không
      cho ADD COLUMN NOT NULL không default). NULL/'' bị chặn ở tầng ứng dụng (worker).
    - translation_segments.translation_status giữ DEFAULT 'draft' (cột cũ T94);
      'draft' xử lý tương đương 'pending' ở tầng ứng dụng.
"""
import sqlite3
import sys
import os
import shutil
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
BACK_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# --- Tables mới (spec T95 §B3, §B4) ---
NEW_TABLES = ['translation_jobs', 'translation_job_items']

MIGRATIONS = [
    # 005 — translation_jobs
    """CREATE TABLE IF NOT EXISTS translation_jobs (
        job_id               TEXT PRIMARY KEY,
        work_id              TEXT NOT NULL,
        requested_scope      TEXT NOT NULL,
        requested_by_user_id TEXT,
        provider             TEXT NOT NULL,
        model_name           TEXT NOT NULL,
        status               TEXT NOT NULL DEFAULT 'queued',
        next_passage_sequence INTEGER,
        total_passages       INTEGER NOT NULL,
        completed_passages   INTEGER NOT NULL DEFAULT 0,
        failed_passages      INTEGER NOT NULL DEFAULT 0,
        started_at           DATETIME,
        finished_at          DATETIME,
        last_error           TEXT,
        created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    # 006 — translation_job_items
    """CREATE TABLE IF NOT EXISTS translation_job_items (
        job_item_id        TEXT PRIMARY KEY,
        job_id             TEXT NOT NULL,
        passage_id         TEXT NOT NULL,
        sequence_no        INTEGER NOT NULL,
        status             TEXT NOT NULL DEFAULT 'queued',
        attempt_count      INTEGER NOT NULL DEFAULT 0,
        provider_request_id TEXT,
        raw_response_path  TEXT,
        error_message      TEXT,
        started_at         DATETIME,
        completed_at       DATETIME,
        FOREIGN KEY (job_id) REFERENCES translation_jobs(job_id),
        UNIQUE (job_id, passage_id)
    )""",
]

# --- Cột additive mới trên các bảng đã có ---
NEW_COLS = [
    # text_passages
    ('text_passages',           'source_status',           "TEXT DEFAULT 'ok'"),
    ('text_passages',           'loc_ref',                 'TEXT'),
    ('text_passages',           'canonical_start_anchor',  'TEXT'),
    ('text_passages',           'canonical_end_anchor',    'TEXT'),
    ('text_passages',           'legacy_passage_id',       'INTEGER'),
    ('text_passages',           'updated_at',              'DATETIME'),
    # translation_segments
    ('translation_segments',    'passage_id',              "TEXT DEFAULT ''"),
    ('translation_segments',    'provider',                'TEXT'),
    ('translation_segments',    'source_original_hash',    'TEXT'),
    ('translation_segments',    'quality_status',          "TEXT DEFAULT 'unreviewed'"),
    ('translation_segments',    'created_by_job_id',       'TEXT'),
    ('translation_segments',    'revision_no',             'INTEGER DEFAULT 1'),
    ('translation_segments',    'supersedes_translation_id', 'TEXT'),
    # passage_translation_alignment
    ('passage_translation_alignment', 'updated_at',        'DATETIME'),
    # translation_job_items (bổ sung sau khi tạo bảng — created_at)
    ('translation_job_items',        'created_at',         'DATETIME DEFAULT CURRENT_TIMESTAMP'),
]

# --- Index mới ---
NEW_INDEXES = [
    ("CREATE INDEX IF NOT EXISTS idx_tp_work_seq ON text_passages(work_id, sequence_no)",
     'text_passages (work_id, sequence_no)'),
    ("CREATE INDEX IF NOT EXISTS idx_ts_passage ON translation_segments(passage_id)",
     'translation_segments (passage_id)'),
    ("CREATE INDEX IF NOT EXISTS idx_ts_status ON translation_segments(translation_status, quality_status)",
     'translation_segments (translation_status, quality_status)'),
    ("CREATE INDEX IF NOT EXISTS idx_align_passage ON passage_translation_alignment(passage_id)",
     'passage_translation_alignment (passage_id)'),
    ("CREATE INDEX IF NOT EXISTS idx_tjobs_work ON translation_jobs(work_id, status)",
     'translation_jobs (work_id, status)'),
    ("CREATE INDEX IF NOT EXISTS idx_tjitems_job ON translation_job_items(job_id)",
     'translation_job_items (job_id)'),
]


def _con():
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA journal_mode=WAL')
    return con


def _table_exists(con, name):
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _col_exists(con, table, col):
    cur = con.execute(f'PRAGMA table_info({table})')
    return any(r[1] == col for r in cur.fetchall())


def _sqlite_ok(con):
    ver = con.execute('SELECT sqlite_version()').fetchone()[0]
    major, minor = int(ver.split('.')[0]), int(ver.split('.')[1])
    return (major, minor) >= (3, 35), ver


def cmd_verify():
    con = _con()
    ok = True
    print('=== Verify T95 schema ===')
    for tbl in NEW_TABLES:
        e = _table_exists(con, tbl)
        ok = ok and e
        print(f'  {"✅" if e else "❌"} table {tbl}')
    for table, col, _ in NEW_COLS:
        e = _col_exists(con, table, col)
        ok = ok and e
        print(f'  {"✅" if e else "❌"} {table}.{col}')
    over, ver = _sqlite_ok(con)
    print(f'  ℹ SQLite {ver} — DROP COLUMN {"OK" if over else "không hỗ trợ"}')
    con.close()
    print('\nT95 schema: ' + ('ĐẦY ĐỦ ✅' if ok else 'CHƯA ĐỦ ❌ — chạy --apply'))
    return ok


def cmd_dry_run():
    con = _con()
    print('=== DRY RUN — SQL sẽ chạy khi --apply ===')
    for i, sql in enumerate(MIGRATIONS, 1):
        tbl = NEW_TABLES[i - 1]
        st = '(đã có, SKIP)' if _table_exists(con, tbl) else '(sẽ tạo)'
        print(f'\n-- Migration {i + 4:03d} — {tbl} {st}')
        print(sql[:130] + '...')
    print('\n-- ALTER TABLE (cột additive)')
    for table, col, coldef in NEW_COLS:
        st = '(đã có, SKIP)' if _col_exists(con, table, col) else '(sẽ thêm)'
        print(f'  ALTER TABLE {table} ADD COLUMN {col} {coldef}  {st}')
    print('\n-- CREATE INDEX')
    for _, desc in NEW_INDEXES:
        print(f'  index {desc}')
    con.close()
    print('\nKhông có gì bị thay đổi (dry-run).')


def cmd_apply():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BACK_DIR, f'lineage.db.backup_t95_{ts}')
    print(f'Backup → {bak}')
    shutil.copy2(DB_PATH, bak)
    print(f'  OK — {os.path.getsize(bak) // (1024 * 1024)} MB')

    con = _con()
    applied, skipped = [], []

    for i, sql in enumerate(MIGRATIONS, 1):
        tbl = NEW_TABLES[i - 1]
        if _table_exists(con, tbl):
            skipped.append(tbl)
        else:
            con.execute(sql)
            con.commit()
            applied.append(tbl)
            print(f'  ✅ Created: {tbl}')

    for table, col, coldef in NEW_COLS:
        if _col_exists(con, table, col):
            skipped.append(f'{table}.{col}')
        else:
            con.execute(f'ALTER TABLE {table} ADD COLUMN {col} {coldef}')
            con.commit()
            applied.append(f'{table}.{col}')
            print(f'  ✅ Added column: {table}.{col}')

    for sql, desc in NEW_INDEXES:
        con.execute(sql)
        con.commit()
        print(f'  ✅ Index: {desc}')

    con.close()
    if skipped:
        print(f'  ⏭  Skipped (đã có): {", ".join(skipped)}')
    print(f'\nApplied: {len(applied)} | Skipped: {len(skipped)}')
    print(f'Backup: {bak}')
    print('Rollback: python scripts/t95_schema_migrate.py --revert (hoặc restore backup)')


def cmd_revert():
    con = _con()
    over, ver = _sqlite_ok(con)
    print('=== REVERT — DROP tables/columns mới ===')
    print('⚠ Sẽ xóa mọi dữ liệu trong translation_jobs / translation_job_items và')
    print('  các cột mới (rỗng — chưa có data nếu revert ngay sau apply).')
    if not over:
        print(f'  ⚠ SQLite {ver} < 3.35: chỉ DROP được tables, KHÔNG DROP cột.')
    print('Tiếp tục? [y/N]', end=' ')
    if input().strip().lower() != 'y':
        print('Đã hủy.')
        con.close()
        return

    for tbl in reversed(NEW_TABLES):
        if _table_exists(con, tbl):
            con.execute(f'DROP TABLE {tbl}')
            con.commit()
            print(f'  ✅ Dropped: {tbl}')
        else:
            print(f'  ⏭  Not found: {tbl}')

    if over:
        for table, col, _ in list(reversed(NEW_COLS)):
            if _col_exists(con, table, col):
                con.execute(f'ALTER TABLE {table} DROP COLUMN {col}')
                con.commit()
                print(f'  ✅ Dropped column: {table}.{col}')
    else:
        print(f'  ⚠ Còn {len(NEW_COLS)} cột mới không DROP được — restore backup nếu muốn sạch.')
    con.close()
    print('\nRevert xong. Restore data: cp data/lineage.db.backup_t95_* data/lineage.db')


if __name__ == '__main__':
    args = set(sys.argv[1:])
    if '--verify' in args:
        cmd_verify()
    elif '--dry-run' in args:
        cmd_dry_run()
    elif '--apply' in args:
        cmd_apply()
    elif '--revert' in args:
        cmd_revert()
    else:
        print(__doc__)