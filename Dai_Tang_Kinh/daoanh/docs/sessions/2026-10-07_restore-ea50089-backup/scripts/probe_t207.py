# -*- coding: utf-8 -*-
"""probe_t207.py — do bac mojibake U+00D0 trong DB co lam hong KEY tra cuu khong.

Viet bang escape \\uXXXX de khong phu thuoc encoding cua shell.
"""
import os
import re
import sqlite3
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'data', 'lineage.db')

ETH = '\u00d0'        # Ð  LATIN CAPITAL LETTER ETH   (sai)
ETH_LC = '\u00f0'     # ð  LATIN SMALL LETTER ETH     (sau .lower())
DSTROKE = '\u0110'    # Đ  LATIN CAPITAL LETTER D WITH STROKE (dung)


def normalize_text(s):
    """Sai y het app.py:96 normalize_text()."""
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('\u0111', 'd').replace(DSTROKE, 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()


def main():
    print('=' * 78)
    print('T207 PROBE — mojibake U+00D0 lam hong key tra cuu?')
    print('=' * 78)

    print('\n1) DE PHAY KHAC BIET giua Ð (ETH) va Đ (D WITH STROKE)?')
    for ch, name in ((DSTROKE, 'Ð Đ'), (ETH, 'Ð Ð')):
        print('   U+%04X %-3s decomposition=%-8r  NFD=%r  lower=%r'
              % (ord(ch), name, unicodedata.decomposition(ch),
                 unicodedata.normalize('NFD', ch), ch.lower()))

    print('\n2) normalize_text() — so sanh khoa tao ra')
    for pair in (('Đoạn lạc', 'Ðoạn lạc'),
                 ('Đại thừa', 'Ðại thừa'),
                 ('Bồ Đề', 'Bồ Ðề'),
                 ('Đại Bi', 'Ðại Bi')):
        good, bad = pair
        ng, nb = normalize_text(good), normalize_text(bad)
        flag = 'KHAC NHAU' if ng != nb else 'trung khop'
        print('   %-12s -> %-22r' % (good, ng))
        print('   %-12s -> %-22r  %s' % (bad, nb, flag))

    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)

    print('\n3) DB co khoa chua "ð" (eth thuong) — dau hieu key bi hong?')
    for t, c in (('lexicon', 'normalized'), ('lexicon', 'key_norm'),
                 ('keyword_map', 'keyword'), ('keyword_map', 'value')):
        n = con.execute('SELECT count(*) FROM "%s" WHERE "%s" LIKE ?'
                        % (t, c), ('%' + ETH_LC + '%',)).fetchone()[0]
        print('   %-14s %-12s %5d row chua ð' % (t, c, n))

    print('\n4) lexicon row chua Ð — normalized/key_norm co chua ð?')
    rows = con.execute(
        'SELECT id, term, normalized, key_norm FROM lexicon '
        'WHERE term LIKE ? LIMIT 3', ('%' + ETH + '%',)).fetchall()
    for rid, term, norm, key in rows:
        print('   id=%-6s term=%r' % (rid, term[:30]))
        print('           normalized=%r' % (norm or '')[:30])
        print('           key_norm   =%r' % (key or '')[:30])

    print('\n5) TRA CUU THAT — tim bang key chuan, con row nao khop?')
    for term in ('Đoạn lạc', 'Đại Bi'):
        key = normalize_text(term)
        n = con.execute('SELECT count(*) FROM lexicon WHERE key_norm = ?',
                        (key,)).fetchone()[0]
        print('   %-12s -> key_norm=%-16r  khop %d row'
              % (term, key, n))
        bad = con.execute('SELECT count(*) FROM lexicon WHERE term LIKE ? '
                          'AND key_norm = ?', ('%' + ETH + '%', key)).fetchone()[0]
        print('        (trong do %d row co Ð trong term)' % bad)

    print('\n6) UOC LUONG THOI GIAN: FTS5 rebuild tren lexicon (bao nhieu dong?)')
    n = con.execute('SELECT count(*) FROM lexicon').fetchone()[0]
    print('   lexicon rows = %d' % n)
    print('   lexicon_fts rows = %d (external content, 0 trigger)'
          % con.execute('SELECT count(*) FROM lexicon_fts').fetchone()[0])

    con.close()


if __name__ == '__main__':
    main()