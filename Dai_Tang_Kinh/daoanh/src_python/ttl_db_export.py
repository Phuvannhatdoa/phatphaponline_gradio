# -*- coding: utf-8 -*-
"""T227: xuất profile từ DB, không đọc XML/TTL file trong luồng export."""
import json,re,xml.etree.ElementTree as ET
from src_python import ttl_profile_v2 as m
from src_python import ttl_db_sources as records
TEI='{http://www.tei-c.org/ns/1.0}'
XML='{http://www.w3.org/XML/1998/namespace}'

def table(conn,name):return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None

def rows(conn,sql,args=(),limit=500):
 data=[dict(r) for r in conn.execute(sql+' LIMIT '+str(limit+1),args)]
 if len(data)>limit:raise ValueError('Hồ sơ có quá '+str(limit)+' record; cần phân trang thay vì cắt mất nguồn.')
 return data

def raw_dila(conn,aid):
 rec=records.latest(conn,'DILA_XML',aid)
 if rec:
  rec=dict(rec)
  if m.digest(rec['raw_text'])!=rec['sha256']:raise ValueError('SHA XML trong DB không khớp; giữ để kiểm tra.')
  node=ET.fromstring(rec['raw_text'])
  if node.get(XML+'id')!=aid:raise ValueError('XML ID không khớp khóa record DB.')
  return rec
 if table(conn,'people_full'):
  r=conn.execute('SELECT * FROM people_full WHERE id=?',(aid,)).fetchone()
  if r and r['raw_xml']:
   raw=r['raw_xml'];node=ET.fromstring(raw)
   if node.get(XML+'id')!=aid:raise ValueError('XML people_full không khớp ID.')
   return {'raw_text':raw,'version':'db-record:'+m.digest(raw),'sha256':m.digest(raw),'created_at':m.now(),'metadata_json':'{}'}
 return None

def safe_mapping(conn,slug):
 if not table(conn,'vn_person_authority'):return None
 candidates=rows(conn,'SELECT * FROM vn_person_authority WHERE id=?',(slug,))
 verified=[r for r in candidates if r.get('status')=='verified' and re.fullmatch(r'A\d{6}',r.get('dila_id') or '')]
 if len(verified)!=1:return None
 row=verified[0];aid=row['dila_id'];xml=raw_dila(conn,aid)
 if not xml:return None
 names={''.join(n.itertext()).strip() for n in ET.fromstring(xml['raw_text']).findall(TEI+'persName') if n.get(XML+'lang') in ('zho-Hant','zh-Hant','zh')}
 if not row.get('name_zh') or row['name_zh'].strip() not in names:return None
 mains=rows(conn,"SELECT id FROM vn_person_authority WHERE dila_id=? AND status='verified' AND ttl_filename IS NOT NULL AND ttl_filename!=''",(aid,))
 if len(mains)!=1:return None
 return aid

def _identifier_uri(conn,identifier):
 if re.fullmatch(r'A\d{6}',identifier or ''):return m.person_uri(m.stable_key('authority:DILA:'+identifier))
 mapped=safe_mapping(conn,identifier)
 return m.person_uri(m.stable_key('authority:DILA:'+mapped)) if mapped else m.person_uri(m.stable_key('legacy:ex:monk/'+identifier))

def from_db(conn,identifier):
 from api_ttl_profile_v2 import profile_from_dila
 if not isinstance(identifier,str) or len(identifier)>240:raise ValueError('Mã hồ sơ DB không hợp lệ.')
 aid=identifier if re.fullmatch(r'A\d{6}',identifier) else None;legacy=None
 if not aid:
  if identifier.startswith('ttl:'):legacy=records.latest(conn,'TTL',identifier[4:],group='active')
  elif identifier.startswith('slug:') and re.fullmatch(r'[A-Za-z0-9_-]+',identifier[5:]):legacy=records.latest(conn,'TTL',slug=identifier[5:],group='active')
  else:raise ValueError('Dùng DILA ID, ttl:filename.ttl hoặc slug:ten_slug.')
  if not legacy:raise ValueError('Không có nguồn TTL active này trong DB.')
  if m.digest(legacy['raw_text'])!=legacy['sha256']:raise ValueError('SHA TTL trong DB không khớp.')
  metadata=json.loads(legacy['metadata_json'])
  if metadata.get('error'):raise ValueError('Nguồn TTL chưa hợp lệ: '+metadata['error'])
  aid=safe_mapping(conn,legacy['main_slug']) if legacy['main_slug'] else None
 issues=[]
 person_row=dict(conn.execute('SELECT * FROM people WHERE id=?',(aid,)).fetchone() or {}) if aid and table(conn,'people') else {}
 xml=raw_dila(conn,aid) if aid else None
 if aid and not person_row and not xml:raise ValueError('DILA ID không có trong DB hệ thống.')
 if xml:
  p=profile_from_dila(aid,xml['raw_text'],xml['version']);p['created_at']=xml['created_at'];p['sources'][0]['snapshot']['db_source_metadata']=json.loads(xml['metadata_json']);p['sources'][0]['snapshot']['storage']='ttl_v2_source_records'
 elif legacy:
  p=m.import_legacy(legacy['raw_text'],legacy['filename']);p['person']['dila_id']=''
 else:
  p=m.blank_profile('authority:DILA:'+aid);p['person'].update(dila_id=aid,name_zh=person_row.get('name_zh') or '')
  issues.append({'type':'missing_raw_xml','message':'DB chỉ có trường DILA đã chuẩn hóa; chưa có XML đầy đủ.'})
 main=p['person']['uri'];source_ids={s['id'] for s in p['sources']};claim_ids={a['id'] for a in p['assertions']}
 def source(sid,code,snapshot,citation,record_id=''):
  if sid in source_ids:return sid
  serialized=json.dumps(snapshot,ensure_ascii=False,sort_keys=True);digest=m.digest(serialized)
  p['sources'].append({'id':sid,'code':code,'record_id':record_id or identifier,'version':'db-snapshot:'+digest,'sha256':digest,'citation':citation,'rights_status':'pending_artifact_review','snapshot':snapshot});source_ids.add(sid);return sid
 def add(key,value,sid,status='source_asserted',kind='literal',language='',subject=None,**extra):
  if value is None or value=='':return
  if key=='generation' and not re.fullmatch(r'[1-9]\d*',str(value)):
   issues.append({'type':'invalid_generation','value':value,'preserved_in':sid});return
  obj={'kind':kind,'value':str(value)}
  if language:obj['language']=language
  claim={'id':'db_'+str(len(claim_ids)+1),'subject':subject or main,'predicate':m.PREDICATES[key],'object':obj,'status':status,'evidence':[sid],'derivation':'system_DB_export',**extra}
  if key=='generation':obj['datatype']=str(m.XSD.integer)
  if key=='founder' and str(value) in ('0','1','false','true'):
   obj['value']='true' if str(value) in ('1','true') else 'false';obj['datatype']=str(m.XSD.boolean)
  p['assertions'].append(claim);claim_ids.add(claim['id'])
 if person_row:
  sid=source('db_people','DILA',person_row,'DB people; normalized import; Vietnamese fields are editorial',aid)
  for field,key in [('name_zh','name'),('name_en','alternative_name'),('name_ja','alternative_name'),('bio','biography'),('dynasty','dynasty'),('birth_year','birth_year'),('death_year','death_year'),('sect','lineage')]:add(key,person_row.get(field),sid,language={'name_zh':'zh-Hant','bio':'zh-Hant','name_en':'en','name_ja':'ja'}.get(field,''))
  vi=source('db_people_vi','LOCAL',{k:person_row.get(k) for k in ('id','name_vi','bio_vi','latin_source','source_origin')},'DB people: bản Việt hóa của hệ thống, không phải tên Việt do DILA cấp',aid)
  p['person']['name_vi']=person_row.get('name_vi') or ''
  add('name',person_row.get('name_vi'),vi,language='vi');add('biography',person_row.get('bio_vi'),vi,language='vi')
 if aid:
  add('dila_id',aid,source('db_identity','DILA',{'id':aid,'storage':'exact DB primary key'},'Khóa DILA ID chính xác trong DB',aid))
  if xml:p['assertions'][-1]['evidence'].append('dila_record')
  authorities=rows(conn,'SELECT * FROM vn_person_authority WHERE dila_id=? ORDER BY id',(aid,)) if table(conn,'vn_person_authority') else []
 else:authorities=rows(conn,'SELECT * FROM vn_person_authority WHERE id=?',(legacy['main_slug'],)) if table(conn,'vn_person_authority') else []
 attached=[]
 for v in authorities:
  sid=source('db_vpa_'+m.digest(v['id'])[:16],'LEGACY_TTL',v,'DB vn_person_authority; giữ status/mapping gốc',v['id'])
  verified=bool(aid and safe_mapping(conn,v['id'])==aid)
  if aid and not verified:
   issues.append({'type':'mapping_candidate','slug':v['id'],'dila_id':aid,'status':v.get('status'),'message':'Giữ row/snapshot; chưa ghép Việt dịch vào nhân vật DILA.'});continue
  if verified and v.get('ttl_filename'):
   filename=v['ttl_filename'];filename=filename if filename.endswith('.ttl') else filename+'.ttl'
   rec=records.latest(conn,'TTL',filename,group='active')
   if rec:attached.append(rec)
  if v.get('name_vi'):p['person']['name_vi']=v['name_vi'];add('name',v['name_vi'],sid,status='legacy_unverified',language='vi')
  for field,key in [('biographical_note_vi','biography'),('dharma_lineage','lineage'),('generation_order','generation'),('gender','gender'),('is_lineage_founder','founder'),('birth_year','birth_year'),('death_year','death_year')]:
   add(key,v.get(field),sid,status='legacy_unverified',language='vi' if key in ('biography','lineage') else '',counting_scheme='legacy_unspecified' if key=='generation' else '')
  for table_name in ('vn_person_relations','vn_person_events','vn_person_places','vn_person_works'):
   if table(conn,table_name):
    data=rows(conn,'SELECT * FROM '+table_name+' WHERE person_id=? ORDER BY id',(v['id'],))
    if data:source('db_'+table_name+'_'+m.digest(v['id'])[:10],'LEGACY_TTL',data,'DB '+table_name+'; dữ liệu nguyên bản theo slug',v['id'])
 if legacy and not aid:attached=[legacy]
 for rec in attached:
  if m.digest(rec['raw_text'])!=rec['sha256']:raise ValueError('SHA TTL trong DB không khớp.')
  sid=source('db_ttl_'+str(rec['id']),'LEGACY_TTL',{'filename':rec['filename'],'sha256':rec['sha256'],'raw_text':rec['raw_text'],'metadata':json.loads(rec['metadata_json'])},'TTL nguyên văn đã nhập DB: '+rec['filename'],rec['filename'])
  if not p.get('legacy_turtle'):p['legacy_turtle']=rec['raw_text']
  if aid:
   old=m.import_legacy(rec['raw_text'],rec['filename']);old_main=old['person']['uri']
   for a in old['assertions']:
    a=dict(a);a['id']='db_ttl_claim_'+str(len(claim_ids)+1);a['evidence']=[sid]
    if a['subject']==old_main:a['subject']=main
    if a['object'].get('kind')=='iri' and a['object']['value']==old_main:a['object']=dict(a['object'],value=main)
    p['assertions'].append(a);claim_ids.add(a['id'])
 if aid and table(conn,'person_bio_vi_draft'):
  virows=rows(conn,'SELECT * FROM person_bio_vi_draft WHERE person_id=?',(aid,))
  for v in virows:
   sid=source('db_bio_vi','LOCAL',v,'DB person_bio_vi_draft; giữ trạng thái admin_approved',aid);add('biography',v.get('bio_vi_draft'),sid,status='draft',language='vi')
 if aid and table(conn,'person_display_names'):
  names=rows(conn,'SELECT * FROM person_display_names WHERE person_id=? OR dila_person_id=? ORDER BY is_preferred DESC,id',(aid,aid))
  if names:
   sid=source('db_display_names','LOCAL',names,'DB person_display_names; tên hiển thị có provenance',aid)
   for n in names:add('name',n.get('display_name_vi'),sid,status='draft',language='vi')
 if aid and table(conn,'person_gen_computed'):
  gens=rows(conn,'SELECT * FROM person_gen_computed WHERE person_id=?',(aid,))
  if gens:
   sid=source('db_computed_generations','LOCAL',gens,'DB person_gen_computed; kết quả tính cũ, không phải chứng cứ xác minh',aid)
   for g in gens:
    for field in ('gen_sect','gen_lamte','gen_thientong'):
     add('generation',g.get(field),sid,status='legacy_unverified',counting_scheme='computed:'+str(g.get('lineage_key'))+':'+field,rationale='Giữ nguyên số trong DB; chưa xác minh theo ba nguồn độc lập.')
 if aid and table(conn,'lineage_edge_assertions'):
  edges=rows(conn,'SELECT * FROM lineage_edge_assertions WHERE subject_person_id=? OR object_person_id=? ORDER BY id',(aid,aid))
  for code in sorted({e['source_code'] for e in edges}):
   group=[e for e in edges if e['source_code']==code];sid=source('db_edges_'+re.sub(r'[^A-Za-z0-9_]','_',code),'LEGACY_TTL' if code=='TTL' else code,group,'DB lineage_edge_assertions; giữ nguồn, status, trust, raw_relation_type',aid)
   for e in group:
    if e['subject_person_id']==e['object_person_id']:issues.append({'type':'self_edge','edge_id':e['id'],'preserved_in':sid});continue
    if e['relation_type']!='da:isTeacherOf':issues.append({'type':'unmapped_relation','edge_id':e['id'],'preserved_in':sid});continue
    if not e['subject_person_id'] or not e['object_person_id']:
     issues.append({'type':'missing_edge_endpoint','edge_id':e['id'],'preserved_in':sid});continue
    teacher=_identifier_uri(conn,e['subject_person_id']);disciple=_identifier_uri(conn,e['object_person_id'])
    add('teacher',disciple,sid,status='rejected' if e['status']=='rejected' else ('source_asserted' if e['mapping_verified'] else 'legacy_unverified'),kind='iri',subject=teacher,relation_scope='DB da:isTeacherOf; không tự nâng thành truyền pháp',original_predicate=e.get('raw_relation_type') or '',rationale=e.get('ref') or '')
 if aid and table(conn,'cbeta_person_mentions'):
  data=rows(conn,'SELECT * FROM cbeta_person_mentions WHERE dila_person_id=? ORDER BY id',(aid,))
  if data:
   sid=source('db_cbeta','CBETA',data,'DB cbeta_person_mentions; giữ sigla, juan, page, context',aid)
   for r in data:add('mentioned_in',json.dumps(r,ensure_ascii=False),sid,status='draft',language='zh-Hant')
 if aid and table(conn,'marcus_people_link'):
  links=rows(conn,'SELECT * FROM marcus_people_link WHERE person_id=?',(aid,));network={};refs=[]
  for link in links:
   nid=link['marcus_node_id']
   if table(conn,'marcus_reference'):refs.extend(rows(conn,'SELECT * FROM marcus_reference WHERE node_id=?',(nid,)))
   if table(conn,'marcus_networks'):
    for e in rows(conn,'SELECT * FROM marcus_networks WHERE teacher_id=? OR student_id=?',(nid,nid)):network[e['id']]=e
  if len(network)>500:raise ValueError('Marcus vượt 500 cạnh; cần phân trang.')
  if links:
   sid=source('db_marcus','MARCUS',{'mapping':links,'people':refs,'edges':list(network.values())},'DB Marcus; giữ loại cạnh nguyên bản, không chuyển mạng thành truyền pháp',aid)
   for link in links:add('external_id','MARCUS:'+str(link['marcus_node_id']),sid,status='draft')
 # Self đã tồn tại được giữ trong original/source snapshot, không xuất thành quan hệ có hiệu lực.
 kept=[]
 for a in p['assertions']:
  if a['predicate'] in m.RELATIONS and a['object'].get('kind')=='iri' and a['subject']==a['object']['value']:
   issues.append({'type':'self_assertion','assertion_id':a['id'],'preserved_in':'originalTurtle/sourceSnapshot'});continue
  kept.append(a)
 p['assertions']=kept
 if not p['person']['name_vi'] and legacy:p['person']['name_vi']=m.import_legacy(legacy['raw_text'],legacy['filename'])['person']['name_vi']
 return m.normalize(p),issues

def registry(conn):
 return {r['source_code']:dict(r) for r in conn.execute('SELECT * FROM data_sources')} if table(conn,'data_sources') else {}

def export(conn,identifier):
 p,issues=from_db(conn,identifier)
 # T232: registry đã cài mới tính; không thay đổi legacy generation table.
 from src_python import generation_engine_v2 as gen
 if p['person'].get('dila_id') and table(conn,'generation_v2_scheme_revisions'):
  computed=gen.calculate_all(conn,p['person']['dila_id']);p=gen.attach_profile(p,computed)
  issues.extend({'type':'generation_'+r['status'],'scheme_id':r['scheme_id'],'message':r['message']} for r in computed['results'] if r['status'] not in ('candidate','derived_reviewable'))
 ttl,validation=m.render(p,registry(conn),False)
 return {'profile':p,'ttl':ttl,'validation':validation,'issues':issues,'source_mode':'database'}

def iter_identifiers(conn,scope='ttl'):
 if scope=='ttl':
  for row in records.iter_ttl(conn):yield 'ttl:'+row['filename'],row['filename']
 elif scope=='dila':
  if records.available(conn):
   sql="SELECT id FROM people UNION SELECT s.record_id FROM ttl_v2_source_records s JOIN ttl_v2_source_import_runs r ON r.id=s.import_run_id WHERE s.kind='DILA_XML' AND r.status='completed' ORDER BY 1"
  else:sql='SELECT id FROM people ORDER BY id'
  for (aid,) in conn.execute(sql):yield aid,aid+'.ttl'
 else:raise ValueError('Scope phải là ttl hoặc dila.')
