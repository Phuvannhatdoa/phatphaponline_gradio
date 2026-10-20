# -*- coding: utf-8 -*-
import copy,json,sqlite3,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src_python import generation_engine_v2 as g,ttl_db_sources as src,ttl_profile_v2 as m
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row
  self.c.executescript(src.SCHEMA+'''CREATE TABLE lineage_edge_assertions(id INTEGER PRIMARY KEY,subject_person_id TEXT,object_person_id TEXT,source_code TEXT,relation_type TEXT,raw_relation_type TEXT,status TEXT,mapping_verified INT,ref TEXT);''');self.c.execute('INSERT INTO ttl_v2_source_import_runs VALUES(?,?,?,?,?,?)',('fixture','completed',m.now(),m.now(),'{}','{}'));self.graph([(1,2),(2,3)])
 def tearDown(self):self.c.close()
 def aid(self,n):return 'A'+str(n).zfill(6)
 def graph(self,edges,extra=()):
  self.c.execute('DELETE FROM lineage_edge_assertions');self.c.execute('DELETE FROM ttl_v2_source_records');ids={1,2,3,4,5}|set(extra)|{n for e in edges for n in e}
  for n in ids:
   parents=[p for p,ch in edges if ch==n];raw='<person xmlns="http://www.tei-c.org/ns/1.0" xml:id="'+self.aid(n)+'"><persName xml:lang="zho-Hant">甲'+str(n)+'</persName><listRelation>'+''.join('<relation type="teacher" active="'+self.aid(p)+'"><desc><bibl>Fixture source '+str(p)+'</bibl></desc></relation>' for p in parents)+'</listRelation></person>'
   self.c.execute('INSERT INTO ttl_v2_source_records(kind,record_id,source_group,filename,version,sha256,raw_text,parse_status,main_slug,metadata_json,import_run_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',('DILA_XML',self.aid(n),'authority','fixture.xml','v1',m.digest(raw),raw,'valid','','{}','fixture',m.now()))
  for i,(p,ch) in enumerate(edges):self.c.execute('INSERT INTO lineage_edge_assertions VALUES(?,?,?,?,?,?,?,?,?)',(i+1,self.aid(p),self.aid(ch),'DILA','da:isTeacherOf','dila:teacher_of','active',1,''))
  self.c.commit()
 def anchor(self,n,value,status='source_asserted'):
  return {'person_id':self.aid(n),'name_zh':'甲'+str(n),'number':value,'status':status,'evidence':[{'citation':'S'+str(i),'version':'v1','independence_key':'root-'+str(i)} for i in range(3)],'reviewer':'fixture admin','reviewed_at':'2026-10-04T12:00:00+07:00','rationale':'Three documented roots; explicit scheme.'}
 def config(self,root=1,value=1):return {'id':'test','label':'Test lineage','convention':'Root1 plus each direct edge','root_id':self.aid(root),'policy':'dila_candidate','anchors':[self.anchor(root,value)]}
 def compute(self,n=3,c=None):return g.compute(self.c,self.aid(n),c or self.config())
 def test_01_chain_and_full_witness(self):
  r=self.compute();self.assertEqual(r['number'],3);self.assertEqual(r['status'],'candidate');self.assertEqual(r['provenance']['witnesses']['3']['person_ids'],[self.aid(1),self.aid(2),self.aid(3)]);self.assertTrue(r['provenance']['edges'][0]['citation'])
 def test_02_multiple_systems_independent(self):
  self.assertEqual(self.compute(c=self.config(1,28))['number'],30);self.assertEqual(self.compute(c=self.config(2,1))['number'],2)
 def test_03_same_length_paths_agree(self):
  self.graph([(1,2),(1,4),(2,3),(4,3)]);r=self.compute();self.assertEqual(r['candidates'],[3]);self.assertEqual(r['number'],3)
 def test_04_different_lengths_conflict(self):
  self.graph([(1,2),(2,3),(1,3)]);r=self.compute();self.assertEqual(r['status'],'conflict');self.assertIsNone(r['number']);self.assertEqual(r['candidates'],[2,3])
 def test_05_conflicting_checkpoint_propagates(self):
  c=self.config();c['anchors'].append(self.anchor(2,8));r=self.compute(c=c);self.assertEqual(r['status'],'conflict');self.assertIsNone(r['number'])
 def test_06_matching_checkpoint_keeps_root_path(self):
  c=self.config();c['anchors'].append(self.anchor(2,2));r=self.compute(c=c);self.assertEqual(r['number'],3);self.assertEqual(r['provenance']['witnesses']['3']['anchor'],self.aid(1))
 def test_07_disconnected_checkpoint_not_membership(self):
  self.graph([(4,3)]);c=self.config();c['anchors'].append(self.anchor(4,8));r=self.compute(c=c);self.assertIsNone(r['number']);self.assertIn(r['status'],('unreachable','incomplete'));self.assertTrue(any(i['type']=='checkpoint_not_connected_to_root' for i in r['issues']))
 def test_08_cycle_and_self_block(self):
  self.graph([(1,2),(2,3),(3,2)]);self.assertEqual(self.compute()['status'],'conflict');self.graph([(1,2),(2,2)]);self.assertEqual(self.compute(2)['status'],'conflict')
 def test_09_missing_parent_is_incomplete(self):
  self.graph([(1,2),(4,2)]);r=self.compute(2);self.assertEqual(r['status'],'incomplete');self.assertIsNone(r['number']);self.assertEqual(r['candidates'],[2])
 def test_10_no_marcus_or_ttl_mixing(self):
  self.c.execute('UPDATE lineage_edge_assertions SET source_code=? WHERE id=?',('MARCUS',2));self.c.commit();self.assertEqual(self.compute()['status'],'unreachable')
 def test_11_xml_edge_not_present_blocked(self):
  self.c.execute('UPDATE lineage_edge_assertions SET subject_person_id=? WHERE id=?',(self.aid(4),2));self.c.commit();r=self.compute();self.assertIsNone(r['number']);self.assertTrue(any(i['type']=='edge_not_in_raw_dila' for i in r['issues']))
 def test_12_names_and_identity_hash_locked(self):
  c=self.config();c['anchors'][0]['name_zh']='錯'
  with self.assertRaises(ValueError):self.compute(c=c)
  self.c.execute('UPDATE ttl_v2_source_records SET sha256=? WHERE record_id=?',('0'*64,self.aid(1)));self.c.commit()
  with self.assertRaises(ValueError):self.compute()
 def test_13_three_roots_no_mirror(self):
  c=self.config();c['anchors'][0]['status']='accepted';g.validate_scheme(self.c,c)
  for e in c['anchors'][0]['evidence']:e['independence_key']='same-book'
  with self.assertRaisesRegex(ValueError,'3'):g.validate_scheme(self.c,c)
 def test_14_reviewed_transmission_not_auto_accepted(self):
  c=self.config();c['anchors'][0]['status']='accepted';c['policy']='reviewed_transmission';c['reviewed_edges']=[{'id':'e'+str(i),'parent':self.aid(i),'child':self.aid(i+1),'kind':'dharma_transmission','status':'accepted','citation':'documented direct transmission','version':'v1','reviewer':'admin','reviewed_at':'2026-10-04T12:00:00+07:00'} for i in (1,2)]
  r=self.compute(c=c);self.assertEqual(r['status'],'derived_reviewable');self.assertEqual(r['number'],3);c['reviewed_edges'][0]['kind']='ordination'
  with self.assertRaises(ValueError):g.validate_scheme(self.c,c)
 def test_15_registry_append_and_compare_swap(self):
  g.ensure_schema(self.c);c=self.config();saved=g.save_scheme(self.c,c,0);self.assertEqual(saved['_revision'],1)
  with self.assertRaises(ValueError):g.save_scheme(self.c,c,0)
  saved=g.save_scheme(self.c,c,1);self.assertEqual(saved['_revision'],2);self.assertEqual(len(g.schemes(self.c)),1)
 def test_16_source_drift_requires_new_review(self):
  c=g.validate_scheme(self.c,self.config());self.c.execute('UPDATE ttl_v2_source_records SET version=? WHERE record_id=?',('v2',self.aid(1)));self.c.commit()
  with self.assertRaisesRegex(ValueError,'Phiên bản'):self.compute(c=c)
 def test_17_malformed_xml_metadata_clean_error(self):
  c=self.config();c['anchors'][0]['reviewer']=12
  with self.assertRaises(ValueError):g.validate_scheme(self.c,c)
  self.c.execute('UPDATE ttl_v2_source_records SET raw_text=?,sha256=? WHERE record_id=?',('badxml',m.digest('badxml'),self.aid(1)));self.c.commit()
  with self.assertRaises(ValueError):g.identity(self.c,self.aid(1))
 def test_18_resource_guard_no_partial_number(self):
  old=g.MAX_NODES;g.MAX_NODES=2
  try:r=self.compute();self.assertEqual(r['status'],'resource_limit');self.assertIsNone(r['number'])
  finally:g.MAX_NODES=old
 def test_19_ttl_computed_draft_roundtrip(self):
  p=m.blank_profile('t232');p['person'].update(name_zh='甲3',dila_id=self.aid(3));r=self.compute();report={'person_id':self.aid(3),'calculated_at':m.now(),'results':[r]};q=g.attach_profile(p,report);ttl,check=m.render(q);self.assertTrue(check['conforms']);self.assertTrue(all(a['status']=='draft' for a in q['assertions']));self.assertEqual(m.parse_v2(ttl)['assertions'],q['assertions'])
 def test_20_invalid_target_without_registry(self):
  with self.assertRaises(ValueError):g.calculate_all(self.c,'../../bad')
if __name__=='__main__':unittest.main(verbosity=2)
