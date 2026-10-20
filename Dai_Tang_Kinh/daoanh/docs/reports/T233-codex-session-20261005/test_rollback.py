import json,sqlite3,sys,tempfile,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from scripts.rollback_codex_session import rollback
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row
  from src_python import codex_namevi as m
  self.m=m;m.ensure(self.c);self.c.executescript('CREATE TABLE people(id TEXT PRIMARY KEY,name_zh TEXT,name_vi TEXT,dynasty TEXT);')
  self.c.execute('INSERT INTO people VALUES(?,?,?,?)',('A000001','法雅','Canonical','唐'));self.c.commit()
  self.temp=tempfile.TemporaryDirectory();meta=m.prepare(self.c,Path(self.temp.name)/'job',transport='codex_chatgpt_session');self.run=meta['run_id'];payload={'results':[{'dila_id':'A000001','name_zh':'法雅','name_vi':'Pháp Nhã','uncertain':False,'notes':''}]}
  m.ingest_session(self.c,self.run,self.run+'-0',payload,{'transport':'codex_chatgpt_session','auth_mode':'chatgpt','model_requested':m.MODEL,'artifact_sha256':m.sha(payload)})
 def tearDown(self):self.c.close();self.temp.cleanup()
 def test_rollback_keeps_sources_and_revision_audit(self):
  self.assertEqual(rollback(self.c,self.run)['changes'],1);self.assertEqual(self.c.execute('SELECT count(*) FROM codex_person_name').fetchone()[0],1)
  rollback(self.c,self.run,True);self.assertEqual(self.c.execute('SELECT count(*) FROM codex_person_name').fetchone()[0],0);self.assertEqual(self.c.execute('SELECT name_vi FROM people').fetchone()[0],'Canonical');self.assertEqual(self.c.execute('SELECT count(*) FROM codex_name_revision').fetchone()[0],1);self.assertTrue(rollback(self.c,self.run)['already_reverted'])
 def test_changed_suggestion_blocks_rollback(self):
  self.c.execute('UPDATE codex_person_name SET name_vi=?',('Admin edit',));self.c.commit()
  with self.assertRaisesRegex(ValueError,'Gợi ý đã đổi'):rollback(self.c,self.run,True)
  self.assertEqual(self.c.execute('SELECT name_vi FROM codex_person_name').fetchone()[0],'Admin edit')
 def test_running_job_blocks_rollback(self):
  self.c.execute('UPDATE codex_name_job SET status=?',('running_session',));self.c.commit()
  with self.assertRaisesRegex(ValueError,'Dừng runner'):rollback(self.c,self.run,True)
if __name__=='__main__':unittest.main(verbosity=2)
