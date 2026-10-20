# -*- coding: utf-8 -*-
import copy,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flask import Flask,Blueprint
from src_python import codex_namevi as m
from api_codex_namevi import register_codex_name_routes

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=self.root/'db.sqlite'
  c=self.connect();c.executescript('CREATE TABLE people(id TEXT PRIMARY KEY,name_zh TEXT,name_vi TEXT,dynasty TEXT);CREATE TABLE name_vi_map(dila_id TEXT,name_vi_final TEXT);')
  c.executemany('INSERT INTO people VALUES(?,?,?,?)',[('A000001','法雅','Tên đã duyệt','Đường'),('A000002','無學','Vô Học','Tống')]);c.execute('INSERT INTO name_vi_map VALUES(?,?)',('A000001','Tên chính giữ nguyên'));c.commit()
  self.manifest=m.prepare(c,self.root/'prepared',2);self.run=self.manifest['run_id'];self.custom=self.run+'-0';self.records=json.loads(c.execute('SELECT input_json FROM codex_name_request').fetchone()[0]);c.close()
  app=Flask('t233');bp=Blueprint('t233',__name__,url_prefix='/daoanh/api/admin/ttl_v2');register_codex_name_routes(bp,self.root,self.connect,lambda token:token=='test-admin');app.register_blueprint(bp);self.client=app.test_client()
 def connect(self):
  c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row;return c
 def tearDown(self):self.tmp.cleanup()
 def output(self):return {'results':[{'dila_id':'A000001','name_zh':'法雅','name_vi':'Pháp Nhã','uncertain':False,'notes':''},{'dila_id':'A000002','name_zh':'無學','name_vi':'Vô Học','uncertain':False,'notes':''}]}
 def response(self,payload=None):return {'status':'completed','model':m.MODEL,'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(payload or self.output(),ensure_ascii=False)}]}]}
 def ingest(self,payload=None):
  c=self.connect()
  try:return m.ingest(c,self.run,self.custom,self.response(payload))
  finally:c.close()
 def test_01_prepare_all_includes_exact_names(self):
  self.assertEqual(self.manifest['requested_people'],2);self.assertEqual(self.manifest['requests'],1)
  request=json.loads((self.root/'prepared/requests.jsonl').read_text(encoding='utf8'));self.assertEqual(request['body']['model'],'gpt-6.1-sol');self.assertTrue(request['body']['text']['format']['strict']);self.assertEqual(request['url'],'/v1/responses')
 def test_02_draft_results_do_not_change_authority(self):
  self.assertEqual(self.ingest()['inserted'],2);c=self.connect();self.assertEqual(c.execute('SELECT name_vi FROM people WHERE id=?',('A000001',)).fetchone()[0],'Tên đã duyệt');self.assertEqual(c.execute('SELECT name_vi_final FROM name_vi_map').fetchone()[0],'Tên chính giữ nguyên');self.assertEqual(c.execute('SELECT status FROM codex_person_name').fetchone()[0],'draft');c.close()
 def test_03_idempotent_receive(self):
  self.ingest();self.assertEqual(self.ingest()['inserted'],0);c=self.connect();self.assertEqual(c.execute('SELECT count(*) FROM codex_name_revision').fetchone()[0],2);c.close()
 def test_04_unknown_id_rejects_entire_group(self):
  p=self.output();p['results'][1]['dila_id']='A999999'
  with self.assertRaisesRegex(ValueError,'unknown'):self.ingest(p)
  c=self.connect();self.assertEqual(c.execute('SELECT count(*) FROM codex_person_name').fetchone()[0],0);c.close()
 def test_05_duplicate_id(self):
  p=self.output();p['results'][1]=p['results'][0]
  with self.assertRaisesRegex(ValueError,'duplicate'):self.ingest(p)
 def test_06_missing_id(self):
  p=self.output();p['results'].pop()
  with self.assertRaisesRegex(ValueError,'missing_ids'):self.ingest(p)
 def test_07_zh_mismatch(self):
  p=self.output();p['results'][0]['name_zh']='雪竇法雅'
  with self.assertRaisesRegex(ValueError,'name_zh'):self.ingest(p)
 def test_08_invented_title_review(self):
  p=self.output();p['results'][0]['name_vi']='Tuyết Đậu Pháp Nhã';self.ingest(p);c=self.connect();self.assertEqual(c.execute('SELECT status FROM codex_person_name WHERE dila_id=?',('A000001',)).fetchone()[0],'needs_review');c.close()
 def test_09_uncertain_marked(self):
  p=self.output();p['results'][0]['uncertain']=True;self.ingest(p);c=self.connect();self.assertEqual(m.stats(c)['needs_review'],1);c.close()
 def test_10_source_changed_rolls_back_group(self):
  c=self.connect();c.execute('UPDATE people SET name_zh=? WHERE id=?',('有學','A000002'));c.commit();c.close()
  with self.assertRaisesRegex(ValueError,'source_changed'):self.ingest()
  c=self.connect();self.assertEqual(c.execute('SELECT count(*) FROM codex_person_name').fetchone()[0],0);self.assertEqual(c.execute('SELECT count(*) FROM codex_name_revision').fetchone()[0],0);c.close()
 def test_11_manifest_tamper_rejects(self):
  c=self.connect();c.execute('UPDATE codex_name_request SET input_sha256=?',('f'*64,));c.commit();c.close()
  with self.assertRaisesRegex(ValueError,'tampered'):self.ingest()
 def test_12_wrong_model_and_refusal_reject(self):
  c=self.connect();r=self.response();r['model']='gemini'
  with self.assertRaisesRegex(ValueError,'unexpected_model'):m.ingest(c,self.run,self.custom,r)
  r=self.response();r['output'][0]['content']=[{'type':'refusal','refusal':'no'}]
  with self.assertRaisesRegex(ValueError,'refusal'):m.ingest(c,self.run,self.custom,r)
  c.close()
 def test_13_resume_skips_current_only(self):
  self.ingest();c=self.connect();meta=m.prepare(c,self.root/'again',2);self.assertEqual(meta['requested_people'],0);c.execute('UPDATE people SET dynasty=? WHERE id=?',('Bắc Tống','A000001'));c.commit();meta=m.prepare(c,self.root/'changed',2);self.assertEqual(meta['requested_people'],1);c.close()
 def test_14_null_and_nonhan_no_fake_translation(self):
  rows=[{'dila_id':'A000003','name_zh':'John'}];p={'results':[{'dila_id':'A000003','name_zh':'John','name_vi':'Giôn','uncertain':False,'notes':''}]};v=m.validate_output(rows,p)[0];self.assertEqual(v['name_vi'],'');self.assertEqual(v['status'],'needs_review')
 def test_15_api_auth_and_limit(self):
  self.assertEqual(self.client.get('/daoanh/api/admin/ttl_v2/codex_name/list').status_code,401)
  self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/codex_name/job',json={'action':'submit'}).status_code,401)
  r=self.client.post('/daoanh/api/admin/ttl_v2/codex_name/lookup',json={'ids':['../x']},headers={'X-Session-Token':'test-admin'});self.assertEqual(r.status_code,422)
 def test_16_api_paginated_and_stale(self):
  self.ingest();h={'X-Session-Token':'test-admin'};r=self.client.get('/daoanh/api/admin/ttl_v2/codex_name/list?per_page=1&q=法',headers=h);self.assertEqual(r.status_code,200);self.assertEqual(r.json['total'],1);self.assertEqual(r.json['items'][0]['codex_name_vi'],'Pháp Nhã');self.assertFalse(r.json['items'][0]['stale'])
  c=self.connect();c.execute('UPDATE people SET name_zh=? WHERE id=?',('法眼','A000001'));c.commit();c.close();r=self.client.post('/daoanh/api/admin/ttl_v2/codex_name/lookup',json={'ids':['A000001']},headers=h);self.assertTrue(r.json['items'][0]['stale'])
 def test_17_output_types(self):
  p=self.output();p['results'][0]['uncertain']='true'
  with self.assertRaisesRegex(ValueError,'types'):self.ingest(p)
 def test_18_input_hash_ignores_existing_vi(self):
  self.assertEqual(m.record_hash({'dila_id':'A000001','name_zh':'法雅','dynasty':'唐','name_vi':'wrong'}),m.record_hash({'dila_id':'A000001','name_zh':'法雅','dynasty':'唐','name_vi':'right'}))

 def session_job(self):
  c=self.connect();meta=m.prepare(c,self.root/'session',256,model=m.MODEL,transport='codex_chatgpt_session');c.close();return meta['run_id'],meta['run_id']+'-0'
 def provenance(self,payload):return {'transport':'codex_chatgpt_session','auth_mode':'chatgpt','cli_version':'test-cli','model_requested':m.MODEL,'artifact_sha256':m.sha(payload),'thread_id':'test-thread'}
 def test_19_session_job_has_no_paid_endpoint(self):
  run,custom=self.session_job();row=json.loads((self.root/'session/requests.jsonl').read_text());self.assertNotIn('url',row);self.assertNotIn('body',row);self.assertEqual(len(row['records']),2)
 def test_20_session_real_provenance_and_canonical_preserved(self):
  run,custom=self.session_job();c=self.connect();payload=self.output();self.assertEqual(m.ingest_session(c,run,custom,payload,self.provenance(payload))['inserted'],2);self.assertEqual(m.ingest_session(c,run,custom,payload,self.provenance(payload))['inserted'],0);row=c.execute('SELECT * FROM codex_person_name LIMIT 1').fetchone();self.assertEqual(json.loads(row['output_json'])['provenance']['auth_mode'],'chatgpt');self.assertEqual(c.execute('SELECT name_vi FROM people WHERE id=?',('A000001',)).fetchone()[0],'Tên đã duyệt');c.close()
 def test_21_session_api_key_mode_and_wrong_model_rejected(self):
  run,custom=self.session_job();c=self.connect();p=self.output();prov=self.provenance(p);prov['auth_mode']='api_key'
  with self.assertRaisesRegex(ValueError,'session_auth'):m.ingest_session(c,run,custom,p,prov)
  prov=self.provenance(p);prov['model_requested']='another-model'
  with self.assertRaisesRegex(ValueError,'unexpected_model'):m.ingest_session(c,run,custom,p,prov)
  c.close()
 def test_22_session_artifact_tampered_and_wrong_transport_rejected(self):
  run,custom=self.session_job();c=self.connect();p=self.output();prov=self.provenance(p);prov['artifact_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'artifact_tampered'):m.ingest_session(c,run,custom,p,prov)
  with self.assertRaisesRegex(ValueError,'not_session_job'):m.ingest_session(c,self.run,self.custom,p,self.provenance(p))
  c.close()
 def test_23_session_stale_source_rolls_back_all(self):
  run,custom=self.session_job();c=self.connect();c.execute('UPDATE people SET name_zh=? WHERE id=?',('有學','A000002'));c.commit();p=self.output()
  with self.assertRaisesRegex(ValueError,'source_changed'):m.ingest_session(c,run,custom,p,self.provenance(p))
  self.assertEqual(c.execute('SELECT count(*) FROM codex_person_name').fetchone()[0],0);c.close()
 def test_24_paid_api_disabled_even_if_key_present(self):
  from unittest.mock import patch
  from scripts import codex_namevi_batch as batch
  with patch.dict('os.environ',{'OPENAI_API_KEY':'test-not-a-real-key','CODEX_API_KEY':'test-not-a-real-key'}):
   with self.assertRaisesRegex(ValueError,'paid_api_disabled'):batch.session()
   for action in ['submit','collect']:
    r=self.client.post('/daoanh/api/admin/ttl_v2/codex_name/job',json={'action':action},headers={'X-Session-Token':'test-admin'});self.assertEqual(r.status_code,409);self.assertIn('API trả phí đã tắt',r.json['error'])
 def test_25_session_env_excludes_paid_credentials(self):
  from unittest.mock import patch
  from scripts.codex_namevi_session import clean_env
  with patch.dict('os.environ',{'OPENAI_API_KEY':'test','CODEX_API_KEY':'test','ANTHROPIC_API_KEY':'test','OPENAI_BASE_URL':'https://bad.example'}):
   for key in ['OPENAI_API_KEY','CODEX_API_KEY','ANTHROPIC_API_KEY','OPENAI_BASE_URL']:self.assertNotIn(key,clean_env())
 def test_26_cli_api_auth_is_not_accepted(self):
  from unittest.mock import patch
  from subprocess import CompletedProcess
  from scripts.codex_namevi_session import cli_status
  with patch('scripts.codex_namevi_session.shutil.which',return_value='codex'),patch('scripts.codex_namevi_session.subprocess.run',side_effect=[CompletedProcess([],0,'','Logged in using an API key'),CompletedProcess([],0,'codex-cli test','')]):self.assertFalse(cli_status()['authenticated'])

if __name__=='__main__':unittest.main(verbosity=2)
