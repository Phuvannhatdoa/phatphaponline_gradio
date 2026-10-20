/* Chuyển hồ sơ đang xem thành bản nháp TTL; không gọi API ghi dữ liệu. */
(function () {
  'use strict';
  const PREFIX = 'daoanh.personTTL.v1.';
  const field = id => document.getElementById(id);
  const value = id => field(id)?.value.trim() || '';
  const literal = text => JSON.stringify(String(text)); // Escape dấu nháy, xuống dòng và backslash đúng RDF.
  const authority = id => 'https://authority.dila.edu.tw/person/search.php?aid=' + id;
  let identities = {};
  const relationSlug = id => 'dila_' + id.toLowerCase();
  const pairs = raw => raw.split(',').map(x => x.trim()).filter(Boolean).map(x => {
    const p = x.split('|').map(x => x.trim());
    return {name:p[0], slug:p[1] || slugify(p[0])};
  });

  window.createPersonTTLDraft = function () {
    if (!_personData || !_dilaFullData) { alert('Hồ sơ đang tải, vui lòng thử lại.'); return; }
    try {
      const vi = {...(_dilaViData || {})};
      // Lấy cả nội dung admin đang sửa nhưng chưa lưu trên trang hồ sơ.
      document.querySelectorAll('[id^="dila-ta-"]').forEach(el => {
        const key = el.id.slice('dila-ta-'.length);
        if (!field('dila-e-' + key)?.hidden) vi[key] = key === 'alt_names_vi' ? el.value.split('\n').filter(Boolean) : el.value;
      });
      const p = {..._personData, name_vi: !field('hdr-name-edit').hidden ? field('hdr-name-input').value.trim() : (_personData.name_vi ? field('hdr-name').textContent.trim() : '')};
      const key = PREFIX + crypto.randomUUID();
      sessionStorage.setItem(key, JSON.stringify({version:1, person_id:personId, created_at:Date.now(), person:p, dila:_dilaFullData, vi, bio_zh:_personBioZh}));
      location.href = '/daoanh/admin/monk_ttl_add.html?draft=' + encodeURIComponent(key) + '&person_id=' + encodeURIComponent(personId);
    } catch (e) { alert('Không chuyển được bản nháp: ' + e.message); }
  };

  if (!field('source_dila_id')) return;
  // Sửa slugify cũ thiếu join(): chuẩn hóa dấu Việt trước khi sinh URI/tên file.
  window.slugify = text => String(text).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
  const genLabel = field('gen_order').closest('.field').querySelector('label');
  const genHint = field('gen_order').closest('.field').querySelector('.hint');
  const originalGenLabel = genLabel.innerHTML, originalGenHint = genHint.textContent;

  // Sinh Turtle an toàn từ tất cả ô nhập; giữ URI DILA riêng cho từng endpoint.
  window.buildTTL = function () {
    const slug = value('slug'), name = value('name_vi');
    if (!slug || !name) return '# ← Cần nhập Tên tiếng Việt và Slug';
    const out = [
      '@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .',
      '@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .',
      '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .',
      '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
      '@prefix owl: <http://www.w3.org/2002/07/owl#> .', '',
      '<ex:monk/' + slug + '> a <bkg:Monk> ;',
      '    rdfs:label ' + literal(name) + '@vi ;'
    ];
    const add = (pred, text, lang) => { if (text) out.push('    ' + pred + ' ' + literal(text) + (lang ? '@'+lang : '') + ' ;'); };
    add('rdfs:label', value('name_zh'), 'zh');
    out.push('    crm:P1_is_identified_by <ex:monk/' + slug + '> ;');
    const id = value('source_dila_id');
    if (/^A\d{6}$/.test(id)) out.push('    owl:sameAs <' + authority(id) + '> ;');
    add('bkg:biographicalNote', value('bio_vi') || name, 'vi');
    add('bkg:biographicalNote', value('source_bio_zh'), 'zh');
    add('bkg:sourceNote', value('source_notes'), '');
    add('bkg:dharmaLineageName', value('lineage_custom') || value('lineage_name'), 'vi');
    for (const [input,pred] of [['birth_year','birthYear'],['death_year','deathYear']]) {
      const year = value(input);
      if (/^-?\d+$/.test(year)) out.push('    bkg:' + pred + ' ' + literal(year) + '^^xsd:integer ;');
    }
    if (value('birth_year') || value('death_year')) {
      out.push('    bkg:birthEvent <ex:monk/' + slug + '_birthEvent> ;');
      out.push('    bkg:deathEvent <ex:monk/' + slug + '_deathEvent> ;');
    }
    const gender = value('source_gender');
    if (gender) out.push('    bkg:gender <bkg:' + gender + '> ;');
    if (/^\d+$/.test(value('gen_order'))) out.push('    bkg:generationOrder ' + value('gen_order') + ' ;');
    const teachers = [{name:value('teacher_vi'),slug:value('teacher_slug')}, ...pairs(value('other_teachers'))].filter(x=>x.slug);
    const students = pairs(value('disciples'));
    const unique = list => [...new Map(list.map(x=>[x.slug,x])).values()];
    for (const [pred,list] of [['hasTeacher',teachers],['hasDisciple',students]]) {
      if (list.length) out.push('    bkg:' + pred + ' ' + unique(list).map(x=>'<ex:monk/'+x.slug+'>').join(', ') + ' ;');
    }
    out.push('    bkg:isLineageFounder ' + field('is_founder').checked + ' .', '');
    unique([...teachers,...students]).forEach(x => {
      if (x.name) out.push('<ex:monk/'+x.slug+'> rdfs:label '+literal(x.name)+'@vi .');
      if (identities[x.slug]) out.push('<ex:monk/'+x.slug+'> owl:sameAs <'+authority(identities[x.slug])+'> .');
    });
    return out.join('\n');
  };
  // Preview phải escape nội dung gốc trước khi đưa vào HTML.
  window.livePreview = function () {
    const safe = buildTTL().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    field('ttl-preview').innerHTML = safe.replace(/(^@prefix.*$|&lt;[^\n]*?&gt;|"(?:\\.|[^"\\])*"@\w+|^#.*$)/gm, token => '<span class="'+(token.startsWith('@')?'kw':token.startsWith('&lt;')?'uri':token.startsWith('#')?'cmt':'str')+'">'+token+'</span>');
  };

  const oldCalcGen = window.calcGen;
  window.calcGen = function () {
    if (!value('source_dila_id')) return oldCalcGen();
    field('gen-display').textContent = value('gen_order') ? 'Số đời đang nhập: '+value('gen_order')+' · Cần kiểm đúng quy ước đếm.' : 'Chưa có số đời xác minh; có thể để trống.';
  };

  const oldReset = window.resetForm;
  window.resetForm = function () {
    identities = {};
    genLabel.innerHTML = originalGenLabel; genHint.textContent = originalGenHint;
    ['source_dila_id','source_bio_zh','source_notes','other_teachers'].forEach(id=>field(id).value='');
    field('source_gender').value='Male'; field('draft-notice').style.display='none';
    const params = new URLSearchParams(location.search), key = params.get('draft');
    if (key?.startsWith(PREFIX)) sessionStorage.removeItem(key);
    params.delete('draft'); params.delete('person_id');
    history.replaceState(null, '', location.pathname + (params.size ? '?' + params : ''));
    oldReset();
  };
  const oldSave = window.saveTTL;
  window.saveTTL = function () {
    const endpoints = [value('slug'),value('teacher_slug'),...pairs(value('other_teachers')).map(x=>x.slug),...pairs(value('disciples')).map(x=>x.slug)].filter(Boolean);
    if (endpoints.some(x=>! /^[a-z0-9_]+$/.test(x))) { showStatus('Slug chỉ gồm chữ thường không dấu, số và gạch dưới.', 'err'); return; }
    if (endpoints.slice(1).includes(value('slug'))) { showStatus('Không được tự làm thầy hoặc trò của chính mình.', 'err'); return; }
    if (value('source_dila_id') && !/^A\d{6}$/.test(value('source_dila_id'))) { showStatus('DILA ID phải có dạng A000885.', 'err'); return; }
    if (!value('source_dila_id')) return oldSave();
    if (!value('name_vi') || !value('slug')) { showStatus('Cần nhập tên Việt và slug trước khi lưu.', 'err'); return; }
    // Hồ sơ DILA được phép chưa có đời/dòng phái: không buộc admin điền số suy đoán.
    const filename = 'TS-' + value('source_dila_id') + '-' + slugify(value('name_vi')).split('_').map(w=>w[0].toUpperCase()+w.slice(1)).join('-');
    showStatus('Đang lưu file TTL...', 'info');
    return fetch('/daoanh/api/admin/monk_ttl', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({filename,slug:value('slug'),ttl_content:buildTTL()})
    }).then(async r=>{ const d=await r.json();
      showStatus(d.ok ? 'Đã lưu: '+d.filepath+'\nDILA ID: '+value('source_dila_id') : 'Lỗi: '+(d.error||'Không lưu được TTL'), d.ok?'ok':'err');
    }).catch(e=>showStatus('Lỗi kết nối: '+e.message,'err'));
  };


  const oldImport = window.parseTTLIntoForm;
  window.parseTTLIntoForm = function (ttl) {
    // Import file khác không được giữ ID/nguồn của bản nháp trước đó.
    resetForm();
    oldImport(ttl);
    const id = ttl.match(/owl:sameAs\s+<https:\/\/authority\.dila\.edu\.tw\/person\/search\.php\?aid=(A\d{6})>/);
    field('source_dila_id').value = id ? id[1] : '';
    livePreview();
  };

  function sourceNotes(p,d,vi) {
    const sections = [];
    const labels = {alt_names:'Tên khác', dynasty_xml:'Triều đại', occupation:'Nghề nghiệp',place_of_origin:'Xuất xứ',bio_extensive:'Tiểu sử chi tiết',birth_date:'Ngày sinh',death_date:'Ngày mất',death_note:'Ghi chú năm mất',birth_death_quote:'Trích dẫn ngày',active_at:'Nơi hoạt động',works_tripitaka:'Kinh trong Đại Tạng',works_by:'Tác phẩm',secondary_lit:'Tài liệu tham khảo',mentioned_in:'Được đề cập trong',listbibl:'Trích dẫn CBETA',name_latin:'Tên Latin',wikidata_id:'Wikidata',sex:'Giới tính',is_monk:'Tăng/Tục'};
    for (const [key,label] of Object.entries(labels)) {
      const zh = d[key]; const translated = vi[(key === 'dynasty_xml' ? 'dynasty' : key) + '_vi'];
      if (zh) sections.push(label + ' (DILA):\n' + (Array.isArray(zh) ? zh.join('\n') : zh));
      if (translated) sections.push(label + ' (Việt):\n' + (Array.isArray(translated) ? translated.join('\n') : translated));
    }
    if (vi.bio_concise_vi) sections.push('Tiểu sử vắn tắt (Việt):\n'+vi.bio_concise_vi);
    if (p.sect) sections.push('Tông phái trên hồ sơ: '+p.sect);
    (d.mentioned_in_refs || []).forEach(r=>{ if(r.url) sections.push(r.text+'\n'+r.url); });
    (d.relations || []).forEach(r=>sections.push((r.type==='teacher'?'Thầy':r.type==='student'?'Học trò':r.type)+': '+(r.name_vi||r.name||'')+' · '+r.person_id+'\n'+(r.bibl||'')+(r.ref_url?'\n'+r.ref_url:'')));
    sections.push('Nguồn DILA: '+authority(p.id));
    return sections.join('\n\n');
  }
  try {
    const params = new URLSearchParams(location.search), key = params.get('draft');
    if (!key) { livePreview(); return; }
    if (!key.startsWith(PREFIX)) throw new Error('Bản nháp không hợp lệ.');
    const draft = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (!draft || draft.version!==1 || draft.person_id!==params.get('person_id') || !/^A\d{6}$/.test(draft.person_id)) throw new Error('Không tìm thấy bản nháp của vị đang chọn. Hãy mở lại từ hồ sơ.');
    const p=draft.person, d=draft.dila, vi=draft.vi || {};
    const year = date => /^[+-]?\d{4}-\d{2}-\d{2}$/.test(date || '') ? Number(date.slice(0,date.indexOf('-',1))) : '';
    const set = (id,v) => { field(id).value = v ?? ''; };
    set('source_dila_id',draft.person_id); set('name_vi',p.name_vi || '');
    set('slug',relationSlug(draft.person_id)); set('name_zh',p.name_zh);
    set('bio_vi',[vi.bio_concise_vi || p.bio_vi,vi.bio_extensive_vi].filter(Boolean).join('\n\n'));
    set('birth_year',p.birth_year ?? year(d.birth_date));set('death_year',p.death_year ?? year(d.death_date));
    set('source_gender', /^(Nam|男|male)$/i.test(d.sex||'') ? 'Male' : /^(Nữ|女|female)$/i.test(d.sex||'') ? 'Female' : '');
    set('source_bio_zh',draft.bio_zh);set('source_notes',sourceNotes(p,d,vi));
    set('gen_order',p.gen_lamte ?? ''); // Không đoán đời từ thầy, niên đại hoặc số trong trích dẫn.
    set('lineage_custom',p.dharma_lineage || '');
    const viNames = new Map((vi.relations_vi||[]).map(r=>[r.person_id,r.name_vi]));
    const relations = (d.relations||[]).filter(r=>/^A\d{6}$/.test(r.person_id)&&r.person_id!==draft.person_id).map(r=>({...r,label:r.name_vi||viNames.get(r.person_id)||'',slug:relationSlug(r.person_id)}));
    relations.forEach(r=>identities[r.slug]=r.person_id);
    const teachers=relations.filter(r=>r.type==='teacher'),students=relations.filter(r=>r.type==='student');
    set('teacher_vi',teachers[0]?.label);set('teacher_slug',teachers[0]?.slug);
    set('other_teachers',teachers.slice(1).map(r=>r.label+' | '+r.slug).join(', '));
    set('disciples',students.map(r=>r.label+' | '+r.slug).join(', '));
    field('gen_order').closest('.field').querySelector('label').textContent = 'Số đời đã xác minh (nếu có)';
    field('gen_order').closest('.field').querySelector('.hint').textContent = 'Giữ đúng quy ước của nguồn; không tự suy số đời từ thầy.';
    field('lineage_name').closest('.field').querySelector('.req')?.remove();
    calcGen();livePreview();
    const notice=field('draft-notice'); notice.textContent='Đã nạp hồ sơ '+draft.person_id+' · '+teachers.length+' thầy · '+students.length+' học trò. Kiểm tra tên Việt, tông phái và số đời trước khi lưu; trường chưa có căn cứ được để trống.';notice.style.display='block';
  } catch(e) { field('draft-notice').textContent=e.message;field('draft-notice').style.display='block'; }
})();
