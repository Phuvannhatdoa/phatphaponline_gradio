# -*- coding: utf-8 -*-
"""T275: API chỉ đọc chuỗi neo số đời lấy từ TTL local.

Không ghi DB, không sửa TTL. Tái sử dụng hàm trong scripts/t275_ttl_anchor.py.
Chuỗi trả về là đường từ gốc tới vị được hỏi (up, kể cả vị đó ở cuối) và các
đệ tử trực tiếp đi xuống (down). Nếu một vị có nhiều thầy, chỉ lấy thầy đầu tiên
(xem ghi chú trong T275).
"""
import importlib.util
import threading
from pathlib import Path

from flask import Blueprint, jsonify, request

_lock = threading.Lock()
_state = {}


def _load_script(base_dir):
    """Nạp scripts/t275_ttl_anchor.py như module, không chạy phần CLI."""
    path = Path(base_dir) / 'scripts' / 't275_ttl_anchor.py'
    spec = importlib.util.spec_from_file_location('t275_ttl_anchor', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def create_ttl_anchor_blueprint(base_dir, get_db=None):
    bp = Blueprint('ttl_anchor', __name__)

    def monks():
        # Đọc TTL một lần rồi giữ trong bộ nhớ (1.037 file nhỏ). Khóa tránh hai luồng đọc cùng lúc.
        with _lock:
            if 'monks' not in _state:
                mod = _load_script(base_dir)
                try:
                    _state['mod'] = mod
                    _state['monks'] = mod.load_all()
                except SystemExit:
                    # load_all() gọi sys.exit khi thiếu thư mục TTL; không để nó thoát server.
                    raise RuntimeError('Không đọc được thư mục TTL local.')
            return _state['mod'], _state['monks']

    @bp.route('/daoanh/api/ttl/anchor-chain')
    def api_ttl_anchor_chain():
        """GET /daoanh/api/ttl/anchor-chain?slug=<slug TTL>
        Trả số đời TTL và chuỗi thầy–đệ quanh một vị. Chỉ đọc."""
        slug = (request.args.get('slug') or '').strip()
        if not slug:
            return jsonify({'ok': False, 'error': 'Thiếu tham số slug (ví dụ slug=lam_te_nghia_huyen).'}), 400
        try:
            mod, m = monks()
        except RuntimeError as ex:
            return jsonify({'ok': False, 'error': str(ex)}), 500
        if slug not in m:
            return jsonify({'ok': False, 'error': 'Không có vị này trong TTL local.', 'slug': slug}), 404
        up, down = mod.chain(m, slug)

        def item(s):
            r = m.get(s, {})
            return {'slug': s, 'label': r.get('label', s), 'gen': r.get('gen')}

        return jsonify({
            'ok': True,
            'slug': slug,
            'gen': m[slug]['gen'],
            'up': [item(s) for s in up],
            'down': [item(s) for s in down],
            'source': 'TTL local',
        })

    @bp.route('/daoanh/api/ttl/anchor-by-dila')
    def api_ttl_anchor_by_dila():
        """GET /daoanh/api/ttl/anchor-by-dila?ids=A003627,A004146
        Số đời TTL cho từng DILA ID (dùng để gắn nhãn nút trên cây). Chỉ đọc.
        Ánh xạ lấy từ vn_person_authority (ttl_filename -> dila_id). Vị không có
        file khớp thì trả status 'unmapped' và gen = null, không đoán."""
        raw = request.args.get('ids') or ''
        ids = [x.strip() for x in raw.split(',') if x.strip()][:200]
        if not ids:
            return jsonify({'ok': False, 'error': 'Thiếu tham số ids (ví dụ ids=A003627,A004146).'}), 400
        if get_db is None:
            return jsonify({'ok': False, 'error': 'Chưa cấu hình kết nối DB.'}), 500
        try:
            mod, m = monks()
        except RuntimeError as ex:
            return jsonify({'ok': False, 'error': str(ex)}), 500
        by_file = {r['file'][:-4]: (s, r) for s, r in m.items()}
        out = {i: {'status': 'unmapped', 'gen': None, 'slug': None, 'label': None} for i in ids}
        conn = get_db()
        try:
            marks = ','.join('?' * len(ids))
            rows = conn.execute(
                f"SELECT dila_id, ttl_filename FROM vn_person_authority WHERE dila_id IN ({marks}) AND ttl_filename != ''",
                ids).fetchall()
        finally:
            conn.close()
        # Gom các file TTL đăng ký cho cùng một DILA ID. Nhiều file khác nhau = xung đột, không chọn bừa.
        files_of = {}
        for did, fname in rows:
            files_of.setdefault(did, set()).add(fname)
        for did, fnames in files_of.items():
            if len(fnames) > 1:
                out[did] = {'status': 'conflict', 'gen': None, 'slug': None, 'label': None,
                            'files': sorted(fnames)}
                continue
            fname = next(iter(fnames))
            hit = by_file.get(fname)
            if hit:
                slug, rec = hit
                out[did] = {'status': 'ok', 'gen': rec['gen'], 'slug': slug, 'label': rec['label']}
        return jsonify({'ok': True, 'map': out, 'source': 'TTL local (vn_person_authority)'})

    return bp
