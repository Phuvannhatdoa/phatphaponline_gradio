import hashlib,importlib.util,io,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('jingde_extractor',ROOT/'extract_jingde.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
class FixtureTests(unittest.TestCase):
 def test_grammar_and_failclosed_exclusions(self):
  fixture=json.loads((ROOT/'test-fixtures.json').read_text(encoding='utf-8'));self.assertTrue(fixture['synthetic']);self.assertFalse(fixture['historical_assertions'])
  for c in fixture['cases']:
   with self.subTest(c['name']):
    tag=c.get('tag','p');body=c.get('xml',c.get('text'));xml=('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><milestone unit="juan" n="001"/><lb n="0001a01"/><'+tag+'>'+body+'</'+tag+'></body></text></TEI>').encode();rows=[]
    for u in M.iter_units(io.BytesIO(xml)):rows.extend(M.extract_unit(u,set()))
    candidates=[r for r in rows if r['status']=='unreviewed'];self.assertEqual(len(candidates),c['expected'])
    if 'type'in c:self.assertEqual(candidates[0]['relation_type'],c['type'])
    if 'reason'in c:self.assertTrue(rows);self.assertTrue(all(r['exclusion_reason']==c['reason'] for r in rows))
    if 'hits'in c:self.assertEqual(len(rows),c['hits'])
    self.assertTrue(all(r['subject_id'] is None and r['object_id'] is None for r in rows));self.assertTrue(all(r['review_state']=='unreviewed' for r in rows))
 def test_heading_does_not_supply_subject(self):
  xml='<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><milestone unit="juan" n="1"/><lb n="0001a01"/><head>明空禪師</head><p>師嗣法海禪師。</p></body></text></TEI>'.encode();rows=[r for u in M.iter_units(io.BytesIO(xml)) for r in M.extract_unit(u,set())];self.assertFalse(any(r['status']=='unreviewed' for r in rows))
 def test_dtd_and_external_entities_failclosed(self):
  xml=b'<!DOCTYPE x [<!ENTITY a SYSTEM "file:///not-allowed">]><x>&a;</x>'
  with self.assertRaises(RuntimeError):list(M.iter_units(io.BytesIO(xml)))
 def test_ids_require_verified_embedded_reference(self):
  unit={'projection':'道圓禪師','entities':[{'start':0,'end':2,'attrs':{'ref':'https://authority.dila.edu.tw/person/search.php?aid=A004166'}}]};positions=list(range(4));self.assertEqual(M.resolve_id(unit,(0,4),positions,{'A004166'})['id'],'A004166');self.assertIsNone(M.resolve_id(unit,(0,4),positions,set())['id']);unit['entities']=[];self.assertIsNone(M.resolve_id(unit,(0,4),positions,{'A004166'})['id'])
 def test_exact_id_typed_direction_comparison(self):
  source=json.loads((ROOT/'jingde-comparison.json').read_text(encoding='utf-8'));baseline=source['baseline_observations'];b=baseline[0];candidate={'candidate_id':'fixture-only','subject_id':b['subject_id'],'object_id':b['object_id'],'relation_type':b['relation_type']};r=M.compare_exact([candidate],baseline);self.assertEqual(len(r['overlap']),1)
  rev=dict(candidate,subject_id=candidate['object_id'],object_id=candidate['subject_id']);r=M.compare_exact([rev],baseline);self.assertEqual(len(r['reverse_review']),1);self.assertFalse(r['conflict_review'])
  other=dict(candidate,relation_type='disciple_of');r=M.compare_exact([other],baseline);self.assertTrue(r['type_difference_not_conflict']);self.assertFalse(r['conflict_review'])
  missing=dict(candidate,subject_id=None);r=M.compare_exact([missing],baseline);self.assertEqual(len(r['unresolved']),1);self.assertFalse(r['new_to_comparable_snapshot'])
 def test_real_dataset_integrity(self):
  d=json.loads((ROOT/'jingde-data.json').read_text(encoding='utf-8'));rows=d['candidates']+d['excluded_trigger_occurrences'];self.assertEqual(len(rows),d['stats']['trigger_occurrences']);self.assertEqual(len(set(r['candidate_id'] for r in rows)),len(rows));self.assertEqual(M.hashfile(pathlib.Path(d['metadata']['source']['path'])),d['metadata']['source']['sha256']);self.assertEqual(M.hashfile(ROOT/'source-header-fragment.xml'),d['metadata']['source']['header_sha256']);self.assertEqual(M.hashfile(ROOT/'extract_jingde.py'),d['metadata']['script_sha256'])
  self.assertTrue(all(r['trigger'] in d['metadata']['approved_triggers'] for r in rows));self.assertTrue(all(r['subject_id'] is None and r['object_id'] is None for r in rows))
  with pathlib.Path(d['metadata']['source']['path']).open('rb') as f:
   for r in rows:
    rep=r['representation'];f.seek(rep['element_byte_start']);self.assertEqual(M.sha_bytes(f.read(rep['element_byte_end']-rep['element_byte_start'])),rep['element_xml_sha256']);self.assertEqual(M.sha_bytes(r['quotation'].encode()),r['quotation_sha256']);self.assertEqual(M.sha_bytes(r['quotation_source_projection'].encode()),rep['quotation_projection_sha256']);self.assertTrue(r['locator']['element_path'].startswith('/tei:TEI[1]/tei:text[1]/tei:body[1]'))
  for src in d['metadata']['comparison_inputs']:self.assertEqual(M.hashfile(pathlib.Path(src['path'])),src['sha256'])
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(FixtureTests);result=unittest.TextTestRunner(verbosity=2).run(suite);report={'status':'PASS' if result.wasSuccessful() else 'FAIL','test_methods':result.testsRun,'grammar_fixture_cases':len(json.loads((ROOT/'test-fixtures.json').read_text(encoding='utf-8'))['cases']),'errors':[str(x) for x in result.errors],'failures':[str(x) for x in result.failures],'scope':'Synthetic fixtures plus every real dataset record XML/quotation hash; no historical or identity promotion'}
 with (ROOT/'test-results.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
 sys.exit(0 if result.wasSuccessful() else 1)
