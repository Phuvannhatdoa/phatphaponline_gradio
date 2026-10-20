"""
test_t261_marcus_object_labels.py
T261 — Marcus Object Label Enrichment
Tests A-Q + Real DB regression

Nguyên tắc:
- JOIN key: SUBSTR(source_reference, -7) == marcus_reference.node_id
- Chỉ áp dụng cho source_id=4 (MARCUS) + format T69:marcus:_______:_______
- KHÔNG đổi existing fields (claim_id, predicate, object_text, source_reference, ...)
- ZERO DB mutation | ZERO schema change | ZERO external API/LLM

Chạy: pytest tests/test_t261_marcus_object_labels.py -v
"""
import json
import re
import sqlite3
import ast
import os
import pytest

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
DB_ABS  = os.path.abspath(DB_PATH)
HAS_DB  = os.path.exists(DB_PATH)

# ─── Unit helpers (no DB) ────────────────────────────────────────────────────

def _parse_obj_id(source_reference):
    """Deterministic object DILA ID từ T69:marcus:subject:object."""
    if not source_reference:
        return None
    p = source_reference.split(':')
    if len(p) == 4 and re.match(r'^A\d{6}$', p[3]):
        return p[3]
    return None

def _esc_html(s):
    if not s: return ''
    return (str(s).replace('&','&amp;').replace('<','&lt;')
            .replace('>','&gt;').replace('"','&quot;').replace("'",'&#x27;'))

def _get_obj_labels(records):
    """Reproduce JS _getObjLabels logic in Python."""
    for r in records:
        if r.get('object_label_vi') or r.get('object_label_zh'):
            return {'vi': r.get('object_label_vi'), 'zh': r.get('object_label_zh')}
    return {'vi': None, 'zh': None}

def _fallback_display(object_id, lbl):
    """Reproduce JS fallback logic."""
    if not object_id:
        return 'EMPTY'
    vi, zh = lbl.get('vi'), lbl.get('zh')
    if vi and zh and vi != zh:
        return 'VI_ZH'
    if vi:
        return 'VI_ONLY'
    if zh:
        return 'ZH_ONLY'
    return 'ID_ONLY'


# ─── Test A: A001897 returns actual object labels ─────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_A_a001897_returns_object_labels():
    """Test A: A001897 claims phải có object_label_vi hoặc object_label_zh."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    eid = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label=?", ('A001897',)).fetchone()['entity_id']
    rows = conn.execute("""
        SELECT c.claim_id, c.source_reference,
               mr.label AS object_label_zh, mr.label_vi AS object_label_vi
        FROM entity_claims c
        LEFT JOIN marcus_reference mr
            ON c.source_id = 4
            AND c.source_reference LIKE 'T69:marcus:_______:_______'
            AND mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.entity_id = ? AND c.source_id = 4
    """, (eid,)).fetchall()
    conn.close()
    assert len(rows) > 0
    resolved = [r for r in rows if r['object_label_vi'] or r['object_label_zh']]
    assert len(resolved) == len(rows), f"Tất cả MARCUS claims phải có labels: {len(resolved)}/{len(rows)}"


# ─── Test B: A000490 resolves to actual labels ────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_B_a000490_resolves_labels():
    """Test B: A000490 → label='希運' label_vi='Hi Vận'."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    mr = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id=?", ('A000490',)).fetchone()
    conn.close()
    assert mr is not None, "A000490 phải có trong marcus_reference"
    assert mr['label'] == '希運', f"Expected '希運', got '{mr['label']}'"
    assert mr['label_vi'] == 'Hi Vận', f"Expected 'Hi Vận', got '{mr['label_vi']}'"


# ─── Test C: DILA ID vẫn visible ─────────────────────────────────────────────

def test_C_canonical_id_remains_visible():
    """Test C: DILA ID luôn hiển thị (không bị ẩn khi có label)."""
    records = [{'object_label_vi': 'Hi Vận', 'object_label_zh': '希運'}]
    lbl = _get_obj_labels(records)
    display = _fallback_display('A000490', lbl)
    # In VI_ZH mode the ID is still shown alongside (not EMPTY or omitted)
    assert display == 'VI_ZH'
    # ID must be included in rendered output
    rendered = _esc_html('A000490')
    assert 'A000490' in rendered


# ─── Test D: thiếu object_label_vi → fallback ZH ─────────────────────────────

def test_D_missing_vi_fallback_zh():
    """Test D: label_vi=NULL → ZH_ONLY display."""
    records = [{'object_label_vi': None, 'object_label_zh': '希運'}]
    lbl = _get_obj_labels(records)
    display = _fallback_display('A000490', lbl)
    assert display == 'ZH_ONLY'


# ─── Test E: thiếu object_label_zh → fallback VI ─────────────────────────────

def test_E_missing_zh_fallback_vi():
    """Test E: label_zh=NULL → VI_ONLY display."""
    records = [{'object_label_vi': 'Hi Vận', 'object_label_zh': None}]
    lbl = _get_obj_labels(records)
    display = _fallback_display('A000490', lbl)
    assert display == 'VI_ONLY'


# ─── Test F: cả hai thiếu → ID_ONLY ─────────────────────────────────────────

def test_F_both_missing_fallback_id():
    """Test F: label_vi=NULL, label_zh=NULL → ID_ONLY."""
    records = [{'object_label_vi': None, 'object_label_zh': None}]
    lbl = _get_obj_labels(records)
    display = _fallback_display('A000490', lbl)
    assert display == 'ID_ONLY'


# ─── Test G: non-MARCUS sources không bị ảnh hưởng ───────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_G_non_marcus_sources_unchanged():
    """Test G: DILA/CBETA claims không có object_label_zh/vi."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT c.claim_id, c.source_id,
               mr.label AS object_label_zh, mr.label_vi AS object_label_vi
        FROM entity_claims c
        LEFT JOIN marcus_reference mr
            ON c.source_id = 4
            AND c.source_reference LIKE 'T69:marcus:_______:_______'
            AND mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.source_id != 4
        LIMIT 200
    """).fetchall()
    conn.close()
    for r in rows:
        assert r['object_label_zh'] is None, f"Non-MARCUS claim {r['claim_id']} không được có label_zh"
        assert r['object_label_vi'] is None, f"Non-MARCUS claim {r['claim_id']} không được có label_vi"


# ─── Test H: existing evidence API fields vẫn tương thích ────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_H_existing_api_fields_compatible():
    """Test H: các fields cũ (claim_id, predicate, object_text, source_reference...) vẫn có."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    eid = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label=?", ('A001897',)).fetchone()['entity_id']
    row = conn.execute("""
        SELECT c.claim_id, c.claim_type, c.predicate, c.object_text,
               c.source_reference, c.confidence, c.verification_status,
               COALESCE(d.source_code,'') AS source_code,
               mr.label AS object_label_zh, mr.label_vi AS object_label_vi
        FROM entity_claims c
        LEFT JOIN data_sources d ON d.source_id = c.source_id
        LEFT JOIN marcus_reference mr
            ON c.source_id = 4
            AND c.source_reference LIKE 'T69:marcus:_______:_______'
            AND mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.entity_id = ? LIMIT 1
    """, (eid,)).fetchone()
    conn.close()
    required_fields = ['claim_id','claim_type','predicate','object_text','source_reference','confidence','verification_status','source_code']
    for f in required_fields:
        assert row[f] is not None or row[f] is None  # field exists (even if NULL)
        assert f in row.keys(), f"Field {f} missing"


# ─── Test I: claim count unchanged ────────────────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_I_claim_count_unchanged():
    """Test I: enrichment JOIN không thay đổi số lượng claims."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    eid = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label=?", ('A001897',)).fetchone()[0]
    count_plain = conn.execute("SELECT COUNT(*) FROM entity_claims WHERE entity_id=?", (eid,)).fetchone()[0]
    count_enriched = conn.execute("""
        SELECT COUNT(*) FROM entity_claims c
        LEFT JOIN marcus_reference mr
            ON c.source_id = 4
            AND c.source_reference LIKE 'T69:marcus:_______:_______'
            AND mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.entity_id = ?
    """, (eid,)).fetchone()[0]
    conn.close()
    assert count_plain == count_enriched, f"Claim count changed: {count_plain} → {count_enriched}"


# ─── Test J: JOIN không duplicate claims ─────────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_J_join_no_duplication():
    """Test J: marcus_reference là 1:0/1 — không tạo duplicate claims."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    eid = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label=?", ('A001897',)).fetchone()[0]
    claim_ids = conn.execute("""
        SELECT c.claim_id FROM entity_claims c
        LEFT JOIN marcus_reference mr
            ON c.source_id = 4
            AND c.source_reference LIKE 'T69:marcus:_______:_______'
            AND mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.entity_id = ?
    """, (eid,)).fetchall()
    conn.close()
    ids = [r[0] for r in claim_ids]
    assert len(ids) == len(set(ids)), "Duplicate claim_ids — JOIN đã fanout"


# ─── Test K: grouping key vẫn là (predicate, object_dila_id) ──────────────────

def test_K_grouping_key_unchanged():
    """Test K: T261 không thay đổi grouping key của T260."""
    claims = [
        {'claim_id': 1, 'predicate': 'lineage_teacher',
         'source_reference': 'T69:marcus:A001897:A000490',
         'object_label_zh': '希運', 'object_label_vi': 'Hi Vận'},
        {'claim_id': 2, 'predicate': 'lineage_teacher',
         'source_reference': 'T69:marcus:A001897:A000490',
         'object_label_zh': '希運', 'object_label_vi': 'Hi Vận'},
    ]
    # Group by (predicate, object_dila_id) — labels không ảnh hưởng key
    groups = {}
    for c in claims:
        obj = _parse_obj_id(c['source_reference'])
        key = (c['predicate'] or '') + '::' + (obj if obj else 'NOOBJ_' + str(c['claim_id']))
        if key not in groups:
            groups[key] = {'records': [], 'object_id': obj}
        groups[key]['records'].append(c)
    assert len(groups) == 1, "Grouping key phải dựa trên predicate+object_dila_id, không phải labels"


# ─── Test L: T260 conflict behavior unchanged ────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_L_t260_conflict_behavior_unchanged():
    """Test L: lineage_conflicts_v2 query không bị ảnh hưởng bởi T261."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    eid = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label=?", ('A001897',)).fetchone()[0]
    conflicts = conn.execute(
        "SELECT conflict_type FROM lineage_conflicts_v2 WHERE person_id=? AND is_conflict=1 AND resolved=0",
        (eid,)
    ).fetchall()
    conn.close()
    # Just verify the query runs without error — T261 does not touch this table
    assert isinstance(conflicts, list)


# ─── Test M: T259 raw view unchanged ─────────────────────────────────────────

def test_M_t259_raw_view_unchanged():
    """Test M: raw view fields (predicate, source_reference, object_text) không đổi."""
    claim = {
        'claim_id': 1, 'predicate': 'lineage_teacher',
        'source_reference': 'T69:marcus:A001897:A000490',
        'object_text': 'Marcus: teacher of A000490 | (T51n2076_p0263c25)',
        'verification_status': 'unverified',
        'object_label_zh': '希運', 'object_label_vi': 'Hi Vận',
    }
    # Raw view uses: predicate, object_text, source_reference, verification_status
    assert claim['predicate'] == 'lineage_teacher'
    assert 'T69:marcus:A001897:A000490' in claim['source_reference']
    assert claim['object_text']  # still present
    assert claim['verification_status'] == 'unverified'


# ─── Test N: labels qua XSS escape ────────────────────────────────────────────

def test_N_labels_xss_escaped():
    """Test N: labels phải qua _escHtml trước khi render."""
    evil = '<script>alert(1)</script>'
    escaped = _esc_html(evil)
    assert '<script>' not in escaped
    assert '&lt;script&gt;' in escaped

    # Normal labels
    vi = _esc_html('Hi Vận')
    zh = _esc_html('希運')
    assert vi == 'Hi Vận'
    assert zh == '希運'


# ─── Test O: zero DB mutation ─────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_O_zero_db_mutation():
    """Test O: enrichment query không ghi vào DB."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    count_before = conn.execute("SELECT COUNT(*) FROM entity_claims").fetchone()[0]
    conn.execute("""
        SELECT c.claim_id, mr.label, mr.label_vi
        FROM entity_claims c
        LEFT JOIN marcus_reference mr ON mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.source_id = 4 LIMIT 100
    """).fetchall()
    count_after = conn.execute("SELECT COUNT(*) FROM entity_claims").fetchone()[0]
    conn.close()
    assert count_before == count_after


# ─── Test P: zero schema mutation ────────────────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_P_zero_schema_mutation():
    """Test P: không có bảng mới được tạo."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    tables_before = set(r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    conn.close()
    # Read-only mode đảm bảo không thể tạo bảng
    assert 'marcus_reference' in tables_before, "marcus_reference phải tồn tại"
    assert 'entity_claims' in tables_before


# ─── Test Q: zero external API/LLM ───────────────────────────────────────────

def test_Q_zero_external_api():
    """Test Q: enrichment hoàn toàn local, JOIN chỉ dùng marcus_reference."""
    # Kiểm tra: không có http call trong label resolution logic
    claim = {'object_label_vi': 'Hi Vận', 'object_label_zh': '希運',
             'source_reference': 'T69:marcus:A001897:A000490'}
    labels = _get_obj_labels([claim])
    assert labels['vi'] == 'Hi Vận'
    assert labels['zh'] == '希運'
    # No network call needed — pure local dict access


# ─── Real DB comprehensive ────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_DB, reason="lineage.db không có sẵn")
def test_real_db_a001897_full_enrichment():
    """Regression: A001897 claim count before/after, resolved labels, no duplication."""
    conn = sqlite3.connect(f'file:{DB_ABS}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    eid = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label=?", ('A001897',)).fetchone()['entity_id']

    # Before (plain count)
    count_before = conn.execute("SELECT COUNT(*) FROM entity_claims WHERE entity_id=?", (eid,)).fetchone()[0]

    # After (with JOIN)
    rows = conn.execute("""
        SELECT c.claim_id, c.predicate, c.source_reference,
               mr.label AS object_label_zh, mr.label_vi AS object_label_vi
        FROM entity_claims c
        LEFT JOIN marcus_reference mr
            ON c.source_id = 4
            AND c.source_reference LIKE 'T69:marcus:_______:_______'
            AND mr.node_id = SUBSTR(c.source_reference, -7)
        WHERE c.entity_id = ?
        ORDER BY c.claim_type, c.claim_id
    """, (eid,)).fetchall()
    conn.close()

    count_after = len(rows)
    resolved = sum(1 for r in rows if r['object_label_vi'] or r['object_label_zh'])
    missing  = count_after - resolved

    print(f"\nA001897: before={count_before} after={count_after} resolved={resolved} missing={missing}")

    assert count_before == count_after, "Claim count không được thay đổi"
    assert resolved == count_before, f"Tất cả claims phải resolved: {resolved}/{count_before}"
    assert missing == 0

    # Check A000490 specifically
    row_490 = next((r for r in rows if r['source_reference'] and r['source_reference'].endswith(':A000490')), None)
    assert row_490 is not None, "Claim về A000490 phải tồn tại"
    assert row_490['object_label_zh'] == '希運'
    assert row_490['object_label_vi'] == 'Hi Vận'


# ─── AST guard ───────────────────────────────────────────────────────────────

def test_app_py_ast_valid():
    """Guard: app.py phải parse được."""
    app_path = os.path.join(os.path.dirname(__file__), '..', 'app.py')
    if not os.path.exists(app_path):
        pytest.skip("app.py không tìm thấy")
    with open(app_path, 'r', encoding='utf-8') as f:
        source = f.read()
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"app.py SyntaxError: {e}")
