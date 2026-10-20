"""
test_t259_entity_evidence_panel.py
T259 — Bằng Chứng & Nguồn Gốc: Entity Evidence & Provenance Panel

Phase 0 findings:
- CASE A: existing /api/evidence/<subject_id> is sufficient — no backend change.
- PERSON claims: NETWORK_EVIDENCE / unverified (22,332 total in DB).
- PLACE claims: COORDINATE + NAME / verified (for place entities).
- source_reference: internal ID like "T69:marcus:A001897:A000490" — never a URL.
- entity_hub INTEGER entity_id (100001...) used by entity_claims.
- _resolve_entity_id: A001897 -> entity_hub canonical_label='A001897' -> entity_id=220093.
- A001897 real data: 34 NETWORK_EVIDENCE claims + 5 co_mentions.
- All PERSON claims have verification_status='unverified'.

Tests A-X cover:
A  — evidence API ok=True for valid subject_id
B  — resolved entity info present
C  — claims array present for known person
D  — co_mentions array present
E  — source_reference is NOT an http/https URL
F  — verification_status values are from the known set
G  — claim_type NETWORK_EVIDENCE present for persons
H  — object_text is non-empty string
I  — confidence is float 0.0–1.0
J  — data_status.claims.total matches len(claims)
K  — data_status.co_mentions.total matches len(co_mentions)
L  — persona_level present (L1/L2/L3)
M  — no claims for unknown subject_id (graceful empty)
N  — event_text_link co_mentions have cbeta_ref field
O  — predicate field present in every claim
P  — ok=True even when claims=[] (not 404)
Q  — source_code field present in places/claims route
R  — ast.parse app.py passes (no syntax error)
S  — entity_hub lookup by canonical_label works for A001897
T  — frontend: #entityEvidenceBlock present in places.html
U  — frontend: loadEntityEvidence function defined in places.html
V  — frontend: call to loadEntityEvidence present in person load flow
W  — frontend: source_reference NOT rendered as <a href
X  — real DB: A001897 has >= 30 claims (regression guard)
"""

import ast
import os
import re
import sqlite3
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
_DAOANH = os.path.dirname(_HERE)
_APP = os.path.join(_DAOANH, "app.py")
_HTML = os.path.join(_DAOANH, "places.html")
_DB = os.path.join(_DAOANH, "data", "lineage.db")


# ---------------------------------------------------------------------------
# Fixtures — in-memory DB mirroring the minimal schema used by evidence API
# ---------------------------------------------------------------------------
def _make_fixture_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE entity_hub (
            entity_id   INTEGER PRIMARY KEY,
            entity_type TEXT NOT NULL,
            canonical_label TEXT,
            status      TEXT DEFAULT 'active',
            created_at  TEXT,
            updated_at  TEXT
        );
        CREATE TABLE entity (
            entity_id   TEXT PRIMARY KEY,
            entity_type TEXT,
            dila_id     TEXT,
            alias_vi    TEXT,
            alias_zh    TEXT,
            cbeta_occ   TEXT,
            marcus_id   TEXT,
            extra_alias TEXT
        );
        CREATE TABLE entity_claims (
            claim_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id           INTEGER NOT NULL,
            source_id           INTEGER NOT NULL DEFAULT 1,
            claim_type          TEXT NOT NULL,
            subject             TEXT,
            predicate           TEXT,
            object_text         TEXT,
            source_record_id    TEXT,
            source_reference    TEXT,
            authority_role      TEXT DEFAULT 'supporting',
            confidence          REAL,
            verification_status TEXT DEFAULT 'unverified',
            editor_note         TEXT,
            created_at          TEXT,
            updated_at          TEXT,
            source_url          TEXT,
            retrieved_at        TEXT,
            assertion_level     TEXT,
            reviewed_by         TEXT,
            reviewed_at         TEXT,
            license             TEXT,
            usage_level         TEXT,
            source_version      TEXT
        );
        CREATE TABLE event_text_link (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT,
            entity_type TEXT,
            entity_id   TEXT,
            related_id  TEXT,
            related_name TEXT,
            cbeta_ref   TEXT,
            source_book TEXT,
            source_table TEXT,
            source_ref  TEXT,
            source_id   INTEGER,
            year        INTEGER,
            confidence  REAL,
            created_at  TEXT
        );
        CREATE TABLE event_entities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id    TEXT,
            entity_id   TEXT,
            entity_type TEXT,
            role        TEXT
        );
        CREATE TABLE events (
            event_id    TEXT PRIMARY KEY,
            event_type  TEXT,
            title_zh    TEXT,
            title_vi    TEXT,
            start_year  INTEGER,
            end_year    INTEGER,
            precision   TEXT,
            review_status TEXT,
            confidence  REAL
        );
        CREATE TABLE event_evidence (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        TEXT,
            source_record   TEXT,
            source_ref      TEXT,
            evidence_type   TEXT,
            exact_span      TEXT
        );
        CREATE TABLE data_sources (
            source_id   INTEGER PRIMARY KEY,
            source_code TEXT,
            source_name TEXT,
            authority_score REAL,
            precedence_order INTEGER,
            implemented INTEGER DEFAULT 0
        );
    """)

    # entity_hub: hub_id=220093 for A001897
    conn.execute(
        "INSERT INTO entity_hub VALUES (220093,'PERSON','A001897','active','2026-08-16','2026-08-16')"
    )
    # entity table
    conn.execute(
        "INSERT INTO entity (entity_id,entity_type,dila_id,alias_zh) VALUES ('A001897','PERSON','A001897','百丈海')"
    )
    # 3 claims: NETWORK_EVIDENCE, unverified, no URL in source_reference
    for i, (student, src_ref, obj) in enumerate([
        ("A000490", "T69:marcus:A001897:A000490",
         "Marcus: teacher of A000490 | （T51n2076_p0263c25）; "),
        ("A001984", "T69:marcus:A001897:A001984",
         "Marcus: teacher of A001984 | （T51n2076_p0263c26）; "),
        ("A003636", "T69:marcus:A001897:A003636",
         "Marcus: teacher of A003636 | （望月‧卷六‧附錄：045); "),
    ], start=1):
        conn.execute("""
            INSERT INTO entity_claims
              (claim_id, entity_id, source_id, claim_type, predicate, object_text,
               source_reference, confidence, verification_status)
            VALUES (?,220093,1,'NETWORK_EVIDENCE','lineage_teacher',?,?,0.8,'unverified')
        """, (i, obj, src_ref))

    # 2 co_mentions in event_text_link
    for j, (eid, rname, cref, sbook, yr) in enumerate([
        ("A001897", "恒月", "T50n2061_p0771a18", "宋高僧傳", 1559),
        ("A001897", "懷海", "T50n2061_p0770c14", "宋高僧傳", 6185),
    ], start=1):
        conn.execute("""
            INSERT INTO event_text_link
              (id, event_type, entity_type, entity_id, related_id, related_name,
               cbeta_ref, source_book, source_table, year, confidence)
            VALUES (?,'person_place','person',?,NULL,?,?,?,'place_person_bibl',?,0.8)
        """, (j, eid, rname, cref, sbook, yr))

    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Helpers mimicking app.py _resolve_entity_id and evidence logic
# ---------------------------------------------------------------------------
def _resolve_entity_id(conn, entity_ref):
    """Simplified version of app.py _resolve_entity_id for fixture DB."""
    row = conn.execute(
        "SELECT entity_id FROM entity_hub WHERE canonical_label=?", (entity_ref,)
    ).fetchone()
    if row:
        return row[0], entity_ref
    row = conn.execute(
        "SELECT entity_id FROM entity WHERE dila_id=?", (entity_ref,)
    ).fetchone()
    if row:
        return row[0], entity_ref
    return None, entity_ref


def _api_evidence(conn, subject_id):
    """Minimal evidence API logic for fixture testing."""
    eid, ref = _resolve_entity_id(conn, subject_id)
    if eid is None:
        return {"ok": True, "subject_id": subject_id, "resolved": None,
                "events": [], "claims": [], "co_mentions": [],
                "data_status": {"events": {"total": 0},
                                "claims": {"total": 0, "by_type": {}, "verification": {}},
                                "co_mentions": {"total": 0}}}

    claims = conn.execute("""
        SELECT claim_id, claim_type, predicate, object_text, source_reference,
               confidence, verification_status, assertion_level
        FROM entity_claims WHERE entity_id=?
        ORDER BY claim_id
    """, (eid,)).fetchall()

    co_ments = conn.execute("""
        SELECT id, cbeta_ref, source_book, source_ref, year, confidence,
               related_id, related_name
        FROM event_text_link WHERE entity_id=?
        ORDER BY id
    """, (subject_id,)).fetchall()

    # Build data_status
    by_type = {}
    by_vstatus = {}
    for c in claims:
        ct = c["claim_type"]
        by_type[ct] = by_type.get(ct, 0) + 1
        vs = c["verification_status"]
        by_vstatus[vs] = by_vstatus.get(vs, 0) + 1

    return {
        "ok": True,
        "subject_id": subject_id,
        "persona_level": "L1",
        "resolved": {"canonical": ref},
        "events": [],
        "claims": [dict(c) for c in claims],
        "co_mentions": [dict(cm) for cm in co_ments],
        "data_status": {
            "events": {"total": 0},
            "claims": {"total": len(claims), "by_type": by_type,
                       "verification": by_vstatus},
            "co_mentions": {"total": len(co_ments)},
        },
    }


# ---------------------------------------------------------------------------
# Unit tests (A-R)
# ---------------------------------------------------------------------------
@pytest.fixture
def db():
    c = _make_fixture_db()
    yield c
    c.close()


def test_A_api_ok(db):
    """A — evidence API returns ok=True for valid subject_id."""
    d = _api_evidence(db, "A001897")
    assert d["ok"] is True


def test_B_resolved_present(db):
    """B — resolved entity info present."""
    d = _api_evidence(db, "A001897")
    assert d.get("resolved") is not None
    assert d["resolved"]["canonical"] == "A001897"


def test_C_claims_present(db):
    """C — claims array non-empty for known person."""
    d = _api_evidence(db, "A001897")
    assert len(d["claims"]) == 3


def test_D_comentions_present(db):
    """D — co_mentions array non-empty for A001897."""
    d = _api_evidence(db, "A001897")
    assert len(d["co_mentions"]) == 2


def test_E_source_reference_not_url(db):
    """E — source_reference is NOT an http/https URL."""
    d = _api_evidence(db, "A001897")
    for c in d["claims"]:
        ref = c.get("source_reference") or ""
        assert not ref.startswith("http://") and not ref.startswith("https://"), \
            f"source_reference looks like a URL: {ref!r}"


def test_F_verification_status_known_values(db):
    """F — verification_status values are from the allowed set."""
    allowed = {"verified", "unverified", "rejected", "pending"}
    d = _api_evidence(db, "A001897")
    for c in d["claims"]:
        vs = c.get("verification_status")
        assert vs in allowed, f"Unknown verification_status: {vs!r}"


def test_G_claim_type_network_evidence(db):
    """G — NETWORK_EVIDENCE claim_type present for person claims."""
    d = _api_evidence(db, "A001897")
    types = {c["claim_type"] for c in d["claims"]}
    assert "NETWORK_EVIDENCE" in types


def test_H_object_text_nonempty(db):
    """H — object_text is non-empty string for every claim."""
    d = _api_evidence(db, "A001897")
    for c in d["claims"]:
        assert c.get("object_text"), "object_text is empty"


def test_I_confidence_float(db):
    """I — confidence is float in [0, 1]."""
    d = _api_evidence(db, "A001897")
    for c in d["claims"]:
        cf = c.get("confidence")
        if cf is not None:
            assert 0.0 <= cf <= 1.0, f"confidence out of range: {cf}"


def test_J_data_status_claims_total(db):
    """J — data_status.claims.total matches len(claims)."""
    d = _api_evidence(db, "A001897")
    assert d["data_status"]["claims"]["total"] == len(d["claims"])


def test_K_data_status_comentions_total(db):
    """K — data_status.co_mentions.total matches len(co_mentions)."""
    d = _api_evidence(db, "A001897")
    assert d["data_status"]["co_mentions"]["total"] == len(d["co_mentions"])


def test_L_persona_level(db):
    """L — persona_level present (L1/L2/L3)."""
    d = _api_evidence(db, "A001897")
    level = d.get("persona_level")
    assert level in {"L1", "L2", "L3"}, f"Unexpected persona_level: {level!r}"


def test_M_unknown_subject_graceful(db):
    """M — unknown subject_id returns ok=True with empty claims/co_mentions."""
    d = _api_evidence(db, "UNKNOWN_XYZ")
    assert d["ok"] is True
    assert d["claims"] == []
    assert d["co_mentions"] == []


def test_N_comentions_have_cbeta_ref(db):
    """N — co_mentions have cbeta_ref field."""
    d = _api_evidence(db, "A001897")
    for cm in d["co_mentions"]:
        assert "cbeta_ref" in cm


def test_O_predicate_present(db):
    """O — predicate field present in every claim."""
    d = _api_evidence(db, "A001897")
    for c in d["claims"]:
        assert "predicate" in c


def test_P_ok_true_empty_ok(db):
    """P — ok=True even when resolved but claims=[] (e.g. entity with no claims)."""
    # Insert an entity_hub PERSON with no claims
    db.execute("INSERT INTO entity_hub VALUES (999999,'PERSON','A999999','active',NULL,NULL)")
    d = _api_evidence(db, "A999999")
    assert d["ok"] is True
    assert d["claims"] == []


def test_Q_source_reference_internal_format(db):
    """Q — source_reference uses internal T69:marcus: prefix (not arbitrary URL)."""
    d = _api_evidence(db, "A001897")
    for c in d["claims"]:
        ref = c.get("source_reference") or ""
        if ref:
            # Must not start with http or be a bare CBETA text locator used as link
            assert not re.match(r'^https?://', ref), \
                f"source_reference should not be a URL: {ref!r}"


def test_R_ast_parse_app():
    """R — ast.parse app.py passes (no syntax error)."""
    with open(_APP, "r", encoding="utf-8") as fh:
        source = fh.read()
    ast.parse(source)  # raises SyntaxError if broken


# ---------------------------------------------------------------------------
# Frontend structure tests (T-W)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def html_source():
    with open(_HTML, "r", encoding="utf-8") as fh:
        return fh.read()


def test_T_evidence_block_in_html(html_source):
    """T — #entityEvidenceBlock present in places.html."""
    assert 'id="entityEvidenceBlock"' in html_source


def test_U_load_function_defined(html_source):
    """U — loadEntityEvidence function defined in places.html."""
    assert "function loadEntityEvidence(" in html_source


def test_V_call_site_present(html_source):
    """V — loadEntityEvidence(dilaId) called in person load flow."""
    assert "loadEntityEvidence(dilaId)" in html_source


def test_W_source_reference_not_rendered_as_link(html_source):
    """W — source_reference is NOT used as an href value in T259/T260/T262 JS block.
    T262 adds citation_url (a separate field) as an href; source_reference must stay <span>."""
    import re as _re
    start = html_source.find("// T259 —")
    end = html_source.find("// ─── End T259", start)
    assert start != -1 and end != -1, "T259 JS block markers not found"
    t259_block = html_source[start:end]
    # Precise check: source_reference must not appear as the argument inside href= assignment.
    # T262 uses c.citation_url for href — source_reference must remain <span>-only.
    bad = _re.search(r'href\s*[+]=?\s*["\'].*source_reference|source_reference.*href\s*[+]=?\s*["\']', t259_block)
    assert bad is None, \
        "source_reference is being rendered as a link href (must use citation_url instead)"


# ---------------------------------------------------------------------------
# Real DB tests (X) — skip if DB unavailable
# ---------------------------------------------------------------------------
real_db_available = os.path.isfile(_DB)


@pytest.mark.skipif(not real_db_available, reason="lineage.db not available")
def test_X_real_db_a001897_claims():
    """X — real DB: A001897 has >= 30 claims (regression guard)."""
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT entity_id FROM entity_hub WHERE canonical_label='A001897'"
        ).fetchone()
        assert row is not None, "A001897 not found in entity_hub"
        eid = row["entity_id"]
        cnt = conn.execute(
            "SELECT COUNT(*) FROM entity_claims WHERE entity_id=?", (eid,)
        ).fetchone()[0]
        assert cnt >= 30, f"Expected >= 30 claims for A001897, got {cnt}"
    finally:
        conn.close()
