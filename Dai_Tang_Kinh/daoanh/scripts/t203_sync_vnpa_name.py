# -*- coding: utf-8 -*-
"""t203_sync_vnpa_name.py — [T203] đồng bộ `vn_person_authority.name_vi` theo nhãn chuẩn.

BỐI CẢNH
---------
32 file TTL có `rdfs:label` SAI (TIER-1 nhãn đảo sang người khác / TIER-2 không liên
quan). 28 file đã được ETL nạp vào `vn_person_authority` ⇒ DB đang lưu **tên sai**.

VÌ SAO CẦN SCRIPT NÀY
---------------------
- `etl_ttl_full_import.py` `phase1_upsert_persons` **skip** nếu `ttl_filename` đã tồn tại
  ⇒ sửa TTL rồi chạy lại ETL **KHÔNG** cập nhật dòng cũ.
- Nút CPadmin `POST /api/admin/ttl-etl/run` gọi script khác (`t05_ttl_namevi_etl.py`),
  script đó chỉ ghi bảng `people` ⇒ không đụng `vn_person_authority`.
⇒ Cần bước sync riêng, DATA-ONLY.

NGUỒN NÃN ĐÚNG
--------------
Nhãn chuẩn lấy từ chính corpus TTL: triple `<ex:monk/SLUG> rdfs:label "TÊN"@vi`.
`SLUG` = `ttl_filename` bỏ prefix `TS-`/`Cs-`/`Bo-Tat-`. **Không suy đoán chính tả.**

AN TOÀN
-------
- Chỉ UPDATE dòng có `name_vi` **đúng bằng** giá trị sai đã biết (guard chống ghi đè nhầm).
- Chỉ sửa dòng thuộc TIER-1/TIER-2 (bằng chứng mạnh), **không** đụng TIER-3 (danh xưng hợp lệ).
- `name_vi_map` / `people` **KHÔNG** đụng (0 ngoài phạm vi task này).
- Backup DB (`sqlite3.backup()`) + snapshot JSON trước khi ghi; `--revert` khôi phục.
- **KHÔNG** sửa `dila_id` (33 nhóm trùng là task riêng — lỗi `match_person`).

Usage:
    python -X utf8 scripts/t203_sync_vnpa_name.py --stats
    python -X utf8 scripts/t203_sync_vnpa_name.py --dry-run
    python -X utf8 scripts/t203_sync_vnpa_name.py --apply
    python -X utf8 scripts/t203_sync_vnpa_name.py --revert
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
REPORT = os.path.join(BACKUP_DIR, 't203_vnpa_name_sync.json')

sys.path.insert(0, HERE)
import t203_quarantine_ttl as Q  # noqa: E402


def build_plan(db_path=None):
    """Trả list {file, id, old, new, dila_id, tier} cho các dòng DB cần sửa."""
    db_path = db_path or DB_PATH
    t1, t2, _ = Q.classify()
    strong = [(r, 'TIER-1') for r in t1] + [(r, 'TIER-2') for r in t2]
    con = sqlite3.connect('file:' + db_path.replace('\\', '/') + '?mode=ro',
                          uri=True)
    con.row_factory = sqlite3.Row
    plan, already, absent = [], [], []
    for r, tier in strong:
        key = r['file'][:-4]
        row = con.execute(
            "SELECT id, name_vi, name_zh, dila_id, status, ttl_filename "
            "FROM vn_person_authority WHERE ttl_filename=?", (key,)).fetchone()
        if row is None:
            absent.append(r['file'])
            continue
        if Q.flat(row['name_vi']) == Q.flat(r['corr']):
            already.append({'file': r['file'], 'id': row['id'],
                            'name_vi': row['name_vi']})
            continue
        plan.append({'file': r['file'], 'id': row['id'], 'tier': tier,
                     'old': row['name_vi'], 'new': r['corr'],
                     'dila_id': row['dila_id'], 'status': row['status'],
                     'evidence': r['evidence']})
    con.close()
    return plan, already, absent


def do_stats(args):
    plan, already, absent = build_plan(args.db_path)
    print('=' * 84)
    print('T203 — SYNC vn_person_authority.name_vi (DATA-ONLY)')
    print('=' * 84)
    print('DB: %s' % (args.db_path or DB_PATH))
    print()
    print('[1] Dòng DB CẦN SỬA          : %d' % len(plan))
    for p in plan:
        print('   [%s] %-32s id=%-26s' % (p['tier'], p['file'], p['id']))
        print('        %r  ->  %r  (x%d nguồn)'
              % (p['old'], p['new'], p['evidence']))
    print()
    print('[2] Dòng DB đã ĐÚNG           : %d' % len(already))
    for a in already:
        print('   %-32s %r' % (a['file'], a['name_vi']))
    print()
    print('[3] File sai nhãn CHƯA vào DB : %d' % len(absent))
    for f in absent:
        print('   %s' % f)
    print()
    print('=' * 84)


def do_dry_run(args):
    plan, already, absent = build_plan(args.db_path)
    print('=' * 84)
    print('T203 — DRY RUN (0 ghi). %d dòng sẽ UPDATE.' % len(plan))
    print('=' * 84)
    for p in plan:
        print()
        print('  id       : %s' % p['id'])
        print('  ttl_file : %s   [%s]' % (p['file'], p['tier']))
        print('  dila_id  : %r  (KHÔNG đụng)' % p['dila_id'])
        print('  TỪ       : name_vi = %r' % p['old'])
        print('  SANG     : name_vi = %r' % p['new'])
    print()
    print('SQL (guard name_vi = giá trị cũ):')
    for p in plan:
        print("   UPDATE vn_person_authority SET name_vi=? WHERE id=? AND name_vi=?;")
    print()
    print('BACKUP: data/backups/lineage_t203_<ts>.db + t203_vnpa_name_sync.json')
    print('=' * 84)


def do_apply(args):
    plan, already, absent = build_plan(args.db_path)
    if not plan:
        print('[KHÔNG CÓ GÌ] mọi dòng đã đúng.')
        return 0
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    bkp = os.path.join(BACKUP_DIR, 'lineage_t203_%s.db' % ts)

    con = sqlite3.connect(args.db_path or DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        dst = sqlite3.connect(bkp)
        try:
            con.backup(dst)
        finally:
            dst.close()
        print('[BACKUP] %s' % bkp)

        with open(REPORT, 'w', encoding='utf-8') as f:
            json.dump({'ts': ts, 'backup': bkp,
                       'before': plan,
                       'already': already,
                       'absent': absent}, f, ensure_ascii=False, indent=1)
        print('[SNAPSHOT] %s' % REPORT)

        con.execute('BEGIN')
        done = []
        for p in plan:
            cur = con.execute(
                'UPDATE vn_person_authority SET name_vi=? WHERE id=? AND name_vi=?',
                (p['new'], p['id'], p['old']))
            if cur.rowcount != 1:
                raise RuntimeError(
                    'id=%s rowcount=%d (mong doi 1) — co dong bi doi tu truoc, dung lai'
                    % (p['id'], cur.rowcount))
            done.append(p)
        con.commit()
        print('[UPDATE] da sua %d dong' % len(done))
    except Exception as e:
        con.rollback()
        print('[LOI] %s' % e)
        print('       Da rollback. Khoi phuc: %s' % bkp)
        return 2
    finally:
        con.close()

    # verify
    plan2, already2, _ = build_plan(args.db_path)
    print()
    print('[VERIFY]')
    print('   con phai sua         : %d  (phai = 0)' % len(plan2))
    print('   da dung              : %d' % len(already2))
    con = sqlite3.connect('file:' + (args.db_path or DB_PATH).replace('\\', '/')
                          + '?mode=ro', uri=True)
    n_bad = con.execute(
        "SELECT COUNT(*) FROM vn_person_authority WHERE id LIKE 'alias_%' "
        "AND status='verified'").fetchone()[0]
    n_dup = con.execute(
        "SELECT COUNT(*) FROM (SELECT dila_id FROM vn_person_authority "
        "WHERE dila_id IS NOT NULL AND dila_id<>'' "
        "GROUP BY dila_id HAVING COUNT(*)>1)").fetchone()[0]
    print('   guard alias+verified : %d  (phai = 0)' % n_bad)
    print('   nhom dila_id trung   : %d  (khong doi — task rieng)' % n_dup)
    con.close()
    print()
    print('[XONG] backup: %s' % bkp)
    print('[REVERT] python -X utf8 scripts/t203_sync_vnpa_name.py --revert')
    return 0


def do_revert(args):
    if not os.path.exists(REPORT):
        print('[LỖI] Không có %s — chưa chạy --apply?' % REPORT)
        return 1
    with open(REPORT, encoding='utf-8') as f:
        rep = json.load(f)
    con = sqlite3.connect(args.db_path or DB_PATH)
    try:
        con.execute('BEGIN')
        for p in rep.get('before', []):
            con.execute(
                'UPDATE vn_person_authority SET name_vi=? WHERE id=? AND name_vi=?',
                (p['old'], p['id'], p['new']))
        con.commit()
        print('[REVERT] da khoi phuc %d dong' % len(rep.get('before', [])))
    except Exception as e:
        con.rollback()
        print('[LỖI] %s' % e)
        return 2
    finally:
        con.close()
    print('       hoac khoi phuc backup: %s' % rep.get('backup'))
    return 0


def main():
    p = argparse.ArgumentParser(
        description='T203 — sync vn_person_authority.name_vi theo nhãn chuẩn TTL')
    p.add_argument('--stats', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--revert', action='store_true')
    p.add_argument('--db-path', dest='db_path', default=None)
    args = p.parse_args()
    if args.revert:
        sys.exit(do_revert(args))
    if args.apply:
        sys.exit(do_apply(args))
    if args.dry_run:
        do_dry_run(args)
    else:
        do_stats(args)
    sys.exit(0)


if __name__ == '__main__':
    main()