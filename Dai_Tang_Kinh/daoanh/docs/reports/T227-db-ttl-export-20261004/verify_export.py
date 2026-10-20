import sys,json,sqlite3,zipfile,hashlib
from pathlib import Path
base=Path(__file__).resolve().parents[3];sys.path.insert(0,str(base))
from src_python import ttl_profile_v2 as m
folder=base/'data/ttl_v2/db_exports/T227-db-export-v2-20261004';result={'ttl_checked':0,'evidence_checked':0,'accepted_assertions':0,'self_typed_relations':0,'merged_dila_profiles':0,'failures':[]}
with zipfile.ZipFile(folder/'ttl-v2.zip') as z:
 with (folder/'manifest.jsonl').open(encoding='utf8') as f:
  for line in f:
   row=json.loads(line)
   if row['status']!='exported':continue
   try:
    raw=z.read(row['filename']);text=raw.decode('utf8');assert m.digest(text)==row['sha256'];assert (folder/row['filename']).read_bytes()==raw
    p=m.parse_v2(text);assert m.validate(p)['conforms'];result['ttl_checked']+=1;result['merged_dila_profiles']+=bool(p['person']['dila_id']);result['accepted_assertions']+=sum(a['status']=='accepted' for a in p['assertions']);result['self_typed_relations']+=sum(a['predicate'] in m.RELATIONS and a['object'].get('kind')=='iri' and a['subject']==a['object']['value'] for a in p['assertions'])
    for s in p['sources']:
     if s['id']=='dila_record':assert m.digest(s['snapshot']['xml'])==s['sha256']
     if s['id'].startswith('db_ttl_'):assert m.digest(s['snapshot']['raw_text'])==s['snapshot']['sha256']
   except Exception as e:result['failures'].append({'filename':row['filename'],'error':str(e)})
 with (folder/'source-evidence-manifest.jsonl').open(encoding='utf8') as f:
  for line in f:
   row=json.loads(line);assert hashlib.sha256(z.read(row['zip_entry'])).hexdigest()==row['sha256'];result['evidence_checked']+=1
 result['zip_crc_errors']=z.testzip()
assert result['ttl_checked']==1037 and result['evidence_checked']==8 and not result['failures'] and result['accepted_assertions']==0 and result['self_typed_relations']==0 and result['zip_crc_errors'] is None,result
(Path(__file__).parent/'export-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
