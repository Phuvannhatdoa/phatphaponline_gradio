"""T215: tạo hồ sơ từng file; không suy diễn DILA ID hay số đời; không ghi DB."""
import json,re,hashlib,zipfile,xml.etree.ElementTree as E,sqlite3
from pathlib import Path
R=Path.cwd(); D=R/'daoanh'; O=D/'docs/reports/T215-eight-uri-20261003'; B=D/'data/backups/T215-eight-uri-20261003'
O.mkdir(parents=True,exist_ok=True); (O/'prepared').mkdir(exist_ok=True); (O/'candidates').mkdir(exist_ok=True); B.mkdir(parents=True,exist_ok=True)
files=['TS-Phuoc-Chau-Dai-An.ttl','TS-Di-Phong-Kinh-Ninh.ttl','TS-Dot-Khong-Tri-Ban.ttl','TS-Dai-Ninh-Dao-Khoan.ttl','TS-Dai-Xa-Nhu-Truong.ttl','TS-Minh-Hoang-Tu-Dung.ttl','TS-Tuyet-Giau-Chon-Phac.ttl','TS-Linh-Cuu.ttl']
names=['Phước Châu Đại An','Di Phong Kính Ninh','Đột Không Trí Bản','Đại Ninh Đạo Khoan','Đại Xá Như Trường','Minh Hoằng Tử Dung','Tuyết Giàu Chơn Phác','Linh Cưu']
slugs=['phuoc_chau_dai_an','di_phong_kinh_ninh','dot_khong_tri_ban','dai_ninh_dao_khoan','dai_xa_nhu_truong','minh_hoang_tu_dung','tuyet_giau_chon_phac','linh_cuu']
ids=['A003636',None,None,'A020545',None,None,None,None]
notes=[
'URI và thầy trong file đã được sửa trước phiên này. DILA có alias 福州大安; thầy A001897 懷海. Bổ sung liên kết DILA, nhãn Hán, nguồn và tóm tắt Việt từ DILA; giữ đời 37.',
'File đang dùng URI bach_van_khong_do và nhãn Nguyệt Khê Diệu Trừng; biography trống. Chưa tìm được record DILA tương ứng 夷峰鏡寧/鏡寧/敬寧 trong XML2026-09 và tìm kiếm web. Không lấy ID của thầy làm ID trò. Bỏ qua sửa khi chưa xác minh.',
'File dùng URI bach_van_khong_do, tên Đột Không Trí Bản, đời61. Chưa tìm được ID cho 突空智板; A020174 突空昇 là người khác, không dùng. Chuỗi Di Phong → Trí Bản → Vô Tận là dữ liệu TTL chưa chứng nhận quốc tế. Bỏ qua sửa.',
'DILA A020545 có alias 大寧道寬, hoạt động 洪州大寧/同安, thầy A001439 楚圓; khớp tiểu sử Việt. TS-Dao-Ninh-Dao-Khoan.ttl là bản trùng cùng người/cùng URI, không phải người khác chiếm URI. Giữ dao_ninh_dao_khoan để không tạo thêm một người hoặc phá tham chiếu. Bổ sung owl:sameAs/nhãn Hán/nguồn trong file đích, giữ đời45. Chưa hợp nhất hai file hoặc đổi URI hàng loạt.',
'Có hai khối Monk cùng URI phong_huyet_dien_chieu và nhãn Nam Viện Huệ Ngung, cùng tiểu sử Phong Huyệt. Đời60/70, thầy To Đức/Tuyết Đậu và trò Giới Hải/Minh Hoằng trộn lẫn. Chưa khóa ID DILA cho Đại Xa/Đại Xá Như Trường (các biến thể 如長/如杖 chưa đủ). Không chọn số đời hoặc thầy theo khối cuối.',
'Có hai khối Phong Huyệt/Nam Viện, đời60/71, thầy/trò của hai người trộn lẫn. Tài liệu chính thức Order of Interbeing xác nhận Minh Hoằng 明弘, hiệu Tử Dung 子融, thầy của Liễu Quán. Chưa tìm được ID DILA tương ứng; A043469 明宏/梅芳 có hành trạng khác, không dùng. Quan hệ Đại Xá → Tử Dung chưa chứng nhận DILA.',
'Có hai khối Phong Huyệt/Nam Viện, đời60/69. A000960 真樸 có alias 雪槱真樸, thầy A001513 木陳道忞. Là ứng viên đáng kiểm; chưa chứng minh tên Việt Tuyết Giàu trong file này chính là 雪槱 (không phải 雪竇 Tuyết Đậu). DILA không liệt kê Đại Xá trong các quan hệ của record này. Tạo TTL ứng viên chỉ cho A000960 ở ngoài thư mục import, không gắn owl:sameAs vào URI Tuyết Giàu.',
'Đường dẫn TS-Linh-Cuu.ttl không tồn tại lúc kiểm. TS-Thach-Cuu.ttl tồn tại, nhãn Thạch Cữu, URI thach_cuu; DILA A019919 石臼, thầy A003623 道一 phù hợp Thạch Cữu. Không tái tạo Linh Cưu từ tiểu sử Thạch Cữu hoặc gán A019919 cho Linh Cưu. DB còn ttl_filename TS-Linh-Cuu cho thach_cuu: cần sửa provenance riêng sau đối chiếu.']
links=[['A003636','A001897'],[],['A020174'],['A020545','A001439'],[],[],['A000960','A001513'],['A019919','A003623']]
need=set(sum(links,[])); ns={'t':'http://www.tei-c.org/ns/1.0'}; records={}; archive=D/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
with zipfile.ZipFile(archive) as z:
 member=next(n for n in z.namelist() if n.endswith('Buddhist_Studies_Person_Authority.xml'))
 with z.open(member) as stream:
  for _,el in E.iterparse(stream,events=('end',)):
   if el.tag.split('}')[-1]!='person':continue
   aid=el.get('{http://www.w3.org/XML/1998/namespace}id')
   if aid in need:records[aid]={'names':[''.join(x.itertext()).strip() for x in el.findall('t:persName',ns)],'relations':[dict(x.attrib) for x in el.findall('.//t:relation',ns)],'xml':E.tostring(el,encoding='unicode')}
   el.clear()
def sha(data):return hashlib.sha256(data).hexdigest()
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
meta={'source':'https://authority.dila.edu.tw/downloads/authority_person.2026-09.zip','archive':str(archive.relative_to(D)).replace('\\','/'),'sha256':filehash(archive),'checked':'2026-10-03','record_count':len(records),'scope':'XML 2026-09 + official web; no-match means unconfirmed, not proof of absence from all DILA versions.'}
(O/'dila-evidence.json').write_text(json.dumps({'source':meta,'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
cases=[]; changes=[]
for i,(fn,name,slug,aid,note,ll) in enumerate(zip(files,names,slugs,ids,notes,links),1):
 p=D/'data/ttl'/fn; exists=p.exists(); raw=p.read_bytes() if exists else b''; text=raw.decode('utf-8-sig') if exists else ''
 if exists and not (B/fn).exists():(B/fn).write_bytes(raw)
 diagnosis=[{'line':n,'text':s.strip()} for n,s in enumerate(text.splitlines(),1) if re.search(r'a\s+<bkg:Monk>|rdfs:label|P1_is_identified|generationOrder|hasTeacher|hasDisciple|birthEvent|deathEvent',s)]
 state='đã bổ sung định danh trong TTL; DB chưa cập nhật' if aid else ('file không tồn tại; bác bỏ đổi Thạch Cữu thành Linh Cưu' if not exists else 'chưa xác minh DILA — bỏ qua sửa')
 c={'case':i,'file':fn,'name_vi':name,'exists':exists,'status':state,'dila_id':aid,'proposed_uri':slug,'generation_action':'giữ nguyên; chưa đủ 3 chứng cứ độc lập','note':note,'evidence_links':['https://authority.dila.edu.tw/person/search.php?aid='+a for a in ll],'current_lines':diagnosis,'before_sha256':sha(raw) if exists else None,'db_action':'read-only; không sync'}
 if i==6:c['evidence_links']+=['https://orderofinterbeing.org/docs/TNH-Tradition-Lineage.pdf']
 if aid:
  text=text.replace('@prefix xsd:', '@prefix owl: <http://www.w3.org/2002/07/owl#> .\n@prefix dct: <http://purl.org/dc/terms/> .\n@prefix dila: <https://authority.dila.edu.tw/person/search.php?aid=> .\n@prefix xsd:',1)
  zh='福州大安' if i==1 else '大寧道寬'
  text=text.replace('    rdfs:label "'+name+'"@vi ;','    rdfs:label "'+name+'"@vi ;\n    rdfs:label "'+zh+'"@zh-Hant ;\n    owl:sameAs dila:'+aid+' ;\n    dct:source dila:'+aid+' ;',1)
  if i==1:
   bio='Thiền sư Đại An ở Phước Châu, còn có tên Trường Khánh Đại An và Lãn An, sống đời Đường. Sư họ Trần, ban đầu học luật ở Hoàng Bá, sau đến tham học Bách Trượng Hoài Hải và lãnh hội tông chỉ. Sư cùng Linh Hựu dựng đạo tràng ở Quy Sơn, về sau trụ trì chùa Trường Khánh tại Phước Châu. Tóm tắt Việt từ DILA A003636; không phải bản dịch toàn văn kinh.'
   text=text.replace('bkg:biographicalNote """"""@vi','bkg:biographicalNote """'+bio+'"""@vi',1)
  teacher='bach_truong_hoai_hai' if i==1 else 'thach_suong_so_vien'; tid='A001897' if i==1 else 'A001439'
  text+='\n# Định danh thầy được đối chiếu DILA; số đời vẫn giữ bản TTL cũ.\n<ex:monk/'+teacher+'> owl:sameAs dila:'+tid+' .\n'
  if i==4:text=text.replace('bkg:dharmaLineageName "Thiền Tông Trung Hoa - Nam Tông"@vi','bkg:dharmaLineageName "Tông Lâm Tế Trung Hoa"@vi',1)
  prepared=O/'prepared'/fn;prepared.write_text(text,encoding='utf-8');c['prepared_file']='prepared/'+fn;c['after_sha256']=filehash(prepared)
  changes.append({'file':fn,'before_sha256':sha(raw),'after_sha256':filehash(prepared),'backup':'data/backups/T215-eight-uri-20261003/'+fn})
 cases.append(c)
# Ứng viên chỉ mô tả record DILA A000960, không khẳng định URI Tuyết Giàu.
prefix='''@prefix pth: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix dila: <https://authority.dila.edu.tw/person/search.php?aid=> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dct: <http://purl.org/dc/terms/> .
'''
candidate=prefix+'''# CANDIDATE ONLY: chưa chứng minh Tuyết Giàu Chơn Phác = 雪槱真樸.
# Không đưa file này vào data/ttl hay chạy import/sync.
<urn:daoanh:draft:dila:A000960> a pth:Monk ;
    rdfs:label "雪槱真樸"@zh-Hant ;
    rdfs:label "Chân Phác, hiệu Tuyết Dữu (bản đọc Hán Việt đề xuất)"@vi ;
    owl:sameAs dila:A000960 ;
    dct:source dila:A000960 ;
    pth:hasTeacher dila:A001513 ;
    pth:biographicalNote "Chân Phác, hiệu 雪槱, họ Từ, người Chương Châu, pháp tự của Mộc Trần Đạo Mẫn. Niên đại sinh và mất chưa rõ. Tóm tắt từ DILA; tên Việt cần duyệt."@vi .
# Không thêm số đời, quan hệ Đại Xá, hoặc owl:sameAs tới URI Tuyết Giàu.
'''
(O/'candidates/A000960-only.ttl').write_text(candidate,encoding='utf-8')
(O/'cases.json').write_text(json.dumps({'task':'T215','checked':'2026-10-03','source':meta,'cases':cases,'summary':{'checked':8,'ttl_updates_prepared':2,'unconfirmed_existing':5,'missing':1,'candidate_only':1,'db_writes':0,'generation_changes':0}},ensure_ascii=False,indent=2),encoding='utf-8')
(B/'manifest.json').write_text(json.dumps({'task':'T215','changes':changes,'db_writes':0},ensure_ascii=False,indent=2),encoding='utf-8')
print('8 hồ sơ, 2 bản TTL chuẩn bị, 1 ứng viên DILA riêng. Không ghi DB.')
