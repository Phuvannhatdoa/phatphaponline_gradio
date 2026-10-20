# -*- coding: utf-8 -*-
import copy, json, sqlite3, sys, tempfile, unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from rdflib import Graph, URIRef, Literal, RDF
from src_python import ttl_profile_v2 as m
from api_ttl_profile_v2 import create_ttl_profile_blueprint, dila_record, profile_from_dila
from flask import Flask

def example():
    p=m.blank_profile('test-T226');p['person']['name_vi']='Tuệ Thăng'
    p['sources']=[{'id':'s1','code':'LOCAL','version':'fixture-1','citation':'Văn bản thử','independence_key':'work-1'}]
    p['assertions']=[{'id':'bio','subject':p['person']['uri'],'predicate':m.PREDICATES['biography'],'object':{'kind':'literal','value':'Hán: 慧升; """\\n <script>alert(1)</script>','language':'vi'},'status':'draft','evidence':['s1']}]
    return p
def accept(a):
    a.update(status='accepted',reviewer='fixture_reviewer',reviewed_at='2026-10-03T10:00:00+07:00')

class ProfileTests(unittest.TestCase):
    def test_01_unicode_roundtrip(self):
        p=example();t,_=m.render(p);self.assertEqual(m.parse_v2(t),p)
    def test_02_draft_is_not_fact(self):
        p=example();t,_=m.render(p);g=Graph().parse(data=t,format='turtle')
        self.assertNotIn((URIRef(p['person']['uri']),URIRef(m.PREDICATES['biography']),m.object_term(p['assertions'][0]['object'])),g)
    def test_03_only_accepted_projected(self):
        p=example();accept(p['assertions'][0]);t,_=m.render(p);g=Graph().parse(data=t,format='turtle')
        self.assertIn((URIRef(p['person']['uri']),URIRef(m.PREDICATES['biography']),m.object_term(p['assertions'][0]['object'])),g)
    def test_04_generation_no_mirror_count(self):
        p=example();a=p['assertions'][0];a.update(predicate=m.PREDICATES['generation'],object={'kind':'literal','value':'50','datatype':str(m.XSD.integer)},counting_scheme='Tổ gốc 1, nhánh thử',rationale='Ba chứng cứ về số 50');accept(a)
        for i in (2,3):p['sources'].append(dict(p['sources'][0],id='s'+str(i)))
        a['evidence']=['s1','s2','s3'];self.assertFalse(m.validate(p)['conforms'])
        p['sources'][1]['independence_key']='work-2';p['sources'][2]['independence_key']='work-3'
        self.assertTrue(m.validate(p)['conforms'])
        t,_=m.render(p);self.assertEqual(m.parse_v2(t),p)
        for s in p['sources']:s['independence_key']='   '
        self.assertFalse(m.validate(p)['conforms'])
        g=Graph().parse(data=t,format='turtle')
        self.assertNotIn((URIRef(p['person']['uri']),RDF.type,m.CRM.E21_Person),g)
        self.assertNotIn((URIRef(p['person']['uri']),RDF.type,m.PTH.Monastic),g)
    def test_05_generation_requires_scheme_rationale(self):
        p=example();a=p['assertions'][0];a.update(predicate=m.PREDICATES['generation'],object={'kind':'literal','value':'49','datatype':str(m.XSD.integer)});accept(a)
        self.assertFalse(m.validate(p)['conforms'])
    def test_06_self_relation_rejected(self):
        p=example();p['assertions'][0].update(predicate=m.PREDICATES['teacher'],object={'kind':'iri','value':p['person']['uri']})
        self.assertFalse(m.validate(p)['conforms'])
    def test_07_dharma_cycle_rejected(self):
        p=example();a=p['assertions'][0];other=m.person_uri('other')
        a.update(predicate=m.PREDICATES['dharma_teacher'],object={'kind':'iri','value':other},relation_scope='fixture');accept(a)
        p['assertions'].append(dict(a,id='back',subject=other,object={'kind':'iri','value':p['person']['uri']}))
        self.assertFalse(m.validate(p)['conforms'])
    def test_08_profile_page_not_sameAs(self):
        p=example();p['assertions'][0].update(predicate=m.PREDICATES['identity'],object={'kind':'iri','value':'https://authority.dila.edu.tw/person/search.php?aid=A008431'})
        self.assertFalse(m.validate(p)['conforms'])
    def test_26_sameAs_literal_rejected_by_application_and_shacl(self):
        from pyshacl import validate
        p=example();a=p['assertions'][0];a.update(predicate=m.PREDICATES['identity'],object={'kind':'literal','value':'A008431'})
        self.assertFalse(m.validate(p)['conforms'])
        accept(a);self.assertFalse(m.validate(p)['conforms'])
        a['object']={'kind':'iri','value':m.person_uri('authority-test')}
        t,_=m.render(p);g=Graph().parse(data=t,format='turtle')
        claim=next(g.subjects(RDF.type,m.PTH.Assertion));g.set((claim,RDF.object,Literal('A008431')))
        shapes=Graph().parse(data=(BASE/'ontology/ttl-profile-v2/shapes.ttl').read_text(encoding='utf8'),format='turtle')
        conforms,_,_=validate(g,shacl_graph=shapes);self.assertFalse(conforms)
    def test_09_legacy_unknown_triples_preserved(self):
        text='@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n<ex:monk/a> a <bkg:Monk>; rdfs:label "Tuệ"@vi; bkg:biographicalNote "慧升"; bkg:generationOrder 50; bkg:hasTeacher <ex:monk/b> .\n<ex:monk/b> <https://example.org/unknown> "保全" .'
        p=m.import_legacy(text,'fixture.ttl');t,_=m.render(p);q=m.parse_v2(t)
        self.assertEqual(q['legacy_turtle'],text)
        a=next(a for a in q['assertions'] if a['predicate']==m.PREDICATES['generation']);self.assertEqual(a['object']['value'],'50');self.assertEqual(a['status'],'legacy_unverified')
        rel=next(a for a in q['assertions'] if a['predicate']==m.PREDICATES['teacher']);self.assertEqual(rel['object']['value'],q['person']['uri'])
    def test_10_graph_payload_tamper_rejected(self):
        t,_=m.render(example());t+='\n<https://example.org/p> <https://example.org/fake> "fact" .'
        with self.assertRaises(ValueError):m.parse_v2(t)
    def test_11_public_registry_gate(self):
        p=example();self.assertFalse(m.validate(p,{'LOCAL':{'license_verified':0,'redistribution_allowed':1}},True)['conforms'])
        p['sources'][0]['license_url']='https://creativecommons.org/licenses/by/4.0/'
        reg={'LOCAL':{'license_verified':1,'redistribution_allowed':1,'license_url':p['sources'][0]['license_url'],'source_version':'fixture-1'}}
        self.assertTrue(m.validate(p,reg,True)['conforms'])
        p['sources'][0]['version']='unapproved-release'
        self.assertFalse(m.validate(p,reg,True)['conforms'])
    def test_12_secret_not_exported(self):
        p=example();p['sources'][0]['snapshot']={'admin_session':'hidden'}
        self.assertFalse(m.validate(p)['conforms'])
    def test_13_malformed_fields_not_crash(self):
        for change in ('source','object','person'):
            p=example()
            if change=='source':p['sources']=[None]
            elif change=='object':p['assertions'][0]['object']=None
            else:p['person']['name_vi']=1
            self.assertFalse(m.validate(p)['conforms'])
    def test_14_date_expression_not_guessed(self):
        p=example();p['assertions'][0].update(predicate=m.PREDICATES['birth_expression'],object={'kind':'literal','value':'元嘉十九年；+0442-01-28 ~ +0443-02-15','language':'zh-Hant'})
        t,_=m.render(p);q=m.parse_v2(t);self.assertEqual(q,p)
        self.assertFalse(any(a['predicate']==m.PREDICATES['birth_year'] for a in q['assertions']))
    def test_15_review_date_invalid(self):
        p=example();accept(p['assertions'][0]);p['assertions'][0]['reviewed_at']='tomorrow'
        self.assertFalse(m.validate(p)['conforms'])
    def test_16_schema_and_shacl_positive_negative(self):
        import jsonschema
        from pyshacl import validate
        p=example();jsonschema.validate(p,json.loads((BASE/'ontology/ttl-profile-v2/schema.json').read_text(encoding='utf8')))
        t,_=m.render(p);g=Graph().parse(data=t,format='turtle')
        shapes=Graph().parse(data=(BASE/'ontology/ttl-profile-v2/shapes.ttl').read_text(encoding='utf8'),format='turtle')
        conforms,_,report=validate(g,shacl_graph=shapes);self.assertTrue(conforms,report)
        claim=next(g.subjects(RDF.type,m.PTH.Assertion));g.set((claim,m.PTH.status,Literal('accepted')))
        conforms,_,_=validate(g,shacl_graph=shapes);self.assertFalse(conforms)

class APITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.db=self.base/'test.db'
        c=sqlite3.connect(self.db);c.execute('CREATE TABLE data_sources(source_code TEXT, license_verified INT, redistribution_allowed INT)');c.execute('INSERT INTO data_sources VALUES (?,?,?)',('LOCAL',0,0));c.commit();c.close()
        def connect():
            c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row;return c
        app=Flask('t226_test');app.register_blueprint(create_ttl_profile_blueprint(self.base,connect,lambda t:t=='fixture-token'));self.client=app.test_client()
    def tearDown(self):self.temp.cleanup()
    def test_17_save_requires_auth(self):
        self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/save',json={'profile':example()}).status_code,401)
        self.assertFalse((self.base/'data').exists())
    def test_18_save_only_staging_idempotent(self):
        p=example();h={'X-Session-Token':'fixture-token'}
        d=self.client.post('/daoanh/api/admin/ttl_v2/save',json={'profile':p},headers=h).get_json()
        self.assertTrue(d['ok']);self.assertTrue(d['filepath'].startswith('data/ttl_v2/drafts/'))
        self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/save',json={'profile':p},headers=h).status_code,200)
        self.assertFalse((self.base/'data/ttl').exists())
    def test_19_client_cannot_claim_license(self):
        p=example();p['sources'][0].update(license_verified=1,license_url='https://creativecommons.org/licenses/by/4.0/')
        self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/render',json={'profile':p,'public':True}).status_code,422)
    def test_20_bad_json_returns_422(self):
        self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/render',json={'profile':{'person':None}}).status_code,422)
    def test_21_dila_mapping_without_artifact_not_accepted(self):
        p=example();p['person'].update(dila_id='A008431',name_zh='延福慧升')
        a=p['assertions'][0];a.update(predicate=m.PREDICATES['dila_id'],object={'kind':'literal','value':'A008431'});accept(a)
        self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/render',json={'profile':p}).status_code,422)
    def test_22_import_broken_turtle_not_saved(self):
        self.assertEqual(self.client.post('/daoanh/api/admin/ttl_v2/import',json={'ttl':'invalid RDF'}).status_code,422)

class LocalAuthorityTests(unittest.TestCase):
    def test_25_local_cbeta_marcus_preserve_raw_types(self):
        def connect():
            c=sqlite3.connect('file:'+str(BASE/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c
        app=Flask('local_sources');app.register_blueprint(create_ttl_profile_blueprint(BASE,connect,lambda t:False));client=app.test_client()
        response=client.get('/daoanh/api/admin/ttl_v2/local_sources/A000885')
        self.assertEqual(response.status_code,200)
        d=response.get_json();codes={s['code'] for s in d['sources']}
        self.assertTrue({'CBETA','MARCUS'}<=codes)
        marcus=next(s for s in d['sources'] if s['code']=='MARCUS')
        self.assertTrue(marcus['snapshot']['mapping'])
        self.assertTrue(all('relation_type' in edge for edge in marcus['snapshot']['edges']))
        self.assertTrue(all(a['status']=='draft' for a in d['assertions']))
        self.assertFalse(any(a['predicate']==m.PREDICATES['dharma_teacher'] for a in d['assertions']))
    def test_24_id_same_record_name_guard(self):
        archive=BASE/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
        p=profile_from_dila('A000885',dila_record(archive,'A000885'),'2026-09')
        a=next(a for a in p['assertions'] if a['predicate']==m.PREDICATES['dila_id']);accept(a)
        def connect():
            c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
            c.execute('CREATE TABLE data_sources(source_code TEXT,license_verified INT,redistribution_allowed INT)')
            c.execute('INSERT INTO data_sources VALUES (?,?,?)',('DILA',0,0));return c
        app=Flask('identity_guard');app.register_blueprint(create_ttl_profile_blueprint(BASE,connect,lambda t:False));client=app.test_client()
        p['person']['name_zh']='別人'
        self.assertEqual(client.post('/daoanh/api/admin/ttl_v2/render',json={'profile':p}).status_code,422)
        p['person']['name_zh']='雪竇重顯'
        self.assertEqual(client.post('/daoanh/api/admin/ttl_v2/render',json={'profile':p}).status_code,200)
    def test_23_real_dila_full_record_no_auto_accept(self):
        archive=BASE/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
        self.assertTrue(archive.exists(),'Cần artifact local đã khóa phiên bản để kiểm test này.')
        raw=dila_record(archive,'A000885');p=profile_from_dila('A000885',raw,'2026-09')
        self.assertIn('雪竇重顯',raw);self.assertEqual(p['person']['name_zh'],'重顯')
        self.assertEqual(p['sources'][0]['snapshot']['xml'],raw)
        self.assertTrue(all(a['status']=='source_asserted' for a in p['assertions']))
        t,_=m.render(p);self.assertEqual(m.parse_v2(t),p)
        self.assertTrue(any(a['predicate']==m.PREDICATES['work'] for a in p['assertions']))

if __name__=='__main__':unittest.main(verbosity=2)
