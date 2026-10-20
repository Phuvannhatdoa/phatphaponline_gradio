# -*- coding: utf-8 -*-
"""probe_t207c.py — do bao nhieu row key_norm lech normalize_text() va vi sao.

Chon giua 2 chien luoc T207:
  A) chi the Ð -> Đ (giu quy uoc key_norm hien tai) — lookup van hong
  B) the Ð -> Đ + TINH LAI key_norm bang normalize_text() — lookup khoi phuc
"""
import os
import re
import sqlite3
import unicodedata
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'data', 'lineage.db')
ETH = '\u00d0'          # Ð sai
DSTROKE = '\u0110'      # Đ dung


def normalize_text(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('\u0111', 'd').replace(DSTROKE, 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()


def main():
    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    rows = con.execute('SELECT id, term, key_norm FROM lexicon '
                       'WHERE key_norm IS NOT NULL').fetchall()
    total = len(rows)
    mismatch = [(i, t, k) for i, t, k in rows if normalize_text(t) != k]
    print('=== 1) TONG QUAN ===')
    print('   lexicon co key_norm      : %d row' % total)
    print('   key_norm != norm(term)   : %d row (%.2f%%)'
          % (len(mismatch), 100.0 * len(mismatch) / total))

    print('\n=== 2) PHA TIEU LECH — do gi? ===')
    cnt = Counter()
    for _i, t, k in mismatch:
        if ETH in (t or ''):
            cnt['co Ð (ETH)'] += 1
        elif DSTROKE in (t or '') or '\u0111' in (t or ''):
            cnt['co Đ/đ (dung)'] += 1
        else:
            cnt['khac'] += 1
    for k2, v in cnt.most_common():
        print('   %-16s %6d row' % (k2, v))

    print('\n=== 3) RIENG NHOM CO Ð — sua xong co khop khong? ===')
    eth_rows = [(i, t, k) for i, t, k in rows if ETH in (t or '')]
    print('   row co Ð trong term      : %d' % len(eth_rows))
    ok_now = sum(1 for _i, t, k in eth_rows if normalize_text(t) == k)
    ok_after_replace = 0
    ok_after_recompute = 0
    for _i, t, k in eth_rows:
        fixed = t.replace(ETH, DSTROKE)
        if normalize_text(fixed) == k:            # chi the, khong tinh lai key
            ok_after_replace += 1
        if normalize_text(fixed) == normalize_text(fixed):  # tinh lai key
            ok_after_recompute += 1
    print('   khop key hien tai        : %d' % ok_now)
    print('   khop SAU khi chi the Ð   : %d   <-- A' % ok_after_replace)
    print('   se khop neu TINH LAI key : %d   <-- B (de nghia)' % len(eth_rows))

    print('\n=== 4) KIEM CHUNG ' + chr(66) + ': co row nao se BI doi key khong mong doi? ===')
    print('   (row khong co Ð nhung key_norm != norm(term) sau khi tinh lai)')
    risk = 0
    for i, t, k in mismatch:
        if ETH in (t or ''):
            continue
        risk += 1
    print('   %d row lech khong do Ð -> khong nen tinh lai (chi the co i)' % risk)

    print('\n=== 5) PHAN BO 162 ROW CO Ð theo bang nao (tac dong FTS) ===')
    cnt2 = Counter()
    for tbl, col in (('lexicon', 'term'), ('lexicon', 'definition')):
        n = con.execute('SELECT count(*) FROM "%s" WHERE "%s" LIKE ?'
                        % (tbl, col), ('%' + ETH + '%',)).fetchone()[0]
        cnt2['%s.%s' % (tbl, col)] = n
    for k2, v in sorted(cnt2.items()):
        print('   %-22s %5d row' % (k2, v))
    both = con.execute('SELECT count(*) FROM lexicon WHERE term LIKE ? '
                       'AND definition LIKE ?',
                       ('%' + ETH + '%', '%' + ETH + '%')).fetchone()[0]
    print('   row co Ð o ca term+definition: %d (can FTS delete+insert 1 lan)'
          % both)

    con.close()


if __name__ == '__main__':
    main()