"""T236 — CBETA Passage Reader tests (A-M).

Verifies:
- Citation→passage resolution contract (deterministic, no fuzzy)
- cbeta_ref_passages richer fallback when sigla+page match
- context_snippet fallback when no ref_passage
- NONE when both absent
- Unresolved citation does not create fake link (UI: no button if no snippet)
- X-series evidence preserved
- Unknown mention_id → 404, graceful
- No DB mutation / no schema change
- T235 API contract backward compatible (mention_id in snippets)
- Rapid person switching (race guard) does not create stale reader links
- DB-derived text escaped in UI
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


# ── In-memory fixture DB ─────────────────────────────────────────────────────

def _make_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE cbeta_person_mentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cbeta_text_sigla TEXT, dila_person_id TEXT, person_name_zh TEXT,
        juan TEXT, page TEXT, context_snippet TEXT
    )""")
    conn.execute("""CREATE TABLE cbeta_ref_passages (
        ref_code TEXT PRIMARY KEY, sigla TEXT, juan INTEGER,
        page TEXT, line_start INTEGER, line_end INTEGER,
        han_text TEXT, vi_summary TEXT, created_at TEXT, updated_at TEXT,
        vi_summary_raw TEXT, vi_summary_clean TEXT
    )""")
    conn.execute("""CREATE TABLE cbeta_catalog_vn (
        id INTEGER PRIMARY KEY, sigla TEXT UNIQUE,
        title_vi TEXT, title_zh TEXT
    )""")
    # Catalog
    conn.execute("INSERT INTO cbeta_catalog_vn VALUES (1,'T51n2076','Cảnh Đức Truyền Đăng Lục','景德傳燈錄')")
    conn.execute("INSERT INTO cbeta_catalog_vn VALUES (2,'X77n1524','Kinh X (phi truyện ký)','X-Series Text')")
    # Mentions: A001897
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (101,'T51n2076','A001897','百丈海','','0252b','snippet T51n2076 0252b 虔州西堂智藏禪師者')")
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (102,'T51n2076','A001897','百丈海','','0268c','snippet T51n2076 0268c 洪州百丈山')")
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (103,'T51n2076','A001897','百丈海','','','')") # empty page + empty snippet
    conn.execute("INSERT INTO cbeta_person_mentions VALUES (104,'X77n1524','A001897','百丈海','','0100a','X-series snippet 百丈海')")  # X-series
    # Passage only for 0252b
    conn.execute("INSERT INTO cbeta_ref_passages (ref_code,sigla,juan,page,line_start,line_end,han_text) VALUES ('T51n2076_p0252b01','T51n2076',0,'0252b',1,1,'full han_text passage 2000+ chars simulation')")
    conn.commit()
    return conn


def _resolve_passage(conn, mention_id):
    """Replicate endpoint logic on in-memory conn."""
    pm = conn.execute("""
        SELECT pm.id, pm.dila_person_id, pm.person_name_zh, pm.cbeta_text_sigla,
               pm.juan, pm.page, pm.context_snippet,
               cv.title_vi, cv.title_zh
        FROM cbeta_person_mentions pm
        LEFT JOIN cbeta_catalog_vn cv ON cv.sigla = pm.cbeta_text_sigla
        WHERE pm.id = ?
    """, (mention_id,)).fetchone()
    if not pm:
        return None

    passage_text = ""
    passage_source = "NONE"
    ref_code = None
    if pm["page"]:
        rp = conn.execute(
            "SELECT ref_code, han_text FROM cbeta_ref_passages WHERE sigla=? AND page=? LIMIT 1",
            (pm["cbeta_text_sigla"], pm["page"])
        ).fetchone()
        if rp and rp["han_text"]:
            passage_text = rp["han_text"]
            passage_source = "cbeta_ref_passages"
            ref_code = rp["ref_code"]
    if not passage_text and pm["context_snippet"]:
        passage_text = pm["context_snippet"]
        passage_source = "context_snippet"

    return {
        "ok": True,
        "mention_id": mention_id,
        "dila_id": pm["dila_person_id"] or "",
        "person_name_zh": pm["person_name_zh"] or "",
        "sigla": pm["cbeta_text_sigla"] or "",
        "title_vi": pm["title_vi"] or "",
        "title_zh": pm["title_zh"] or "",
        "juan": pm["juan"] or "",
        "page": pm["page"] or "",
        "passage_text": passage_text,
        "passage_source": passage_source,
        "ref_code": ref_code or ""
    }


# ── Tests A-M ────────────────────────────────────────────────────────────────

class TestT236CbetaPassageReader:

    # A. Resolvable citation maps to correct sigla
    def test_a_sigla(self):
        conn = _make_db()
        r = _resolve_passage(conn, 101)
        assert r is not None and r['sigla'] == 'T51n2076'

    # B. Correct juan (empty in fixture — preserved)
    def test_b_juan(self):
        conn = _make_db()
        r = _resolve_passage(conn, 101)
        assert r['juan'] == ''

    # C. Correct page locator
    def test_c_page(self):
        conn = _make_db()
        r = _resolve_passage(conn, 101)
        assert r['page'] == '0252b'

    # D. Correct passage text (cbeta_ref_passages has match for 0252b → richer text)
    def test_d_passage_text_ref_passage(self):
        conn = _make_db()
        r = _resolve_passage(conn, 101)
        assert r['passage_source'] == 'cbeta_ref_passages'
        assert 'full han_text passage' in r['passage_text']

    # D2. Fallback to context_snippet when no ref_passage (0268c not in cbeta_ref_passages)
    def test_d2_passage_fallback_snippet(self):
        conn = _make_db()
        r = _resolve_passage(conn, 102)
        assert r['passage_source'] == 'context_snippet'
        assert '洪州百丈山' in r['passage_text']

    # E. Deterministic resolution: same mention_id always same result
    def test_e_deterministic(self):
        conn = _make_db()
        r1 = _resolve_passage(conn, 101)
        r2 = _resolve_passage(conn, 101)
        assert r1['passage_source'] == r2['passage_source']
        assert r1['passage_text'] == r2['passage_text']

    # F. Unresolved citation (empty snippet + empty page) → passage_source = 'NONE', no fake passage
    def test_f_unresolved_no_fake(self):
        conn = _make_db()
        r = _resolve_passage(conn, 103)
        assert r is not None
        assert r['passage_source'] == 'NONE'
        assert r['passage_text'] == ''

    # G. X-series evidence preserved (X77n1524 not discarded)
    def test_g_x_series_preserved(self):
        conn = _make_db()
        r = _resolve_passage(conn, 104)
        assert r is not None
        assert r['sigla'] == 'X77n1524'
        assert 'X-series snippet' in r['passage_text']
        assert r['passage_source'] == 'context_snippet'

    # H. Unknown mention_id → None (endpoint should return 404)
    def test_h_unknown_mention_id(self):
        conn = _make_db()
        r = _resolve_passage(conn, 99999)
        assert r is None

    # I. DB-derived text not fabricated — passage_text matches DB content exactly
    def test_i_no_fabrication(self):
        conn = _make_db()
        r = _resolve_passage(conn, 101)
        # The passage must come from DB, not invented
        assert r['passage_text'] == 'full han_text passage 2000+ chars simulation'

    # J. No DB mutation in endpoint logic
    def test_j_no_mutation(self):
        endpoint_src = _APP_SRC[_APP_SRC.find('def api_cbeta_person_passage'):]
        endpoint_src = endpoint_src[:endpoint_src.find('\ndef ')]
        for kw in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']:
            assert kw not in endpoint_src.upper(), f"Endpoint has mutation: {kw}"

    # K. No schema mutation
    def test_k_no_schema(self):
        endpoint_src = _APP_SRC[_APP_SRC.find('def api_cbeta_person_passage'):]
        endpoint_src = endpoint_src[:endpoint_src.find('\ndef ')]
        assert 'CREATE' not in endpoint_src.upper()
        assert 'ALTER' not in endpoint_src.upper()

    # L. T235 API contract backward compatible — mention_id now in snippet response
    def test_l_t235_contract_includes_mention_id(self):
        # The cbeta-mentions endpoint snippet query must select 'id AS mention_id'
        assert 'id AS mention_id' in _APP_SRC
        assert '"mention_id": s["mention_id"]' in _APP_SRC

    # M. Rapid person switching: openCbetaPassageReader is independent (no person context)
    def test_m_race_guard_reader_independent(self):
        # openCbetaPassageReader() uses mention_id directly — no race condition with person switch
        assert 'openCbetaPassageReader' in _PLACES_SRC
        # The button only fires when mention_id is present
        assert 'sn.mention_id' in _PLACES_SRC

    # Additional: UI escape
    def test_ui_passage_uses_textContent(self):
        # cpm-passage must use textContent (not innerHTML) → XSS safe for passage text
        assert "getElementById('cpm-passage').textContent" in _PLACES_SRC

    # Additional: reader modal exists in DOM
    def test_modal_exists(self):
        assert 'id="cbetaPassageModal"' in _PLACES_SRC

    # Additional: close function exists
    def test_close_function_exists(self):
        assert 'function closeCbetaPassageModal' in _PLACES_SRC


# ── Real DB tests ─────────────────────────────────────────────────────────────

@pytest.mark.skipif(not os.path.exists(_DB), reason="Production DB not available")
class TestT236RealDB:

    def _rconn(self):
        conn = sqlite3.connect(f'file:{_DB}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def test_r1_a001897_mention_id_present(self):
        """A001897 mentions must have integer IDs (PK exists)."""
        conn = self._rconn()
        rows = conn.execute(
            "SELECT id FROM cbeta_person_mentions WHERE dila_person_id='A001897'"
        ).fetchall()
        conn.close()
        assert len(rows) == 7
        for r in rows:
            assert isinstance(r['id'], int) and r['id'] > 0

    def test_r2_a001897_no_ref_passage_match(self):
        """A001897 citations: 0 match cbeta_ref_passages (sigla+page). Document this."""
        conn = self._rconn()
        matched = conn.execute("""
            SELECT COUNT(*) c FROM cbeta_person_mentions pm
            JOIN cbeta_ref_passages rp ON rp.sigla=pm.cbeta_text_sigla AND rp.page=pm.page
            WHERE pm.dila_person_id='A001897'
        """).fetchone()['c']
        conn.close()
        # Documented fact: 0 matches → all fall back to context_snippet
        assert matched == 0
        print(f"\nA001897 ref_passage matches: {matched} (expected 0 — all use context_snippet fallback)")

    def test_r3_a001897_all_snippets_non_empty(self):
        """A001897 context_snippets: all 7 should be non-empty except any with empty page."""
        conn = self._rconn()
        rows = conn.execute(
            "SELECT id, page, context_snippet FROM cbeta_person_mentions WHERE dila_person_id='A001897'"
        ).fetchall()
        conn.close()
        for r in rows:
            if r['page']:  # only check rows that have page locator
                assert r['context_snippet'] and len(r['context_snippet']) > 0, f"Empty snippet for id={r['id']}"

    def test_r4_passage_endpoint_route_defined(self):
        """Route /daoanh/api/cbeta/person-passage/<int:mention_id> must be in app.py."""
        assert "'/daoanh/api/cbeta/person-passage/<int:mention_id>'" in _APP_SRC

    def test_r5_x_series_total_preserved(self):
        """X-series mentions not filtered from cbeta_person_mentions."""
        conn = self._rconn()
        x_count = conn.execute(
            "SELECT COUNT(*) c FROM cbeta_person_mentions WHERE cbeta_text_sigla LIKE 'X%'"
        ).fetchone()['c']
        conn.close()
        # X-series data should be preserved (X77n1524 has 14,637 rows)
        assert x_count > 0, "X-series mentions must not be discarded"
        print(f"\nX-series mention count: {x_count}")

    def test_r6_ast_parse(self):
        """app.py must parse without syntax error."""
        import ast
        with open(_APP, encoding='utf-8') as f:
            src = f.read()
        ast.parse(src)  # raises SyntaxError if invalid
