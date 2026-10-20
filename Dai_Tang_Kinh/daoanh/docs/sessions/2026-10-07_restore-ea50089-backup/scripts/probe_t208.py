# -*- coding: utf-8 -*-
"""probe_t208.py — do rui ro khi tinh lai `lexicon.key_norm` cho 53.686 row.

T207 chi sua 162 row co Ð. Con lai 53.686 row `key_norm` KHONG bang
`normalize_text(term)` ( lech vi chu `đ/Đ` ĐÚNG — key_norm giu dau, con
normalize_text bo dau).

Cau hoi then chot: neu tinh lai key_norm cho nhom do, co tao VA CHAM khoa khong?
Neu 2 term khac nhau collapse ve cung 1 key, truy van
  SELECT term FROM lexicon WHERE key_norm = ? ORDER BY priority LIMIT 1
se tra ve mot term SAI → huong nghich so voi muc tieu "khoi phuc tra cuu".

Viet bang escape \\uXXXX de khong phu thuoc encoding cua shell.
"""
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t207_fix_db_mojibake as T   # noqa: E402

DB = os.path.join(os.path.dirname(HERE), 'data', 'lineage.db')
DSTROKE = '\u0110'
D_LOW = '\u0111'


def main():
    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    con.row_factory = sqlite3.Row
    norm = T.load_normalize_text()

    rows = con.execute('SELECT id, term, key_norm, priority FROM lexicon '
                       'WHERE key_norm IS NOT NULL').fetchall()
    total = len(rows)
    print('=' * 78)
    print('T208 PROBE — rui ro tinh lai key_norm')
    print('=' * 78)
    print('lexicon co key_norm: %d row' % total)

    mismatch = [r for r in rows if norm(r['term']) != r['key_norm']]
    print('key_norm != normalize_text(term): %d row (%.1f%%)'
          % (len(mismatch), 100.0 * len(mismatch) / total))

    # ---- 1) phan loai nguyen nhan lech --------------------------------
    print('\n1) PHA TIEU LECH')
    c = Counter()
    for r in mismatch:
        t = r['term'] or ''
        if T.ETH in t:
            c['Ð (da xu ly o T207)'] += 1
        elif DSTROKE in t or D_LOW in t:
            c['đ/Đ DUNG — nhom T208'] += 1
        else:
            c['ly do khac'] += 1
    for k, v in c.most_common():
        print('   %-22s %7d row' % (k, v))

    grp = [r for r in mismatch
           if (DSTROKE in (r['term'] or '') or D_LOW in (r['term'] or ''))
           and T.ETH not in (r['term'] or '')]

    # ---- 2) VA CHAM: 2 term khac -> cung 1 key moi? --------------------
    print('\n2) VA CHAM — 2 term KHAC NHAU co collapse ve cung 1 key moi?')
    newkey = {}
    for r in grp:
        newkey.setdefault(norm(r['term']), []).append(r['id'])
    collide = {k: v for k, v in newkey.items() if len(v) > 1}
    n_affected = sum(len(v) for v in collide.values())
    print('   nhom T208               : %d row' % len(grp))
    print('   key moi bi TRUNG        : %d key' % len(collide))
    print('   row tham gia va cham    : %d' % n_affected)
    print('   => hanh vi tra cuu co DOI khong: %s'
          % ('CO' if collide else 'KHONG'))
    for k, v in list(collide.items())[:5]:
        terms = [x['term'] for x in grp if x['id'] in v][:3]
        print('      %-30r <- %r' % (k, terms))

    # ---- 3) VA CHAM voi row NGOAI nhom (da co key dung) ---------------
    print('\n3) VA CHAM voi row NGOAI nhom (key hien tai da khop)')
    out_map = {}
    for r in rows:
        if r in grp:
            continue
        out_map.setdefault(r['key_norm'], []).append(r['id'])
    cross = [k for k in newkey if k in out_map]
    print('   key moi cua nhom T208 da ton tai o row ngoai nhom: %d' % len(cross))
    for k in cross[:5]:
        terms = [x['term'] for x in grp if norm(x['term']) == k][:2]
        others = [x['term'] for x in rows
                  if x['key_norm'] == k and x not in grp][:2]
        print('      %-26r' % k)
        print('         nhom T208 se la : %r' % terms)
        print('         row dang co     : %r' % others)

    # ---- 4) do loi kiem tra: bao nhieu row se KHUOC trai nhan them -----
    print('\n4) LOI KIEM TRA — app.py:1226 dung LENGTH(term) < 60')
    grp_short = [r for r in grp if len(r['term'] or '') < 60]
    print('   row nhom T208 co term < 60 ky tu: %d / %d' % (len(grp_short),
                                                            len(grp)))
    print('   (chi nhom nay la nhung row thuc su duoc app.py tim thay)')

    # ---- 5) do loi duoi day 30 ----------------------------------------
    print('\n5) SO LUONG DUOI DAY 30 / DO DAI TRUONG')
    lb = [len(r['term'] or '') for r in grp]
    lb.sort()
    print('   term < 30 ky tu : %d' % sum(1 for x in lb if x < 30))
    print('   term 30-59      : %d' % sum(1 for x in lb if 30 <= x < 60))
    print('   term >= 60      : %d (khong bao gio duoc app.py:1226 tim)'
          % sum(1 for x in lb if x >= 60))

    # ---- 6) mau 8 row de admin doi chieu ------------------------------
    print('\n6) MAU 8 ROW (truoc / sau)')
    for r in grp[:8]:
        print('   term     = %r' % r['term'][:56])
        print('      key cu = %r' % (r['key_norm'] or '')[:56])
        print('      key moi= %r' % norm(r['term'])[:56])

    # ---- 7) kiem tra co bao nhieu key moi RONG khong? ------------------
    print('\n7) key moi rong (normalize_text tra ve "")')
    empty = [r for r in grp if not norm(r['term'])]
    print('   %d row — neu >0 thi key_norm="" se pha truy van' % len(empty))
    for r in empty[:3]:
        print('      term=%r' % (r['term'] or '')[:60])

    con.close()


if __name__ == '__main__':
    main()