/* T233: cột tham khảo riêng, DOM textContent, không tự duyệt hay sửa name_vi. */
(function(){'use strict';
const $=id=>document.getElementById(id);const api='/daoanh/api/admin/ttl_v2/codex_name';
let latestRun='',page=1,timer,busy=false,refreshTimer;
async function request(route,body){
 const headers={'Content-Type':'application/json','X-Session-Token':localStorage.getItem('admin_session')||''};
 const r=await fetch(api+route,body===undefined?{headers}:{method:'POST',headers,body:JSON.stringify(body)});
 let d;try{d=await r.json();}catch(e){throw new Error('Server chưa nạp cột Codex.');}
 if(!r.ok||!d.ok)throw new Error(d.error||'API Codex lỗi.');return d;
}
function state(value){return({draft:'Gợi ý · chưa duyệt',needs_review:'Cần kiểm',stale:'Nguồn đã đổi'})[value]||'Chưa chạy';}
async function hydrate(){
 if(busy)return;const rows=Array.from(document.querySelectorAll('#etl-match-flag-table tbody tr[data-dila-id],#etl-flag-queue-body tr[data-dila-id]')).filter(tr=>tr.querySelector('.codex-name-cell')&&!tr.dataset.codexLoaded);
 if(!rows.length)return;busy=true;
 try{const ids=[...new Set(rows.map(tr=>tr.dataset.dilaId))];const by=new Map();
  for(let offset=0;offset<ids.length;offset+=200){const d=await request('/lookup',{ids:ids.slice(offset,offset+200)});d.items.forEach(x=>by.set(x.dila_id,x));}
  rows.forEach(tr=>{const c=tr.querySelector('.codex-name-cell');const r=by.get(tr.dataset.dilaId);c.textContent=r&&!r.stale?(r.name_vi||'—'):'—';c.title=r?state(r.stale?'stale':r.status)+' · '+r.model+' · '+r.notes:'Chưa có kết quả GPT Sol trong DB';tr.dataset.codexLoaded='1';});
 }catch(e){$('codex-name-status').textContent=e.message;}finally{busy=false;}
}
function cell(row,text){const c=document.createElement('td');c.textContent=text||'—';row.append(c);return c;}
async function loadList(){
 const d=await request('/list?'+new URLSearchParams({page,q:$('codex-search').value.trim()}));const box=$('codex-corpus-body');box.replaceChildren();
 d.items.forEach(item=>{const tr=document.createElement('tr');box.append(tr);const link=document.createElement('a');link.href='/daoanh/admin/person.html?id='+encodeURIComponent(item.dila_id);link.target='_blank';link.textContent=item.dila_id;cell(tr,'').replaceChildren(link);cell(tr,item.name_zh);cell(tr,item.dila_name_vi);const name=cell(tr,item.stale?'':item.codex_name_vi);name.style.color='#67e8f9';name.title=(item.codex_model||'')+' · '+(item.codex_notes||'');cell(tr,state(item.stale?'stale':item.codex_status));});
 const pages=$('codex-corpus-pages');pages.replaceChildren();const text=document.createElement('span');text.textContent=d.total.toLocaleString()+' ID · trang '+d.page+'/'+d.pages;pages.append(text);
 [['‹ Trước',page-1,page>1],['Sau ›',page+1,page<d.pages]].forEach(([label,to,enabled])=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.disabled=!enabled;b.addEventListener('click',()=>{page=to;loadList().catch(showError);});pages.append(b);});
}
function showError(e){$('codex-name-status').textContent=e.message;}
async function status(){
 const d=await request('/status');const job=d.jobs.find(j=>j.transport==='codex_chatgpt_session'&&j.resumable);latestRun=job?.id||'';
 $('codex-name-status').textContent=d.done.toLocaleString()+'/'+d.total.toLocaleString()+' tên Codex đã lưu · '+d.needs_review+' cần kiểm · '+d.model+' · '+(d.subscription?.authenticated?'Codex đăng nhập ChatGPT':'Server chưa đăng nhập Codex bằng ChatGPT')+' · API trả phí đã tắt'+(job?' · lô '+job.status+(job.error_code?' · '+job.error_code:''):'');
 const running=job?.status==='running_session'||d.operations.some(o=>o.status==='running');
 $('codex-run').disabled=!d.subscription?.authenticated||!job||running||job.status==='done';$('codex-pause').disabled=!job||!running;$('codex-prepare').disabled=running;
 if(running){clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>refresh().catch(showError),5000);}
 return d;
}
async function job(action){
 const d=await request('/job',{action,run_id:latestRun});$('codex-name-status').textContent=action==='pause'?'Sẽ dừng sau nhóm hiện tại.':'Đang '+action+' · '+d.operation;await status();
}
async function refresh(){document.querySelectorAll('[data-codex-loaded]').forEach(tr=>delete tr.dataset.codexLoaded);await Promise.all([status(),loadList(),hydrate()]);}
function init(){
 ['prepare','run','pause'].forEach(action=>$('codex-'+action).addEventListener('click',()=>job(action).catch(showError)));
 $('codex-refresh').addEventListener('click',()=>refresh().catch(showError));$('codex-search-button').addEventListener('click',()=>{page=1;loadList().catch(showError);});$('codex-search').addEventListener('keydown',e=>{if(e.key==='Enter'){page=1;loadList().catch(showError);}});
 const observed=$('etl-flag-queue-body');new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(hydrate,100);}).observe(observed,{childList:true});
 // Match report có thêm một cột; sửa colspan theo số header, không dùng số cũ.
 document.querySelectorAll('#etl-match-flag-table,#etl-flag-queue-table').forEach(t=>{const fix=()=>t.querySelectorAll('td[colspan]').forEach(td=>td.colSpan=t.querySelectorAll('thead th').length);new MutationObserver(fix).observe(t.tBodies[0],{childList:true});fix();});
 refresh().catch(showError);
}
init();
}());
