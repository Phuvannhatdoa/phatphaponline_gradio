import importlib
import sys
sys.path.insert(0, 'scripts')
import t204_ttl_preflight as pf
import json

blocking, warnings, _ = pf.preflight('data/ttl/old')
findings = sorted(blocking + warnings, key=lambda x: str(x))
print('Blocking:', len(blocking))
print('Warnings:', len(warnings))
print('Total findings:', len(findings))
for f in findings:
    code = f.get('code')
    file = f.get('file', f.get('dila_id', f.get('msg', '')))
    print('  {}: {}'.format(code, file))
print()
print('Findings JSON:')
print(json.dumps(findings, ensure_ascii=False, indent=2))