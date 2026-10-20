# -*- coding: utf-8 -*-
"""
T212 - Safe Canonical Curation: D1-A CLEAR_ALIAS (4 confirmed groups)

Admin-authorized: D1-A = APPROVE SAFE CURATION (T208 decision sheet)
Evidence source: T207-ADMIN-CURATION-DECISION-GATE-01.md

Modes:
  --stats    : in ra trang thai hien tai (read-only)
  --dry-run  : in mutation manifest, khong thay doi DB
  --apply    : chay mutations (can backup truoc)
  --revert   : rollback tu backup (phai chi dinh --backup-path)

MANIFEST (4 confirmed groups):
  DELETE vn_person_authority WHERE id='alias_A009319'   [A009319]
  DELETE vn_person_authority WHERE id='alias_A010534'   [A010534]
  DELETE vn_person_authority WHERE id='alias_A020120'   [A020120]
  DELETE vn_person_authority WHERE id='alias_A044094'   [A044094]

EXCLUDED (3 groups - pre-existing dila_id=NULL):
  A004981: phong_huyet_dien_chieu.dila_id=None - alias da bi tach truoc
  A021291: lao_na_tu_dang_dai_hoang.dila_id=None - alias da bi tach truoc
  A008471: hoang_long_tri_minh.dila_id=None - alias da bi tach truoc
"""
import sqlite3, hashlib, shutil, os, sys, argparse
from datetime import datetime

DB_PATH    = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'backups')

# ==================================================
# MANIFEST: 4 xac nhan CLEAR_ALIAS DELETE
# ==================================================
MANIFEST = [
    {
        'dila_id'     : 'A009319',
        'table'       : 'vn_person_authority',
        'pk_col'      : 'id',
        'pk_val'      : 'alias_A009319',
        'operation'   : 'DELETE',
        'old_name_vi' : 'Tung Son Pho Tich',
        'old_name_zh' : '嵩山普寂',  # 嵩山普寂
        'old_status'  : 'alias_vi_suffix',
        'keep_id'     : 'tung_son_pho_tich',
        'authority'   : 'T207 CLEAR_ALIAS + people.name_zh=嵩山普寂',
    },
    {
        'dila_id'     : 'A010534',
        'table'       : 'vn_person_authority',
        'pk_col'      : 'id',
        'pk_val'      : 'alias_A010534',
        'operation'   : 'DELETE',
        'old_name_vi' : 'Huyen Sach',
        'old_name_zh' : '玄策',  # 玄策
        'old_status'  : 'alias_vi_suffix',
        'keep_id'     : 'vu_chau_huyen_sach',
        'authority'   : 'T207 CLEAR_ALIAS + people.name_zh=玄策',
    },
    {
        'dila_id'     : 'A020120',
        'table'       : 'vn_person_authority',
        'pk_col'      : 'id',
        'pk_val'      : 'alias_A020120',
        'operation'   : 'DELETE',
        'old_name_vi' : 'Dam Chau Trung Van Cai',
        'old_name_zh' : '中雲蓋',  # 中雲蓋
        'old_status'  : 'alias_vi_suffix',
        'keep_id'     : 'dam_chau_trung_van_cai',
        'authority'   : 'T207 CLEAR_ALIAS + people.name_zh=中雲蓋',
    },
    {
        'dila_id'     : 'A044094',
        'table'       : 'vn_person_authority',
        'pk_col'      : 'id',
        'pk_val'      : 'alias_A044094',
        'operation'   : 'DELETE',
        'old_name_vi' : 'Ngo Hung Phap Hai',
        'old_name_zh' : '法海',  # 法海
        'old_status'  : 'alias_vi_suffix',
        'keep_id'     : 'thieu_chau_phap_hai',
        'authority'   : 'T207 CLEAR_ALIAS + people.name_zh=法海',
    },
]

EXPECTED_ROW_COUNT_CHANGED = 4

# Pre-states: (id, expected_dila_id, expected_status, expected_name_zh)
PRE_STATES = {
    'alias_A009319' : ('A009319', 'alias_vi_suffix', '嵩山普寂'),
    'alias_A010534' : ('A010534', 'alias_vi_suffix', '玄策'),
    'alias_A020120' : ('A020120', 'alias_vi_suffix', '中雲蓋'),
    'alias_A044094' : ('A044094', 'alias_vi_suffix', '法海'),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def get_stats(cur):
    cur.execute('SELECT COUNT(*) FROM vn_person_authority')
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vn_person_authority WHERE dila_id=''")
    empty = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM vn_person_authority WHERE dila_id IS NULL')
    null = cur.fetchone()[0]
    # Current count of the 4 alias rows
    alias_ids = [m['pk_val'] for m in MANIFEST]
    cur.execute(
        'SELECT COUNT(*) FROM vn_person_authority WHERE id IN ({})'.format(
            ','.join('?' for _ in alias_ids)
        ), alias_ids
    )
    alias_count = cur.fetchone()[0]
    return total, empty, null, alias_count


def preflight_check(cur):
    """Kiem tra pre-state cua 4 alias rows truoc khi DELETE."""
    errors = []
    for pk_val, (exp_dila, exp_status, exp_zh) in PRE_STATES.items():
        cur.execute(
            'SELECT id, dila_id, status, name_zh FROM vn_person_authority WHERE id=?',
            (pk_val,)
        )
        row = cur.fetchone()
        if row is None:
            errors.append(f'{pk_val}: ROW NOT FOUND — da bi xoa truoc?')
            continue
        rid, dila_id, status, name_zh = row
        if dila_id != exp_dila:
            errors.append(f'{pk_val}: dila_id={repr(dila_id)} != expected {repr(exp_dila)}')
        if status != exp_status:
            errors.append(f'{pk_val}: status={repr(status)} != expected {repr(exp_status)}')
        if (name_zh or '') != exp_zh:
            errors.append(f'{pk_val}: name_zh={repr(name_zh)} != expected {repr(exp_zh)}')
    return errors


def do_stats():
    con = sqlite3.connect('file:' + os.path.abspath(DB_PATH).replace('\\', '/') + '?mode=ro', uri=True)
    cur = con.cursor()
    total, empty, null, alias_count = get_stats(cur)
    print(f'vn_person_authority total : {total}')
    print(f'dila_id empty             : {empty}')
    print(f'dila_id NULL              : {null}')
    print(f'Alias rows still present  : {alias_count} / 4')
    print()
    print('Current state of manifest rows:')
    for m in MANIFEST:
        cur.execute(
            'SELECT id, dila_id, status, name_zh FROM vn_person_authority WHERE id=?',
            (m['pk_val'],)
        )
        r = cur.fetchone()
        if r:
            print(f"  [{m['dila_id']}] {r[0]}: dila_id={repr(r[1])} status={repr(r[2])} name_zh={repr(r[3] or '')}")
        else:
            print(f"  [{m['dila_id']}] {m['pk_val']}: NOT FOUND (da bi xoa)")
    con.close()


def do_dry_run():
    con = sqlite3.connect('file:' + os.path.abspath(DB_PATH).replace('\\', '/') + '?mode=ro', uri=True)
    cur = con.cursor()
    errors = preflight_check(cur)
    if errors:
        print('PREFLIGHT FAILED:')
        for e in errors: print(f'  ERROR: {e}')
        con.close()
        sys.exit(1)
    total, empty, null, _ = get_stats(cur)
    con.close()

    print('=== DRY-RUN: T212 D1-A Mutation Manifest ===')
    print()
    print(f'DB state before:')
    print(f'  vn_person_authority total : {total}')
    print(f'  dila_id empty             : {empty}')
    print(f'  dila_id NULL              : {null}')
    print()
    print('Mutations:')
    for i, m in enumerate(MANIFEST, 1):
        print(f"  {i}. DELETE FROM {m['table']} WHERE {m['pk_col']}='{m['pk_val']}'")
        print(f"     dila_id={m['dila_id']} | old_status={m['old_status']} | authority: {m['authority']}")
    print()
    print(f'EXPECTED_ROW_COUNT_CHANGED : {EXPECTED_ROW_COUNT_CHANGED}')
    print(f'Expected total after       : {total - EXPECTED_ROW_COUNT_CHANGED}')
    print()
    print('Excluded groups (pre-existing dila_id=NULL):')
    print('  A004981: phong_huyet_dien_chieu - da co dila_id=None, khong can DELETE')
    print('  A021291: lao_na_tu_dang_dai_hoang / dai_hong_to_chung - chi con 1 row dila_id=A021291 (auto_ttl, khong phai alias vi suffix)')
    print('  A008471: hoang_long_tri_minh - da co dila_id=None, khong can DELETE')
    print()
    print('DRY-RUN COMPLETE. Khong co thay doi DB.')


def do_apply():
    db_abs = os.path.abspath(DB_PATH)

    # 1. Backup
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'lineage_t212_{ts}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    print(f'[1/5] Backup: {backup_path}')
    shutil.copy2(db_abs, backup_path)
    sha_src = sha256_file(db_abs)
    sha_bk  = sha256_file(backup_path)
    if sha_src != sha_bk:
        print(f'BACKUP VERIFICATION FAILED: src={sha_src} bk={sha_bk}')
        sys.exit(1)
    print(f'     size: {os.path.getsize(backup_path):,}')
    print(f'     SHA256: {sha_bk}')
    print(f'     Verify: PASS')

    # 2. Preflight
    con = sqlite3.connect(db_abs)
    cur = con.cursor()
    print('\n[2/5] Preflight pre-state check...')
    errors = preflight_check(cur)
    if errors:
        print('PREFLIGHT FAILED — ABORT, no mutation:')
        for e in errors: print(f'  ERROR: {e}')
        con.close()
        sys.exit(1)
    total_before, _, _, alias_count_before = get_stats(cur)
    print(f'     Preflight: PASS ({alias_count_before} alias rows confirmed)')

    # 3. Apply in transaction
    print('\n[3/5] Applying mutations...')
    try:
        con.execute('BEGIN')
        affected = 0
        for m in MANIFEST:
            sql = f"DELETE FROM {m['table']} WHERE {m['pk_col']}=?"
            cur.execute(sql, (m['pk_val'],))
            n = cur.rowcount
            if n != 1:
                raise ValueError(
                    f"DELETE {m['pk_val']}: expected 1 row affected, got {n}"
                )
            affected += n
            print(f"     DELETE {m['pk_val']} ({m['dila_id']}) -> {n} row")

        if affected != EXPECTED_ROW_COUNT_CHANGED:
            raise ValueError(
                f'Total affected={affected} != expected {EXPECTED_ROW_COUNT_CHANGED}'
            )

        # Post-state verify
        total_after, _, _, alias_count_after = get_stats(cur)
        expected_total = total_before - EXPECTED_ROW_COUNT_CHANGED
        if total_after != expected_total:
            raise ValueError(
                f'Post-apply total={total_after} != expected {expected_total}'
            )
        if alias_count_after != 0:
            raise ValueError(
                f'Alias rows still present: {alias_count_after} (expected 0)'
            )

        con.execute('COMMIT')
        print(f'     Total affected: {affected} / {EXPECTED_ROW_COUNT_CHANGED} expected -> PASS')
        print(f'     Total rows: {total_before} -> {total_after} (delta={total_before - total_after})')

    except Exception as exc:
        con.execute('ROLLBACK')
        con.close()
        print(f'\nROLLBACK: {exc}')
        sys.exit(1)

    # 4. SHA256 post-apply
    print('\n[4/5] Post-apply verification...')
    sha_post = sha256_file(db_abs)
    print(f'     SHA256 post-apply: {sha_post}')
    print(f'     SHA256 backup:     {sha_bk}')
    print(f'     Changed (expected): {sha_post != sha_bk}')

    # 5. Done
    print('\n[5/5] Summary:')
    print(f'     Backup: {backup_path}')
    print(f'     Backup SHA256: {sha_bk}')
    print(f'     Mutations: {affected} DELETE')
    print(f'     Status: DONE')
    con.close()
    return backup_path, sha_bk, sha_post


def do_revert(backup_path):
    db_abs = os.path.abspath(DB_PATH)
    if not os.path.exists(backup_path):
        print(f'BACKUP NOT FOUND: {backup_path}')
        sys.exit(1)
    sha_bk = sha256_file(backup_path)
    shutil.copy2(backup_path, db_abs)
    sha_restored = sha256_file(db_abs)
    if sha_restored != sha_bk:
        print(f'REVERT VERIFICATION FAILED')
        sys.exit(1)
    print(f'REVERT: {backup_path} -> {db_abs}')
    print(f'SHA256: {sha_restored}')
    print('REVERT COMPLETE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='T212 Safe Canonical Curation')
    parser.add_argument('--stats',       action='store_true')
    parser.add_argument('--dry-run',     action='store_true')
    parser.add_argument('--apply',       action='store_true')
    parser.add_argument('--revert',      action='store_true')
    parser.add_argument('--backup-path', default='')
    args = parser.parse_args()

    if args.stats:
        do_stats()
    elif args.dry_run:
        do_dry_run()
    elif args.apply:
        do_apply()
    elif args.revert:
        if not args.backup_path:
            print('--revert requires --backup-path')
            sys.exit(1)
        do_revert(args.backup_path)
    else:
        parser.print_help()
