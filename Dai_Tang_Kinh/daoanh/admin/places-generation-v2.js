/* T232: panel phụ, số suy dẫn có quy ước/đường; không thay số đời legacy của cây.
   Nếu trang có #lineage-gen-v2-body → render inline vào left panel (places.html).
   Ngược lại → giữ nguyên corner panel cũ (fallback cho các trang khác). */
(function(){'use strict';
let serial=0,current='';
const inlineBody=()=>document.getElementById('lineage-gen-v2-body');
const inlineWrap=()=>document.getElementById('lineage-gen-v2-inline');
/* Corner panel legacy — ẩn khi dùng inline mode */
const panel=document.createElement('section');panel.id='lineage-generation-v2';panel.style.cssText='position:fixed;right:16px;bottom:18px;width:min(360px,calc(100vw - 32px));max-height:42vh;overflow:auto;padding:14px;background:#020617;color:#e2e8f0;border:1px solid #d97706;border-radius:10px;z-index:70;font-family:Inter,sans-serif;font-size:12px;box-shadow:0 8px 24px #0008';
const cornerTitle=document.createElement('h3');cornerTitle.textContent='Pháp mạch · theo từng hệ truyền thừa';cornerTitle.style.cssText='margin:0 0 8px;font-size:14px;color:#fbbf24';panel.append(cornerTitle);const box=document.createElement('div');panel.append(box);panel.hidden=true;document.body.append(panel);
const states={candidate:'Dự kiến',derived_reviewable:'Suy dẫn · cần trình duyệt',conflict:'Mâu thuẫn',unreachable:'Chưa nối tới mốc',missing_anchor:'Chưa khóa mốc',incomplete:'Thiếu dữ liệu',resource_limit:'Vượt giới hạn'};
function renderInto(container,id,data,wrap){
  container.replaceChildren();
  /* Chỉ hiển thị dòng có số xác định (number !== null) và
     bỏ hệ "Thích Ca 1" (trùng với Ca Diếp 1, +1; Ca Diếp=1 là quy ước chuẩn). */
  var results=data.report.results||[];
  var visible=results.filter(function(r){
    return r.number!==null && !(r.label&&r.label.includes('Thích Ca 1'));
  });
  if(!visible.length){
    if(!results.length){if(wrap)wrap.style.display='none';return;}
    /* BUG-027: đã tính xong nhưng không hệ nào chốt được số đời — giải thích lý do theo status,
       KHÔNG ẩn panel (trước đây wrap.style.display='none' khiến panel biến mất không lý do). */
    var counts={};
    results.forEach(function(r){var st=r.status||'incomplete';counts[st]=(counts[st]||0)+1;});
    var parts=[];
    if(counts.unreachable)parts.push(counts.unreachable+' tông chưa nối tới mốc');
    if(counts.missing_anchor)parts.push(counts.missing_anchor+' tông thiếu mốc');
    if(counts.conflict)parts.push(counts.conflict+' tông mâu thuẫn đường truyền');
    Object.keys(counts).forEach(function(st){
      if(st==='unreachable'||st==='missing_anchor'||st==='conflict')return;
      var label=states[st]||st;
      parts.push(counts[st]+' tông '+label.toLowerCase());
    });
    var msg=document.createElement('div');
    msg.style.cssText='font-size:11px;color:var(--da-muted,#94a3b8);line-height:1.6;padding:4px 0;word-break:break-word;white-space:normal';
    msg.textContent='Chưa xác định số đời: '+(parts.length?parts.join(', ')+'.':'không có hệ truyền thừa nào tính được.');
    container.append(msg);
    return;
  }
  visible.forEach(function(r){
    /* Rút gọn label: bỏ suffix hệ đếm " · Ca Diếp 1" / " · Thích Ca 1", thêm "Truyền Thừa " */
    var cleanLabel='Truyền Thừa '+r.label.replace(/\s*·\s*(Ca Diếp|Thích Ca)\s*\d+\s*$/,'').trim();
    var row=document.createElement('div');row.style.cssText='font-size:13px;font-weight:600;color:var(--da-text);padding:3px 0';
    row.textContent=cleanLabel+' · Đời thứ '+r.number;
    container.append(row);
  });
}
async function load(id){
  const body=inlineBody(),wrap=inlineWrap();
  const useInline=!!(body&&wrap);
  if(!/^A\d{6}$/.test(id||'')){if(useInline)wrap.style.display='none';else panel.hidden=true;current='';return;}
  if(id===current&&(useInline?wrap.style.display!=='none':!panel.hidden))return;
  current=id;
  if(useInline){wrap.style.display='';body.innerHTML='<div style="color:#94a3b8;font-size:10px">Đang tính cho '+id+'…</div>';}
  else{panel.hidden=false;box.textContent='Đang tính cho '+id+'…';}
  const n=++serial;
  try{const response=await fetch('/daoanh/api/admin/ttl_v2/generation/calculate/'+id);const data=await response.json();if(n!==serial)return;if(!response.ok||!data.ok)throw new Error(data.error||'Chưa đọc được mốc số đời.');renderInto(useInline?body:box,id,data,useInline?wrap:null);}
  catch(e){if(n===serial)(useInline?body:box).textContent=e.message;}
}
/* T355 vong 2 (BUG-033): url() TRUOC ĐÂY luôn gọi load(focus) MỖI LẦN được gọi — kể cả khi
   history.pushState/replaceState chỉ ghi lại do đổi "chain" (mở/thu node trong tab Pháp mạch,
   xem places.html _t130SyncUrl ~11202), focus/mode không hề đổi. Vì admin/places-generation-v2.js
   monkey-patch pushState/replaceState (bên dưới) để gọi lại url() sau MỌI lần ghi URL, mỗi click
   mở/thu node sinh ra 1 request load(focus) chạy song song với request load(pid) đúng (gọi trực
   tiếp từ places.html khi click thân node, dòng ~6754) — 2 request này RACE nhau qua biến `serial`
   dùng chung trong load(), kết quả hiển thị cuối cùng là request NÀO VỀ SAU, không phải node vừa
   chọn. Bằng chứng: network log docs/sessions/2026-10-11/T355_round2_network_BEFORE.txt — mỗi lần
   click đều sinh cặp request xen kẽ /generation/calculate/<focus> và /generation/calculate/<pid>.
   Fix: chỉ load(focus) khi focus/mode THỰC SỰ đổi so với lần url() chạy trước (điều hướng thật —
   initial load, popstate, hoặc đổi focus) — bỏ qua khi URL chỉ đổi do sync chain/expand-state. */
  let _lastUrlFocus=null,_lastUrlMode=null;
  function url(){const q=new URLSearchParams(location.search);const _m=q.get('mode'),_f=q.get('focus');if(_m==='lineage'){if(_f===_lastUrlFocus&&_m===_lastUrlMode)return;_lastUrlFocus=_f;_lastUrlMode=_m;load(_f);}else{_lastUrlFocus=null;_lastUrlMode=null;const wrap=inlineWrap();if(wrap)wrap.style.display='none';panel.hidden=true;current='';}}
window.addEventListener('popstate',url);
/* T354: hàm network.on('click') của cây Pháp mạch (places.html, mode=lineage)
   tự cập nhật sidebar title/breadcrumb/quicklist bằng DOM trực tiếp, KHÔNG
   gọi qua selectPerson/openPersonLineage/_gmpShowNodeDetail/_nexusShowDetail
   — nên panel "Đời thứ N" không bao giờ tính lại khi click node trong cây.
   Expose load() để places.html gọi thẳng, không cần thêm 1 lớp monkey-patch. */
window._ptdaLoadGenerationV2=load;
['selectPerson','openPersonLineage'].forEach(function(name){var original=window[name];if(typeof original==='function')window[name]=function(id){for(var _len=arguments.length,args=new Array(_len>1?_len-1:0),_key=1;_key<_len;_key++)args[_key-1]=arguments[_key];load(id);return original.apply(this,[id].concat(args));};});
['_gmpShowNodeDetail','_nexusShowDetail'].forEach(function(name){var original=window[name];if(typeof original==='function')window[name]=function(node){for(var _len=arguments.length,args=new Array(_len>1?_len-1:0),_key=1;_key<_len;_key++)args[_key-1]=arguments[_key];load(node&&(node.person_id||node.dila_id||node.id));return original.apply(this,[node].concat(args));};});
var replace=history.replaceState.bind(history);history.replaceState=function(){var result=replace.apply(history,arguments);url();return result;};var push=history.pushState.bind(history);history.pushState=function(){var result=push.apply(history,arguments);url();return result;};
url();
}());
