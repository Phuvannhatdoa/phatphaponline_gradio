import sys,json,re,hashlib
from pathlib import Path
D=Path.cwd()/'daoanh';sys.path.insert(0,str(D/'data/backups/T215-fix-sync-20261002/python-deps'))
from rdflib import Graph,URIRef,Literal,OWL,RDFS
O=D/'docs/reports/T215-eight-uri-20261003'; results=[]
for f in sorted((O/'prepared').glob('*.ttl')):
 g=Graph().parse(data=f.read_text(encoding='utf-8-sig'),format='turtle'); before=(D/'data/backups/T215-eight-uri-20261003'/f.name).read_text(encoding='utf-8-sig');after=f.read_text(encoding='utf-8')
 assert re.findall(r'generationOrder\s+(\d+)',before)==re.findall(r'generationOrder\s+(\d+)',after)
 assert re.findall(r'hasTeacher\s+<([^>]+)>',before)==re.findall(r'hasTeacher\s+<([^>]+)>',after)
 slug=re.search(r'<ex:monk/([^>]+)>\s+a\s+<bkg:Monk>',after).group(1)
 aid='A003636' if 'Phuoc' in f.name else 'A020545'
 assert (URIRef('ex:monk/'+slug),OWL.sameAs,URIRef('https://authority.dila.edu.tw/person/search.php?aid='+aid)) in g
 assert len(list(g.objects(URIRef('ex:monk/'+slug),RDFS.label)))==2
 for s,p,o in g:
  if str(p).endswith('hasTeacher'):assert s!=o
 if 'Dai-Ninh' in f.name:
  assert re.search(r'biographicalNote\s+"""(.*?)"""@vi',before,re.S).group(1)==re.search(r'biographicalNote\s+"""(.*?)"""@vi',after,re.S).group(1)
 results.append({'file':f.name,'rdf_triples':len(g),'generation_preserved':True,'teacher_preserved':True,'mapping':aid,'passed':True})
f=O/'candidates/A000960-only.ttl';g=Graph().parse(data=f.read_text(encoding='utf-8-sig'),format='turtle');assert 'tuyet_giau' not in f.read_text(encoding='utf-8');assert not any(str(p).endswith('generationOrder') for _,p,_ in g)
results.append({'file':'candidates/A000960-only.ttl','rdf_triples':len(g),'mapping_to_local_tuyet_giau':False,'passed':True})
(O/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(results,ensure_ascii=False))
