# -*- coding: utf-8 -*-
"""
T215-VNPA-DILA-ID-RECOVERY-01
Khôi phục 33 giá trị vn_person_authority.dila_id bị mất do ETL INSERT OR REPLACE sau T211.

Nguồn xác thực: T214 forensic audit → T206 backup (100% khớp T207 backup).
Chỉ UPDATE WHERE dila_id IS NULL — không overwrite giá trị không phải NULL.
Không INSERT, không DELETE, không thay đổi schema.

Modes:
    --stats      In thống kê hiện tại (read-only)
    --dry-run    In manifest + xác minh pre-states, không ghi DB
    --apply      Backup → preflight → BEGIN → 33 UPDATE → assert → COMMIT
    --revert     Đặt lại 33 rows về NULL (undoes T215 only)

Usage:
    python scripts/t215_restore_vnpa_dila_ids.py --stats
    python scripts/t215_restore_vnpa_dila_ids.py --dry-run
    python scripts/t215_restore_vnpa_dila_ids.py --apply
    python scripts/t215_restore_vnpa_dila_ids.py --revert
    python scripts/t215_restore_vnpa_dila_ids.py --revert --backup-path data/backups/lineage_t215_....db
"""

import argparse
import hashlib
import os
import shutil
import sqlite3
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_ABS   = os.path.join(BASE_DIR, 'data', 'lineage.db')
BK_DIR   = os.path.join(BASE_DIR, 'data', 'backups')

# ─────────────────────────────────────────────────────────────
# MANIFEST — 33 rows từ T214 forensic evidence
# Source: T206 backup (lineage_t206_20261002_005334.db)
#         confirmed by T207 backup (100% match)
# Evidence class: BACKUP_VERIFIED (2 independent backups)
# ─────────────────────────────────────────────────────────────
MANIFEST = [
    ('chung_son_dao_long',        'A030596'),
    ('cuu_danh_to',               'A024897'),
    ('dam_chau_dai_xuyen',        'A020018'),
    ('dong_son_te_vi',            'A021350'),
    ('duong_chau_tue_giac',       'A026824'),
    ('hoa_nghiem_dao_long',       'A030596'),
    ('hoang_long_tri_minh',       'A008471'),
    ('kinh_trieu_thi_loi',        'A025951'),
    ('lang_nha_tue_giac',         'A026824'),
    ('lao_na_tu_dang_dai_hoang',  'A021291'),
    ('linh_thuu_tue_giac',        'A026824'),
    ('long_khanh_khanh_nhan',     'A014491'),
    ('ma_noa_la',                 'A008792'),
    ('nam_nhac_huyen_thai',       'A010511'),
    ('ngu_dai_tri_thong',         'A045400'),
    ('nguu_dau_hue_phuong',       'A038165'),
    ('nguyet_chuong_tri_uyen',    'A000108'),
    ('phap_nhu',                  'A045639'),
    ('phong_huyet_dien_chieu',    'A004981'),
    ('phu_son_duc_tuyen',         'A047679'),
    ('quang_tue_duc_tuyen',       'A047679'),
    ('so_an_hue_phuong',          'A038165'),
    ('song_lam_duc_dung',         'A021326'),
    ('tay_vuc_quat_da_tam_tang',  'A002653'),
    ('thach_cung_hue_tang',       'A009478'),
    ('thai_tu_dong_quang',        'A038615'),
    ('the_nham_ton_tho',          'A010511'),
    ('tho_chau_tri_thong',        'A045400'),
    ('tinh_do_thien_tu',          'A021084'),
    ('tri_hai_dao_binh',          'A014617'),
    ('tu_to_phap_dien',           'A021395'),
    ('tue_nhat_minh',             'A043012'),
    ('van_cu_phap_nhu',           'A045639'),
]

EXPECTED_ROWS_CHANGED  = 33
EXPECTED_FIELDS_CHANGED = 33

# T212 verified-deleted alias rows — must remain absent
T212_DELETED = ['alias_A009319', 'alias_A010534', 'alias_A020120', 'alias_A044094']


# ─────────────────────────────────────────────────────────────
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def get_conn(path=DB_ABS, ro=False):
    if ro:
        uri = 'file:' + path.replace('\\', '/') + '?mode=ro'
        con = sqlite3.connect(uri, uri=True)
    else:
        con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def print_stats(con):
    total = con.execute('SELECT COUNT(*) FROM vn_person_authority').fetchone()[0]
    null_ = con.execute("SELECT COUNT(*) FROM vn_person_authority WHERE dila_id IS NULL").fetchone()[0]
    empty = con.execute("SELECT COUNT(*) FROM vn_person_authority WHERE dila_id=''").fetchone()[0]
    has_v = con.execute("SELECT COUNT(*) FROM vn_person_authority WHERE dila_id IS NOT NULL AND dila_id!=''").fetchone()[0]
    print(f'  vn_person_authority total  : {total}')
    print(f'  dila_id IS NULL            : {null_}')
    print(f'  dila_id = ""               : {empty}')
    print(f'  dila_id has value          : {has_v}')
    return total, null_, empty, has_v


def preflight(con, mode='apply'):
    """Kiểm tra pre-states: mỗi row trong manifest phải có dila_id IS NULL."""
    print(f'\n[PREFLIGHT] Kiểm tra {EXPECTED_ROWS_CHANGED} rows...')
    errors = []
    ok_count = 0
    for pk, target_dila in MANIFEST:
        row = con.execute(
            'SELECT id, dila_id, name_vi, status FROM vn_person_authority WHERE id=?', (pk,)
        ).fetchone()
        if row is None:
            errors.append(f'  [ERROR] Row không tồn tại: id={pk!r}')
            continue
        if row['dila_id'] is not None:
            if mode == 'apply':
                errors.append(f'  [SKIP/WARN] id={pk!r} dila_id={row["dila_id"]!r} (không phải NULL → bỏ qua, idempotent)')
            else:
                errors.append(f'  [INFO] id={pk!r} dila_id={row["dila_id"]!r} (đã có giá trị)')
        else:
            ok_count += 1
            print(f'  [OK] id={pk!r} dila_id=NULL → sẽ restore thành {target_dila!r}')

    skipped = [e for e in errors if '[SKIP' in e]
    hard_errors = [e for e in errors if '[ERROR]' in e]

    if skipped:
        print('\n  Rows đã có giá trị (idempotent — bỏ qua khi apply):')
        for s in skipped:
            print(f'  {s}')

    if hard_errors:
        print('\n  HARD ERRORS:')
        for e in hard_errors:
            print(f'  {e}')
        return False, ok_count

    print(f'\n  → {ok_count} rows ready to restore, {len(skipped)} already have value (idempotent)')
    return True, ok_count


def verify_t212_preserved(con):
    """T212 legitimate deletions phải vẫn absent."""
    print('\n[T212 PRESERVATION CHECK]')
    ok = True
    for alias_id in T212_DELETED:
        row = con.execute('SELECT id FROM vn_person_authority WHERE id=?', (alias_id,)).fetchone()
        if row is not None:
            print(f'  [FAIL] T212 alias row tái xuất hiện: {alias_id!r}')
            ok = False
        else:
            print(f'  [OK] T212 deleted row vẫn absent: {alias_id!r}')
    return ok


# ─────────────────────────────────────────────────────────────
# MODE: --stats
# ─────────────────────────────────────────────────────────────
def mode_stats():
    print('=== T215 STATS (READ-ONLY) ===')
    st = os.stat(DB_ABS)
    print(f'  DB path  : {DB_ABS}')
    print(f'  DB size  : {st.st_size:,}')
    print(f'  DB mtime : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))}')
    print(f'  DB SHA256: {sha256_file(DB_ABS)}')
    con = get_conn(ro=True)
    print()
    print_stats(con)
    print()
    print(f'MANIFEST rows: {len(MANIFEST)}')
    print()
    # Show current state for all manifest rows
    null_count = 0
    nonnull_count = 0
    for pk, target_dila in MANIFEST:
        row = con.execute('SELECT dila_id FROM vn_person_authority WHERE id=?', (pk,)).fetchone()
        if row is None:
            print(f'  MISSING: id={pk!r}')
        elif row['dila_id'] is None:
            null_count += 1
        else:
            nonnull_count += 1
            print(f'  ALREADY_SET: id={pk!r} dila_id={row["dila_id"]!r}')
    print(f'  Manifest rows: NULL={null_count}, already-set={nonnull_count}')
    con.close()


# ─────────────────────────────────────────────────────────────
# MODE: --dry-run
# ─────────────────────────────────────────────────────────────
def mode_dry_run():
    print('=== T215 DRY-RUN ===')
    print(f'Manifest: {len(MANIFEST)} entries (T214 forensic evidence source: T206+T207 backups)\n')
    for i, (pk, dila) in enumerate(MANIFEST, 1):
        print(f'  [{i:02d}] UPDATE id={pk!r} SET dila_id={dila!r} WHERE dila_id IS NULL')
    con = get_conn(ro=True)
    ok, ready = preflight(con, mode='dry-run')
    if not ok:
        print('\n[DRY-RUN] PREFLIGHT FAILED — would STOP before apply')
    else:
        print(f'\n[DRY-RUN] PREFLIGHT OK — {ready} rows would be restored')
    print(f'\nEXPECTED_ROWS_CHANGED  = {EXPECTED_ROWS_CHANGED}')
    print(f'EXPECTED_FIELDS_CHANGED = {EXPECTED_FIELDS_CHANGED}')
    verify_t212_preserved(con)
    con.close()


# ─────────────────────────────────────────────────────────────
# MODE: --apply
# ─────────────────────────────────────────────────────────────
def mode_apply():
    print('=== T215 APPLY ===')

    # 1. DB baseline
    st_pre = os.stat(DB_ABS)
    sha_pre = sha256_file(DB_ABS)
    print(f'\n[1] DB baseline')
    print(f'  path  : {DB_ABS}')
    print(f'  size  : {st_pre.st_size:,}')
    print(f'  SHA256: {sha_pre}')

    # 2. Backup
    os.makedirs(BK_DIR, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    bk_name = f'lineage_t215_{ts}.db'
    bk_path = os.path.join(BK_DIR, bk_name)

    print(f'\n[2] Backup → {bk_path}')
    shutil.copy2(DB_ABS, bk_path)
    sha_bk = sha256_file(bk_path)
    print(f'  source SHA256 : {sha_pre}')
    print(f'  backup SHA256 : {sha_bk}')
    if sha_pre != sha_bk:
        print('[FATAL] Backup SHA256 mismatch — ABORT')
        sys.exit(1)
    # Verify backup opens
    try:
        test_con = sqlite3.connect(bk_path)
        test_con.execute('SELECT COUNT(*) FROM vn_person_authority').fetchone()
        test_con.close()
        print('  backup opens OK ✓')
    except Exception as e:
        print(f'[FATAL] Backup DB open failed: {e} — ABORT')
        sys.exit(1)
    print(f'  BACKUP VERIFIED ✓  (file: {bk_name})')

    # 3. Pre-apply stats
    con = get_conn()
    print('\n[3] Pre-apply stats')
    pre_total, pre_null, pre_empty, pre_has = print_stats(con)

    # 4. Preflight
    ok, ready = preflight(con, mode='apply')
    if not ok:
        print('\n[FATAL] PREFLIGHT FAILED — ABORT')
        con.close()
        sys.exit(1)

    # T212 preservation check
    if not verify_t212_preserved(con):
        print('\n[FATAL] T212 deleted rows reappeared — ABORT')
        con.close()
        sys.exit(1)

    # 5. Apply in transaction
    print(f'\n[5] Applying {ready} UPDATE statements...')
    try:
        con.execute('BEGIN')
        affected = 0
        for pk, target_dila in MANIFEST:
            cur = con.execute(
                'UPDATE vn_person_authority SET dila_id=? WHERE id=? AND dila_id IS NULL',
                (target_dila, pk)
            )
            if cur.rowcount > 0:
                affected += cur.rowcount
                print(f'  UPDATED id={pk!r} → dila_id={target_dila!r}')
            else:
                row = con.execute('SELECT dila_id FROM vn_person_authority WHERE id=?', (pk,)).fetchone()
                if row is None:
                    print(f'  [WARN] id={pk!r} NOT FOUND in DB')
                else:
                    print(f'  [SKIP] id={pk!r} dila_id={row["dila_id"]!r} (already set, idempotent)')

        print(f'\n  affected rows = {affected}')

        # 6. Assertions
        if affected != EXPECTED_ROWS_CHANGED:
            print(f'[FATAL] Expected {EXPECTED_ROWS_CHANGED} rows changed, got {affected} — ROLLBACK')
            con.execute('ROLLBACK')
            con.close()
            sys.exit(1)

        # Verify total unchanged
        post_total = con.execute('SELECT COUNT(*) FROM vn_person_authority').fetchone()[0]
        if post_total != pre_total:
            print(f'[FATAL] Total row count changed {pre_total}→{post_total} — ROLLBACK')
            con.execute('ROLLBACK')
            con.close()
            sys.exit(1)

        # Verify null count reduced
        post_null = con.execute("SELECT COUNT(*) FROM vn_person_authority WHERE dila_id IS NULL").fetchone()[0]
        expected_null = pre_null - affected
        if post_null != expected_null:
            print(f'[FATAL] Expected NULL count={expected_null}, got {post_null} — ROLLBACK')
            con.execute('ROLLBACK')
            con.close()
            sys.exit(1)

        # Verify empty unchanged
        post_empty = con.execute("SELECT COUNT(*) FROM vn_person_authority WHERE dila_id=''").fetchone()[0]
        if post_empty != pre_empty:
            print(f'[FATAL] Empty-string count changed {pre_empty}→{post_empty} — ROLLBACK')
            con.execute('ROLLBACK')
            con.close()
            sys.exit(1)

        # T212 preservation after apply
        if not verify_t212_preserved(con):
            print('\n[FATAL] T212 preservation failed after apply — ROLLBACK')
            con.execute('ROLLBACK')
            con.close()
            sys.exit(1)

        con.execute('COMMIT')
        print('\n[COMMIT] ✓')

    except Exception as e:
        print(f'[FATAL] Exception during apply: {e} — ROLLBACK')
        try:
            con.execute('ROLLBACK')
        except Exception:
            pass
        con.close()
        sys.exit(1)

    # 7. WAL checkpoint
    con.execute('PRAGMA wal_checkpoint(FULL)')
    con.close()

    # 8. Post-apply verification
    print('\n[6] Post-apply stats')
    con2 = get_conn(ro=True)
    post_total2, post_null2, post_empty2, post_has2 = print_stats(con2)

    # Field-level verify
    print('\n[7] Field-level verify (all 33 rows)')
    verify_ok = True
    for pk, target_dila in MANIFEST:
        row = con2.execute('SELECT dila_id FROM vn_person_authority WHERE id=?', (pk,)).fetchone()
        if row is None:
            print(f'  [FAIL] id={pk!r} NOT FOUND')
            verify_ok = False
        elif row['dila_id'] != target_dila:
            print(f'  [FAIL] id={pk!r} dila_id={row["dila_id"]!r} expected {target_dila!r}')
            verify_ok = False
        else:
            print(f'  [OK] id={pk!r} dila_id={row["dila_id"]!r} ✓')

    con2.close()

    if not verify_ok:
        print('\n[FATAL] Field-level verify FAILED')
        sys.exit(1)

    sha_post = sha256_file(DB_ABS)
    print(f'\n[8] Post-apply SHA256: {sha_post}')
    print(f'   (changed from: {sha_pre})')

    print(f'\n=== APPLY SUMMARY ===')
    print(f'  DB total     : {pre_total} → {post_total2} (delta={post_total2-pre_total})')
    print(f'  dila_id NULL : {pre_null} → {post_null2} (delta={post_null2-pre_null})')
    print(f'  dila_id ""   : {pre_empty} → {post_empty2} (unchanged)')
    print(f'  rows restored: {affected}')
    print(f'  backup       : {bk_path}')
    print(f'  backup SHA256: {sha_bk}')
    print(f'\nT215 --apply COMPLETE ✓')
    return bk_path, sha_bk, sha_pre, sha_post, affected


# ─────────────────────────────────────────────────────────────
# MODE: --revert
# ─────────────────────────────────────────────────────────────
def mode_revert(backup_path=None):
    """Revert: đặt 33 rows về NULL (undoes T215 only).
    Chỉ SET dila_id=NULL WHERE id=? AND dila_id=<expected_restored_value>.
    """
    print('=== T215 REVERT ===')

    if backup_path:
        # Hard revert via backup file
        print(f'Reverting via backup file: {backup_path}')
        if not os.path.exists(backup_path):
            print(f'[FATAL] Backup not found: {backup_path}')
            sys.exit(1)
        sha_bk = sha256_file(backup_path)
        shutil.copy2(backup_path, DB_ABS)
        sha_post = sha256_file(DB_ABS)
        if sha_bk != sha_post:
            print('[FATAL] Backup restore SHA256 mismatch')
            sys.exit(1)
        print(f'  Restored from backup. SHA256={sha_post}')
        # Checkpoint
        con = get_conn()
        con.execute('PRAGMA wal_checkpoint(FULL)')
        con.close()
        print('T215 revert via backup complete ✓')
        return

    # Soft revert: SET dila_id=NULL WHERE id=? AND dila_id=<expected>
    print('Reverting via soft UPDATE (SET dila_id=NULL for T215 manifest rows only)')
    con = get_conn()

    # Preflight: verify each row has the expected restored value
    print('\n[PREFLIGHT REVERT]')
    errors = []
    ok_count = 0
    for pk, expected_dila in MANIFEST:
        row = con.execute('SELECT dila_id FROM vn_person_authority WHERE id=?', (pk,)).fetchone()
        if row is None:
            errors.append(f'  [WARN] id={pk!r} not found')
            continue
        if row['dila_id'] != expected_dila:
            errors.append(f'  [SKIP] id={pk!r} dila_id={row["dila_id"]!r} (expected {expected_dila!r}, skip)')
        else:
            ok_count += 1

    for e in errors:
        print(e)
    print(f'  {ok_count} rows will be reverted to NULL')

    if ok_count == 0:
        print('[INFO] Nothing to revert (already NULL or no matching rows)')
        con.close()
        return

    try:
        con.execute('BEGIN')
        reverted = 0
        for pk, expected_dila in MANIFEST:
            cur = con.execute(
                'UPDATE vn_person_authority SET dila_id=NULL WHERE id=? AND dila_id=?',
                (pk, expected_dila)
            )
            reverted += cur.rowcount
        con.execute('COMMIT')
        print(f'\n  Reverted {reverted} rows to dila_id=NULL')
    except Exception as e:
        print(f'[FATAL] Revert failed: {e}')
        con.execute('ROLLBACK')
        con.close()
        sys.exit(1)

    con.execute('PRAGMA wal_checkpoint(FULL)')
    con.close()
    print('T215 revert complete ✓')


# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='T215 VNPA dila_id recovery')
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument('--stats',   action='store_true')
    grp.add_argument('--dry-run', action='store_true', dest='dry_run')
    grp.add_argument('--apply',   action='store_true')
    grp.add_argument('--revert',  action='store_true')
    parser.add_argument('--backup-path', default=None, help='Backup file for --revert')
    args = parser.parse_args()

    if args.stats:
        mode_stats()
    elif args.dry_run:
        mode_dry_run()
    elif args.apply:
        mode_apply()
    elif args.revert:
        mode_revert(args.backup_path)


if __name__ == '__main__':
    main()
