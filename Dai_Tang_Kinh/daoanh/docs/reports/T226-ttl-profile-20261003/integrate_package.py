import json
from pathlib import Path
p=Path('package.json');d=json.loads(p.read_text(encoding='utf8'));d['scripts']['e2e:runtime']='node scripts/run-runtime-tests.cjs';d['scripts']['test:t226']='python -X utf8 tests/test_t226_ttl_profile.py';v=d['scripts']['pipeline'];
if 'npm run test:t226' not in v:d['scripts']['pipeline']=v.replace('npm run test:translation','npm run test:t226 && npm run test:translation')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('runtime fresh output + test:t226 added')
