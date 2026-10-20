# -*- coding: utf-8 -*-
"""
T172 — Migration `person_hanviet_debug` (sidecar) + seed `hanviet_char_map` +
`hanviet_exception_list`. Zero-RAM, idempotent, backup, --revert.

SPEC: docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md §7

Usage:
    python scripts/t172_hanviet_charwise_migrate.py --dry-run     # xem SQL sẽ chạy (RO)
    python scripts/t172_hanviet_charwise_migrate.py --apply       # backup + seed + sweep full 48.673
    python scripts/t172_hanviet_charwise_migrate.py --apply --person A000006,A000044   # fixture nhỏ
    python scripts/t172_hanviet_charwise_migrate.py --apply --limit 2000
    python scripts/t172_hanviet_charwise_migrate.py --no-copy     # thay vì copy DB: dump 3 cột sang JSON
    python scripts/t172_hanviet_charwise_migrate.py --revert      # DROP 3 bảng sidecar (hỏi xác nhận)

Env override for test: T172_DB=<path>  (bản sao DB riêng — không đụng lineage.db thật)

Revert:
    1) python scripts/t172_hanviet_charwise_migrate.py --revert  (DROP sidecar)
    2) hoặc restore backup: data/backups/lineage_backup_t172_<ts>.db → data/lineage.db
KHÔNG bao giờ ghi `people` — test COUNT(*) people trước = sau.
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE    = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from t172_build_charmap import (  # noqa: E402
    CREATE_CHAR_MAP, INDEX_CHAR_MAP,
    is_ideograph, extract_han_viet_char, load_db_sources, merged_char_rows,
    compute_charwise, validate_status, legacy_compare,
    is_transliteration_flag, DICT_VERSION,
    VALIDATION_STATUSES, LEGACY_STATUSES,
)

ROOT    = os.path.dirname(BASE)
DB_PATH = os.environ.get('T172_DB') or os.path.join(ROOT, 'data', 'lineage.db')
BACK_DIR = os.path.join(ROOT, 'data', 'backups')

CREATE_DEBUG = """
CREATE TABLE IF NOT EXISTS person_hanviet_debug (
  person_id                  TEXT PRIMARY KEY,  -- = people.id (A000001…)
  han_name_raw               TEXT,
  han_viet_legacy            TEXT,
  han_viet_charwise          TEXT,
  han_char_count             INTEGER,
  han_viet_syllable_count    INTEGER,
  unknown_characters         TEXT,
  han_viet_validation_status TEXT,
  han_viet_validation_reason TEXT,
  legacy_match_status        TEXT,
  is_transliteration         INTEGER DEFAULT 0,
  dict_version               TEXT,
  updated_at                 TIMESTAMP
)
"""
CREATE_EXCEPTION = """
CREATE TABLE IF NOT EXISTS hanviet_exception_list (
  char_sequence TEXT PRIMARY KEY,
  note          TEXT,
  added_by      TEXT
)
"""
INDEX_DEBUG = [
    'CREATE INDEX IF NOT EXISTS idx_hvd_status ON person_hanviet_debug(han_viet_validation_status)',
    'CREATE INDEX IF NOT EXISTS idx_hvd_legacy ON person_hanviet_debug(legacy_match_status)',
    'CREATE INDEX IF NOT EXISTS idx_hvd_translit ON person_hanviet_debug(is_transliteration)',
]

# Seed ngoại lệ (SPEC §3) — phiên âm tên, từng-tự sẽ gây hiểu nhầm (Sanskrit Svara)
EXCEPTION_SEED = [
    ('蘇嚩羅', 'Tô Phược La — phiên âm Sanskrit/Svara, ngoại lệ không đối chiếu từng tự', 't172'),
]


def _con(path=None):
    con = sqlite3.connect(path or DB_PATH)
    con.execute('PRAGMA busy_timeout=10000')
    return con


def _table_exists(con, name):
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def backup_db(path=None):
    """File-level copy lineage.db → data/backups/lineage_backup_t172_<ts>.db (SPEC §7)."""
    src = path or DB_PATH
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(BACK_DIR, exist_ok=True)
    dst = os.path.join(BACK_DIR, f'lineage_backup_t172_{ts}.db')
    shutil.copy2(src, dst)
    return dst


def dump_people_json(path=None):
    """--no-copy: dump 3 cột people (id, name_zh, name_vi) sang JSON tạm."""
    con = _con(path)
    rows = con.execute('SELECT id, name_zh, name_vi FROM people ORDER BY id').fetchall()
    con.close()
    out = [{'id': r[0], 'name_zh': r[1], 'name_vi': r[2]} for r in rows]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(BACK_DIR, exist_ok=True)
    dst = os.path.join(BACK_DIR, f'lineage_t172_people3col_{ts}.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return dst, len(out)


def load_char_map(con):
    """Đọc toàn bộ hanviet_char_map → dict char → entry (bộ nhớ ~11.3k — Zero-RAM OK)."""
    cmap = {}
    for ch, reading, src, poly, cands in con.execute(
            'SELECT char, reading, source, is_polyphonic, candidates FROM hanviet_char_map'):
        cmap[ch] = {'reading': reading, 'is_polyphonic': poly, 'candidates': cands or ''}
    return cmap


def load_exceptions(con):
    return {r[0] for r in con.execute('SELECT char_sequence FROM hanviet_exception_list')}


# ────────────────────────────────────────────────────────────────────────
# Sweep tuần tự (generator + fetchmany(2000) — Zero-RAM)
# ────────────────────────────────────────────────────────────────────────
def iter_people(con, person_ids=None, limit=None):
    sql = 'SELECT id, name_zh, name_vi FROM people'
    params = []
    if person_ids:
        sql += f' WHERE id IN ({",".join("?" * len(person_ids))})'
        params = list(person_ids)
    sql += ' ORDER BY id'
    if limit:
        sql += f' LIMIT {int(limit)}'
    cur = con.execute(sql, params)
    while True:
        page = cur.fetchmany(2000)
        if not page:
            break
        for row in page:
            yield row
    cur.close()


def process_person(row, cmap, ex_set):
    pid, name_zh, name_vi = row[0], row[1] or '', row[2] or ''
    res = compute_charwise(name_zh, cmap)
    if res['han_count'] == 0:
        return None  # không phải tên Hán — bỏ qua
    han = [c for c in name_zh if is_ideograph(c)]
    exception_hit = ''.join(han) in ex_set
    legacy_match = legacy_compare(name_vi, res['charwise'])
    status, reason = validate_status(res['unknown'], exception_hit, res['poly'], legacy_match)
    translit = is_transliteration_flag(res['unknown'], legacy_match)
    return {
        'person_id': pid,
        'han_name_raw': name_zh,
        'han_viet_legacy': name_vi or None,
        'han_viet_charwise': res['charwise'],
        'han_char_count': res['han_count'],
        'han_viet_syllable_count': res['syll_count'],
        'unknown_characters': ''.join(res['unknown']) or None,
        'han_viet_validation_status': status,
        'han_viet_validation_reason': reason,
        'legacy_match_status': legacy_match,
        'is_transliteration': translit,
        'dict_version': DICT_VERSION,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def upsert_debug(con, rows):
    con.executemany(
        'INSERT OR REPLACE INTO person_hanviet_debug '
        '(person_id, han_name_raw, han_viet_legacy, han_viet_charwise, han_char_count, '
        ' han_viet_syllable_count, unknown_characters, han_viet_validation_status, '
        ' han_viet_validation_reason, legacy_match_status, is_transliteration, '
        ' dict_version, updated_at) '
        'VALUES (:person_id, :han_name_raw, :han_viet_legacy, :han_viet_charwise, '
        ' :han_char_count, :han_viet_syllable_count, :unknown_characters, '
        ' :han_viet_validation_status, :han_viet_validation_reason, :legacy_match_status, '
        ' :is_transliteration, :dict_version, :updated_at)', rows)


def print_status_counts(con):
    counts = []
    for st in VALIDATION_STATUSES:
        n = con.execute('SELECT COUNT(*) FROM person_hanviet_debug WHERE han_viet_validation_status=?',
                        (st,)).fetchone()[0]
        counts.append({'status': st, 'count': n})
    legacy = []
    for lm in LEGACY_STATUSES:
        n = con.execute('SELECT COUNT(*) FROM person_hanviet_debug WHERE legacy_match_status=?',
                        (lm,)).fetchone()[0]
        legacy.append({'legacy_match': lm, 'count': n})
    n_none = con.execute('SELECT COUNT(*) FROM person_hanviet_debug WHERE legacy_match_status IS NULL'
                         ).fetchone()[0]
    legacy.append({'legacy_match': 'NULL', 'count': n_none})
    translit = con.execute('SELECT COUNT(*) FROM person_hanviet_debug WHERE is_transliteration=1'
                           ).fetchone()[0]
    print('===== T172 status counts =====')
    for c in counts:
        print(f'  [status] {c["status"]:<12} {c["count"]:,}')
    for c in legacy:
        print(f'  [legacy_match] {str(c["legacy_match"]):<14} {c["count"]:,}')
    print(f'  [is_transliteration=1] {translit:,}')
    return {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'dict_version': DICT_VERSION,
        'status': counts,
        'legacy_match': legacy,
        'is_transliteration_count': translit,
    }


def cmd_dry_run():
    con = _con()
    print('=== DRY RUN — SQL sẽ chạy khi --apply ===')
    print(CREATE_CHAR_MAP)
    for q in INDEX_CHAR_MAP:
        print(q)
    print(CREATE_EXCEPTION)
    print(CREATE_DEBUG)
    for q in INDEX_DEBUG:
        print(q)
    print('-- seed exception list:')
    for seq, note, by in EXCEPTION_SEED:
        print(f'   INSERT OR REPLACE ({seq}, {note}, {by})')
    print(f'-- sweep  SELECT id, name_zh, name_vi FROM people ORDER BY id (fetchmany 2000)')
    who = [t for t in ('person_hanviet_debug', 'hanviet_char_map', 'hanviet_exception_list') if _table_exists(con, t)]
    print('-- tables đã tồn tại (sẽ re-seed idempotent):', who or '(chưa có)')
    con.close()


def cmd_apply(args):
    db = args.db_path or DB_PATH
    # backup hoặc --no-copy
    backup_path = None
    if not args.no_copy:
        backup_path = os.environ.get('T172_BACKUP') or backup_db(db)
        print(f'[backup] → {backup_path}')
    else:
        dst, n = dump_people_json(db)
        print(f'[no-copy] 3 cột people ({n:,}) → {dst}')

    con = _con(db)
    people_before = con.execute('SELECT COUNT(*) FROM people').fetchone()[0]
    try:
        # 1) hanviet_char_map (merge 3 dict, idempotent INSERT OR REPLACE)
        hv = extract_han_viet_char()
        dbs = load_db_sources(db)
        rows, viol = merged_char_rows(hv, dbs)
        con.execute(CREATE_CHAR_MAP)
        for q in INDEX_CHAR_MAP:
            con.execute(q)
        con.executemany(
            'INSERT OR REPLACE INTO hanviet_char_map(char, reading, source, is_polyphonic, candidates) '
            'VALUES (:char, :reading, :source, :is_polyphonic, :candidates)', rows)
        print(f'[charmap] {len(rows):,} chars seeded ({sum(1 for r in rows if r["is_polyphonic"]):,} đa âm)')
        if viol:
            print(f'⚠ {len(viol)} violations 1-âm-tiết (xem danh sách --stats của t172_build_charmap)')

        # 2) exception list seed
        con.execute(CREATE_EXCEPTION)
        con.executemany(
            'INSERT OR REPLACE INTO hanviet_exception_list(char_sequence, note, added_by) VALUES (?,?,?)',
            EXCEPTION_SEED)
        print(f'[exception] {len(EXCEPTION_SEED)} seed rows')

        # 3) sidecar sweep
        con.execute(CREATE_DEBUG)
        for q in INDEX_DEBUG:
            con.execute(q)
        if not _table_exists(con, 'person_hanviet_debug'):
            raise RuntimeError('person_hanviet_debug chưa được tạo — dừng để tránh UPSERT sai')
        cmap = load_char_map(con)
        ex_set = load_exceptions(con)

        batch = []
        n_rows = 0
        n_skipped = 0
        t0 = time.time()
        for row in iter_people(con, person_ids=args.person, limit=args.limit):
            rec = process_person(row, cmap, ex_set)
            if rec is None:
                n_skipped += 1
                continue
            batch.append(rec)
            if len(batch) >= 2000:
                upsert_debug(con, batch)
                con.commit()
                n_rows += len(batch)
                batch = []
        if batch:
            upsert_debug(con, batch)
            con.commit()
            n_rows += len(batch)
        el = time.time() - t0
        print(f'[sweep] {n_rows:,} person debug rows · {n_skipped:,} skipped (không phải tên Hán) · {el:.1f}s')

        people_after = con.execute('SELECT COUNT(*) FROM people').fetchone()[0]
        ok = people_before == people_after
        print(f'[immutable] people COUNT(*) {people_before:,} → {people_after:,}  {"✓ KHÔNG đổi" if ok else "✗ BỊ ĐỔI!"}')
        if not ok:
            raise RuntimeError('people bị thay đổi — dừng')

        # 4) log counts → console + data/t172_status_counts.json
        payload = print_status_counts(con)
        out = os.path.join(ROOT, 'data', 't172_status_counts.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f'[log] → {out}')
        print(f'[backup] {backup_path}')
    finally:
        con.close()


def cmd_revert(args):
    db = args.db_path or DB_PATH
    con = _con(db)
    try:
        arch = 'RESTORE backup: data/backups/lineage_backup_t172_*.db → ' + db
        print('Revert T172:')
        print('  DROP person_hanviet_debug')
        print('  DROP hanviet_exception_list')
        print('  DROP hanviet_char_map')
        print('  (KHÔNG đụng people)')
        print('  Khôi phục dữ liệu: %s' % arch)
        if not args.yes:
            ans = input('Nhập yes để DROP 3 bảng: ').strip().lower()
            if ans != 'yes':
                print('Đã hủy.'); return
        for t in ('person_hanviet_debug', 'hanviet_exception_list', 'hanviet_char_map'):
            con.execute(f'DROP TABLE IF EXISTS {t}')
        con.commit()
        print('✓ Đã DROP 3 bảng sidecar (people nguyên vẹn).')
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser(description='T172 hanviet charwise migration')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--revert', action='store_true')
    ap.add_argument('--yes', action='store_true', help='revert không hỏi')
    ap.add_argument('--no-copy', action='store_true', help='không copy DB (dump 3 cột JSON)')
    ap.add_argument('--person', help='chỉ xử lý các id (A000006,...)')
    ap.add_argument('--limit', type=int, help='giới hạn số person (thử trước)')
    ap.add_argument('--db-path', help='đè DB path (test)')
    args = ap.parse_args()
    if args.person:
        args.person = [p.strip() for p in args.person.split(',') if p.strip()]
    if args.dry_run:
        cmd_dry_run()
    elif args.apply:
        cmd_apply(args)
    elif args.revert:
        cmd_revert(args)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()