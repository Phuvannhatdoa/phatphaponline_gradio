# -*- coding: utf-8 -*-
"""probe_t208c.py — do loiich cho phuong an AN TOAN: khoa du phu (khong ghi lai du lieu).

Tinh lai `key_norm` thi tao 241 key va cham voi term KHAC NGHIA
(Tứ Độ vs Tự Do, Tam Đức vs Tam Dục) ⇒ tra cuu tra sai. Phai BO.

Phuong an an toan: GIU NGUYEN key_norm, them khoa phu TINH LUC TRA CUU, va
CHI tra ket qua khi khoa do chi tro toi MOT term duy nhat (tranh tra sai).

Probe nay do bao nhieu row se MO dau tra duoc, va bao nhieu bi bo qua vi
moi rong.

Viet bang escape \\uXXXX de khong phu thuoc encoding cua shell.
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t207_fix_db_mojibake as T   # noqa: E402

DB = os.path.join(os.path.dirname(HERE), 'data', 'lineage.db')
DSTROKE = '\u0110'
D_LOW = '\u0111'


def main():
    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    norm = T.load_normalize_text()
    print('=' * 78)
    print('T208 PROBE C — loiich khoa phu (khong ghi lai du lieu)')
    print('=' * 78)

    rows = con.execute('SELECT id, term, key_norm FROM lexicon '
                       'WHERE key_norm IS NOT NULL').fetchall()
    by_id = {r[0]: r for r in rows}
    print('lexicon co key_norm: %d\n' % len(rows))

    # nhom T208 = key_norm != normalize_text(term), do đ/Đ, khong phai Ð
    grp = [r for r in rows
           if norm(r[1] or '') != r[2]
           and (DSTROKE in (r[1] or '') or D_LOW in (r[1] or ''))
           and T.ETH not in (r[1] or '')]
    print('nhom T208: %d row' % len(grp))

    # app.py:1226 co LENGTH(term) < 60
    short = [r for r in grp if len(r[1] or '') < 60]
    print('  trong do term < 60 ky tu (app.py:1226 moi tim): %d\n' % len(short))

    # ---- A) khoa phu co bao nhieu TERM KHAC NHAU tro toi? -----------
    print('A) MO RONG khoa phu — so term KHAC NHAU cung tro 1 key:')
    from collections import defaultdict
    alt = defaultdict(set)
    for r in rows:
        alt[norm(r[1] or '')].add(r[1] or '')
    uniq, ambig = 0, 0
    ambig_keys = []
    for r in short:
        k = norm(r[1] or '')
        if len(alt[k]) == 1:
            uniq += 1
        else:
            ambig += 1
            if len(ambig_keys) < 6:
                ambig_keys.append((k, sorted(alt[k])[:3]))
    print('   row se MO tra duoc (khoa chi 1 term) : %d' % uniq)
    print('   row se BI BO QUA   (khoa nhieu term) : %d' % ambig)
    print('   => %d / %d row nhom T208 tro lai tim duoc'
          % (uniq, len(short)))
    for k, terms in ambig_keys:
        print('      bo qua %-22r -> %r' % (k, terms))

    # ---- B) kiem tra: co bao nhieu term KHAC NGHIA cung khoa khong? ---
    print('\nB) KIEM TRA AN TOAN — cac cap key_phu == key_hien_tai')
    risk = 0
    examples = []
    for r in short:
        k = norm(r[1] or '')
        # row dang co key_norm = k (dung ngay khoa truy van hien tai)
        other = con.execute('SELECT DISTINCT term FROM lexicon '
                            'WHERE key_norm = ? AND term <> ?',
                            (k, r[1] or '')).fetchall()
        if other:
            risk += 1
            if len(examples) < 6:
                examples.append((k, r[1], [o[0] for o in other[:2]]))
    print('   row co key_phu trung key cua row KHAC (term khac nghia): %d' % risk)
    for k, mine, others in examples:
        print('      key %-22r' % k)
        print('         nhom T208 : %r' % mine[:46])
        print('         dang co   : %r' % [x[:40] for x in others])

    # ---- C) khoi luong ban ghi va do dai index ------------------------
    print('\nC) KHOI LUONG (neu them cot + index)')
    print('   them 1 cot TEXT vao lexicon (%d row)' % len(rows))
    print('   uoc luong ~ %d byte du lieu + index' % len(rows) * 60)
    print('   KHONG de xoa/gan lai du lieu nao -> revert chi can DROP COLUMN')

    # ---- D) thu tu uu tien hien tai cua app.py:1226 --------------------
    print('\nD) THU TU UU TIEN (phai giu nguyen de khong doi hien huong)')
    print('   ORDER BY priority ASC LIMIT 1   (nhom source cao hon thang)')
    con.close()


if __name__ == '__main__':
    main()