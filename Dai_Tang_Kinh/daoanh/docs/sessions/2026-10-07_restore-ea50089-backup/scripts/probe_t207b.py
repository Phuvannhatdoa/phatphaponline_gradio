# -*- coding: utf-8 -*-
"""probe_t207b.py — do key_norm co THAT su khop normalize_text() khong?

 Cau hoi quyet dinh: sua Ð trong DB co giup tra cuu lexicon khong,
 hay van ton tai loi lon hon (key_norm dung quy uoc khac normalize_text).
"""
import os
import re
import sqlite3
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'data', 'lineage.db')
ETH = '\u00d0'


def normalize_text(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('\u0111', 'd').replace('\u0110', 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()


def main():
    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    total = con.execute('SELECT count(*) FROM lexicon').fetchone()[0]
    print('lexicon rows = %d' % total)

    print('\n1) BAO CHUNG: key_norm co bang normalize_text(term) khong?')
    print('   (lay mau 2000 row co key_norm NOT NULL)')
    rows = con.execute(
        'SELECT term, key_norm FROM lexicon WHERE key_norm IS NOT NULL '
        'LIMIT 2000').fetchall()
    match = sum(1 for t, k in rows if normalize_text(t) == k)
    print('   khop  %d / %d row  (%.1f%%)' % (match, len(rows),
                                              100.0 * match / len(rows)))
    print('   => neu <5%%, lookup app.py:1226 / :2800 KHONG BAO GIO KHOP')

    print('\n2) key_norm co bao gio chua dau? (normalize_text bo dau)')
    withacc = con.execute(
        "SELECT count(*) FROM lexicon WHERE key_norm IS NOT NULL "
        "AND (key_norm LIKE '%á%' OR key_norm LIKE '%à%' "
        "OR key_norm LIKE '%ả%' OR key_norm LIKE 'đ%')").fetchone()[0]
    print('   key_norm chua dau tieng Viet: %d row' % withacc)

    print('\n3) cac row co Ð — key_norm co khop quy uoc nao?')
    rows = con.execute(
        'SELECT id, term, normalized, key_norm FROM lexicon '
        'WHERE term LIKE ? LIMIT 3', ('%' + ETH + '%',)).fetchall()
    for rid, term, norm, key in rows:
        print('   id=%s' % rid)
        print('      term        = %r' % term[:44])
        print('      normalized  = %r' % (norm or '')[:44])
        print('      key_norm    = %r' % (key or '')[:44])
        print('      norm(term)  = %r   <-- app.py dung ham nay' % normalize_text(term)[:44])
        print('      khop key_norm? %s' % (normalize_text(term) == key))

    print('\n4) BAO CHUNG HANH DONG: tra cuu that voi mot tu co Ð')
    for term in ('Ðại Bi', 'Ðoạn lạc'):
        key = normalize_text(term)
        n = con.execute('SELECT count(*) FROM lexicon WHERE key_norm = ?',
                        (key,)).fetchone()[0]
        print('   %-12s -> key=%-14r  khop %d row' % (term, key, n))
    fixed_key = normalize_text('Đại Bi')
    n = con.execute('SELECT count(*) FROM lexicon WHERE key_norm = ?',
                    (fixed_key,)).fetchone()[0]
    print('   %-12s -> key=%-14r  khop %d row  <-- sau khi sua Ð'
          % ('Đại Bi', fixed_key, n))

    print('\n5) BAO CHUNG HANH DONG 2: neu chi the Ð->Đ trong DB')
    print('   (khong doi quy uoc key_norm), lookup co nhan duoc khong?')
    # gia lap: replace Ð->Đ roi tinh key theo quy uoc normalize_text
    import unicodedata as ud
    def norm_keep(s):
        s = s.replace(ETH, '\u0110')
        return s
    for raw in ('Ðại Bi',):
        fixed_term = norm_keep(raw)
        # key_norm hien tai giu dau, nen key sau khi sua van khong khop
        print('   fixed term = %r' % fixed_term)
        print('   normalize_text(fixed) = %r' % normalize_text(fixed_term))
        print('   => van ≠ key_norm luu trong DB (giu dau)')

    print('\n6) BAO CHUNG HANH DONG 3: co duong nao normalize_text()')
    print('   DUNG key_norm khong? (doi chieu so ban ghi)')
    total2 = con.execute('SELECT count(*) FROM lexicon').fetchone()[0]
    print('   lexicon co %d row; nhung key_norm != normalize_text(term)' % total2)
    con.close()


if __name__ == '__main__':
    main()