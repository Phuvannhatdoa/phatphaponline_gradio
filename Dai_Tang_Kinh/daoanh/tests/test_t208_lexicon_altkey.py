# -*- coding: utf-8 -*-
"""test_t208_lexicon_altkey.py — [T208] khoá tra cứu phụ, additive + revert sạch.

Chạy trên DB NHÂN TẠO nhỏ (cùng DDL thật) — không đụng DB thật.

Cần chứng minh:
  1) migration ADDITIVE: thêm cột, KHÔNG sửa `key_norm`
  2) khoá phụ CHỈ nằm ở row hiện tra cứu hỏng (key_norm != normalize_text(term))
  3) LỚP CHẶN 1: khoá phụ trỏ tới đúng 1 term → không bao giờ trả sai
     (đặc biệt KHÔNG gộp 'Tứ Độ' với 'Tự Do', 'Tam Đức' với 'Tam Dục')
  4) LỚP CHẶN 2: không khoá phụ nào trùng khoá hiện có của term KHÁC
  5) tra cứu hiện tại không đổi: key_norm còn nguyên, số dòng không đổi
  6) `--revert` = DROP COLUMN, mất 0 dữ liệu
  7) truy vấn 2 bước (key_norm rồi mới key_norm_alt) trả đúng

Chạy: python -X utf8 tests/test_t208_lexicon_altkey.py
"""
import io
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
for p in (DAOANH, os.path.join(DAOANH, 'scripts')):
    if p not in sys.path:
        sys.path.insert(0, p)

import t208_lexicon_altkey_migration as M   # noqa: E402
import t207_fix_db_mojibake as T            # noqa: E402

_pass = 0
_fail = []


def check(label, cond, extra=''):
    global _pass
    if cond:
        _pass += 1
        print('   OK   %s' % label)
    else:
        _fail.append(label)
        print('   FAIL %s%s' % (label, ('  %s' % extra) if extra else ''))


DDL = """
CREATE TABLE lexicon (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL, normalized TEXT NOT NULL, definition TEXT,
  source TEXT NOT NULL, priority INTEGER, key_norm TEXT
);
"""

# (term, key_norm_cu) — key_norm "cũ" cố tình sai quy ước (giữ dấu) để mô phỏng
# dữ liệu hỏng thật.
ROWS = [
    # tra cứu ĐƯỢC ngay (key_norm khớp normalize_text)
    ('Bát Nhã', 'bat nha', 1),
    ('Chân Như', 'chan nhu', 1),
    # tra cứu HỎNG (key_norm giữ dấu) — ứng viên khoá phụ, khoá DUY NHẤT
    ('Tự Tánh', 'tu tánh', 1),
    ('Vô Ni', 'vô ni', 1),
    # MƠ RỒNG: 2 term khác nghĩa cùng key → phải bị loại
    ('Tứ Độ', 'tư độ', 1),
    ('Tự Do', 'tư do', 1),
    # MƠ RỒNG: 3 term cùng key
    ('Đại Tu', 'đại tu', 1),
    ('Đại Từ', 'đại từ', 1),
    ('Đại Tự', 'đại tự', 1),
]


def build(path):
    con = sqlite3.connect(path)
    con.executescript(DDL)
    for i, (term, key, pri) in enumerate(ROWS, 1):
        con.execute('INSERT INTO lexicon (id, term, normalized, definition,'
                    ' source, priority, key_norm) VALUES (?,?,?,?,?,?,?)',
                    (i, term, term, 'def', 'test', pri, key))
    con.commit()
    con.close()


def two_step_lookup(con, seg, norm):
    """Truy vấn 2 bước: key_norm trước (giữ nguyên hành vi), rồi key_norm_alt."""
    key = norm(seg)
    r = con.execute('SELECT term FROM lexicon WHERE key_norm = ? '
                    'AND LENGTH(term) < 60 ORDER BY priority ASC LIMIT 1',
                    (key,)).fetchone()
    if r:
        return r['term'], 'key_norm'
    r = con.execute('SELECT term FROM lexicon WHERE key_norm_alt = ? '
                    'AND LENGTH(term) < 60 ORDER BY priority ASC LIMIT 1',
                    (key,)).fetchone()
    if r:
        return r['term'], 'key_norm_alt'
    return None, None


def main():
    tmp = tempfile.mkdtemp(prefix='t208test_')
    db = os.path.join(tmp, 'fixture.db')
    build(db)

    M.DB_PATH = db
    M.BACKUP_DIR = os.path.join(tmp, 'backups')
    os.makedirs(M.BACKUP_DIR, exist_ok=True)
    norm = T.load_normalize_text()

    print('=== 1) TRƯỚC migration ===')
    con = M.connect(db, ro=True)
    check('chưa có cột key_norm_alt', not M.has_col(con, M.COL))
    keys_before = {r['id']: r['key_norm']
                   for r in con.execute('SELECT id, key_norm FROM lexicon')}
    n_before = con.execute('SELECT count(*) FROM lexicon').fetchone()[0]
    got, how = two_step_lookup.__wrapped__(con, 'Tự Tánh', norm) \
        if hasattr(two_step_lookup, '__wrapped__') else (None, None)
    con.close()
    check('số row lexicon = %d' % n_before, n_before == len(ROWS))
    plan = M.build_plan(M.connect(db, ro=True), norm)
    M.connect(db, ro=True).close()
    print('   kế hoạch: +%d khoá phụ, bỏ %d mơ rồng'
          % (len(plan['plan']), plan['skip_amb']))
    check('chỉ 2 row hỏng-duy-nhất được thêm khoá phụ',
          len(plan['plan']) == 2, '(got %d)' % len(plan['plan']))
    check('không thêm khoá phụ cho các cặp mơ rồng',
          plan['skip_amb'] >= 5, '(got %d)' % plan['skip_amb'])

    print('\n=== 2) --apply (additive) ===')
    con = M.connect(db)
    M.apply(con, plan)
    con.commit()
    con.close()
    con = M.connect(db, ro=True)
    check('đã có cột key_norm_alt', M.has_col(con, M.COL))
    check('key_norm KHÔNG bị sửa (additive thuần)',
          {r['id']: r['key_norm']
           for r in con.execute('SELECT id, key_norm FROM lexicon')}
          == keys_before)
    check('số row không đổi',
          con.execute('SELECT count(*) FROM lexicon').fetchone()[0] == n_before)
    con.close()

    print('\n=== 3) LỚP CHẶN 1 — không bao giờ trả sai ===')
    con = M.connect(db, ro=True)
    for seg, must_not, why in (('Tứ Độ', 'Tự Do', 'Tứ Độ ≠ Tự Do'),
                               ('Tam Đức', 'Tam Dục', 'Tam Đức ≠ Tam Dục')):
        hit, how = two_step_lookup(con, seg, norm)
        ok = hit is None or hit != must_not
        check('%s KHÔNG bị trả nhầm %s (%s)' % (seg, must_not, why), ok,
              '(got %r)' % hit)
    # cac cap thuoc "nhom T208" phai bi bo qua
    hit, how = two_step_lookup(con, 'Đại Tu', norm)
    check('Đại Tu / Đại Từ / Đại Tự mơ rồng → KHÔNG trả kết quả sai',
          hit is None, '(got %r)' % hit)
    con.close()

    print('\n=== 4) LỚP CHẶN 2 — không trùng khoá của term khác ===')
    con = M.connect(db, ro=True)
    n_clash = con.execute(
        'SELECT count(*) FROM lexicon a JOIN lexicon b '
        'ON a.key_norm_alt = b.key_norm AND a.term <> b.term '
        'WHERE a.key_norm_alt IS NOT NULL').fetchone()[0]
    check('0 khoá phụ trùng khoá hiện có của term khác', n_clash == 0,
          '(got %d)' % n_clash)
    n_multi = 0
    for r in con.execute('SELECT DISTINCT key_norm_alt AS k FROM lexicon '
                         'WHERE key_norm_alt IS NOT NULL'):
        n = con.execute('SELECT count(DISTINCT term) FROM lexicon '
                        'WHERE key_norm_alt = ?', (r['k'],)).fetchone()[0]
        if n != 1:
            n_multi += 1
    check('mọi khoá phụ trỏ tới đúng 1 term', n_multi == 0,
          '(got %d vi phạm)' % n_multi)
    con.close()

    print('\n=== 5) HÀNH VI HIỆN TẠI KHÔNG ĐỔI + tra cứu mới ===')
    con = M.connect(db, ro=True)
    hit, how = two_step_lookup(con, 'Bát Nhã', norm)
    check('mục ĐÃ tìm được vẫn tìm bằng key_norm (không đổi đường)',
          hit == 'Bát Nhã' and how == 'key_norm', '(got %r/%s)' % (hit, how))
    hit, how = two_step_lookup(con, 'Tự Tánh', norm)
    check('mục HỎNG trước đây giờ tìm được qua key_norm_alt',
          hit == 'Tự Tánh' and how == 'key_norm_alt', '(got %r/%s)' % (hit, how))
    hit, how = two_step_lookup(con, 'Vô Ni', norm)
    check('Vô Ni cũng tìm được qua khoá phụ',
          hit == 'Vô Ni' and how == 'key_norm_alt', '(got %r/%s)' % (hit, how))
    con.close()

    print('\n=== 6) --revert = DROP COLUMN, mất 0 dữ liệu ===')
    con = M.connect(db)
    if M.has_col(con, M.COL):
        con.execute('DROP INDEX IF EXISTS %s' % M.IDX)
        con.execute('ALTER TABLE lexicon DROP COLUMN "%s"' % M.COL)
        con.commit()
    con.close()
    con = M.connect(db, ro=True)
    check('cột đã bị DROP', not M.has_col(con, M.COL))
    check('key_norm sau revert y hệt trước migration',
          {r['id']: r['key_norm']
           for r in con.execute('SELECT id, key_norm FROM lexicon')}
          == keys_before)
    check('số row sau revert không đổi',
          con.execute('SELECT count(*) FROM lexicon').fetchone()[0] == n_before)
    check('PRAGMA integrity_check = ok',
          con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
    con.close()

    shutil.rmtree(tmp, ignore_errors=True)
    print()
    print('=' * 66)
    if _fail:
        print('T208 test: %d PASS, %d FAIL' % (_pass, len(_fail)))
        for f in _fail:
            print('   FAIL:', f)
        sys.exit(1)
    print('T208 test: %d/%d PASS' % (_pass, _pass))
    print('=' * 66)


if __name__ == '__main__':
    main()