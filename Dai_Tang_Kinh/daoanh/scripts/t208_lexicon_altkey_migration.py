# -*- coding: utf-8 -*-
"""t208_lexicon_altkey_migration.py — [T208] thêm khoá tra cứu PHỤ cho `lexicon`.

VÌ SAO KHÔNG TÍNH LẠI `key_norm`
-------------------------------
Đề xuất ban đầu của T208 là tính lại `key_norm = normalize_text(term)` cho
53.384 row. **ĐO ĐÃ BÁC BỎ ĐỀ XUẤT ĐÓ** (probe_t208.py):

  * 6.866 khoá mới bị TRÙNG, 15.453 row dính vào.
  * 241 khoá va chạm với term **KHÁC NGHĨA**:
        'dinh'  <- Định   nhưng đang có Dĩnh
        'tu do'  <- Tứ Độ  nhưng đang có Tự Do
        'tam duc'<- Tam Đức nhưng đang có Tam Dục
        'that dai'<- Thất Đại nhưng đang có Thật Dài
    ⇒ tra cứu sẽ trả về DỊCH SAI cho các mục Phật học khác nhau.

Ngoài ra probe_t208b.py cho thấy `key_norm` của 53.384 row **không do normalizer
nào sinh ra được** — nó tự mâu thuẫn trong cùng một chuỗi:
    'Đuc lon. tu ton xung nhung nguoi đao đuc lon.'      ← Đ hoa rồi đ thường
Chỉ 36,3% khớp được với "bỏ dấu nhưng giữ đ/Đ" ⇒ đây là **dữ liệu hỏng**, không
phải lệch quy ước. Sửa hàng loạt là sai.

PHƯƠNG ÁN AN TOÀN ĐÃ CHỌN
-------------------------
KHÔNG ghi lại dữ liệu nào. Thêm **cột mới** `key_norm_alt` chỉ cho những row mà
tra cứu hiện tại KHÔNG tìm được, và chỉ khi khoá phụ đó trỏ tới **ĐÚNG MỘT
term** trong toàn bảng (probe_t208c/d):

    Lớp 1: khoá phụ chỉ trỏ tới 1 term duy nhất  -> loại 2.194 row mơ rồng
    Lớp 2: khoá phụ chưa bị term nào chiếm      -> loại phần còn lại
    ⇒ AN TOÀN: 19.481 / 21.675 ứng viên (term < 60 ký tự, đúng điều kiện
      `LENGTH(term) < 60` của `app.py:1250`)

`key_norm` GỮ NGUYÊN 100% ⇒ hành vi tra cứu HIỆN TẠI không đổi.
Revert = `DROP COLUMN` + `DROP INDEX` ⇒ **không mất dữ liệu nào**.

An toàn
-------
- Additive thuần: không ALTER/UPDATE row hiện có.
- Backup DB bằng sqlite3 backup API.
- `--stats`/`--dry-run` không ghi gì.
- Verify: cột tồn tại, đúng số dòng, `key_norm` KHÔNG đổi, số term riêng = 1.

Usage:
    python -X utf8 scripts/t208_lexicon_altkey_migration.py --stats
    python -X utf8 scripts/t208_lexicon_altkey_migration.py --dry-run
    python -X utf8 scripts/t208_lexicon_altkey_migration.py --apply
    python -X utf8 scripts/t208_lexicon_altkey_migration.py --verify
    python -X utf8 scripts/t208_lexicon_altkey_migration.py --revert
"""
import argparse
import datetime
import io
import os
import sqlite3
import sys
from collections import defaultdict

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

COL = 'key_norm_alt'
IDX = 'idx_lexicon_key_norm_alt'


def connect(path, ro=False):
    if ro:
        con = sqlite3.connect('file:%s?mode=ro' % path.replace('\\', '/'),
                              uri=True)
    else:
        con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def norm_fn():
    """Lấy đúng normalize_text() từ app.py bằng AST (không import Flask app)."""
    import sys as _s
    _s.path.insert(0, os.path.join(DAOANH, 'scripts'))
    import t207_fix_db_mojibake as T
    return T.load_normalize_text()


def has_col(con, col):
    return any(r['name'] == col for r in con.execute(
        'PRAGMA table_info(lexicon)'))


def build_plan(con, norm):
    """Tính kế hoạch (chỉ đọc)."""
    rows = con.execute('SELECT id, term, key_norm FROM lexicon '
                       'WHERE key_norm IS NOT NULL').fetchall()
    alt_terms = defaultdict(set)
    for r in rows:
        alt_terms[norm(r['term'] or '')].add(r['term'] or '')

    # key đã bị chiếm bởi row KHÔNG thuộc nhóm sửa (lớp chặn 2)
    grp = [r for r in rows if norm(r['term'] or '') != r['key_norm']]
    grp_ids = {r['id'] for r in grp}
    taken = {r['key_norm'] for r in rows if r['id'] not in grp_ids}

    plan, skip_amb, skip_taken = [], 0, 0
    for r in rows:
        alt = norm(r['term'] or '')
        if not alt:
            continue
        if norm(r['term'] or '') == r['key_norm']:
            continue                      # đã tìm được bằng khoá hiện tại
        if len(alt_terms[alt]) != 1:     # lớp 1
            skip_amb += 1
            continue
        if alt in taken:                 # lớp 2
            skip_taken += 1
            continue
        plan.append((r['id'], alt))
    return {'plan': plan, 'skip_amb': skip_amb, 'skip_taken': skip_taken,
            'total_rows': len(rows), 'grp': len(grp_ids)}


def print_plan(plan):
    print('\n--- KẾ HOẠCH (chưa ghi gì) ---')
    print('  lexicon có key_norm      : %d row' % plan['total_rows'])
    print('  nhóm hiện tra cứu HỎNG   : %d row' % plan['grp'])
    print('  THÊM key_norm_alt (an toàn): %d row' % len(plan['plan']))
    print('  bỏ qua — mơ rồng (Lớp 1) : %d row' % plan['skip_amb'])
    print('  bỏ qua — khoá đã bị chiếm : %d row' % plan['skip_taken'])
    print('  key_norm HIỆN TẠI: KHÔNG bị đụng tới.')


def do_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BACKUP_DIR, 'lineage_t208_%s.db' % ts)
    src = sqlite3.connect('file:%s?mode=ro' % DB_PATH.replace('\\', '/'), uri=True)
    out = sqlite3.connect(dst)
    src.backup(out)
    out.close()
    src.close()
    return dst


def apply(con, plan):
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=30000')
    cur = con.cursor()
    try:
        cur.execute('BEGIN IMMEDIATE')
        if not has_col(con, COL):
            cur.execute('ALTER TABLE lexicon ADD COLUMN "%s" TEXT' % COL)
        cur.execute('CREATE INDEX IF NOT EXISTS %s ON lexicon("%s")'
                    % (IDX, COL))
        cur.executemany('UPDATE lexicon SET "%s"=? WHERE id=?' % COL,
                        [(alt, rid) for rid, alt in plan['plan']])
        cur.execute('COMMIT')
    except Exception:
        cur.execute('ROLLBACK')
        raise
    return len(plan['plan'])


def verify(db_path=DB_PATH):
    norm = norm_fn()
    con = connect(db_path, ro=True)
    out, ok = [], True
    c_has = has_col(con, COL)
    ok &= c_has
    out.append(('cột `%s` tồn tại' % COL, c_has, ''))

    if not c_has:
        con.close()
        return False, out

    # kỳ vọng = chính kế hoạch tính lại (không hardcode con số)
    plan = build_plan(con, norm)
    exp = len(plan['plan'])
    n_alt = con.execute('SELECT count(*) FROM lexicon WHERE "%s" IS NOT NULL'
                        % COL).fetchone()[0]
    c1 = (n_alt == exp)
    ok &= c1
    out.append(('số row có khoá phụ = %d (đúng kế hoạch)' % exp, c1,
                '(got %d)' % n_alt))

    # nhóm app.py:1250 thực sự dùng (LENGTH(term) < 60)
    n60 = con.execute('SELECT count(*) FROM lexicon WHERE "%s" IS NOT NULL '
                      'AND LENGTH(term) < 60' % COL).fetchone()[0]
    out.append(('trong đó term < 60 ký tự (điều kiện app.py:1250) = %d' % n60,
                True, ''))

    # mỗi khoá phụ trỏ tới đúng 1 term
    n_multi = 0
    for r in con.execute('SELECT DISTINCT "%s" AS k FROM lexicon '
                         'WHERE "%s" IS NOT NULL' % (COL, COL)):
        n = con.execute('SELECT count(DISTINCT term) FROM lexicon '
                        'WHERE "%s" = ?' % COL, (r['k'],)).fetchone()[0]
        if n != 1:
            n_multi += 1
    c2 = (n_multi == 0)
    ok &= c2
    out.append(('mọi khoá phụ trỏ tới ĐÚNG 1 term (không thể trả sai)',
                c2, '(%d khoá vi phạm)' % n_multi))

    # khoá phụ KHÔNG được trùng key_norm của term khác (lớp chặn 2)
    n_clash = con.execute(
        'SELECT count(*) FROM lexicon a JOIN lexicon b '
        'ON a."%s" = b.key_norm AND a.term <> b.term '
        'WHERE a."%s" IS NOT NULL' % (COL, COL)).fetchone()[0]
    c3 = (n_clash == 0)
    ok &= c3
    out.append(('không khoá phụ nào trùng khoá hiện có của term KHÁC', c3,
                '(%d trường hợp)' % n_clash))

    # key_norm nguyên vẹn
    n_cur = con.execute('SELECT count(*) FROM lexicon '
                        'WHERE key_norm IS NOT NULL').fetchone()[0]
    out.append(('key_norm còn nguyên (%d row, không sửa dữ liệu)' % n_cur,
                n_cur == plan['total_rows'], ''))

    ic = con.execute('PRAGMA integrity_check').fetchone()[0]
    c4 = (ic == 'ok')
    ok &= c4
    out.append(('PRAGMA integrity_check = %r' % ic, c4, ''))
    con.close()
    return ok, out


def main():
    ap = argparse.ArgumentParser(
        description='T208 — thêm khoá tra cứu phụ cho lexicon (additive, revert = DROP)')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--revert', action='store_true')
    args = ap.parse_args()
    norm = norm_fn()

    print('=' * 78)
    print('T208 — THÊM KHOÁ TRA CỨU PHỤ (lexicon.key_norm_alt)')
    print('DB = %s' % DB_PATH)
    print('=' * 78)

    con = connect(DB_PATH, ro=True)
    plan = build_plan(con, norm)
    print_plan(plan)
    con.close()

    if args.verify:
        print()
        ok, out = verify()
        for label, good, extra in out:
            print('   [%s] %s%s' % ('OK ' if good else 'FAIL', label,
                                    ('  ' + extra) if extra else ''))
        print('\n   => %s' % ('PASS' if ok else 'FAIL'))
        return 0 if ok else 1

    if args.revert:
        con = connect(DB_PATH)
        if has_col(con, COL):
            con.execute('DROP INDEX IF EXISTS %s' % IDX)
            con.execute('ALTER TABLE lexicon DROP COLUMN "%s"' % COL)
            con.commit()
            print('[REVERT] đã DROP COLUMN %s (không mất dữ liệu)' % COL)
        else:
            print('[REVERT] cột %s không tồn tại — không cần làm gì' % COL)
        con.close()
        return 0

    if not (args.apply or args.dry_run):
        return 0
    if args.dry_run:
        print('\n  [DRY-RUN] chưa ghi. Dùng --apply.')
        return 0

    print()
    bkp = do_backup()
    print('[BACKUP] %s' % bkp)
    con = connect(DB_PATH)
    n = apply(con, plan)
    con.commit()
    con.close()
    print('[APPLY] thêm %s cho %d row (key_norm KHÔNG đổi)' % (COL, n))
    print('[REVERT] python -X utf8 scripts/t208_lexicon_altkey_migration.py --revert')
    print()
    ok, out = verify()
    for label, good, extra in out:
        print('   [%s] %s%s' % ('OK ' if good else 'FAIL', label,
                                ('  ' + extra) if extra else ''))
    print('\n   => %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())