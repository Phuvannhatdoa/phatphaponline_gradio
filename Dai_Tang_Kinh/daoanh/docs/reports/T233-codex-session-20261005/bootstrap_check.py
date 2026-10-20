import importlib.util,json
from pathlib import Path
base=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('t233_main',base/'app.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
client=module.app.test_client();result={}
for url,status in [('/daoanh/api/admin/ttl_v2/schema',200),('/daoanh/api/admin/ttl_v2/from_db/A004980',200),('/daoanh/api/admin/ttl_v2/export_db/A008431',200),('/daoanh/api/admin/lineages',200),('/daoanh/api/admin/ttl_v2/generation/schemes',200),('/daoanh/api/admin/ttl_v2/generation/calculate/A004980',200),('/daoanh/api/admin/ttl_v2/codex_name/status',401)]:
 r=client.get(url);result[url]={'status':r.status_code,'bytes':len(r.data)};assert r.status_code==status,(url,r.data[:300])
 if url.endswith('/schemes'):assert len(r.json['schemes'])==9
 if '/calculate/' in url:assert next(x for x in r.json['report']['results'] if x['scheme_id']=='linji')['number']==2
print(json.dumps(result,ensure_ascii=False));(Path(__file__).parent/'bootstrap-result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
