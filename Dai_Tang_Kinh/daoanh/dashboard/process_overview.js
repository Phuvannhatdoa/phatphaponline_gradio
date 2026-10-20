/* T390: derived document snapshot only; no status override or writable endpoint. */
(function () {
  'use strict';
  const root = document.getElementById('executiveOverview');
  if (!root) return;
  const colors = {done:'#34d399',in_progress:'#fbbf24',pending:'#64748b',blocked:'#f87171',other:'#a78bfa'};
  const labels = {done:'Hoàn thành',in_progress:'Đang làm',pending:'Chờ thực hiện',blocked:'Bị chặn',other:'Trạng thái khác'};
  let generation = 0;
  const text = value => typeof value === 'string' ? value : (typeof value === 'number' ? String(value) : '');
  const short = (value, length=180) => { const s=text(value).trim(); return s.length>length ? s.slice(0,length)+'…' : s; };
  const metadata = value => { const s=short(value); return /^(?:[|>][+-]?)$/.test(s) ? '' : s; };
  const el = (tag, value, className) => { const node=document.createElement(tag); if(value!==undefined) node.textContent=value; if(className) node.className=className; return node; };
  const clear = id => { const node=document.getElementById(id); node.replaceChildren(); return node; };
  const taskLink = task => /^[A-Za-z0-9][A-Za-z0-9_.-]*\.md$/.test(text(task.file)) ? '../tasks/'+encodeURIComponent(task.file) : null;
  function dependencies(value) {
    if (Array.isArray(value)) return {ids:value.filter(v=>typeof v==='string').map(v=>v.trim()).filter(Boolean), malformed:value.some(v=>typeof v!=='string')};
    const s=text(value).trim();
    if (!s || s==='[]') return {ids:[],malformed:false};
    if (!s.startsWith('[') || !s.endsWith(']')) return {ids:[],malformed:true};
    const items=s.slice(1,-1).split(',').map(v=>v.trim().replace(/^['"]|['"]$/g,'')).filter(Boolean);
    return {ids:[...new Set(items)],malformed:items.some(v=>! /^[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(v))};
  }
  const priority = task => ({P0:0,critical:0,P1:1,high:1,P2:2,medium:2,P3:3,low:3}[text(task.priority)] ?? 4);
  function model(data) {
    if (!data || !Array.isArray(data.tasks) || data.tasks.some(t=>!t || typeof t!=='object' || Array.isArray(t))) throw Error('Snapshot thiếu danh sách task hợp lệ');
    const tasks=data.tasks;
    const counts={done:0,in_progress:0,pending:0,blocked:0,other:0};
    const index=new Map();
    const aliases=new Map();
    tasks.forEach(t=>{
      counts[Object.hasOwn(counts,t.status) ? t.status : 'other']++;
      const id=text(t.id); if(!index.has(id)) index.set(id,[]); index.get(id).push(t);
      const stem=text(t.file).replace(/\.md$/,''); if(stem){if(!aliases.has(stem)) aliases.set(stem,[]);aliases.get(stem).push(t);}
    });
    const resolve=id=>{const found=index.get(id)||aliases.get(id)||[];return found.length===1?found[0]:null;};
    const deps=new Map(tasks.map(t=>[t,dependencies(t.depends_on)]));
    const active=tasks.filter(t=>t.status!=='done');
    const waiting=active.filter(t=>deps.get(t).malformed || deps.get(t).ids.some(id=>!resolve(id)||resolve(id).status!=='done'));
    const duplicateGroups=[...index.entries()].filter(([id,rows])=>id && rows.length>1);
    // SCCs show real closed dependency paths; missing/ambiguous references never become edges.
    let nextIndex=0; const stack=[],onStack=new Set(),order=new Map(),low=new Map(),cycles=[];
    function visit(task) {
      order.set(task,nextIndex);low.set(task,nextIndex++);stack.push(task);onStack.add(task);
      for(const id of deps.get(task).ids){const target=resolve(id);if(!target)continue;if(!order.has(target)){visit(target);low.set(task,Math.min(low.get(task),low.get(target)));}else if(onStack.has(target))low.set(task,Math.min(low.get(task),order.get(target)));}
      if(low.get(task)===order.get(task)){const group=[];let member;do{member=stack.pop();onStack.delete(member);group.push(member);}while(member!==task);if(group.length>1 || deps.get(task).ids.some(id=>resolve(id)===task)) cycles.push(group);}
    }
    tasks.forEach(t=>{if(!order.has(t))visit(t);});
    return {tasks,counts,active,waiting,duplicateGroups,cycles,deps,resolve};
  }
  function kpis(m) {
    const box=clear('overviewKpis');
    const rows=[['total','Hồ sơ task',m.tasks.length,'Số record trong snapshot'],['done','Hoàn thành',m.counts.done,'Status tài liệu: done'],['in_progress','Đang thực hiện',m.counts.in_progress,'Status tài liệu: in_progress'],['blocked','Bị chặn',m.counts.blocked,'Status tài liệu: blocked'],['pending','Chờ thực hiện',m.counts.pending,'Status tài liệu: pending']];
    for(const [tone,label,count,caption] of rows){const card=el('dl',undefined,'dash-kpi');card.dataset.tone=tone;card.append(el('dt',label),el('dd',String(count)),el('p',caption));box.append(card);}
  }
  function statusChart(m) {
    const holder=clear('overviewDonut'); const legend=clear('overviewStatusLegend');
    const ns='http://www.w3.org/2000/svg'; const svg=document.createElementNS(ns,'svg');
    svg.setAttribute('viewBox','0 0 180 180');svg.setAttribute('role','img');svg.setAttribute('aria-labelledby','overviewChartTitle overviewChartDesc');
    const title=document.createElementNS(ns,'title');title.id='overviewChartTitle';title.textContent='Phân bố trạng thái task';
    const desc=document.createElementNS(ns,'desc');desc.id='overviewChartDesc';desc.textContent='Tổng '+m.tasks.length+' hồ sơ. '+Object.keys(m.counts).map(k=>labels[k]+': '+m.counts[k]).join('; ')+'.';svg.append(title,desc);
    const circle=(color)=>{const c=document.createElementNS(ns,'circle');c.setAttribute('cx','90');c.setAttribute('cy','90');c.setAttribute('r','68');c.setAttribute('fill','none');c.setAttribute('stroke',color);c.setAttribute('stroke-width','16');return c;};
    svg.append(circle('#1e293b'));const circumference=2*Math.PI*68;let offset=0;
    for(const key of Object.keys(m.counts)) {
      const count=m.counts[key]; const fraction=m.tasks.length?count/m.tasks.length:0;
      if(count){const c=circle(colors[key]);c.setAttribute('stroke-dasharray',(fraction*circumference)+' '+circumference);c.setAttribute('stroke-dashoffset',String(-offset));c.setAttribute('transform','rotate(-90 90 90)');c.dataset.status=key;c.dataset.count=String(count);svg.append(c);offset+=fraction*circumference;}
      if(key!=='other'||count){const row=el('div');row.dataset.status=key;const dt=el('dt');const dot=el('span',undefined,'dash-dot');dot.style.backgroundColor=colors[key];dot.setAttribute('aria-hidden','true');dt.append(dot,document.createTextNode(labels[key]));row.append(dt,el('dd',String(count)+' · '+(fraction*100).toFixed(1)+'%'));legend.append(row);}
    }
    const center=document.createElementNS(ns,'text');center.setAttribute('x','90');center.setAttribute('y','90');center.setAttribute('text-anchor','middle');center.setAttribute('fill','#f8fafc');center.setAttribute('font-size','30');center.setAttribute('font-weight','800');center.textContent=String(m.tasks.length);svg.append(center);
    const caption=document.createElementNS(ns,'text');caption.setAttribute('x','90');caption.setAttribute('y','112');caption.setAttribute('text-anchor','middle');caption.setAttribute('fill','#94a3b8');caption.setAttribute('font-size','11');caption.textContent='HỒ SƠ TASK';svg.append(caption);holder.append(svg);
  }
  function risks(m) {
    const box=clear('overviewRiskBars');
    const rows=[['blocked','Task ghi blocked',m.counts.blocked],['waiting','Task chưa done, chờ phụ thuộc',m.waiting.length],['cycles','Nhóm chu trình phụ thuộc',m.cycles.length],['duplicates','Nhóm ID trùng trong JSON',m.duplicateGroups.length]];
    const max=Math.max(1,...rows.map(r=>r[2]));
    rows.forEach(([key,label,count])=>{const row=el('div',undefined,'dash-risk-row');row.dataset.risk=key;row.dataset.count=String(count);const name=el('div');name.append(el('span',label),el('strong',String(count)));const bar=el('div',undefined,'dash-bar');bar.setAttribute('aria-hidden','true');const fill=el('span');fill.style.width=(count/max*100)+'%';bar.append(fill);row.append(name,bar);box.append(row);});
    const cycles=m.cycles.slice(0,4).map(group=>group.map(t=>text(t.id)).sort().join(' ↔ '));
    document.getElementById('overviewDependencies').textContent=cycles.length?'Thành viên chu trình (không phải thứ tự đường đi): '+cycles.join('; ')+'. Cần kiểm task gốc trước khi đổi phụ thuộc.':'Không thấy chu trình trong các tham chiếu được phân giải duy nhất. Thiếu/trùng ID không được suy thành cạnh.';
  }
  function actions(m) {
    const box=clear('overviewActions');const sort=(a,b)=>priority(a)-priority(b)||text(a.id).localeCompare(text(b.id),'vi',{numeric:true});
    const columns=[['Ưu tiên cao',m.active.filter(t=>priority(t)<=1).sort(sort)],['Cần gỡ blocker',m.tasks.filter(t=>t.status==='blocked').sort(sort)],['Đang thực hiện',m.tasks.filter(t=>t.status==='in_progress').sort(sort)]];
    for(const [label,list] of columns){const column=el('section',undefined,'dash-action-column');const heading=el('h4',label);heading.append(el('span',Math.min(5,list.length)+' / '+list.length+' hồ sơ'));column.append(heading);const ol=el('ol');
      for(const task of list.slice(0,5)){const li=el('li');const href=taskLink(task);const title=el(href?'a':'span',undefined,'dash-action-title');if(href)title.setAttribute('href',href);title.append(el('strong',short(task.id,45)),document.createTextNode(short(task.title,105)));li.append(title);
        const dep=m.deps.get(task);const unresolved=dep.ids.filter(id=>!m.resolve(id)||m.resolve(id).status!=='done');const meta=[short(task.priority,18)||'Chưa ghi ưu tiên',labels[task.status]||'Status khác','Agent: '+(short(task.owner,70)||'chưa ghi owner')];li.append(el('p',meta.join(' · '),'dash-action-meta'));
        if(dep.malformed || unresolved.length)li.append(el('p',dep.malformed?'Phụ thuộc: chưa đọc được định dạng; kiểm task gốc.':'Chờ: '+short(unresolved.join(', '),140),'dash-action-meta'));
        li.append(el('p','Tiếp: '+(metadata(task.undone_action)||metadata(task.done_when)||'Mở task gốc để kiểm scope, nghiệm thu và bằng chứng.'),'dash-action-next'));
        const done=Number(task.criteria_done),total=Number(task.criteria_total);if(Number.isInteger(done)&&Number.isInteger(total)&&done>=0&&total>0&&done<=total)li.append(el('p','Checklist: '+done+'/'+total+' · bằng chứng tài liệu, chưa suy QA PASS.','dash-action-meta'));ol.append(li);}
      column.append(list.length?ol:el('p','Không có hồ sơ trong nhóm này.','dash-empty'));box.append(column);}
  }
  function render(data,source) {
    const m=model(data);kpis(m);statusChart(m);risks(m);actions(m);
    const generated=short(data.generated_at,70)||'không có mốc sinh';
    document.getElementById('overviewFreshness').textContent='Sinh snapshot: '+generated+' · Nguồn: '+source+(text(data.generated_at)&& !/(Z|[+-]\d{2}:?\d{2})$/.test(data.generated_at)?' · JSON không ghi múi giờ.':'');
    const notice=document.getElementById('overviewNotice');notice.classList.remove('is-error');notice.textContent=m.tasks.length+' hồ sơ · '+m.active.length+' chưa done · '+m.waiting.length+' chờ phụ thuộc. Số liệu snapshot tài liệu, không phải kiểm chứng dữ liệu production.'+(m.counts.other?' Có '+m.counts.other+' hồ sơ status khác.':'');
    root.dataset.loaded='true'; root.dataset.total=String(m.tasks.length);
  }
  function fail(message){root.dataset.loaded='false';root.removeAttribute('data-total');['overviewKpis','overviewDonut','overviewStatusLegend','overviewRiskBars','overviewActions'].forEach(clear);document.getElementById('overviewDependencies').textContent='';document.getElementById('overviewFreshness').textContent='Không có snapshot hợp lệ để tính số liệu.';const notice=document.getElementById('overviewNotice');notice.classList.add('is-error');notice.textContent='Không tải được snapshot: '+message+'. Không hiển thị số 0 thay dữ liệu thiếu.';}
  async function load() {
    const mine=++generation;const button=document.getElementById('overviewReload');button.disabled=true;const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);
    try{const response=await fetch('../data/progress_data.json',{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error('HTTP '+response.status);const data=await response.json();if(mine===generation)render(data,'progress_data.json local');}
    catch(e){if(mine===generation)fail(e.name==='AbortError'?'hết thời gian':short(e.message,100));}
    finally{clearTimeout(timer);if(mine===generation)button.disabled=false;}
  }
  document.getElementById('overviewReload').addEventListener('click',load);
  window.addEventListener('ptda:progress-snapshot',event=>{++generation;document.getElementById('overviewReload').disabled=false;try{render(event.detail.data,short(event.detail.source,60)||'progress snapshot');}catch(e){fail(short(e.message,100));}});
  load();
})();
