# -*- coding: utf-8 -*-
"""
T169 Phase 1 — Side-car table `place_groq_audit` (additive, KHÔNG ALTER bảng lớn chung)

Quyết định Admin (A): không ALTER `places_pending`/`namevi_map_places` → bảng side-car
`place_groq_audit` (PK = places_dila.id). Revert = DROP TABLE 1 dòng + 2 index.

Usage:
    python scripts/t169_place_groq_audit_migrate.py --stats    # thống kê nguồn (RO)
    python scripts/t169_place_groq_audit_migrate.py --dry-run  # xem SQL sẽ chạy
    python scripts/t169_place_groq_audit_migrate.py --apply    # backup + tạo table + index
    python scripts/t169_place_groq_audit_migrate.py --revert   # DROP table + index (hỏi xác nhận)

ROLLBACK:
    1) python scripts/t169_place_groq_audit_migrate.py --revert    (DROP side-car, nhanh)
    2) hoặc restore backup: data/backups/lineage_t169_<ts>.db → data/lineage.db

Ghi chú:
    - Backup `--apply` dùng sqlite backup API (Zero-RAM giữ nguyên dữ liệu sống, WAL-safe).
    - Không chạm `places_pending` / `namevi_map_places` / `places_dila` (chỉ đọc stats).
"""
import os
import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE     = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.environ.get('T169_DB') or os.path.join(BASE, '..', 'data', 'lineage.db')
BACK_DIR = os.path.join(BASE, '..', 'data', 'backups')

# --- Bảng side-car (SPEC §4) ---
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS place_groq_audit (
  id             TEXT PRIMARY KEY,          -- = places_dila.id (PL long, zero-padded)
  name_zh        TEXT,
  dict_vi        TEXT,                      -- snapshot places_pending.name_vi lúc check
  groq_trans_vi  TEXT,
  needs_review   INTEGER DEFAULT 0,
  review_status  TEXT DEFAULT 'pending',    -- pending|verified|conflict|api_error|approved_dict
  diff_type      TEXT,                      -- NONE|POLYPHONIC_CHAR|TAXONOMY_VARIANT|PHONETIC_MISMATCH
  diff_reason    TEXT,
  model_id       TEXT,
  batch_id       TEXT,
  prompt_tokens  INTEGER,
  completion_tokens INTEGER,
  checked_at     TIMESTAMP
)
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_pga_review ON place_groq_audit(needs_review, review_status)",
    "CREATE INDEX IF NOT EXISTS idx_pga_diff   ON place_groq_audit(diff_type)",
]


def _con():
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA journal_mode=WAL')
    return con


def _table_exists(con, name):
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def cmd_stats():
    con = _con()
    print('=== T169 stats (read-only) ===')
    counts = {}
    for t in ('places_dila', 'places_pending', 'namevi_map_places'):
        try:
            counts[t] = con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except Exception as e:
            counts[t] = f'ERR {e}'
        print(f'  {t}: {counts[t]:,}' if isinstance(counts[t], int) else f'  {t}: {counts[t]}')
    try:
        n_zh = con.execute("SELECT COUNT(*) FROM places_dila WHERE name_zh IS NOT NULL AND name_zh != ''").fetchone()[0]
        joined = con.execute("""SELECT COUNT(*) FROM places_dila d
                                JOIN places_pending p ON p.id = d.id
                                WHERE d.name_zh IS NOT NULL AND d.name_zh != ''""").fetchone()[0]
        print(f'  places_dila có name_zh: {n_zh:,}')
        n_groups = joined // 25
        if joined % 25:
            n_groups += 1
        print(f'  spine (dila∩pending, zh valid): {joined:,} → {n_groups:,} batch × 25 (spec 2.366)')
    except Exception as e:
        print(f'  (skip scope stats: {e})')
    side = _table_exists(con, 'place_groq_audit')
    print(f'  place_groq_audit: {"đã tồn tại" if side else "CHƯA tạo"}')
    if side:
        for st, c in con.execute("SELECT review_status, COUNT(*) FROM place_groq_audit GROUP BY review_status"):
            print(f'    {st}: {c:,}')
    con.close()


def cmd_dry_run():
    con = _con()
    print('=== DRY RUN — SQL sẽ chạy khi --apply ===')
    st = '(đã có, SKIP)' if _table_exists(con, 'place_groq_audit') else '(sẽ tạo)'
    print(f'\nCREATE TABLE place_groq_audit {st}')
    print('\n'.join('  ' + l for l in CREATE_SQL.strip().splitlines()))
    for sql in INDEXES:
        print(f'  CREATE INDEX {sql.split("ON", 1)[1].strip().split("(")[0].strip()}')
    con.close()
    print('\nKhông có gì bị thay đổi (dry-run).')


def cmd_apply():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(BACK_DIR, exist_ok=True)
    bak = os.path.join(BACK_DIR, f'lineage_t169_{ts}.db')
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
    if not _table_exists(con, 'place_groq_audit'):
        con.execute(CREATE_SQL)
        con.commit()
        print('  ✅ Created: place_groq_audit')
    else:
        print('  ⏭ Skip (đã có): place_groq_audit')
    for sql in INDEXES:
        con.execute(sql)
    con.commit()
    print('  ✅ Indexes: idx_pga_review, idx_pga_diff')
    con.close()
    print('Hoàn tất — chạy --stats để kiểm tra.')


def cmd_revert():
    con = _con()
    if not _table_exists(con, 'place_groq_audit'):
        print('Không thấy place_groq_audit — không có gì để revert.')
        con.close()
        return False
    print('⚠️  REVERT sẽ DROP bảng side-car T169 + 2 index. Dữ liệu audit trong đó sẽ MẤT.')
    print('(Backup data/backups/lineage_t169_* vẫn giữ nếu cần khôi phục.)')
    print('Tiếp tục? [gõ "yes" để xác nhận]', end=' ')
    if input().strip().lower() != 'yes':
        print('Đã hủy.')
        con.close()
        return False
    con.execute('DROP TABLE IF EXISTS place_groq_audit')
    con.commit()
    print('  🗑 Dropped table: place_groq_audit')
    con.close()
    print('Revert hoàn tất.')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/t169_place_groq_audit_migrate.py --stats|--dry-run|--apply|--revert')
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