import ast, sys

def routes_from(path):
    t = ast.parse(open(path, encoding='utf-8').read())
    out = set()
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef):
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and getattr(d.func, 'attr', '') == 'route':
                    args = [a.value for a in d.args if isinstance(a, ast.Constant)]
                    methods = ''
                    for k in d.keywords:
                        if k.arg == 'methods':
                            methods = ','.join(sorted(e.value for e in k.value.elts))
                    out.add((args[0] if args else '', methods or 'GET', n.name))
    return out

before = routes_from(sys.argv[1])
after = routes_from(sys.argv[2]) | routes_from(sys.argv[3])
print('before:', len(before), 'after:', len(after))
print('missing after:', sorted(before - after))
print('extra after:', sorted(after - before))
