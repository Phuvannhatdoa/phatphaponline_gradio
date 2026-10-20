# -*- coding: utf-8 -*-
"""T226: hồ sơ TTL có chứng cứ; lưu revision vào staging, không full-ETL/ghi DB."""
import hashlib, json, re, zipfile, xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from flask import Blueprint, jsonify, request
from src_python import ttl_profile_v2 as model

TEI='{http://www.tei-c.org/ns/1.0}'
XML='{http://www.w3.org/XML/1998/namespace}'

def dila_record(archive, aid):
    """Streaming đúng một record; không nạp toàn bộ authority XML vào RAM."""
    with zipfile.ZipFile(archive) as z:
        entry=next((n for n in z.namelist() if n.endswith('Person_Authority.xml')),None)
        if not entry:raise ValueError('Archive DILA không có Person Authority XML.')
        with z.open(entry) as stream:
            stack=[]
            for event,node in ET.iterparse(stream,events=('start','end')):
                if event=='start':stack.append(node);continue
                if node.tag==TEI+'person':
                    if node.get(XML+'id')==aid:return ET.tostring(node,encoding='unicode')
                    if len(stack)>1:stack[-2].remove(node)
                stack.pop()
    raise ValueError('ID không có trong bản DILA local đã khóa phiên bản.')

def profile_from_dila(aid,raw,version):
    node=ET.fromstring(raw);p=model.blank_profile('authority:DILA:'+aid)
    names=[{'text':''.join(n.itertext()).strip(),'language':n.get(XML+'lang',''),'type':n.get('type','primary')} for n in node.findall(TEI+'persName')]
    zh=[n['text'] for n in names if n['language'] in ('zho-Hant','zh-Hant','zh')]
    p['person'].update(dila_id=aid,name_zh=zh[0] if zh else '',entity_type='Person')
    p['sources']=[{'id':'dila_record','code':'DILA','record_id':aid,'record_url':'https://authority.dila.edu.tw/person/search.php?aid='+aid,'dataset_url':'https://github.com/DILA-edu/Authority-Databases','version':version,'retrieved_at':model.now(),'citation':'DILA TEI person xml:id='+aid,'sha256':model.digest(raw),'rights_status':'pending_registry_review','snapshot':{'xml':raw,'names':names}}]
    def add(key,value,language='',subject=None,kind='literal',evidence=None,**extra):
        if value is None or value=='':return
        obj={'kind':kind,'value':value}
        if language:obj['language']=language
        p['assertions'].append(dict(id='dila_'+str(len(p['assertions'])+1),subject=subject or p['person']['uri'],predicate=model.PREDICATES[key],object=obj,status='source_asserted',evidence=evidence or ['dila_record'],derivation='DILA_TEI_record',**extra))
    add('dila_id',aid)
    for n in names:add('name' if n['type']=='primary' else 'alternative_name',n['text'],{'zho-Hant':'zh-Hant','jpn':'ja','jpn-Latn':'ja-Latn'}.get(n['language'],n['language']))
    mapping={'concise':'biography','extensive':'biography','dynasty':'dynasty','placeOfOrigin':'origin','activeAt':'active_at','worksInTripitaka':'work','worksBy':'work','mentionedIn':'mentioned_in','birthDeathDateQuote':'other'}
    for n in node.findall(TEI+'note'):add(mapping.get(n.get('type'),'other'),''.join(n.itertext()).strip(),'zh-Hant')
    for tag,key in [('birth','birth_expression'),('death','death_expression'),('occupation','occupation'),('listBibl','mentioned_in')]:
        for n in node.findall(TEI+tag):add(key,''.join(n.itertext()).strip(),'zh-Hant')
    sex=node.find(TEI+'sex')
    if sex is not None and sex.get('value') in ('1','2'):add('gender',{'1':'Male','2':'Female'}[sex.get('value')])
    monk=next((n for n in node.findall(TEI+'note') if n.get('type')=='monk'),None)
    if monk is not None and ''.join(monk.itertext()).strip()=='是':
        p['person']['entity_type']='Monastic';add('entity_type',str(model.PTH.Monastic),kind='iri')
    if node.get('ana')=='historical':add('entity_type',str(model.CRM.E21_Person),kind='iri')
    for n in node.findall(TEI+'idno'):add('external_id',n.get('type','')+':'+''.join(n.itertext()).strip())
    for r in node.findall('.//'+TEI+'relation'):
        typ=r.get('type');other=r.get('active','')
        if typ not in ('teacher','student') or not re.fullmatch(r'A\d{6}',other):continue
        if other==aid:continue
        sid='relation_'+str(len(p['sources']))
        citation='; '.join(''.join(n.itertext()).strip() for n in r.findall('.//'+TEI+'bibl'))
        url=next((''.join(n.itertext()).strip() for n in r.findall('.//'+TEI+'ref') if n.get('type')=='url'),'')
        s={'id':sid,'code':'DILA','record_id':aid+':'+other,'version':version,'citation':citation or 'DILA relation '+typ,'rights_status':'pending_registry_review'}
        if model.iri(url):s['record_url']=url
        p['sources'].append(s)
        other_uri=model.person_uri(model.stable_key('authority:DILA:'+other))
        add('teacher',p['person']['uri'] if typ=='teacher' else other_uri,subject=other_uri if typ=='teacher' else p['person']['uri'],kind='iri',evidence=['dila_record',sid],relation_scope='DILA raw type='+typ+'; chưa xác nhận là truyền pháp',rationale=citation)
    return p

def create_ttl_profile_blueprint(base_dir,get_connection,verify_session):
    bp=Blueprint('ttl_profile_v2',__name__,url_prefix='/daoanh/api/admin/ttl_v2')
    base=Path(base_dir)
    archive=base/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
    @lru_cache(maxsize=24)
    def official(aid,mtime):
        return dila_record(archive,aid)
    def registry():
        conn=get_connection()
        try:return {r['source_code']:dict(r) for r in conn.execute('SELECT * FROM data_sources')}
        finally:conn.close()
    def read_body():
        if request.content_length and request.content_length>8*1024*1024:raise ValueError('Hồ sơ vượt 8 MB.')
        b=request.get_json(silent=True)
        if not isinstance(b,dict):raise ValueError('Cần JSON object.')
        return b
    def accepted_identity_errors(p):
        claims=[a for a in p['assertions'] if a.get('status')=='accepted' and a.get('predicate')==model.PREDICATES['dila_id']]
        if not claims:return []
        aid=p['person'].get('dila_id','')
        # T227: hồ sơ xuất từ DB kiểm trực tiếp record DB; không cần archive trong exporter.
        from src_python.ttl_db_export import raw_dila
        conn=get_connection()
        try:db_record=raw_dila(conn,aid)
        finally:conn.close()
        if db_record:
            names={''.join(n.itertext()).strip() for n in ET.fromstring(db_record['raw_text']).findall(TEI+'persName') if n.get(XML+'lang') in ('zho-Hant','zh-Hant','zh')}
            sm={s['id']:s for s in p['sources']}
            proven=all(any(sm.get(s,{}).get('code')=='DILA' and sm.get(s,{}).get('record_id')==aid and sm.get(s,{}).get('version')==db_record['version'] and sm.get(s,{}).get('sha256')==db_record['sha256'] for s in a.get('evidence',[])) for a in claims)
            if proven:
                return [] if p['person'].get('name_zh','').strip() in names else ['Tên Hán không khớp tên/biệt danh trên record DILA trong DB.']

        if not archive.exists():return ['Chưa có artifact DILA local để kiểm tên/ID; giữ mapping ở source_asserted.']
        raw=official(aid,archive.stat().st_mtime_ns);node=ET.fromstring(raw)
        names={''.join(n.itertext()).strip() for n in node.findall(TEI+'persName') if n.get(XML+'lang') in ('zho-Hant','zh-Hant','zh')}
        if p['person'].get('name_zh','').strip() not in names:return ['Tên Hán không khớp tên/biệt danh của chính ID trong DILA local; không duyệt mapping.']
        sm={s['id']:s for s in p['sources']}
        for a in claims:
            if not any(sm.get(s,{}).get('code')=='DILA' and sm.get(s,{}).get('record_id')==aid and sm.get(s,{}).get('version')=='2026-09' and sm.get(s,{}).get('sha256')==model.digest(raw) for s in a.get('evidence',[])):
                return ['Mapping được duyệt cần record DILA local đúng ID, phiên bản và SHA256; nạp bản authority trước.']
        return []
    def checked(b):
        p=model.normalize(b.get('profile'));reg=registry();public=b.get('public') is True
        result=model.validate(p,reg,public)
        if result['conforms']:
            result['errors'].extend(accepted_identity_errors(p));result['conforms']=not result['errors']
        return p,reg,public,result
    @bp.route('/schema')
    def schema():
        try:
            reg=registry()
            return jsonify(ok=True,version=model.VERSION,predicates=model.PREDICATES,statuses=model.STATUSES,profile=model.blank_profile(),sources=[{k:r.get(k) for k in ('source_code','source_name','source_version','repository_url','license_verified','redistribution_allowed','license_url','legal_status')} for r in reg.values()])
        except Exception:return jsonify(ok=False,error='Không đọc được registry local.'),503
    @bp.route('/from_dila/<aid>')
    def from_dila(aid):
        if not re.fullmatch(r'A\d{6}',aid):return jsonify(ok=False,error='DILA ID không hợp lệ.'),400
        try:
            from src_python.ttl_db_export import raw_dila
            conn=get_connection()
            try:cached=raw_dila(conn,aid)
            finally:conn.close()
            if cached:p=profile_from_dila(aid,cached['raw_text'],cached['version'])
            else:
                if not archive.exists():raise ValueError('Thiếu artifact DILA 2026-09 local; không đoán từ tên hiển thị.')
                p=profile_from_dila(aid,official(aid,archive.stat().st_mtime_ns),'2026-09')
            return jsonify(ok=True,profile=p,validation=model.validate(p,registry()),note='Bản authority local 2026-09; chưa phải bản web mới nhất. Mapping/quan hệ chưa được duyệt.')
        except ValueError as e:return jsonify(ok=False,error=str(e)),422
    @bp.route('/import',methods=['POST'])
    def import_file():
        try:
            b=read_body();text=b.get('ttl','')
            if not isinstance(text,str) or not text.strip():raise ValueError('File TTL rỗng.')
            from rdflib import Graph
            g=Graph().parse(data=text.lstrip('\ufeff'),format='turtle')
            p=model.parse_v2(text) if next(g.objects(None,model.PTH.profilePayload),None) is not None else model.import_legacy(text,str(b.get('filename','legacy.ttl')))
            return jsonify(ok=True,profile=p,validation=model.validate(p,registry()))
        except Exception as e:return jsonify(ok=False,error='Không nhập được TTL: '+str(e)[:500]),422
    @bp.route('/local_sources/<aid>')
    def local_sources(aid):
        """Bảo toàn record đã index; không coi mapping Marcus cũ là được duyệt."""
        if not re.fullmatch(r'A\d{6}',aid):return jsonify(ok=False,error='DILA ID không hợp lệ.'),400
        conn=get_connection()
        try:
            reg=registry();sources=[];claims=[]
            tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            def rows(sql,args):
                data=[dict(r) for r in conn.execute(sql+' LIMIT 501',args)]
                if len(data)>500:raise ValueError('Có hơn500 record liên quan; cần adapter phân trang, không cắt mất dữ liệu.')
                return data
            def source(sid,code,snapshot,citation):
                r=reg.get(code,{})
                s={'id':sid,'code':code,'record_id':aid,'version':r.get('source_version') or '', 'retrieved_at':model.now(),'citation':citation,'rights_status':'pending_artifact_review','snapshot':snapshot}
                if model.iri(r.get('repository_url')):s['dataset_url']=r['repository_url']
                s['sha256']=model.digest(json.dumps(snapshot,ensure_ascii=False,sort_keys=True))
                sources.append(s)
            if 'cbeta_person_mentions' in tables:
                mentions=rows('SELECT * FROM cbeta_person_mentions WHERE dila_person_id=? ORDER BY id',(aid,))
                if mentions:
                    source('cbeta_local_mentions','CBETA',mentions,'DB local cbeta_person_mentions; cần kiểm đúng edition/ID/đoạn văn')
                    for row in mentions:
                        claims.append({'id':'cbeta_mention_'+str(row['id']),'predicate':model.PREDICATES['mentioned_in'],'object':{'kind':'literal','value':json.dumps(row,ensure_ascii=False),'language':'zh-Hant'},'status':'draft','evidence':['cbeta_local_mentions'],'derivation':'local_index_unverified'})
            if {'marcus_people_link','marcus_reference','marcus_networks'}<=tables:
                links=rows('SELECT * FROM marcus_people_link WHERE person_id=? ORDER BY marcus_node_id',(aid,))
                if links:
                    records=[];edges={}
                    for link in links:
                        nid=link['marcus_node_id']
                        records.extend(rows('SELECT * FROM marcus_reference WHERE node_id=?',(nid,)))
                        for row in rows('SELECT * FROM marcus_networks WHERE teacher_id=? OR student_id=? ORDER BY id',(nid,nid)):edges[row['id']]=row
                        claims.append({'id':'marcus_mapping_'+str(len(claims)),'predicate':model.PREDICATES['external_id'],'object':{'kind':'literal','value':'MARCUS:'+nid},'status':'draft','evidence':['marcus_local'],'derivation':'legacy_crosswalk_unverified','rationale':'Giữ match_confidence/match_method trong snapshot; không phải mapping đã duyệt.'})
                    if len(edges)>500:raise ValueError('Mạng liên quan vượt500 cạnh; cần adapter phân trang.')
                    source('marcus_local','MARCUS',{'mapping':links,'people':records,'edges':list(edges.values())},'DB local Marcus; giữ relation_type/source_data/ref gốc; không tự chuyển cạnh mạng thành truyền pháp')
            return jsonify(ok=True,sources=sources,assertions=claims,note='Record local được giữ nguyên dưới snapshot; version registry chỉ là metadata cũ, cần khóa artifact trước duyệt. Không có record local không có nghĩa nguồn quốc tế không có dữ liệu.')
        except ValueError as e:return jsonify(ok=False,error=str(e)),422
        finally:conn.close()
    @bp.route('/render',methods=['POST'])
    @bp.route('/validate',methods=['POST'])
    def render_profile():
        try:
            p,reg,public,result=checked(read_body())
            if not result['conforms']:return jsonify(ok=False,validation=result,error='; '.join(result['errors'])),422
            ttl,_=model.render(p,reg,public)
            return jsonify(ok=True,ttl=ttl,validation=result)
        except (ValueError,TypeError,RecursionError) as e:return jsonify(ok=False,error=str(e)[:500]),422
    @bp.route('/save',methods=['POST'])
    def save():
        if not verify_session(request.headers.get('X-Session-Token','')):return jsonify(ok=False,error='Đăng nhập Admin để lưu revision.'),401
        try:
            p,reg,public,result=checked(read_body())
            if not result['conforms']:return jsonify(ok=False,validation=result,error='; '.join(result['errors'])),422
            ttl,_=model.render(p,reg,public)
            revision=hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True).encode('utf8')).hexdigest()
            folder=base/'data/ttl_v2/drafts'/p['person']['key'];folder.mkdir(parents=True,exist_ok=True)
            dest=folder/(revision+'.ttl')
            try:
                with dest.open('x',encoding='utf8',newline='\n') as f:f.write(ttl)
            except FileExistsError:
                # Không coi revision hỏng/khác là đã lưu thành công.
                if dest.read_text(encoding='utf8')!=ttl:raise ValueError('Revision tồn tại nhưng nội dung khác; giữ nguyên để kiểm tra.')
            return jsonify(ok=True,filepath=dest.relative_to(base).as_posix(),revision=revision,message='Đã lưu revision TTL v2 vào staging; DB và TTL đang chạy chưa thay đổi.',validation=result)
        except (ValueError,TypeError,RecursionError) as e:return jsonify(ok=False,error=str(e)[:500]),422
    # T227 — luồng DB → profile/TTL và xuất lô có xác thực.
    import threading,uuid,sqlite3
    from flask import Response,send_file
    from src_python import ttl_db_export,ttl_db_batch
    batch_lock=threading.Lock();batch_jobs={}
    @bp.route('/from_db/<path:identifier>')
    def from_db(identifier):
        conn=get_connection()
        try:
            conn.execute('BEGIN');result=ttl_db_export.export(conn,identifier)
            return jsonify(ok=True,**result,note='Hồ sơ được đọc trực tiếp từ DB; nguồn và trạng thái được giữ riêng. Không tự xác minh số đời/mapping.')
        except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
        finally:conn.close()
    @bp.route('/export_db/<path:identifier>')
    def export_db(identifier):
        conn=get_connection()
        try:
            conn.execute('BEGIN');result=ttl_db_export.export(conn,identifier)
            name='PTDA-'+(result['profile']['person']['dila_id'] or result['profile']['person']['key'])+'.ttl'
            return Response(result['ttl'],mimetype='text/turtle',headers={'Content-Disposition':'attachment; filename="'+name+'"','X-TTL-Source':'database'})
        except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
        finally:conn.close()
    @bp.route('/db_stats')
    def db_stats():
        conn=get_connection()
        try:
            from src_python import ttl_db_sources as src
            result={'dila_people':conn.execute('SELECT count(*) FROM people').fetchone()[0] if ttl_db_export.table(conn,'people') else 0,'source_records':{}}
            if src.available(conn):
                for r in conn.execute("SELECT s.kind,s.source_group,count(*) n FROM ttl_v2_source_records s JOIN ttl_v2_source_import_runs j ON j.id=s.import_run_id WHERE j.status='completed' GROUP BY s.kind,s.source_group"):
                    result['source_records'][r['kind']+':'+r['source_group']]=r['n']
            return jsonify(ok=True,**result)
        finally:conn.close()
    @bp.route('/batch',methods=['POST'])
    def start_batch():
        if not verify_session(request.headers.get('X-Session-Token','')):return jsonify(ok=False,error='Đăng nhập Admin để xuất bộ TTL.'),401
        acquired=False
        try:
            b=read_body();scope=b.get('scope','ttl')
            if scope!='ttl':raise ValueError('Trang Admin xuất bộ TTL local; scope DILA toàn bộ dùng CLI streaming.')
            if not batch_lock.acquire(blocking=False):return jsonify(ok=False,error='Một lô đang chạy; đợi lô đó hoàn tất.'),409
            acquired=True
            conn=get_connection()
            try:database_path=conn.execute('PRAGMA database_list').fetchone()[2]
            finally:conn.close()
            job_id=uuid.uuid4().hex;out=base/'data/ttl_v2/db_exports'/job_id
            job={'job_id':job_id,'status':'running','counts':{'processed':0,'exported':0,'needs_review':0}};batch_jobs[job_id]=job
            def worker():
                try:
                    def progress(counts,filename):job.update(counts=counts,current_filename=filename)
                    summary=ttl_db_batch.run(database_path,out,'ttl',progress=progress);job.update(status='done',counts=summary['counts'],summary=summary)
                except Exception as e:job.update(status='failed',error=str(e)[:1000])
                finally:batch_lock.release()
            threading.Thread(target=worker,daemon=True,name='ttl-db-export-'+job_id).start()
            acquired=False
            return jsonify(ok=True,**job),202
        except Exception as e:
            if acquired:batch_lock.release()
            return jsonify(ok=False,error=str(e)),422
    def stored_job(job_id):
        job=batch_jobs.get(job_id)
        if job:return job
        folder=base/'data/ttl_v2/db_exports'/job_id
        try:
            summary=json.loads((folder/'summary.json').read_text(encoding='utf8'))
            if summary.get('source_mode')=='database' and (folder/'ttl-v2.zip').is_file():
                return {'job_id':job_id,'status':'done','counts':summary['counts'],'summary':summary}
        except (OSError,ValueError,KeyError):pass
        return None
    @bp.route('/batch/<job_id>')
    def batch_status(job_id):
        if not verify_session(request.headers.get('X-Session-Token','')):return jsonify(ok=False,error='Đăng nhập Admin.'),401
        if not re.fullmatch(r'[a-f0-9]{32}',job_id):return jsonify(ok=False,error='Mã lô không hợp lệ.'),400
        job=stored_job(job_id)
        return (jsonify(ok=True,**job) if job else (jsonify(ok=False,error='Không có lô này trong phiên server hiện tại.'),404))
    @bp.route('/batch/<job_id>/download')
    def batch_download(job_id):
        if not verify_session(request.headers.get('X-Session-Token','')):return jsonify(ok=False,error='Đăng nhập Admin.'),401
        if not re.fullmatch(r'[a-f0-9]{32}',job_id):return jsonify(ok=False,error='Mã lô không hợp lệ.'),400
        file=base/'data/ttl_v2/db_exports'/job_id/'ttl-v2.zip'
        if not file.is_file() or (stored_job(job_id) or {}).get('status')!='done':return jsonify(ok=False,error='Lô chưa hoàn tất.'),409
        return send_file(file,as_attachment=True,download_name='PTDA-TTL-v2-'+job_id[:8]+'.zip')
    from api_generation_v2 import register_generation_routes
    register_generation_routes(bp,get_connection,verify_session)
    from api_codex_namevi import register_codex_name_routes
    register_codex_name_routes(bp,base,get_connection,verify_session)
    return bp
