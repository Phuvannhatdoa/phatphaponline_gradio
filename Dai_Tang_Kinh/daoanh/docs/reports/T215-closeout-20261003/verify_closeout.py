# -*- coding: utf-8 -*-
"""Kiểm đọc lại DB, hash TTL/cách ly, API và chứng cứ DILA, không ghi DB."""
import json,sqlite3,runpy,hashlib,xml.etree.ElementTree as E
from pathlib import Path
D=Path.cwd()/'daoanh';O=D/'docs/reports/T215-closeout-20261003';B=D/'data/backups/T215-closeout-20261003'
a=runpy.run_path(str(O/'apply_closeout.py'));c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
r=json.loads((B/'sync-report.json').read_text(encoding='utf-8'));p=json.loads((B/'change-plan.json').read_text(encoding='utf-8'));s=json.loads((O/'after-audit/summary.json').read_text(encoding='utf-8'));v=json.loads((O/'api-verification.json').read_text(encoding='utf-8'));e=json.loads((O/'dila-evidence.json').read_text(encoding='utf-8'))
assert r['committed'];assert a['snapshot'](c)==r['after'],'DB đã thay đổi từ snapshot closeout';assert a['protection'](c)==r['non_ttl_source_hash_before'];a['check_files'](False)
for code in ('EMPTY','RDF_INVALID','MAIN_UNSUPPORTED','MULTIPLE_MAIN','SELF_EDGE','SUBJECT_COLLISION','DIRECTED_CYCLE','REVERSED_PAIR'):assert s['findings'].get(code,0)==0,code
assert s['files_scanned']==s['rdf_valid']==s['main_records'];assert all(x['pass'] and x['self_edges']==0 for x in v)
assert r['generation_existing_rows_unchanged'];assert all(not '\u00d0' in f.read_bytes().decode('utf-8-sig') for f in (D/'data/ttl').glob('*.ttl'))
for x in p['accepted_edges']:
 t,d=x['teacher'],x['disciple'];assert t!=d
 assert any(z.get('type')=='teacher' and z.get('active')==t for z in e['records'][d]['relations']) or any(z.get('type')=='student' and z.get('active')==d for z in e['records'][t]['relations'])
for id in ('A038890','A004981'):
 api=json.loads((O/('api-negative-'+id+'.json')).read_text(encoding='utf-8'));assert api['center']['display_name']['source_file']!='TS-Ma-To-Dao-Nhat.ttl' if id=='A038890' else api['center']['display_name']['primary']=='Nam Viện Huệ Ngung'
archive=D/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip';assert hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()==e['archive_sha256']
result={'db_snapshot_readback':'PASS','ttl_hash_and_quarantine':'PASS','dila_marcus_lineage_unchanged':'PASS','raw_authority_archive_unchanged':'PASS','rollback_simulation':r['rollback_test'],'generation_existing_rows_unchanged':True,'rdf_valid':s['rdf_valid'],'self_edges':0,'subject_collisions':0,'directed_cycles':0,'api_cases_pass':len(v),'negative_identity_cases_pass':2,'rejected_ttl_assertions':len(r['rejected_assertion_ids']),'inserted_ttl_assertions':len(r['inserted_assertion_ids']),'inserted_unique_pairs':len({(x['subject_person_id'],x['object_person_id']) for x in r['after']['lineage_edge_assertions'] if x['id'] in r['inserted_assertion_ids']}),'skipped_remapped_source_edges':len(p['skipped_edges']),'generation_review_pairs':26,'academic_scope':'5 hồ sơ danh tính/API; phần chưa xác minh được bỏ qua, không coi toàn corpus đã được chứng nhận học thuật.'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));c.close()
