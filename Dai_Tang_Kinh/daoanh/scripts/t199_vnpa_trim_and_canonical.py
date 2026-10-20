# -*- coding: utf-8 -*-
"""t199_vnpa_trim_and_canonical.py — T199: TRIM khoảng trắng Hán + canonical row A001984.

DATA-ONLY. KHÔNG ALTER schema. KHÔNG đụng `status` của 450 row alias.

Usage:
    python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --stats
    python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --dry-run
    python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --apply
    python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert

Scope (Admin đã phê chuẩn 2026-09-30):
    1) TRIM vn_person_authority.name_zh     — 2 row
    2) TRIM marcus_reference.label         — 58 row
    3) INSERT canonical_decision 1 row cho A001984 — CHỈ KHI `--with-canonical`.
       ⚠ MẶC ĐỊNH TẮT vì canonical_decision là DEAD CODE:
         canonical_lock.py:871 dùng `pd.dila_id` nhưng places_dila PK = `id`
         ⇒ query nguồn #1 LUÔN throw `no such column: pd.dila_id`, _safe() nuốt ⇒ trả []
         ⇒ chèn row bây giờ là chèn 1 row CHẾT. Phải sửa code trước — task T201.
       Sau khi T201 sửa code + test PASS thì chạy:
         python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --apply --with-canonical
       Khi đó: canonical_lock._LOCK_FLAGS chứa 'canonical_decision.admin_approved' ⇒ LOCKED
               SOURCE_PRIORITY đặt 'canonical_decision' đầu tiên ⇒ thắng nguồn khác

KHÔNG làm (cố ý):
    - KHÔNG UPDATE status='verified' lên 450 row alias_vi_suffix
      (438/450 khác people.name_vi => sẽ khóa 438 tên sai trong canonical_lock)
    - KHÔNG TRIM name_vi (đã sạch 1506/1506)
    - KHÔNG sửa dila_id trùng (33 nhóm) -> task T200

REVERT:
    1) python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert
    2) hoặc khôi phục backup: data/backups/lineage_t199_<YYYYmmdd_HHMMSS>.db
"""
import argparse
import datetime
import json
import os
import sqlite3
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

# ---------------------------------------------------------------------------
# Hằng số scope — KHÔNG nới rộng
# ---------------------------------------------------------------------------
TARGET_DILA = 'A001984'
CANONICAL_NAME_VI = 'Quy Sơn Linh Hựu'   # == people.name_vi (verify 2026-09-30)
AUTHORITY_RANK = 'admin_approved'
VERIFICATION_STATUS = 'verified'
CONFIDENCE = 1.0
EDITOR = 'admin'
DECISION_NOTE = ('T199 — Admin phê chuẩn canonical row cho A001984 '
                 '(supersedes T179 plan bị bác: không flip status 450 row alias)')

# Guard: KHÔNG row alias nào được mang status='verified'
ALIAS_VERIFIED_GUARD = (
    "SELECT count(*) FROM vn_person_authority WHERE id LIKE 'alias_%' AND status='verified'"
)

# (bảng, cột) cần TRIM
TRIM_TARGETS = (
    ('vn_person_authority', 'name_zh'),
    ('marcus_reference', 'label'),
)


def _iso():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def _connect(path=None):
    return sqlite3.connect(path or DB_PATH)


def _backup(con):
    """Copy DB sang data/backups/lineage_t199_<ts>.db. Trả về path."""
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BACKUP_DIR, 'lineage_t199_%s.db' % ts)
    dst_con = sqlite3.connect(dst)
    try:
        con.backup(dst_con)
    finally:
        dst_con.close()
    return dst


# ---------------------------------------------------------------------------
# Thu thập dữ liệu
# ---------------------------------------------------------------------------
def collect_rows(con):
    """Trả về (trim_items, canonical_existing).

    trim_items: list of dict(table, column, key_col, key, old, new)
    canonical_existing: list row hiện có của TARGET_DILA trong canonical_decision
    """
    trim_items = []
    for table, col in TRIM_TARGETS:
        cols = [r[1] for r in con.execute('PRAGMA table_info(%s)' % table)]
        if col not in cols:
            raise SystemExit('[LOI] Bang %s khong co cot %s' % (table, col))
        # khoa: chon cot khoa duy nhat neu co, fall back 'id'/'node_id'
        key_col = None
        for cand in ('id', 'node_id', 'entity_ref'):
            if cand in cols:
                key_col = cand
                break
        if key_col is None:
            raise SystemExit('[LOI] Bang %s khong tim thay cot khoa' % table)
        sql = ('SELECT %s, %s FROM %s WHERE %s IS NOT NULL AND %s <> trim(%s)'
               % (key_col, col, table, col, col, col))
        for key, val in con.execute(sql):
            trim_items.append({
                'table': table, 'column': col, 'key_col': key_col, 'key': key,
                'old': val, 'new': val.strip(),
            })
    canonical_existing = con.execute(
        'SELECT entity_ref, canonical_name_vi, authority_rank, verification_status '
        'FROM canonical_decision WHERE entity_ref=?', (TARGET_DILA,)
    ).fetchall()
    return trim_items, canonical_existing


def print_stats(con):
    """Báo cáo read-only. Không ghi gì."""
    trim_items, canon = collect_rows(con)
    print('=' * 68)
    print('T199 — THONG KE (read-only, 0 ghi)')
    print('=' * 68)
    print('DB: %s' % DB_PATH)
    print()

    print('[1] Khoang trang thua (se TRIM)')
    for table, col in TRIM_TARGETS:
        n = len([i for i in trim_items if i['table'] == table])
        print('    %-24s %-10s %d row' % (table, col, n))
    print('    TONG: %d row' % len(trim_items))
    print('    (name_vi: KHONG sua — da sach 1506/1506)')
    print()

    print('[2] canonical_decision cho %s' % TARGET_DILA)
    if canon:
        for row in canon:
            print('    DA CO: %r' % (row,))
    else:
        print('    CHUA CO — chi se chen khi --apply --with-canonical')
        print('    ⚠ MAC DINH TAT: canonical_decision la DEAD CODE (canonical_lock.py:871')
        print('      `pd.dila_id` sai, places_dila PK=`id`) => nen chuyen sang task T201.')
    total = con.execute('SELECT count(*) FROM canonical_decision').fetchone()[0]
    print('    Tong canonical_decision trong DB: %d row' % total)
    print()

    print('[3] Guard: khong row alias nao co status=verified')
    print('    %s = %d' % (ALIAS_VERIFIED_GUARD,
                           con.execute(ALIAS_VERIFIED_GUARD).fetchone()[0]))
    print()

    print('[4] Phan bo status (nhan nguon goc, KHONG phai hang chat luong)')
    for status, n in con.execute(
            'SELECT status, count(*) FROM vn_person_authority '
            'GROUP BY status ORDER BY 2 DESC'):
        print('    %-24s %d' % (status, n))
    print()

    print('[5] dila_id trung (defer sang T200)')
    dup = con.execute(
        'SELECT count(*) FROM (SELECT dila_id FROM vn_person_authority '
        'WHERE dila_id IS NOT NULL AND dila_id <> "" '
        'GROUP BY dila_id HAVING count(*) > 1)').fetchone()[0]
    print('    So dila_id mang 2-3 dong: %d  (LIMIT 1 khong ORDER BY => khong xac dinh)' % dup)
    print('=' * 68)


def print_dry_run(con):
    """In chính xác thay đổi sẽ ghi. Không ghi gì."""
    trim_items, canon = collect_rows(con)
    print('=' * 68)
    print('T199 — DRY RUN (0 ghi)')
    print('=' * 68)

    print('[A] TRIM %d row' % len(trim_items))
    for it in trim_items:
        print('    %s.%s  %s=%r' % (it['table'], it['column'], it['key_col'], it['key']))
        print('        -%r' % it['old'])
        print('        +%r' % it['new'])
    print()

    print('[B] canonical_decision — CHI KHI --apply --with-canonical')
    if not args.with_canonical:
        print('    BO QUA (mac dinh): canonical_decision la DEAD CODE.')
        print('    Ly do: canonical_lock.py:871 dung `pd.dila_id` nhung places_dila PK=`id`')
        print('           => query nguon #1 LUON throw, _safe() nuot loi, tra []')
        print('           => chen row bay gio se la 1 row CHET. Task T201 se sua truoc.')
        print('    (T199 scope thuc te = TRIM 60 row Han + guard)')
    elif canon:
        print('    ⚠ DA CO row cho %s — KHONG insert de tranh trung.' % TARGET_DILA)
        for row in canon:
            print('      %r' % (row,))
    else:
        print('    entity_ref             = %r' % TARGET_DILA)
        print('    canonical_name_vi      = %r' % CANONICAL_NAME_VI)
        print('    authority_rank         = %r   -> LOCK (canonical_lock._LOCK_FLAGS)' % AUTHORITY_RANK)
        print('    confidence             = %s' % CONFIDENCE)
        print('    verification_status    = %r   -> LOCK' % VERIFICATION_STATUS)
        print('    source_id              = NULL')
        print('    decision_note          = %r' % DECISION_NOTE)
        print('    editor                 = %r' % EDITOR)
    print()

    print('[C] SQL se chay')
    print('    (60 dong, rut gon 3 dong mau de khong lam noi)')
    for it in trim_items[:2]:
        print('    UPDATE %s SET %s=? WHERE %s=? AND %s=?;'
              % (it['table'], it['column'], it['key_col'], it['column']))
    if not canon:
        print('    INSERT INTO canonical_decision')
        print('      (entity_ref, canonical_name_vi, authority_rank, confidence,')
        print('       verification_status, decision_note, evidence_citations, editor,')
        print('       decided_at, updated_at)')
        print('    VALUES (?,?,?,?,?,?,?,?,?,?);')
    print()
    print('=' * 68)
    print('⚠ ADMIN: xac nhan danh sach TRIM o tren roi chay --apply')
    print('=' * 68)


def do_apply(args):
    con = _connect(args.db)
    try:
        trim_items, canon = collect_rows(con)

        if args.with_canonical and canon and not args.force:
            print('[TU CHONG] %s da co row trong canonical_decision: %r' % (TARGET_DILA, canon))
            print('           Dung --force neu that su muon them.')
            return 1

        guard_bad = con.execute(ALIAS_VERIFIED_GUARD).fetchone()[0]
        if guard_bad:
            print('[TU CHONG] Guard: co %d row alias co status=verified.' % guard_bad)
            print('           nen xem lai truoc khi tien tiep.')
            return 1

        print('[BACKUP] dang tao %s ...' % BACKUP_DIR)
        bkp = _backup(con)
        print('[BACKUP] OK: %s' % bkp)

        # ghi snapshot de revert
        snap = os.path.join(BACKUP_DIR, 'lineage_t199_snapshot_%s.json' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        with open(snap, 'w', encoding='utf-8') as f:
            json.dump({'target': TARGET_DILA,
                       'trim': trim_items,
                       'canonical_before': [list(r) for r in canon]}, f, ensure_ascii=False, indent=1)
        print('[SNAPSHOT] %s' % snap)

        con.execute('BEGIN')
        for it in trim_items:
            cur = con.execute(
                'UPDATE %s SET %s=? WHERE %s=? AND %s=?'
                % (it['table'], it['column'], it['key_col'], it['column']),
                (it['new'], it['key'], it['old']))
            if cur.rowcount != 1:
                raise RuntimeError(
                    'TRIM %s.%s key=%r rowcount=%d (mong doi 1) — dung lai'
                    % (it['table'], it['column'], it['key'], cur.rowcount))
        con.commit()
        print('[TRIM] da cap nhat %d row' % len(trim_items))

        if args.with_canonical and not canon:
            ev = json.dumps([
                'people.id=A001984 name_zh=靈祐 (sạch)',
                'people.name_vi=Quy Sơn Linh Hựu',
                'vn_person_authority.alias_A001984.name_vi=Quy Sơn Linh Hựu',
            ], ensure_ascii=False)
            ts = _iso()
            con.execute(
                'INSERT INTO canonical_decision '
                '(entity_ref, canonical_name_vi, authority_rank, confidence, '
                ' verification_status, decision_note, evidence_citations, editor, '
                ' decided_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                (TARGET_DILA, CANONICAL_NAME_VI, AUTHORITY_RANK, CONFIDENCE,
                 VERIFICATION_STATUS, DECISION_NOTE, ev, EDITOR, ts, ts))
            con.commit()
            print('[CANON] da INSERT canonical_decision cho %s (--with-canonical)' % TARGET_DILA)
        elif args.with_canonical:
            print('[CANON] da co row, skip INSERT')
        else:
            print('[CANON] BO QUA — canh bao DEAD CODE o tren; xem task T201')

        print()
        print('[VERIFY]')
        for table, col in TRIM_TARGETS:
            left = con.execute(
                'SELECT count(*) FROM %s WHERE %s IS NOT NULL AND %s <> trim(%s)'
                % (table, col, col, col)).fetchone()[0]
            print('    %-24s %-10s con thua khoang trang: %d' % (table, col, left))
        vi_left = con.execute(
            "SELECT count(*) FROM vn_person_authority "
            "WHERE name_vi IS NOT NULL AND name_vi <> trim(name_vi)").fetchone()[0]
        print('    vn_person_authority.name_vi thua khoang trang: %d (phai = 0)' % vi_left)
        g = con.execute(ALIAS_VERIFIED_GUARD).fetchone()[0]
        print('    guard alias+verified: %d (phai = 0)' % g)
        pv = con.execute('SELECT name_vi FROM people WHERE id=?', (TARGET_DILA,)).fetchone()
        print('    people.name_vi %s = %r' % (TARGET_DILA, pv[0] if pv else None))
        cd = con.execute(
            'SELECT canonical_name_vi, authority_rank, verification_status '
            'FROM canonical_decision WHERE entity_ref=?', (TARGET_DILA,)).fetchall()
        print('    canonical_decision %s: %r' % (TARGET_DILA, cd))
        print()
        print('[XONG] backup: %s' % bkp)
        return 0
    except Exception as e:
        con.rollback()
        print('[LOI] %s' % e)
        print('       Da rollback. Khoi phuc backup neu can.')
        return 2
    finally:
        con.close()


def do_revert(args):
    """Khôi phục từ snapshot JSON gần nhất, hoặc báo cáo backup có sẵn."""
    if not os.path.isdir(BACKUP_DIR):
        print('[LOI] Khong co thu muc %s' % BACKUP_DIR)
        return 1
    snaps = sorted(f for f in os.listdir(BACKUP_DIR)
                   if f.startswith('lineage_t199_snapshot_') and f.endswith('.json'))
    if not snaps:
        print('[LOI] Khong tim thay snapshot JSON.')
        print('       Dung cach khoi phuc backup thu cong:')
        for f in sorted(os.listdir(BACKUP_DIR)):
            if f.startswith('lineage_t199_'):
                print('         data/backups/%s' % f)
        return 1
    latest = os.path.join(BACKUP_DIR, snaps[-1])
    print('[REVERT] dung snapshot %s' % latest)
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)
    con = _connect(args.db)
    try:
        con.execute('BEGIN')
        for it in data['trim']:
            cur = con.execute(
                'UPDATE %s SET %s=? WHERE %s=? AND %s=?'
                % (it['table'], it['column'], it['key_col'], it['column']),
                (it['old'], it['key'], it['new']))
            if cur.rowcount != 1:
                raise RuntimeError(
                    'REVERT %s.%s key=%r rowcount=%d (mong doi 1)'
                    % (it['table'], it['column'], it['key'], cur.rowcount))
        n_canon = con.execute(
            'DELETE FROM canonical_decision WHERE entity_ref=? AND authority_rank=?',
            (data['target'], AUTHORITY_RANK)).rowcount
        con.commit()
        print('[REVERT] da khoi phuc %d row TRIM + xoa %d canonical_decision row'
              % (len(data['trim']), n_canon))
        return 0
    except Exception as e:
        con.rollback()
        print('[LOI] %s' % e)
        return 2
    finally:
        con.close()


def main():
    p = argparse.ArgumentParser(
        description='T199 — TRIM khoang trang Han + canonical row A001984 (data-only)')
    p.add_argument('--stats', action='store_true', help='thong ke read-only')
    p.add_argument('--dry-run', action='store_true', help='in thay doi se ghi (0 ghi)')
    p.add_argument('--apply', action='store_true', help='backup + ghi')
    p.add_argument('--revert', action='store_true', help='khoi phuc theo snapshot')
    p.add_argument('--force', action='store_true', help='bo qua guard trung row')
    p.add_argument('--with-canonical', dest='with_canonical', action='store_true',
                   help='them canonical_decision row cho A001984 — CHI dung sau khi T201 '
                        'sua canonical_lock.py:871 (mac dinh TAT vi canonical_decision la DEAD CODE)')
    p.add_argument('--db-path', dest='db_path', default=None,
                   help='duong dan DB tuy chon (mac dinh data/lineage.db)')
    args = p.parse_args()
    args.db = args.db_path

    if args.revert:
        sys.exit(do_revert(args))
    if args.apply:
        sys.exit(do_apply(args))
    if not os.path.exists(args.db_path or DB_PATH):
        print('[LOI] Khong tim thay DB: %s' % (args.db_path or DB_PATH))
        sys.exit(1)
    con = _connect(args.db_path)
    try:
        if args.dry_run:
            print_dry_run(con)
        else:
            print_stats(con)
    finally:
        con.close()
    sys.exit(0)


if __name__ == '__main__':
    main()