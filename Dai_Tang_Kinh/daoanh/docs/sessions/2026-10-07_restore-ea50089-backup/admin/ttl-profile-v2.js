/* T226: form có chứng cứ, DOM text an toàn, không suy số đời/định danh từ tên. */
(function () {
'use strict';
const $=id=>document.getElementById(id);
let profile,contract,ttl='',timer,serial=0,dbIdentifier='',batchJob='';
const api='/daoanh/api/admin/ttl_v2';
const labels={entity_type:'Loại thực thể có nguồn',name:'Tên',alternative_name:'Biệt danh',biography:'Tiểu sử',dila_id:'DILA ID',gender:'Giới tính',lineage:'Dòng phái',generation:'Số đời',founder:'Khai tổ',teacher:'Thầy chung → trò',dharma_teacher:'Thầy truyền pháp → trò',ordination_teacher:'Thầy thụ giới → trò',studied_with:'Tham học với',fellow_student:'Đồng môn',birth_expression:'Ngày sinh nguyên văn',death_expression:'Ngày mất nguyên văn',birth_year:'Năm sinh',death_year:'Năm mất',active_at:'Hoạt động tại',origin:'Quê quán',occupation:'Vai trò',work:'Tác phẩm',mentioned_in:'Văn bản nhắc đến',dynasty:'Triều đại',external_id:'Định danh ngoài',identity:'Đồng nhất URI · cần xác minh',other:'Ghi chú nguồn'};
const stateNames={draft:'Nháp',source_asserted:'Nguồn ghi nhận',accepted:'Đã duyệt',disputed:'Mâu thuẫn',rejected:'Bác bỏ',legacy_unverified:'TTL cũ · chưa xác minh'};
function status(message,ok) {const e=$('status-box');e.className='status-box '+(ok?'status-ok':'status-err');e.style.display='block';e.style.whiteSpace='pre-wrap';e.textContent=message;}
async function request(route,body) {
 const headers={'Content-Type':'application/json'};
 if(route==='/save'||route.startsWith('/batch')||route.startsWith('/generation/'))headers['X-Session-Token']=localStorage.getItem('admin_session')||'';
 const r=await fetch(api+route,body===undefined?{headers}:{method:'POST',headers,body:JSON.stringify(body)});
 let d;
 try {d=await r.json();} catch(e) {
  if(r.status===404)throw new Error('Server đang chạy chưa nạp chức năng TTL v2. Cần khởi động lại ứng dụng rồi tải lại trang.');
  throw new Error('Server chưa trả dữ liệu hồ sơ hợp lệ; thử tải lại trang.');
 }
 if(!r.ok||!d.ok){if(d.validation)showValidation(d.validation);throw new Error(d.error||'API trả lỗi '+r.status);}
 return d;
}
function showValidation(v) {
 $('validation').textContent=(v.conforms?'✓ Cấu trúc hợp lệ. Đây không phải chứng nhận lịch sử.':'✗ Cần sửa trước khi xuất.')+
 (v.errors.length?'\n'+v.errors.join('\n'):'')+
 (v.warnings.length?'\n'+v.warnings.length+' lưu ý; '+v.warnings.slice(0,5).join('\n')+(v.warnings.length>5?'\n… xem trạng thái từng nhận định.':''):'');
}
function dirty(){ttl='';$('ttl-preview').textContent='Hồ sơ đã thay đổi · đang kiểm tra…';clearTimeout(timer);timer=setTimeout(()=>preview(false).catch(e=>status(e.message,false)),450);}
async function preview(publicPackage) {
 const n=++serial;
 const d=await request('/render',{profile,public:!!publicPackage});
 if(n!==serial)return null;
 if(!publicPackage){ttl=d.ttl;$('ttl-preview').textContent=ttl;}
 showValidation(d.validation);
 return d;
}
function field(container,title,value,onChange,type='input',options) {
 const wrap=document.createElement('div');wrap.className='field';
 const label=document.createElement('label');label.textContent=title;
 const el=document.createElement(type);const id='v2_'+crypto.randomUUID();el.id=id;label.htmlFor=id;
 if(type==='select'){(options||[]).forEach(o=>{const opt=document.createElement('option');opt.value=o[0];opt.textContent=o[1];el.append(opt);});}
 el.value=value===undefined?'':value;
 if(type==='textarea')el.rows=3;
 el.addEventListener('change',()=>{onChange(el.value);dirty();});
 wrap.append(label,el);container.append(wrap);return el;
}
function button(parent,title,fn){const b=document.createElement('button');b.type='button';b.className='btn btn-secondary';b.textContent=title;b.addEventListener('click',fn);parent.append(b);return b;}
function drawSources() {
 const box=$('source-list');box.replaceChildren();
 profile.sources.forEach(s=>{
  const card=document.createElement('details');card.className='source-card';const summary=document.createElement('summary');
  summary.textContent=s.id+' · '+(s.code||'Nguồn mới')+' · '+(s.record_id||s.citation||'Chưa có định vị');card.append(summary);
  const grid=document.createElement('div');grid.className='row2';card.append(grid);
  const code=field(grid,'Mã nguồn',s.code,v=>{s.code=v;summary.textContent=s.id+' · '+v;});code.setAttribute('list','source-codes');
  [['record_id','ID record'],['version','Phiên bản / commit / edition'],['record_url','URL record / đoạn văn'],['dataset_url','URL bộ dữ liệu'],['retrieved_at','Ngày truy xuất · ISO 8601'],['sha256','SHA256 artifact / record'],['independence_key','Nguồn gốc chứng cứ · không phải tên website'],['license_url','URL giấy phép đúng artifact'],['rights_status','Trạng thái quyền sử dụng'],['attribution','Cách ghi công']].forEach(x=>field(grid,x[1],s[x[0]],v=>s[x[0]]=v));
  field(card,'Định vị, quyển, trang, dòng, trích dẫn nguyên văn',s.citation,v=>s.citation=v,'textarea');
  if(s.snapshot!==undefined){const info=document.createElement('p');info.className='hint';info.textContent='Nguyên bản record đã được giữ trong sourceSnapshot · '+JSON.stringify(s.snapshot).length+' ký tự.';card.append(info);}
  button(card,'Bỏ nguồn',()=>{if(profile.assertions.some(a=>(a.evidence||[]).includes(s.id))){status('Nguồn đang được nhận định sử dụng; gỡ liên kết chứng cứ trước.',false);return;}profile.sources=profile.sources.filter(x=>x!==s);drawSources();drawAssertions();dirty();});
  box.append(card);
 });
 $('source-summary').textContent=profile.sources.length+' record nguồn · '+profile.assertions.length+' nhận định. Registry local hiện có '+contract.sources.length+' nguồn; chưa xác minh danh mục 25 nguồn.';
}
function drawAssertions() {
 const box=$('assertion-list');box.replaceChildren();
 profile.assertions.forEach(a=>{
  const card=document.createElement('details');card.className='assertion-card';const summary=document.createElement('summary');
  const label=()=>{const key=Object.keys(contract.predicates).find(k=>contract.predicates[k]===a.predicate);summary.textContent=(labels[key]||'Thuộc tính mở')+' · '+String(a.object.value).slice(0,100)+' · '+stateNames[a.status||'draft'];};
  label();card.append(summary);
  const grid=document.createElement('div');grid.className='row2';card.append(grid);
  const opts=Object.entries(contract.predicates).map(x=>[x[1],labels[x[0]]||x[0]]);
  if(!opts.some(x=>x[0]===a.predicate))opts.push([a.predicate,'Thuộc tính đã nhập: '+a.predicate]);
  field(grid,'Loại nhận định',a.predicate,v=>{a.predicate=v;label();},'select',opts);
  field(grid,'Trạng thái',a.status||'draft',v=>{a.status=v;label();},'select',Object.entries(stateNames));
  field(card,'Subject URI · hướng quan hệ: thầy → trò',a.subject||profile.person.uri,v=>a.subject=v);
  field(grid,'Object là',a.object.kind,v=>{a.object.kind=v;label();},'select',[['literal','Giá trị / văn bản'],['iri','URI nhân vật / tài nguyên']]);
  field(grid,'Ngôn ngữ · vi, zh-Hant, en…',a.object.language||'',v=>a.object.language=v);
  field(card,'Giá trị / object URI',a.object.value,v=>{a.object.value=v;label();},'textarea');
  field(card,'Datatype URI · số đời dùng xsd:integer',a.object.datatype||'',v=>a.object.datatype=v);
  const ev=document.createElement('div');const evTitle=document.createElement('p');evTitle.className='hint';evTitle.textContent='Chứng cứ cho riêng nhận định này';ev.append(evTitle);
  profile.sources.forEach(s=>{const labelEl=document.createElement('label');labelEl.className='evidence-check';const cb=document.createElement('input');cb.type='checkbox';cb.checked=(a.evidence||[]).includes(s.id);cb.addEventListener('change',()=>{a.evidence=a.evidence||[];a.evidence=cb.checked?Array.from(new Set(a.evidence.concat(s.id))):a.evidence.filter(x=>x!==s.id);dirty();});labelEl.append(cb,document.createTextNode(s.id+' · '+(s.code||'')+' · '+(s.citation||s.record_id||'')));ev.append(labelEl);});card.append(ev);
  field(card,'Ngữ cảnh quan hệ / nguyên văn xác định loại',a.relation_scope||'',v=>a.relation_scope=v);
  field(card,'Hệ đếm số đời · gốc, đời đầu, nhánh, quy ước',a.counting_scheme||'',v=>a.counting_scheme=v);
  field(card,'Lập luận / mâu thuẫn / số cũ và số đúng',a.rationale||'',v=>a.rationale=v,'textarea');
  field(grid,'Người duyệt',a.reviewer||'',v=>a.reviewer=v);
  field(grid,'Ngày duyệt · ISO 8601',a.reviewed_at||'',v=>a.reviewed_at=v);
  button(card,'Bỏ nhận định',()=>{profile.assertions=profile.assertions.filter(x=>x!==a);drawAssertions();drawSources();dirty();});
  box.append(card);
 });
}
function setForm() {
 const p=profile.person;$('name_vi').value=p.name_vi||'';$('name_zh').value=p.name_zh||'';$('source_dila_id').value=p.dila_id||'';$('person_uri').value=p.uri;$('entity_type').value=p.entity_type||'Person';
 const map={bio_vi:'biography',birth_expression:'birth_expression',death_expression:'death_expression',source_gender:'gender',lineage_name:'lineage',gen_order:'generation',is_founder:'founder'};
 Object.entries(map).forEach(([id,key])=>{
  const candidates=profile.assertions.filter(x=>x.subject===p.uri&&x.predicate===contract.predicates[key]&&x.object.kind==='literal'&&(id!=='bio_vi'||x.object.language==='vi'));
  const a=candidates.find(x=>x.id==='editor_'+id)||candidates.find(x=>x.status==='accepted')||candidates.find(x=>(x.evidence||[]).some(s=>s.startsWith('db_vpa_')))||candidates[0];
  $(id).value=a?String(a.object.value):'';
 });
 const gen=profile.assertions.find(x=>x.predicate===contract.predicates.generation);$('counting_scheme').value=gen?.counting_scheme||'';
 $('legacy-info').textContent=profile.legacy_turtle?'Đã giữ toàn bộ TTL gốc: '+profile.legacy_turtle.length+' ký tự. Các triple chưa ánh xạ vẫn nằm nguyên trong originalTurtle.':'Hồ sơ mới; không có nguyên bản legacy.';
 drawSources();drawAssertions();
 window.dispatchEvent(new CustomEvent('generation-v2-results',{detail:profile.sources.filter(s=>s.id.startsWith('generation_v2_')).map(s=>s.snapshot)}));
}
function localSource() {
 let s=profile.sources.find(x=>x.id==='editorial');
 if(!s){s={id:'editorial',code:'LOCAL',record_id:'Vietnamese_editorial',citation:'Phật Tổ Đạo Ảnh · bản Việt dịch/biên tập chưa xác minh',version:'draft:'+profile.created_at,retrieved_at:new Date().toISOString(),rights_status:'pending_editorial_review'};profile.sources.push(s);}
 return s.id;
}
function baseAssertion(id,key,value,extra={}) {
 const aid='editor_'+id;const prior=profile.assertions.find(a=>a.id===aid);
 if(value===''){if(prior)profile.assertions=profile.assertions.filter(a=>a!==prior);return;}
 const obj={kind:'literal',value};
 if(['name_vi','bio_vi'].includes(id))obj.language='vi';
 if(id==='name_zh')obj.language='zh-Hant';
 if(id==='gen_order')obj.datatype='http://www.w3.org/2001/XMLSchema#integer';
 if(id==='is_founder')obj.datatype='http://www.w3.org/2001/XMLSchema#boolean';
 const a={id:aid,subject:profile.person.uri,predicate:contract.predicates[key],object:obj,status:'draft',evidence:[localSource()],derivation:'editorial_input',...extra};
 if(prior)Object.assign(prior,a);else profile.assertions.push(a);
}
function basicChange(id) {
 if(['name_vi','name_zh','source_dila_id','entity_type'].includes(id)){const k={source_dila_id:'dila_id'}[id]||id;profile.person[k]=$(id).value.trim();}
 const map={name_vi:'name',name_zh:'name',source_dila_id:'dila_id',bio_vi:'biography',birth_expression:'birth_expression',death_expression:'death_expression',source_gender:'gender',is_founder:'founder',lineage_name:'lineage',gen_order:'generation'};
 if(map[id])baseAssertion(id,map[id],$(id).value,id==='gen_order'?{counting_scheme:$('counting_scheme').value}:{});
 if(id==='counting_scheme'){const a=profile.assertions.find(x=>x.id==='editor_gen_order');if(a)a.counting_scheme=$(id).value;}
 drawSources();drawAssertions();dirty();
}
async function loadDb() {
 const id=$('db_record_id').value.trim()||$('source_dila_id').value.trim();
 if(profile.assertions.length||profile.sources.length||profile.legacy_turtle)throw new Error('Hồ sơ đang có dữ liệu. Dùng “Hồ sơ mới” trước khi nạp lại để giữ thông tin đang biên tập.');
 const d=await request('/from_db/'+encodeURIComponent(id));
 profile=d.profile;dbIdentifier=id;$('db_record_id').value=id;setForm();
 ttl=d.ttl;$('ttl-preview').textContent=ttl;showValidation(d.validation);
 status(d.note+(d.issues.length?'\n'+d.issues.length+' điểm giữ để đối chiếu: '+d.issues.slice(0,5).map(x=>x.type).join(', '):''),true);
}
async function downloadResponse(route,name) {
 const response=await fetch(api+route,{headers:{'X-Session-Token':localStorage.getItem('admin_session')||''}});
 if(!response.ok){let d={};try{d=await response.json();}catch(e){}throw new Error(d.error||'Không tải được file: '+response.status);}
 const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function exportDb() {
 const id=$('db_record_id').value.trim()||dbIdentifier||$('source_dila_id').value.trim();
 if(!id)throw new Error('Nhập DILA ID hoặc ttl:filename.ttl trước khi xuất.');
 await downloadResponse('/export_db/'+encodeURIComponent(id),'PTDA-'+id.replace(/[^A-Za-z0-9_.-]/g,'_')+'.ttl');
 status('Đã xuất trực tiếp từ DB. Để tải các thay đổi đang biên tập trên form, dùng “Tải TTL đang biên tập”.',true);
}
async function pollBatch() {
 try{
  const job=await request('/batch/'+batchJob);const c=job.counts||{};
  $('db-batch-status').textContent='Lô '+batchJob.slice(0,8)+' · '+(c.processed||0)+' đã xử lý · '+(c.exported||0)+' TTL đã xuất · '+(c.needs_review||0)+' cần kiểm tra'+(job.current_filename?' · '+job.current_filename:'');
  if(job.status==='running'){setTimeout(pollBatch,2000);return;}
  $('export-db-batch').disabled=false;
  if(job.status==='failed')throw new Error(job.error||'Xuất lô thất bại.');
  $('download-db-batch').hidden=false;
  status('Xuất lô hoàn tất. ZIP có TTL v2, manifest từng file và báo cáo; file chưa hợp lệ không được báo là đã xuất.',true);
 }catch(e){$('export-db-batch').disabled=false;status(e.message,false);}
}
async function startDbBatch() {
 $('export-db-batch').disabled=true;$('download-db-batch').hidden=true;
 try{const job=await request('/batch',{scope:'ttl'});batchJob=job.job_id;await pollBatch();}
 catch(e){$('export-db-batch').disabled=false;throw e;}
}
async function loadDila() {
 const aid=$('source_dila_id').value.trim();
 const existing=profile.sources.find(s=>s.id==='dila_record');
 if(existing&&existing.record_id!==aid)throw new Error('Hồ sơ đang có record DILA khác. Dùng “Hồ sơ mới” trước khi nhập nhân vật khác.');
 if(existing)throw new Error('Record DILA này đã nạp. Các nhận định và thông tin duyệt được giữ nguyên; dùng “Hồ sơ mới” nếu cần nạp lại từ nguồn.');
 const d=await request('/from_dila/'+encodeURIComponent(aid));
 const old=profile;const p=d.profile;const oldMain=old.person.uri;
 if(old.assertions.length||old.legacy_turtle){
  const newMain=p.person.uri;p.person.key=old.person.key;p.person.uri=oldMain;p.person.legacy_slug=old.person.legacy_slug||'';
  p.assertions.forEach(a=>{if(a.subject===newMain)a.subject=oldMain;if(a.object.kind==='iri'&&a.object.value===newMain)a.object.value=oldMain;});
 }
 p.person.name_vi=$('name_vi').value||old.person.name_vi||'';
 const keepSources=old.sources.filter(s=>s.id!=='dila_record'&&!s.id.startsWith('relation_'));
 p.sources.push(...keepSources.filter(s=>!p.sources.some(x=>x.id===s.id)));
 p.assertions.push(...old.assertions.filter(a=>!a.id.startsWith('dila_')&&!a.id.startsWith('editor_source_dila_id')));
 p.legacy_turtle=old.legacy_turtle||'';if(old.migration)p.migration=old.migration;
 profile=p;setForm();status(d.note,true);await preview(false);
}
async function loadLocalSources() {
 const aid=profile.person.dila_id;
 if(!aid||aid!==$('source_dila_id').value.trim())throw new Error('Nạp record DILA của nhân vật trước khi lấy các mapping/mentions local.');
 const d=await request('/local_sources/'+encodeURIComponent(aid));
 // Chỉ bổ sung ID mới; nạp lại không được xóa metadata nguồn hay nhận định đã biên tập/duyệt.
 const ids=new Set(profile.sources.map(s=>s.id));
 const addedSources=d.sources.filter(s=>!ids.has(s.id));profile.sources.push(...addedSources);
 const claimIds=new Set(profile.assertions.map(a=>a.id));
 profile.assertions.push(...d.assertions.filter(a=>!claimIds.has(a.id)).map(a=>({...a,subject:profile.person.uri})));
 drawSources();drawAssertions();status(addedSources.length+' record nguồn đã nạp mới; dữ liệu đã có được giữ nguyên. '+d.note,true);await preview(false);
}
function download(text,publicPackage) {
 const a=document.createElement('a');const url=URL.createObjectURL(new Blob([text],{type:'text/turtle;charset=utf-8'}));
 a.href=url;a.download='PTDA-'+profile.person.key+(publicPackage?'-public':'-draft')+'.ttl';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function importFile() {
 const input=$('ttl-import-input');const f=input.files[0];if(!f)return;
 try {if(f.size>8*1024*1024)throw new Error('File vượt 8 MB. Dùng migration theo từng file.');const d=await request('/import',{ttl:await f.text(),filename:f.name});profile=d.profile;setForm();await preview(false);status('Đã nhập để kiểm tra; file gốc và DB chưa thay đổi.',true);}finally{input.value='';}
}
async function transferredDraft() {
 const key=new URLSearchParams(location.search).get('draft');if(!key)return;
 const raw=sessionStorage.getItem('daoanh.personTTL.v1.'+key);if(!raw)throw new Error('Bản chuyển từ trang nhân vật không còn trong phiên; dữ liệu hiện tại được giữ nguyên.');
 const draft=JSON.parse(raw);const p=draft.person||{};
 $('source_dila_id').value=draft.person_id||p.person_id||p.id||'';$('name_vi').value=p.name_vi||'';profile.person.name_vi=$('name_vi').value;
 $('db_record_id').value=$('source_dila_id').value;await loadDb();
 profile.person.name_vi=p.name_vi||profile.person.name_vi;
 const sid='person_page_snapshot';
 profile.sources.push({id:sid,code:'LOCAL',record_id:profile.person.dila_id,citation:'Snapshot trang Admin person · gồm dữ liệu DILA, Việt dịch và trường đang sửa',version:'page-snapshot:'+draft.created_at,retrieved_at:new Date(draft.created_at||Date.now()).toISOString(),rights_status:'pending_review',snapshot:draft});
 const vi=draft.vi||{};$('bio_vi').value=vi.bio_vi||p.bio_vi||'';
 if($('bio_vi').value)baseAssertion('bio_vi','biography',$('bio_vi').value,{evidence:[sid],derivation:'Vietnamese_translation_page_snapshot'});
 if(p.dharma_lineage)baseAssertion('lineage_name','lineage',p.dharma_lineage,{evidence:[sid]});
 if(p.gen_lamte!==undefined&&p.gen_lamte!==null&&p.gen_lamte!=='')baseAssertion('gen_order','generation',String(p.gen_lamte),{evidence:[sid],status:'legacy_unverified',counting_scheme:'legacy_unspecified',rationale:'Số đời đang hiển thị trong DB; chưa xác minh hệ đếm và căn cứ.'});
 if(profile.person.name_vi)baseAssertion('name_vi','name',profile.person.name_vi,{evidence:[sid],derivation:'Vietnamese_translation'});
 setForm();$('draft-notice').style.display='block';$('draft-notice').textContent='Đã chuyển toàn bộ snapshot trang nhân vật. Thông tin cấu trúc lấy từ DB; snapshot trang web và bản Việt dịch được giữ riêng.';
}
async function init() {
 contract=await request('/schema');profile=contract.profile;
 contract.sources.forEach(s=>{const opt=document.createElement('option');opt.value=s.source_code;opt.label=s.source_name||s.source_code;$('source-codes').append(opt);});
 ['name_vi','name_zh','source_dila_id','entity_type','bio_vi','birth_expression','death_expression','source_gender','is_founder','lineage_name','gen_order','counting_scheme'].forEach(id=>$(id).addEventListener('change',()=>basicChange(id)));
 const actions={
  'compute-generation-v2':async()=>{const d=await request('/generation/attach',{profile});profile=d.profile;setForm();await preview(false);status('Đã tính theo từng hệ; kết quả dự kiến và đường truyền được giữ trong TTL. Số cũ vẫn giữ nguyên.',true);},
  'save-generation-v2':async()=>{const aid=profile.person.dila_id;if(!aid)throw new Error('Nạp DILA ID đã khóa trước khi lưu phép tính.');const d=await request('/generation/save_result/'+encodeURIComponent(aid),{});status(d.note+' · '+d.id,true);},
  'load-db':loadDb,
  'export-db-profile':exportDb,
  'export-db-batch':startDbBatch,
  'download-db-batch':async()=>{await downloadResponse('/batch/'+batchJob+'/download','PTDA-TTL-v2-'+batchJob.slice(0,8)+'.zip');},
  'load-dila':loadDila,
  'load-local-sources':loadLocalSources,
  'validate-profile':async()=>{await preview(false);status('Đã kiểm tra cấu trúc, nguồn và điều kiện duyệt.',true);},
  'save-profile':async()=>{const d=await request('/save',{profile});status(d.message+'\n'+d.filepath,true);},
  'download-profile':async()=>{const d=await preview(false);if(d)download(d.ttl,false);},
  'public-profile':async()=>{const d=await preview(true);if(d){download(d.ttl,true);status('Gói đã qua kiểm tra quyền nguồn trong registry.',true);}},
  'copy-profile':async()=>{const d=await preview(false);if(d){await navigator.clipboard.writeText(d.ttl);status('Đã copy TTL đã kiểm tra.',true);}},
  'add-source':async()=>{profile.sources.push({id:'source_'+crypto.randomUUID().replaceAll('-',''),code:'',version:'',citation:'',rights_status:'unknown'});drawSources();drawAssertions();dirty();},
  'add-assertion':async()=>{profile.assertions.push({id:'claim_'+crypto.randomUUID().replaceAll('-',''),subject:profile.person.uri,predicate:contract.predicates.other,object:{kind:'literal',value:'',language:'vi'},status:'draft',evidence:[]});drawAssertions();dirty();},
  'add-relation':async()=>{const d=await request('/from_dila/'+encodeURIComponent($('relation-id').value.trim()));if(d.profile.person.dila_id===profile.person.dila_id)throw new Error('Không thể tự làm thầy/trò/đồng môn.');const kind=$('relation-kind').value;const directional=['teacher','dharma_teacher','ordination_teacher'].includes(kind);const incoming=directional&&$('relation-direction').value==='teacher';const other=d.profile.person.uri;profile.assertions.push({id:'relation_'+crypto.randomUUID().replaceAll('-',''),subject:incoming?other:profile.person.uri,predicate:contract.predicates[kind],object:{kind:'iri',value:incoming?profile.person.uri:other},status:'draft',evidence:[],relation_scope:'Vị liên quan: '+d.profile.person.dila_id+' '+d.profile.person.name_zh+'; cần nguồn chứng minh quan hệ'});drawAssertions();dirty();},
  'reset-profile':async()=>{dbIdentifier='';$('db_record_id').value='';profile=(await request('/schema')).profile;ttl='';serial++;history.replaceState(null,'',location.pathname);$('draft-notice').style.display='none';setForm();$('ttl-preview').textContent='Hồ sơ mới · nhập tên hoặc nạp ID DILA.';status('Đã tạo hồ sơ mới; revision đã lưu vẫn được giữ.',true);}
 };
 Object.entries(actions).forEach(([id,fn])=>$(id).addEventListener('click',()=>Promise.resolve().then(fn).catch(e=>status(e.message,false))));
 $('ttl-import-input').addEventListener('change',()=>importFile().catch(e=>status(e.message,false)));
 setForm();await transferredDraft();
 const urlId=new URLSearchParams(location.search).get('db_id')||new URLSearchParams(location.search).get('person_id');
 if(urlId&&!profile.sources.length&&!profile.assertions.length){$('db_record_id').value=urlId;await loadDb();}
 if(profile.person.name_vi||profile.person.name_zh)await preview(false);else $('ttl-preview').textContent='Nhập tên hoặc nạp DILA ID để bắt đầu.';
}
init().catch(e=>status('Không khởi tạo được form v2: '+e.message,false));
}());
