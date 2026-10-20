# -*- coding: utf-8 -*-
"""T226: application profile RDF 1.1; nhận định nguồn không tự thành sự thật.
Đọc từng file, giữ nguyên legacy; không tính đời và không ghi DB nguồn.
"""
import copy, datetime, hashlib, json, re, uuid
from urllib.parse import urlparse
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD
VERSION='2.0.0'
BASE='https://www.phatphaponline.org/resource/'
PTH=Namespace('https://www.phatphaponline.org/ontology/daoanh#')
PROV=Namespace('http://www.w3.org/ns/prov#')
DCT=Namespace('http://purl.org/dc/terms/')
DCAT=Namespace('http://www.w3.org/ns/dcat#')
CRM=Namespace('http://www.cidoc-crm.org/cidoc-crm/')
SKOS=Namespace('http://www.w3.org/2004/02/skos/core#')
FOAF=Namespace('http://xmlns.com/foaf/0.1/')
BKG=Namespace('http://www.phatphaponline.org/ontology/buddhist-kg#')
STATUSES=('draft','source_asserted','accepted','disputed','rejected','legacy_unverified')
PREDICATES={
 'name':str(RDFS.label),'alternative_name':str(SKOS.altLabel),'biography':str(BKG.biographicalNote),'entity_type':str(RDF.type),
 'dila_id':str(PTH.dilaId),'gender':str(PTH.gender),'lineage':str(PTH.lineageMembership),
 'generation':str(PTH.generationNumber),'founder':str(PTH.isLineageFounder),
 'teacher':str(PTH.teacherOf),'dharma_teacher':str(PTH.dharmaTeacherOf),
 'ordination_teacher':str(PTH.ordinationTeacherOf),'studied_with':str(PTH.studiedWith),
 'fellow_student':str(PTH.fellowStudentOf),'birth_expression':str(PTH.birthDateExpression),
 'death_expression':str(PTH.deathDateExpression),'birth_year':str(PTH.birthYear),'death_year':str(PTH.deathYear),
 'active_at':str(PTH.activeAt),'origin':str(PTH.placeOfOrigin),'occupation':str(PTH.occupation),
 'work':str(PTH.associatedWork),'mentioned_in':str(PTH.mentionedIn),'dynasty':str(PTH.dynasty),
 'external_id':str(PTH.externalIdentifier),'identity':str(OWL.sameAs),'other':str(PTH.sourceNote)}
RELATIONS={PREDICATES[k] for k in ('teacher','dharma_teacher','ordination_teacher','studied_with','fellow_student')}
EDITORIAL_KEYS=('birth_year','death_year','birth_date','death_date','death_note','alt_names','occupation','place_of_origin','active_at','works_tripitaka','works_by','secondary_lit','mentioned_in','listbibl','name_latin','wikidata_id','dynasty_xml','sex','is_monk')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def stable_key(seed):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.phatphaponline.org/daoanh/'+seed))
def person_uri(key):return BASE+'person/'+key
def iri(value):
 return isinstance(value,str) and value.startswith(('https://','http://')) and not re.search(r'[\s<>"{}|\\^\x00-\x1f]',value)
def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def blank_profile(seed=None):
 key=stable_key(seed) if seed else str(uuid.uuid4())
 return {'profile_version':VERSION,'person':{'key':key,'uri':person_uri(key),'legacy_slug':'','name_vi':'','name_zh':'','dila_id':'','entity_type':'Person'},'sources':[],'assertions':[],'created_at':now(),'legacy_turtle':''}
def normalize(payload):
 if not isinstance(payload,dict):raise ValueError('Hồ sơ phải là JSON object.')
 p=copy.deepcopy(payload)
 allowed={'profile_version','person','sources','assertions','created_at','legacy_turtle','migration'}
 if set(p)-allowed:raise ValueError('Trường hồ sơ không hỗ trợ; dùng snapshot nguồn hoặc assertion để mở rộng.')
 def check_secrets(v):
  if isinstance(v,dict):
   for k,item in v.items():
    if str(k).lower() in {'password','api_key','apikey','access_token','session_token','admin_session','authorization'}:raise ValueError('Không lưu mật khẩu/token trong hồ sơ.')
    check_secrets(item)
  elif isinstance(v,list):
   for item in v:check_secrets(item)
 check_secrets(p)
 if p.get('profile_version')!=VERSION:raise ValueError('Phiên bản hồ sơ không hỗ trợ; cần '+VERSION)
 if not isinstance(p.get('person'),dict):raise ValueError('Thiếu nhân vật chính.')
 person=p['person'];key=person.get('key','')
 if not isinstance(key,str):raise ValueError('ID nội bộ phải là chuỗi.')
 for k in ('uri','name_vi','name_zh','dila_id','legacy_slug','entity_type'):
  if k in person and not isinstance(person[k],str):raise ValueError('Trường nhân vật '+k+' phải là chuỗi.')
 if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',key):raise ValueError('ID nội bộ không hợp lệ.')
 if person.get('uri')!=person_uri(key):raise ValueError('URI phải thuộc định danh ổn định đã cấp cho hồ sơ.')
 for k in ('sources','assertions'):
  if not isinstance(p.get(k),list):raise ValueError('Trường '+k+' phải là danh sách.')
 if len(p['sources'])>500 or len(p['assertions'])>3000:raise ValueError('Hồ sơ vượt giới hạn; dùng công cụ migration theo từng file.')
 for item in p['sources']+p['assertions']:
  if not isinstance(item,dict):raise ValueError('Nguồn và nhận định phải là object.')
 for s in p['sources']:
  for k in ('id','code','version','record_id','citation','record_url','dataset_url','license_url','sha256','independence_key','retrieved_at','rights_status','attribution'):
   if k in s and not isinstance(s[k],str):raise ValueError('Trường nguồn '+k+' phải là chuỗi.')
 for a in p['assertions']:
  for k in ('id','status','predicate','subject','reviewer','reviewed_at','rationale','relation_scope','counting_scheme','derivation','original_predicate'):
   if k in a and not isinstance(a[k],str):raise ValueError('Trường nhận định '+k+' phải là chuỗi.')
  if not isinstance(a.get('object'),dict):raise ValueError('Object nhận định phải là object.')
  if 'evidence' in a and (not isinstance(a['evidence'],list) or any(not isinstance(v,str) for v in a['evidence'])):raise ValueError('Evidence cần danh sách ID nguồn.')
 if not isinstance(p.get('legacy_turtle',''),str):raise ValueError('Legacy Turtle phải là chuỗi.')
 return p

def validate(payload, registry=None, public=False):
 """Kiểm cấu trúc và các điều kiện học thuật. accepted là duyệt tay, không phải AI tin cậy."""
 errors=[];warnings=[]
 try:p=normalize(payload)
 except ValueError as e:return {'conforms':False,'errors':[str(e)],'warnings':[]}
 person=p['person'];uri=person['uri'];source_map={};claims=set();registry=registry or {}
 if not person.get('name_vi','').strip() and not person.get('name_zh','').strip():errors.append('Cần ít nhất một tên hiển thị.')
 if person.get('dila_id') and not re.fullmatch(r'A\d{6}',person['dila_id']):errors.append('DILA ID phải có dạng A + 6 chữ số.')
 if person.get('entity_type','Person') not in ('Person','Monastic'):errors.append('Loại nhân vật không hợp lệ.')
 for s in p['sources']:
  sid=s.get('id','')
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',sid) or sid in source_map:errors.append('ID nguồn rỗng/trùng hoặc không hợp lệ: '+str(sid));continue
  source_map[sid]=s
  for field in ('record_url','dataset_url','license_url'):
   if s.get(field) and not iri(s[field]):errors.append('URL '+field+' không hợp lệ ở '+sid)
  if not s.get('record_url') and not s.get('citation'):warnings.append('Nguồn '+sid+' chưa có URL/định vị văn bản.')
  if not s.get('version'):warnings.append('Nguồn '+sid+' chưa khóa phiên bản; không giả là bản mới nhất.')
  if s.get('sha256') and not re.fullmatch(r'[a-f0-9]{64}',s['sha256']):errors.append('SHA256 nguồn không hợp lệ ở '+sid)
  if s.get('code') not in registry and s.get('code') not in ('LOCAL','LEGACY_TTL'):warnings.append('Nguồn '+s.get('code','')+' chưa có trong registry local; dùng làm draft.')
  if public:
   # Không tin checkbox license từ client; kiểm trạng thái thật của registry.
   r=registry.get(s.get('code',''),{})
   if not (r.get('license_verified')==1 and r.get('redistribution_allowed')==1 and
           s.get('license_url') and s.get('license_url')==r.get('license_url') and
           s.get('version') and s.get('version')==r.get('source_version')):
    errors.append('Chưa có hồ sơ quyền tái phân phối đúng phiên bản/giấy phép cho nguồn '+sid)
 for a in p['assertions']:
  aid=a.get('id','');status=a.get('status','draft');pred=a.get('predicate','');subject=a.get('subject',uri);obj=a.get('object',{})
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',aid) or aid in claims:errors.append('ID nhận định rỗng/trùng: '+str(aid))
  claims.add(aid)
  if status not in STATUSES:errors.append('Trạng thái nhận định không hợp lệ: '+str(aid))
  if not iri(pred) or not iri(subject):errors.append('Subject/predicate phải là HTTP(S) IRI ở '+str(aid))
  if obj.get('kind') not in ('literal','iri') or not isinstance(obj.get('value'),(str,int,float,bool)):errors.append('Object nhận định không hợp lệ ở '+str(aid));continue
  if obj['kind']=='iri' and not iri(obj['value']):errors.append('Object IRI không hợp lệ ở '+str(aid))
  lang=obj.get('language','');dt=obj.get('datatype','')
  if not isinstance(lang,str) or not isinstance(dt,str):errors.append('Language/datatype phải là chuỗi: '+str(aid));continue
  if lang and not re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*',lang):errors.append('Mã ngôn ngữ không hợp lệ ở '+str(aid))
  if lang and dt:errors.append('Literal không được đồng thời có language và datatype: '+str(aid))
  if dt and not iri(dt):errors.append('Datatype IRI không hợp lệ: '+str(aid))
  refs=a.get('evidence',[])
  if not isinstance(refs,list):errors.append('Evidence phải là danh sách ở '+str(aid));refs=[]
  if any(ref not in source_map for ref in refs):errors.append('Tham chiếu nguồn không tồn tại ở '+str(aid))
  if pred in RELATIONS:
   if obj.get('kind')!='iri':errors.append('Quan hệ nhân vật cần object IRI ở '+str(aid))
   if obj.get('value')==subject:errors.append('Không được tự làm thầy/trò/đồng môn: '+str(aid))
   if not a.get('relation_scope'):warnings.append('Quan hệ '+str(aid)+' chưa ghi ngữ cảnh; teacher chung không phải mặc nhiên truyền pháp.')
  if pred==str(RDF.type) and obj.get('kind')!='iri':errors.append('Loại thực thể cần object IRI ở '+str(aid))
  if pred==str(OWL.sameAs):
   if obj.get('kind')!='iri':errors.append('owl:sameAs cần object IRI định danh nhân vật ở '+str(aid))
   elif 'search.php?' in obj['value'] or '/wiki/' in obj['value']:errors.append('owl:sameAs chỉ cho URI nhân vật, không dùng trang hồ sơ/văn bản ở '+str(aid))
  if pred==str(PTH.generationNumber):
   val=str(obj.get('value',''))
   if obj.get('kind')!='literal' or not re.fullmatch(r'[1-9]\d*',val) or dt!=str(XSD.integer):errors.append('Số đời cần integer dương, không tự suy: '+str(aid))
   if not a.get('counting_scheme'):warnings.append('Số đời '+str(aid)+' chưa có hệ đếm, gốc, phạm vi.')
  if status=='accepted':
   if not refs or any(not source_map.get(ref,{}).get('citation','').strip() and not source_map.get(ref,{}).get('record_url') for ref in refs):errors.append('Nhận định được duyệt phải có nguồn/định vị: '+str(aid))
   if any(not source_map.get(ref,{}).get('version','').strip() for ref in refs):errors.append('Nhận định được duyệt cần phiên bản nguồn: '+str(aid))
   if registry and any(source_map.get(ref,{}).get('code') not in registry and source_map.get(ref,{}).get('code') not in ('LOCAL','LEGACY_TTL') for ref in refs):errors.append('Nguồn mới cần đăng ký trước khi duyệt nhận định: '+str(aid))
   if not a.get('reviewer','').strip() or not a.get('reviewed_at'):errors.append('Nhận định được duyệt cần người/ngày duyệt: '+str(aid))
   elif a.get('reviewed_at'):
    try:
     date=datetime.datetime.fromisoformat(a['reviewed_at'].replace('Z','+00:00'))
     if date.tzinfo is None:raise ValueError()
    except ValueError:errors.append('Ngày duyệt phải là ISO 8601 có timezone: '+str(aid))
   if pred==str(PTH.generationNumber):
    roots={source_map.get(ref,{}).get('independence_key','').strip() for ref in refs}-{''}
    if len(roots)<3:errors.append('Số đời được duyệt cần ít nhất 3 chứng cứ độc lập; ba bản sao cùng nguồn không tính: '+str(aid))
    if not a.get('counting_scheme','').strip() or not a.get('rationale','').strip():errors.append('Số đời được duyệt cần hệ đếm và lập luận số cũ/số đúng: '+str(aid))
   if pred==str(PTH.dilaId) and (str(obj.get('value'))!=person.get('dila_id') or subject!=uri):errors.append('DILA ID được duyệt phải đúng nhân vật chính: '+str(aid))
  elif status in ('draft','legacy_unverified'):warnings.append('Nhận định '+str(aid)+' được giữ làm tham chiếu, chưa chiếu thành fact.')
 # Chống vòng ở các cạnh truyền pháp đã duyệt trong cùng hồ sơ.
 edges={}
 for a in p['assertions']:
  if a.get('status')=='accepted' and a.get('predicate')==PREDICATES['dharma_teacher'] and a.get('object',{}).get('kind')=='iri':edges.setdefault(a.get('subject',uri),set()).add(a['object']['value'])
 visiting=set();done=set()
 def visit(n):
  if n in visiting:return True
  if n in done:return False
  visiting.add(n)
  bad=any(visit(d) for d in edges.get(n,()))
  visiting.remove(n);done.add(n);return bad
 if any(visit(n) for n in list(edges)):errors.append('Có vòng truyền pháp trong các nhận định đã duyệt.')
 if public and p.get('legacy_turtle'):errors.append('Gói public không được kèm nguyên TTL legacy chưa xác minh quyền dùng.')
 return {'conforms':not errors,'errors':list(dict.fromkeys(errors)),'warnings':list(dict.fromkeys(warnings))}

def object_term(obj):
 if obj['kind']=='iri':return URIRef(obj['value'])
 return Literal(obj['value'],lang=obj.get('language') or None,datatype=URIRef(obj['datatype']) if obj.get('datatype') else None)

def render(payload,registry=None,public=False):
 p=normalize(payload);result=validate(p,registry,public)
 if not result['conforms']:raise ValueError('; '.join(result['errors']))
 g=Graph()
 for prefix,ns in [('pth',PTH),('prov',PROV),('dcterms',DCT),('dcat',DCAT),('crm',CRM),('skos',SKOS),('foaf',FOAF),('bkg',BKG),('owl',OWL),('rdf',RDF),('rdfs',RDFS),('xsd',XSD)]:g.bind(prefix,ns)
 person=p['person'];main=URIRef(person['uri']);doc=URIRef(BASE+'dossier/'+person['key']);g.add((main,RDF.type,PTH.Person))
 # Loại điều hướng khác với khẳng định đã duyệt về tu sĩ/nhân vật lịch sử.
 g.add((main,PTH.editorialEntityType,Literal(person.get('entity_type','Person'))))
 g.add((doc,RDF.type,DCAT.Dataset));g.add((doc,RDF.type,PROV.Entity));g.add((doc,DCT.conformsTo,URIRef('https://www.phatphaponline.org/ontology/ttl-profile/2.0.0')));g.add((doc,PTH.profileVersion,Literal(VERSION)));g.add((doc,FOAF.primaryTopic,main));g.add((doc,PTH.accessLevel,Literal('public' if public else 'internal_draft')))
 # Snapshot JSON cho roundtrip, public chỉ được xuất sau gate rights; không nhúng secret/token.
 g.add((doc,PTH.profilePayload,Literal(json.dumps(p,ensure_ascii=False,sort_keys=True),datatype=RDF.JSON)))
 for lang,k in [('vi','name_vi'),('zh-Hant','name_zh')]:
  if person.get(k):g.add((main,PTH.displayName,Literal(person[k],lang=lang)))
 if person.get('legacy_slug'):g.add((main,PTH.legacyIdentifier,Literal(person['legacy_slug'])))
 for s in p['sources']:
  su=URIRef(BASE+'source-record/'+person['key']+'/'+s['id']);g.add((su,RDF.type,PTH.SourceRecord));g.add((su,RDF.type,PROV.Entity));g.add((doc,PROV.wasDerivedFrom,su));g.add((su,DCT.identifier,Literal(s['id'])));g.add((su,PTH.sourceCode,Literal(s.get('code',''))))
  for key,pred in [('record_id',PTH.sourceRecordId),('version',DCT.hasVersion),('citation',DCT.bibliographicCitation),('sha256',PTH.sha256),('independence_key',PTH.independenceKey),('attribution',DCT.rights),('retrieved_at',PTH.retrievedAt),('rights_status',PTH.rightsStatus)]:
   if s.get(key):g.add((su,pred,Literal(s[key])))
  for key,pred in [('record_url',FOAF.page),('dataset_url',PTH.datasetUrl),('license_url',DCT.license)]:
   if s.get(key):g.add((su,pred,URIRef(s[key])))
  if s.get('snapshot') is not None:g.add((su,PTH.sourceSnapshot,Literal(json.dumps(s['snapshot'],ensure_ascii=False,sort_keys=True),datatype=RDF.JSON)))
 for a in p['assertions']:
  au=URIRef(BASE+'assertion/'+person['key']+'/'+a['id']);sub=URIRef(a.get('subject',str(main)));pred=URIRef(a['predicate']);obj=object_term(a['object']);status=a.get('status','draft')
  g.add((au,RDF.type,PTH.Assertion));g.add((au,RDF.type,RDF.Statement));g.add((au,RDF.type,PROV.Entity));g.add((au,RDF.subject,sub));g.add((au,RDF.predicate,pred));g.add((au,RDF.object,obj));g.add((au,PTH.status,Literal(status)));g.add((doc,PTH.hasAssertion,au))
  for ref in a.get('evidence',[]):g.add((au,PROV.wasDerivedFrom,URIRef(BASE+'source-record/'+person['key']+'/'+ref)))
  for key,prop in [('rationale',PTH.rationale),('relation_scope',PTH.relationScope),('derivation',PTH.derivationMethod),('reviewer',PTH.reviewedBy),('reviewed_at',PTH.reviewedAt),('counting_scheme',PTH.countingScheme),('original_predicate',PTH.originalPredicate)]:
   if a.get(key):g.add((au,prop,Literal(a[key])))
  # RDF Statement n'entraîne pas le triple: projection explicite seulement après revue.
  if status=='accepted':g.add((sub,pred,obj))
 if p.get('legacy_turtle'):
  raw=p['legacy_turtle'];legacy=URIRef(BASE+'legacy/'+person['key']);g.add((legacy,RDF.type,PROV.Entity));g.add((legacy,PTH.originalTurtle,Literal(raw)));g.add((legacy,PTH.sha256,Literal(digest(raw))));g.add((doc,PROV.wasDerivedFrom,legacy))
 return g.serialize(format='turtle'),result

def parse_v2(text):
 g=Graph().parse(data=text.lstrip('\ufeff'),format='turtle');values=list(g.objects(None,PTH.profilePayload))
 if len(values)!=1:raise ValueError('TTL v2 phải có đúng một payload hồ sơ; không dùng regex để đoán.')
 p=normalize(json.loads(str(values[0])))
 expected,_=render(p)
 eg=Graph().parse(data=expected,format='turtle')
 # Không để payload âm thầm thay thế graph hoặc làm mất triple mở rộng.
 for graph in (g,eg):
  for triple in list(graph.triples((None,PTH.accessLevel,None))):graph.remove(triple)
 from rdflib.compare import isomorphic
 if not isomorphic(g,eg):raise ValueError('Graph và payload không khớp; giữ file gốc để review, không import mất triple.')
 return p

def import_legacy(text,filename='legacy.ttl'):
 """RDF reader: giữ nguyên biography, toàn file và triple lạ; không tạo sameAs từ nhãn."""
 g=Graph().parse(data=text.lstrip('\ufeff'),format='turtle')
 mains=set(g.subjects(RDF.type,URIRef('bkg:Monk')))|set(g.subjects(RDF.type,BKG.Monk))
 if len(mains)!=1:raise ValueError('TTL legacy cần đúng một nhân vật chính; file rỗng/trùng chủ thể phải review trước.')
 main=next(iter(mains));legacy_uri=str(main);slug=legacy_uri.rsplit('/',1)[-1]
 if not slug:raise ValueError('URI nhân vật legacy rỗng; không suy danh tính từ filename.')
 p=blank_profile('legacy:'+legacy_uri);person=p['person'];person['legacy_slug']=slug;person['entity_type']='Monastic';p['legacy_turtle']=text
 for lang,key in [('vi','name_vi'),('zh','name_zh')]:person[key]=next((str(v) for v in g.objects(main,RDFS.label) if getattr(v,'language',None) in (lang,lang+'-Hant')),'')
 p['sources']=[{'id':'legacy','code':'LEGACY_TTL','record_id':filename,'citation':filename,'version':'sha256:'+digest(text),'sha256':digest(text),'rights_status':'unknown','independence_key':'legacy:'+digest(text)}]
 # Candidate DILA ID không tự thành mapping đã xác minh.
 for obj in g.objects(main,OWL.sameAs):
  m=re.search(r'(?:aid=|/)(A\d{6})(?:$|[&#])',str(obj))
  if m:person['dila_id']=m[1]
 count=0
 for sub,pred,obj in sorted(g,key=lambda t:tuple(map(str,t))):
  if sub!=main:continue
  if pred in (RDF.type,RDFS.label):continue
  count+=1;target_pred=str(pred);object_value={'kind':'iri','value':str(obj)} if isinstance(obj,URIRef) else {'kind':'literal','value':str(obj)}
  if isinstance(obj,Literal):
   if obj.language:object_value['language']=obj.language
   elif obj.datatype:object_value['datatype']=str(obj.datatype)
  # Các URI legacy được lưu ở original_turtle; claim chuyển URI chính/tham chiếu theo seed, không kết luận đồng nhất DILA.
  if isinstance(obj,URIRef) and str(obj).startswith('ex:monk/'):
   if obj==main or pred in (BKG.hasTeacher,BKG.hasDisciple):
    object_value['value']=person_uri(stable_key('legacy:'+str(obj)))
   else:
    object_value['value']=BASE+'legacy-resource/'+stable_key('legacy:'+str(obj))
  if pred==BKG.hasTeacher:target_pred=PREDICATES['teacher'];subject=object_value['value'];object_value={'kind':'iri','value':person['uri']}
  else:subject=person['uri']
  if pred==BKG.hasDisciple:target_pred=PREDICATES['teacher']
  if pred==BKG.generationOrder:target_pred=PREDICATES['generation'];object_value['datatype']=str(XSD.integer)
  if pred==BKG.dharmaLineageName:target_pred=PREDICATES['lineage']
  if pred==BKG.isLineageFounder:target_pred=PREDICATES['founder']
  if pred==BKG.gender and str(obj) in ('bkg:Male','bkg:Female',str(BKG.Male),str(BKG.Female)):
   target_pred=PREDICATES['gender'];object_value={'kind':'literal','value':'Male' if str(obj).endswith('Male') else 'Female'}
  if pred==OWL.sameAs and 'search.php?' in str(obj):target_pred=str(PTH.authorityRecord);object_value={'kind':'iri','value':str(obj)}
  # Skip URI hệ ex:/bkg: không phải HTTP khi làm predicate/object claim; nguyên bản vẫn nguyên vẹn.
  if not iri(target_pred) or (object_value['kind']=='iri' and not iri(object_value['value'])):continue
  claim={'id':'legacy_'+str(count),'subject':subject,'predicate':target_pred,'object':object_value,'status':'legacy_unverified','evidence':['legacy'],'original_predicate':str(pred),'derivation':'legacy_migration'}
  if target_pred in RELATIONS:claim['relation_scope']='legacy_unspecified'
  if target_pred==PREDICATES['generation']:claim['counting_scheme']='legacy_unspecified'
  p['assertions'].append(claim)
 p['migration']={'source_filename':filename,'source_sha256':digest(text),'source_rdf_triples':len(g),'unknown_triples_preserved':True,'academic_reverification':False}
 return p
