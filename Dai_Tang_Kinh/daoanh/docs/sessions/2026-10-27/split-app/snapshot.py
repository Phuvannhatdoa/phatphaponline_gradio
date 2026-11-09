import sys, json, hashlib, io, time
sys.path.insert(0, '.')
import importlib
mod = importlib.import_module(sys.argv[1])
app = mod.app
rules = sorted(
    [[r.rule, sorted(m for m in r.methods if m not in ('HEAD', 'OPTIONS')), r.endpoint] for r in app.url_map.iter_rules()],
    key=lambda x: (x[0], x[2]))
client = app.test_client()
snap = {}
for rule, methods, endpoint in rules:
    if 'GET' not in methods or '<' in rule:
        continue
    try:
        r = client.get(rule)
        body = r.get_data()
        snap[rule] = [r.status_code, hashlib.sha256(body).hexdigest()[:16], len(body)]
    except Exception as e:
        snap[rule] = ['EXC', type(e).__name__]
out = {'rules': rules, 'get_snapshot': snap}
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('rules', len(rules), 'get_checked', len(snap))
