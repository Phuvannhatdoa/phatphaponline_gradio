"""Gộp mã nguồn app sau khi tách (app.py, core.py, db_core.py, t265_routes.py, routes_*.py) để công cụ quét chữ."""
import glob
import os

_PARTS = ('app.py', 'core.py', 'db_core.py', 't265_routes.py')


def read_app_source(base):
    paths = [os.path.join(base, p) for p in _PARTS] + sorted(glob.glob(os.path.join(base, 'routes_*.py')))
    return '\n'.join(open(p, encoding='utf-8', errors='replace').read() for p in paths)
