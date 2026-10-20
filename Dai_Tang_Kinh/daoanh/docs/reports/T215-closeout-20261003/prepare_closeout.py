# -*- coding: utf-8 -*-
"""T215: kế hoạch có hash, chứng cứ DILA và snapshot từng row. Chưa ghi TTL/DB."""
import sys,json,re,sqlite3,hashlib,zipfile,xml.etree.ElementTree as E,datetime
from pathlib import Path
D=Path.cwd()/'daoanh'; O=D/'docs/reports/T215-closeout-20261003'; B=D/'data/backups/T215-closeout-20261003'
sys.path.insert(0,str(D/'data/backups/T215-fix-sync-20261002/python-deps'))
from rdflib import Graph,URIRef,Namespace,RDF,RDFS,OWL
K=Namespace('http://www.phatphaponline.org/ontology/buddhist-kg#')
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
c=sqlite3.connect('file:'+str(D/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True); c.row_factory=sqlite3.Row
rr=lambda q,a=():[dict(r) for r in c.execute(q,a)]
quarantine={
 'TS-Dot-Khong-Tri-Ban.ttl':'Chiếm URI Bạch Vân; tên đã có chứng cứ CBETA nhưng chưa có DILA ID/thầy khóa đúng.',
 'TS-Tuyet-Giau-Chon-Phac.ttl':'Hai block Phong Huyệt/Nam Viện; chưa chứng minh Tuyết Hữu/Tuyết Giàu đồng nhất DILA.',
 'TS-Truong-Vien.ttl':'Chép biography và URI Phật Ý Linh Nhạc vào tên Trường Viễn; chưa xác minh người đúng.',
 'TS-Phuc-Chau-Dai-An.ttl':'Template rỗng: ex:monk/, nhãn và biography trống. Không suy danh tính từ filename.',
 'TS-Dai-Xa-Nhu-Truong.ttl':'File admin đã để trống; chỉ lưu dossier chứng cứ, không import.',
 'TS-Minh-Hoang-Tu-Dung.ttl':'File admin đã để trống; chưa có DILA ID xác minh.',
 'TS-Dao-Ninh-Dao-Khoan.ttl':'Bản trùng URI Đại Ninh; giữ TS-Dai-Ninh-Dao-Khoan.ttl đã xác minh A020545.'}
files=[]; parsed={}
for f in sorted((D/'data/ttl').glob('*.ttl')):
 if f.name=='0-template.ttl':continue
 raw=f.read_bytes(); txt=raw.decode('utf-8-sig'); rec={'file':f.name,'before_sha256':sha(raw)}
 if f.name in quarantine:rec.update(action='quarantine',reason=quarantine[f.name]);files.append(rec);continue
 g=Graph().parse(data=txt,format='turtle'); subjects=[s for s in g.subjects(RDF.type,None) if any(str(t).endswith('Monk') for t in g.objects(s,RDF.type))]
 if len(set(subjects))!=1:continue
 s=subjects[0]; slug=str(s).split('ex:monk/')[-1]
 parsed[f.stem]={'slug':slug,'teachers':[str(t).split('ex:monk/')[-1] for t in g.objects(s,K.hasTeacher)],'students':[str(t).split('ex:monk/')[-1] for t in g.objects(s,K.hasDisciple)],'label':str(next((x for x in g.objects(s,RDFS.label) if x.language=='vi'),'')),'bio':str(next(g.objects(s,K.biographicalNote),'')),'lineage':str(next(g.objects(s,K.dharmaLineageName),'')),'generation':str(next(g.objects(s,K.generationOrder),''))}
 if '\u00d0' in txt:
  assert not re.search(r'<[^>]*\u00d0[^>]*>|@prefix[^.]*\u00d0[^.]*\.|"[^"]*\u00d0[^"]*"@(?:zh|ja|sa)',txt),f.name
  new=txt.replace('\u00d0','\u0110'); g2=Graph().parse(data=new,format='turtle')
  def structural(h):return sorted((str(a),str(b),str(z)) for a,b,z in h if not hasattr(z,'language') or z.language not in ('vi',None))
  assert structural(g)==structural(g2); assert len(g)==len(g2)
  rec.update(action='text_fix',before_text=txt,after_text=new,characters=txt.count('\u00d0'),after_sha256=sha(new.encode('utf-8')));files.append(rec)
 # Thêm liên kết canonical, không đổi URI/quan hệ/đời.
 bindings={'TS-Ma-To-Dao-Nhat.ttl':('A003623','馬祖道一'),'TS-Phong-Huyet-Dien-Chieu.ttl':('A004982','風穴延沼'),'TS-Thach-Cuu.ttl':('A019919','石臼')}
 if f.name in bindings:
  aid,zh=bindings[f.name]; assert not list(g.objects(s,OWL.sameAs)),f.name+' đã có binding, kiểm lại'
  new=txt
  if '@prefix owl:' not in new:new='@prefix owl: <http://www.w3.org/2002/07/owl#> .\n'+new
  new+='\n<'+str(s)+'> owl:sameAs <https://authority.dila.edu.tw/person/search.php?aid='+aid+'> ;\n    rdfs:label "'+zh+'"@zh .\n'
  g2=Graph().parse(data=new,format='turtle'); assert (s,OWL.sameAs,URIRef('https://authority.dila.edu.tw/person/search.php?aid='+aid)) in g2
  rec.update(action='binding',after_text=new,after_sha256=sha(new.encode('utf-8')),dila_id=aid,name_zh=zh);files.append(rec)
# Bản trùng Đại Ninh: cùng main fields; khác chữ trong bio được lưu nguyên backup, không tự hợp văn bản.
a=parsed['TS-Dai-Ninh-Dao-Khoan']; rawdup=(D/'data/ttl/TS-Dao-Ninh-Dao-Khoan.ttl').read_bytes(); gd=Graph().parse(data=rawdup.decode('utf-8-sig'),format='turtle')
assert a['slug']=='dao_ninh_dao_khoan' and a['teachers']==['thach_suong_so_vien']
assert any(str(s)=='ex:monk/dao_ninh_dao_khoan' for s in gd.subjects(RDF.type,None))
assert list(gd.objects(URIRef('ex:monk/dao_ninh_dao_khoan'),K.hasTeacher))==[URIRef('ex:monk/thach_suong_so_vien')]
vpa=rr('select * from vn_person_authority'); mapping={r['id']:r['dila_id'] for r in vpa if r['dila_id']};mapping.update(ma_to_dao_nhat='A003623',phong_huyet_dien_chieu='A004982',phuoc_chau_dai_an='A003636',thach_cuu='A019919')
qrefs=[Path(f).stem for f in quarantine]+['TS-Linh-Cuu','TS-Di-Phong-Kinh-Ninh']
bad=rr("select * from lineage_edge_assertions where source_code='TTL' and status='active' and (ref in ("+','.join('?' for _ in qrefs)+") or subject_person_id='A038890' or object_person_id='A038890' or (ref in ('TS-Nam-Vien-Hue-Ngung','TS-Phong-Huyet-Dien-Chieu') and subject_person_id=object_person_id) or (ref='phong_huyet_dien_chieu' and (subject_person_id in ('dai_xa_nhu_truong','dao_man_moc_tran','tuyet_dau_chon_phac') or object_person_id in ('dai_xa_nhu_truong','dao_man_moc_tran','tuyet_dau_chon_phac'))))",qrefs)
# Đại Ninh duplicate assertions cùng cặp đúng: không rút nguồn hợp lệ, chỉ chuyển ref sang canonical.
bad=[r for r in bad if r['ref']!='TS-Dao-Ninh-Dao-Khoan']
candidates=[]
for f,p in parsed.items():
 for kind,targets in [('hasTeacher',p['teachers']),('hasDisciple',p['students'])]:
  for target in targets:
   if not ({p['slug'],target}&{'ma_to_dao_nhat','phong_huyet_dien_chieu','phuoc_chau_dai_an','thach_cuu'}):continue
   t,d=(target,p['slug']) if kind=='hasTeacher' else (p['slug'],target)
   if t in mapping and d in mapping:candidates.append({'teacher':mapping[t],'disciple':mapping[d],'ref':f,'raw_relation_type':kind,'local_teacher':t,'local_disciple':d})
ids={x[k] for x in candidates for k in ('teacher','disciple')}|{'A003636','A001897','A019919','A003623','A004981','A004982','A004983','A004015','A004980','A038890'}
records={}; n={'t':'http://www.tei-c.org/ns/1.0'}; archive=D/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
with zipfile.ZipFile(archive) as z:
 name=next(x for x in z.namelist() if x.endswith('Buddhist_Studies_Person_Authority.xml'))
 with z.open(name) as stream:
  for _,e in E.iterparse(stream,events=('end',)):
   if e.tag.split('}')[-1]!='person':continue
   aid=e.get('{http://www.w3.org/XML/1998/namespace}id')
   if aid in ids:records[aid]={'names':[''.join(x.itertext()).strip() for x in e.findall('t:persName',n)],'relations':[dict(x.attrib) for x in e.findall('.//t:relation',n)],'xml':E.tostring(e,encoding='unicode')}
   e.clear()
def verified(t,d):return any(x.get('type')=='teacher' and x.get('active')==t for x in records.get(d,{}).get('relations',[])) or any(x.get('type')=='student' and x.get('active')==d for x in records.get(t,{}).get('relations',[]))
assert '馬祖道一' in records['A003623']['names']; assert 'みちかず' in records['A038890']['names']; assert '風穴延沼' in records['A004982']['names']; assert verified('A003623','A019919') and verified('A004981','A004982') and verified('A001897','A003636')
accepted=[x for x in candidates if verified(x['teacher'],x['disciple']) and x['teacher']!=x['disciple']]; skipped=[x for x in candidates if x not in accepted]
plan={'created_at':datetime.datetime.now().isoformat(),'files':files,'bad_assertions':bad,'accepted_edges':accepted,'skipped_edges':skipped,'parsed_focus':{f:p for f,p in parsed.items() if p['slug'] in ('ma_to_dao_nhat','phong_huyet_dien_chieu','phuoc_chau_dai_an','thach_cuu','phat_y_linh_nhac')},'authority_before':[r for r in vpa if r['id'] in ('ma_to_dao_nhat','phong_huyet_dien_chieu','phuoc_chau_dai_an','phuc_chau_dai_an','thach_cuu','alias_A003623','phat_y_linh_nhac')],'quarantine_refs':qrefs,'generation_action':'Giữ nguyên số đời của mọi row đã có; row Phước Châu mới chỉ chép 37 tham chiếu TTL, không xác nhận thống kê đời.'}
dump(O/'dila-evidence.json',{'records':records,'archive_sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'source':'https://authority.dila.edu.tw/downloads/authority_person.2026-09.zip'})
dump(B/'change-plan.json',plan);dump(O/'plan-summary.json',{'file_actions':[(x['file'],x['action']) for x in files],'reject_ttl_assertions':len(bad),'verified_source_edges':len(accepted),'skipped_edges':len(skipped),'quarantine_reasons':quarantine,'generation_action':plan['generation_action']});print(json.dumps({'files':len(files),'reject':len(bad),'accepted':len(accepted),'skipped':len(skipped)},ensure_ascii=False))
