
/* ── Theme toggle ──────────────────────────────── */
const themes = ['', 'light', 'dark'];
let ti = 0;
const btn = document.getElementById('themeBtn');
btn.addEventListener('click', () => {
  ti = (ti + 1) % themes.length;
  const t = themes[ti];
  if (t) document.documentElement.setAttribute('data-theme', t);
  else document.documentElement.removeAttribute('data-theme');
});

/* ── Search ────────────────────────────────────── */
function handleSearch(e) {
  e.preventDefault();
  const q = document.getElementById('heroSearch').value.trim();
  if (!q) return;
  if (q.includes('Thiếu Lâm') || q.includes('少林')) {
    showPlaceDemo();
    return;
  }
  const placesUrl = '/daoanh/places?q=' + encodeURIComponent(q);
  // T453: tra kinh lục DILA trước; không có kết quả (hoặc lỗi) → đi trang địa danh như cũ.
  fetch('/daoanh/api/search?q=' + encodeURIComponent(q))
    .then(r => r.ok ? r.json() : null)
    .then(d => {
      const works = (d && d.dila_works) || [];
      const people = (d && d.dila_people) || [];
      if (!works.length && !people.length) { window.location.href = placesUrl; return; }
      renderDilaWorks(works, q, placesUrl, people, d.dila_works_total);
    })
    .catch(() => { window.location.href = placesUrl; });
}

/* ── T453: hiển thị kinh lục DILA (badge nguồn từng lớp) ── */
function _esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
    ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}
/* Một dòng thông tin: biểu tượng · nhãn · giá trị (giá trị đã escape sẵn). Giá trị rỗng → bỏ dòng. */
function _line(icon, label, valueHtml) {
  return valueHtml ? `<div class="dw-line"><span class="ic">${icon}</span><span class="lb">${label}</span>` +
    `<span class="vl">${valueHtml}</span></div>` : '';
}
function renderDilaPeople(people) {
  return people.map(p => {
    const places = (p.places || []).map(pl =>
      `${_esc(pl.name_vi || pl.name_zh)} <span class="dw-han">${_esc(pl.name_zh)}</span> (${_esc(pl.works)})`).join(' · ');
    return `<div class="dw-item dw-person-card">
      <div>🧘 <span class="dw-title">${_esc(p.name_vi || p.name_zh)}</span> <span class="dw-han">${_esc(p.name_zh)}</span>
        <span class="dw-badge" title="Tên Việt: phiên âm ZQ">ZQ</span></div>
      ${_line('🆔', 'DILA ID', `<span class="dw-badge dila" style="margin-left:0">${_esc(p.person_id)}</span>`)}
      ${_line('📚', 'Tác phẩm', `${_esc(p.works)} bộ · ${_esc(p.juans ?? 0)} quyển`)}
      ${_line('📍', 'Nơi dịch', places)}
      <div class="dw-meta dw-actions">
        <button type="button" class="dw-btn" data-pid="${_esc(p.person_id)}" data-sort="juans">Xem tất cả ${_esc(p.works)} tác phẩm</button>
        <span class="dw-sort" hidden>Sắp theo:
          <button type="button" class="dw-btn" data-pid="${_esc(p.person_id)}" data-sort="juans">số quyển</button>
          <button type="button" class="dw-btn" data-pid="${_esc(p.person_id)}" data-sort="year">năm</button>
          <button type="button" class="dw-btn" data-pid="${_esc(p.person_id)}" data-sort="title">tên</button></span>
      </div>
      <div class="dw-all"></div>
    </div>`;
  }).join('');
}
/* T453: "Xem tất cả" — tải toàn bộ tác phẩm của một người */
function loadAllWorks(btn) {
  const card = btn.closest('.dw-person-card');
  const out = card.querySelector('.dw-all');
  out.innerHTML = '<div class="dw-meta">Đang tải…</div>';
  fetch(`/daoanh/api/public/dila_works?person_id=${encodeURIComponent(btn.dataset.pid)}&sort=${btn.dataset.sort}`)
    .then(r => r.json())
    .then(d => {
      card.querySelector('.dw-sort').hidden = false;
      out.innerHTML = `<ol class="dw-list">${(d.works || []).map(w => {
        const yr = w.time_from == null ? '' : (w.year_precision === 'dynasty_range'
          ? ` · ${_esc(w.dynasty_vi || '')} (theo triều đại)` : ` · ${_esc(w.time_from)}${w.time_to && w.time_to !== w.time_from ? '–' + _esc(w.time_to) : ''}`);
        return `<li><b>${_esc(w.title_vi || w.title_zh)}</b> <span class="dw-han">${_esc(w.title_zh)}</span>
          <span class="dw-meta">· ${_esc(w.cbeta_id)} · ${_esc(w.juans ?? '?')} quyển${yr}${w.places_vi ? ' · ' + _esc(w.places_vi) : ''}</span></li>`;
      }).join('')}</ol>`;
    })
    .catch(() => { out.innerHTML = '<div class="dw-meta">Không tải được danh sách.</div>'; });
}
document.addEventListener('click', e => {
  const b = e.target.closest('.dw-btn');
  if (b) loadAllWorks(b);
});
function renderDilaWorks(works, q, placesUrl, people, total) {
  total = total || works.length;
  const countText = total > works.length
    ? `${_esc(total)} kết quả cho “${_esc(q)}” (hiển thị ${works.length})`
    : `${_esc(total)} kết quả cho “${_esc(q)}”`;
  const box = document.getElementById('dilaWorks');
  const items = works.map(w => {
    const years = w.time_from == null ? '' :
      (w.year_precision === 'dynasty_range'
        ? `${_esc(w.dynasty_vi || '')} (${_esc(w.time_from)}–${_esc(w.time_to)}, theo triều đại)`
        : `${_esc(w.time_from)}${w.time_to ? '–' + _esc(w.time_to) : ''}`);
    const people = (w.contributors || []).map(c =>
      `<span class="dw-person" title="DILA ID ${_esc(c.person_id)}">${_esc(c.name_vi || c.name_zh)}</span>` +
      ` <span class="dw-han">${_esc(c.name_zh)}</span>` +
      `<span class="dw-badge" title="Tên Việt: phiên âm ZQ">ZQ</span>`).join(', ');
    const size = [w.vol ? `Tập ${_esc(w.vol)}` : '', w.juans != null ? `${_esc(w.juans)} quyển` : '',
      w.cjk_chars ? `${Number(w.cjk_chars).toLocaleString('vi-VN')} chữ` : ''].filter(Boolean).join(' · ');
    const cat = [w.category_vi ? `${_esc(w.category_vi)} <span class="dw-han">${_esc(w.category_zh)}</span>` : '',
      w.orig_category_vi ? `nguyên phân loại: ${_esc(w.orig_category_vi)} <span class="dw-han">${_esc(w.orig_category_zh)}</span>` : '']
      .filter(Boolean).join(' · ');
    return `<div class="dw-item">
      <div>📖 <span class="dw-title">${_esc(w.title_vi || w.title_zh)}</span>
        ${w.title_vi
          ? '<span class="dw-badge" title="Bản dịch Cloud session, chưa duyệt">Bản dịch AI · chưa duyệt</span>'
          : '<span class="dw-badge" title="Chưa có bản dịch tiếng Việt">Chưa dịch</span>'}</div>
      ${_line('🀄', 'Tên Hán', `${_esc(w.title_zh)} <span class="dw-badge dila" title="Tên Hán, năm, mã: DILA authority_catalog">DILA</span>`)}
      ${_line('🔖', 'Mã', `${_esc(w.cbeta_id)}${w.authority_id ? ` · DILA ${_esc(w.authority_id)}` : ''}`)}
      ${_line('📚', 'Quy mô', size)}
      ${_line('🗂️', 'Bộ loại', cat)}
      ${_line('🕰️', 'Niên đại', years)}
      ${_line('✍️', 'Soạn dịch', _esc(w.byline_vi || w.byline_zh))}
      ${_line('👤', 'Người', people)}
      ${_line('📍', 'Nơi dịch', _esc(w.places_vi))}
    </div>`;
  }).join('');
  box.innerHTML = `<div class="dw-head"><span>Kinh lục DILA: ${countText}</span>
    <a href="${placesUrl}">Tìm địa danh →</a></div>${renderDilaPeople(people || [])}${items}`;
  box.hidden = false;
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function setSearch(val) {
  document.getElementById('heroSearch').value = val;
  document.getElementById('heroSearch').focus();
}

/* ── Thiếu Lâm Tự demo panel ───────────────────── */
let _minimap = null;
function showPlaceDemo() {
  document.getElementById('heroSearch').value = 'Thiếu Lâm Tự';
  const panel = document.getElementById('placeResult');
  panel.classList.add('visible');
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  // Init Leaflet minimap (lazy, once)
  setTimeout(() => {
    const el = document.getElementById('sr-minimap');
    if (!el || _minimap) { if (_minimap) _minimap.invalidateSize(); return; }
    _minimap = L.map(el, { zoomControl: true, attributionControl: false, scrollWheelZoom: true, dragging: true })
      .setView([34.5885, 112.9343], 8);
    L.tileLayer('https://mt1.google.com/vt/lyrs=m&hl=vi&x={x}&y={y}&z={z}', { maxZoom: 20 }).addTo(_minimap);
    L.circleMarker([34.5885, 112.9343], {
      radius: 8, color: '#B8941E', fillColor: '#B8941E', fillOpacity: 0.9, weight: 2
    }).bindTooltip('少林寺 · Thiếu Lâm Tự', { permanent: true, direction: 'top', offset: [0, -10],
      className: 'minimap-tip' }).addTo(_minimap).openTooltip();
  }, 80);
}
function closePlaceDemo() {
  document.getElementById('placeResult').classList.remove('visible');
}

