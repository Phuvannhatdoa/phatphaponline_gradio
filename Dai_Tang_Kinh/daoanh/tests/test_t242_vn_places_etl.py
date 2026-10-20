# -*- coding: utf-8 -*-
"""T242 — VN Temple GPS ETL tests (T0 Wikidata / T1 Overpass / T2 disantongiao + merge).

Chạy ego:    python -X utf8 tests/test_t242_vn_places_etl.py
Chạy pytest: python -X utf8 -m pytest tests/test_t242_vn_places_etl.py -v

Bộ test dùng DB temp + fixture JSON nhỏ (KHÔNG gọi mạng, KHÔNG đụng lineage.db thật).
Coverage:
  [G1] parser T0   : parse_sparql_bindings lọc đúng chùa + có tọa độ
  [G2] parser T1   : parse_overpass_elements node/way(center) + bỏ thiếu tên
  [G3] parser T2   : parse_disantongiao_html bỏ header / dòng Tỉnh / &nbsp;
  [G4] geocode     : candidate_queries thứ tự fallback tên+địa chỉ → tên+tỉnh → tên+VN
  [G5] id          : 'VN'+10 số, deterministic, không phải format PL
  [G6] bbox        : trong bbox → places_vn; ngoài/không GPS → places_vn_pending
  [G7] merge       : gộp T0/T1/T2, dedupe 200m, INSERT OR IGNORE idempotent
  [G8] dataset_sources: 4 nguồn đăng ký đủ (WIKIDATA/OPENSTREETMAP/DISANTONGIAO_VN + geocoder)
  [G9] revert      : DROP 2 bảng + xoá source T242, chạy lại lần 2 vẫn an toàn
"""

import importlib.util
import json
import os
import re
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)


def _load(name, filename):
    path = os.path.join(_DAOANH, 'scripts', filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T0 = _load('vn_t0', 'vn_places_t0_wikidata.py')
T1 = _load('vn_t1', 'vn_places_t1_osm.py')
T2 = _load('vn_t2', 'vn_places_t2_disantongiao.py')
GEO = _load('vn_geocode', 'vn_places_geocode_google.py')
MV = _load('vn_merge', 'vn_places_merge_validate.py')

ID_RE = re.compile(r'^VN[0-9]{10}$')


# ── Fixtures ────────────────────────────────────────────────────────────────

SPARQL_BINDINGS = [
    {'item': {'value': 'http://www.wikidata.org/entity/Q1063916'},
     'coord': {'value': 'Point(106.66117 10.75291)'},
     'label_vi': {'value': 'Chùa Bà Thiên Hậu'},
     'adminLabel': {'value': 'Chợ Lớn'}},
    {'item': {'value': 'http://www.wikidata.org/entity/Q391406'},
     'coord': {'value': 'Point(108.124446 15.76324)'},
     'label_vi': {'value': 'Thánh địa Mỹ Sơn'}},   # không chứa 'chùa' → loại
    {'item': {'value': 'http://www.wikidata.org/entity/Q999999'},
     'coord': {'value': 'Point(105.0 10.0)'},       # thiếu label → loại
     'label_en': {'value': 'Some Building'}},
    {'item': {'value': 'http://www.wikidata.org/entity/Q111111'},
     'label_vi': {'value': 'Chùa Hương'}},          # thiếu P625 → loại
]

OD_ELEMENTS = [
    {'type': 'node', 'id': 123, 'lat': 21.0, 'lon': 105.8,
     'tags': {'name': 'Chùa Lý Triều Quốc Sư', 'religion': 'buddhist'}},
    {'type': 'way', 'id': 456,
     'center': {'lat': 20.5, 'lon': 106.2},
     'tags': {'name': 'Chùa Trấn Quốc', 'name:en': 'Tran Quoc Pagoda'}},
    {'type': 'node', 'id': 789, 'lat': 10.0, 'lon': 106.0, 'tags': {}},  # thiếu tên → loại
]

DISA_HTML = """
<table>
 <tr><td><b>TT</b></td><td><b>Pháp danh</b></td><td><b>Tên chùa</b></td><td><b>Địa chỉ</b></td></tr>
 <tr><td>31</td><td>Tỉnh Phú Thọ</td><td>&nbsp;</td><td>&nbsp;</td><td></td><td></td><td></td></tr>
 <tr><td>c1</td><td>Đại đức trụ trì Thích Thiền Diệu</td><td>Ch&ugrave;a Bảo S&aacute;i</td><td>X&atilde; Lương Lỗ, huyện Thanh Ba, tỉnh Ph&#250; Thọ</td></tr>
 <tr><td>c2</td><td></td><td>Chùa Sơn Phúc</td><td>Thôn Hữu Lộc, xã Trúc Lâm, huyện Tĩnh Gia, tỉnh Thanh Hóa</td></tr>
</table>
"""


def _mk_json(tmp, path, payload):
    p = os.path.join(tmp, path)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    return p


def _setup_merge(tmp):
    """Tạo 3 file JSON fixture + trả đường dẫn."""
    t0p = _mk_json(tmp, 't0.json', {'records': [
        {'source': 'wikidata', 'external_key': 'Q1', 'name_vi': 'Chùa Một',
         'name_en': '', 'name_zh': '', 'admin': 'Quảng Bình',
         'lat': 16.0, 'lon': 108.0, 'accuracy': 'dila_exact'},
        {'source': 'wikidata', 'external_key': 'Q2', 'name_vi': 'Chùa Hai',
         'admin': '', 'lat': 7.0, 'lon': 108.0, 'accuracy': 'dila_exact'},  # ngoài bbox
    ]})
    t1p = _mk_json(tmp, 't1.json', {'records': [
        # trùng 'Chùa Một' trong 200m với T0 → dedupe
        {'source': 'osm', 'external_key': 'node/111', 'name': 'Chùa Một',
         'lat': 16.000001, 'lon': 108.0, 'accuracy': 'osm_centroid'},
        {'source': 'osm', 'external_key': 'node/222', 'name': 'Chùa Ba',
         'lat': 20.0, 'lon': 105.0, 'accuracy': 'osm_centroid'},
        {'source': 'osm', 'external_key': 'node/333', 'name': 'Chùa Tư',
         'lat': 21.0, 'lon': 106.5, 'accuracy': 'osm_centroid'},
    ]})
    t2p = _mk_json(tmp, 't2g.json', {'provider': 'nominatim', 'records': [
        {'source': 'disantongiao', 'external_key': 'c5', 'ten_chua': 'Chùa Năm',
         'dia_chi': 'Hà Nội', 'geo_lat': 10.0, 'geo_long': 105.0,
         'province': 'Tây Ninh', 'district': '', 'geocode_provider': 'nominatim'},
    ], 'pending': [
        {'source': 'disantongiao', 'external_key': 'c6', 'ten_chua': 'Chùa Sáu',
         'dia_chi': 'Việt Nam', 'geocode_provider': 'nominatim'},
    ]})
    return t0p, t1p, t2p


def _rows(con, t, cols):
    return [dict(zip(cols, r)) for r in con.execute(f"SELECT {','.join(cols)} FROM {t} ORDER BY id")]


# ── G1 – G4 parser ──────────────────────────────────────────────────────────

def test_t242_parser_sparql():
    recs = T0.parse_sparql_bindings(SPARQL_BINDINGS)
    names = [r['external_key'] for r in recs]
    assert 'Q1063916' in names                # có tọa độ + label chùa
    assert 'Q391406' not in names             # 'Thánh địa Mỹ Sơn' không khớp chùa
    assert 'Q999999' not in names             # label en không khớp tiếng Việt
    assert 'Q111111' not in names             # thiếu P625
    rec = recs[0]
    assert rec['lat'] == 10.75291 and rec['lon'] == 106.66117
    assert rec['accuracy'] == 'dila_exact'


def test_t242_parser_overpass():
    recs = T1.parse_overpass_elements(OD_ELEMENTS)
    assert len(recs) == 2
    keys = {r['external_key'] for r in recs}
    assert 'node/123' in keys and 'way/456' in keys
    way = [r for r in recs if r['external_key'] == 'way/456'][0]
    assert way['lat'] == 20.5 and way['lon'] == 106.2     # centroid way
    assert way['accuracy'] == 'osm_centroid'


def test_t242_parser_disantongiao():
    recs, skipped = T2.parse_disantongiao_html(DISA_HTML)
    assert skipped == 1                       # dòng nhóm Tỉnh
    assert len(recs) == 2
    e1 = recs[0]
    assert e1['ten_chua'] == 'Chùa Bảo Sái'   # html entity đã unescape
    assert e1['dia_chi'] == 'Xã Lương Lỗ, huyện Thanh Ba, tỉnh Phú Thọ'
    assert e1['external_key'] == 'c1'


def test_t242_geocode_candidates():
    rec = {'ten_chua': 'Chùa Sơn Phúc', 'dia_chi': 'Thôn Hữu Lộc, xã Trúc Lâm, huyện Tĩnh Gia, tỉnh Thanh Hóa'}
    qs = GEO.candidate_queries(rec)
    assert len(qs) == 3
    assert qs[0].startswith('Chùa Sơn Phúc, Thôn Hữu Lộc')
    assert 'Thanh Hóa' in qs[1]              # tên + tỉnh
    assert qs[2] == 'Chùa Sơn Phúc, Việt Nam'
    assert GEO.extract_province(rec['dia_chi']) == 'Thanh Hóa'
    assert 'Việt Nam' in GEO.build_query(rec)


# ── G5 – G6 id + bbox ───────────────────────────────────────────────────────

def test_t242_id_namespace():
    a = MV.make_id('wikidata', 'Q1063916')
    b = MV.make_id('wikidata', 'Q1063916')
    c = MV.make_id('osm', 'node/123')
    assert ID_RE.match(a) and ID_RE.match(c)
    assert a == b                              # deterministic
    assert a != c
    assert not a.startswith('PL') and not c.startswith('PL')


def test_t242_bbox():
    assert MV.in_vietnam_bbox(16.0, 108.0)
    assert MV.in_vietnam_bbox(24.0, 110.0)
    assert not MV.in_vietnam_bbox(25.0, 108.0)
    assert not MV.in_vietnam_bbox(7.0, 108.0)
    assert not MV.in_vietnam_bbox(16.0, 120.0)
    assert not MV.in_vietnam_bbox(None, 108.0)


# ── G7 merge ────────────────────────────────────────────────────────────────

def _apply(db_path, t0p, t1p, t2p):
    if not os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        con.execute(
            "CREATE TABLE dataset_sources ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL UNIQUE, source_type TEXT, origin_url TEXT, license TEXT,"
            " usage_level TEXT CHECK (usage_level IN ('GREEN','YELLOW','RED')) DEFAULT 'YELLOW',"
            " attribution_text TEXT, notes TEXT)")
        con.commit()
        con.close()
    rep = MV.apply(db_path, t0_path=t0p, t1_path=t1p, t2g_path=t2p)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    vn = _rows(con, 'places_vn', ['id', 'name_vi', 'source', 'accuracy', 'geo_lat'])
    pend = _rows(con, 'places_vn_pending', ['id', 'name_vi', 'raw_source'])
    srcs = [r[0] for r in con.execute(
        "SELECT name FROM dataset_sources WHERE name LIKE 'WIKIDATA' OR name LIKE 'OPENSTREETMAP%' "
        "OR name LIKE 'DISANTONGIAO%'")]
    con.close()
    return rep, vn, pend, srcs


def test_t242_merge_apply():
    tmp = tempfile.mkdtemp(prefix='t242_')
    t0p, t1p, t2p = _setup_merge(tmp)
    db = os.path.join(tmp, 'lineage.db')
    rep, vn, pend, srcs = _apply(db, t0p, t1p, t2p)

    assert rep['deduped'] == 1                                       # node/111 trùng Chùa Một
    names = [r['name_vi'] for r in vn]
    assert names.count('Chùa Một') == 1                              # chỉ giữ bản T0
    assert set(names) == {'Chùa Một', 'Chùa Ba', 'Chùa Tư', 'Chùa Năm'}
    assert rep['inserted'] == 4
    assert rep['pending_inserted'] == 2                              # Chùa Hai (out) + Chùa Sáu (no_gps)

    id_set = {r['id'] for r in vn} | {r['id'] for r in pend}
    assert all(ID_RE.match(i) for i in id_set)
    for r in vn:
        assert 8 <= r['geo_lat'] <= 24

    # accuracy/source đúng theo tầng
    src_acc = {(r['source'], r['accuracy']) for r in vn}
    assert ('wikidata', 'dila_exact') in src_acc
    assert ('osm', 'osm_centroid') in src_acc
    assert ('disantongiao', 'geocode_street') in src_acc

    # pending chứa lý do
    pend_reasons = [json.loads(r['raw_source']).get('pending_reason') for r in pend]
    assert 'out_of_bbox_vn' in pend_reasons and 'no_gps' in pend_reasons
    assert set(srcs) == {'WIKIDATA', 'OPENSTREETMAP', 'DISANTONGIAO_VN', 'OPENSTREETMAP_NOMINATIM'}
    assert rep['sources_registered'] == 4


def test_t242_merge_idempotent():
    tmp = tempfile.mkdtemp(prefix='t242_')
    t0p, t1p, t2p = _setup_merge(tmp)
    db = os.path.join(tmp, 'lineage.db')
    _apply(db, t0p, t1p, t2p)
    rep2, vn2, pend2, _ = _apply(db, t0p, t1p, t2p)
    con = sqlite3.connect(db)
    n_vn = con.execute('SELECT COUNT(*) FROM places_vn').fetchone()[0]
    n_pend = con.execute('SELECT COUNT(*) FROM places_vn_pending').fetchone()[0]
    con.close()
    assert n_vn == 4 and n_pend == 2                    # không nhân đôi
    assert len(vn2) == 4 and len(pend2) == 2


# ── G9 revert ───────────────────────────────────────────────────────────────

def test_t242_revert():
    tmp = tempfile.mkdtemp(prefix='t242_')
    t0p, t1p, t2p = _setup_merge(tmp)
    db = os.path.join(tmp, 'lineage.db')
    _apply(db, t0p, t1p, t2p)

    out = MV.revert(db)
    assert out['places_vn'] == 'dropped'
    assert out['places_vn_pending'] == 'dropped'
    assert out['sources_deleted'] == 4

    con = sqlite3.connect(db)
    exists = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name IN ('places_vn','places_vn_pending')").fetchone()[0]
    left = con.execute("SELECT COUNT(*) FROM dataset_sources WHERE name LIKE 'WIKIDATA' OR name LIKE 'OPENSTREETMAP%' OR name LIKE 'DISANTONGIAO%'").fetchone()[0]
    con.close()
    assert exists == 0
    assert left == 0

    # revert lần 2 vẫn an toàn
    out2 = MV.revert(db)
    assert out2.get('places_vn') != 'dropped'                       # bảng đã mất
    assert True


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_t242_')]
    failed = 0
    for fn in tests:
        try:
            fn()
            print('  \u2713 %s' % fn.__name__)
        except Exception as e:
            failed += 1
            import traceback
            traceback.print_exc()
            print('  \u2717 %s: %r' % (fn.__name__, e))
    print('T242 PASS %d/%d' % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())