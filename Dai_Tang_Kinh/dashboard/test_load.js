#!/usr/bin/env node
/**
 * Test tích hợp: giả lập TRÌNH DUYỆT (fetch + DOM) rồi chạy đúng luồng của dashboard.
 * Mục đích: bắt lỗi runtime làm trang hiển thị "toàn bộ 0" — thứ mà test parser không thấy.
 *
 * Chạy:  node dashboard/test_load.js
 *
 * Cách làm:
 *   - require('./agent_team.js') khi CHƯA có document → module không tự boot
 *   - cắm globalThis.document / location / history / fetch (fetch đọc file thật từ đĩa
 *     đúng như server tĩnh trả về) rồi gọi mod.boot() để chạy luồng thật
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const ORIGIN = 'http://127.0.0.1:8090';
const PAGE = ORIGIN + '/dashboard/agent_team.html';

let pass = 0, fail = 0;
const failures = [];
function ok(cond, name, extra) {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; failures.push(name + (extra ? ' — ' + extra : '')); console.log('  FAIL ' + name + (extra ? ' — ' + extra : '')); }
}

function eq(actual, expected, name) {
  ok(actual === expected, name,
    'nhận ' + JSON.stringify(actual) + ', mong đợi ' + JSON.stringify(expected));
}

/* ---------------- fetch giả lập: đọc file thật từ đĩa ---------------- */
function makeResponse(body, status) {
  status = status || 200;
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status: status,
    text: () => Promise.resolve(text),
    json: () => Promise.resolve(JSON.parse(text))
  };
}

function listDir(dir, rel) {
  const files = fs.readdirSync(dir)
    .filter(f => f.toLowerCase().endsWith('.md') && !f.startsWith('.'))
    .map(f => ({ file: f, size: fs.statSync(path.join(dir, f)).size, modified: fs.statSync(path.join(dir, f)).mtimeMs / 1000 }));
  return { ok: true, source: rel, dir: rel, count: files.length, files };
}

const SRC_DIRS = {
  dila: path.join(ROOT, 'tasks'),
  real: path.join(ROOT, 'daoanh', 'tasks'),
  docs: path.join(ROOT, 'daoanh', 'docs')
};

const requests = [];
globalThis.fetch = function (url) {
  const u = new URL(url, PAGE);
  const p = decodeURIComponent(u.pathname);
  requests.push({ url: url, path: p, method: 'GET' });

  if (p === '/api/health') return Promise.resolve(makeResponse({ ok: true, mode: 'dila-dashboard' }));

  if (p === '/api/real-task-status') {
    const body = JSON.parse(arguments[1] && arguments[1].body ? arguments[1].body : '{}');
    requests.push({ path: p, method: 'POST', body: body });
    // server trả kèm notify khi Admin chuyển sang done
    const notify = body.status === 'done'
      ? { queued: true, title: 'T462 Done', message: 'Harness loop', state_url: '/api/notify-done/last' }
      : null;
    return Promise.resolve(makeResponse({ ok: true, file: body.file, old: 'in_progress', status: body.status, notify: notify }));
  }

  if (p === '/api/task-contexts') {
    return Promise.resolve(makeResponse({
      ok: true, count: 1, contexts: {
        'T22-nlp-fosi-zhi-founding-dates.md': {
          id: 'T22',
          description: 'MÔ TẢ TỔNG HỢP TỪ DOCS: pipeline founding date cho 59K places',
          extra: [{ source: 'daoanh/docs/tasktodo.md', kind: 'tasktodo',
                    text: 'Ngữ cảnh tasktodo: T22 đã deferred, code lưu trữ' }],
          sources: ['daoanh/docs/tasktodo.md'],
          done_when: 'Layer D ≥200 rows'
        }
      }
    }));
  }

  if (p === '/api/notify-done/last') {
    return Promise.resolve(makeResponse({
      ok: true,
      last: { state: 'done', started: '2026-10-25 20:00:00', finished: '2026-10-25 20:00:40',
              result: { ok: true, title: 'T462 Done', steps: [{ step: 'build_progress_data', ok: true, rc: 0 },
                                                              { step: 'notify_done', ok: true, rc: 0 }] } }
    }));
  }

  if (p === '/api/task-note') {
    const body = JSON.parse(arguments[1] && arguments[1].body ? arguments[1].body : '{}');
    requests.push({ path: p, method: 'POST', body: body });
    return Promise.resolve(makeResponse({ ok: true, source: body.source, file: body.file, stamp: '2026-10-25 17:10' }));
  }

  if (p === '/api/list') {
    const src = u.searchParams.get('source') || 'dila';
    const dir = SRC_DIRS[src];
    if (!dir) return Promise.resolve(makeResponse({ ok: false, error: 'source không hợp lệ' }, 400));
    return Promise.resolve(makeResponse(listDir(dir, src)));
  }

  if (p.startsWith('/api/')) return Promise.resolve(makeResponse({ ok: false }, 404));

  // file tĩnh: /tasks/x.md, /daoanh/tasks/x.md, /daoanh/docs/x.md
  for (const rel of ['tasks', 'daoanh/tasks', 'daoanh/docs']) {
    const prefix = '/' + rel + '/';
    if (!p.startsWith(prefix)) continue;
    const file = path.join(ROOT, rel, p.slice(prefix.length));
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return Promise.resolve(makeResponse('not found', 404));
    return Promise.resolve(makeResponse(fs.readFileSync(file, 'utf8')));
  }
  return Promise.resolve(makeResponse('not found', 404));
};

/* ---------------- DOM giả lập ---------------- */
const els = {};
function fakeEl(id) {
  return {
    id: id || '', innerHTML: '', textContent: '', title: '', disabled: false, dataset: {},
    classList: { add() { }, remove() { }, contains() { return false; } },
    style: {}, children: [],
    addEventListener() { }, appendChild(c) { this.children.push(c); }, remove() { },
    getAttribute() { return null; }, setAttribute() { }
  };
}
function el(id) { if (!els[id]) els[id] = fakeEl(id); return els[id]; }
['tasksContainer', 'modeBadge', 'sourceNote', 'statsNote', 'totalTasks', 'inProgress', 'awaitingAdmin',
  'totalBugs', 'totalBlockers', 'toastStack', 'refreshBtn',
  'searchInput', 'statusFilter', 'clearFilter', 'categoryTabs'].forEach(el);

const tabs = ['dila', 'real', 'docs'].map(s => {
  const t = fakeEl('tab-' + s);
  t.getAttribute = (k) => (k === 'data-source' ? s : null);
  return t;
});

globalThis.document = {
  readyState: 'complete',
  getElementById: el,
  querySelectorAll: (sel) => (sel.indexOf('sourceTabs') !== -1 ? tabs : []),
  addEventListener() { },
  createElement: () => fakeEl('tmp'),
  body: { appendChild() { } }
};

const locationObj = { href: PAGE, search: '', protocol: 'http:' };
globalThis.location = locationObj;
globalThis.history = { replaceState() { } };
globalThis.confirm = () => true;

/* ---------------- chạy ---------------- */
const mod = require('./agent_team.js');

async function main() {
  console.log('\n[A] Nguồn DILA (mặc định) qua HTTP giả lập');
  locationObj.search = '';
  await mod.boot();
  const html = el('tasksContainer').innerHTML;
  ok(html.includes('task-card'), 'render được task card (không bị 0)');
  ok(html.includes('data-task="DILA-TASK-0001"'), 'có DILA-TASK-0001');
  ok(html.includes('data-status="'), 'card có status từ file (không hardcode)');
  ok((html.match(/class="task-card"/g) || []).length === 3, 'render đủ 3 card');
  ok(el('totalTasks').textContent === '3', 'stats Tasks = 3', el('totalTasks').textContent);
  ok(el('totalBugs').textContent === '4', 'stats Bugs = 4', el('totalBugs').textContent);
  ok(el('sourceNote').innerHTML.includes('tasks/'), 'dòng Nguồn ghi đúng thư mục');

  console.log('\n[B] Nguồn TASK THẬT (daoanh/tasks)');
  const REAL_COUNT = fs.readdirSync(path.join(ROOT, 'daoanh', 'tasks'))
    .filter(f => f.toLowerCase().endsWith('.md') && !f.startsWith('.')).length;
  const realTasks = await mod.setSource('real');
  const realHtml = el('tasksContainer').innerHTML;
  ok(realHtml.includes('data-task="T'), 'render task thật (T…/BUG-…)');
  ok(/<h3 class="task-title">T22 : Founding Date Pipeline/.test(realHtml),
    'tiêu đề có mã task trước mô tả: "T22 : Founding Date Pipeline…"');
  ok(!/T22 : T22/.test(realHtml), 'không lặp mã task 2 lần');
  ok(!realHtml.includes('<span class="task-id">T22</span>'), 'không còn mã task tách riêng ở header (đã gộp vào tiêu đề)');
  ok(realHtml.includes('status-'), 'badge status của task thật');
  ok(!realHtml.includes('class="fatal"'), 'không rơi vào khối lỗi');
  ok(el('totalTasks').textContent === String(REAL_COUNT),
    'stats Tasks = ' + REAL_COUNT + ' (tổng file thật)', el('totalTasks').textContent);
  ok((realHtml.match(/class="task-card"/g) || []).length === REAL_COUNT,
    'hiển thị đủ ' + REAL_COUNT + ' card, không cắt bớt');
  ok(realHtml.indexOf('data-task="T462"') !== -1 && realHtml.indexOf('data-task="T462"') < realHtml.indexOf('data-task="T461"'),
    'mới nhất trước: T462 đứng trên T461');
  ok(realHtml.indexOf('data-task="T462"') < realHtml.indexOf('data-task="T245"'),
    'T462 (mới) đứng trên T245 (cũ)');
  ok(realHtml.indexOf('data-task="T462"') < realHtml.indexOf('data-task="T11"'),
    'T462 đứng trên T11');
  ok(realHtml.includes('Task thật của dự án'), 'ghi rõ task thật');
  ok(requests.some(r => r.path === '/api/task-contexts'), 'có gọi /api/task-contexts để bù mô tả task thiếu');
  ok(realHtml.includes('Ngữ cảnh thêm'), 'card hiện "Ngữ cảnh thêm (từ docs)"');
  ok(realHtml.includes('daoanh/docs/tasktodo.md'), 'card có link file nguồn (tasktodo.md)');
  ok(realHtml.includes('Ngữ cảnh tasktodo'), 'card hiện đúng nội dung ngữ cảnh từ docs');
  ok(realHtml.includes('class="panel brief"'), 'card có panel "Mô tả nhiệm vụ & mục tiêu hoàn thành"');
  ok(realHtml.includes('Mục tiêu hoàn thành (done_when)'), 'card hiện done_when để Admin check TaskDone');
  ok(realHtml.includes('Layer D'), 'card T22 hiện đúng nội dung done_when');
  ok(/class="panel brief"/.test(realHtml) && realHtml.includes('Mô tả nhiệm vụ'), 'card hiện mô tả nhiệm vụ');
  ok(realHtml.includes('agent-empty'), 'task thật gọn: 1 dòng "chưa có dữ liệu", không bịa 3 agent');
  ok(realHtml.includes('id="status-T462-harness-coder-tester-loop.md"'), 'card có select đổi status (A)');
  ok(realHtml.includes('<option value="pending"'), 'select có option status thật (pending)');
  ok(realHtml.includes('<option value="in_progress"'), 'select có option in_progress');

  console.log('\n[B2] Cate chips: gom nhóm theo trạng thái (Coding/Testing/Debugging…)');
  ok(realHtml.includes('class="task-group"'), 'xem "Tất cả" → gom thành nhóm');
  ok(realHtml.includes('class="group-head"'), 'mỗi nhóm có tiêu đề trạng thái');
  ok(realHtml.includes('data-category="coding"'), 'có nhóm Coding');
  ok(realHtml.includes('data-category="debugging"'), 'có nhóm Debugging');
  ok(realHtml.includes('data-category="done"'), 'có nhóm Done');
  ok(realHtml.indexOf('data-category="coding"') < realHtml.indexOf('data-category="pending"'),
    'nhóm đang làm (Coding) đứng trước Pending');
  ok(els.categoryTabs.innerHTML.includes('data-category="all"'), 'có chip "Tất cả"');
  ok(els.categoryTabs.innerHTML.includes('data-category="debugging"'), 'có chip Debugging');
  ok(els.categoryTabs.innerHTML.includes('data-category="testing"'), 'chip Testing vẫn hiện dù 0 task');
  eq((els.categoryTabs.innerHTML.match(/class="cat-chip/g) || []).length, 8,
    'đủ 8 chip: Tất cả + 6 nhóm + Khác');
  ok(/class="n">\d+/.test(els.categoryTabs.innerHTML), 'chip có số lượng');

  const counts = mod.countByCategory(realTasks);
  const sum = Object.keys(counts).reduce((s, k) => s + counts[k], 0);
  eq(sum, realTasks.length, 'tổng đếm theo nhóm = tổng task (' + realTasks.length + ')');
  ok(counts.coding > 0 && counts.pending > 0, 'có task ở Coding và Pending', JSON.stringify(counts));

  const dbg = mod.filterByCategory(realTasks, 'debugging');
  ok(dbg.length === counts.debugging && dbg.every(t => ['debugging', 'bug_found'].indexOf(t.status) !== -1),
    'click Debugging → chỉ task debugging/bug_found (' + dbg.length + ')');

  // mô phỏng bấm chip Coding
  mod.setUiState('', '', 'coding');
  mod.render(realTasks, { total: REAL_COUNT, shown: REAL_COUNT, source: 'real' });
  const codingHtml = el('tasksContainer').innerHTML;
  const codingCards = (codingHtml.match(/class="task-card"/g) || []).length;
  ok(codingCards === counts.coding, 'bấm Coding → chỉ còn ' + counts.coding + ' card', String(codingCards));
  ok(/nhóm 💻 Coding/.test(el('statsNote').textContent), 'statsNote ghi rõ nhóm đang xem', el('statsNote').textContent);
  ok(!codingHtml.includes('class="task-group"'), 'khi đã chọn nhóm → không lặp lại group header');
  mod.setUiState('', '', 'all');

  console.log('\n[B2b] Gộp A+B: search + lọc status trên CÙNG page');
  // lọc theo mã task
  const byCode = mod.filterTasks(realTasks, 'T46', '');
  ok(byCode.length >= 3 && byCode.every(t => /T46\d/.test(t.id)), 'search "T46" lọc đúng nhóm T46x (' + byCode.map(t => t.id).join(',') + ')');
  // lọc theo status
  const blocked = mod.filterTasks(realTasks, '', 'blocked');
  ok(blocked.length > 0 && blocked.every(t => t.status === 'blocked'), 'lọc status=blocked: ' + blocked.length + ' task');
  // kết hợp search + status
  const both = mod.filterTasks(realTasks, 'T4', 'in_progress');
  ok(both.every(t => t.status === 'in_progress' && /T4/.test(t.id)), 'kết hợp search + status');
  // render theo filter: chỉ còn card khớp
  mod.setUiState('T461', '');
  mod.render(realTasks, { total: REAL_COUNT, shown: REAL_COUNT, source: 'real' });
  const filteredHtml = el('tasksContainer').innerHTML;
  ok((filteredHtml.match(/class="task-card"/g) || []).length === 1, 'search "T461" → còn đúng 1 card');
  ok(filteredHtml.includes('data-task="T461"'), 'card còn lại là T461');
  ok(new RegExp('đang lọc: 1\\/' + REAL_COUNT).test(el('statsNote').textContent),
    'statsNote báo đang lọc 1/' + REAL_COUNT, el('statsNote').textContent);
  // xoá lọc
  mod.setUiState('', '');
  mod.render(realTasks, { total: REAL_COUNT, shown: REAL_COUNT, source: 'real' });
  ok((el('tasksContainer').innerHTML.match(/class="task-card"/g) || []).length === REAL_COUNT,
    'xoá lọc → trả lại ' + REAL_COUNT + ' card');

  console.log('\n[B3] Đổi status task thật (A) gọi đúng API');
  requests.length = 0;
  await mod.changeRealStatus('T462-harness-coder-tester-loop.md', 'done');
  const post = requests.find(r => r.method === 'POST' && r.path === '/api/real-task-status');
  ok(!!post, 'có POST /api/real-task-status');
  ok(post && post.body.file === 'T462-harness-coder-tester-loop.md' && post.body.status === 'done',
    'body gửi đúng file + status', JSON.stringify(post && post.body));

  console.log('\n[B3b] Admin xác nhận DONE → build_progress_data + Tiểu Thiên báo Done');
  await new Promise(r => setTimeout(r, 50));
  const toastMsgs = el('toastStack').children.map(c => c.textContent).join(' | ');
  ok(/Đang chạy build_progress_data/.test(toastMsgs), 'báo đang chạy pipeline nền', toastMsgs);
  ok(requests.some(r => r.path === '/api/notify-done/last'), 'có gọi /api/notify-done/last để lấy kết quả');
  ok(/Tiểu Thiên đã báo/.test(toastMsgs), 'báo kết quả: Tiểu Thiên đã báo', toastMsgs);
  ok(/T462 Done/.test(toastMsgs), 'toast có tiêu đề "T462 Done"', toastMsgs);

  console.log('\n[B4] Editor Admin note cho từng task (VD BUG-025)');
  ok(realHtml.includes('id="note-btn-T462-harness-coder-tester-loop.md"'), 'task thật có nút ghi chú');
  ok(realHtml.includes('id="note-editor-T462-harness-coder-tester-loop.md"'), 'task thật có editor inline');
  ok(realHtml.includes('id="note-input-T462-harness-coder-tester-loop.md"'), 'editor có textarea');
  ok(realHtml.includes('<option value="debugging"'), 'status select có option debugging (Debug)');
  requests.length = 0;
  await mod.saveNote('T462-harness-coder-tester-loop.md', 'Admin: bug ở bước chọn item lần 2');
  const notePost = requests.find(r => r.method === 'POST' && r.path === '/api/task-note');
  ok(!!notePost, 'có POST /api/task-note');
  ok(notePost && notePost.body.source === 'real' &&
     notePost.body.file === 'T462-harness-coder-tester-loop.md' &&
     /Admin: bug/.test(notePost.body.note), 'note gửi đúng source=real + file + nội dung',
     JSON.stringify(notePost && notePost.body));

  await mod.setSource('dila');
  requests.length = 0;
  await mod.saveNote('DILA-TASK-0002.md', 'ghichu dila');
  const notePost2 = requests.find(r => r.method === 'POST' && r.path === '/api/task-note');
  ok(notePost2 && notePost2.body.source === 'dila', 'task DILA gửi source=dila');
  ok(el('tasksContainer').innerHTML.includes('id="note-btn-DILA-TASK-0002.md"'), 'task DILA cũng có editor');

  console.log('\n[C] Nguồn DOCS THẬT (daoanh/docs)');
  await mod.setSource('docs');
  const docsHtml = el('tasksContainer').innerHTML;
  ok(docsHtml.includes('doc-card'), 'render doc card');
  ok(docsHtml.includes('Mở file'), 'doc card có link mở file');
  ok(docsHtml.includes('daoanh/docs/'), 'link trỏ đúng daoanh/docs/');
  ok(el('inProgress').textContent === '—', 'docs: stat tiến độ = "—" (không bịa 0)');

  console.log('\n[D] Mở bằng file:// (double-click)');
  mod.setSourceState('dila');
  locationObj.protocol = 'file:';
  await mod.boot();
  const fatal = el('tasksContainer').innerHTML;
  ok(fatal.includes('class="fatal"'), 'hiện khối cảnh báo thay vì im lặng');
  ok(fatal.includes('file://'), 'nói rõ nguyên nhân file://');
  ok(fatal.includes('python dashboard/serve.py'), 'có lệnh chạy server');
  ok(fatal.includes('http://127.0.0.1:8090/dashboard/agent_team.html'), 'có URL đúng');

  console.log('\n[E] Server chạy sai thư mục (/tasks/ 404)');
  locationObj.protocol = 'http:';
  const realFetch = globalThis.fetch;
  globalThis.fetch = function (url) {
    const u = new URL(url, PAGE);
    if (u.pathname.startsWith('/api/')) return Promise.resolve(makeResponse({ ok: false }, 404));
    return Promise.resolve(makeResponse('not found', 404));
  };
  await mod.refresh();
  const broken = el('tasksContainer').innerHTML;
  ok(broken.includes('class="fatal"'), 'hiện cảnh báo khi server sai thư mục');
  ok(broken.includes('Dai_Tang_Kinh'), 'hướng dẫn chạy ở đúng thư mục');
  globalThis.fetch = realFetch;

  console.log('\n────────────────────────────────────────');
  console.log(`KẾT QUẢ: ${pass} pass, ${fail} fail`);
  if (fail) { failures.forEach(f => console.log('  - ' + f)); process.exit(1); }
  console.log('TẤT CẢ TEST PASS');
}

main().catch(e => { console.error('LỖI RUNTIME:', e); process.exit(1); });
