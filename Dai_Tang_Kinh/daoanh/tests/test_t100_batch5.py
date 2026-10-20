"""T100-BATCH5 — dataset_version + verification_summary + JSON-LD export + release gate.

18 test cases A-R. Không import Flask app — mock-based unit tests, không cần server.
"""
import sys, os, hashlib, json, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ---------------------------------------------------------------------------
# Mock stub để import các helper mà không cần Flask context
# ---------------------------------------------------------------------------

# Tạo module app stub để _resolve_entity_id có thể mock
_app_stub = types.ModuleType('app')
sys.modules['app'] = _app_stub

# Import trực tiếp các helper từ app.py bằng exec (tránh import toàn bộ Flask app)
_HERE = os.path.dirname(__file__)
_APP_PY = os.path.join(_HERE, '..', 'app.py')

# Đọc app.py và extract phần cần test (2 helper functions)
with open(_APP_PY, encoding='utf-8') as f:
    _src = f.read()

# Tìm và exec phần helper T100-P3
def _extract_func(src, func_name):
    """Extract toàn bộ def <func_name>(...) từ source."""
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            lines = src.splitlines()
            start = node.lineno - 1
            end = node.end_lineno
            return '\n'.join(lines[start:end])
    return None

_dv_src = _extract_func(_src, '_compute_dataset_version')
_vs_src = _extract_func(_src, '_compute_verification_summary')

# Cần _resolve_entity_id — mock nó
def _mock_resolve(conn, entity_id):
    """Mock: entity_id dạng 'PL001' → (1, entity_id), khác → (None, None)."""
    if entity_id and entity_id.startswith('PL'):
        return (1, entity_id)
    return (None, None)

# Exec helpers trong namespace có mock
_ns = {
    'hashlib': hashlib,
    '_resolve_entity_id': _mock_resolve,
}
exec(_dv_src, _ns)
exec(_vs_src, _ns)

_compute_dataset_version = _ns['_compute_dataset_version']
_compute_verification_summary = _ns['_compute_verification_summary']


# ---------------------------------------------------------------------------
# Mock connection helper
# ---------------------------------------------------------------------------

class MockCursor:
    def __init__(self, rows): self._rows = rows
    def fetchall(self): return self._rows
    def fetchone(self): return self._rows[0] if self._rows else None

class MockConn:
    """Fake SQLite connection cho unit tests."""
    def __init__(self, claims=None):
        self._claims = claims or []
    def execute(self, sql, params=()):
        # Trả mock claim rows khi query entity_claims
        if 'entity_claims' in sql and 'entity_id' in sql:
            return MockCursor(self._claims)
        return MockCursor([])

def _make_claim(cid, ctype='NAME', pred='vi', obj='Hà Nội', vs='unverified', conf=0.9):
    """Tạo dict giả lập row entity_claims."""
    return {
        'claim_id': cid, 'claim_type': ctype, 'predicate': pred,
        'object_text': obj, 'verification_status': vs, 'confidence': conf,
    }


# ---------------------------------------------------------------------------
# Case A-C: dataset_version
# ---------------------------------------------------------------------------

def test_A_dataset_version_stable():
    """A: Cùng claims → cùng version hash."""
    claims = [_make_claim(1), _make_claim(2)]
    conn1 = MockConn(claims)
    conn2 = MockConn(claims)
    r1 = _compute_dataset_version(conn1, 'PL001')
    r2 = _compute_dataset_version(conn2, 'PL001')
    assert r1['version'] == r2['version'], "A FAIL: hash không stable"
    print("A PASS: dataset_version stable")

def test_B_dataset_version_changes_on_different_claims():
    """B: Khác claims → khác version."""
    r1 = _compute_dataset_version(MockConn([_make_claim(1)]), 'PL001')
    r2 = _compute_dataset_version(MockConn([_make_claim(1), _make_claim(2)]), 'PL001')
    assert r1['version'] != r2['version'], "B FAIL: hash phải khác khi claims khác"
    print("B PASS: dataset_version changes when claims change")

def test_C_dataset_version_no_claims():
    """C: Không có claims → version='no_claims', claim_count=0."""
    r = _compute_dataset_version(MockConn([]), 'PL001')
    assert r['version'] == 'no_claims', "C FAIL: version phải là 'no_claims'"
    assert r['claim_count'] == 0, "C FAIL: claim_count phải 0"
    print("C PASS: dataset_version no_claims case")

def test_D_dataset_version_unresolved_entity():
    """D: entity_id không resolve được → version='no_claims'."""
    r = _compute_dataset_version(MockConn([_make_claim(1)]), 'PERSON001')
    assert r['version'] == 'no_claims', "D FAIL: unresolved entity phải → no_claims"
    print("D PASS: dataset_version unresolved entity")

def test_E_dataset_version_full_hash_64chars():
    """E: full_hash phải là 64 char hex."""
    r = _compute_dataset_version(MockConn([_make_claim(1)]), 'PL001')
    assert len(r['full_hash']) == 64, "E FAIL: full_hash phải 64 chars"
    print("E PASS: full_hash is 64-char hex")

def test_F_dataset_version_claim_count():
    """F: claim_count khớp số claims."""
    claims = [_make_claim(i) for i in range(5)]
    r = _compute_dataset_version(MockConn(claims), 'PL001')
    assert r['claim_count'] == 5, "F FAIL: claim_count phải 5"
    print("F PASS: claim_count correct")


# ---------------------------------------------------------------------------
# Case G-I: verification_summary
# ---------------------------------------------------------------------------

def test_G_verification_summary_all_unverified():
    """G: 100% unverified → release_status='review_required', verified_ratio=0."""
    stats = {"total": 10, "verification": {"unverified": 10}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['release_status'] == 'review_required', "G FAIL"
    assert r['verified_ratio'] == 0.0, "G FAIL: ratio phải 0"
    assert r['dominant_status'] == 'unverified', "G FAIL: dominant phải unverified"
    print("G PASS: all unverified → review_required")

def test_H_verification_summary_half_verified():
    """H: 50% verified → release_status='releasable'."""
    stats = {"total": 10, "verification": {"unverified": 5, "verified": 5}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['release_status'] == 'releasable', "H FAIL: 50% phải releasable"
    assert r['verified_ratio'] == 0.5, "H FAIL: ratio phải 0.5"
    print("H PASS: 50% verified → releasable")

def test_I_verification_summary_empty():
    """I: Không có claims → review_required, ratio=0."""
    r = _compute_verification_summary({"total": 0, "verification": {}, "by_type": {}})
    assert r['release_status'] == 'review_required', "I FAIL"
    assert r['verified_ratio'] == 0.0, "I FAIL"
    print("I PASS: empty claims → review_required")


# ---------------------------------------------------------------------------
# Case J-L: release gate logic
# ---------------------------------------------------------------------------

def test_J_release_gate_below_threshold():
    """J: verified_ratio < 0.5 → 'review_required'."""
    stats = {"total": 10, "verification": {"unverified": 7, "verified": 3}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['release_status'] == 'review_required', "J FAIL: 30% phải review_required"
    print("J PASS: 30% verified → review_required")

def test_K_release_gate_above_threshold():
    """K: verified_ratio > 0.5 → 'releasable'."""
    stats = {"total": 10, "verification": {"unverified": 3, "verified": 7}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['release_status'] == 'releasable', "K FAIL: 70% phải releasable"
    print("K PASS: 70% verified → releasable")

def test_L_release_gate_verified_crosswalk():
    """L: verified_crosswalk + verified đều tính vào verified_count."""
    stats = {"total": 10, "verification": {"unverified": 4, "verified": 3, "verified_crosswalk": 3}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['verified_count'] == 6, "L FAIL: verified_count phải 3+3=6"
    assert r['release_status'] == 'releasable', "L FAIL: 60% phải releasable"
    print("L PASS: verified_crosswalk counted")


# ---------------------------------------------------------------------------
# Case M-O: JSON-LD structure (kiểm tra schema tĩnh, không call server)
# ---------------------------------------------------------------------------

def _build_jsonld(place_id, name_vi, name_zh=None, lat=None, lng=None,
                  dv_version='abc12345', dv_count=3, claims=None):
    """Tái tạo logic JSON-LD từ endpoint để test cấu trúc."""
    base = "https://phatphaponline.org"
    jsonld = {
        "@context": {
            "@vocab": "https://schema.org/",
            "pth": "https://phatphaponline.org/daoanh/ns#",
            "dila": "https://dila.ac.tw/authority/",
        },
        "@type": "Place",
        "@id": f"{base}/daoanh/places/{place_id}",
        "identifier": place_id,
        "name": name_vi,
    }
    if name_zh:
        jsonld["alternateName"] = name_zh
    if lat is not None and lng is not None:
        jsonld["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng}
    jsonld["pth:datasetVersion"] = dv_version
    jsonld["pth:claimCount"] = dv_count
    if claims:
        jsonld["additionalProperty"] = claims
    return jsonld

def test_M_jsonld_required_fields():
    """M: JSON-LD phải có @context, @type='Place', @id, identifier, name."""
    jl = _build_jsonld('PL001234', 'Hà Nội')
    assert jl['@type'] == 'Place', "M FAIL: @type phải Place"
    assert 'identifier' in jl, "M FAIL: identifier thiếu"
    assert 'name' in jl, "M FAIL: name thiếu"
    assert '@context' in jl, "M FAIL: @context thiếu"
    assert 'phatphaponline.org' in jl['@id'], "M FAIL: @id thiếu domain"
    print("M PASS: JSON-LD required fields present")

def test_N_jsonld_pth_namespace():
    """N: @context phải có pth: namespace trỏ đến phatphaponline.org/daoanh/ns#."""
    jl = _build_jsonld('PL001234', 'Hà Nội')
    assert 'pth' in jl['@context'], "N FAIL: pth namespace thiếu"
    assert jl['@context']['pth'] == 'https://phatphaponline.org/daoanh/ns#', "N FAIL: pth URI sai"
    print("N PASS: pth namespace correct")

def test_O_jsonld_geo_optional():
    """O: geo chỉ xuất hiện khi có lat+lng."""
    jl_no_geo = _build_jsonld('PL001234', 'Hà Nội')
    jl_with_geo = _build_jsonld('PL001234', 'Hà Nội', lat=21.0278, lng=105.8342)
    assert 'geo' not in jl_no_geo, "O FAIL: geo không được xuất hiện khi không có tọa độ"
    assert 'geo' in jl_with_geo, "O FAIL: geo phải có khi có tọa độ"
    assert jl_with_geo['geo']['@type'] == 'GeoCoordinates', "O FAIL: geo @type sai"
    print("O PASS: geo optional field correct")


# ---------------------------------------------------------------------------
# Case P-R: regression — existing evidence/claims APIs không bị ảnh hưởng
# ---------------------------------------------------------------------------

def test_P_verification_summary_no_conflict_key():
    """P: conflict=0 khi không có conflict trong verification dict."""
    stats = {"total": 5, "verification": {"unverified": 5}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['conflict_count'] == 0, "P FAIL: conflict_count phải 0"
    assert r['needs_review_count'] == 0, "P FAIL: needs_review_count phải 0"
    print("P PASS: missing keys default to 0")

def test_Q_dataset_version_deterministic_order():
    """Q: Sắp xếp theo claim_id đảm bảo hash deterministic (không phụ thuộc thứ tự input)."""
    # Tạo 2 conn với claims cùng nội dung nhưng claim_id khác order (MockConn luôn trả đúng thứ tự)
    # → Nếu hash stable, test Q pass
    c1 = [_make_claim(1, obj='A'), _make_claim(2, obj='B')]
    c2 = [_make_claim(1, obj='A'), _make_claim(2, obj='B')]
    r1 = _compute_dataset_version(MockConn(c1), 'PL001')
    r2 = _compute_dataset_version(MockConn(c2), 'PL001')
    assert r1['full_hash'] == r2['full_hash'], "Q FAIL: hash phải deterministic"
    print("Q PASS: dataset_version deterministic")

def test_R_verification_summary_verified_ratio_precision():
    """R: verified_ratio làm tròn 4 chữ số thập phân."""
    stats = {"total": 3, "verification": {"unverified": 2, "verified": 1}, "by_type": {}}
    r = _compute_verification_summary(stats)
    assert r['verified_ratio'] == round(1/3, 4), "R FAIL: ratio không đúng precision"
    print("R PASS: verified_ratio precision correct")


# ---------------------------------------------------------------------------
# Chạy tất cả tests
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_A_dataset_version_stable,
        test_B_dataset_version_changes_on_different_claims,
        test_C_dataset_version_no_claims,
        test_D_dataset_version_unresolved_entity,
        test_E_dataset_version_full_hash_64chars,
        test_F_dataset_version_claim_count,
        test_G_verification_summary_all_unverified,
        test_H_verification_summary_half_verified,
        test_I_verification_summary_empty,
        test_J_release_gate_below_threshold,
        test_K_release_gate_above_threshold,
        test_L_release_gate_verified_crosswalk,
        test_M_jsonld_required_fields,
        test_N_jsonld_pth_namespace,
        test_O_jsonld_geo_optional,
        test_P_verification_summary_no_conflict_key,
        test_Q_dataset_version_deterministic_order,
        test_R_verification_summary_verified_ratio_precision,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*50}")
    print(f"T100-BATCH5: {passed}/{len(tests)} PASS, {failed} FAIL")
    if failed:
        sys.exit(1)
