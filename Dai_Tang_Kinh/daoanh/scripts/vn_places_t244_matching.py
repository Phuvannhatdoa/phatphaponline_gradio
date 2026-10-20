# -*- coding: utf-8 -*-
"""T244 (M7 GIS VN/Global) — Matching Engine `matchGeographicSites`.

Gán auto / queue / reject cho cặp địa điểm theo đúng M7 §Logic Khớp:
  - Điểm = 0,5·tên + 0,3·không gian + 0,2·loại&thời kỳ; trùng chữ Hán hoàn toàn +0,2.
  - Auto : trùng chữ Hán và ≤2 km, HOẶC ≤10 km khi một bên là tâm hành chính.
  - Queue: khoảng cách 2–25 km, HOẶC độ giống tên 0,85–0,95.
  - >25 km: KHÔNG BAO GIỜ tự liên kết.
  - Va chạm (nhiều chùa chung tọa độ) → buộc duyệt tay (queue), không chọn ngầm.
  - Bản Việt Nam: tự động linking VÔ HIỆU đến khi có ≥200 cặp ground truth (gate `vn_gate`).

Công cụ chạy thật:
  python -X utf8 scripts/vn_places_t244_matching.py --build-candidates [--limit-a N]
  python -X utf8 scripts/vn_places_t244_matching.py --eval <labels.json> [--report out.json]
  python -X utf8 scripts/vn_places_t244_matching.py --smoke
  --db=<path>  (mặc định data/lineage.db) · --bb=minlat,maxlat,minlon,maxlon (mặc định bbox VN)

TÍNH CHẤT:
  - Pure/non-mutating: không sửa DB, chỉ đọc + xuất JSON (additive, revert = xóa file).
  - Zero-RAM: pipeline đọc theo generator; candidate giới hạn theo lưới ô.
"""

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)
try:
    from vn_places_name_utils import nfkc, vn_key
except ImportError:
    sys.path.insert(0, _HERE)
    from vn_places_name_utils import nfkc, vn_key  # noqa: F401

DEFAULT_DB = os.path.join(_DAOANH, 'data', 'lineage.db')
DEFAULT_CANDIDATES = os.path.join(_DAOANH, 'data', 't244_sample_pairs.json')
DEFAULT_REPORT = os.path.join(_DAOANH, 'data', 't244_matching_report.json')
VN_BBOX = (8.0, 24.0, 102.0, 110.0)

# ── Trọng số / ngưỡng (M7 §Logic, SSOT) ─────────────────────────────────────
W_NAME, W_SPATIAL, W_TYPE_PERIOD = 0.5, 0.3, 0.2
HAN_EXACT_BONUS = 0.2
DIST_AUTO_HAN_KM = 2.0
DIST_AUTO_ADMIN_KM = 10.0
DIST_QUEUE_MIN_KM = 2.0
DIST_QUEUE_MAX_KM = 25.0
NAME_QUEUE_LO, NAME_QUEUE_HI = 0.85, 0.95
EARTH_R = 6371.0088

# ── Khoảng cách ─────────────────────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2):
    """Haversine km; None nếu thiếu tọa độ."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return EARTH_R * 2 * math.asin(math.sqrt(min(1.0, a)))


def spatial_score(dist_km):
    """1 ở ≤2km; giảm tuyến tính, 0 ở ≥25km."""
    if dist_km is None:
        return 0.0
    if dist_km <= DIST_AUTO_HAN_KM:
        return 1.0
    if dist_km >= DIST_QUEUE_MAX_KM:
        return 0.0
    return 1.0 - (dist_km - DIST_AUTO_HAN_KM) / (DIST_QUEUE_MAX_KM - DIST_AUTO_HAN_KM)


# ── Tên (đặc trưng + độ giống) ──────────────────────────────────────────────

def name_features(site):
    name_vi = site.get('name_vi') or ''
    name_zh = site.get('name_zh') or ''
    return {
        'zh': nfkc(name_zh),
        'vn_full': vn_key(name_vi, stripped=False),
        'vn_stripped': vn_key(name_vi, stripped=True),
        'hanvi': nfkc(site.get('hanvi') or ''),
        'pinyin': nfkc(site.get('pinyin') or ''),
    }


def _token_sim(a, b):
    if not a or not b:
        return 0.0
    ta = a.split()
    tb = b.split()
    if not ta or not tb:
        sa, sb = set(a), set(b)
        return (len(sa & sb) / len(sa | sb)) if (sa | sb) else 0.0
    return len(set(ta) & set(tb)) / len(set(ta) | set(tb))


def _char_seq_sim(a, b):
    if not a or not b:
        return 0.0
    return sum(1 for ca, cb in zip(a, b) if ca == cb) / max(len(a), len(b))


def name_similarity(fa, fb):
    """Độ giống tên 0..1: max(vi→ đầy đủ/stripped, Hán, hanvi, pinyin)."""
    sim_vn = max(_token_sim(fa['vn_full'], fb['vn_full']),
                 _token_sim(fa['vn_stripped'], fb['vn_stripped']))
    zh = 0.0
    if fa['zh'] and fb['zh']:
        if fa['zh'] == fb['zh']:
            zh = 1.0
        else:
            zh = max(_char_seq_sim(fa['zh'], fb['zh']), _token_sim(fa['zh'], fb['zh']))
    hv = _token_sim(fa['hanvi'], fb['hanvi']) * 0.9 if (fa['hanvi'] and fb['hanvi']) else 0.0
    py = _token_sim(fa['pinyin'], fb['pinyin']) * 0.9 if (fa['pinyin'] and fb['pinyin']) else 0.0
    return max(sim_vn, zh, hv, py)


# ── Loại & thời kỳ ──────────────────────────────────────────────────────────

_TEMPLE_FAMILY = {'temple', 'chua', 'tu', 'pagoda', 'monastery',
                  'tinh xa', 'thien vien'}


def _type_match(a, b):
    ta = (a.get('place_type') or '').strip().lower()
    tb = (b.get('place_type') or '').strip().lower()
    if not ta and not tb:
        return 1.0
    if ta == tb:
        return 1.0
    fam_a, fam_b = ta in _TEMPLE_FAMILY, tb in _TEMPLE_FAMILY
    if fam_a and fam_b:
        return 0.8
    return 0.3


def _period_overlap(a, b):
    pa, pb = a.get('period') or '', b.get('period') or ''
    if not pa or not pb:
        return 0.5
    ra, rb = _year_range(pa), _year_range(pb)
    if ra is None or rb is None:
        return 0.5
    return 1.0 if max(ra[0], rb[0]) <= min(ra[1], rb[1]) else 0.4


def _year_range(s):
    m = re.findall(r'(\d{3,4})\D+(\d{3,4})', s)
    if m:
        return (int(m[0][0]), int(m[0][1]))
    m = re.findall(r'(\d{3,4})', s)
    if len(m) >= 2:
        return (int(m[0]), int(m[1]))
    return None


def type_period_score(a, b):
    return 0.5 * _type_match(a, b) + 0.5 * _period_overlap(a, b)


# ── Điểm + quyết định ───────────────────────────────────────────────────────

def score_pair(a, b, fa, fb, dist_km):
    name = name_similarity(fa, fb)
    space = spatial_score(dist_km)
    tp = type_period_score(a, b)
    score = W_NAME * name + W_SPATIAL * space + W_TYPE_PERIOD * tp
    zh_exact = bool(fa['zh'] and fa['zh'] == fb['zh'])
    if zh_exact:
        score += HAN_EXACT_BONUS
    return min(1.0, score), name, space, tp, zh_exact


def decide(a, b, fa, fb, dist_km):
    """Raw decision (chưa gate VN, chưa collision)."""
    score, name, space, tp, zh_exact = score_pair(a, b, fa, fb, dist_km)
    d = {
        'a_id': a.get('id'), 'b_id': b.get('id'),
        'score': round(score, 4), 'name_sim': round(name, 4),
        'space': round(space, 4), 'type_period': round(tp, 4),
        'zh_exact': zh_exact,
        'dist_km': None if dist_km is None else round(dist_km, 3),
        'b_lat': b.get('lat'), 'b_lon': b.get('lon'),
        'country': a.get('country') or b.get('country') or 'VN',
    }
    if dist_km is None or dist_km > DIST_QUEUE_MAX_KM:
        d['decision'] = 'reject'
        d['reason'] = 'dist_gt_25' if dist_km else 'no_coords'
        return d
    admin = bool(a.get('admin_centroid') or b.get('admin_centroid'))
    if (zh_exact and dist_km <= DIST_AUTO_HAN_KM) or (admin and dist_km <= DIST_AUTO_ADMIN_KM):
        d['decision'] = 'auto'
        d['reason'] = 'zh_exact_le_2km' if zh_exact else 'admin_centroid_le_10km'
    elif (DIST_QUEUE_MIN_KM < dist_km <= DIST_QUEUE_MAX_KM) or \
         (NAME_QUEUE_LO <= name <= NAME_QUEUE_HI):
        d['decision'] = 'queue'
        d['reason'] = 'dist_2_25km' if (DIST_QUEUE_MIN_KM < dist_km <=
                                        DIST_QUEUE_MAX_KM) else 'name_0.85_0.95'
    else:
        d['decision'] = 'reject'
        d['reason'] = 'below_threshold'
    return d


def apply_collision(results):
    """≥2 cặp auto chung một tọa độ (ref) → demote queue, buộc duyệt tay."""
    group = defaultdict(list)
    for m in results:
        if m['b_lat'] is None or m['b_lon'] is None:
            continue
        group[(round(m['b_lat'], 6), round(m['b_lon'], 6))].append(m)
    for members in group.values():
        auto = [m for m in members if m['decision'] == 'auto']
        if len(auto) >= 2:
            for m in auto:
                m['decision'] = 'queue'
                m['reason'] = 'collision_same_coord'
                m['collision'] = True


def apply_vn_gate(results, enabled=True):
    """VN gate: auto → queue (chờ ≥200 cặp ground truth). Ghi raw_decision trước gate."""
    for m in results:
        if 'raw_decision' not in m:
            m['raw_decision'] = m['decision']
            m['raw_reason'] = m['reason']
        if enabled and m['country'] == 'VN' and m['decision'] == 'auto':
            m['decision'] = 'queue'
            m['reason'] = 'vn_gate_auto_disabled'
            m['vn_gate'] = True


def match_geographic_sites(sites_a, sites_b, opts=None):
    """matchGeographicSites(sites): khớp A(nguồn) × B(tham chiếu).

    opts: vn_gate (bật mặc định). Trả list dict mỗi cặp (auto|queue|reject);
    va chạm cùng tọa độ demote auto→queue; gate VN demote auto→queue.
    """
    opts = opts or {}
    fa_map = {id(a): name_features(a) for a in sites_a}
    by_id = {id(b): b for b in sites_b}
    fb_map = {id(b): name_features(b) for b in sites_b}
    key_buckets = defaultdict(list)
    for b in sites_b:
        fb = fb_map[id(b)]
        for k in set(filter(None, (fb['vn_full'], fb['vn_stripped']))):
            key_buckets[k].append(id(b))

    results, seen = [], set()
    for a in sites_a:
        fa = fa_map[id(a)]
        lat, lon = a.get('lat'), a.get('lon')
        cand_ids = set()
        for k in set(filter(None, (fa['vn_full'], fa['vn_stripped']))):
            cand_ids.update(key_buckets.get(k, ()))
        for bid, b in by_id.items():
            if b.get('lat') is not None and b.get('lon') is not None:
                d = haversine_km(lat, lon, b['lat'], b['lon'])
                if d is not None and d <= DIST_QUEUE_MAX_KM:
                    cand_ids.add(bid)
        for bid in cand_ids:
            key = (a.get('id'), by_id[bid].get('id'))
            if key in seen:
                continue
            seen.add(key)
            b = by_id[bid]
            dist = haversine_km(lat, lon, b.get('lat'), b.get('lon'))
            if dist is None or dist <= DIST_QUEUE_MAX_KM:
                results.append(decide(a, b, fa, fb_map[bid], dist))
    apply_collision(results)
    apply_vn_gate(results, enabled=opts.get('vn_gate', True))
    return results


# ── Chạy thật trên DB ───────────────────────────────────────────────────────

def load_places_vn(conn):
    cur = conn.execute(
        'SELECT id, name_vi, name_zh, geo_lat, geo_long, district, source '
        'FROM places_vn WHERE geo_lat IS NOT NULL AND geo_long IS NOT NULL')
    out = []
    for rid, name_vi, name_zh, lat, lon, district, src in cur:
        out.append({'id': 'VN|' + rid, 'name_vi': name_vi, 'name_zh': name_zh or '',
                    'lat': lat, 'lon': lon, 'country': 'VN',
                    'place_type': 'temple', 'period': '',
                    'source_label': src, 'admin_centroid': False,
                    'district': district or ''})
    return out


def load_dila_ref(conn, bbox=VN_BBOX):
    minlat, maxlat, minlon, maxlon = bbox
    ids = [r[0] for r in conn.execute(
        'SELECT id FROM places_dila '
        'WHERE geo_lat BETWEEN ? AND ? AND geo_long BETWEEN ? AND ?',
        (minlat, maxlat, minlon, maxlon))]
    if not ids:
        return []
    ph = ','.join('?' * len(ids))
    name_vi = dict(conn.execute(
        'SELECT dila_id, MIN(name_vi) FROM namevi_map_places '
        'WHERE dila_id IN (%s) AND name_vi IS NOT NULL AND name_vi != \'\' '
        'GROUP BY dila_id' % ph, ids))
    hv = {}
    for dila_id, hanvi, pinyin in conn.execute(
            'SELECT dila_id, hanvi, pinyin FROM place_norm_keys '
            'WHERE name_role=\'dila_zh\' AND dila_id IN (%s)' % ph, ids):
        hv[dila_id] = (hanvi, pinyin)
    out = []
    for rid, name, name_zh, district, lat, lon in conn.execute(
            'SELECT id, name, name_zh, district, geo_lat, geo_long FROM places_dila '
            'WHERE id IN (%s)' % ph, ids):
        h, p = hv.get(rid, (None, None))
        out.append({'id': 'PL|' + rid, 'name_vi': name_vi.get(rid, ''),
                    'name_zh': name_zh or name or '', 'lat': lat, 'lon': lon,
                    'country': 'VN', 'place_type': 'temple', 'period': '',
                    'hanvi': h or '', 'pinyin': p or '', 'admin_centroid': False,
                    'district': district or ''})
    return out


def build_candidates(conn, bbox=VN_BBOX, limit_a=None, cap_per_a=60):
    """Khớp places_vn × places_dila(VN) bounded per-A; trả (results, sites_a, ref)."""
    t0 = time.time()
    sites_a = load_places_vn(conn)
    ref = load_dila_ref(conn, bbox)
    if limit_a and limit_a < len(sites_a):
        sites_a = sites_a[:limit_a]
    print('places_vn: %d | places_dila ref (bbox): %d' % (len(sites_a), len(ref)))
    fb_cache = [name_features(b) for b in ref]

    results = []
    for i, a in enumerate(sites_a):
        fa = name_features(a)
        key_ids = set()
        for j, fb in enumerate(fb_cache):
            if fa['vn_full'] and (fb['vn_full'] == fa['vn_full'] or
                                  fb['vn_stripped'] == fa['vn_full']):
                key_ids.add(j)
            if fa['vn_stripped'] and (fb['vn_stripped'] == fa['vn_stripped'] or
                                      fb['vn_full'] == fa['vn_stripped']):
                key_ids.add(j)
        near = []
        for j, b in enumerate(ref):
            d = haversine_km(a['lat'], a['lon'], b['lat'], b['lon'])
            if d is not None and d <= DIST_QUEUE_MAX_KM:
                near.append((d, j))
        near.sort(key=lambda t: t[0])
        keep = list(key_ids) + [j for _, j in near if j not in key_ids]
        if cap_per_a and len(keep) > cap_per_a:
            keep = keep[:cap_per_a]
        for j in keep:
            b = ref[j]
            dist = haversine_km(a['lat'], a['lon'], b['lat'], b['lon'])
            if dist is None:
                continue
            results.append(decide(a, b, fa, fb_cache[j], dist))
        if (i + 1) % 2000 == 0:
            print('  processed %d/%d (pairs=%d, %.1fs)' % (
                i + 1, len(sites_a), len(results), time.time() - t0))
    return results, sites_a, ref


def _sample_write(results, out_path):
    apply_collision(results)          # demote auto → queue khi va chạm (trước gate)
    apply_vn_gate(results, enabled=True)
    rng = random.Random(20261007)
    bucket = defaultdict(list)
    for m in results:
        bk = (m.get('collision') and 'collision') or \
             (m['raw_decision'] == 'auto' and 'auto') or \
             (m['raw_reason'] == 'name_0.85_0.95' and 'name_band') or \
             (0.5 <= m['name_sim'] < NAME_QUEUE_LO and 'name_low') or \
             (m['raw_decision'] == 'queue' and 'queue') or 'reject'
        bucket[bk].append(m)
    caps = {'collision': 60, 'auto': 120, 'name_band': 600, 'name_low': 300,
            'queue': 300, 'reject': 80}
    rows, pairs = [], {}
    for bk in ('collision', 'auto', 'name_band', 'name_low', 'queue', 'reject'):
        members = bucket.get(bk, [])
        rng.shuffle(members)
        for m in members[:caps.get(bk, 0)]:
            if m['raw_decision'] == 'reject' and m['name_sim'] < 0.5:
                continue
            rid = '%s|%s' % (m['a_id'], m['b_id'])
            rows.append({'a_id': m['a_id'], 'b_id': m['b_id'], 'label': '',
                         'sampled_from': bk})
            pairs[rid] = {'a_id': m['a_id'], 'b_id': m['b_id'],
                          'score': m['score'], 'name_sim': m['name_sim'],
                          'dist_km': m['dist_km'], 'reason': m['raw_reason'],
                          'raw_decision': m['raw_decision'],
                          'final_decision': m['decision']}
    out = {'engine': 'T244 matchGeographicSites',
           'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
           'note': 'label ∈ {accept,reject,later}; <200 cặp ground truth thì VN gate vô hiệu auto',
           'n_pairs': len(rows), 'labels': rows, 'pairs': pairs}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('[OK] sample:', os.path.basename(out_path), '| rows:', len(rows))
    return out


def _report_stats(results, out_path=None):
    apply_collision(results)
    apply_vn_gate(results, enabled=True)
    auto_gt25 = [m for m in results if m['raw_decision'] == 'auto' and m['dist_km'] and
                 m['dist_km'] > DIST_QUEUE_MAX_KM]
    stats = defaultdict(int)
    for m in results:
        stats['raw_' + m['raw_decision']] += 1
        stats['final_' + m['decision']] += 1
        if m.get('collision'):
            stats['collision_same_coord'] += 1
        if m.get('vn_gate'):
            stats['vn_gate_demoted'] += 1
    warnings = []
    if stats['raw_auto'] == 0:
        warnings.append('raw_auto==0: places_vn thiếu name_zh (auto cần Hán-exact) '
                        'và không có admin-polygon (admin path tắt) − auto path hiện chưa kích hoạt')
    report = {
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'engine': 'T244 matchGeographicSites',
        'pairs_total': len(results),
        'auto_over_25km_raw': len(auto_gt25),      # PHẢI = 0
        'raw_auto_available': stats['raw_auto'],
        'warnings': warnings,
        'by_decision': dict(stats),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('[OK] report:', out_path)
    return report


def eval_sample(labels_path, report_path=None):
    """Precision/coverage trên mẫu có nhãn (dùng raw_decision = engine pre-gate)."""
    data = json.load(open(labels_path, encoding='utf-8'))
    labels = data.get('labels', data if isinstance(data, list) else [])
    pairs = data.get('pairs', {})
    tp = fp = fn = 0
    for l in labels:
        label = (l.get('label') or '').strip().lower()
        gold = label in ('accept', 'yes', '1', 'true', 'correct')
        info = pairs.get('%s|%s' % (l.get('a_id'), l.get('b_id')), {})
        pred = info.get('raw_decision') or info.get('final_decision')
        pred_pos = pred == 'auto'
        if gold:
            if pred_pos:
                tp += 1
            else:
                fn += 1
        elif pred_pos:
            fp += 1
    precision = (tp / (tp + fp)) if (tp + fp) else None
    coverage = (tp / (tp + fn)) if (tp + fn) else None
    report = {'n_labeled': sum(1 for l in labels if (l.get('label') or '').strip()),
              'tp': tp, 'fp': fp, 'fn': fn,
              'precision': round(precision, 4) if precision is not None else None,
              'coverage': round(coverage, 4) if coverage is not None else None,
              'threshold': 'raw auto (trước VN gate)'}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report_path:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('[OK] report:', report_path)
    return report


def _smoke():
    cases = [
        ({'id': 'A1', 'name_vi': 'Chùa Trấn Quốc', 'name_zh': '', 'lat': 21.0333,
          'lon': 105.85, 'place_type': 'temple', 'country': 'VN'},
         {'id': 'B1', 'name_vi': 'Trấn Quốc', 'name_zh': '', 'lat': 21.03335,
          'lon': 105.8501, 'place_type': 'temple', 'country': 'VN'}),
        ({'id': 'A2', 'name_vi': 'Chùa Kim Cương', 'name_zh': '金剛寺', 'lat': 21.0,
          'lon': 105.8, 'place_type': 'temple', 'country': 'VN'},
         {'id': 'B2', 'name_vi': 'Kim Cương', 'name_zh': '金剛寺', 'lat': 21.01,
          'lon': 105.81, 'place_type': 'temple', 'country': 'VN'}),
        ({'id': 'A3', 'name_vi': 'Chùa A', 'name_zh': '', 'lat': 16.0, 'lon': 108.2,
          'place_type': 'temple', 'country': 'VN'},
         {'id': 'B3', 'name_vi': 'Chùa A', 'name_zh': '', 'lat': 16.4, 'lon': 108.6,
          'place_type': 'temple', 'country': 'VN'}),
    ]
    for a, b in cases:
        fa, fb = name_features(a), name_features(b)
        dist = haversine_km(a['lat'], a['lon'], b['lat'], b['lon'])
        m = decide(a, b, fa, fb, dist)
        apply_vn_gate([m], enabled=True)
        print('%s × %s | dist=%.3fkm | score=%.3f | raw=%s → final=%s (%s)' % (
            a['name_vi'], b['name_vi'], dist or 0.0, m['score'],
            m['raw_decision'], m['decision'], m['reason']))


def cli():
    ap = argparse.ArgumentParser(description='T244 — Matching Engine matchGeographicSites')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--build-candidates', action='store_true')
    g.add_argument('--eval', metavar='LABELS.json')
    g.add_argument('--smoke', action='store_true')
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--bb', default=','.join(str(x) for x in VN_BBOX))
    ap.add_argument('--limit-a', type=int, default=None)
    ap.add_argument('--out', default=DEFAULT_CANDIDATES)
    ap.add_argument('--report', default=DEFAULT_REPORT)
    args = ap.parse_args()

    if args.smoke:
        _smoke()
        return 0
    if args.eval:
        eval_sample(args.eval, args.report)
        return 0
    import sqlite3
    conn = sqlite3.connect(args.db)
    try:
        bbox = tuple(float(x) for x in args.bb.split(','))
        results, _, _ = build_candidates(conn, bbox, args.limit_a)
        _sample_write(results, args.out)
        _report_stats(results, args.report)
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(cli())