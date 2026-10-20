/* T232: UI Admin dùng form, không yêu cầu viết JSON/cộng số bằng tay. */
(function () {
'use strict';
const $=id=>document.getElementById(id);const api='/daoanh/api/admin/ttl_v2/generation';
let schemes=[],current;
async function request(route,body) {
 const headers={'Content-Type':'application/json','X-Session-Token':localStorage.getItem('admin_session')||''};
 const response=await fetch(api+route,body===undefined?{headers}:{method:'POST',headers,body:JSON.stringify(body)});
 let value;try{value=await response.json();}catch(e){throw new Error('Server chưa nạp hệ thống số đời v2.');}
 if(!response.ok||!value.ok)throw new Error(value.error||'Không đọc được hệ đếm.');return value;
}
function field(parent,label,value,change,options) {
 const wrap=document.createElement('div');wrap.className='field';const title=document.createElement('label');title.textContent=label;
 const input=document.createElement(options?'select':'input');input.id='gen_'+crypto.randomUUID();title.htmlFor=input.id;
 if(options)options.forEach(([key,text])=>{const o=document.createElement('option');o.value=key;o.textContent=text;input.append(o);});
 input.value=value??'';input.addEventListener('change',()=>change(input.value));wrap.append(title,input);parent.append(wrap);return input;
}
function removeButton(parent,label,callback) {const b=document.createElement('button');b.type='button';b.className='btn btn-secondary';b.textContent=label;b.addEventListener('click',callback);parent.append(b);}
function drawEditor() {
 const box=$('generation-scheme-editor');box.replaceChildren();
 field(box,'Mã hệ đếm ổn định',current.id,v=>current.id=v).readOnly=!!current._revision;
 field(box,'Tên hiển thị',current.label,v=>current.label=v);
 field(box,'Quy ước: ai đời 0/1, phạm vi, cách cộng',current.convention,v=>current.convention=v);
 field(box,'DILA ID gốc tính · phải là một mốc bên dưới',current.root_id,v=>current.root_id=v);
 field(box,'Loại đường dùng để tính',current.policy,v=>current.policy=v,[['dila_candidate','DILA teacher chung · số dự kiến'],['reviewed_transmission','Chỉ truyền pháp trực tiếp đã duyệt']]);
 current.anchors.forEach((a,index)=>{
  const card=document.createElement('div');card.className='source-card';box.append(card);
  const h=document.createElement('h4');h.textContent='Mốc '+(index+1);card.append(h);
  field(card,'DILA ID',a.person_id,v=>a.person_id=v);field(card,'Tên Hán chính xác / biệt danh trong ID',a.name_zh,v=>a.name_zh=v);
  const number=field(card,'Số đời mốc',a.number,v=>a.number=v===''?null:Number(v));number.type='number';number.min='0';number.max='10000';number.step='1';
  field(card,'Trạng thái mốc',a.status,v=>a.status=v,[['draft','Nháp'],['source_asserted','Sử liệu ghi nhận · chưa duyệt'],['accepted','Đã duyệt · cần ba gốc chứng cứ']]);
  field(card,'Lập luận số đời và quy ước',a.rationale,v=>a.rationale=v);
  field(card,'Người duyệt',a.reviewer,v=>a.reviewer=v);field(card,'Ngày duyệt ISO8601 có timezone',a.reviewed_at,v=>a.reviewed_at=v);
  (a.evidence||[]).forEach((e,n)=>{
   const ev=document.createElement('div');ev.className='source-card';card.append(ev);
   const p=document.createElement('p');p.textContent='Chứng cứ '+(n+1);ev.append(p);
   [['citation','Sử liệu, quyển/trang/dòng, đoạn chứng minh'],['version','Phiên bản / edition / hash'],['independence_key','Gốc chứng cứ · cùng tác phẩm dùng cùng khóa'],['url','URL chính thức']].forEach(([k,label])=>field(ev,label,e[k],v=>e[k]=v));
   removeButton(ev,'Bỏ chứng cứ',()=>{a.evidence.splice(n,1);drawEditor();});
  });
  removeButton(card,'Thêm chứng cứ',()=>{a.evidence=a.evidence||[];a.evidence.push({citation:'',version:'',independence_key:'',url:''});drawEditor();});
  removeButton(card,'Bỏ mốc',()=>{current.anchors.splice(index,1);drawEditor();});
 });
 (current.reviewed_edges||[]).forEach((e,index)=>{
  const card=document.createElement('div');card.className='source-card';box.append(card);
  const h=document.createElement('h4');h.textContent='Cạnh truyền pháp đã duyệt '+(index+1);card.append(h);
  [['id','ID cạnh ổn định'],['parent','DILA ID thầy'],['child','DILA ID trò'],['citation','Sử liệu chứng minh truyền pháp trực tiếp'],['version','Phiên bản nguồn'],['reviewer','Người duyệt'],['reviewed_at','Ngày duyệt ISO8601 có timezone']].forEach(([key,label])=>field(card,label,e[key],v=>e[key]=v));
  removeButton(card,'Bỏ cạnh',()=>{current.reviewed_edges.splice(index,1);drawEditor();});
 });
}
async function reload(selected) {
 const response=await request('/schemes');schemes=response.schemes;
 const select=$('generation-scheme-select');select.replaceChildren();
 schemes.concat([{id:'',label:'＋ Hệ đếm mới'}]).forEach(s=>{const o=document.createElement('option');o.value=s.id;o.textContent=s.label+(s._revision?' · v'+s._revision:'');select.append(o);});
 select.value=selected===undefined?(schemes[0]?.id||''):selected;choose();
}
function choose() {
 const found=schemes.find(s=>s.id===$('generation-scheme-select').value);
 current=found?structuredClone(found):{id:'',label:'',convention:'',root_id:'',policy:'dila_candidate',anchors:[],reviewed_edges:[]};drawEditor();
}
function renderResults(results) {
 const box=$('generation-v2-results');box.replaceChildren();
 const states={candidate:'Dự kiến',derived_reviewable:'Suy dẫn · đủ điều kiện trình duyệt',conflict:'Mâu thuẫn',unreachable:'Chưa nối tới mốc',missing_anchor:'Chưa có mốc',incomplete:'Thiếu dữ liệu',resource_limit:'Vượt giới hạn'};
 results.forEach(r=>{
  const card=document.createElement('details');card.className='assertion-card';box.append(card);
  const title=document.createElement('summary');title.textContent=r.label+' · '+(r.number===null?'chưa chốt':'đời '+r.number)+' · '+(states[r.status]||r.status);card.append(title);
  const p=document.createElement('p');p.textContent=r.convention+' '+r.message;card.append(p);
  if(r.candidates?.length>1){const c=document.createElement('p');c.textContent='Các số xung đột: '+r.candidates.join(', ');card.append(c);}
  Object.entries(r.provenance?.witnesses||{}).forEach(([n,w])=>{
   const line=document.createElement('p');line.textContent='Đường cho đời '+n+': '+w.person_ids.map(id=>id+' '+(r.provenance.identities[id]?.names[0]||'')).join(' → ');card.append(line);
  });
  (r.issues||[]).forEach(i=>{const line=document.createElement('p');line.textContent=i.type+' · '+(i.person_id||(i.person_ids||[]).join(', '))+(i.numbers?' · '+i.numbers.join(', '):'');card.append(line);});
 });
 if(!results.length)box.textContent='Nạp hồ sơ có DILA ID rồi bấm Tính số đời từ DILA.';
}
window.addEventListener('generation-v2-results',e=>renderResults(e.detail));
async function init() {
 $('generation-scheme-select').addEventListener('change',choose);
 $('generation-add-anchor').addEventListener('click',()=>{current.anchors.push({person_id:'',name_zh:'',number:1,status:'draft',evidence:[],rationale:''});drawEditor();});
 $('generation-add-edge').addEventListener('click',()=>{current.reviewed_edges=current.reviewed_edges||[];current.reviewed_edges.push({id:'edge_'+crypto.randomUUID(),parent:'',child:'',kind:'dharma_transmission',status:'accepted',citation:'',version:'',reviewer:'',reviewed_at:''});drawEditor();});
 $('generation-save-scheme').addEventListener('click',async()=>{
  try {const saved=await request('/schemes',{scheme:current,expected_revision:current._revision||0});await reload(saved.scheme.id);$('generation-scheme-status').textContent='Đã lưu v'+saved.scheme._revision+'. Tính lại để dùng mốc mới; chưa sửa số đời cũ.';}
  catch(e){$('generation-scheme-status').textContent=e.message;}
 });
 await reload();
}
init().catch(e=>$('generation-scheme-status').textContent=e.message);
}());
