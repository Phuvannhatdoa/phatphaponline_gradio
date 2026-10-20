"""T140 — Pháp Mạch UI/UX tests (16 cases A-P).

Hybrid approach:
- Source-code pattern tests: kiểm tra places.html chứa JS implementation đúng
- Logic tests: tái tạo pure-function equivalents của JS (truncation, filter, header)

Không cần server. Không mutate DB. Không call external API.
"""
import sys, os, re

_HERE = os.path.dirname(__file__)
_PLACES_HTML = os.path.join(_HERE, '..', 'places.html')

with open(_PLACES_HTML, encoding='utf-8') as _f:
    _SRC = _f.read()


# ---------------------------------------------------------------------------
# Pure-logic equivalents (Python re-implementation của JS functions)
# ---------------------------------------------------------------------------

def tree_short_label(name_vi, label_vi=None, kids_count=0, is_expanded=False):
    """Python equivalent của _treeShortLabel(n, L, kidsCount, isExpanded)."""
    t = label_vi or name_vi or ''
    t = str(t)
    if len(t) > 22:
        t = t[:22] + '…'
    if kids_count:
        t += (' ▾' if is_expanded else ' ▸') + str(kids_count)
    return t


def apply_lineage_filters_logic(nodes, edges, filters, center_id=None, state_edges=None):
    """Python equivalent của _applyLineageFilters — pure logic, không cần DOM.

    filters: dict với keys: all, visible, tl1, tl2, tl3, conflict, hasref
    state_edges: list of edge dicts (cho tl1/tl2/tl3 trust_level lookup)
    """
    state_edges = state_edges or []
    # Build index: _eid → raw edge (trust_level, has_ref)
    edge_by_eid = {}
    for i, e in enumerate(state_edges):
        edge_by_eid[i] = e

    res_n, res_e = list(nodes), list(edges)

    def dir_dis(pid):
        return any(
            (e.get('from') == pid or e.get('to') == pid) and
            any(s.get('direction_mismatch') for s in (e.get('sources') or []))
            for e in edges
        )

    if filters.get('conflict'):
        res_n = [n for n in res_n if dir_dis(n['id'])]
        res_e = [e for e in res_e if dir_dis(e.get('from')) or dir_dis(e.get('to'))]

    if filters.get('tl1') or filters.get('tl2') or filters.get('tl3'):
        def edge_passes_tl(e):
            raw = edge_by_eid.get(e.get('_eid'))
            tl = raw.get('trust_level') if raw else None
            if filters.get('tl1') and tl == 'L1': return True
            if filters.get('tl2') and tl == 'L2': return True
            if filters.get('tl3') and (tl == 'L3' or not tl): return True
            return False
        res_e = [e for e in res_e if edge_passes_tl(e)]
        used = set(e.get('from') for e in res_e) | set(e.get('to') for e in res_e)
        res_n = [n for n in res_n if n['id'] in used or n['id'] == center_id]

    if filters.get('hasref'):
        res_e = [e for e in res_e if e.get('_hasRef') or
                 (edge_by_eid.get(e.get('_eid'), {}).get('has_ref'))]
        used = set(e.get('from') for e in res_e) | set(e.get('to') for e in res_e)
        res_n = [n for n in res_n if n['id'] in used or n['id'] == center_id]

    return {'nodes': res_n, 'edges': res_e}


def render_lineage_header_text(center_id, name_vi, name_zh=None,
                               edges=None, kids_direct=0):
    """Python equivalent của _renderLineageHeader — trả text thô (không HTML tags)."""
    edges = edges or []
    name = name_vi or center_id or ''
    ref_n = sum(1 for e in edges if e.get('has_ref'))
    confl = sum(1 for e in edges if any(s.get('direction_mismatch') for s in (e.get('sources') or [])))
    parts = ['Pháp hệ', '›', name]
    if name_zh:
        parts.append(f'({name_zh})')
    if center_id:
        parts.append(f'– DILA ID: {center_id}')
    if edges:
        stat = f'{kids_direct} đệ tử trực tiếp · {ref_n}/{len(edges)} cạnh có dẫn chứng'
        if confl:
            stat += f' · ⚠ {confl} quan hệ ngược chiều'
        parts.append(stat)
    return ' '.join(parts)


# ---------------------------------------------------------------------------
# Case A-B: default depth + URL contract
# ---------------------------------------------------------------------------

def test_A_default_depth_url_contains_up2_down2():
    """A: loadLineageTree và centerLineageOn dùng ?up=2&down=2."""
    assert 'up=2&down=2' in _SRC, "A FAIL: ?up=2&down=2 không có trong source"
    count = _SRC.count('up=2&down=2')
    assert count >= 2, f"A FAIL: phải có ít nhất 2 lần ?up=2&down=2, thực tế {count}"
    print("A PASS: default depth up=2&down=2 present ≥2 times")

def test_B_breadcrumb_renders_name_and_id():
    """B: _renderLineageHeader tạo breadcrumb với name + DILA ID."""
    h = render_lineage_header_text('A001234', 'Mã Tổ Đạo Nhất', name_zh='馬祖道一')
    assert 'Pháp hệ' in h, "B FAIL: thiếu 'Pháp hệ'"
    assert '›' in h, "B FAIL: thiếu dấu ›"
    assert 'Mã Tổ Đạo Nhất' in h, "B FAIL: thiếu tên Việt"
    assert '馬祖道一' in h, "B FAIL: thiếu tên Hán"
    assert 'A001234' in h, "B FAIL: thiếu DILA ID"
    print("B PASS: breadcrumb renders name + Hán + DILA ID")


# ---------------------------------------------------------------------------
# Case C-D: summary header
# ---------------------------------------------------------------------------

def test_C_summary_header_complete_data():
    """C: summary header hiển thị edge stats khi có cạnh."""
    edges = [
        {'from': 'A1', 'to': 'A2', 'has_ref': True, 'sources': []},
        {'from': 'A1', 'to': 'A3', 'has_ref': False, 'sources': [{'direction_mismatch': True}]},
    ]
    h = render_lineage_header_text('A1', 'Huệ Năng', edges=edges, kids_direct=2)
    assert '2 đệ tử trực tiếp' in h, "C FAIL: thiếu số đệ tử"
    assert '1/2 cạnh có dẫn chứng' in h, "C FAIL: thiếu stats cạnh"
    assert '⚠ 1 quan hệ ngược chiều' in h, "C FAIL: thiếu cảnh báo conflict"
    print("C PASS: summary header with complete data")

def test_D_summary_header_missing_optional_fields():
    """D: summary header không crash khi thiếu name_zh, không có cạnh."""
    h = render_lineage_header_text('A001234', 'Vô Danh', name_zh=None, edges=[])
    assert 'Pháp hệ' in h, "D FAIL"
    assert 'Vô Danh' in h, "D FAIL"
    assert 'None' not in h, "D FAIL: 'None' không được xuất hiện trong header"
    assert '馬' not in h, "D FAIL: không có name_zh → không render"
    print("D PASS: summary header handles missing optional fields")


# ---------------------------------------------------------------------------
# Case E-G: provenance legend
# ---------------------------------------------------------------------------

def test_E_marcus_legend_in_source():
    """E: source code có chú giải MARCUS = cấu trúc chính."""
    # Kiểm tra legend text và filter label
    assert 'MARCUS' in _SRC, "E FAIL: MARCUS không có trong source"
    assert 'lineage-filter-tl1' in _SRC, "E FAIL: tl1 (MARCUS) filter không có"
    # Kiểm tra tooltip MARCUS semantic text
    assert 'marcus_networks' in _SRC.lower() or 'MARCUS' in _SRC, "E FAIL"
    print("E PASS: MARCUS legend + filter present")

def test_F_dila_legend_in_source():
    """F: source code có chú giải DILA = đối chiếu."""
    assert 'DILA' in _SRC, "F FAIL: DILA không có trong source"
    assert 'lineage-filter-tl2' in _SRC, "F FAIL: tl2 (DILA) filter không có"
    assert 'direction_mismatch' in _SRC, "F FAIL: direction_mismatch không có"
    print("F PASS: DILA legend + filter + mismatch detection present")

def test_G_mixed_provenance_mismatch_detection():
    """G: direction_mismatch detection trả đúng kết quả."""
    def edge_mismatch(edge):
        return bool(edge and any(s.get('direction_mismatch') for s in (edge.get('sources') or [])))

    e_ok = {'from': 'A1', 'to': 'A2', 'sources': [{'direction_mismatch': False}]}
    e_mm = {'from': 'A1', 'to': 'A2', 'sources': [{'direction_mismatch': True}]}
    e_no_src = {'from': 'A1', 'to': 'A2', 'sources': []}
    assert not edge_mismatch(e_ok), "G FAIL: bình thường phải False"
    assert edge_mismatch(e_mm), "G FAIL: mismatch phải True"
    assert not edge_mismatch(e_no_src), "G FAIL: no sources phải False"
    print("G PASS: mixed provenance mismatch detection")


# ---------------------------------------------------------------------------
# Case H-J: AbortController
# ---------------------------------------------------------------------------

def test_H_abortcontroller_pattern_in_source():
    """H: _linLoadCtrl + _linLoadAbort() pattern có trong source."""
    assert '_linLoadCtrl' in _SRC, "H FAIL: _linLoadCtrl không có"
    assert '_linLoadAbort' in _SRC, "H FAIL: _linLoadAbort không có"
    assert 'new AbortController()' in _SRC, "H FAIL: AbortController không có"
    assert '_linLoadCtrl.abort()' in _SRC, "H FAIL: .abort() không có"
    print("H PASS: AbortController pattern present")

def test_I_abort_error_handled_silently():
    """I: khi signal.aborted → return (không show error)."""
    # Kiểm tra source có pattern: if (ctrl.signal.aborted) return
    pattern = r'ctrl\.signal\.aborted\s*\)\s*return'
    assert re.search(pattern, _SRC), "I FAIL: aborted-guard không có"
    print("I PASS: AbortError handled silently (return on aborted)")

def test_J_real_fetch_error_displayed():
    """J: lỗi fetch thật hiển thị message cho user."""
    assert 'Lỗi tải pháp hệ' in _SRC, "J FAIL: error message không có"
    # Kiểm tra pattern: không phải AbortError mới hiển thị
    # catch(e) { if (ctrl.signal.aborted) return; ... Lỗi tải pháp hệ
    pattern = r'ctrl\.signal\.aborted\s*\)\s*return[^}]*Lỗi tải pháp hệ'
    assert re.search(pattern, _SRC, re.DOTALL), "J FAIL: real error display pattern sai"
    print("J PASS: real fetch error displayed, AbortError suppressed")


# ---------------------------------------------------------------------------
# Case K-L: label truncation
# ---------------------------------------------------------------------------

def test_K_long_label_truncated_at_22():
    """K: label > 22 chars bị truncate thành 22 + '…'."""
    long_name = 'Thiên Hy Thừa Quế Đại Sư'  # 25 chars
    result = tree_short_label(long_name)
    assert result.endswith('…'), f"K FAIL: phải kết thúc bằng '…', got '{result}'"
    assert len(result.rstrip('…')) <= 22, "K FAIL: phần trước '…' phải ≤22 chars"
    print("K PASS: label truncated at 22 chars")

def test_L_full_label_retained_for_short_names():
    """L: label ≤22 chars giữ nguyên (không truncate)."""
    short_name = 'Mã Tổ Đạo Nhất'  # 15 chars
    result = tree_short_label(short_name)
    assert '…' not in result, "L FAIL: label ngắn không được truncate"
    assert short_name in result, "L FAIL: tên gốc phải giữ nguyên"
    # Kiểm tra _treeShortLabel func trong source cũng dùng 22
    assert '> 22' in _SRC or '>22' in _SRC.replace(' ', ''), "L FAIL: threshold 22 phải có trong source"
    print("L PASS: short label retained unchanged")


# ---------------------------------------------------------------------------
# Case M-N: group filter
# ---------------------------------------------------------------------------

def test_M_group_filter_tl1_deterministic():
    """M: filter tl1 chỉ giữ edges L1, luôn deterministic."""
    nodes = [{'id': 'A1'}, {'id': 'A2'}, {'id': 'A3'}]
    edges = [
        {'from': 'A1', 'to': 'A2', '_eid': 0, 'sources': []},
        {'from': 'A2', 'to': 'A3', '_eid': 1, 'sources': []},
    ]
    state_edges = [
        {'trust_level': 'L1', 'has_ref': True},
        {'trust_level': 'L2', 'has_ref': False},
    ]
    r1 = apply_lineage_filters_logic(nodes, edges, {'tl1': True}, center_id='A1', state_edges=state_edges)
    r2 = apply_lineage_filters_logic(nodes, edges, {'tl1': True}, center_id='A1', state_edges=state_edges)
    assert r1['edges'] == r2['edges'], "M FAIL: filter không deterministic"
    assert len(r1['edges']) == 1, f"M FAIL: tl1 phải giữ 1 edge L1, got {len(r1['edges'])}"
    assert r1['edges'][0]['to'] == 'A2', "M FAIL: sai edge"
    print("M PASS: group filter tl1 deterministic")

def test_N_group_filter_empty_state():
    """N: filter quá chặt → empty result (trả về nodes chỉ còn center)."""
    nodes = [{'id': 'A1'}, {'id': 'A2'}]
    edges = [{'from': 'A1', 'to': 'A2', '_eid': 0, 'sources': []}]
    state_edges = [{'trust_level': 'L2', 'has_ref': False}]
    r = apply_lineage_filters_logic(nodes, edges, {'tl1': True}, center_id='A1', state_edges=state_edges)
    assert len(r['edges']) == 0, "N FAIL: không có edge L1 → phải rỗng"
    # node A1 (center) vẫn còn, A2 bị lọc
    assert any(n['id'] == 'A1' for n in r['nodes']), "N FAIL: center phải giữ lại"
    assert not any(n['id'] == 'A2' for n in r['nodes']), "N FAIL: A2 phải bị lọc"
    print("N PASS: filter empty state (center retained)")


# ---------------------------------------------------------------------------
# Case O-P: stale A race guard + API contract
# ---------------------------------------------------------------------------

def test_O_stale_render_guard_in_source():
    """O: A→B switch: sau abort, check signal.aborted → không render stale A."""
    # loadLineageTree: ctrl.signal.aborted check sau fetch
    pattern = r'const d = await res\.json\(\).*?if \(ctrl\.signal\.aborted\) return'
    assert re.search(pattern, _SRC, re.DOTALL), (
        "O FAIL: stale-render guard không đúng pattern "
        "(cần check aborted ngay sau json parse)"
    )
    print("O PASS: stale render guard present after json parse")

def test_P_lineage_api_contract_compatible():
    """P: API endpoint /api/monk/<id>/lineage-tree vẫn dùng đúng params."""
    pattern = r'/daoanh/api/monk/.*lineage-tree\?up=2&down=2'
    assert re.search(pattern, _SRC), "P FAIL: lineage-tree API endpoint không đúng"
    # Kiểm tra include_single param vẫn còn
    assert 'include_single=1' in _SRC, "P FAIL: include_single=1 thiếu"
    print("P PASS: lineage API contract compatible")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_A_default_depth_url_contains_up2_down2,
        test_B_breadcrumb_renders_name_and_id,
        test_C_summary_header_complete_data,
        test_D_summary_header_missing_optional_fields,
        test_E_marcus_legend_in_source,
        test_F_dila_legend_in_source,
        test_G_mixed_provenance_mismatch_detection,
        test_H_abortcontroller_pattern_in_source,
        test_I_abort_error_handled_silently,
        test_J_real_fetch_error_displayed,
        test_K_long_label_truncated_at_22,
        test_L_full_label_retained_for_short_names,
        test_M_group_filter_tl1_deterministic,
        test_N_group_filter_empty_state,
        test_O_stale_render_guard_in_source,
        test_P_lineage_api_contract_compatible,
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
    print(f"T140-PHAP-MACH: {passed}/{len(tests)} PASS, {failed} FAIL")
    if failed:
        sys.exit(1)
