"""
t165_rules_engine_migrate.py — T165 Rules-Constrained Translation Engine — schema migration (additive)
========================================================================================================
Thêm 5 cột additive vào DB lineage.db:
  translation_rules:  match_scope TEXT DEFAULT 'always'  ('always' | 'terms')
                      match_terms  TEXT NULL              (JSON array Hán, ví dụ ["法嗣","三昧"])
  translation_cache:  constitution_hash  TEXT NULL   (sha16[:16] prompt thật đã dùng)
                      selected_rule_codes TEXT NULL   (CSV sorted codes đã inject; NULL = legacy "dính mọi rule")
                      glossary_hash      TEXT NULL    (sha16[:16] filtered glossary pairs + exemplar ids)

Backfill match_scope (quy tắc SPEC §4.2):
  1. rule_type='terminology' VÀ rule_text extract được ≥1 cặp Hán (regex §6.2) → match_scope='terms',
     match_terms = JSON list (lọc ≥2 chars, dedup).
  2. Còn lại → 'always' (an toàn — không giảm rule oan).
  In stats: n always / n terms / n extract fail→always.

Không DROP trong --apply mặc định. Idempotent (check pragma table_info trước khi ADD).
Usage:
    python scripts/t165_rules_engine_migrate.py --stats      # đọc trạng thái hiện tại (0 apply)
    python scripts/t165_rules_engine_migrate.py --dry-run    # in SQL + backup path (0 apply)
    python scripts/t165_rules_engine_migrate.py --apply      # backup + ADD + backfill (có backup trước)
    python scripts/t165_rules_engine_migrate.py --revert     # DROP 5 cột (rollback schema)
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

RULES_COLS = ('match_scope', 'match_terms')
CACHE_COLS = ('constitution_hash', 'selected_rule_codes', 'glossary_hash')

# Regex §6.2 — extract match terms từ rule_text:
#   1) "漢字 → vi" / "漢字 -> vi"  → group 1 là Hán
#   2) "vi (漢字)"                 → group 1 là Hán
# union, dedup, giữ 2-8 chars Hán; fail → []
_RE_ARROW = re.compile(r'([一-鿿㐀-䶿]{1,8})\s*(?:→|->|➞|⟶)\s*\S+')
_RE_PAREN = re.compile(r'[（(]([一-鿿㐀-䶿]{2,8})[）)]')
_RE_HAN = re.compile(r'^[一-鿿㐀-䶿]{2,8}$')


def extract_match_terms(rule_text):
    """Trích danh sách thuật ngữ Hán (2-8 chars) từ rule_text. Fail → []."""
    if not rule_text:
        return []
    terms = []
    for m in _RE_ARROW.finditer(rule_text):
        t = m.group(1).rstrip('：:：')
        if _RE_HAN.match(t):
            terms.append(t)
    for m in _RE_PAREN.finditer(rule_text):
        terms.append(m.group(1))
    seen, out = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _col_exists(conn, table, col):
    try:
        return any(r[1] == col for r in conn.execute(f'PRAGMA table_info({table})').fetchall())
    except Exception:
        return False


def _backup_path():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return os.path.join(BACKUP_DIR, f'lineage_t165_{datetime.datetime.now():%Y%m%d_%H%M%S}.db')


def _make_backup(conn):
    """Backup bằng sqlite backup API (an toàn khi DB đang mở)."""
    path = _backup_path()
    dst = sqlite3.connect(path)
    try:
        conn.backup(dst)
    finally:
        dst.close()
    return path


def _stats(conn):
    rules = [r[1] for r in conn.execute('PRAGMA table_info(translation_rules)')]
    cache = [r[1] for r in conn.execute('PRAGMA table_info(translation_cache)')]
    print('┌── T165 schema stats ──────────────────────────────')
    print('│ DB path:', DB_PATH)
    print('│ translation_rules.cols:', ', '.join(rules))
    print('│ translation_cache.cols :', ', '.join(cache))
    print('├── translation_rules ──')
    n_rules = conn.execute('SELECT COUNT(*) FROM translation_rules').fetchone()[0]
    n_term = conn.execute("SELECT COUNT(*) FROM translation_rules WHERE rule_type='terminology'").fetchone()[0]
    print(f'│ rows total          : {n_rules}')
    print(f'│ rows terminology    : {n_term}')
    # NC: dự kiến backfill
    if 'match_scope' not in rules:
        term_rows = conn.execute(
            "SELECT rule_text FROM translation_rules WHERE rule_type='terminology'"
        ).fetchall()
        n_terms = n_always = n_fail = 0
        for (rt,) in term_rows:
            terms = extract_match_terms(rt)
            if terms:
                n_terms += 1
            else:
                n_fail += 1
        non_term = n_rules - n_term
        print(f'│ [dry] → terms        : {n_terms} (extract OK)')
        print(f'│ [dry] extract fail   : {n_fail} (→ always)')
        print(f'│ [dry] → always       : {n_non_term_safe(non_term, n_fail)}')
    else:
        for row in conn.execute(
            "SELECT match_scope, COUNT(*) FROM translation_rules GROUP BY match_scope"
        ).fetchall():
            print(f'│ match_scope {row[0]!r:<10}: {row[1]}')
    print('├── translation_cache ──')
    n_cache = conn.execute('SELECT COUNT(*) FROM translation_cache').fetchone()[0]
    print(f'│ rows total          : {n_cache}')
    if 'constitution_hash' not in cache:
        print('│ [dry] constitution_hash/selected_rule_codes/glossary_hash = NULL (không đoán lịch sử)')
    else:
        n_ch = conn.execute("SELECT COUNT(*) FROM translation_cache WHERE constitution_hash IS NOT NULL").fetchone()[0]
        n_src = conn.execute("SELECT COUNT(*) FROM translation_cache WHERE selected_rule_codes IS NOT NULL").fetchone()[0]
        print(f'│ constitution_hash != NULL : {n_ch}')
        print(f'│ selected_rule_codes !=NULL: {n_src}')
    rv_bad = conn.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE rules_version IS NOT NULL "
        "AND rules_version NOT GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]"
        "[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'"
    ).fetchone()[0]
    print(f'│ rules_version không hợp lệ sha16 : {rv_bad} (giữ, lookup không match, không DELETE)')
    # T178 gap 13 — metrics
    has_metrics = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (_METRICS_TABLE,)
    ).fetchone()
    if has_metrics:
        n_m = conn.execute(f'SELECT COUNT(*) FROM {_METRICS_TABLE}').fetchone()[0]
        avg = conn.execute(
            f'SELECT AVG(prompt_tokens) FROM {_METRICS_TABLE} WHERE cache_hit=0'
        ).fetchone()[0]
        avg_txt = f'{avg:.0f}' if avg is not None else 'n/a'
        print(f'│ {_METRICS_TABLE}: {n_m} row · prompt_tokens TB (MISS) = {avg_txt}')
    else:
        print(f'│ {_METRICS_TABLE}: chưa tồn tại (chạy --apply để tạo — additive)')
    print('└──────────────────────────────────────────────────')


def n_non_term_safe(non_term, n_fail):
    return non_term + n_fail


def _sql_plan():
    return [
        ("translation_rules", "match_scope", "ADD COLUMN match_scope TEXT DEFAULT 'always'"),
        ("translation_rules", "match_terms", "ADD COLUMN match_terms TEXT"),
        ("translation_cache", "constitution_hash", "ADD COLUMN constitution_hash TEXT"),
        ("translation_cache", "selected_rule_codes", "ADD COLUMN selected_rule_codes TEXT"),
        ("translation_cache", "glossary_hash", "ADD COLUMN glossary_hash TEXT"),
    ]


# T178 gap 13 — bảng metrics append-only (KHÔNG đụng bảng/cột đang dùng)
_METRICS_TABLE = 'translation_prompt_metrics'
_METRICS_DDL = [
    f"""CREATE TABLE IF NOT EXISTS {_METRICS_TABLE} (
  id INTEGER PRIMARY KEY,
  measured_at TEXT NOT NULL DEFAULT (datetime('now')),
  source_type TEXT,
  source_len INTEGER,
  prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  model_id TEXT,
  cache_hit INTEGER NOT NULL DEFAULT 0,
  constitution_hash TEXT
)""",
    f"CREATE INDEX IF NOT EXISTS idx_prompt_metrics_time "
    f"ON {_METRICS_TABLE}(measured_at DESC)",
]


def _apply(conn):
    backup = _make_backup(conn)
    print(f'[backup] {backup}')
    added = 0
    for table, col, ddl in _sql_plan():
        if _col_exists(conn, table, col):
            print(f'[skip ] {table}.{col} đã tồn tại')
            continue
        conn.execute(f'ALTER TABLE {table} {ddl}')
        added += 1
        print(f'[add  ] {table}.{col}')

    # T178 gap 13: bảng metrics append-only + 2 index (idempotent CREATE IF NOT EXISTS)
    for ddl in _METRICS_DDL:
        conn.execute(ddl)
    conn.commit()
    n_metrics = conn.execute(f'SELECT COUNT(*) FROM {_METRICS_TABLE}').fetchone()[0]
    print(f'[add  ] {_METRICS_TABLE} (rows hiện tại: {n_metrics})')
    conn.commit()

    # Backfill match_scope/match_terms
    if _col_exists(conn, 'translation_rules', 'match_scope'):
        n_terms = n_always = n_fail = 0
        rows = conn.execute(
            "SELECT id, rule_type, rule_text FROM translation_rules"
        ).fetchall()
        for rid, rtype, rr_text in rows:
            terms = extract_match_terms(rr_text) if rtype == 'terminology' else []
            if terms:
                conn.execute(
                    "UPDATE translation_rules SET match_scope='terms', match_terms=? WHERE id=?",
                    (json.dumps(terms, ensure_ascii=False), rid)
                )
                n_terms += 1
            else:
                conn.execute(
                    "UPDATE translation_rules SET match_scope='always', match_terms=NULL WHERE id=?",
                    (rid,)
                )
                n_always += 1
                if rtype == 'terminology':
                    n_fail += 1
        conn.commit()
        print(f'[backfill match_scope] terms={n_terms} always={n_always} (trong đó terminology fail→always={n_fail})')
    else:
        print('[skip backfill] cột match_scope chưa tồn tại')

    # Backfill cache 3 cột = NULL (mặc định đã NULL — đảm bảo explicit)
    if _col_exists(conn, 'translation_cache', 'constitution_hash'):
        conn.execute(
            "UPDATE translation_cache SET constitution_hash=NULL, selected_rule_codes=NULL, glossary_hash=NULL "
            "WHERE constitution_hash IS NOT NULL OR selected_rule_codes IS NOT NULL OR glossary_hash IS NOT NULL"
        )
        conn.commit()
        print('[backfill cache] constitution_hash/selected_rule_codes/glossary_hash đặt NULL')

    print(f'[done ] backup: {backup}')
    return backup


def _revert(conn):
    dropped = 0
    # DROP theo thứ tự ngược để tránh phụ thuộc
    for table, col, _ddl in reversed(_sql_plan()):
        if _col_exists(conn, table, col):
            conn.execute(f'ALTER TABLE {table} DROP COLUMN {col}')
            dropped += 1
            print(f'[drop ] {table}.{col}')
        else:
            print(f'[skip ] {table}.{col} không tồn tại')
    # T178 gap 13: DROP bảng metrics (append-only → mất history đo, KHÔNG mất bản dịch)
    _t = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (_METRICS_TABLE,)
    ).fetchone()
    if _t:
        n = conn.execute(f'SELECT COUNT(*) FROM {_METRICS_TABLE}').fetchone()[0]
        conn.execute(f'DROP TABLE {_METRICS_TABLE}')
        print(f'[drop ] {_METRICS_TABLE} (mất {n} row metrics — chỉ log đo, không phải bản dịch)')
    else:
        print(f'[skip ] {_METRICS_TABLE} không tồn tại')
    conn.commit()
    print(f'[done ] dropped {dropped} cột + metrics table. (Dữ liệu cache mới giữ — đã mất fingerprint; miss dần qua hash.)')


def main():
    ap = argparse.ArgumentParser(description='T165 rules-engine schema migration (additive)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--stats', action='store_true', help='In trạng thái hiện tại (0 apply)')
    g.add_argument('--dry-run', action='store_true', help='In kế hoạch SQL + backup path (0 apply)')
    g.add_argument('--apply', action='store_true', help='Backup + ADD + backfill')
    g.add_argument('--revert', action='store_true', help='DROP 5 cột (rollback schema)')
    # T178: cho phép trỏ DB khác (test trên copy, KHÔNG đụng prod) — default giữ nguyên
    ap.add_argument('--db', default=None, help='DB path khác (test trên copy). Default: data/lineage.db')
    args = ap.parse_args()
    if args.db:
        global DB_PATH
        DB_PATH = args.db

    if not os.path.exists(DB_PATH):
        print(f'LỖI: không tìm thấy DB {DB_PATH}')
        sys.exit(1)

    if args.stats or args.dry_run:
        conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        try:
            _stats(conn)
            if args.dry_run:
                print('\n[SQL plan]')
                for table, col, ddl in _sql_plan():
                    print(f'  ALTER TABLE {table} {ddl};   # missing={not _col_exists(conn, table, col)}')
                print(f'  backup → {_backup_path()}')
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        if args.apply:
            print(f'[T165 --apply] opening: {DB_PATH}')
            backup = _apply(conn)
            print(f'BACKUP_PATH={backup}')
            _stats(conn)
        elif args.revert:
            print(f'[T165 --revert] opening: {DB_PATH}')
            _revert(conn)
        else:
            ap.error('thiếu --action')
    finally:
        conn.close()


if __name__ == '__main__':
    main()