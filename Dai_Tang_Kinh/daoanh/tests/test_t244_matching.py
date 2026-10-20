# -*- coding: utf-8 -*-
"""T244 — Matching Engine matchGeographicSites tests.

Chạy ego:    python -X utf8 tests/test_t244_matching.py
Không mạng, không đụng DB thật (fixture site dicts thuần).
Coverage:
  [K1] haversine_km       : 0 tại trùng tọa độ; ~1.600km Hà Nội→Sài Gòn
  [K2] spatial_score      : 1 ở ≤2km; 0 ở ≥25km; tuyến tính giữa; None→0
  [K3] name_similarity    : trùng khóa VN/hán → cao; khác → thấp; band 0,857
  [K4] score_pair         : khớp đúng công thức 0,5/0,3/0,2 (+0,2 Hán, cốc 1,0)
  [K5] auto zh≤2km        : trùng chữ Hán + ≤2km → auto
  [K6] auto admin≤10km    : một bên tâm hành chính + ≤10km → auto
  [K7] queue dist 2–25km  : khoảng cách 2–25 → queue
  [K8] queue name band    : độ giống tên 0,85–0,95 → queue
  [K9] reject >25km       : KHÔNG BAO GIỜ auto vượt 25km
  [K10] reject dưới ngưỡng: không đạt tiêu chí nào → reject
  [K11] VN gate           : raw auto → final queue (auto vô hiệu VN)
  [K12] collision         : 2 cặp auto chung tọa độ → demote queue
  [K13] matchGeographicSites: end-to-end (gate on/off, seen-dedup)
  [K14] eval precision/coverage: đúng TP/FP/FN trên mẫu nhãn
  [K15] type_period       : cùng loại/trùng thời kỳ → 1; tách biệt → 0,4; rỗng → 0,5
"""

import importlib.util
import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_DAOANH, 'scripts')


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_SCRIPTS, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load('vn_t244', 'vn_places_t244_matching.py')

_SITE = {
    'id': 'S1', 'name_vi': 'Trấn Quốc', 'name_zh': '', 'hanvi': '', 'pinyin': '',
    'lat': 21.0333, 'lon': 105.85, 'place_type': 'temple', 'period': '',
    'country': 'VN', 'admin_centroid': False,
}


def _site(**kw):
    s = dict(_SITE)
    s.update(kw)
    return s


def test_haversine():
    assert M.haversine_km(21.0333, 105.85, 21.0333, 105.85) == 0.0
    d = M.haversine_km(21.0333, 105.85, 10.78, 106.68)   # Hà Nội → Sài Gòn
    assert 1100 < d < 1200, d
    assert M.haversine_km(None, 105.85, 21.0, 105.8) is None


def test_spatial_score():
    assert M.spatial_score(None) == 0.0
    assert M.spatial_score(0.0) == 1.0
    assert M.spatial_score(2.0) == 1.0
    assert M.spatial_score(13.5) == 0.5            # tuyến tính (25-2)
    assert M.spatial_score(25.0) == 0.0
    assert M.spatial_score(40.0) == 0.0


def test_name_similarity():
    a = _site(name_vi='Chùa Trấn Quốc')
    b = _site(name_vi='Trấn Quốc')
    fa, fb = M.name_features(a), M.name_features(b)
    assert M.name_similarity(fa, fb) >= 0.9        # stripped khớp
    assert M.name_similarity(fa, fa) == 1.0
    # Hán trùng
    c = _site(name_vi='Chùa X', name_zh='金剛寺', hanvi='kim cương tự', pinyin='jin gang si')
    d = _site(name_vi='Chùa Y', name_zh='金剛寺', hanvi='kim cương tự', pinyin='jin gang si')
    assert M.name_similarity(M.name_features(c), M.name_features(d)) == 1.0
    # không liên quan
    e = _site(name_vi='Chùa Aaa Bbb', name_zh='鎮國寺', hanvi='trấn quốc tự', pinyin='zhen guo si')
    f = _site(name_vi='Chùa Ccc Ddd', name_zh='金剛寺',
              hanvi='kim cương tự', pinyin='jin gang si')
    assert M.name_similarity(M.name_features(e), M.name_features(f)) < 0.6


def test_score_formula():
    a = _site(id='A', name_vi='Trấn Quốc', name_zh='鎮國寺', period='500-750',
              lat=21.0, lon=105.8)
    b = _site(id='B', name_vi='Trấn Quốc', name_zh='鎮國寺', period='600-800',
              lat=21.0, lon=105.8)
    fa, fb = M.name_features(a), M.name_features(b)
    score, name, space, tp, zh = M.score_pair(a, b, fa, fb, 0.5)
    assert name == 1.0 and space == 1.0 and tp == 1.0 and zh is True
    assert score == 1.0                              # 0,5+0,3+0,2 (+0,2 Hán cap 1,0)
    # không Hán: name 1,0 · dist 10,5km (space≈0,6304) · tp 0,75 (period rỗng)
    # → 0,5·1 + 0,3·space + 0,2·0,75
    c = _site(id='C', name_vi='Chùa A', name_zh='', lat=21.0, lon=105.8)
    d = _site(id='D', name_vi='Chùa A', name_zh='', lat=21.0, lon=105.9)
    fc, fd = M.name_features(c), M.name_features(d)
    dist = M.haversine_km(21.0, 105.8, 21.0, 105.9)  # ~10,5km
    score2, name2, space2, tp2, zh2 = M.score_pair(c, d, fc, fd, 10.5)
    expect = 0.5 * 1.0 + 0.3 * M.spatial_score(10.5) + 0.2 * M.type_period_score(c, d)
    assert abs(score2 - expect) < 1e-3, (score2, expect)


def test_auto_zh_le_2km():
    a = _site(name_vi='Chùa Kim Cương', name_zh='金剛寺', lat=21.0, lon=105.8)
    b = _site(name_vi='Kim Cương', name_zh='金剛寺', lat=21.01, lon=105.81, id='B')
    fa, fb = M.name_features(a), M.name_features(b)
    m = M.decide(a, b, fa, fb, 1.5)
    assert m['decision'] == 'auto' and m['reason'] == 'zh_exact_le_2km'


def test_auto_admin_le_10km():
    a = _site(name_vi='Chùa Xa', name_zh='', lat=21.0, lon=105.8, admin_centroid=True)
    b = _site(name_vi='Một Địa Điểm Hoàn Toàn Khác', name_zh='', lat=21.05, lon=105.83, id='B')
    fa, fb = M.name_features(a), M.name_features(b)
    m = M.decide(a, b, fa, fb, 5.0)
    assert m['decision'] == 'auto' and m['reason'] == 'admin_centroid_le_10km'


def test_queue_dist_band():
    a = _site(name_vi='Chùa Một Cột', name_zh='', lat=21.0333, lon=105.8333)
    b = _site(name_vi='Chùa Một Cột', name_zh='', lat=21.12, lon=105.85, id='B')  # ~10km
    fa, fb = M.name_features(a), M.name_features(b)
    m = M.decide(a, b, fa, fb, 10.0)
    assert m['decision'] == 'queue' and m['reason'] == 'dist_2_25km'


def test_queue_name_band():
    # A: name_vi khác phiên âm, nhưng chữ Hán nòng giống 0,857 (6/7) → band 0,85–0,95
    a = _site(name_vi='Chùa Xyz Aaa', name_zh='佛說無量壽經寺', lat=21.0, lon=105.8)
    b = _site(name_vi='Chùa Qwe Bbb', name_zh='佛說無量壽經', lat=21.005, lon=105.805, id='B')
    fa, fb = M.name_features(a), M.name_features(b)
    assert abs(M.name_similarity(fa, fb) - (6 / 7)) < 1e-9
    m = M.decide(a, b, fa, fb, 1.0)
    assert m['decision'] == 'queue' and m['reason'] == 'name_0.85_0.95'


def test_reject_gt_25km():
    a = _site(name_vi='Chùa Trấn Quốc', name_zh='鎮國寺', lat=21.0333, lon=105.85)
    b = _site(name_vi='Trấn Quốc', name_zh='鎮國寺', lat=21.4, lon=106.0, id='B')  # ~43km
    fa, fb = M.name_features(a), M.name_features(b)
    m = M.decide(a, b, fa, fb, 43.0)
    assert m['decision'] == 'reject' and m['reason'] == 'dist_gt_25'


def test_reject_below_threshold():
    a = _site(name_vi='Chùa Aaa', name_zh='', lat=21.0, lon=105.8)
    b = _site(name_vi='Chùa Bbb', name_zh='', lat=21.002, lon=105.802, id='B')
    fa, fb = M.name_features(a), M.name_features(b)
    m = M.decide(a, b, fa, fb, 0.3)
    assert m['decision'] == 'reject' and m['reason'] == 'below_threshold'


def test_vn_gate():
    a = _site(name_vi='Chùa Kim Cương', name_zh='金剛寺', lat=21.0, lon=105.8)
    b = _site(name_vi='Kim Cương', name_zh='金剛寺', lat=21.01, lon=105.81, id='B')
    results = [M.decide(a, b, M.name_features(a), M.name_features(b), 1.5)]
    M.apply_vn_gate(results, enabled=True)
    assert results[0]['raw_decision'] == 'auto'
    assert results[0]['decision'] == 'queue' and results[0]['reason'] == 'vn_gate_auto_disabled'


def test_collision_same_coord():
    b = _site(id='B', name_vi='Kim Cương', name_zh='金剛寺', lat=21.0, lon=105.8)
    a1 = _site(id='A1', name_vi='Chùa Kim Cương', name_zh='金剛寺', lat=20.99, lon=105.79)
    a2 = _site(id='A2', name_vi='Chùa Kim Cương B', name_zh='金剛寺', lat=21.01, lon=105.81)
    results = [M.decide(a1, b, M.name_features(a1), M.name_features(b), 1.4),
               M.decide(a2, b, M.name_features(a2), M.name_features(b), 1.4)]
    assert all(r['decision'] == 'auto' for r in results)
    M.apply_collision(results)
    assert all(r['decision'] == 'queue' and r.get('collision') for r in results)


def test_match_geographic_sites_e2e():
    sites_a = [_site(id='A1', name_vi='Chùa Trấn Quốc', name_zh='鎮國寺',
                     lat=21.0333, lon=105.85)]
    sites_b = [_site(id='B1', name_vi='Trấn Quốc', name_zh='鎮國寺',
                     lat=21.033, lon=105.8501),
               _site(id='B2', name_vi='Chùa Không Liên Quan', name_zh='',
                     lat=20.5, lon=106.0)]
    out = M.match_geographic_sites(sites_a, sites_b, {'vn_gate': True})
    assert len(out) >= 1
    for m in out:
        if m['b_id'] == 'B1':
            assert m['raw_decision'] == 'auto'
            assert m['decision'] == 'queue' and m['vn_gate'] is True   # gate VN
        else:
            assert m['decision'] == 'reject'
    # gate tắt → auto thật
    out2 = M.match_geographic_sites(sites_a, sites_b[:1], {'vn_gate': False})
    assert out2[0]['decision'] == 'auto'


def test_eval_precision_coverage():
    labels = {'labels': [
        {'a_id': 'A1', 'b_id': 'B1', 'label': 'accept'},
        {'a_id': 'A2', 'b_id': 'B2', 'label': 'accept'},
        {'a_id': 'A3', 'b_id': 'B3', 'label': 'reject'},
    ], 'pairs': {
        'A1|B1': {'a_id': 'A1', 'b_id': 'B1', 'raw_decision': 'auto', 'final_decision': 'queue'},
        'A2|B2': {'a_id': 'A2', 'b_id': 'B2', 'raw_decision': 'queue', 'final_decision': 'queue'},
        'A3|B3': {'a_id': 'A3', 'b_id': 'B3', 'raw_decision': 'auto', 'final_decision': 'queue'},
    }}
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(labels, f, ensure_ascii=False)
    try:
        rep = M.eval_sample(path)
        assert rep['tp'] == 1 and rep['fp'] == 1 and rep['fn'] == 1
        assert rep['precision'] == 0.5 and rep['coverage'] == 0.5
    finally:
        os.remove(path)


def test_type_period():
    a = _site(place_type='temple', period='618-907')
    b = _site(place_type='temple', period='700-750')
    assert M.type_period_score(a, b) == 1.0          # cùng loại + trùng thời kỳ
    a2 = _site(place_type='temple', period='500-600')
    b2 = _site(place_type='temple', period='700-750')
    assert M.type_period_score(a2, b2) == 0.5 * 1.0 + 0.5 * 0.4
    a3 = _site(place_type='', period='618-907')
    b3 = _site(place_type='monastery', period='')
    assert M.type_period_score(a3, b3) == 0.5 * 0.3 + 0.5 * 0.5


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    n = 0
    for fn in fns:
        fn()
        n += 1
    print('T244 PASS %d/%d' % (n, n))
    return 0


if __name__ == '__main__':
    sys.exit(_run())