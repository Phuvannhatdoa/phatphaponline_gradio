"""
T94 Phase 1 — Tạo alignment schema (additive, không đụng data cũ)

Usage:
    python scripts/t94_create_alignment_schema.py --dry-run    # xem SQL sẽ chạy
    python scripts/t94_create_alignment_schema.py --apply      # tạo tables + columns
    python scripts/t94_create_alignment_schema.py --verify     # kiểm tra tables có chưa
    python scripts/t94_create_alignment_schema.py --revert     # DROP tables mới, DROP columns mới

ROLLBACK: python scripts/t94_create_alignment_schema.py --revert
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

NEW_TABLES = ['text_passages', 'translation_segments', 'passage_translation_alignment']
NEW_COLS   = [
    ('passage', 'raw_zh_hash',         'TEXT'),
    ('passage', 'passage_id_ref',      'TEXT'),
    ('passage', 'segmentation_method', "TEXT DEFAULT 'punctuation'"),
]

MIGRATIONS = [
    # 001
    """CREATE TABLE IF NOT EXISTS text_passages (
    passage_id          TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    source_system       TEXT NOT NULL DEFAULT 'CBETA',
    canonical_ref       TEXT,
    juan                TEXT,
    sequence_no         INTEGER,
    original_zh         TEXT NOT NULL,
    raw_zh_hash         TEXT NOT NULL,
    segmentation_method TEXT,
    tei_anchor_start    TEXT,
    tei_anchor_end      TEXT,
    source_url          TEXT,
    source_version      TEXT,
    import_run_id       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
)""",
    # 002
    """CREATE TABLE IF NOT EXISTS translation_segments (
    translation_id      TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    language            TEXT DEFAULT 'vi',
    translation_text    TEXT NOT NULL,
    translator_type     TEXT,
    model_name          TEXT,
    prompt_version      TEXT,
    source_passage_ids  TEXT,
    translation_status  TEXT DEFAULT 'draft',
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
)""",
    # 003
    """CREATE TABLE IF NOT EXISTS passage_translation_alignment (
    alignment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id          TEXT NOT NULL,
    translation_id      TEXT NOT NULL,
    alignment_type      TEXT NOT NULL,
    source_start_offset INTEGER,
    source_end_offset   INTEGER,
    confidence          REAL DEFAULT 0.5,
    alignment_method    TEXT,
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    note                TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passage_id) REFERENCES text_passages(passage_id),
    FOREIGN KEY (translation_id) REFERENCES translation_segments(translation_id)
)""",
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


def cmd_verify():
    con = _con()
    ok = True
    print('=== Verify alignment schema ===')
    for tbl in NEW_TABLES:
        exists = _table_exists(con, tbl)
        print(f'  {"✅" if exists else "❌"} {tbl}')
        if not exists:
            ok = False
    for table, col, _ in NEW_COLS:
        exists = _col_exists(con, table, col)
        print(f'  {"✅" if exists else "❌"} {table}.{col}')
        if not exists:
            ok = False
    con.close()
    if ok:
        print('\nPhase 1 schema: ĐẦY ĐỦ ✅')
    else:
        print('\nPhase 1 schema: CHƯA ĐỦ ❌ — Chạy --apply để tạo')
    return ok


def cmd_dry_run():
    con = _con()
    print('=== DRY RUN — SQL sẽ chạy khi --apply ===')
    for i, sql in enumerate(MIGRATIONS, 1):
        tbl = NEW_TABLES[i - 1]
        exists = _table_exists(con, tbl)
        status = '(đã có, SKIP)' if exists else '(sẽ tạo)'
        print(f'\n-- Migration {i:03d} {status}')
        print(sql[:120] + '...')
    print('\n-- Migration 004 — ALTER TABLE passage')
    for table, col, coldef in NEW_COLS:
        exists = _col_exists(con, table, col)
        status = '(đã có, SKIP)' if exists else '(sẽ thêm)'
        print(f'  ALTER TABLE {table} ADD COLUMN {col} {coldef}  {status}')
    con.close()
    print('\nKhông có gì bị thay đổi (dry-run).')


def cmd_apply():
    # Backup trước
    ts  = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BACK_DIR, f'lineage.db.backup_t94_{ts}')
    print(f'Backup → {bak}')
    shutil.copy2(DB_PATH, bak)
    bak_size = os.path.getsize(bak) // (1024 * 1024)
    print(f'  OK — {bak_size} MB')

    con = _con()
    applied = []
    skipped = []

    # Tạo tables
    for i, sql in enumerate(MIGRATIONS, 1):
        tbl = NEW_TABLES[i - 1]
        if _table_exists(con, tbl):
            skipped.append(tbl)
        else:
            con.execute(sql)
            con.commit()
            applied.append(tbl)
            print(f'  ✅ Created: {tbl}')

    # Thêm columns
    for table, col, coldef in NEW_COLS:
        if _col_exists(con, table, col):
            skipped.append(f'{table}.{col}')
        else:
            con.execute(f'ALTER TABLE {table} ADD COLUMN {col} {coldef}')
            con.commit()
            applied.append(f'{table}.{col}')
            print(f'  ✅ Added column: {table}.{col}')

    con.close()

    if skipped:
        print(f'  ⏭  Skipped (đã có): {", ".join(skipped)}')
    print(f'\nApplied: {len(applied)} | Skipped: {len(skipped)}')
    print(f'Rollback: python scripts/t94_create_alignment_schema.py --revert')


def cmd_revert():
    con = _con()
    print('=== REVERT — DROP tables mới, DROP columns mới ===')
    print('WARNING: Sẽ xóa TẤT CẢ dữ liệu trong 3 bảng alignment!')
    print('Tiếp tục? [y/N]', end=' ')
    ans = input().strip().lower()
    if ans != 'y':
        print('Đã hủy.')
        con.close()
        return

    # DROP alignment tables (ngược thứ tự để tránh FK conflict)
    for tbl in reversed(NEW_TABLES):
        if _table_exists(con, tbl):
            con.execute(f'DROP TABLE {tbl}')
            con.commit()
            print(f'  ✅ Dropped: {tbl}')
        else:
            print(f'  ⏭  Not found: {tbl}')

    # SQLite không hỗ trợ DROP COLUMN trước v3.35
    # Kiểm tra version
    ver = con.execute('SELECT sqlite_version()').fetchone()[0]
    major, minor = int(ver.split('.')[0]), int(ver.split('.')[1])
    if major > 3 or (major == 3 and minor >= 35):
        for table, col, _ in NEW_COLS:
            if _col_exists(con, table, col):
                con.execute(f'ALTER TABLE {table} DROP COLUMN {col}')
                con.commit()
                print(f'  ✅ Dropped column: {table}.{col}')
    else:
        print(f'  ⚠ SQLite {ver} < 3.35 — không DROP COLUMN được.')
        print(f'  Columns {[c[1] for c in NEW_COLS]} vẫn còn trong passage table (rỗng, vô hại).')

    con.close()
    print('\nRevert xong. Restore dữ liệu: cp lineage.db.backup_t94_* data/lineage.db')


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
