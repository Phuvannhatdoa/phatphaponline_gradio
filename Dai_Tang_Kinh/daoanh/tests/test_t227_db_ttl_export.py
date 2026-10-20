# -*- coding: utf-8 -*-
import copy,json,sqlite3,sys,tempfile,time,unittest,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from flask import Flask
from rdflib import Graph,RDF,Literal,URIRef
from src_python import ttl_profile_v2 as m,ttl_db_sources as src,ttl_db_export as exp,ttl_db_batch as batch
from api_ttl_profile_v2 import create_ttl_profile_blueprint
XML='''<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><listPerson>
<person xml:id="A008431" ana="historical"><persName xml:lang="zho-Hant">慧升</persName><persName type="alternative" xml:lang="zho-Hant">延福慧升</persName><sex value="1"/><note type="concise">原文慧升。</note><note type="monk">是</note><birth>原文日期</birth><note type="worksBy">作品一</note></person>
<person xml:id="A000885"><persName xml:lang="zho-Hant">重顯</persName></person>
</listPerson></body></text></TEI>'''
TTL='''@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> . @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . <ex:monk/dien_phuc_tue_thang> a <bkg:Monk>; rdfs:label "Diên Phúc Tuệ Thăng"@vi; bkg:biographicalNote "Bản Việt đầy đủ — 慧升."@vi; bkg:generationOrder 50; bkg:hasTeacher <ex:monk/duc_vuong_doan_du> .'''
class DBTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.db=self.base/'test.db';self.ttl=self.base/'ttl';self.q=self.base/'quarantine';self.ttl.mkdir();self.q.mkdir();(self.ttl/'TS-Dien-Phuc-Tue-Thang.ttl').write_text('\ufeff'+TTL,encoding='utf8');(self.ttl/'0-template.ttl').write_text('bad turtle',encoding='utf8');(self.q/'bad.ttl').write_text('quarantined evidence',encoding='utf8')
  self.archive=self.base/'person.zip'
  with zipfile.ZipFile(self.archive,'w') as z:z.writestr('Person_Authority.xml',XML)
  c=self.connect();c.executescript('''CREATE TABLE people(id TEXT PRIMARY KEY,name_zh TEXT,name_vi TEXT,bio TEXT,bio_vi TEXT,sect TEXT,dynasty TEXT,birth_year INT,death_year INT);
CREATE TABLE data_sources(source_code TEXT,license_verified INT,redistribution_allowed INT);
CREATE TABLE vn_person_authority(id TEXT,ttl_filename TEXT,name_vi TEXT,name_zh TEXT,dila_id TEXT,status TEXT,biographical_note_vi TEXT,dharma_lineage TEXT,generation_order INT,gender TEXT,is_lineage_founder INT,birth_year INT,death_year INT);
CREATE TABLE person_gen_computed(person_id TEXT,lineage_key TEXT,gen_sect INT,gen_lamte INT,gen_thientong INT);
CREATE TABLE lineage_edge_assertions(id INT,subject_person_id TEXT,object_person_id TEXT,source_code TEXT,relation_type TEXT,raw_relation_type TEXT,status TEXT,mapping_verified INT,ref TEXT);
''')
  c.execute('INSERT INTO people VALUES(?,?,?,?,?,?,?,?,?)',('A008431','慧升','Tuệ Thăng','DB Hán','DB Việt','Thiền Tông','Tống',None,None));c.execute('INSERT INTO people VALUES(?,?,?,?,?,?,?,?,?)',('A000885','重顯','Trọng Hiển','',None,None,None,None,None))
  c.execute('INSERT INTO data_sources VALUES(?,?,?)',('DILA',0,0));c.execute('INSERT INTO vn_person_authority VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',('dien_phuc_tue_thang','TS-Dien-Phuc-Tue-Thang','Diên Phúc Tuệ Thăng','延福慧升','A008431','verified','Biên tập DB','Lâm Tế',50,'Male',0,None,None))
  c.execute('INSERT INTO person_gen_computed VALUES(?,?,?,?,?)',('A008431','old_computed',None,999,0));c.execute('INSERT INTO lineage_edge_assertions VALUES(?,?,?,?,?,?,?,?,?)',(1,'A000885','A008431','DILA','da:isTeacherOf','dila:teacher_of','active',1,''));c.execute('INSERT INTO lineage_edge_assertions VALUES(?,?,?,?,?,?,?,?,?)',(2,'A008431','A008431','DILA','da:isTeacherOf','dila:teacher_of','active',1,''));c.commit()
  self.counts=src.import_sources(c,self.archive,self.ttl,self.q,'fixture');c.close()
  app=Flask('t227');app.register_blueprint(create_ttl_profile_blueprint(self.base,self.connect,lambda token:token=='fixture-token'));self.client=app.test_client()
 def connect(self):
  c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row;return c
 def tearDown(self):self.temp.cleanup()
 def profile(self,identifier='A008431'):
  c=self.connect()
  try:return exp.export(c,identifier)
  finally:c.close()
 def test_01_source_counts_and_raw_BOM(self):
  self.assertEqual(self.counts['xml'],2);self.assertEqual(self.counts['ttl_active'],2);self.assertEqual(self.counts['ttl_quarantine'],1)
  c=self.connect();r=src.latest(c,'TTL','TS-Dien-Phuc-Tue-Thang.ttl',group='active');self.assertEqual(r['raw_text'],'\ufeff'+TTL);self.assertEqual(r['sha256'],src.file_digest(self.ttl/'TS-Dien-Phuc-Tue-Thang.ttl'));c.close()
 def test_02_import_idempotent_and_base_unchanged(self):
  c=self.connect();before=c.execute('SELECT count(*) FROM '+src.TABLE).fetchone()[0];counts=src.import_sources(c,self.archive,self.ttl,self.q,'again');self.assertEqual(counts['inserted'],0);self.assertEqual(c.execute('SELECT count(*) FROM '+src.TABLE).fetchone()[0],before);self.assertEqual(c.execute('SELECT generation_order FROM vn_person_authority').fetchone()[0],50);c.close()
 def test_03_export_reads_DB_without_original_files(self):
  self.archive.unlink()
  for f in self.ttl.iterdir():f.unlink()
  result=self.profile();self.assertIn('原文慧升',result['ttl']);self.assertIn('Bản Việt đầy đủ',result['ttl']);self.assertIn('Biên tập DB',result['ttl']);self.assertEqual(result['source_mode'],'database');self.assertEqual(m.parse_v2(result['ttl']),result['profile'])
 def test_04_stable_exact_identity(self):
  p=self.profile()['profile'];self.assertEqual(p['person']['dila_id'],'A008431');self.assertEqual(p['person']['uri'],m.person_uri(m.stable_key('authority:DILA:A008431')));self.assertEqual(p['person']['name_vi'],'Diên Phúc Tuệ Thăng')
 def test_05_generation_preserved_not_verified_or_increased(self):
  p=self.profile()['profile'];gens=[a for a in p['assertions'] if a['predicate']==m.PREDICATES['generation']];self.assertEqual({a['object']['value'] for a in gens},{'50','999'});self.assertTrue(all(a['status']=='legacy_unverified' for a in gens));self.assertFalse(any(a['status']=='accepted' for a in p['assertions']))
 def test_06_self_edge_preserved_only_snapshot(self):
  r=self.profile();self.assertTrue(any(i['type']=='self_edge' for i in r['issues']));self.assertTrue(any(s['id']=='db_edges_DILA' and any(e['id']==2 for e in s['snapshot']) for s in r['profile']['sources']));self.assertFalse(any(a['predicate'] in m.RELATIONS and a['subject']==a['object']['value'] for a in r['profile']['assertions']))
 def test_07_teacher_direction_not_dharma(self):
  p=self.profile()['profile'];teacher=m.person_uri(m.stable_key('authority:DILA:A000885'));self.assertTrue(any(a['predicate']==m.PREDICATES['teacher'] and a['subject']==teacher and a['object']['value']==p['person']['uri'] for a in p['assertions']));self.assertFalse(any(a['predicate']==m.PREDICATES['dharma_teacher'] for a in p['assertions']))
 def test_08_unverified_mapping_does_not_merge_people(self):
  c=self.connect();c.execute("UPDATE vn_person_authority SET status='auto_ttl'");c.commit();c.close();p=self.profile('ttl:TS-Dien-Phuc-Tue-Thang.ttl')['profile'];self.assertEqual(p['person']['dila_id'],'');self.assertEqual(p['person']['legacy_slug'],'dien_phuc_tue_thang');self.assertNotEqual(p['person']['uri'],m.person_uri(m.stable_key('authority:DILA:A008431')))
 def test_09_alias_mismatch_blocks_merge(self):
  c=self.connect();c.execute("UPDATE vn_person_authority SET name_zh='別人'");c.commit();c.close();p=self.profile('slug:dien_phuc_tue_thang')['profile'];self.assertEqual(p['person']['dila_id'],'')
 def test_10_DB_updates_appear_in_export(self):
  c=self.connect();c.execute("UPDATE vn_person_authority SET biographical_note_vi='Nội dung DB mới'");c.commit();c.close();self.assertIn('Nội dung DB mới',self.profile()['ttl'])
 def test_11_readonly_batch_zip_and_template_report(self):
  out=self.base/'out';r=batch.run(self.db,out);self.assertEqual(r['counts'],{'processed':2,'exported':1,'needs_review':1});self.assertFalse(r['database_written']);self.assertFalse((out/'bad.ttl').exists())
  with zipfile.ZipFile(out/'ttl-v2.zip') as z:self.assertIn('TS-Dien-Phuc-Tue-Thang.ttl',z.namelist());self.assertIn('manifest.jsonl',z.namelist());self.assertIn('source-evidence-manifest.jsonl',z.namelist());self.assertEqual(sum(n.endswith('.txt') for n in z.namelist()),2)
  with self.assertRaises(ValueError):batch.run(self.db,out)
 def test_12_api_DB_load_and_download(self):
  self.archive.unlink();r=self.client.get('/daoanh/api/admin/ttl_v2/from_db/A008431');self.assertEqual(r.status_code,200);self.assertEqual(r.get_json()['source_mode'],'database');r=self.client.get('/daoanh/api/admin/ttl_v2/export_db/A008431');self.assertEqual(r.status_code,200);self.assertEqual(r.headers['X-TTL-Source'],'database');self.assertIn('attachment',r.headers['Content-Disposition'])
 def test_13_api_auth_gate_and_bad_identifier(self):
  self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/batch',json={'scope':'ttl'}).status_code,401);self.assertEqual(self.client.get('/daoanh/api/admin/ttl_v2/from_db/not-an-id').status_code,422)
 def test_18_completed_job_survives_blueprint_restart(self):
  job='a'*32;out=self.base/'data/ttl_v2/db_exports'/job;batch.run(self.db,out)
  app=Flask('restarted');app.register_blueprint(create_ttl_profile_blueprint(self.base,self.connect,lambda token:token=='fixture-token'));client=app.test_client();headers={'X-Session-Token':'fixture-token'}
  self.assertEqual(client.get('/daoanh/api/admin/ttl_v2/batch/'+job,headers=headers).get_json()['status'],'done')
  response=client.get('/daoanh/api/admin/ttl_v2/batch/'+job+'/download',headers=headers);self.assertEqual(response.status_code,200);response.close()
 def test_17_bad_cached_template_returns_422(self):
  r=self.client.get('/daoanh/api/admin/ttl_v2/from_db/ttl:0-template.ttl');self.assertEqual(r.status_code,422);self.assertIn('Nguồn TTL chưa hợp lệ',r.get_json()['error'])
 def test_14_DB_authority_accept_without_archive(self):
  self.archive.unlink();p=self.profile()['profile'];a=next(a for a in p['assertions'] if a['id']=='dila_1');a.update(status='accepted',reviewer='fixture',reviewed_at='2026-10-04T10:00:00+07:00');r=self.client.post('/daoanh/api/admin/ttl_v2/render',json={'profile':p});self.assertEqual(r.status_code,200,r.get_json())
 def test_15_tampered_raw_DB_blocked(self):
  c=self.connect();c.execute("UPDATE ttl_v2_source_records SET raw_text='tampered' WHERE kind='DILA_XML'");c.commit();c.close()
  with self.assertRaises(ValueError):self.profile()
 def test_16_async_batch_authenticated(self):
  headers={'X-Session-Token':'fixture-token'};r=self.client.post('/daoanh/api/admin/ttl_v2/batch',json={'scope':'ttl'},headers=headers);self.assertEqual(r.status_code,202);job=r.get_json()['job_id']
  for _ in range(100):
   state=self.client.get('/daoanh/api/admin/ttl_v2/batch/'+job,headers=headers).get_json()
   if state['status']!='running':break
   time.sleep(.03)
  self.assertEqual(state['status'],'done',state);response=self.client.get('/daoanh/api/admin/ttl_v2/batch/'+job+'/download',headers=headers);self.assertEqual(response.status_code,200);response.close()
if __name__=='__main__':unittest.main(verbosity=2)
