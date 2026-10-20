# -*- coding: utf-8 -*-
"""T243 — M7 place name normalization tests (DILA ingest + search index).

Chạy ego:    python -X utf8 tests/test_t243_place_name_normalize.py
Chạy pytest: python -X utf8 -m pytest tests/test_t243_place_name_normalize.py -v

Bộ test dùng DB temp (fixture nhỏ) — KHÔNG gọi mạng, KHÔNG đụng lineage.db thật.
Coverage:
  [K1] nfkc            : full-width → half-width, giữ Hán tự
  [K2] vn_key          : không dấu tiếng Việt (đ→d, bỏ dấu, lower, collapse)
  [K3] strip_facility  : bỏ tiền tố VN (Chùa/Tổ đình) + hậu tố Hán (寺/院/庵)
  [K4] hanvi_reading   : tra hanviet_char_map từng chữ
  [K5] pinyin_reading  : pypinyin (thiếu lib → None)
  [K6] place_key_entries: mỗi tên sinh 2 key (full + stripped)
  [G1] build dry-run   : đếm đúng, không ghi DB
  [G2] build apply     : bảng + FTS đầy, count khớp
  [G3] search FTS      : norm_key khớp trả đúng dila_id
  [G4] revert          : DROP 2 bảng, chạy lại lần 2 an toàn
  [G5] idempotent      : apply 2 lần → cùng row count
"""

import importlib.util
import os
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_DAOANH, 'scripts')


def _load(name, filename):
    path = os.path.join(_SCRIPTS, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


U = _load('vn_name_utils', 'vn_places_name_utils.py')
NORM = _load('vn_t243_norm', 'vn_places_t243_normalize.py')


def _make_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript('''
    CREATE TABLE places_dila (
      id TEXT PRIMARY KEY, name TEXT, name_zh TEXT, name_en TEXT,
      name_san TEXT, name_jpn TEXT, name_peo TEXT, name_other TEXT,
      location_xml TEXT, geo_lat REAL, geo_long REAL, place_key TEXT,
      district TEXT, note TEXT, note_category TEXT, listbibl TEXT,
      raw_xml TEXT, source_id INTEGER
    );
    CREATE TABLE namevi_map_places (
      id INTEGER PRIMARY KEY, name_vi TEXT, name_zh TEXT, dila_id TEXT,
      confidence REAL, source TEXT, created_at TEXT, needs_review INTEGER,
      note_vi TEXT, gps_lat TEXT, gps_long TEXT, source_id INTEGER,
      district_vi TEXT, country_vi TEXT, vn_name_status TEXT
    );
    CREATE TABLE hanviet_char_map (char TEXT PRIMARY KEY, reading TEXT, source TEXT,
      is_polyphonic INTEGER, candidates TEXT);
    CREATE TABLE custom_hanviet_override (char TEXT PRIMARY KEY, hanviet TEXT,
      added_by TEXT, created_at DATETIME);
    ''')
    conn.executemany(
        'INSERT INTO places_dila (id,name,name_zh,district,geo_lat,geo_long) '
        'VALUES (?,?,?,?,?,?)',
        [
            ('PL000000000001', 'Kim Cương Tự', '金剛寺', 'VN-TestA', 21.0, 105.8),
            ('PL000000000002', 'Trấn Quốc', '鎮國寺', 'VN-Hanoi', 21.0333, 105.85),
            ('PL000000000003', 'Khe Chùa', '溪寺', 'VN-QuangNinh', None, None),
            ('PL000000000004', 'Bái Đính', '', 'VN-NinhBinh', 20.25, 105.9),
        ])
    conn.executemany(
        'INSERT INTO namevi_map_places (id,name_vi,name_zh,dila_id,confidence,source) '
        'VALUES (?,?,?,?,?,?)',
        [
            (1, 'Chùa Kim Cương', '金剛寺', 'PL000000000001', 0.9, 'manual'),
            (2, 'Chùa Trấn Quốc', '鎮國寺', 'PL000000000002', 0.9, 'manual'),
            (3, 'Chùa Khe', '溪寺', 'PL000000000003', 0.8, 'manual'),
        ])
    conn.executemany(
        'INSERT INTO hanviet_char_map (char,reading,source) VALUES (?,?,?)',
        [('金', 'kim', 't'), ('剛', 'cương', 't'), ('寺', 'tự', 't'),
         ('鎮', 'trấn', 't'), ('國', 'quốc', 't'), ('溪', 'khê', 't')])
    conn.commit()
    return conn, path


def _cleanup(conn, path):
    try:
        conn.close()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_nfkc():
    assert U.nfkc('Ｃｈùａ') == 'Chùa'
    assert U.nfkc('  Chùa Trấn Quốc  ') == 'Chùa Trấn Quốc'
    assert U.nfkc('鎮國寺') == '鎮國寺'


def test_vn_key():
    assert U.vn_key('Chùa Trấn Quốc') == 'chua tran quoc'
    assert U.vn_key('Đại Tòng Lâm Bửu Long') == 'dai tong lam buu long'
    assert U.vn_key('  多  空格  ') == '多 空格'
    assert U.NORMALIZE_FROM_APP is True  # AST-extract thành công từ app.py


def test_strip_facility():
    assert U.strip_facility('Chùa Trấn Quốc') == 'Trấn Quốc'
    assert U.strip_facility('Tổ đình Vĩnh Nghiêm') == 'Vĩnh Nghiêm'
    assert U.strip_facility('Thiền viện Trúc Lâm') == 'Trúc Lâm'
    assert U.strip_facility('鎮國寺') == '鎮國'
    assert U.strip_facility('妙蓮庵') == '妙蓮'
    assert U.strip_facility('Trấn Quốc') == 'Trấn Quốc'   # không có cơ sở → nguyên dạng


def test_hanvi_reading():
    m = {'金': 'kim', '剛': 'cương', '寺': 'tự', '鎮': 'trấn', '國': 'quốc'}
    assert U.hanvi_reading('鎮國寺', m) == 'trấn quốc tự'
    assert U.hanvi_reading('金剛寺', m) == 'kim cương tự'
    assert U.hanvi_reading('未知字', m) == '未 知 字'   # không tra được → giữ nguyên
    assert U.hanvi_reading('', m) is None


def test_pinyin_reading():
    if U.pinyin_available():
        assert U.pinyin_reading('鎮國寺') == 'zhen guo si'
    else:
        assert U.pinyin_reading('鎮國寺') is None


def test_place_key_entries():
    rows = list(U.place_key_entries('Chùa Trấn Quốc'))
    keys = {r['key_kind']: r['norm_key'] for r in rows}
    assert keys['full'] == 'chua tran quoc'
    assert keys['stripped'] == 'tran quoc'
    assert len(rows) == 2


def test_build_dry_run_counts():
    conn, path = _make_db()
    try:
        st = NORM.build_index(conn, dry_run=True)
        assert st['places_total'] == 4
        assert st['places_with_geo'] == 3
        assert st['places_with_vi_name'] == 3
        assert st['rows_keys'] == 20        # 6 + 6 + 6 + 2
        assert st['hanvi_rows'] == 6        # mỗi place 1→3 có name_zh (2 key)
        assert st['suffix_stripped_rows'] > 0
        # dry-run không ghi bảng
        assert conn.execute("SELECT COUNT(*) FROM place_norm_keys").fetchone()[0] == 0
    finally:
        _cleanup(conn, path)


def test_build_apply_and_search():
    conn, path = _make_db()
    try:
        st = NORM.build_index(conn, dry_run=False)
        assert st['fts_rows'] == st['rows_keys'] == 20
        # tìm theo khóa chuẩn không dấu
        rows = conn.execute(
            "SELECT k.dila_id, k.key_kind FROM place_norm_fts f "
            "JOIN place_norm_keys k ON k.rowid=f.rowid "
            "WHERE place_norm_fts MATCH '\"tran quoc\"'").fetchall()
        got = set(r[0] for r in rows) | set()
        assert 'PL000000000002' in got, rows
        # tìm "kim cuong" (chùa) — có cả dila gốc + vi name
        rows = conn.execute(
            "SELECT k.dila_id FROM place_norm_fts f "
            "JOIN place_norm_keys k ON k.rowid=f.rowid "
            "WHERE place_norm_fts MATCH '\"kim cuong\"'").fetchall()
        assert 'PL000000000001' in set(r[0] for r in rows)
        # place không có geo → has_geo=0
        c = conn.execute(
            "SELECT COUNT(*) FROM place_norm_keys WHERE dila_id='PL000000000003' AND has_geo=0").fetchone()[0]
        assert c >= 1
        # hanvi được ghi ở role dila_zh
        hv = conn.execute(
            "SELECT hanvi FROM place_norm_keys WHERE dila_id='PL000000000002' "
            "AND name_role='dila_zh' LIMIT 1").fetchone()[0]
        assert hv == 'trấn quốc tự'
    finally:
        _cleanup(conn, path)


def test_revert_then_idempotent():
    conn, path = _make_db()
    try:
        NORM.build_index(conn, dry_run=False)
        NORM.revert(conn)
        for tbl in (NORM.TB_KEYS, NORM.TB_FTS):
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tbl,)).fetchone()
            assert row is None, 'revert phải DROP %s' % tbl
        # apply lại lần 2 → cùng kết quả
        st = NORM.build_index(conn, dry_run=False)
        assert st['rows_keys'] == 20
        assert st['fts_rows'] == 20
    finally:
        _cleanup(conn, path)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    n = len(fns)
    for fn in fns:
        fn()
    print('T243 PASS %d/%d' % (n, n))
    return 0


if __name__ == '__main__':
    sys.exit(_run())