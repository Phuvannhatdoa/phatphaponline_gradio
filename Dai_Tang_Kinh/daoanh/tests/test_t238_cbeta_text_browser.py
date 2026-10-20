"""
T238 — CBETA Text Browser (Duyệt văn bản CBETA)
Tests: A-V (unit với fixture DB) + R1-R5 (real DB)

Thiết kế:
- /daoanh/api/cbeta/texts    → danh sách 5 bộ khả dụng
- /daoanh/api/cbeta/text/<sigla>/browse → browse một bộ theo page locator
- juan = '' cho tất cả rows → CASE D (không có juan data)
- GROUP BY page tránh duplicate snippets (nhiều người nhắc trong cùng trang)
- Ordering: page ASC, MIN(id) ASC (deterministic)
- coverage.complete_text = False (đoạn trích, không phải bản toàn văn)
"""

import ast
import os
import sqlite3
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# ─── Fixture DB ──────────────────────────────────────────────────────────────
def _make_fixture_db():
    """In-memory DB với dữ liệu tối thiểu cho T238."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''CREATE TABLE cbeta_person_mentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_name_zh TEXT, dila_id TEXT,
        cbeta_text_sigla TEXT, juan TEXT DEFAULT '',
        page TEXT, context_snippet TEXT
    )''')
    c.execute('''CREATE TABLE cbeta_catalog_vn (
        sigla TEXT PRIMARY KEY, title_vi TEXT, title_zh TEXT
    )''')
    c.execute('''CREATE TABLE cbeta_ref_passages (
        id INTEGER PRIMARY KEY, sigla TEXT, page TEXT,
        han_text TEXT, ref_code TEXT
    )''')

    # Catalog
    c.executemany('INSERT INTO cbeta_catalog_vn VALUES (?,?,?)', [
        ('T51n2076', 'Cảnh Đức Truyền Đăng Lục',  '景德傳燈錄'),
        ('X77n1524', 'Thiền Lâm Tăng Bảo Truyện',  '禪林僧寶傳'),
    ])

    # Mentions: T51n2076 có 3 trang, X77n1524 có 2 trang
    rows = [
        ('馬祖', 'DILA_001', 'T51n2076', '', '0196c', 'snippet A'),
        ('百丈', 'DILA_002', 'T51n2076', '', '0196c', 'snippet B'),  # cùng page → GROUP BY
        ('黃檗', 'DILA_003', 'T51n2076', '', '0200a', 'snippet C'),
        ('臨濟', 'DILA_004', 'T51n2076', '', '0205b', 'snippet D'),
        ('馬祖', 'DILA_001', 'X77n1524', '', '0010a', 'snippet E'),
        ('百丈', 'DILA_002', 'X77n1524', '', '0015c', 'snippet F'),
    ]
    c.executemany('INSERT INTO cbeta_person_mentions (person_name_zh,dila_id,cbeta_text_sigla,juan,page,context_snippet) VALUES (?,?,?,?,?,?)', rows)
    conn.commit()
    return conn


# ─── Helpers (copy logic từ app.py để test độc lập) ──────────────────────────
def _api_cbeta_texts(conn):
    """Logic của /daoanh/api/cbeta/texts."""
    cur = conn.cursor()
    cur.execute('''
        SELECT pm.cbeta_text_sigla AS sigla,
               cv.title_vi, cv.title_zh,
               COUNT(*) AS total_mentions,
               COUNT(CASE WHEN pm.page IS NOT NULL AND pm.page != '' THEN 1 END) AS mentions_with_page,
               COUNT(DISTINCT CASE WHEN pm.page != '' THEN pm.page END) AS unique_pages
        FROM cbeta_person_mentions pm
        LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
        GROUP BY pm.cbeta_text_sigla
        ORDER BY total_mentions DESC
    ''')
    rows = [dict(r) for r in cur.fetchall()]
    return {'ok': True, 'count': len(rows), 'texts': rows}


def _api_cbeta_text_browse(conn, sigla, offset=0, limit=20):
    """Logic của /daoanh/api/cbeta/text/<sigla>/browse."""
    limit = min(int(limit), 100)
    offset = max(int(offset), 0)
    cur = conn.cursor()

    # Kiểm tra sigla tồn tại
    cur.execute('''
        SELECT cv.title_vi, cv.title_zh,
               COUNT(*) as total_mentions,
               COUNT(DISTINCT CASE WHEN pm.page != '' THEN pm.page END) as unique_pages
        FROM cbeta_person_mentions pm
        LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
        WHERE pm.cbeta_text_sigla = ?
    ''', (sigla,))
    meta = cur.fetchone()
    if not meta or not meta['total_mentions']:
        return None  # 404

    # Đếm total pages
    cur.execute('''
        SELECT COUNT(DISTINCT page) FROM cbeta_person_mentions
        WHERE cbeta_text_sigla = ? AND page IS NOT NULL AND page != ''
    ''', (sigla,))
    total = cur.fetchone()[0]

    # Lấy trang, GROUP BY để tránh duplicate
    cur.execute('''
        SELECT page,
               MIN(id) AS reader_ref,
               COUNT(*) AS mention_count,
               MIN(context_snippet) AS snippet
        FROM cbeta_person_mentions
        WHERE cbeta_text_sigla = ? AND page IS NOT NULL AND page != ''
        GROUP BY page
        ORDER BY page ASC, MIN(id) ASC
        LIMIT ? OFFSET ?
    ''', (sigla, limit, offset))
    items = [dict(r) for r in cur.fetchall()]

    has_prev = offset > 0
    has_next = (offset + limit) < total

    return {
        'ok': True,
        'sigla': sigla,
        'title_vi': meta['title_vi'],
        'title_zh': meta['title_zh'],
        'coverage': {
            'total_mentions': meta['total_mentions'],
            'unique_pages': meta['unique_pages'],
            'granularity': 'context_snippet',
            'complete_text': False,
            'note': 'Đây là đoạn trích từ dữ liệu đã nhập, không phải bản toàn văn liên tục.',
        },
        'items': items,
        'pagination': {
            'offset': offset, 'limit': limit, 'total': total,
            'has_next': has_next, 'has_prev': has_prev,
        },
    }


# ─── Tests ───────────────────────────────────────────────────────────────────
class TestT238TextBrowser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_fixture_db()

    # A: /texts trả về ok=True và có texts list
    def test_a_texts_ok(self):
        r = _api_cbeta_texts(self.db)
        self.assertTrue(r['ok'])
        self.assertIn('texts', r)
        self.assertIsInstance(r['texts'], list)
        self.assertGreater(r['count'], 0)

    # B: /texts chứa cả 2 sigla trong fixture
    def test_b_texts_contains_both_siglas(self):
        r = _api_cbeta_texts(self.db)
        siglas = {t['sigla'] for t in r['texts']}
        self.assertIn('T51n2076', siglas)
        self.assertIn('X77n1524', siglas)

    # C: /texts có title_vi và title_zh từ catalog
    def test_c_texts_have_titles(self):
        r = _api_cbeta_texts(self.db)
        t51 = next(t for t in r['texts'] if t['sigla'] == 'T51n2076')
        self.assertEqual(t51['title_vi'], 'Cảnh Đức Truyền Đăng Lục')
        self.assertEqual(t51['title_zh'], '景德傳燈錄')

    # D: /texts sắp xếp theo total_mentions DESC
    def test_d_texts_sorted_by_mentions_desc(self):
        r = _api_cbeta_texts(self.db)
        mentions = [t['total_mentions'] for t in r['texts']]
        self.assertEqual(mentions, sorted(mentions, reverse=True))

    # E: /texts có unique_pages đúng (T51n2076 có 3 trang riêng biệt)
    def test_e_texts_unique_pages(self):
        r = _api_cbeta_texts(self.db)
        t51 = next(t for t in r['texts'] if t['sigla'] == 'T51n2076')
        self.assertEqual(t51['unique_pages'], 3)

    # F: browse T51n2076 ok=True
    def test_f_browse_ok(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertIsNotNone(r)
        self.assertTrue(r['ok'])

    # G: browse trả về sigla, title_vi, title_zh
    def test_g_browse_meta(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertEqual(r['sigla'], 'T51n2076')
        self.assertEqual(r['title_vi'], 'Cảnh Đức Truyền Đăng Lục')

    # H: browse GROUP BY page — trang 0196c chỉ xuất hiện 1 lần dù có 2 người nhắc
    def test_h_group_by_page_no_duplicate(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        pages = [item['page'] for item in r['items']]
        self.assertEqual(len(pages), len(set(pages)), 'Duplicate pages found')

    # I: browse items có mention_count đúng (trang 0196c có 2 nhắc)
    def test_i_mention_count(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        p0196c = next(item for item in r['items'] if item['page'] == '0196c')
        self.assertEqual(p0196c['mention_count'], 2)

    # J: browse items sắp xếp theo page ASC (string sort)
    def test_j_items_sorted_page_asc(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        pages = [item['page'] for item in r['items']]
        self.assertEqual(pages, sorted(pages))

    # K: browse items có reader_ref (MIN id, không null)
    def test_k_reader_ref_not_null(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        for item in r['items']:
            self.assertIsNotNone(item['reader_ref'])
            self.assertIsInstance(item['reader_ref'], int)

    # L: browse items có snippet không null
    def test_l_items_have_snippet(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        for item in r['items']:
            self.assertIn('snippet', item)

    # M: coverage.complete_text = False
    def test_m_coverage_complete_text_false(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertFalse(r['coverage']['complete_text'])

    # N: coverage.granularity = 'context_snippet'
    def test_n_coverage_granularity(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertEqual(r['coverage']['granularity'], 'context_snippet')

    # O: coverage.note có nội dung (cảnh báo không toàn văn)
    def test_o_coverage_note_nonempty(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertTrue(r['coverage']['note'])

    # P: pagination có đầy đủ fields
    def test_p_pagination_fields(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        p = r['pagination']
        for field in ('offset', 'limit', 'total', 'has_next', 'has_prev'):
            self.assertIn(field, p)

    # Q: pagination limit max 100 (vượt trần → clamp)
    def test_q_limit_max_100(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076', limit=999)
        self.assertLessEqual(r['pagination']['limit'], 100)

    # R: sigla không tồn tại → None (404)
    def test_r_sigla_not_found(self):
        r = _api_cbeta_text_browse(self.db, 'NOTEXIST')
        self.assertIsNone(r)

    # S: coverage.unique_pages đúng
    def test_s_coverage_unique_pages(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertEqual(r['coverage']['unique_pages'], 3)

    # T: pagination.total = số trang distinct
    def test_t_pagination_total(self):
        r = _api_cbeta_text_browse(self.db, 'T51n2076')
        self.assertEqual(r['pagination']['total'], 3)

    # U: offset pagination (limit=2, skip trang đầu)
    def test_u_offset_pagination(self):
        r0 = _api_cbeta_text_browse(self.db, 'T51n2076', offset=0, limit=2)
        r1 = _api_cbeta_text_browse(self.db, 'T51n2076', offset=2, limit=2)
        pages0 = {item['page'] for item in r0['items']}
        pages1 = {item['page'] for item in r1['items']}
        self.assertTrue(pages0.isdisjoint(pages1), 'Offset pages overlap')

    # V: ast.parse app.py không lỗi (syntax check)
    def test_v_app_py_syntax(self):
        app_path = os.path.join(BASE_DIR, 'app.py')
        with open(app_path, encoding='utf-8') as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            self.fail(f'app.py SyntaxError: {e}')


# ─── Real DB Tests ────────────────────────────────────────────────────────────
REAL_DB = os.path.join(BASE_DIR, 'data', 'lineage.db')

@unittest.skipUnless(os.path.exists(REAL_DB), 'Real DB not available')
class TestT238RealDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(REAL_DB)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    # R1: /texts trả về ít nhất 5 bộ
    def test_r1_texts_at_least_5(self):
        r = _api_cbeta_texts(self.conn)
        self.assertTrue(r['ok'])
        self.assertGreaterEqual(r['count'], 5)

    # R2: T51n2076 có ít nhất 100 trang distinct
    def test_r2_t51n2076_has_pages(self):
        r = _api_cbeta_text_browse(self.conn, 'T51n2076')
        self.assertIsNotNone(r)
        self.assertGreaterEqual(r['coverage']['unique_pages'], 100)

    # R3: X77n1524 có ít nhất 50 trang distinct
    def test_r3_x77n1524_has_pages(self):
        r = _api_cbeta_text_browse(self.conn, 'X77n1524')
        self.assertIsNotNone(r)
        self.assertGreaterEqual(r['coverage']['unique_pages'], 50)

    # R4: Không có duplicate page trong 1 sigla
    def test_r4_no_duplicate_pages_t51n2076(self):
        r = _api_cbeta_text_browse(self.conn, 'T51n2076', limit=100)
        pages = [item['page'] for item in r['items']]
        self.assertEqual(len(pages), len(set(pages)))

    # R5: reader_ref là integer hợp lệ
    def test_r5_reader_ref_valid(self):
        r = _api_cbeta_text_browse(self.conn, 'T51n2076')
        for item in r['items']:
            self.assertIsInstance(item['reader_ref'], int)
            self.assertGreater(item['reader_ref'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
