# -*- coding: utf-8 -*-
"""T233: API riêng không đổi Gemini/authority names."""
import json,re,threading,uuid,sqlite3,time
from flask import jsonify,request
from src_python import codex_namevi as model

def register_codex_name_routes(bp,base,get_connection,verify_session):
 lock=threading.Lock();operations={};cli_cache={"time":0,"value":{}}
 def subscription():
  if time.monotonic()-cli_cache["time"]>30:
   from scripts.codex_namevi_session import cli_status
   value=cli_status();value.pop("exe",None);cli_cache.update(time=time.monotonic(),value=value)
  return cli_cache["value"]
 def auth():return verify_session(request.headers.get('X-Session-Token',''))
 def body():
  if request.content_length and request.content_length>32768:raise ValueError('Request vượt giới hạn.')
  b=request.get_json(silent=True)
  if not isinstance(b,dict):raise ValueError('Cần JSON object.')
  return b
 def stored_folder(c,run):
  if not re.fullmatch(r'[a-f0-9]{32}',str(run)):raise ValueError('Run ID không hợp lệ.')
  row=c.execute('SELECT metadata_json FROM codex_name_job WHERE id=?',(run,)).fetchone()
  if not row:raise ValueError('Không có lô này.')
  # API chỉ dùng folder đã tạo dưới cây data; không nhận path từ client.
  key=json.loads(row[0]).get('folder_key','')
  if not re.fullmatch(r'[a-f0-9]{32}',key):raise ValueError('Lô CLI: dùng CLI để submit/collect.')
  return base/'data/codex_names'/key
 @bp.route('/codex_name/status')
 def codex_name_status():
  if not auth():return jsonify(ok=False,error='Đăng nhập Admin.'),401
  c=get_connection()
  try:
   return jsonify(ok=True,model=model.MODEL,prompt_version=model.PROMPT_VERSION,transport='codex_chatgpt_session',paid_api_enabled=False,api_key_configured=False,subscription=subscription(),**model.stats(c),operations=list(operations.values()))
  finally:c.close()
 @bp.route('/codex_name/lookup',methods=['POST'])
 def codex_name_lookup():
  if not auth():return jsonify(ok=False,error='Đăng nhập Admin.'),401
  c=get_connection()
  try:
   ids=body().get('ids')
   if not isinstance(ids,list) or len(ids)>200 or any(not isinstance(i,str) or not re.fullmatch(r'A\d{6}',i) for i in ids):raise ValueError('Cần tối đa 200 DILA ID chính xác.')
   if not ids or not model.exists(c,'codex_person_name'):return jsonify(ok=True,items=[])
   rows=[dict(r) for r in c.execute('SELECT n.*,p.name_zh current_name_zh,p.dynasty FROM codex_person_name n JOIN people p ON p.id=n.dila_id WHERE n.dila_id IN ('+','.join('?' for _ in ids)+')',ids)]
   for r in rows:
    r['stale']=model.record_hash({'dila_id':r['dila_id'],'name_zh':r['current_name_zh'],'dynasty':r['dynasty']})!=r['input_sha256'];r.pop('output_json',None)
   return jsonify(ok=True,items=rows)
  except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
  finally:c.close()
 @bp.route('/codex_name/list')
 def codex_name_list():
  if not auth():return jsonify(ok=False,error='Đăng nhập Admin.'),401
  c=get_connection()
  try:
   page=max(1,int(request.args.get('page',1)));size=min(100,max(1,int(request.args.get('per_page',50))));q=request.args.get('q','').strip()[:100]
   where='WHERE p.id LIKE ? OR p.name_zh LIKE ? OR p.name_vi LIKE ?' if q else '';args=['%'+q+'%']*3 if q else []
   total=c.execute('SELECT count(*) FROM people p '+where,args).fetchone()[0]
   available=model.exists(c,'codex_person_name');select='n.name_vi codex_name_vi,n.status codex_status,n.model codex_model,n.notes codex_notes,n.input_sha256' if available else "NULL codex_name_vi,NULL codex_status,NULL codex_model,NULL codex_notes,NULL input_sha256"
   join='LEFT JOIN codex_person_name n ON n.dila_id=p.id' if available else ''
   rows=[dict(r) for r in c.execute('SELECT p.id dila_id,p.name_zh,p.name_vi dila_name_vi,p.dynasty,'+select+' FROM people p '+join+' '+where+' ORDER BY p.id LIMIT ? OFFSET ?',args+[size,(page-1)*size])]
   for r in rows:r['stale']=bool(r['input_sha256'] and model.record_hash(r)!=r['input_sha256'])
   return jsonify(ok=True,items=rows,total=total,page=page,pages=(total+size-1)//size)
  except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
  finally:c.close()
 @bp.route('/codex_name/job',methods=['POST'])
 def codex_name_job():
  if not auth():return jsonify(ok=False,error='Đăng nhập Admin.'),401
  try:
   b=body();action=b.get('action')
   if action in ('submit','collect'):return jsonify(ok=False,error='API trả phí đã tắt theo yêu cầu Admin; dùng Codex đăng nhập ChatGPT.'),409
   if action not in ('prepare','run','pause'):raise ValueError('Action không hợp lệ.')
   from scripts import codex_namevi_session as session_runner
   if action=='pause':
    c=get_connection()
    try:
     folder=stored_folder(c,b.get('run_id'));(folder/'stop-requested').write_text('Admin yêu cầu dừng sau nhóm hiện tại.',encoding='utf8')
     return jsonify(ok=True,status='pause_requested')
    finally:c.close()
   if action=='run' and not subscription().get('authenticated'):return jsonify(ok=False,error='Máy server cần Codex CLI đăng nhập ChatGPT.'),409
   if not lock.acquire(blocking=False):return jsonify(ok=False,error='Một thao tác Codex đang chạy.'),409
   operation=uuid.uuid4().hex;operations[operation]={'id':operation,'action':action,'status':'running'}
   def work():
    c=None
    try:
     c=get_connection()
     if not model.exists(c,'codex_name_job'):raise ValueError('Chưa cài bảng Codex. Chạy installer có backup.')
     if action=='prepare':
      key=uuid.uuid4().hex;result=session_runner.prepare(c,base/'data/codex_names'/key)
      row=c.execute('SELECT metadata_json FROM codex_name_job WHERE id=?',(result['run_id'],)).fetchone();meta=json.loads(row[0]);meta['folder_key']=key
      c.execute('UPDATE codex_name_job SET metadata_json=? WHERE id=?',(model.dump(meta),result['run_id']));c.commit()
     else:
      folder=stored_folder(c,b.get('run_id'));result=session_runner.run(c,folder,max_groups=0)
     operations[operation].update(status='done',result=result)
    except Exception as e:operations[operation].update(status='failed',error=str(e)[:180])
    finally:
     if c is not None:c.close()
     lock.release()
   try:threading.Thread(target=work,daemon=True).start()
   except Exception:lock.release();raise
   return jsonify(ok=True,operation=operation,status='running'),202
  except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
