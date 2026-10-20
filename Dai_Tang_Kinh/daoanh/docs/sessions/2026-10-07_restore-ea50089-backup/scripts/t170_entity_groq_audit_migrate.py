# -*- coding: utf-8 -*-
"""
T170 Phase 1 — Side-car table `person_groq_audit` (additive, KHÔNG ALTER bảng lớn chung)

Chỉ tạo MỚI side-car person. `place_groq_audit` thuộc về T169 — guard: nếu tồn tại thì
verify cột khớp, KHÔNG DROP/recreate. `--revert` T170 chỉ DROP person side-car.

Usage:
    python scripts/t170_entity_groq_audit_migrate.py --stats    # thống kê nguồn (RO)
    python scripts/t170_entity_groq_audit_migrate.py --dry-run  # xem SQL sẽ chạy
    python scripts/t170_entity_groq_audit_migrate.py --apply    # backup + tạo table + index
    python scripts/t170_entity_groq_audit_migrate.py --revert   # DROP table person (hỏi xác nhận)

Env override for test: T170_DB=<path>

Revert:
    1) python scripts/t170_entity_groq_audit_migrate.py --revert    (DROP person side-car)
       (place thuộc T169: revert bằng scripts/t169_place_groq_audit_migrate.py --revert)
    2) hoặc restore backup: data/backups/lineage_t170_<ts>.db → data/lineage.db
"""
import os
import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE     = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.environ.get('T170_DB') or os.path.join(BASE, '..', 'data', 'lineage.db')
BACK_DIR = os.path.join(BASE, '..', 'data', 'backups')

# --- Bảng side-car person (SPEC §4) ---
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS person_groq_audit (
  id             TEXT PRIMARY KEY,          -- = people.id (A000001…)
  name_zh        TEXT,
  dict_vi        TEXT,                      -- snapshot people.name_vi lúc check
  groq_trans_vi  TEXT,
  final_vi       TEXT,
  clean_zh       TEXT,                      -- sau bracket-strip (R2)
  meta_note      TEXT,                      -- span ngoặc tách ra (R2)
  variant_zh     TEXT,
  is_uncertain   INTEGER DEFAULT 0,
  needs_review   INTEGER DEFAULT 0,
  review_status  TEXT DEFAULT 'pending',    -- enum §3.4
  diff_type      TEXT,
  diff_reason    TEXT,
  model_id       TEXT,
  batch_id       TEXT,
  prompt_tokens  INTEGER,
  completion_tokens INTEGER,
  retry_count    INTEGER DEFAULT 0,
  last_error     TEXT,
  processing_started_at TIMESTAMP,
  checked_at     TIMESTAMP
)
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_gpa_review ON person_groq_audit(needs_review, review_status)",
    "CREATE INDEX IF NOT EXISTS idx_gpa_diff   ON person_groq_audit(diff_type)",
]

# place T169 — 13 cột hiện có để guard verify (T170 KHÔNG đụng)
PLACE_T169_COLS = [
    'id', 'name_zh', 'dict_vi', 'groq_trans_vi', 'needs_review', 'review_status',
    'diff_type', 'diff_reason', 'model_id', 'batch_id', 'prompt_tokens',
    'completion_tokens', 'checked_at',
]


def _con():
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA busy_timeout=10000')
    return con


def _table_exists(con, name):
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _cols(con, name):
    try:
        return [r[1] for r in con.execute(f'PRAGMA table_info({name})')]
    except Exception:
        return []


def cmd_stats():
    con = _con()
    print('=== T170 stats (read-only) ===')
    counts = {}
    for t in ('people', 'people_full', 'places_dila'):
        try:
            counts[t] = con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except Exception as e:
            counts[t] = f'ERR {e}'
        print(f'  {t}: {counts[t]:,}' if isinstance(counts[t], int) else f'  {t}: {counts[t]}')
    try:
        n_zh = con.execute("SELECT COUNT(*) FROM people WHERE name_zh IS NOT NULL AND name_zh != ''").fetchone()[0]
        n_vi = con.execute("SELECT COUNT(*) FROM people WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]
        n_groups = n_zh // 25
        if n_zh % 25:
            n_groups += 1
        print(f'  people có name_zh: {n_zh:,} · có name_vi: {n_vi:,}')
        print(f'  spine person ~{n_groups:,} batch × 25')
    except Exception as e:
        print(f'  (skip person scope stats: {e})')
    p = _table_exists(con, 'person_groq_audit')
    print(f'  person_groq_audit: {"đã tồn tại" if p else "CHƯA tạo"}')
    if p:
        for st, c in con.execute("SELECT review_status, COUNT(*) FROM person_groq_audit GROUP BY review_status"):
            print(f'    {st}: {c:,}')
    place = _table_exists(con, 'place_groq_audit')
    place_ok = '(guard: bảng tồn tại — T170 KHÔNG đụng)'
    if place:
        cur_cols = _cols(con, 'place_groq_audit')
        if set(cur_cols) >= set(PLACE_T169_COLS):
            place_ok = f'(guard OK: 13 cột khớp T169 — KHÔNG đụng)'
        else:
            place_ok = f'(⚠️ CỘT LỆCH T169: {sorted(set(PLACE_T169_COLS) - set(cur_cols))})'
    print(f'  place_groq_audit: {"đã tồn tại " + place_ok if place else "KHÔNG tồn tại (bỏ qua, T169 quản lý)"}')
    con.close()


def cmd_dry_run():
    con = _con()
    print('=== DRY RUN — SQL sẽ chạy khi --apply ===')
    st = '(đã có, SKIP)' if _table_exists(con, 'person_groq_audit') else '(sẽ tạo)'
    print(f'\nCREATE TABLE person_groq_audit {st}')
    print('\n'.join('  ' + l for l in CREATE_SQL.strip().splitlines()))
    for sql in INDEXES:
        print(f'  CREATE INDEX {sql.split("ON", 1)[1].strip().split("(")[0].strip()}')
    if _table_exists(con, 'place_groq_audit'):
        print('  → place_groq_audit (T169): GUARD, không tạo lại / không DROP.')
    con.close()
    print('\nKhông có gì bị thay đổi (dry-run).')


def cmd_apply():
    con = _con()
    if not _table_exists(con, 'people'):
        print('❌ Thiếu bảng people (spine person). Không apply.')
        con.close()
        return
    con.close()

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(BACK_DIR, exist_ok=True)
    bak = os.path.join(BACK_DIR, f'lineage_t170_{ts}.db')
    print(f'Backup (sqlite backup API) → {bak}')

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(bak)
    with dst:
        src.backup(dst)
    dst.close()
    size_mb = (os.path.getsize(bak) // (1024 * 1024))
    print(f'  OK — {size_mb:,} MB')
    src.close()

    con = _con()
    if not _table_exists(con, 'person_groq_audit'):
        con.execute(CREATE_SQL)
        con.commit()
        print('  ✅ Created: person_groq_audit')
    else:
        print('  ⏭ Skip (đã có): person_groq_audit')
    for sql in INDEXES:
        con.execute(sql)
    con.commit()
    print('  ✅ Indexes: idx_gpa_review, idx_gpa_diff')
    if _table_exists(con, 'place_groq_audit'):
        cur_cols = _cols(con, 'place_groq_audit')
        if set(cur_cols) >= set(PLACE_T169_COLS):
            print('  🛡 Guard OK: place_groq_audit (T169) giữ nguyên 13 cột, không DROP.')
        else:
            print('  ⚠️ Guard WARN: place_groq_audit cột lệch T169 — báo Admin.')
    con.close()
    print('Hoàn tất — chạy --stats để kiểm tra.')


def cmd_revert():
    con = _con()
    if not _table_exists(con, 'person_groq_audit'):
        print('Không thấy person_groq_audit — không có gì để revert.')
        con.close()
        return False
    print('⚠️  REVERT sẽ DROP bảng side-car person T170 + 2 index. Dữ liệu audit trong đó sẽ MẤT.')
    print('(Backup data/backups/lineage_t170_* vẫn giữ nếu cần khôi phục.)')
    print('KHÔNG đụng place_groq_audit (thuộc T169).')
    print('Tiếp tục? [gõ "yes" để xác nhận]', end=' ')
    if input().strip().lower() != 'yes':
        print('Đã hủy.')
        con.close()
        return False
    con.execute('DROP TABLE IF EXISTS person_groq_audit')
    con.commit()
    print('  🗑 Dropped table: person_groq_audit')
    if _table_exists(con, 'place_groq_audit'):
        print('  🛡 place_groq_audit (T169) giữ nguyên.')
    con.close()
    print('Revert hoàn tất.')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/t170_entity_groq_audit_migrate.py --stats|--dry-run|--apply|--revert')
        sys.exit(1)
    flag = sys.argv[1]
    if flag == '--stats':
        cmd_stats()
    elif flag == '--dry-run':
        cmd_dry_run()
    elif flag == '--apply':
        cmd_apply()
    elif flag == '--revert':
        cmd_revert()
    else:
        print(f'Unknown flag: {flag}')
        sys.exit(1)