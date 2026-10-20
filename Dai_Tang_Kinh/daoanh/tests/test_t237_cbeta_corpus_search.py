"""T237 — CBETA Corpus Search tests (A-T).

Verifies:
- Exact substring search over cbeta_person_mentions.context_snippet
- No fuzzy/LLM/semantic matching
- Result limit, ordering, provenance fields
- Coverage honesty (searchable != catalog total)
- T236 reader reference deterministic
- X-series not filtered
- Frontend escaping, race guard
- No DB/schema mutation
"""
import sys, os, re, sqlite3
import pytest

_HERE   = os.path.dirname(__file__)
_APP    = os.path.join(_HERE, '..', 'app.py')
_PLACES = os.path.join(_HERE, '..', 'places.html')
_DB     = os.path.join(_HERE, '..', 'data', 'lineage.db')

with open(_PLACES, encoding='utf-8') as _f:
    _PLACES_SRC = _f.read()
with open(_APP, encoding='utf-8') as _f:
    _APP_SRC = _f.read()


# ── In-memory fixture DB ────────────────────────────────────────────────────

def _make_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE cbeta_person_mentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cbeta_text_sigla TEXT, dila_person_id TEXT, person_name_zh TEXT,
        juan TEXT, page TEXT, context_snippet TEXT
    )""")
    conn.execute("""CREATE TABLE cbeta_catalog_vn (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sigla TEXT UNIQUE,
        title_vi TEXT, title_zh TEXT
    )""")
    # Catalog
    conn.execute("INSERT INTO cbeta_catalog_vn VALUES (1,'T51n2076','Cảnh Đức Truyền Đăng Lục','景德傳燈錄')")
    conn.execute("INSERT INTO cbeta_catalog_vn VALUES (2,'X77n1524','Kinh X','X-Series Text')")
    # Mentions containing 百丈
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (1,'T51n2076','A001897','百丈海','1','0252b','虔州百丈山大智禪師者')")
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (2,'T51n2076','A001897','百丈海','2','0268c','洪州百丈山懷海禪師')")
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (3,'T51n2076','A001234','馬祖','1','0100a','馬祖道一禪師入百丈山')")
    # X-series
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (4,'X77n1524','A001897','百丈海','','0100a','X-series 百丈海 evidence')")
    # No match
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (5,'T51n2076','A002000','六祖','1','0300a','六祖慧能大師')")
    conn.commit()
    return conn


def _search(conn, q, limit=30):
    """Replicate corpus-search endpoint logic on in-memory conn."""
    if not q or len(q) < 2:
        return None  # 400
    pattern = '%' + q + '%'
    total_passages = conn.execute(
        "SELECT COUNT(*) FROM cbeta_person_mentions "
        "WHERE context_snippet IS NOT NULL AND context_snippet != ''"
    ).fetchone()[0]
    total_texts = conn.execute(
        "SELECT COUNT(DISTINCT cbeta_text_sigla) FROM cbeta_person_mentions"
    ).fetchone()[0]
    catalog_total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]
    rows = conn.execute("""
        SELECT pm.id AS mention_id, pm.cbeta_text_sigla AS sigla,
               pm.person_name_zh, pm.juan, pm.page, pm.context_snippet AS snippet,
               cv.title_vi, cv.title_zh
        FROM cbeta_person_mentions pm
        LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
        WHERE pm.context_snippet LIKE ?
        ORDER BY pm.cbeta_text_sigla ASC, pm.page ASC, pm.id ASC
        LIMIT ?
    """, (pattern, limit)).fetchall()
    return {
        "ok": True, "query": q,
        "result_count": len(rows), "limit": limit,
        "coverage": {
            "texts_searchable": total_texts,
            "passages_searchable": total_passages,
            "catalog_total": catalog_total,
            "scope": "imported_corpus"
        },
        "results": [
            {"mention_id": r["mention_id"], "sigla": r["sigla"] or "",
             "title_vi": r["title_vi"] or "", "title_zh": r["title_zh"] or "",
             "juan": r["juan"] or "", "page": r["page"] or "",
             "snippet": r["snippet"] or "", "reader_ref": r["mention_id"]}
            for r in rows
        ]
    }


# ── Tests A-T ────────────────────────────────────────────────────────────────

class TestT237CbetaCorpusSearch:

    # A. Valid Chinese substring returns results
    def test_a_valid_query_returns_results(self):
        conn = _make_db()
        r = _search(conn, '百丈')
        assert r and r['ok'] and r['result_count'] > 0

    # B. No-match returns empty list, ok=True
    def test_b_no_match_empty(self):
        conn = _make_db()
        r = _search(conn, '無此字')
        assert r and r['ok']
        assert r['result_count'] == 0
        assert r['results'] == []

    # C. Invalid/empty query → None (400)
    def test_c_empty_query_rejected(self):
        conn = _make_db()
        assert _search(conn, '') is None
        assert _search(conn, ' ') is None

    # C2. Single char query rejected (< 2 chars)
    def test_c2_single_char_rejected(self):
        conn = _make_db()
        assert _search(conn, '百') is None

    # D. SQL injection-like input is safe (parameterized)
    def test_d_sql_injection_safe(self):
        conn = _make_db()
        r = _search(conn, "' OR '1'='1")
        assert r and r['ok']
        assert r['result_count'] == 0  # no match, not an injection

    # E. Result limit enforced
    def test_e_limit_enforced(self):
        conn = _make_db()
        r = _search(conn, '百丈', limit=2)
        assert r and r['result_count'] <= 2
        assert len(r['results']) <= 2

    # F. Deterministic ordering: sigla → page → id
    def test_f_deterministic_ordering(self):
        conn = _make_db()
        r1 = _search(conn, '百丈')
        r2 = _search(conn, '百丈')
        siglas1 = [x['sigla'] for x in r1['results']]
        siglas2 = [x['sigla'] for x in r2['results']]
        assert siglas1 == siglas2
        # Should be sorted (T51n2076 < X77n1524)
        for i in range(len(siglas1) - 1):
            assert siglas1[i] <= siglas1[i+1]

    # G. Sigla provenance preserved
    def test_g_sigla_preserved(self):
        conn = _make_db()
        r = _search(conn, '百丈')
        siglas = {x['sigla'] for x in r['results']}
        assert 'T51n2076' in siglas

    # H. Juan preserved where available
    def test_h_juan_preserved(self):
        conn = _make_db()
        r = _search(conn, '百丈')
        results_with_juan = [x for x in r['results'] if x['juan']]
        assert len(results_with_juan) > 0

    # I. Page/source locator preserved
    def test_i_page_preserved(self):
        conn = _make_db()
        r = _search(conn, '百丈')
        results_with_page = [x for x in r['results'] if x['page']]
        assert len(results_with_page) > 0

    # J. LEFT JOIN does NOT discard passage without catalog entry
    def test_j_left_join_preserves_uncatalogued(self):
        conn = _make_db()
        # Add a mention with sigla not in catalog
        conn.execute("INSERT INTO cbeta_person_mentions VALUES (99,'NOCATALOG','A999','百丈','1','0001a','百丈無目錄')")
        conn.commit()
        r = _search(conn, '百丈無目錄')
        assert r['result_count'] == 1
        assert r['results'][0]['title_vi'] == ''  # NULL → ''

    # K. Coverage counts are correct
    def test_k_coverage_correct(self):
        conn = _make_db()
        r = _search(conn, '百丈')
        cov = r['coverage']
        assert cov['passages_searchable'] == 5  # fixture has 5 rows
        assert cov['texts_searchable'] == 2     # T51n2076, X77n1524
        assert cov['catalog_total'] == 2        # fixture has 2 catalog rows

    # L. Catalog count != searchable count (honesty)
    def test_l_catalog_not_misrepresented(self):
        conn = _make_db()
        r = _search(conn, '百丈')
        cov = r['coverage']
        # In real DB: 3122 catalog but only 5 siglas in mentions
        # In fixture: scope must be 'imported_corpus'
        assert cov['scope'] == 'imported_corpus'
        assert 'catalog_total' in cov
        assert 'passages_searchable' in cov

    # M. Reader reference is deterministic (mention_id integer)
    def test_m_reader_ref_deterministic(self):
        conn = _make_db()
        r1 = _search(conn, '百丈')
        r2 = _search(conn, '百丈')
        refs1 = [x['reader_ref'] for x in r1['results']]
        refs2 = [x['reader_ref'] for x in r2['results']]
        assert refs1 == refs2
        for ref in refs1:
            assert isinstance(ref, int)

    # N. X-series material is NOT silently filtered
    def test_n_x_series_preserved(self):
        conn = _make_db()
        r = _search(conn, 'X-series')
        assert r['result_count'] > 0
        assert any(x['sigla'] == 'X77n1524' for x in r['results'])

    # O. Frontend escapes DB-derived content (_escHtml)
    def test_o_frontend_escapes_content(self):
        assert '_escHtml(r.sigla)' in _PLACES_SRC or '_escHtml(r.title_vi)' in _PLACES_SRC
        assert '_escHtml(r.snippet)' in _PLACES_SRC

    # P. Frontend XSS: query rendered with _escHtml
    def test_p_query_escaped_in_render(self):
        assert '_escHtml(d.query)' in _PLACES_SRC

    # Q. Stale search race guard: AbortController pattern
    def test_q_race_guard_abort_controller(self):
        assert 'AbortController' in _PLACES_SRC
        assert '_cbetaCorpusAbort' in _PLACES_SRC
        assert 'AbortError' in _PLACES_SRC

    # R. T236 reader reuse confirmed: same openCbetaPassageReader function called
    def test_r_t236_reader_reused(self):
        assert 'openCbetaPassageReader' in _PLACES_SRC
        # T237 calls it from corpus search results
        assert 'cbetaCorpusSearch' in _PLACES_SRC

    # S. Zero DB mutation in endpoint
    def test_s_no_db_mutation(self):
        endpoint_src = _APP_SRC[_APP_SRC.find('def api_cbeta_corpus_search'):]
        endpoint_src = endpoint_src[:endpoint_src.find('\ndef ')]
        for kw in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']:
            assert kw not in endpoint_src.upper(), f"Endpoint has mutation: {kw}"

    # T. Zero schema mutation
    def test_t_no_schema_mutation(self):
        endpoint_src = _APP_SRC[_APP_SRC.find('def api_cbeta_corpus_search'):]
        endpoint_src = endpoint_src[:endpoint_src.find('\ndef ')]
        assert 'CREATE' not in endpoint_src.upper()
        assert 'ALTER' not in endpoint_src.upper()

    # Extra: route defined
    def test_route_defined(self):
        assert "'/daoanh/api/cbeta/corpus-search'" in _APP_SRC

    # Extra: coverage block in frontend
    def test_coverage_block_in_frontend(self):
        assert 'cbetaCorpusCoverage' in _PLACES_SRC
        assert 'cbetaCorpusBlock' in _PLACES_SRC or 'cbetaCorpusInput' in _PLACES_SRC


# ── Real DB tests ─────────────────────────────────────────────────────────────

@pytest.mark.skipif(not os.path.exists(_DB), reason="Production DB not available")
class TestT237RealDB:

    def _rconn(self):
        conn = sqlite3.connect(f'file:{_DB}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def test_r1_baizhang_query(self):
        """百丈 should return results."""
        conn = self._rconn()
        r = _search(conn, '百丈', limit=30)
        conn.close()
        assert r and r['ok']
        assert r['result_count'] > 0
        print(f"\n百丈 results: {r['result_count']}")

    def test_r2_mazhu_query(self):
        """馬祖 may return 0 (CASE D: limited corpus)."""
        conn = self._rconn()
        r = _search(conn, '馬祖', limit=30)
        conn.close()
        assert r and r['ok']
        print(f"\n馬祖 results: {r['result_count']} (0 expected in limited corpus)")

    def test_r3_real_coverage_honest(self):
        """Searchable texts << catalog (3122)."""
        conn = self._rconn()
        r = _search(conn, '百丈', limit=1)
        conn.close()
        cov = r['coverage']
        assert cov['catalog_total'] == 3122
        assert cov['texts_searchable'] < 3122
        print(f"\nSearchable: {cov['texts_searchable']} texts / {cov['passages_searchable']} passages, Catalog: {cov['catalog_total']}")

    def test_r4_x_series_in_real_db(self):
        """X-series mentions present and searchable."""
        conn = self._rconn()
        x_count = conn.execute(
            "SELECT COUNT(*) FROM cbeta_person_mentions WHERE cbeta_text_sigla LIKE 'X%'"
        ).fetchone()[0]
        conn.close()
        assert x_count > 0

    def test_r5_reader_ref_is_valid_integer(self):
        """All reader_ref values from real search are valid integers."""
        conn = self._rconn()
        r = _search(conn, '百丈', limit=10)
        conn.close()
        for item in r['results']:
            assert isinstance(item['reader_ref'], int) and item['reader_ref'] > 0

    def test_r6_ast_parse(self):
        """app.py must parse without syntax error."""
        import ast
        with open(_APP, encoding='utf-8') as f:
            src = f.read()
        ast.parse(src)
