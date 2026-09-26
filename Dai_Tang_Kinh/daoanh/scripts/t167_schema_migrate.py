# -*- coding: utf-8 -*-
"""
T167 Phase 1 — Schema Rules-Constrained Translation (additive, không đụng data cũ)

Mở rộng cho Translation Constitution versioned:
  1. Bảng mới: translation_rulesets (ruleset_id, ruleset_version, description, is_canonical, ...)
  2. Bảng mới: translation_ruleset_rules (mapping ruleset ↔ rule)
  3. Cột additive: translation_segments.ruleset_id (TEXT)
  4. Cột additive: translation_rules.ruleset_id (TEXT), translation_rules.ruleset_version (TEXT), translation_rules.is_canonical (INTEGER)

Usage:
    python scripts/t167_schema_migrate.py --dry-run    # xem SQL sẽ chạy
    python scripts/t167_schema_migrate.py --apply      # backup + áp dụng
    python scripts/t167_schema_migrate.py --verify     # kiểm tra schema
    python scripts/t167_schema_migrate.py --revert     # DROP tables/columns mới (hỏi xác nhận)

ROLLBACK:
    1) python scripts/t167_schema_migrate.py --revert   (nếu SQLite >= 3.35)
    2) hoặc restore backup: copy lineage.db.backup_t167_* → data/lineage.db

Ghi chú:
    - translation_segments.ruleset_id DEFAULT '' (SQLite không cho ADD COLUMN NOT NULL không default)
    - translation_rules.ruleset_id/ruleset_version DEFAULT '' (upsert sẽ điền khi seed)
    - Tương thích additive với T95 + T123 (translation_rules đã có từ seed_style_constitution.py)
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

# --- Tables mới (T167 §Phase 1) ---
NEW_TABLES = [
    'translation_rulesets',
    'translation_ruleset_rules',
]

MIGRATIONS = [
    # 001 — translation_rulesets
    """CREATE TABLE IF NOT EXISTS translation_rulesets (
        ruleset_id          TEXT PRIMARY KEY,
        ruleset_version     TEXT NOT NULL,
        description         TEXT NOT NULL,
        is_canonical        INTEGER NOT NULL DEFAULT 0,
        created_by          TEXT DEFAULT 'system',
        created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (ruleset_version)
    )""",
    # 002 — translation_ruleset_rules (many-to-many ruleset ↔ rule)
    """CREATE TABLE IF NOT EXISTS translation_ruleset_rules (
        ruleset_id      TEXT NOT NULL,
        rule_code       TEXT NOT NULL,
        priority        INTEGER NOT NULL DEFAULT 0,
        is_active       INTEGER NOT NULL DEFAULT 1,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (ruleset_id, rule_code),
        FOREIGN KEY (ruleset_id) REFERENCES translation_rulesets(ruleset_id),
        FOREIGN KEY (rule_code) REFERENCES translation_rules(rule_code)
    )""",
]

# --- Cột additive mới ---
NEW_COLS = [
    # translation_segments — ruleset_id để truy vết constitution version per segment
    ('translation_segments',    'ruleset_id',              "TEXT DEFAULT ''"),
    # T167 Phase 4 — validator kết quả (điền bởi worker / CLI validator)
    ('translation_segments',    'validation_status',       "TEXT DEFAULT ''"),
    ('translation_segments',    'validation_report',       "TEXT DEFAULT ''"),
    ('translation_segments',    'validated_at',            "TEXT DEFAULT ''"),
    # translation_rules — extend with ruleset metadata (additive, dùng khi seed T167)
    ('translation_rules',       'ruleset_id',              "TEXT DEFAULT ''"),
    ('translation_rules',       'ruleset_version',         "TEXT DEFAULT ''"),
    ('translation_rules',       'is_canonical',            "INTEGER NOT NULL DEFAULT 0"),
]

# --- Index mới ---
NEW_INDEXES = [
    ("CREATE INDEX IF NOT EXISTS idx_ts_ruleset ON translation_segments(ruleset_id)",
     'translation_segments (ruleset_id)'),
    ("CREATE INDEX IF NOT EXISTS idx_ts_validation ON translation_segments(validation_status)",
     'translation_segments (validation_status)'),
    ("CREATE INDEX IF NOT EXISTS idx_ruleset_rules ON translation_ruleset_rules(ruleset_id, rule_code)",
     'translation_ruleset_rules (ruleset_id, rule_code)'),
    ("CREATE INDEX IF NOT EXISTS idx_rules_ruleset ON translation_rules(ruleset_id, ruleset_version)",
     'translation_rules (ruleset_id, ruleset_version)'),
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
    print('=== Verify T167 schema ===')
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
    print('\nT167 schema: ' + ('ĐẦY ĐỦ ✅' if ok else 'CHƯA ĐỦ ❌ — chạy --apply'))
    return ok


def cmd_dry_run():
    con = _con()
    print('=== DRY RUN — SQL sẽ chạy khi --apply ===')
    for i, sql in enumerate(MIGRATIONS, 1):
        tbl = NEW_TABLES[i - 1]
        st = '(đã có, SKIP)' if _table_exists(con, tbl) else '(sẽ tạo)'
        print(f'\n-- Migration {i:03d} — {tbl} {st}')
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
    bak = os.path.join(BACK_DIR, f'lineage.db.backup_t167_{ts}')
    print(f'Backup → {bak}')
    shutil.copy2(DB_PATH, bak)
    print(f'  OK — {os.path.getsize(bak) // (1024 * 1024)} MB')

    con = _con()
    applied, skipped = [], []

    for i, sql in enumerate(MIGRATIONS):
        tbl = NEW_TABLES[i]
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
            print(f'  ✅ Added: {table}.{col}')

    for sql, desc in NEW_INDEXES:
        con.execute(sql)
    con.commit()
    print(f'  ✅ Indexes created')

    con.close()
    print(f'\nApplied: {applied}')
    print(f'Skipped (đã có): {skipped}')
    print('Hoàn tất — chạy --verify để kiểm tra.')


def cmd_revert():
    over, ver = _sqlite_ok(_con())
    if not over:
        print(f'❌ SQLite {ver} không hỗ trợ DROP COLUMN (cần >= 3.35). Hãy restore backup.')
        return False

    print('⚠️  REVERT sẽ xóa tables/cột T167 MỚI TẠO. Data trong đó sẽ MẤT.')
    print('Tiếp tục? [gõ "yes" để xác nhận]', end=' ')
    if input().strip().lower() != 'yes':
        print('Đã hủy.')
        return False

    con = _con()
    # Drop columns (reverse order)
    for table, col, _ in reversed(NEW_COLS):
        if _col_exists(con, table, col):
            con.execute(f'ALTER TABLE {table} DROP COLUMN {col}')
            con.commit()
            print(f'  🗑 Dropped: {table}.{col}')
        else:
            print(f'  ⏭ Skip (không có): {table}.{col}')

    # Drop tables (reverse order)
    for tbl in reversed(NEW_TABLES):
        if _table_exists(con, tbl):
            con.execute(f'DROP TABLE {tbl}')
            con.commit()
            print(f'  🗑 Dropped table: {tbl}')
        else:
            print(f'  ⏭ Skip table (không có): {tbl}')

    con.close()
    print('Revert hoàn tất.')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/t167_schema_migrate.py --dry-run|--apply|--verify|--revert')
        sys.exit(1)
    flag = sys.argv[1]
    if flag == '--verify':
        cmd_verify()
    elif flag == '--dry-run':
        cmd_dry_run()
    elif flag == '--apply':
        cmd_apply()
    elif flag == '--revert':
        cmd_revert()
    else:
        print(f'Unknown flag: {flag}')
        sys.exit(1)