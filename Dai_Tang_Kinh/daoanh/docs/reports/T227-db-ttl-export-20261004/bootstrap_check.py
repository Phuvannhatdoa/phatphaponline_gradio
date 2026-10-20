import importlib.util,json
from pathlib import Path
base=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('t227_main',base/'app.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
client=module.app.test_client();routes=['/daoanh/api/admin/ttl_v2/schema','/daoanh/api/admin/ttl_v2/from_db/A000885','/daoanh/api/admin/ttl_v2/export_db/A008431','/daoanh/api/admin/lineages'];result={}
for url in routes:
 r=client.get(url);result[url]={'status':r.status_code,'bytes':len(r.data)};assert r.status_code==200,(url,r.data[:300])
print(json.dumps(result,ensure_ascii=False));(Path(__file__).parent/'bootstrap-result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
