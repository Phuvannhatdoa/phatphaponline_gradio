import argparse,hashlib,json,sqlite3
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];MANIFEST=BASE/'data/backups/T233-codex-namevi-20261004/rollback-manifest.json'

SAFE_TABLES=set(["generation_v2_scheme_revisions","generation_v2_calculations","codex_person_name","codex_name_revision","codex_name_job","codex_name_request"])
SAFE_RESTORE=set(["api_ttl_profile_v2.py","admin/ttl-profile-v2.js","admin/monk_ttl_add.html","src_python/ttl_db_export.py","package.json","admin/namevimap.html","places.html","tests/test_b25_authority_contract.py"])
SAFE_CREATED=set(["src_python/generation_engine_v2.py","api_generation_v2.py","scripts/install_generation_v2.py","scripts/compute_generations_v2.py","scripts/t232_inspect.py","admin/generation-ui-v2.js","admin/places-generation-v2.js","tests/test_t232_generation_engine.py","src_python/codex_namevi.py","scripts/codex_namevi_batch.py","api_codex_namevi.py","admin/codex-namevi.js","admin/codex-namevi.css","tests/test_t233_codex_namevi.py","scripts/reload-name-generation-main.ps1","scripts/test-name-generation-ui.cjs"])
def filehash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def within(s):
 p=(BASE/s).resolve();p.relative_to(BASE.resolve());return p
def tablehash(c,t):
 h=hashlib.sha256();n=0
 for r in c.execute('SELECT * FROM '+t+' ORDER BY rowid'):
  h.update(json.dumps(list(r),ensure_ascii=False,separators=(',',':')).encode('utf8'));h.update(b'\n');n+=1
 return {'rows':n,'sha256':h.hexdigest()}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args();m=json.loads(MANIFEST.read_text(encoding='utf8'));issues=[]
 if set(m['tables'])!=SAFE_TABLES or len(m['tables'])!=len(SAFE_TABLES):raise ValueError('Unexpected table scope')
 if {r['file'] for r in m['restore']}!=SAFE_RESTORE or len(m['restore'])!=len(SAFE_RESTORE):raise ValueError('Unexpected restore scope')
 if {r['file'] for r in m['created']}!=SAFE_CREATED or len(m['created'])!=len(SAFE_CREATED):raise ValueError('Unexpected created-code scope')
 for r in m['restore']:
  if filehash(within(r['file']))!=r['after_sha256']:issues.append('changed:'+r['file'])
  if filehash(within(r['backup']))!=r['before_sha256']:issues.append('bad_backup:'+r['backup'])
 for r in m['created']:
  if filehash(within(r['file']))!=r['after_sha256']:issues.append('changed:'+r['file'])
 c=sqlite3.connect(BASE/'data/lineage.db',timeout=30) if args.apply else sqlite3.connect('file:'+str(BASE/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True)
 if args.apply:c.execute('BEGIN IMMEDIATE')
 for t in m['tables']:
  if tablehash(c,t)!=m['db_fingerprints'].get(t):issues.append('table_changed_or_unsealed:'+t)
 if issues:
  c.rollback();c.close();raise ValueError('; '.join(issues))
 print(json.dumps({'mode':'APPLY' if args.apply else 'DRY-RUN','guards':'PASS','restore_files':len(m['restore']),'remove_created_code':len(m['created']),'drop_additive_tables':m['tables'],'source_tables_restored':0,'reports_backups_preserved':True}))
 if args.apply:
  # Không restore toàn DB: giữ mọi bảng dữ liệu nguồn và công việc session khác.
  for t in m['tables']:c.execute('DROP TABLE '+t)
  for r in m['restore']:
   target=within(r['file']);target.write_bytes(within(r['backup']).read_bytes());assert filehash(target)==r['before_sha256']
  for r in m['created']:within(r['file']).unlink()
  c.commit()
 c.close()
if __name__=='__main__':main()
