#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T508 — Đo số route thực tế lúc runtime bằng Flask url_map (CHỈ ĐỌC).

Vì sao không `import app` trực tiếp: app.py ở module-level gọi
ensure_cbeta_ref_table() / ensure_ai_person_name_table() / _ensure_bio_vi_column()
/ _ensure_ops_tables() → mở SQLite và chạy CREATE TABLE IF NOT EXISTS. Nếu DB
data/lineage.db không tồn tại, sqlite3 sẽ TẠO file DB mới ⇒ ghi DB ngoài ý muốn.

Script này chặn điều đó: mọi sqlite3.connect(...) trỏ tới file đều bị chuyển
hướng sang thư mục sandbox tạm (ổ đĩa tạm), nên project KHÔNG bị ghi gì.
server.py được copy sang sandbox trước khi import (nó tự tạo
data/admin_emails.txt khi thiếu → sẽ tạo trong sandbox).

Cách dùng (cwd = thư mục daoanh):
    python -X utf8 measure_routes.py app
    python -X utf8 measure_routes.py server
    python -X utf8 measure_routes.py both

Kết quả: in ra màn hình + (tuỳ chọn) ghi JSON qua --json <file>.
Chỉ đọc source + đọc url_map, không sửa app.py/server.py, không ghi DB project.
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile

PROJECT_DIR = None


def _install_sqlite_redirect(sandbox_dir):
    """Chuyển hướng mọi kết nối SQLite tới file → sandbox (không đụng DB project)."""
    original_connect = sqlite3.connect
    redirected = []

    def _redirect(database, *args, **kwargs):
        target = database
        try:
            if isinstance(database, (str, bytes, os.PathLike)):
                db = os.fsdecode(database)
                if db != ':memory:' and not db.startswith('file:'):
                    base = os.path.basename(db) or 'scratch.db'
                    target = os.path.join(sandbox_dir, base)
                    redirected.append(os.path.abspath(db))
        except Exception:
            target = database
        return original_connect(target, *args, **kwargs)

    sqlite3.connect = _redirect
    return original_connect, redirected


def _collect(flask_app, label, source_file):
    """Thu thập thông tin từ url_map của Flask app."""
    rules = sorted(flask_app.url_map.iter_rules(), key=lambda r: str(r.rule))
    all_rules = []
    for r in rules:
        all_rules.append({
            'rule': str(r.rule),
            'endpoint': r.endpoint,
            'methods': sorted(m for m in r.methods if m not in ('HEAD', 'OPTIONS')),
        })
    endpoint_static = [r for r in rules if r.endpoint == 'static']
    return {
        'label': label,
        'source_file': source_file,
        'total_rules': len(all_rules),
        'rules_excluding_static_endpoint': len(all_rules) - len(endpoint_static),
        'static_rules': [{'rule': str(r.rule), 'endpoint': r.endpoint}
                         for r in endpoint_static],
        'unique_endpoints': len({r['endpoint'] for r in all_rules}),
        'unique_paths': len({r['rule'] for r in all_rules}),
        'method_counts': _method_counts(all_rules),
        'rules': all_rules,
    }


def _method_counts(all_rules):
    counts = {}
    for r in all_rules:
        for m in r['methods']:
            counts[m] = counts.get(m, 0) + 1
    return dict(sorted(counts.items()))


def measure_app(sandbox_dir):
    """Đo url_map của app.py (cổng 5000) qua import, SQLite chuyển sang sandbox."""
    original_connect, redirected = _install_sqlite_redirect(sandbox_dir)
    try:
        if PROJECT_DIR not in sys.path:
            sys.path.insert(0, PROJECT_DIR)
        import app as app_module  # noqa: E402  (import sau khi patch sqlite3)
        flask_app = app_module.app
        info = _collect(flask_app, 'app.py (port 5000)', os.path.join(PROJECT_DIR, 'app.py'))
        info['sqlite_paths_diverted_to_sandbox'] = sorted(set(redirected))
        return info
    finally:
        sqlite3.connect = original_connect


def measure_server(sandbox_dir):
    """Đo url_map của server.py (cổng 5001) qua bản copy trong sandbox."""
    os.makedirs(os.path.join(sandbox_dir, 'server_sandbox'), exist_ok=True)
    # server.py tự tạo data/admin_emails.txt khi thiếu → cho nó ghi TRONG sandbox
    os.makedirs(os.path.join(sandbox_dir, 'server_sandbox', 'data'), exist_ok=True)
    src = os.path.join(PROJECT_DIR, 'server.py')
    dst = os.path.join(sandbox_dir, 'server_sandbox', 'server.py')
    shutil.copyfile(src, dst)
    sys.path.insert(0, os.path.dirname(dst))
    for name in ('server',):
        sys.modules.pop(name, None)
    import server as server_module  # noqa: E402
    flask_app = server_module.app
    info = _collect(flask_app, 'server.py (port 5001)', src)
    info['sandbox_copy'] = dst
    return info


def main():
    global PROJECT_DIR
    parser = argparse.ArgumentParser(description='T508 — đo số route runtime (chỉ đọc)')
    parser.add_argument('target', choices=['app', 'server', 'both'])
    parser.add_argument('--project', default=None,
                        help='Thư mục chứa app.py/server.py (mặc định: thư mục của script)')
    parser.add_argument('--json', default=None, help='Ghi kết quả ra file JSON')
    args = parser.parse_args()

    if args.project:
        PROJECT_DIR = os.path.abspath(args.project)
    else:
        # script nằm trong docs/sessions/<ngày>/T508-coder/ → lùi 4 cấp về daoanh
        PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   '..', '..', '..', '..'))
        if not os.path.exists(os.path.join(PROJECT_DIR, 'app.py')):
            PROJECT_DIR = os.getcwd()

    sandbox_dir = tempfile.mkdtemp(prefix='t508_routes_')
    print(f'[T508] project  = {PROJECT_DIR}')
    print(f'[T508] sandbox  = {sandbox_dir} (mọi DB ghi ra đây, không đụng project)')
    print(f'[T508] python   = {sys.version.split()[0]}')

    results = []
    try:
        if args.target in ('app', 'both'):
            results.append(measure_app(sandbox_dir))
        if args.target in ('server', 'both'):
            results.append(measure_server(sandbox_dir))
    finally:
        # Dọn sandbox (chỉ chứa DB rỗng + bản copy server.py)
        shutil.rmtree(sandbox_dir, ignore_errors=True)

    payload = {'measured_at': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
               'results': results}

    for info in results:
        print('')
        print('=' * 68)
        print(f"  {info['label']}")
        print('=' * 68)
        print(f"  source file                         : {info['source_file']}")
        print(f"  len(app.url_map.iter_rules())  TỔNG : {info['total_rules']}")
        print(f"  sau khi loại endpoint 'static'      : {info['rules_excluding_static_endpoint']}")
        print(f"  số endpoint (view function) khác nhau: {info['unique_endpoints']}")
        print(f"  số path (rule) khác nhau            : {info['unique_paths']}")
        print(f"  theo method                         : {info['method_counts']}")
        if info['static_rules']:
            print(f"  rule nội bộ Flask 'static'          : "
                  f"{[r['rule'] for r in info['static_rules']]}")
        diverted = info.get('sqlite_paths_diverted_to_sandbox')
        if diverted is not None:
            print(f"  DB bị chuyển hướng (không ghi project): {diverted}")
        print(f"  {'-' * 64}")
        print(f"  {'METHOD':<22}{'RULE':<60}ENDPOINT")
        for r in info['rules']:
            print(f"  {','.join(r['methods']):<22}{r['rule']:<60}{r['endpoint']}")

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n[T508] JSON → {args.json}")


if __name__ == '__main__':
    main()
