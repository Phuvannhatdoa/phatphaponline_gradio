(function () {
  'use strict';
  const local = location.protocol === 'file:' ||
    (['http:','https:'].includes(location.protocol) && ['localhost','127.0.0.1','[::1]'].includes(location.hostname));
  if (!local) {
    document.getElementById('main').hidden=true;
    document.getElementById('guardMessage').textContent='Chỉ mở tại máy. Không render gói có quyền chưa giải quyết trên origin công khai.';
    return;
  }
  const bundle=globalThis.PHASE4_DATA, model=globalThis.Phase4Model;
  if (!bundle || !model) {
    document.getElementById('main').hidden=true;
    document.getElementById('guardMessage').textContent='Thiếu dữ liệu cục bộ; giữ nguyên bốn file JS/CSS cạnh preview.html.';
    return;
  }
  function freeze(value) {if(value && typeof value==='object' && !Object.isFrozen(value)){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
  freeze(bundle);
  const data=bundle.data, fixtures=bundle.fixtures;
  if (!data.input_integrity.upstream_chain_verified) {
    document.getElementById('guardMessage').className='warning';
    document.getElementById('guardMessage').textContent='Cảnh báo provenance: hash đầu vào hiện tại khác hash được ghi trong artifact trước. Phase4 chỉ pin byte hiện tại, không xác nhận chuỗi manifest cũ. Xem phase4-manifest.json; không sửa nguồn hoặc phê duyệt dữ liệu.';
  }
  const $=id=>document.getElementById(id);
  const node=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(className)n.className=className;return n;};
  const json=value=>JSON.stringify(value,null,2);
  const missing=value=>value===null||value===undefined||value===''?'Chưa cung cấp':String(value);
  const clear=id=>{const n=$(id);n.replaceChildren();return n;};
  const personMap=new Map(data.source_person.map(p=>[p.source_node_key,p]));
  const mappingMap=new Map(data.mapping_candidates.map(p=>[p.source_node_key,p]));
  const evidenceMap=new Map(data.source_evidence.map(e=>[e.id,e]));
  function mode(name) {
    for(const m of ['source','compare','evidence']) $(m+'Panel').hidden=m!==name;
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===name)));
    $('modeStatus').textContent={source:'Chỉ quan sát nguồn; không xác nhận quan hệ lịch sử.',compare:'Đối chiếu trình bày; không gộp hoặc phê duyệt dữ liệu nguồn.',evidence:'Locator và thuộc tính được giữ nguyên; quyền chưa clearance.'}[name];
  }
  function showEvidence(id) {
    mode('evidence');$('evidenceSelect').value=id;
    $('evidenceDetail').textContent=json(evidenceMap.get(id)||{status:'Chưa có trích đoạn',evidence_id:id});
    $('evidenceDetail').focus();
  }
  function evidenceButton(id) {const b=node('button',id);b.type='button';b.addEventListener('click',()=>showEvidence(id));return b;}
  function graph(container, persons, observations) {
    container.replaceChildren();
    const view=model.compare(persons,observations), ns='http://www.w3.org/2000/svg';
    const height=Math.max(220,Math.ceil(view.nodes.length/5)*135);
    const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 900 '+height);svg.setAttribute('role','img');
    const title=document.createElementNS(ns,'title');title.textContent='Quan sát endpoint: đường không mũi tên là vô hướng hoặc chưa rõ; đây không phải cây thầy trò.';svg.append(title);
    const coords=new Map(view.nodes.map((n,i)=>[n.key,{x:90+(i%5)*178,y:55+Math.floor(i/5)*135}]));
    for(const edge of view.edges) {
      const a=coords.get(edge.endpoints[0]),b=coords.get(edge.endpoints[1]);
      const line=document.createElementNS(ns,'line');line.setAttribute('x1',a.x);line.setAttribute('y1',a.y);line.setAttribute('x2',b.x);line.setAttribute('y2',b.y);
      line.dataset.direction=edge.direction;svg.append(line);
      if(edge.direction==='undefined') line.setAttribute('stroke-dasharray','5 4');
      if(edge.direction==='directed') {
        const dx=b.x-a.x,dy=b.y-a.y,length=Math.hypot(dx,dy)||1,ux=dx/length,uy=dy/length;
        const tip={x:b.x-20*ux,y:b.y-20*uy},base={x:tip.x-11*ux,y:tip.y-11*uy};
        const arrow=document.createElementNS(ns,'polygon');
        arrow.setAttribute('points',tip.x+','+tip.y+' '+(base.x+5*uy)+','+(base.y-5*ux)+' '+(base.x-5*uy)+','+(base.y+5*ux));
        arrow.setAttribute('fill','#fbbf24');arrow.dataset.directedArrow='true';svg.append(arrow);
      }
    }
    view.nodes.forEach(n=>{
      const c=coords.get(n.key),p=persons.find(p=>model.identityKey(p)===n.key);
      const circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',c.x);circle.setAttribute('cy',c.y);circle.setAttribute('r','17');svg.append(circle);
      const label=document.createElementNS(ns,'text');label.setAttribute('x',c.x);label.setAttribute('y',c.y+38);label.setAttribute('text-anchor','middle');label.textContent=p.source_label;svg.append(label);
      const id=document.createElementNS(ns,'text');id.setAttribute('x',c.x);id.setAttribute('y',c.y+57);id.setAttribute('text-anchor','middle');id.textContent=p.source_external_id;svg.append(id);
    });
    container.append(svg);return view;
  }
  function source() {
    const query=$('search').value.trim().toLowerCase(),format=$('format').value;
    const visible=data.source_person.filter(p=>!query||(p.source_label+' '+p.source_external_id).toLowerCase().includes(query));
    const keys=new Set(visible.map(p=>p.source_node_key));
    const observations=data.source_observation.filter(o=>keys.has(o.source_node_key)&&keys.has(o.target_node_key)&&(format==='all'||o.raw_source_record.format===format));
    graph($('graph'),visible,observations);
    const tbody=clear('persons');
    visible.forEach(p=>{
      const m=mappingMap.get(p.source_node_key),tr=node('tr');tr.dataset.sourceKey=p.source_node_key;
      [p.source_node_key+' / '+p.source_external_id,p.source_label,missing(m.vietnamese_label),
        missing(m.proposed_ptda_person_id),m.identity_status+' / '+m.review_status,
        'CSV: '+missing(p.generation.csv_raw)+' · workbook: '+missing(p.generation.workbook_raw)+' · '+p.generation.system_id].forEach(v=>tr.append(node('td',v)));
      tbody.append(tr);
    });
    $('observationSummary').textContent=observations.length+' bản quan sát được hiển thị; mỗi UUID/locator còn riêng. Một cụm tác phẩm; không tính số biểu diễn thành số nguồn độc lập.';
    const body=clear('observations');
    observations.forEach(o=>{
      const tr=node('tr');tr.dataset.observationId=o.observation_id;
      tr.append(node('td',o.observation_id+' · '+o.raw_source_record.format),
        node('td',o.source_node_key+' — '+o.target_node_key),
        node('td',o.relation_type+' / '+o.direction),
        node('td',o.source_reference_raw+' · '+o.warnings.join('; ')));
      const proof=node('td');o.evidence_refs.forEach(id=>proof.append(evidenceButton(id)));tr.append(proof);body.append(tr);
    });
  }
  function compare() {
    const chosen=fixtures.cases.find(f=>f.id===$('scenario').value);
    const ps=chosen?chosen.source_person:data.source_person,obs=chosen?chosen.observations:data.source_observation;
    const result=graph($('comparisonGraph'),ps,obs);
    $('simulationWarning').classList.toggle('simulated',Boolean(chosen));
    $('simulationWarning').textContent=chosen?'SIMULATED / GIẢ LẬP — người và tác phẩm hư cấu, không phải dữ liệu DILA/Marcus hoặc xác nhận lịch sử.':'Dữ liệu nguồn thực P3: chỉ một cụm Tổ Đường Tập. Không có bộ quan hệ DILA/Marcus độc lập để đối chiếu thực.';
    $('comparisonSummary').textContent=result.nodes.length+' định danh trình bày · '+obs.length+' quan sát · '+result.edges.length+' nhóm ngữ nghĩa. Gom hiển thị không xóa observation.';
    $('comparisonSummary').dataset.nodes=String(result.nodes.length);$('comparisonSummary').dataset.edges=String(result.edges.length);
    const rows=clear('comparisonRows');
    result.edges.forEach(e=>{
      const card=node('article',undefined,'card');card.dataset.direction=e.direction;
      card.append(node('h4',e.endpoints.join(e.direction==='directed'?' → ':' — ')),node('p',e.relation_type+' / '+e.direction));
      card.append(node('p',e.observation_ids.length+' quan sát · '+e.work_ids.length+' nhóm tác phẩm nguồn · '+e.representation_ids.length+' biểu diễn'));
      card.append(node('p','Work: '+e.work_ids.join(', ')),node('p','Quan sát: '+e.observation_ids.join(', ')));
      e.evidence_refs.forEach(id=>{if(evidenceMap.has(id))card.append(evidenceButton(id));else card.append(node('span',id,'badge'));});rows.append(card);
    });
    const annotations=clear('generationAnnotations');
    result.nodes.forEach(n=>{
      const card=node('article',undefined,'card');card.append(node('h4',n.key),node('pre',json(n.generations)),node('p','Giữ nhãn hệ đếm; không cộng, không quy đổi, không nhân đôi người do khác số đời.'));annotations.append(card);
    });
  }
  function details() {
    const witnesses=clear('witnesses');
    data.source_observation.filter(o=>[o.source_node_key,o.target_node_key].sort().join('|')==='ztj:A000587|ztj:A004166').forEach(o=>{
      const card=node('article',undefined,'card');card.dataset.witness=o.observation_id;card.append(node('h4',o.observation_id),node('p',o.source_reference_raw),node('pre',json(o.source_location)),node('p',o.warnings.join('; ')));
      o.evidence_refs.forEach(id=>card.append(evidenceButton(id)));witnesses.append(card);
    });
    witnesses.append(node('p','CSV giữ UUID khớp witness 0300b07 nhưng locator trỏ 0412a05. Không chọn bản thắng và không tự sửa nguồn.','warning'));
    const unknown=clear('unknownGenerations');data.generation_unknowns.forEach(g=>{const card=node('article',undefined,'card');card.dataset.unknownGeneration=g.source_node_key;card.append(node('h4',g.source_node_key),node('pre',json(g.generation)));unknown.append(card);});
    $('uncertaintyTitle').textContent='41 linkGrp cert=low; '+data.uncertainty.all_uncertainty_records.length+' bản ghi bất định được giữ nguyên (có thể ngoài mẫu 15 người)';
    const uncertainty=clear('uncertainties');data.uncertainty.all_uncertainty_records.forEach((q,i)=>{const card=node('article',undefined,'card');card.dataset.cert=q.record.attributes.cert||'not-encoded';card.dataset.tag=q.record.tag;card.append(node('h4',String(i+1)+'. '+q.record.tag+' · '+q.file),node('pre',json(q.record)));uncertainty.append(card);});
    const rights=clear('rightsRows');rights.append(node('p','Bốn TEI: CC BY-NC-SA 4.0 trong file và CC BY 4.0 cấp record/thư mục. Chưa clearance; không cấp license cho PTDA/DILA/CBETA.','warning'));
    data.rights.matrix.forEach(r=>{const card=node('article',undefined,'card');card.append(node('h4',r.file),node('pre',json(r)));rights.append(card);});
    const select=clear('evidenceSelect');data.source_evidence.forEach(e=>{const op=node('option',e.id+' · '+e.kind+' · '+e.locator);op.value=e.id;select.append(op);});
    $('evidenceDetail').textContent=json(data.source_evidence[0]||{status:'Chưa cung cấp'});
  }
  const summary=clear('summary');
  for(const [count,label] of [[data.source_person.length,'Nhân vật được chọn'],[data.source_observation.length,'Quan sát nguồn riêng'],[data.uncertainty.linkgrp_low_records.length,'linkGrp cert=low'],[data.rights.conflict_count,'TEI chưa giải quyết quyền']]) {
    const dl=node('dl');dl.append(node('dt',label),node('dd',count));summary.append(dl);
  }
  fixtures.cases.forEach(f=>{const op=node('option','SIMULATED · '+f.title);op.value=f.id;$('scenario').append(op);});
  $('modes').addEventListener('click',e=>{const button=e.target.closest('button[data-mode]');if(button)mode(button.dataset.mode);});
  $('format').addEventListener('change',source);$('search').addEventListener('input',source);
  $('scenario').addEventListener('change',compare);
  $('evidenceSelect').addEventListener('change',()=>{$('evidenceDetail').textContent=json(evidenceMap.get($('evidenceSelect').value));});
  source();compare();details();mode('source');
  document.body.dataset.ready='true';
})();
