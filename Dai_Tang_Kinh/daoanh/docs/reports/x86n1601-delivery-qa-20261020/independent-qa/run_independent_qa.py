from pathlib import Path
import hashlib, xml.etree.ElementTree as ET, json, contextlib, io, ast
from lxml import etree
base=Path('daoanh/docs/reports/x86n1601-delivery-qa-20261020').resolve(); p=base/'package/PTDA-X86n1601-pilot-v0.1'; out=base/'independent-qa'; out.mkdir(exist_ok=True)
log=io.StringIO()
def load(name,path):
 ns={'__name__':name,'__file__':str(path)};exec(compile(path.read_text(encoding='utf8'),str(path),'exec'),ns);return ns
before={f.relative_to(p).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
 print('ZIP_SHA256',hashlib.sha256((base/'package.zip').read_bytes()).hexdigest());print('SOURCE_SIZE',(p/'source/X86n1601.source.xml').stat().st_size)
 for line in (p/'SHA256SUMS.txt').read_text().splitlines():
  h,f=line.split(maxsplit=1);print('MANIFEST_HASH',f,before[f]==h)
 parser=etree.XMLParser(resolve_entities=False,no_network=True);schema=etree.XMLSchema(etree.parse(str(p/'schema/ptda-lineage-v1.xsd'),parser));doc=etree.parse(str(p/'derived/X86n1601.pilot.claims.xml'),parser);print('REAL_XSD_VALIDATION',schema.validate(doc),str(schema.error_log))
 v=load('qa_validate',p/'scripts/validate_package.py');print('BUNDLED_VALIDATOR',v['validate_claims_xml'](str(p/'derived/X86n1601.pilot.claims.xml')))
 tree=ast.parse((p/'tests/test_extraction.py').read_text())
 for n in ast.walk(tree):
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='claims_file' for t in n.targets):n.value=ast.Constant(str(p/'derived/X86n1601.pilot.claims.xml'))
 ns={'__name__':'qa_tests'};exec(compile(ast.fix_missing_locations(tree),'test_extraction_path_adapter','exec'),ns);print('BUNDLED_TESTS_PATH_ADAPTED',ns['test_extraction']())
 e=load('qa_extract',p/'scripts/extract_pilot_final.py');root=ET.parse(p/'source/X86n1601.source.xml').getroot();persons,mentions,rels=e['extract_lineage_data'](root)
 replay=e['build_claims_xml'](persons,mentions,rels,before['source/X86n1601.source.xml']);replaystr=e['format_xml'](replay);(out/'replay.claims.xml').write_text(replaystr,encoding='utf8')
 orig=ET.parse(p/'derived/X86n1601.pilot.claims.xml').getroot();rr=ET.fromstring(replaystr);n={'p':e['PTDA_NS']}
 for r in [orig,rr]:r.find('p:sourceManifest/p:downloadTime',n).text='NORMALIZED_FOR_COMPARISON'
 print('REPLAY_EQUAL_EXCEPT_DOWNLOAD_TIME',ET.tostring(orig)==ET.tostring(rr))
 fixture='''<TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:cb="http://www.cbeta.org/ns/1.0"><text><body><cb:div><cb:mulu>三十三祖</cb:mulu><list><item xml:id="test1"><note>第一祖</note>甲師<list><item>甲師未曾傳法予乙師，乙師不是其弟子。</item></list></item><item xml:id="test2"><note>第二祖</note>乙師<list><item>此為測試人物。</item></list></item></list></cb:div></body></text></TEI>'''
 (out/'synthetic-negative-fixture.xml').write_text(fixture,encoding='utf8');fp,fm,fr=e['extract_lineage_data'](ET.fromstring(fixture));print('NEGATIVE_FIXTURE_CLAIMS',json.dumps(fr,ensure_ascii=False));print('NEGATIVE_SEMANTIC_TEST_PASS',len(fr)==0)
 rows=[]
 for rel in rels:
  person=next(x for x in persons.values() if x['id']==rel['subject_person_id']);item=root.find(".//*[@{http://www.w3.org/XML/1998/namespace}id='"+person['xml_id']+"']");lbs=[x.get('n') for x in item.iter('{http://www.tei-c.org/ns/1.0}lb') if x.get('ed')=='X'];rows.append(dict(rel,source_item_id=person['xml_id'],locator_scope='subject item bounds, edition X; not exact claim span',source_lb_first=lbs[0] if lbs else None,source_lb_last=lbs[-1] if lbs else None,evidence_in_replayed_bio=rel['evidence_text'] in person['bio_text']))
 (out/'nine-claims-audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print('CLAIM_ROWS',json.dumps(rows,ensure_ascii=False))
after={f.relative_to(p).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()};log.write('\nPACKAGE_UNCHANGED '+str(before==after)+'\n');(out/'runtime-log.txt').write_text(log.getvalue(),encoding='utf8');(out/'package-hashes.json').write_text(json.dumps(before,indent=2),encoding='utf8');print(log.getvalue())
