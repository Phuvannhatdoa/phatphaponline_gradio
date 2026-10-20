"""T378 — trích khối zenlineage (T139 Phase 2) từ app.py sang api_zenlineage.py (Flask blueprint).
Chạy một lần từ daoanh/. Hoàn tác: chép lại docs/sessions/2026-10-13/housekeeping/app.py.bak-before-T378 và xoá api_zenlineage.py.
"""
import io, sys

SRC = 'app.py'
START_MARK = '# T139 Phase 2 — Zen Lineage HITL Review (additive, DERIVED-only)'
END_MARK = "@app.route('/daoanh/api/admin/places_pending')"
FIRST_ROUTE = "@app.route('/daoanh/api/admin/zenlineage/candidates')"

raw = open(SRC, 'rb').read()
text = raw.decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split(nl)
i_mark = next(i for i, l in enumerate(lines) if l.strip() == START_MARK)
start = i_mark - 1                     # dòng '# =====' ngay trên
assert lines[start].startswith('# ====='), lines[start]
end = next(i for i, l in enumerate(lines) if l.strip() == END_MARK)   # giữ dòng này
block = lines[start:end]
while block and not block[-1].strip():
    block.pop()
r0 = next(i for i, l in enumerate(block) if l.strip() == FIRST_ROUTE)
helpers, routes = block[:r0], block[r0:]
while helpers and not helpers[-1].strip():
    helpers.pop()
assert sum(l.startswith('@app.route(') for l in routes) == 5
assert not any('@app.' in l for l in helpers)

body = []
for l in routes:
    l = l.replace('@app.route(', '@bp.route(').replace('app.logger.', 'current_app.logger.')
    body.append(('    ' + l) if l.strip() else '')
assert not any('app.' in l.replace('current_app.', '') .replace('@bp.', '') and 'app.' in l.split('#')[0].replace('current_app.', '') for l in body), 'còn tham chiếu app.'

mod = ['# -*- coding: utf-8 -*-',
       '"""T378 (bước 1 của T364): Zen Lineage HITL Review — tách nguyên văn từ app.py sang blueprint.',
       '',
       'Nội dung route, SQL và response giữ y như khi còn trong app.py (T139 Phase 2). Đăng ký trong app.py:',
       '    app.register_blueprint(create_zenlineage_blueprint(get_db_connection))',
       'Route giữ nguyên đường dẫn /daoanh/api/admin/zenlineage/*; tên endpoint đổi thành "zenlineage.<hàm>".',
       '"""',
       'import json',
       '',
       'from flask import Blueprint, current_app, jsonify, request',
       '',
       '',
       'def _iso_now():',
       '    from datetime import datetime as _dt',
       "    return _dt.now().isoformat(timespec='seconds')",
       '',
       ''] + helpers + ['', '',
       'def create_zenlineage_blueprint(get_db_connection):',
       "    bp = Blueprint('zenlineage', __name__)",
       ''] + body + ['', '    return bp', '']
open('api_zenlineage.py', 'w', encoding='utf-8', newline='\n').write('\n'.join(mod))

pointer = ['# T139 Phase 2 — Zen Lineage HITL Review: đã tách sang api_zenlineage.py (T378, 2026-10-13);',
           '# blueprint được đăng ký ở cuối file, cạnh api_ttl_anchor.', '', '']
new_lines = lines[:start] + pointer + lines[end:]
reg_anchor = 'app.register_blueprint(create_ttl_anchor_blueprint(os.path.dirname(__file__), get_db_connection))'
k = next(i for i, l in enumerate(new_lines) if l.strip() == reg_anchor)
new_lines[k + 1:k + 1] = ['',
                          '# T378: Zen Lineage HITL Review (T139 Phase 2) — 5 route /daoanh/api/admin/zenlineage/*.',
                          'from api_zenlineage import create_zenlineage_blueprint',
                          'app.register_blueprint(create_zenlineage_blueprint(get_db_connection))']
open(SRC, 'wb').write(nl.join(new_lines).encode('utf-8'))
print('removed app.py lines %d-%d (%d lines); helpers=%d routes=%d' % (start + 1, end, end - start, len(helpers), len(routes)))
