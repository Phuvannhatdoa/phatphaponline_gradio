# -*- coding: utf-8 -*-
"""test_t207_db_mojibake.py — [T207] sửa mojibake Ð trong DB + khôi phục tra cứu.

Chạy trên DB NHÂN TẠO nhỏ (cùng DDL thật) — không đụng DB thật, không cần copy 1.5 GB.

Cần chứng minh:
  1) `Ð` (U+00D0) biến mất hoàn toàn ở 20 cột văn bản + lexicon + FTS index
  2) `lexicon_fts` (FTS5 external-content) ĐỒNG BỘ — qua lệnh integrity-check
     rank=1, không chỉ đếm row
  3) `lexicon.key_norm` được TÍNH LẠI = `normalize_text(term)` (chiến lược B)
  4) Tra cứu chữ Đ khớp row SAU khi sửa, và HỎNG TRƯỚC khi sửa (bằng chứng A/B)
  5) Hán tự (CJK) không đổi
  6) Tổng row các bảng không đổi
  7) `PRAGMA integrity_check` = ok
  8) `--revert` khôi phục đúng từng ô
  9) Hàm `normalize_text()` lấy từ app.py bằng AST khớp đúng định nghĩa gốc

Chạy: python -X utf8 tests/test_t207_db_mojibake.py
"""
import io
import json
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

import t207_fix_db_mojibake as T   # noqa: E402

ETH = T.ETH
DSTROKE = T.DSTROKE

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


# ---------------------------------------------------------------------------
DDL = """
CREATE TABLE lexicon (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL,
  normalized TEXT NOT NULL,
  definition TEXT,
  source TEXT NOT NULL,
  priority INTEGER,
  entity_type TEXT,
  lang TEXT,
  created_at TEXT,
  key_norm TEXT
);
CREATE VIRTUAL TABLE lexicon_fts USING fts5(
  term, definition, content=lexicon, content_rowid=id
);
CREATE TABLE name_vi_map (id INTEGER PRIMARY KEY, name_vi TEXT,
  name_vi_final TEXT, bio_snippet TEXT);
CREATE TABLE entity_monks (id INTEGER PRIMARY KEY, name TEXT,
  definition TEXT);
CREATE TABLE entity_temples (id INTEGER PRIMARY KEY, name TEXT,
  definition TEXT);
CREATE TABLE entity_works (id INTEGER PRIMARY KEY, definition TEXT);
CREATE TABLE vn_person_authority (id TEXT PRIMARY KEY, name_vi TEXT,
  biographical_note_vi TEXT);
CREATE TABLE vn_person_relations (id TEXT PRIMARY KEY,
  target_label_vi TEXT);
CREATE TABLE person_bio_vi_draft (id TEXT PRIMARY KEY, bio_vi_draft TEXT);
CREATE TABLE keyword_map (id INTEGER PRIMARY KEY, keyword TEXT,
  value TEXT);
CREATE TABLE translation_exemplar (id INTEGER PRIMARY KEY, zh TEXT, vi TEXT);
"""

# (term, definition) — term có Ð, definition có thể có
ROWS = [
    ('* Chú Ðại Bi giang giai', 'Chu giai Ðai Bi cho nguoi hoc'),
    ('Ðoan lac, Ðoan kho', 'Hai khai niem ve mat on'),
    ('Bồ Ðề', 'Bo Ðe la cay giac nguyen'),
    ('Tam Quan Ðại Bi', 'Khong co Ð trong dong nay'),
    ('Tu Han Ðieu', 'Khong co Ð'),
]

OTHER_ROWS = {
    'name_vi_map': ['Cư Sĩ Ðề Hình', 'Cư Sĩ Ðề Hình', 'Bồ Ðề'],
    'entity_monks': ['Ðại sư Hoàng', 'Bồ Ðề'],
    'entity_temples': ['Chùa Ðại Bi'],
    'entity_works': ['Gia cương Ðại thừa'],
    'vn_person_authority': ['Cư Sĩ Ðề Hình'],
    'vn_person_relations': ['Thiền sư Ðam Nguyên Ứng Chân'],
    'person_bio_vi_draft': ['Ngài Ðại sư vô danh'],
    'keyword_map': ['Ðễ', 'Hòa thuận'],
    'translation_exemplar': ['Ðại thừa khởi tín luận', 'Theo tu dien'],
}


def build_fixture(path):
    con = sqlite3.connect(path)
    con.executescript(DDL)
    for i, (term, dfn) in enumerate(ROWS, 1):
        con.execute('INSERT INTO lexicon (id, term, normalized, definition, '
                    'source, priority, key_norm) VALUES (?,?,?,?,?,?,?)',
                    (i, term, term, dfn, 'test', 1, 'KHOA-SAI-' + str(i)))
    con.execute("INSERT INTO lexicon_fts(lexicon_fts) VALUES('rebuild')")
    con.execute('INSERT INTO name_vi_map VALUES (1, ?, ?, ?)',
                ('Cư Sĩ Ðề Hình', 'Cư Sĩ Ðề Hình', 'Ðoạn văn có Ð'))
    con.execute('INSERT INTO name_vi_map VALUES (2, ?, ?, ?)',
                ('Bồ Ðề', 'Bồ Ðề', 'Sao cho khong co Ð'))
    con.execute('INSERT INTO entity_monks VALUES (1, ?, ?)',
                ('Ðại sư Hoàng', 'Bia Ðại sư'))
    con.execute('INSERT INTO entity_monks VALUES (2, ?, ?)', ('Bồ Ðề', None))
    con.execute('INSERT INTO entity_temples VALUES (1, ?, ?)',
                ('Chùa Ðại Bi', 'Nội dung Ð'))
    con.execute('INSERT INTO entity_works VALUES (1, ?)',
                ('Gia cương Ðại thừa',))
    con.execute('INSERT INTO vn_person_authority VALUES (?, ?, ?)',
                ('A000001', 'Cư Sĩ Ðề Hình', 'Tiểu sử có Ð'))
    con.execute('INSERT INTO vn_person_relations VALUES (?, ?)',
                ('R1', 'Thiền sư Ðam Nguyên Ứng Chân'))
    con.execute('INSERT INTO person_bio_vi_draft VALUES (?, ?)',
                ('P1', 'Ngài Ðại sư vô danh'))
    con.execute('INSERT INTO keyword_map VALUES (1, ?, ?)',
                ('Ðễ', 'Hòa thuận, kính anh'))
    con.execute('INSERT INTO translation_exemplar VALUES (1, ?, ?)',
                ('Ðại thừa khởi tín luận', 'Ðại thừa khởi tín luận'))
    con.commit()
    con.close()


def count_eth(path):
    con = sqlite3.connect('file:%s?mode=ro' % path.replace('\\', '/'), uri=True)
    n = 0
    for tbl, col, _n2 in T.TEXT_COLUMNS:
        n += con.execute('SELECT count(*) FROM "%s" WHERE "%s" LIKE ?'
                         % (tbl, col), ('%' + ETH + '%',)).fetchone()[0]
    for col in ('term', 'definition', 'normalized', 'key_norm'):
        n += con.execute('SELECT count(*) FROM lexicon WHERE "%s" LIKE ?' % col,
                         ('%' + ETH + '%',)).fetchone()[0]
    n += con.execute('SELECT count(*) FROM lexicon_fts WHERE term LIKE ? '
                     'OR definition LIKE ?', ('%' + ETH + '%',) * 2).fetchone()[0]
    con.close()
    return n


def main():
    tmpdir = tempfile.mkdtemp(prefix='t207test_')
    db = os.path.join(tmpdir, 'fixture.db')
    bdir = os.path.join(tmpdir, 'backups')
    os.makedirs(bdir, exist_ok=True)
    build_fixture(db)

    norm = T.load_normalize_text()
    # chuyển script sang chạy trên fixture
    T.DB_PATH = db
    T.BACKUP_DIR = bdir
    T.APP_PY = os.path.join(DAOANH, 'app.py')

    print('=== 1) hàm normalize_text lấy từ app.py (AST) khớp bản gốc ===')
    import ast
    import re as _re
    import unicodedata
    src = io.open(T.APP_PY, encoding='utf-8', errors='replace').read()
    node = None
    for nd in ast.walk(ast.parse(src)):
        if isinstance(nd, ast.FunctionDef) and nd.name == 'normalize_text':
            node = nd
    check('app.py có hàm normalize_text()', node is not None)
    check('AST lấy đúng thân hàm (chứa .replace Đ)',
          '.replace(' in ast.get_source_segment(src, node) and 'Đ' in ast
          .get_source_segment(src, node))
    check('normalize_text("Đoạn lạc") == "doan lac"',
          norm('Đoạn lạc') == 'doan lac', '(got %r)' % norm('Đoạn lạc'))
    check('normalize_text("Ðoạn lạc") == "ðoan lac" (sai — đây là lỗi gốc)',
          norm('Ðoạn lạc') == 'ðoan lac', '(got %r)' % norm('Ðoạn lạc'))

    print()
    print('=== 2) TRƯỚC khi sửa ===')
    n_eth = count_eth(db)
    check('fixture có ký tự Ð', n_eth > 0, '(%d)' % n_eth)
    con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
    # chứng minh lookup hỏng TRƯỚC khi sửa
    term = ROWS[0][0].replace(ETH, DSTROKE)
    key = norm(term)
    before = con.execute('SELECT count(*) FROM lexicon WHERE key_norm = ?',
                         (key,)).fetchone()[0]
    check('tra cứu chữ Đ HỎNG trước khi sửa (0 row)', before == 0,
          '(got %d)' % before)
    cjk_before = T._cjk_total(con)
    rows_before = T.all_rowcounts(con)
    con.close()

    print()
    print('=== 3) --apply ===')
    plan = T.build_plan(T.connect(db, ro=True), norm)
    T.connect(db, ro=True).close()
    con = T.connect(db)
    snap = T.snapshot_of(con)
    stats = T.apply_plan(con, norm, plan, snap)
    con.commit()
    con.close()
    check('cả 5 row lexicon fixture đều có Ð (thiết kế)',
          all(ETH in t for t, _d in ROWS))
    check('lexicon row sửa = 5', stats['lexicon_rows'] == 5,
          '(got %d)' % stats['lexicon_rows'])
    check('key_norm tính lại = 5', stats['key_norm'] == 5,
          '(got %d)' % stats['key_norm'])
    check('text row sửa > 0', stats['text_rows'] > 0,
          '(got %d)' % stats['text_rows'])

    print()
    print('=== 4) SAU khi sửa ===')
    check('0 ký tự Ð còn lại (20 cột + lexicon + FTS)', count_eth(db) == 0,
          '(còn %d)' % count_eth(db))
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    after = con.execute('SELECT count(*) FROM lexicon WHERE key_norm = ?',
                        (key,)).fetchone()[0]
    check('tra cứu chữ Đ KHỚP sau khi sửa (>=1 row)', after >= 1,
          '(got %d)' % after)
    # round-trip: TỪNG row đã sửa phải có key_norm == normalize_text(term CỦA NÓ)
    n_bad_rt = 0
    for term, _dfn in ROWS:
        fixed_term = term.replace(ETH, DSTROKE)
        got = con.execute('SELECT key_norm FROM lexicon WHERE term = ?',
                          (fixed_term,)).fetchone()
        if got is None or got['key_norm'] != norm(fixed_term):
            n_bad_rt += 1
    check('round-trip key_norm cho TỪNG row đã sửa (%d row)' % len(ROWS),
          n_bad_rt == 0, '(%d row lệch)' % n_bad_rt)
    # FTS đồng bộ — lệnh định danh
    try:
        con.execute("INSERT INTO lexicon_fts(lexicon_fts, rank) "
                    "VALUES('integrity-check', 1)")
        con.commit()
        check('FTS5 integrity-check rank=1 (index khớp bảng nội dung)', True)
    except sqlite3.DatabaseError as e:
        check('FTS5 integrity-check rank=1', False, str(e))
    dup = con.execute('SELECT count(*) FROM (SELECT rowid FROM lexicon_fts '
                      'GROUP BY rowid HAVING count(*) > 1)').fetchone()[0]
    check('không có rowid ghi trùng trong FTS index', dup == 0)
    cjk_after = T._cjk_total(con)
    check('số ký tự CJK không đổi', cjk_before == cjk_after,
          '(trước %d, sau %d)' % (cjk_before, cjk_after))
    rows_after = T.all_rowcounts(con)
    check('tổng row %d bảng không đổi' % len(rows_before), rows_before == rows_after,
          str([t for t in rows_before if rows_before[t] != rows_after.get(t)]))
    ic = con.execute('PRAGMA integrity_check').fetchone()[0]
    check('PRAGMA integrity_check = ok', ic == 'ok', '(got %r)' % ic)
    # Hán tự trong fixture: thêm 1 term Hán để chứng minh không bị đụng
    con.execute('INSERT INTO lexicon (id, term, normalized, definition, source)'
                ' VALUES (99, ?, ?, ?, ?)',
                ('大證國師 Ðại sư', '大證國師 Ðại sư', 'x', 't'))
    con.execute("INSERT INTO lexicon_fts(lexicon_fts) VALUES('rebuild')")
    con.commit()
    hzk = con.execute("SELECT term FROM lexicon WHERE id=99").fetchone()[0]
    check('Hán tự giữ nguyên sau khi thêm', '大證國師' in hzk and 'Ðại' in hzk,
          '(got %r)' % hzk)
    # dọn row thử nghiệm để không làm lệch số đếm ở phần revert
    con.execute("INSERT INTO lexicon_fts(lexicon_fts, rowid, term, definition)"
                " VALUES('delete', 99, ?, ?)", (hzk, 'x'))
    con.execute('DELETE FROM lexicon WHERE id=99')
    con.commit()
    con.close()

    print()
    print('=== 5) REVERT khôi phục đúng ===')
    con = sqlite3.connect(db)
    for r in snap['lexicon']:
        con.execute('UPDATE lexicon SET term=?, definition=?, normalized=?, '
                    'key_norm=? WHERE id=?',
                    (r['term'], r['definition'], r['normalized'],
                     r['key_norm'], r['id']))
    for r in snap['text']:
        con.execute('UPDATE "%s" SET "%s"=? WHERE %s=?'
                    % (r['table'], r['column'], r['pk_col']), (r['value'], r['pk']))
    con.commit()
    con.close()
    check('sau revert, ký tự Ð quay lại đúng số lượng cũ',
          count_eth(db) == n_eth, '(revert %d, cần %d)' % (count_eth(db), n_eth))
    con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
    b2 = con.execute('SELECT count(*) FROM lexicon WHERE key_norm = ?',
                     (key,)).fetchone()[0]
    check('sau revert, tra cứu lại HỎNG như cũ (0 row)', b2 == 0)
    con.close()

    shutil.rmtree(tmpdir, ignore_errors=True)
    print()
    print('=' * 66)
    if _fail:
        print('T207 test: %d PASS, %d FAIL' % (_pass, len(_fail)))
        for f in _fail:
            print('   FAIL:', f)
        sys.exit(1)
    print('T207 test: %d/%d PASS' % (_pass, _pass))
    print('=' * 66)


if __name__ == '__main__':
    main()