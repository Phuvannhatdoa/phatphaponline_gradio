# -*- coding: utf-8 -*-
"""probe_t208b.py — tim normalizer CU (legacy) ma key_norm hien tai su dung.

Ket qua probe_t208.py: tinh lai key_norm bang normalize_text() se TAO 241 key
va cham voi term KHAC NGHIA (Tứ Độ vs Tự Do, Tam Đức vs Tam Dục) ⇒ tra cuu tra
sai ⇒ phuong an do phai BO.

Huong khac: GIU NGUYEN du lieu, sua o CHI O TIM KIEM — thu nhieu bien the khoa
va fallback. De lam duoc phai biet normalizer cu tao ra key_norm hien tai.

Gia thuyet: legacy = lowercase + bo dau, NHUNG KHONG map đ/Đ -> d.
Vi du term 'Đai Đức' -> key 'Đai Đuc' (giu Đ, bo ạ và ứ).

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


def strip_mn(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def legacy_a(s):
    """Gia thuyet: bo dau + lower, KHONG map đ/Đ."""
    return re.sub(r'\s+', ' ', strip_mn(s).lower()).strip()


def legacy_b(s):
    """Gia thuyet: bo dau + lower + map đ/Đ -> d."""
    return re.sub(r'\s+', ' ', strip_mn(s).lower().replace(D_LOW, 'd')
                  .replace(DSTROKE, 'd')).strip()


def main():
    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    con.row_factory = sqlite3.Row

    rows = con.execute('SELECT term, key_norm FROM lexicon '
                       'WHERE key_norm IS NOT NULL').fetchall()
    print('=' * 78)
    print('T208 PROBE B — tim normalizer CU')
    print('=' * 78)
    print('mau: %d row\n' % len(rows))

    n = len(rows)
    hit_a = sum(1 for r in rows if legacy_a(r['term'] or '') == r['key_norm'])
    hit_b = sum(1 for r in rows if legacy_b(r['term'] or '') == r['key_norm'])
    norm = T.load_normalize_text()
    hit_n = sum(1 for r in rows if norm(r['term'] or '') == r['key_norm'])
    print('KHOA KHOI HANH TRONG DB:')
    print('   normalize_text() (bo dau + đ->d)      : %6d / %d (%.1f%%)'
          % (hit_n, n, 100.0 * hit_n / n))
    print('   legacy_a (bo dau, GIU đ/Đ)            : %6d / %d (%.1f%%)'
          % (hit_a, n, 100.0 * hit_a / n))
    print('   legacy_b (bo dau + đ->d)               : %6d / %d (%.1f%%)'
          % (hit_b, n, 100.0 * hit_b / n))

    # key_norm dang dung bo dau chuc nhiem gi?
    with_dau = sum(1 for r in rows
                   if re.search(r'[\u00e0-\u01b0]', r['key_norm'] or ''))
    print('\nkey_norm chua ky tu Latin-Extended (dau): %d row' % with_dau)

    print('\n=== VOI 53.384 row nhom T208 (lech do đ/Đ) ===')
    grp = [r for r in rows
           if norm(r['term'] or '') != r['key_norm']
           and (DSTROKE in (r['term'] or '') or D_LOW in (r['term'] or ''))
           and T.ETH not in (r['term'] or '')]
    m = len(grp)
    ga = sum(1 for r in grp if legacy_a(r['term'] or '') == r['key_norm'])
    gn = sum(1 for r in grp if norm(r['term'] or '') == r['key_norm'])
    print('   so nhom              : %d' % m)
    print('   khop legacy_a         : %d (%.1f%%)' % (ga, 100.0 * ga / m))
    print('   khop normalize_text() : %d' % gn)
    print('\n   12 MAU khop/khong khop:')
    for r in grp[:12]:
        ok = 'DUNG ' if legacy_a(r['term'] or '') == r['key_norm'] else 'SAI  '
        print('   %s term=%-46r' % (ok, (r['term'] or '')[:44]))
        print('        key cu =%r' % (r['key_norm'] or '')[:50])
        print('        legacy =%r' % legacy_a(r['term'] or '')[:50])

    # neu legacy_a dung: fallback co an toan khong? (va cham)
    print('\n=== AN TOAN: fallback 2 khoa co tao ra nham khong? ===')
    # khoa moi cua nhom T208 (legacy_a) co trung voi nhau?
    idx = {}
    for r in grp:
        idx.setdefault(legacy_a(r['term'] or ''), []).append(r['id'])
    coll = {k: v for k, v in idx.items() if len(v) > 1}
    print('   nhom T208: %d key moi, trong do %d key bi trung'
          % (len(idx), len(coll)))
    # co key moi nao trung voi key cua row NGOAI nhom?
    outside = {}
    for r in rows:
        if r in grp:
            continue
        outside.setdefault(r['key_norm'], []).append(r['id'])
    cross = [k for k in idx if k in outside]
    print('   key moi trung voi row ngoai nhom: %d' % len(cross))
    for k in cross[:6]:
        t_new = [x['term'] for x in grp if legacy_a(x['term'] or '') == k][:2]
        t_old = [x['term'] for x in rows
                 if x['key_norm'] == k and x not in grp][:2]
        print('      %-24r' % k)
        print('         nhom T208 : %r' % t_new)
        print('         dang co   : %r' % t_old)

    con.close()


if __name__ == '__main__':
    main()