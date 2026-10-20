/* T358: review cục bộ, không có endpoint ghi task/DB. */
(function () {
  'use strict';
  const VERSION = 'ptda-triage-execution/v1';
  const PREFIX = 'ptda:harness:admin-review:v1:';
  const REQUIRED = ['implementation', 'tests', 'independent_qa'];
  const root = document.getElementById('triageExecution');
  if (!root) return;
  const rows = document.getElementById('triageRows');
  const message = document.getElementById('triageMessage');
  const dialog = document.getElementById('triageConfirm');
  const input = document.getElementById('triageConfirmInput');
  const save = document.getElementById('triageConfirmSave');
  const error = document.getElementById('triageConfirmError');
  let report = null;
  let taskIndex = new Map();
  let active = null;
  let loadNumber = 0;

  function node(tag, value, className) {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = String(value);
    if (className) element.className = className;
    return element;
  }
  // Chỉ liên kết tài liệu nội bộ; chuỗi JSON không trở thành HTML/JS.
  function safeLink(href) {
    if (typeof href !== 'string' || !href.startsWith('../')) return null;
    const relative = href.slice(3).split('/');
    if (!['tasks', 'docs', 'scripts', 'admin'].includes(relative[0]) || !relative.every(part => /^[A-Za-z0-9_.-]+$/.test(part)) || !/[.](md|py|html)$/.test(relative[relative.length - 1])) return null;
    const parts = href.slice(3).split('/');
    return parts.every(part => part && part !== '.' && part !== '..') ? href : null;
  }
  function references(parent, values) {
    if (!Array.isArray(values)) return;
    values.forEach(ref => {
      const href = ref && safeLink(ref.href);
      const item = node('span', undefined, 'triage-reference');
      if (href) {
        const link = node('a', ref.label || href);
        link.setAttribute('href', href);
        item.append(link);
      } else {
        item.textContent = String(ref && ref.label || 'Nguồn không hợp lệ');
      }
      parent.append(item);
    });
  }
  function hasProof(check) {
    return Array.isArray(check.evidence) && check.evidence.some(ref => ref && safeLink(ref.href));
  }
  function gate(row) {
    if (!report || report.definition_version !== VERSION || row.kind !== 'task') return 'Chỉ là blocker, chưa có bản build nghiệm thu.';
    if (!Array.isArray(row.task_ids) || !row.task_ids.length) return 'Thiếu ID task.';
    for (const id of row.task_ids) {
      const matches = taskIndex.get(id) || [];
      if (matches.length !== 1) return 'ID thiếu hoặc trùng trong Dashboard: ' + id;
      if (matches[0].status === 'blocked') return 'Task đang blocked: ' + id;
    }
    if (!Array.isArray(row.prerequisites) || row.prerequisites.some(pre => !pre || pre.satisfied !== true)) return 'Chưa đủ điều kiện trước.';
    const dev = row.development;
    if (!dev || dev.completed !== true || !Array.isArray(dev.checks)) return 'Dev chưa xác nhận hoàn tất.';
    for (const name of REQUIRED) {
      const checks = dev.checks.filter(check => check && check.key === name);
      if (checks.length !== 1 || checks[0].passed !== true || !hasProof(checks[0])) return 'Thiếu PASS có bằng chứng: ' + name;
    }
    if (dev.checks.some(check => !check || check.passed !== true || !hasProof(check))) return 'Còn điều kiện dev chưa PASS.';
    return '';
  }
  // So nội dung chính xác thay vì tin trạng thái/receipt của một báo cáo cũ.
  function token(row) {
    return JSON.stringify({version: report.definition_version, report: report.report_id, revision: report.revision,
      row: row.row_id, ids: row.task_ids, prerequisites: row.prerequisites, development: row.development,
      tasks: row.task_ids.map(id => (taskIndex.get(id) || []).map(task => ({id: task.id, status: task.status, file: task.file})))});
  }
  function receipt(row) {
    try {
      const value = JSON.parse(localStorage.getItem(PREFIX + row.row_id));
      return value && value.review_status === 'admin_reviewed' && value.evidence_token === token(row) ? value : null;
    } catch (_) { return null; }
  }
  function currentStatus(row) {
    return (row.task_ids || []).map(id => {
      const matches = taskIndex.get(id) || [];
      return id + ': ' + (matches.length === 1 ? matches[0].status : matches.length > 1 ? 'ID trùng' : 'không có trong Dashboard');
    }).join(' · ');
  }
  function render() {
    rows.replaceChildren();
    document.getElementById('triageMeta').textContent = 'Audit: ' + report.audited_at + ' · ' + report.revision + ' · Các bằng chứng này là snapshot, không phải kiểm production mới.';
    const sequences = document.getElementById('triageSequences');
    sequences.replaceChildren();
    (report.sequences || []).forEach(value => sequences.append(node('span', value, 'triage-sequence')));
    report.rows.forEach(row => {
      const tr = node('tr');
      tr.dataset.rowId = row.row_id;
      const task = node('th', undefined, 'triage-task');
      task.scope = 'row';
      task.append(node('strong', row.title));
      task.append(node('small', currentStatus(row)));
      references(task, row.links);
      const agent = node('td', row.agent);
      const prerequisites = node('td');
      (row.prerequisites || []).forEach(pre => prerequisites.append(node('div', (pre.satisfied === true ? '✓ ' : '○ ') + pre.label)));
      if (!row.prerequisites || !row.prerequisites.length) prerequisites.textContent = 'Không có phụ thuộc chặn đã biết; vẫn cần scope và QA.';
      const development = node('td');
      development.append(node('p', row.development.summary));
      const checks = node('ul', undefined, 'triage-checks');
      row.development.checks.forEach(check => checks.append(node('li', (check.passed === true ? 'PASS: ' : 'Chưa PASS: ') + check.label)));
      development.append(checks);
      references(development, row.evidence);
      const next = node('td', row.admin_next_action);
      const review = node('td');
      const reason = gate(row);
      const reviewed = !reason && receipt(row);
      const button = node('button', reviewed ? 'Đã review cục bộ' : 'DONE');
      button.type = 'button';
      button.className = 'hx-btn triage-done';
      button.disabled = Boolean(reason || reviewed);
      button.setAttribute('aria-label', 'DONE review ' + row.title);
      button.setAttribute('aria-describedby', 'triage-reason-' + row.row_id);
      const why = node('small', reason || (reviewed ? 'Chỉ lưu trên trình duyệt này; task giữ nguyên.' : 'Đủ điều kiện dev; chờ Admin xác nhận.'));
      why.id = 'triage-reason-' + row.row_id;
      button.addEventListener('click', () => open(row, button));
      review.append(button, why);
      tr.append(task, agent, prerequisites, development, next, review);
      rows.append(tr);
    });
  }
  function close() {
    if (dialog.open) dialog.close();
    const previous = active;
    active = null;
    input.value = '';
    save.disabled = true;
    if (previous && previous.button.isConnected) previous.button.focus();
  }
  function open(row, button) {
    if (gate(row) || receipt(row)) return;
    active = {row, button, token: token(row)};
    input.value = '';
    save.disabled = true;
    error.textContent = '';
    document.getElementById('triageConfirmTitle').textContent = 'DONE review — ' + row.title;
    document.getElementById('triageConfirmScope').textContent = 'Xác nhận bạn đã review các bằng chứng dev. Chỉ lưu admin_reviewed cục bộ; không thay task frontmatter, Dashboard tổng hoặc dữ liệu production.';
    document.getElementById('triageConfirmLabel').textContent = 'Nhập chính xác ' + row.row_id + ' để xác nhận';
    if (typeof dialog.showModal !== 'function') { active = null; message.textContent = 'Trình duyệt chưa hỗ trợ dialog; review vẫn khóa.'; return; }
    dialog.showModal();
    input.focus();
  }
  input.addEventListener('input', () => { save.disabled = !active || input.value !== active.row.row_id || Boolean(gate(active.row)); });
  document.getElementById('triageCancel').addEventListener('click', close);
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  save.addEventListener('click', () => {
    if (!active || input.value !== active.row.row_id) return;
    const row = active.row;
    if (gate(row) || active.token !== token(row)) { error.textContent = 'Điều kiện đã đổi; tải lại báo cáo trước khi review.'; save.disabled = true; return; }
    try {
      const value = {definition_version: VERSION, report_id: report.report_id, revision: report.revision,
        row_id: row.row_id, review_status: 'admin_reviewed', evidence_token: token(row), reviewed_at: new Date().toISOString()};
      localStorage.setItem(PREFIX + row.row_id, JSON.stringify(value));
      if (!receipt(row)) throw new Error('Không đọc lại được đánh dấu review.');
      close();
      render();
      message.textContent = 'Đã lưu review cục bộ cho ' + row.row_id + '. Trạng thái task và production giữ nguyên.';
      const refreshed = rows.querySelector('[data-row-id="' + row.row_id + '"] .triage-done');
      if (refreshed) refreshed.parentElement.querySelector('small').setAttribute('tabindex', '-1');
      if (refreshed) refreshed.parentElement.querySelector('small').focus();
    } catch (_) {
      error.textContent = 'Không lưu được localStorage. Chưa xác nhận review; kiểm tra quyền lưu của trình duyệt.';
    }
  });
  async function getJson(path) {
    const response = await fetch(path, {method: 'GET', cache: 'no-store'});
    if (!response.ok) throw new Error('Không tải được báo cáo.');
    return response.json();
  }
  async function load() {
    const number = ++loadNumber;
    close();
    report = null;
    rows.replaceChildren();
    message.textContent = 'Đang tải báo cáo…';
    try {
      const values = await Promise.all([getJson('../data/triage_execution_report.json'), getJson('../data/progress_data.json')]);
      if (number !== loadNumber) return;
      const candidate = values[0];
      if (!candidate || candidate.definition_version !== VERSION || typeof candidate.report_id !== 'string' || typeof candidate.revision !== 'string' || !Array.isArray(candidate.rows) || !Array.isArray(values[1].tasks)) throw new Error('Sai định nghĩa báo cáo.');
      const ids = new Set();
      candidate.rows.forEach(row => {
        if (!row || !/^[A-Za-z0-9_-]+$/.test(row.row_id) || ids.has(row.row_id) || !row.development || !Array.isArray(row.development.checks) || !Array.isArray(row.task_ids)) throw new Error('Sai định nghĩa row.');
        ids.add(row.row_id);
      });
      taskIndex = new Map();
      values[1].tasks.forEach(task => { const matches = taskIndex.get(task.id) || []; matches.push(task); taskIndex.set(task.id, matches); });
      report = candidate;
      render();
      message.textContent = 'Báo cáo đã tải. DONE khóa cho mọi dòng còn thiếu điều kiện dev; local review không đóng task.';
    } catch (_) {
      if (number !== loadNumber) return;
      report = null;
      rows.replaceChildren();
      message.textContent = 'Không tải/kiểm được báo cáo. DONE bị khóa; thử tải lại.';
    }
  }
  document.getElementById('triageReload').addEventListener('click', load);
  load();
}());
