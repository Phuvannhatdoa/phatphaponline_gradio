"""Tach app.py thanh core.py + routes_<nhom>.py + app.py (bootstrap).

Moi dong cua file nguon nam dung 1 file dich (kiem tra bang assert).
Chay tu thu muc daoanh/:  python -X utf8 docs/sessions/2026-10-27/split-app/split.py --dry-run
"""
import ast
import collections
import os
import sys

SRC = 'docs/sessions/2026-10-27/split-app/app.py.pilot-state'
MAX_GROUP_BYTES = 600_000

GROUP_RULES = [
    ('pages', ('/dashboard', '/daoanh/dashboard', '/daoanh/admin/', '/daoanh/login', '/daoanh/admin/<path')),
    ('translate', ('translate', 'hvdic', '/cbeta', '/passage', '/segments', '/translation', 'vn_', 'gemini')),
    ('namevi', ('namevi', 'lexicon', 'hanviet', 'hv', 'transliterate', 'translit')),
    ('places', ('place',)),
    ('lineage', ('lineage', 'monk', 'person', 'persons', 'dila', 'nexus', 'events', 'chronology',
                 'entity', 'search', 'work', 'authority', 'progress')),
    ('ttl', ('ttl', 'ontology', 'anchor', 'timeline')),
]


def is_route_fn(n):
    return isinstance(n, ast.FunctionDef) and any(
        isinstance(d, ast.Call) and getattr(d.func, 'attr', '') == 'route' for d in n.decorator_list)


def route_paths(node):
    out = []
    for x in ast.walk(node):
        if isinstance(x, ast.Call) and getattr(x.func, 'attr', '') == 'route' and x.args:
            if isinstance(x.args[0], ast.Constant):
                out.append(x.args[0].value)
    return out


def group_of(paths):
    joined = ' '.join(paths)
    for name, keys in GROUP_RULES:
        if any(k in joined for k in keys):
            return name
    return 'misc'


def is_main_if(n):
    return isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and \
        ast.unparse(n.test).replace(' ', '') in ("__name__=='__main__'", "__name__==\"__main__\"")


def is_if_true(n):
    return isinstance(n, ast.If) and isinstance(n.test, ast.Constant) and n.test.value is True


def bound_names(node):
    names = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
            names.add(x.id)
        elif isinstance(x, (ast.FunctionDef, ast.ClassDef)):
            names.add(x.name)
        elif isinstance(x, ast.arg):
            names.add(x.arg)
        elif isinstance(x, (ast.Import, ast.ImportFrom)):
            for a in x.names:
                names.add((a.asname or a.name).split('.')[0])
        elif isinstance(x, ast.ExceptHandler) and x.name:
            names.add(x.name)
    return names


def module_bound(node):
    """Ten gan o cap module (khong di vao than ham/lop)."""
    out = set()
    stack = [node]
    while stack:
        x = stack.pop()
        if isinstance(x, (ast.FunctionDef, ast.ClassDef)):
            out.add(x.name)
            continue
        if isinstance(x, ast.Lambda):
            continue
        if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
            out.add(x.id)
        elif isinstance(x, (ast.Import, ast.ImportFrom)):
            for a in x.names:
                out.add((a.asname or a.name).split('.')[0])
        elif isinstance(x, ast.ExceptHandler) and x.name:
            out.add(x.name)
        stack.extend(ast.iter_child_nodes(x))
    return out


def used_names(node):
    return {x.id for x in ast.walk(node) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}


def undefined_names(text):
    import io
    import re
    from pyflakes.api import check
    from pyflakes.reporter import Reporter
    buf = io.StringIO()
    check(text, 'x.py', Reporter(buf, buf))
    return set(re.findall(r"undefined name '([^']+)'", buf.getvalue()))


def main():
    dry = '--dry-run' in sys.argv
    src = open(SRC, encoding='utf-8').read()
    lines = src.split('\n')
    tree = ast.parse(src)

    # 1. Gom cac don vi (unit) cap module, moi dong thuoc dung 1 unit.
    units = []
    prev_end = 0
    for n in tree.body:
        start = prev_end + 1
        end = n.end_lineno
        units.append({'node': n, 'start': start, 'end': end})
        prev_end = end
    if prev_end < len(lines):
        units[-1]['end'] = len(lines)

    rebound = set()
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            for x in ast.walk(n):
                if isinstance(x, ast.Global):
                    rebound.update(x.names)

    for u in units:
        n = u['node']
        u['has_global'] = any(isinstance(x, ast.Global) for x in ast.walk(n))
        if is_route_fn(n) or is_if_true(n):
            u['kind'] = 'route'
            u['paths'] = route_paths(n)
        elif is_main_if(n):
            u['kind'] = 'boot'
        elif isinstance(n, ast.Try) and any('add_url_rule' in ast.unparse(s) for s in n.body):
            u['kind'] = 'boot'
        elif isinstance(n, ast.Expr) and ('register_blueprint' in ast.unparse(n) or
                                          'app.route(' in ast.unparse(n) or 'add_url_rule' in ast.unparse(n)):
            u['kind'] = 'boot'
        else:
            u['kind'] = 'core'

    # Route co khai bao global, hoac doc bien bi gan lai trong ham -> giu o core de tranh snapshot cu.
    for u in units:
        if u['kind'] == 'route':
            if u['has_global'] or (used_names(u['node']) & rebound):
                u['kind'] = 'core'
                u['forced_core'] = True

    for u in units:
        if u['kind'] == 'route':
            u['group'] = group_of(u['paths']) if u['paths'] else 'misc'
        elif u['kind'] == 'boot':
            u['group'] = 'boot'
        else:
            u['group'] = 'core'

    # 2. Chia nho nhom qua lon theo thu tu goc.
    by_group = collections.defaultdict(list)
    for u in units:
        if u['kind'] == 'route':
            by_group[u['group']].append(u)
    for g, us in list(by_group.items()):
        size = sum(len('\n'.join(lines[u['start'] - 1:u['end']])) for u in us)
        if size > MAX_GROUP_BYTES and len(us) > 1:
            chunks, cur, cur_size = [], [], 0
            for u in us:
                s = len('\n'.join(lines[u['start'] - 1:u['end']]))
                if cur and cur_size + s > MAX_GROUP_BYTES:
                    chunks.append(cur)
                    cur, cur_size = [], 0
                cur.append(u)
                cur_size += s
            chunks.append(cur)
            for i, ch in enumerate(chunks, 1):
                for u in ch:
                    u['group'] = f'{g}{i}'
            del by_group[g]
            for ch in chunks:
                for u in ch:
                    by_group[u['group']].append(u)

    # 3. Ban do ten -> module.
    owner_module = {}
    owner_unit = {}
    for u in units:
        mod = {'core': 'core', 'boot': 'app'}.get(u['group'], 'routes_' + u['group'])
        u['module'] = mod
        for nm in module_bound(u['node']):
            if nm in owner_module and owner_module[nm] != mod:
                if not (u['kind'] == 'core' and owner_module[nm] == 'core'):
                    raise SystemExit(f'Trung ten {nm}: {owner_module[nm]} vs {mod}')
            owner_module[nm] = mod
            owner_unit[nm] = u

    import_stmts = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    import_text = [ '\n'.join(lines[n.lineno - 1:n.end_lineno]) for n in import_stmts]
    import_bound = set()
    for n in import_stmts:
        import_bound |= bound_names(n)

    # 4. Sinh import cho moi module.
    module_units = collections.defaultdict(list)
    for u in units:
        module_units[u['module']].append(u)

    def render(mod, us):
        body = []
        for u in us:
            body.append('\n'.join(lines[u['start'] - 1:u['end']]))
        needed = collections.defaultdict(set)
        for u in us:
            local = bound_names(u['node'])
            for nm in used_names(u['node']) - local:
                if nm in import_bound and mod != 'app':
                    continue
                if nm not in owner_module:
                    continue
                om = owner_module[nm]
                if om == mod:
                    continue
                needed[om].add(nm)
        if mod == 'core':
            needed.clear()
        header = []
        if mod == 'core':
            pass
        elif mod == 'app':
            header.append('"""Bootstrap: tao app, dang ky route module va chay server."""')
        else:
            header.append(f'"""Route nhom {mod[len("routes_"):]}: tach tu app.py (xem docs/sessions/2026-10-27/split-app)."""')
        head = []
        if mod not in ('core', 'app'):
            head.extend(sorted(set(import_text), key=import_text.index))
        for om in sorted(needed):
            names = sorted(needed[om])
            if om == 'core':
                head.append('from core import ' + ', '.join(names))
            else:
                head.append(f'from {om} import ' + ', '.join(names))
        if mod == 'app':
            head.extend(f'import {r}  # noqa: F401' for r in sorted(m for m in module_units if m.startswith('routes_')))
        parts = header + head
        return '\n'.join(parts) + '\n\n\n' + '\n\n\n'.join(body) + '\n'

    outputs = {}
    for mod, us in module_units.items():
        outputs[mod + '.py' if mod != 'app' else 'app.py'] = render(mod, us)

    # 5. Kiem tra phu toan bo dong.
    covered = []
    for u in units:
        covered.extend(range(u['start'], u['end'] + 1))
    assert covered == list(range(1, len(lines) + 1)), 'Coverage loi'

    # 6. Kiem tra khong co vong (route module import module khac route module).
    deps = collections.defaultdict(set)
    for name, text in outputs.items():
        mod = name[:-3]
        for line in text.split('\n'):
            if line.startswith('from ') and ' import ' in line:
                other = line.split()[1]
                if other.startswith('routes_') and other != mod:
                    deps[mod].add(other)
    for a in deps:
        for b in deps[a]:
            if a in deps.get(b, ()):
                raise SystemExit(f'Vong import {a} <-> {b}')

    baseline = undefined_names(src)
    print('undefined names trong app.py goc (ton tai san, khong sua):', sorted(baseline))
    for name, text in outputs.items():
        miss = undefined_names(text) - baseline
        if miss:
            raise SystemExit(f'Thieu import trong {name}: {sorted(miss)}')

    summary = {m: (len(us), sum(len('\n'.join(lines[u['start'] - 1:u['end']])) for u in us))
               for m, us in module_units.items()}
    for m, (n, s) in sorted(summary.items()):
        print(f'{m:24s} units={n:4d} bytes={s:9d}')
    print('forced_core routes:', [u['node'].name for u in units if u.get('forced_core')])
    if dry:
        return
    for name, text in outputs.items():
        with open(name, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    print('written:', ', '.join(sorted(outputs)))


if __name__ == '__main__':
    main()
