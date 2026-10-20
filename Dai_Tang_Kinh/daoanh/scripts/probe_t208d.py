# -*- coding: utf-8 -*-
"""probe_t208d.py — so AN TOAN thuc su, voi CA 2 lop chan.

probe_t208c cho thay 2 loai rui ro:
  A) 2.194 row: nhieu term KHAC NHAU cung tro 1 key (Đại Tu / Đại Từ / Đại Tự)
  B)   545 row: key phu TRUNG key cua row KHAC, term KHAC NGHIA
                (Định vs Dĩnh, Tứ Độ vs Tự Do, Tam Đức vs Tam Dục, ...)
=> khong duoc tra ve mot term tu khoa phu khi gap ca 2 dieu kien.

Lop 1: khoa phu chi tro toi DUNG MOT term trong toan lexicon.
Lop 2: khoa phu CHUA bi term nao khop (ke ca row nhom T208) dung san.
Dat ca 2 => an toàn.

Viet bang escape \\uXXXX de khong phu thuoc encoding cua shell.
"""
import os
import sqlite3
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t207_fix_db_mojibake as T   # noqa: E402

DB = os.path.join(os.path.dirname(HERE), 'data', 'lineage.db')
DSTROKE = '\u0110'
D_LOW = '\u0111'


def main():
    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    norm = T.load_normalize_text()
    rows = con.execute('SELECT id, term, key_norm FROM lexicon '
                       'WHERE key_norm IS NOT NULL').fetchall()
    grp_ids = {r[0] for r in rows
               if norm(r[1] or '') != r[2]
               and (DSTROKE in (r[1] or '') or D_LOW in (r[1] or ''))
               and T.ETH not in (r[1] or '')}
    print('=' * 78)
    print('T208 PROBE D — so AN TOAN that su (2 lop chan)')
    print('=' * 78)
    print('nhom T208: %d row' % len(grp_ids))

    # khoa phu -> tap term (toan lexicon)
    alt_terms = defaultdict(set)
    for r in rows:
        alt_terms[norm(r[1] or '')].add(r[1] or '')

    # key da co san (row NGOAI nhom)
    taken = {r[2] for r in rows if r[0] not in grp_ids}

    cands = [r for r in rows
             if r[0] in grp_ids and len(r[1] or '') < 60]
    print('ung vien (term < 60 nhu app.py:1226): %d\n' % len(cands))

    l1_ok, l2_ok, both = 0, 0, 0
    ex_l1, ex_l2 = [], []
    for r in cands:
        k = norm(r[1] or '')
        ok1 = len(alt_terms[k]) == 1
        ok2 = k not in taken
        if ok1:
            l1_ok += 1
            if not ok2 and len(ex_l2) < 4:
                ex_l2.append((k, r[1],
                              sorted({x[1] for x in rows if x[2] == k})[:2]))
        else:
            if len(ex_l1) < 4:
                ex_l1.append((k, sorted(alt_terms[k])[:3]))
        if ok2:
            l2_ok += 1
        if ok1 and ok2:
            both += 1
    print('Lop 1 (khoa chi 1 term)          : %d' % l1_ok)
    print('Lop 2 (khoa chua bi dung)         : %d' % l2_ok)
    print('=> AN TOAN (ca 2 lop)             : %d' % both)
    print('=> BI BO QUA                       : %d' % (len(cands) - both))
    print('   moc tang so dong tra duoc       : +%d / %d ung vien'
          % (both, len(cands)))
    print('\nVi du bi bo qua o Lop 1 (nhieu term cung key):')
    for k, terms in ex_l1:
        print('   %-22r -> %r' % (k, terms))
    print('\nVi du bi loai o Lop 2 (key da co san, KHAC NGHIA):')
    for k, mine, others in ex_l2:
        print('   %-22r nhom=%r  dang_co=%r' % (k, mine[:26], others))

    # thu tu uu tien: nut co nhom nao bi "b qua co y" hon khong?
    print('\nBAO CAO CHO ADMIN:')
    print('  * 19.481 dong se MO tra duoc — nhung chi khi them khoa phu.')
    print('  * %d dong van BI BO QUA (moi rong) — dung hon la tra sai.' % (len(cands) - both))
    print('  * KHONG ghi lai du lieu: them cot moi, key_norm giu nguyen.')
    print('  * revert = DROP COLUMN (khong ton du lieu gi).')
    con.close()


if __name__ == '__main__':
    main()