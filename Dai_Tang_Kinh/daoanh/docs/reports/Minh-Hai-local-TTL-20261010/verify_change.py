import argparse, hashlib, json
from pathlib import Path
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL
parser=argparse.ArgumentParser()
parser.add_argument('--active', action='store_true')
args=parser.parse_args()
base=Path(__file__).resolve().parent
root=base.parents[2]
manifest=json.loads((base/'manifest.json').read_text(encoding='utf8'))
target=root/manifest['target'] if args.active else base/'proposed.ttl'
backup=root/manifest['backup_file']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(backup)==manifest['before_sha256'], 'Backup hash changed'
assert sha(target)==manifest['after_sha256'], 'Target hash differs from proposed'
before=Graph().parse(backup,format='turtle')
after=Graph().parse(target,format='turtle')
main=URIRef('ex:monk/minh_hai_phap_bao')
teacher=URIRef('ex:monk/nguyen_thieu_sieu_bach')
bkg=Namespace('http://www.phatphaponline.org/ontology/buddhist-kg#')
pth=Namespace('https://www.phatphaponline.org/ontology/daoanh#')
assert set(after.objects(main,RDFS.label))=={Literal('Minh Hải Pháp Bảo',lang='vi'),Literal('明海法寶',lang='zh-Hant')}
assert set(after.objects(main,bkg.generationOrder))==set(before.objects(main,bkg.generationOrder))
assert int(next(after.objects(main,bkg.generationOrder)))==71
assert list(after.objects(main,bkg.hasTeacher))==[teacher]
assert not any(s==o for pred in [bkg.hasTeacher,bkg.hasDisciple] for s,o in after.subject_objects(pred))
assert not list(after.triples((None,OWL.sameAs,None)))
assert not list(after.triples((None,pth.dilaId,None)))
assert set(after.subjects(RDF.type,URIRef('bkg:Monk')))=={main}
removed=set(before)-set(after)
assert len(removed)==2 and all(s==main and p in [RDFS.label,bkg.biographicalNote] for s,p,o in removed), 'Unexpected removed triples'
assert all((s,p,o) in after for s,p,o in before if not(s==main and p in [RDFS.label,bkg.biographicalNote]))
assert len(list(after.objects(main,bkg.biographicalNote)))==1
bio=str(next(after.objects(main,bkg.biographicalNote)))
assert all(fragment in bio for fragment in ['Báo Tư','Chúc Thánh','Ma Ha Ca Diếp','71','A000662'])
assert list(after.objects(teacher,RDFS.label))==[Literal('Nguyên Thiều Siêu Bạch',lang='vi')]
ref=Graph().parse(root/'data/ttl/TS-Nguyen-Thieu-Sieu-Bach.ttl',format='turtle')
assert (teacher,bkg.hasDisciple,main) in ref
assert int(next(ref.objects(teacher,bkg.generationOrder)))==70
assert int(next(after.objects(main,bkg.generationOrder)))==int(next(ref.objects(teacher,bkg.generationOrder)))+1
rootGraph=Graph().parse(root/'data/ttl/Ton-Gia-Ma-Ha-Ca-Diep.ttl',format='turtle')
assert int(next(rootGraph.objects(URIRef('ex:monk/ma_ha_ca_diep'),bkg.generationOrder)))==1
assert set(after.objects(None,pth.status))=={Literal('source_asserted')}
for record in manifest['reference_files']:
    assert sha(root/record['path'])==record['sha256'], 'Reference file changed: '+record['path']
result={'mode':'active' if args.active else 'candidate','ok':True,'triples_before':len(before),'triples_after':len(after),'removed_triples':len(removed),'label_vi':'Minh Hải Pháp Bảo','generation_before':71,'generation_after':71,'teacher_generation':70,'counting_root_generation':1,'teacher_uri':str(teacher),'reciprocal_teacher_edge':True,'self_edges':0,'dila_id':None,'owl_sameAs_count':0,'reference_hashes_unchanged':True,'generation_assertion_status':'source_asserted','historical_chain_fully_verified':False}
(base/('verification-active.json' if args.active else 'verification-candidate.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\
',encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
