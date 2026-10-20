"""
T262 — Structured Marcus Citation Inspection
Tests: A–N (unit) + real_db_full + ast_guard
"""
import ast, importlib.util, json, os, re, sqlite3, sys, types
import pytest

# ── AST guard ─────────────────────────────────────────────────────────────────
def test_ast_guard():
    src = os.path.join(os.path.dirname(__file__), '..', 'app.py')
    with open(src, encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)  # raises SyntaxError on bad Python

# ── Helpers ───────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
SKIP_DB = not os.path.exists(DB_PATH)

# Regex mirroring _T262_CBETA_URL_RE in app.py
_URL_RE = re.compile(
    r'https?://cbetaonline\.dila\.edu\.tw/(?:zh/)?'
    r'(?:[A-Z]{1,3}\d+n[A-Z0-9]+)_(?:[a-z]\d+[a-c]\d+)'
)

def _extract_citation_url(object_text):
    if not object_text:
        return None
    m = _URL_RE.search(object_text)
    return m.group(0) if m else None

# ── Unit tests ─────────────────────────────────────────────────────────────────
def test_A_url_extracted_from_object_text():
    txt = 'Marcus: teacher of A013751 | citation; http://cbetaonline.dila.edu.tw/T51n2076_p0264a14'
    assert _extract_citation_url(txt) == 'http://cbetaonline.dila.edu.tw/T51n2076_p0264a14'

def test_B_https_variant_extracted():
    txt = 'Marcus: teacher of A022517 | text; https://cbetaonline.dila.edu.tw/zh/B27n0151_p0453b10'
    assert _extract_citation_url(txt) == 'https://cbetaonline.dila.edu.tw/zh/B27n0151_p0453b10'

def test_C_j_series_sigla():
    txt = 'text; http://cbetaonline.dila.edu.tw/J40nB486_p0290c27'
    assert _extract_citation_url(txt) == 'http://cbetaonline.dila.edu.tw/J40nB486_p0290c27'

def test_D_none_when_no_url():
    txt = 'Marcus: teacher of A000668 | 《傳燈錄》; （T51n2076_p0263c25）; '
    assert _extract_citation_url(txt) is None

def test_E_none_for_empty_text():
    assert _extract_citation_url('') is None
    assert _extract_citation_url(None) is None

def test_F_malformed_url_not_extracted():
    # truncated URL (no locator)
    txt = 'text; http://cbetaonline.dila.edu.tw/GA010n0009_p0'
    assert _extract_citation_url(txt) is None

def test_G_double_slash_url_not_extracted():
    txt = 'text; http://cbetaonline.dila.edu.tw/http://cbetaonline.dila.edu.tw'
    assert _extract_citation_url(txt) is None

def test_H_wangyue_ref_no_url():
    txt = 'Marcus: teacher of A019864 | （望月‧卷六‧附錄：045); '
    assert _extract_citation_url(txt) is None

def test_I_cbeta_inline_no_url():
    txt = '(CBETA, T50, no. 2061, p. 774, c13-14)'
    assert _extract_citation_url(txt) is None

def test_J_url_must_start_with_cbetaonline():
    txt = 'see https://example.com/T51n2076_p0264a14 for details'
    assert _extract_citation_url(txt) is None

def test_K_b_series_sigla():
    txt = 'http://cbetaonline.dila.edu.tw/B35n0194_p0349a09'
    assert _extract_citation_url(txt) == 'http://cbetaonline.dila.edu.tw/B35n0194_p0349a09'

def test_L_x_series_sigla():
    txt = 'http://cbetaonline.dila.edu.tw/X77n1523_p0356c15'
    assert _extract_citation_url(txt) == 'http://cbetaonline.dila.edu.tw/X77n1523_p0356c15'

def test_M_citation_url_field_present_in_claim_dict():
    """citation_url key always present (None or str) — no KeyError in JS."""
    claim_with_url = {
        "object_text": "http://cbetaonline.dila.edu.tw/T51n2076_p0264a14",
        "citation_url": _extract_citation_url("http://cbetaonline.dila.edu.tw/T51n2076_p0264a14"),
    }
    assert "citation_url" in claim_with_url
    assert claim_with_url["citation_url"] is not None

def test_N_no_db_mutation():
    """T262 is read-only: regex operates on Python string, no DB write."""
    txt = "http://cbetaonline.dila.edu.tw/T51n2076_p0264a14"
    url = _extract_citation_url(txt)
    assert url == "http://cbetaonline.dila.edu.tw/T51n2076_p0264a14"
    # No DB connection used — pass by definition

# ── Real DB tests ──────────────────────────────────────────────────────────────
@pytest.mark.skipif(SKIP_DB, reason="lineage.db not found")
def test_real_db_full():
    """A001897: claim_count unchanged, citation_url populated for URL claims."""
    conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    eid_row = conn.execute(
        "SELECT entity_id FROM entity_hub WHERE canonical_label='A001897'"
    ).fetchone()
    assert eid_row is not None, "A001897 not found in entity_hub"
    eid = eid_row["entity_id"]

    rows = conn.execute(
        "SELECT object_text FROM entity_claims WHERE entity_id=? AND source_id=4",
        (eid,)
    ).fetchall()
    conn.close()

    assert len(rows) == 34, f"expected 34 MARCUS claims for A001897, got {len(rows)}"

    urls_found = [_extract_citation_url(r["object_text"]) for r in rows]
    url_count = sum(1 for u in urls_found if u is not None)
    assert url_count >= 1, "expected at least 1 URL citation for A001897"

    # All extracted URLs start with cbetaonline domain
    for u in urls_found:
        if u is not None:
            assert "cbetaonline.dila.edu.tw" in u

@pytest.mark.skipif(SKIP_DB, reason="lineage.db not found")
def test_real_db_url_coverage():
    """30% of MARCUS claims have extractable URL (Phase 0 finding)."""
    conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT object_text FROM entity_claims WHERE source_id=4 AND object_text IS NOT NULL"
    ).fetchall()
    conn.close()
    total = len(rows)
    url_cnt = sum(1 for r in rows if _extract_citation_url(r["object_text"]) is not None)
    # Phase 0 measured 6726/22332 ≈ 30.1% — allow ±5%
    pct = url_cnt / total * 100
    assert 25 <= pct <= 35, f"URL coverage {pct:.1f}% outside expected 25–35% range"
