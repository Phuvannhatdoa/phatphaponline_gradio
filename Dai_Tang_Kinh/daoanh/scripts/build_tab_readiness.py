#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_tab_readiness.py — ACADEMIC_3_LEVELS_16_TABS_V1 (T100-P1/Batch 3): đánh giá mức sẵn sàng
của 17 tab Đạo Ảnh bằng BẰNG CHỨNG CODE + DB thật, không điểm chủ quan.

Mô hình chấm "chấm 2 trục" (dimensions × data-exists/UI-displays):
  - DATA axis:  data_exist (2đ) · data_table (1đ) · data_verified (1đ) · index_honest (1đ)
  - UI  axis:   ui_render (2đ) · ui_route (2đ) · ui_label_safe (1đ) · ui_evidence (1đ)
  Tối đa 12đ/tab. Grade: Cử nhân ≥6/12 · Cao học ≥9/12 · Tiến sĩ =12/12 (+ dataset_version, JSON-LD)

8 alert (P1-BACHELOR — sau Batch 3):
  1. Tab bar 17 vs 17 (fix_tabs.js đồng bộ nexus + entities)    6. Real-hóa 6 tab stub
  2. Tab stub còn lại (chưa có API nguồn)                        7. Co-mention chưa tách thị giác
  3. Dispatch tab 'entity' không có nhánh render                  8. Grade core tabs < 9
  4. entity_claims 100% 'unverified'                              5. events 100% 'candidate'

Cách chạy:
  python scripts/build_tab_readiness.py            # sinh data/tab_readiness.json
  python scripts/build_tab_readiness.py --verbose  # in chi tiết từng tab

Không ghi DB — chỉ đọc. Zero-RAM: không nạp bảng lớn, chỉ COUNT + PRAGMA.
"""

import os
import re
import sys
import json
import sqlite3
from datetime import datetime

# Ép stdout UTF-8 để in tiếng Việt/ký tự đặc biệt trên Windows console (cp1252)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACES_HTML = os.path.join(BASE_DIR, 'places.html')
APP_PY = os.path.join(BASE_DIR, 'app.py')
FIX_TABS_JS = os.path.join(BASE_DIR, 'fix_tabs.js')
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'tab_readiness.json')

VERBOSE = '--verbose' in sys.argv
MODEL = 'ACADEMIC_3_LEVELS_16_TABS_V1'

# danh sách tab tuyệt đối lấy từ button bar (không hardcode thứ tự ngầm)
CORE_TABS = ['entity', 'daitang', 'graph', 'persons', 'lineage', 'nexus',
             'timeline', 'giaoly', 'sukien']

# route nguồn (mờ) cho từng tab — kiểm tra tồn tại trong app.py
TAB_INFO = {
    'entity':    {'label': '地 Thực Thể',  'fn': 'renderCbetaTab',  'route': '/daoanh/api/places/<id>/cbeta',
                  'route_frag': 'api/places/<place_id>/cbeta', 'table': 'places_dila', 'note': 'entity/canon evidence'},
    'daitang':   {'label': '📜 Đại Tạng',  'fn': 'renderDaiTangTab', 'route': '/daoanh/api/entity/<id>/canon',
                  'route_frag': 'api/entity/<entity_id>/canon', 'table': 'canon_catalog', 'note': 'Bộ Kinh'},
    'graph':     {'label': '🕸 Đồ Thị',    'fn': 'renderGraphTab',  'route': '/daoanh/api/places/<id>/graph',
                  'route_frag': 'api/places/<place_id>/graph', 'table': 'event_text_link', 'note': 'graph evidence'},
    'persons':   {'label': '🧑 Nhân Vật',  'fn': 'renderPersonsTab', 'route': '/daoanh/api/places/<id>/persons',
                  'route_frag': 'api/places/<place_id>/persons', 'table': 'people', 'note': 'name_vi 100%'},
    'lineage':   {'label': '🌳 Truyền Thừa', 'fn': 'loadLineageTree', 'route': '/daoanh/api/monk/<id>/lineage-tree',
                  'route_frag': 'api/monk/<dila_id>/lineage-tree', 'table': 'marcus_networks', 'note': 'marcus'},
    'nexus':     {'label': '🔥 Nexus',     'fn': 'renderNexusTab',  'route': '/daoanh/api/nexus/<id>',
                  'route_frag': 'api/nexus/<entity_id>', 'table': 'nexus_events', 'note': 'event-centric'},
    'timeline':  {'label': '⏱ Niên Đại',   'fn': 'renderTimelineTab', 'route': '/daoanh/api/places/<id>/timeline',
                  'route_frag': 'api/places/<place_id>/timeline', 'table': 'events', 'note': 'events'},
    'giaoly':    {'label': '🔍 Giáo Lý',   'fn': 'renderGiaolyTab', 'route': '/daoanh/api/places/<id>/pali',
                  'route_frag': ['api/places/<place_id>/pali', 'api/places/<place_id>/doctrine'],
                  'table': 'pali_place_ref', 'note': 'Pali/SC + GIÁO LÝ phân đôi (Batch 4 P2)'},
    'sukien':    {'label': '⚡ Sự Kiện',   'fn': 'loadSukienTab',   'route': '/daoanh/api/places/<id>/events',
                  'route_frag': 'api/places/<place_id>/events', 'table': 'events', 'note': 'events'},
    'bandoo':    {'label': '🗺 Bản Đồ',    'fn': 'renderBandooTab', 'route': 'client-side (_currentGps)',
                  'route_frag': None, 'table': 'places', 'note': 'GPS nội bộ'},
    'thuvien':   {'label': '📚 Thư Viện',  'fn': 'renderThuvienTab', 'route': '/daoanh/api/places/<id>',
                  'route_frag': 'api/places/<place_id>', 'table': None, 'note': 'identity header + NOT-INDEXED (_daStubTab)'},
    'nghile':    {'label': '🙏 Nghi Lễ',   'fn': 'renderNghileTab', 'route': '/daoanh/api/places/<id>',
                  'route_frag': 'api/places/<place_id>', 'table': None, 'note': 'identity header + NOT-INDEXED (_daStubTab)'},
    'giaoduc':   {'label': '🎓 Giáo Dục',  'fn': 'renderGiaoducTab', 'route': '/daoanh/api/places/<id>',
                  'route_frag': 'api/places/<place_id>', 'table': None, 'note': 'identity header + NOT-INDEXED (_daStubTab)'},
    'dulieu':    {'label': '📊 Dữ Liệu',   'fn': 'renderDulieTab', 'route': '/daoanh/api/evidence/<subject_id>',
                  'route_frag': 'api/evidence/<subject_id>', 'table': 'entity_claims',
                  'note': 'render data_status thật (Batch 3 P1)'},
    'hinhanh':   {'label': '🖼 Hình Ảnh',  'fn': 'renderHinhanhTab', 'route': '/daoanh/api/places/<id>',
                  'route_frag': 'api/places/<place_id>', 'table': None, 'note': 'identity header + NOT-INDEXED (_daStubTab)'},
    'nghethuat': {'label': '🎨 Nghệ Thuật', 'fn': 'renderNghethuatTab', 'route': '/daoanh/api/places/<id>',
                  'route_frag': 'api/places/<place_id>', 'table': None, 'note': 'identity header + NOT-INDEXED (_daStubTab)'},
    'entities':  {'label': '🧩 Thực Tổng Hợp', 'fn': 'renderEntitiesTab', 'route': '/daoanh/api/evidence/<subject_id>',
                  'route_frag': 'api/evidence/<subject_id>', 'table': 'entity_claims',
                  'note': 'aggregate claims+events+co_mentions (Batch 3 P1)'},
}

# bảng mà tab phụ thuộc → mức kiểm chứng để chấm data_verified
VERIFIED_OK = {
    'people': True,            # name_vi 100% (48,673/48,673)
    'places_dila': True,
    'places': True,
    'marcus_networks': True,   # mọi row có ref citation thật
    'canon_catalog': True,
    'nexus_events': True,      # có evidence_type gắn passage CBETA
    'pali_place_ref': True,    # verified_by ZQ, confidence 0.99
    'event_text_link': True,
    'events': False,           # 100% 'candidate'
    'entity_claims': False,    # 100% 'unverified'
}


def read(name):
    with open(name, encoding='utf-8') as f:
        return f.read()


def db_counts():
    """Trả về (table_exists:set, count:dict, notes:dict) — chỉ COUNT, không nạp bảng."""

    con = None
    try:
        con = sqlite3.connect(DB_PATH)
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except Exception as e:
        return set(), {}, {'db': str(e)}
    counts = {}
    for t in ('entity_claims', 'events', 'event_evidence', 'event_text_link', 'nexus_events',
              'people', 'pali_place_ref', 'marcus_networks', 'canon_catalog', 'places_dila',
              'places', 'namevi_map_places', 'glossary_term', 'lineage_conflicts_v2',
              'doctrine_concept', 'pali_cbeta_map'):
        if t in tables:
            try:
                counts[t] = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
            except Exception:
                counts[t] = None
    # mức kiểm chứng then chốt
    if 'entity_claims' in tables:
        row = con.execute("SELECT COUNT(*) FROM entity_claims WHERE verification_status != 'unverified'").fetchone()
        counts['entity_claims_verified'] = row[0]
    if 'events' in tables:
        row = con.execute("SELECT COUNT(*) FROM events WHERE review_status NOT IN ('candidate','draft')").fetchone()
        counts['events_reviewed'] = row[0]
    if 'nexus_events' in tables:
        try:
            co = con.execute("SELECT COUNT(*) FROM nexus_events WHERE evidence_type = 'cbeta_co_mention'").fetchone()
            counts['nexus_co_mention'] = co[0]
        except Exception:
            counts['nexus_co_mention'] = None
    con.close()
    return tables, counts, {}


def main():
    places = read(PLACES_HTML)
    app = read(APP_PY)
    fix_js = read(FIX_TABS_JS) if os.path.exists(FIX_TABS_JS) else ''

    # 1) các tab button trong places.html
    bar = places.split('id="da-stabs">', 1)[1].split('</div>', 1)[0] if 'id="da-stabs">' in places else ''
    tab_keys = re.findall(r'data-t="([^"]+)"', bar)
    # 2) fix_tabs.js — đối chứng 15/16
    fix_keys = re.findall(r'data-t="([^"]+)"', fix_js)

    # 3) dispatch 'entity' đã sửa chưa
    dispatch_entity_ok = bool(re.search(r"tab === 'entity' \|\| tab === 'cbeta'", places))

    # 4) helpers mới
    has_empty = '_daEmptyState(' in places
    has_safe = '_daSafeLabel(' in places
    has_comention_dash = 'coMention' in places and '[2, 4]' in places

    # 5) stub tabs: _renderPendingTab('key')
    stub_keys = re.findall(r"_renderPendingTab\('([^']+)'\)", places)

    # 6) evidence route trong app.py
    has_evidence_route = re.search(r"@app.route\('/daoanh/api/evidence/<subject_id>'\)", app) is not None

    # 7) DB
    tables, counts, _ = db_counts()

    rows = []
    for key in tab_keys:
        info = TAB_INFO.get(key, {'label': key, 'fn': '?', 'route': '?', 'route_frag': None, 'table': None, 'note': ''})
        is_stub = key in stub_keys
        fn = info.get('fn', '?')
        fn_exists = bool(re.search(r'function %s\b' % re.escape(fn), places))
        tbl = info.get('table')
        table_exists = bool(tbl and tbl in tables)
        count = counts.get(tbl) if tbl else None
        data_exist = bool(count)
        data_verified = VERIFIED_OK.get(tbl, False) if tbl else False
        # route: route_frag có thể là chuỗi hoặc list (any-of) — Batch 4 thêm doctrine.
        frag = info.get('route_frag')
        frags = [frag] if isinstance(frag, str) else (frag or [])
        route_ok = False
        for f in frags:
            pat = re.escape(f).replace(r'\<id\>', r'<[^>]*>').replace(r'\<place_id\>', r'<[^>]*>').replace(r'\<entity_id\>', r'<[^>]*>').replace(r'\<monk_id\>', r'<[^>]*>')
            if re.search(pat, app):
                route_ok = True
                break
        if not frags and info.get('route', '').startswith('client-side'):
            route_ok = True

        # fn domain: có cần label-safe? (chỉ Graph/Nexus xây nút từ node API)
        needs_label = key in ('graph', 'nexus')
        if needs_label:
            fnsrc = ''
            mm = re.search(r'function %s\b' % re.escape(fn), places)
            if mm:
                fnsrc = places[mm.start():mm.start() + 4000]
            label_safe = ('_nexusSafeLabel' in fnsrc) or ('_daSafeLabel' in fnsrc)
            if not label_safe:
                gmm = re.search(r'function _renderVisGraph\b.{0,4000}', places, re.S)
                label_safe = gmm is not None and ('_nexusSafeLabel' in gmm.group(0))
        else:
            label_safe = True  # không xây nút từ node API → không áp dụng

        honest_empty = has_empty or (not is_stub)  # real tab có empty-state helper chung
        ui_evidence = key in ('graph', 'nexus', 'giaoly', 'sukien', 'entity', 'dulieu', 'entities')

        pts = {
            'data_exist': 2 if data_exist else 0,
            'data_table': 1 if table_exists else 0,
            'data_verified': 1 if data_verified else 0,
            'index_honest': 1 if honest_empty else 0,
            'ui_render': 2 if (fn_exists and not is_stub) else 0,
            'ui_route': 2 if route_ok else 0,
            'ui_label_safe': 1 if label_safe else 0,
            'ui_evidence': 1 if ui_evidence else 0,
        }
        score = sum(pts.values())
        grade = ('Tiến sĩ' if score == 12 else ('Cao học' if score >= 9 else ('Cử nhân' if score >= 6 else 'Chưa đạt')))
        rows.append({
            'key': key, 'label': info.get('label', key),
            'fn': fn, 'fn_exists': fn_exists, 'is_stub': is_stub,
            'route': info.get('route', ''), 'route_found': route_ok,
            'table': tbl, 'table_exists': table_exists, 'row_count': count,
            'data_exist': data_exist, 'data_verified': data_verified,
            'labels_need': needs_label, 'label_safe': label_safe,
            'honest_empty': honest_empty,
            'score': score, 'grade': grade,
        })

    core = [r for r in rows if r['key'] in CORE_TABS]
    core_avg = round(sum(r['score'] for r in core) / len(core), 2) if core else 0

    # 8 alert
    claims_unverified = counts.get('entity_claims_verified') == 0
    events_unverified = counts.get('events_reviewed') == 0
    alerts = [
        {'id': 1, 'level': 'high', 'title': 'Tab bar lệch xen kẽ giữa places.html & fix_tabs.js',
         'detail': f"places.html có {len(tab_keys)} tab; fix_tabs.js có {len(fix_keys)} tab (thêm nexus + entities). "
                    'fix_tabs.js phải đồng bộ 1:1 — nếu lệch sẽ tái đẻ bar sai khi chạy lại.',
         'status': 'open' if (len(fix_keys) > 0 and len(fix_keys) != len(tab_keys)) else 'resolved'},
        {'id': 2, 'level': 'medium', 'title': f'{len(stub_keys)} tab vẫn stub (chưa có API nguồn)',
         'detail': 'thuvien · nghile · giaoduc · dulieu · hinhanh · nghethuat — empty-state đã trung thực NOT-INDEXED. '
                    'Thuộc lộ trình T100 P1/P2.',
         'status': 'open' if len(stub_keys) else 'resolved'},
        {'id': 3, 'level': 'high', 'title': "Dispatch tab 'entity' không có nhánh render",
         'detail': "Button 地 Thực Thể tồn tại nhưng openTab không xử lý 'entity' (chỉ có 'cbeta') → click im lặng. "
                    f"Đã sửa: {('tab === \'entity\' || tab === \'cbeta\'' if dispatch_entity_ok else 'CHƯA sửa')}.",
         'status': 'resolved' if dispatch_entity_ok else 'open'},
        {'id': 4, 'level': 'high', 'title': 'entity_claims 100% unverified',
         'detail': f"{counts.get('entity_claims', '?')} claim — chỉ {(counts.get('entity_claims_verified') or 0)} đã kiểm chứng. "
                    'Không được dùng làm nguồn kết luận học thuật khi chưa review theo batch.',
         'status': 'open' if claims_unverified else 'resolved'},
        {'id': 5, 'level': 'high', 'title': 'events 100% candidate',
         'detail': f"{counts.get('events', '?')} event — {(counts.get('events_reviewed') or 0)} đã review. "
                    'Sự kiện chỉ hiển thị dạng "candidate" kèm evidence_type (dila_note/cbeta_*).',
         'status': 'open' if events_unverified else 'resolved'},
        {'id': 6, 'level': 'medium', 'title': f"{sum(1 for r in rows if r['is_stub'])} tab chưa có route nguồn",
         'detail': 'Các tab này hiển thị NOT-INDEXED trung thực; thêm API + UI là P1.',
         'status': 'open' if any(r['is_stub'] for r in rows) else 'resolved'},
        {'id': 7, 'level': 'medium', 'title': 'Co-mention chưa tách thị giác khỏi quan hệ có evidence',
         'detail': 'Rule: edge phải có source ref (solid) — co-mention dotted/hidden. '
                    f"Đã thêm dashed [2,4] + tooltip trong _renderVisGraph (Graph+Nexus): {'OK' if has_comention_dash else 'CHƯA'}.",
         'status': 'resolved' if has_comention_dash else 'open'},
        {'id': 8, 'level': 'info', 'title': 'Grade core tabs chưa đạt chuẩn release',
         'detail': f'Trung bình {len(core)} core tabs = {core_avg}/12 (chuẩn release ≥8, core ≥9). '
                    'Full grade (dataset_version, JSON-LD, evidence drawer) là P2/P3.',
         'status': 'open' if core_avg < 9 else 'resolved'},
    ]

    data = {
        'generated_at': datetime.now().isoformat(timespec='minutes'),
        'model': MODEL,
        'thresholds': {'cu_nhan': 6, 'cao_hoc': 9, 'tien_si': 12, 'release_gate': 8, 'core_gate': 9},
        'source_files': {'places_html': PLACES_HTML, 'app_py': APP_PY, 'fix_tabs_js': FIX_TABS_JS, 'db': DB_PATH},
        'tabs': rows,
        'core_tabs': CORE_TABS,
        'core_avg': core_avg,
        'alerts': alerts,
        'data_status': {
            'entity_claims': {'total': counts.get('entity_claims'), 'verified': counts.get('entity_claims_verified')},
            'events': {'total': counts.get('events'), 'reviewed': counts.get('events_reviewed')},
            'event_evidence': counts.get('event_evidence'),
            'event_text_link': counts.get('event_text_link'),
            'nexus_events': {'total': counts.get('nexus_events'), 'co_mention': counts.get('nexus_co_mention')},
            'pali_place_ref': counts.get('pali_place_ref'),
            'people': counts.get('people'),
            'marcus_networks': counts.get('marcus_networks'),
            'canon_catalog': counts.get('canon_catalog'),
            'glossary_term': counts.get('glossary_term'),
            'lineage_conflicts_v2': counts.get('lineage_conflicts_v2'),
        },
        'helpers': {'daEmptyState': has_empty, 'daSafeLabel': has_safe, 'evidence_route': has_evidence_route},
    }

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print('T100-P1/Batch3 TAB_READINESS:')
    print('  tabs:', len(tab_keys), '| stubs:', len(stub_keys), '| fix_tabs.js:', len(fix_keys))
    print('  core_avg: %.2f/12' % core_avg)
    if VERBOSE:
        for r in rows:
            print(f"  [{r['key']:10}] {r['grade']:8} {r['score']:2}/12  fn={r['fn_exists']} stub={r['is_stub']} "
                  f"route#{r['route_found']} data#{r['data_exist']} safe={r['label_safe']} tbl={r['table'] or ''}:{r['row_count']}")
    for a in alerts:
        print(f"  [{a['id']}] {('RESOLVED' if a['status']=='resolved' else ' OPEN    ')} {a['level']:6} - {a['title']}")
    print('  ->', OUT_PATH)


if __name__ == '__main__':
    main()