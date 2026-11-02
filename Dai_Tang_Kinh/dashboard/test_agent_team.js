#!/usr/bin/env node
/**
 * Test dashboard DILA Team — chạy:  node dashboard/test_agent_team.js
 *
 * Test này KHÔNG mở browser, KHÔNG gọi agent:
 *   1. parse 3 file task thật trong /tasks/ và kiểm tra percent/bugs/blockers/agents
 *   2. kiểm tra quy tắc "% lấy từ percent hoặc done/total", không tự tính
 *   3. render ra HTML string (DOM giả) và kiểm tra đúng nội dung + nút Approve/Reject
 *   4. kiểm tra parser danh sách file: JSON (server) và HTML autoindex (python -m http.server)
 *
 * Nếu máy có file `_listing_sample.html` (index thật của python -m http.server) thì test luôn file đó.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const TASKS_DIR = path.join(ROOT, 'tasks');
const mod = require('./agent_team.js');

let pass = 0;
let fail = 0;
const failures = [];

function ok(cond, name, extra) {
  if (cond) {
    pass++;
    console.log('  ok   ' + name);
  } else {
    fail++;
    failures.push(name + (extra ? ' — ' + extra : ''));
    console.log('  FAIL ' + name + (extra ? ' — ' + extra : ''));
  }
}

function eq(actual, expected, name) {
  ok(actual === expected, name, 'nhận ' + JSON.stringify(actual) + ', mong đợi ' + JSON.stringify(expected));
}

function readTask(file) {
  return fs.readFileSync(path.join(TASKS_DIR, file), 'utf8');
}

// Dữ liệu live: agent/Admin đổi file liên tục → test không được hardcode status.
function fileStatus(file) {
  const m = /## Status\r?\n(.+)/.exec(readTask(file));
  return m ? m[1].trim().toLowerCase().replace(/\s+/g, '_') : null;
}

/* ------------------------------------------------------------------ */
console.log('\n[1] Parse 3 file task thật trong /tasks/');
/* ------------------------------------------------------------------ */

const t1 = mod.parseTask(readTask('DILA-TASK-0001.md'), 'DILA-TASK-0001.md');
const t2 = mod.parseTask(readTask('DILA-TASK-0002.md'), 'DILA-TASK-0002.md');
const t3 = mod.parseTask(readTask('DILA-TASK-0003.md'), 'DILA-TASK-0003.md');

eq(t1.id, 'DILA-TASK-0001', '0001 — Task Number lấy từ heading #');
eq(t1.status, 'bug_found', '0001 — Status');
ok(/Hán-Việt/.test(t1.title), '0001 — Title', t1.title);
eq(t1.overall.percent, 60, '0001 — overall percent = 60');
eq(t1.overall.percentSource, 'percent-field', '0001 — percent lấy từ trường percent');
eq(t1.overall.done, 6, '0001 — overall done');
eq(t1.overall.total, 10, '0001 — overall total');
eq(t1.bugs, 3, '0001 — bug count = 2+0+1');
eq(t1.blockers.length, 2, '0001 — blocker count');
eq(t1.checklistDone + '/' + t1.checklistTotal, '3/5', '0001 — acceptance criteria 3/5');
eq(Object.keys(t1.agents).length, 3, '0001 — đọc đủ 3 agent');

eq(t1.agents.planner.id, 'claude_code_planner', '0001 — agent 1 map → claude_code_planner');
eq(t1.agents.developer.id, 'opencode_developer', '0001 — agent 2 map → opencode_developer');
eq(t1.agents.tester.id, 'openrouter_tester', '0001 — agent 3 map → openrouter_tester');
eq(t1.agents.planner.percent, 60, '0001 — Claude Code percent = 60');
eq(t1.agents.developer.percent, 25, '0001 — OpenCode percent = 25');
eq(t1.agents.tester.percent, 40, '0001 — DeepSeek Tester percent = 40');
eq(t1.agents.planner.bugs, 2, '0001 — Claude Code bugs');
eq(t1.agents.developer.bugs, 0, '0001 — OpenCode bugs');

eq(t2.status, 'coding', '0002 — Status');
eq(t2.overall.percent, 40, '0002 — overall percent = 40');
eq(t2.bugs, 1, '0002 — bug count = 0+1+0');
eq(t2.blockers.length, 1, '0002 — blocker count');
eq(t2.checklistDone + '/' + t2.checklistTotal, '2/5', '0002 — acceptance criteria 2/5');

eq(t3.status, fileStatus('DILA-TASK-0003.md'), '0003 — Status đọc đúng file (' + t3.status + ')');
eq(t3.overall.percent, 100, '0003 — overall percent = 100');
eq(t3.overall.done + '/' + t3.overall.total, '10/10', '0003 — done/total');
eq(t3.bugs, 0, '0003 — bug count');
eq(t3.blockers.length, 0, '0003 — "None" không bị tính là blocker');
eq(t3.checklistDone + '/' + t3.checklistTotal, '5/5', '0003 — acceptance criteria 5/5');
ok(/2026-10-25/.test(t3.lastUpdated), '0003 — last updated', t3.lastUpdated);

/* ------------------------------------------------------------------ */
console.log('\n[2] Quy tắc percent: KHÔNG tự sinh progress');
/* ------------------------------------------------------------------ */

const noPercent = mod.parseTask([
  '# DILA-TASK-0099', '', '## Title', 'Không có percent field', '', '## Status', 'coding', '',
  '## Overall Progress', 'done: 3', 'total: 4', '', '## Last Updated', '2026-10-25 10:00'
].join('\n'), 'DILA-TASK-0099.md');
eq(noPercent.overall.percent, 75, 'thiếu percent → fallback done/total = 75');
eq(noPercent.overall.percentSource, 'done/total', 'nguồn percent = done/total');

const noProgress = mod.parseTask('# DILA-TASK-0098\n\n## Title\nTrống\n\n## Status\ncreated\n', 'DILA-TASK-0098.md');
eq(noProgress.overall.percent, null, 'không có percent và done/total → null (không bịa số)');
eq(noProgress.status, 'created', 'trạng thái created đọc được');
eq(noProgress.bugs, 0, 'không có Agents → bugs = 0');
eq(noProgress.blockers.length, 0, 'không có Blockers → 0');

const crlf = mod.parseTask(
  readTask('DILA-TASK-0001.md').replace(/\n/g, '\r\n'), 'DILA-TASK-0001.md'
);
eq(crlf.overall.percent, 60, 'file CRLF vẫn parse đúng');
eq(crlf.status, 'bug_found', 'file CRLF vẫn đọc Status');

const bugText = mod.parseTask([
  '# DILA-TASK-0097', '', '## Status', 'coding', '', '## Agents', '',
  '### DeepSeek Tester', '- Status: testing', '- Progress: 1/10', '- Percent: 10', '- Bugs: none', '',
  '### Claude Code', '- Status: working', '- Progress: 2/10', '- Percent: 20', '- Bugs: 2 lỗi UI'
].join('\n'), 'DILA-TASK-0097.md');
eq(bugText.bugs, 2, 'Bugs: "none" → 0, "2 lỗi UI" → 2');

// Rule DILA Team: "Progress = done/total HOẶC checklist"
const checklistOnly = mod.parseTask([
  '# DILA-TASK-0096', '', '## Title', 'Chỉ có checklist', '', '## Status', 'testing', '',
  '## Acceptance Criteria',
  '- [x] AC 1', '- [x] AC 2', '- [ ] AC 3', '- [ ] AC 4', '',
  '## Last Updated', '2026-10-25 12:00'
].join('\n'), 'DILA-TASK-0096.md');
eq(checklistOnly.overall.percent, 50, 'thiếu percent + done/total → lấy từ checklist 2/4 = 50');
eq(checklistOnly.overall.percentSource, 'checklist', 'nguồn percent = checklist');
eq(checklistOnly.checklistDone + '/' + checklistOnly.checklistTotal, '2/4', 'đếm checklist 2/4');

/* ------------------------------------------------------------------ */
console.log('\n[3] Render HTML (DOM giả)');
/* ------------------------------------------------------------------ */

const els = {};
function fakeEl(id) {
  return {
    id: id || '', innerHTML: '', textContent: '', title: '', disabled: false,
    dataset: {}, style: {}, children: [],
    addEventListener() {}, appendChild(c) { this.children.push(c); }, remove() {}
  };
}
const container = fakeEl('tasksContainer');
els.tasksContainer = container;
['modeBadge', 'totalTasks', 'inProgress', 'awaitingAdmin', 'totalBugs', 'totalBlockers', 'toastStack']
  .forEach(id => { els[id] = fakeEl(id); });

global.document = {
  readyState: 'complete',
  getElementById(id) { return els[id] || (els[id] = fakeEl(id)); },
  addEventListener() {},
  createElement() { return fakeEl('tmp'); },
  body: { appendChild() {} }
};

mod.render([t1, t2, t3]);
const html = container.innerHTML;

ok((html.match(/class="task-card"/g) || []).length === 3, 'render 3 task card');
ok(html.includes('data-task="DILA-TASK-0001"'), 'card có data-task 0001');
ok(html.includes('data-status="bug_found"'), 'card hiển thị status bug_found');
[t1, t2, t3].forEach(x => {
  ok(html.includes('status-' + mod.statusClass(x.status)), 'badge class khớp status ' + x.status + ' (' + x.id + ')');
});
ok(/data-overall-percent[^>]*>60%/.test(html), 'hiển thị overall percent 60%');
ok(/data-overall-percent[^>]*>40%/.test(html), 'hiển thị overall percent 40%');
ok(/data-overall-percent[^>]*>100%/.test(html), 'hiển thị overall percent 100%');
ok(/data-percent-source="percent-field"/.test(html), 'ghi rõ percent lấy từ trường percent:');
ok(html.includes('data-bug-count>3'), 'hiển thị bug count 3 (task 0001)');
ok(html.includes('data-blocker-count>2'), 'hiển thị blocker count 2 (task 0001)');
ok((html.match(/data-agent="claude_code_planner"/g) || []).length === 3, '3 progress bar cho claude_code_planner');
ok((html.match(/data-agent="opencode_developer"/g) || []).length === 3, '3 progress bar cho opencode_developer');
ok((html.match(/data-agent="openrouter_tester"/g) || []).length === 3, '3 progress bar cho openrouter_tester');
ok(html.includes('data-agent="claude_code_planner" data-percent="60"'), 'bar percent Claude = 60');
ok(html.includes('Acceptance criteria'), 'có section Acceptance criteria');
ok((html.match(/type="checkbox"/g) || []).length === 15, 'render đủ 15 checkbox (5+5+5)');
ok(html.includes('Markers') === false, 'không có dữ liệu giả');
ok(html.includes('READY_FOR_ADMIN') === (t3.status === 'done_pending_admin'),
  'READY_FOR_ADMIN hiện đúng khi task đang done_pending_admin (hiện tại: ' + t3.status + ')');

// Nút duyệt phải khớp dữ liệu live (agent/Admin đổi file → không hardcode)
const pendingTasks = [t1, t2, t3].filter(x => x.status === 'done_pending_admin');
const approveIds = html.match(/id="approve-[^"]+"/g) || [];
eq(approveIds.length, pendingTasks.length, 'số nút Approve = số task done_pending_admin (' + pendingTasks.length + ')');
[t1, t2, t3].forEach(x => {
  const has = html.includes('id="approve-' + x.file + '"');
  ok(has === (x.status === 'done_pending_admin'), 'nút Approve của ' + x.id + ' khớp status ' + x.status);
});

// Gating test độc lập dữ liệu live: dùng fixture done_pending_admin
const fixturePending = mod.parseTask([
  '# DILA-TASK-0088', '', '## Title', 'Fixture duyệt', '', '## Status', 'done_pending_admin', '',
  '## Overall Progress', 'done: 5', 'total: 5', 'percent: 100', '',
  '## Acceptance Criteria', '- [x] xong', '', '## Last Updated', '2026-10-25 17:00'
].join('\n'), 'DILA-TASK-0088.md');
const fxHtml = mod.cardHTML(fixturePending);
ok(fxHtml.includes('id="approve-DILA-TASK-0088.md"') && fxHtml.includes('id="reject-DILA-TASK-0088.md"'),
  'fixture done_pending_admin → có cả Approve + Reject');
const t3approved = Object.assign({}, fixturePending, { status: 'approved' });
ok(!mod.cardHTML(t3approved).includes('id="approve-'), 'status approved → ẩn nút Approve/Reject');

ok(els.totalTasks.textContent === '3', 'stats: 3 tasks');
ok(els.awaitingAdmin.textContent === String(pendingTasks.length),
  'stats: ' + pendingTasks.length + ' chờ Admin duyệt (khớp dữ liệu)');
ok(els.totalBugs.textContent === '4', 'stats: tổng bug = 3+1+0');

/* ------------------------------------------------------------------ */
console.log('\n[3b] Workflow 10 state + agent phụ trách (spec DILA Team)');
/* ------------------------------------------------------------------ */

const step1 = mod.stepperHTML('bug_found');
ok(step1.includes('data-stepper="bug_found"'), 'stepper nhận đúng state');
ok(step1.includes('bug_found') && step1.includes('debugging') && step1.includes('retesting'),
  'state bug_found hiển thị nhánh lỗi bug_found → debugging → retesting');
ok(/bug quay về claude_code_planner/.test(step1), 'nhánh lỗi ghi rõ "bug quay về Planner"');
ok(step1.includes('done_pending_admin'), 'stepper vẫn hiển thị đích done_pending_admin');

const stepCoding = mod.stepperHTML('coding');
ok(!stepCoding.includes('debugging'), 'state coding không chen nhánh lỗi vào stepper');
ok(/step current[^>]*>coding/.test(stepCoding), 'state coding được highlight');

const step3 = mod.stepperHTML('done_pending_admin');
ok(step3.includes('approved'), 'done_pending_admin → approved kế tiếp');
ok(/step current[^>]*>done_pending_admin/.test(step3), 'highlight đúng done_pending_admin');

for (const s of ['created', 'planning', 'coding', 'testing', 'bug_found', 'debugging', 'retesting', 'done_pending_admin', 'approved', 'rejected']) {
  ok(mod.stepperHTML(s).includes('data-stepper="' + s + '"'), 'stepper hỗ trợ state ' + s);
}

const cardBug = mod.cardHTML(t1);      // bug_found → Planner phụ trách
const cardCode = mod.cardHTML(t2);     // coding → Developer
const cardDone = mod.cardHTML(t3);     // done_pending_admin → Admin
ok(cardBug.includes('agent-bar-row active" data-agent="claude_code_planner"'), 'bug_found → claude_code_planner đang phụ trách');
ok(cardCode.includes('agent-bar-row active" data-agent="opencode_developer"'), 'coding → opencode_developer đang phụ trách');
ok(!cardDone.includes('agent-bar-row active'), 'done_pending_admin → không agent nào phụ trách (chờ Admin)');
ok(/chờ claude_code_planner \(bug về Planner/.test(mod.cardHTML(Object.assign({}, t1, { status: 'bug_found' }))) ||
   /bug về Planner/.test(cardBug), 'footer bug_found trỏ về Planner');
ok(/claude_code_planner/.test(mod.cardHTML(Object.assign({}, t1, { status: 'rejected' })).split('task-footer')[1] || ''),
  'rejected → Planner re-plan');

/* ------------------------------------------------------------------ */
console.log('\n[4] Parser danh sách file');
/* ------------------------------------------------------------------ */

const jsonList = mod.parseTaskList(JSON.stringify({
  tasks: [{ file: 'DILA-TASK-0002.md' }, { file: 'DILA-TASK-0001.md' }]
}));
eq(jsonList.join(','), 'DILA-TASK-0002.md,DILA-TASK-0001.md', 'parse JSON {"tasks":[...]}');

const htmlList = mod.parseTaskList(
  '<a href="DILA-TASK-0001.md">DILA-TASK-0001.md</a><a href="DILA-TASK-0002.md">x</a>' +
  '<a href="../dashboard/">../</a><a href="notes.txt">notes.txt</a>'
);
eq(htmlList.length, 2, 'parse HTML autoindex → chỉ lấy .md');
ok(htmlList.includes('DILA-TASK-0001.md'), 'autoindex lấy đúng tên file');

const samplePath = path.join(__dirname, '_listing_sample.html');
if (fs.existsSync(samplePath)) {
  const fromReal = mod.parseTaskList(fs.readFileSync(samplePath, 'utf8'));
  eq(fromReal.length, 3, 'index thật của python -m http.server → 3 file .md');
  ok(fromReal.includes('DILA-TASK-0003.md'), 'index thật có DILA-TASK-0003.md');
} else {
  console.log('  skip index thật (không có _listing_sample.html)');
}

/* ------------------------------------------------------------------ */
console.log('\n[5] Bảo đảm không gọi agent / không tự sinh progress');
/* ------------------------------------------------------------------ */

const jsSource = fs.readFileSync(path.join(__dirname, 'agent_team.js'), 'utf8');
ok(!/require\(['"]child_process|execSync|execFileSync|spawnSync/.test(jsSource), 'JS không spawn process');
ok(!/node:child_process|['"]child_process['"]/.test(jsSource), 'JS không import child_process');
ok(!/claude\s+-|opencode\s+run|npx\s+claude/i.test(jsSource), 'JS không gọi CLI agent');
ok(!/localStorage|indexedDB|sessionStorage/.test(jsSource), 'JS không lưu state cục bộ');
const htmlSource = fs.readFileSync(path.join(__dirname, 'agent_team.html'), 'utf8');
ok(!/agents\.json|state\.json/.test(htmlSource + jsSource), 'không tham chiếu state/agents.json');

/* ------------------------------------------------------------------ */
console.log('\n[6] Nguồn THẬT: daoanh/tasks (frontmatter) + daoanh/docs');
/* ------------------------------------------------------------------ */

ok(Object.keys(mod.SOURCES).length === 3, 'có 3 nguồn: dila / real / docs');

// --- task thật: daoanh/tasks/T245-*.md (frontmatter YAML + AC checklist)
const realFile = 'T245-m7-reference-linkage-geo-cross-ref.md';
const realPath = path.join(ROOT, 'daoanh', 'tasks', realFile);
if (fs.existsSync(realPath)) {
  mod.setSourceState('real');
  const realMd = fs.readFileSync(realPath, 'utf8');
  const rt = mod.parseRealTask(realMd, realFile, { size: realMd.length, modified: 1759700000 });

  eq(rt.kind, 'frontmatter', 'task thật → kind=frontmatter');
  eq(rt.id, 'T245', 'đọc id từ frontmatter');
  ok(/M7/.test(rt.title), 'đọc title từ frontmatter (bỏ quotes)', rt.title);
  eq(rt.status, 'pending', 'đọc status từ frontmatter');
  eq(rt.lastUpdated, '2026-10-06', 'last updated = frontmatter updated');
  eq(rt.checklistTotal, 3, 'đếm đúng 3 acceptance criteria của T245');
  eq(rt.checklistDone, 0, '0 AC đã tick');
  eq(rt.overall.percentSource, 'checklist', 'percent lấy từ checklist (rule progress = done/total hoặc checklist)');
  eq(rt.overall.percent, 0, 'percent = 0% (0/3 AC)');
  eq(rt.bugs, 0, 'task thật không có bug field → 0, không bịa');
  eq(rt.sourceDir, '../daoanh/tasks/', 'đường dẫn file trỏ đúng daoanh/tasks/');

  const realCard = mod.cardHTML(rt);
  ok(realCard.includes('data-task="T245"'), 'render card cho task thật');
  ok(realCard.includes('status-pending'), 'badge dùng class status-pending');
  ok(realCard.includes('Task thật của dự án'), 'ghi rõ là task thật, không áp workflow DILA');
  ok(!realCard.includes('id="approve-'), 'task thật không có nút Approve (không ở done_pending_admin)');
  ok(realCard.includes('chưa có dữ liệu'), 'agent chưa có progress thật → "chưa có dữ liệu", không bịa');

  // đếm toàn bộ task thật
  const realFiles = fs.readdirSync(path.join(ROOT, 'daoanh', 'tasks')).filter(f => f.endsWith('.md'));
  ok(realFiles.length > 100, 'daoanh/tasks có nhiều task thật (' + realFiles.length + ' file)', String(realFiles.length));
} else {
  ok(false, 'không tìm thấy ' + realPath);
}

// --- docs thật: daoanh/docs/README.md
const docPath = path.join(ROOT, 'daoanh', 'docs', 'README.md');
if (fs.existsSync(docPath)) {
  mod.setSourceState('docs');
  const docMd = fs.readFileSync(docPath, 'utf8');
  const doc = mod.parseDocCard(docMd, 'README.md', { size: docMd.length, modified: 1759700000 });
  eq(doc.kind, 'doc', 'docs → kind=doc');
  ok(doc.title.length > 0, 'docs có title', doc.title);
  ok(doc.excerpt.length > 0, 'docs có trích đoạn text thật');
  ok(!/^#{1,6}\s/m.test(doc.excerpt), 'trích đoạn đã bỏ ký hiệu heading');
  eq(doc.overall.percent, null, 'docs không có progress (null, không bịa)');
  const docCard = mod.docCardHTML(doc);
  ok(docCard.includes('doc-card'), 'render doc card');
  ok(docCard.includes('href="../daoanh/docs/README.md"'), 'doc card link đúng file thật');
  ok(docCard.includes('Mở file'), 'doc card có nút mở file');
  ok(!docCard.includes('approve-'), 'doc card không có approve/reject');
  mod.setSourceState('dila');
} else {
  ok(false, 'không tìm thấy ' + docPath);
}

/* ------------------------------------------------------------------ */
console.log('\n[7] Editor Admin note (mô tả bug + đổi status trên card)');
/* ------------------------------------------------------------------ */

const withNotes = mod.parseTask([
  '# DILA-TASK-0095', '', '## Title', 'Có note', '', '## Status', 'debugging', '',
  '## Acceptance Criteria', '- [ ] a', '',
  '## Admin Notes', '- [2026-10-25 17:05] Mô tả bug rõ hơn: click lần 2 mất marker',
  '- note không có timestamp', '',
  '## Last Updated', '2026-10-25 17:05'
].join('\n'), 'DILA-TASK-0095.md');

eq(withNotes.notes.length, 2, 'đọc 2 admin note');
eq(withNotes.notes[0].stamp, '2026-10-25 17:05', 'note có timestamp');
ok(/Mô tả bug rõ hơn/.test(withNotes.notes[0].text), 'note giữ nguyên nội dung', withNotes.notes[0].text);
eq(withNotes.notes[1].stamp, '', 'note không timestamp → stamp rỗng');

const noteCard = mod.cardHTML(withNotes);
ok(noteCard.includes('id="note-btn-DILA-TASK-0095.md"'), 'card có nút "Ghi chú Admin"');
ok(noteCard.includes('id="note-editor-DILA-TASK-0095.md"'), 'card có editor inline');
ok(noteCard.includes('Admin notes'), 'hiển thị panel Admin notes');
ok(noteCard.includes('Mô tả bug rõ hơn'), 'hiển thị nội dung note cũ');
ok(noteCard.includes('id="note-input-DILA-TASK-0095.md"'), 'có textarea nhập');
ok(noteCard.includes('id="note-save-DILA-TASK-0095.md"'), 'có nút Lưu ghi chú');
eq(mod.statusClass('debugging'), 'debugging', 'status debugging hợp lệ (chuyển sang Debug)');
ok(mod.stepperHTML('debugging').includes('debugging'), 'stepper hiển thị debugging');
ok(!mod.docCardHTML({ file: 'README.md', title: 'x', excerpt: '', size: 1, lastUpdated: '—' }).includes('note-btn'),
  'doc card không có editor (read-only)');

/* ------------------------------------------------------------------ */
console.log('\n[8] Cate: gom nhóm theo trạng thái (Coding/Testing/Debugging)');
/* ------------------------------------------------------------------ */

eq(mod.CATEGORIES.length, 6, 'có 6 nhóm Cate');
eq(mod.categoryOf('in_progress'), 'coding', 'in_progress → Coding');
eq(mod.categoryOf('coding'), 'coding', 'coding → Coding');
eq(mod.categoryOf('debugging'), 'debugging', 'debugging → Debugging');
eq(mod.categoryOf('bug_found'), 'debugging', 'bug_found → Debugging');
eq(mod.categoryOf('testing'), 'testing', 'testing → Testing');
eq(mod.categoryOf('blocked'), 'blocked', 'blocked → Blocked');
eq(mod.categoryOf('done'), 'done', 'done → Done');
eq(mod.categoryOf('something-weird'), 'other', 'status lạ → nhóm Khác');

const catTasks = [
  mod.parseTask('# DILA-TASK-A\n\n## Title\nA\n\n## Status\ncoding\n', 'A.md'),
  mod.parseTask('# DILA-TASK-B\n\n## Title\nB\n\n## Status\ndebugging\n', 'B.md'),
  mod.parseTask('# DILA-TASK-C\n\n## Title\nC\n\n## Status\ndone\n', 'C.md'),
  mod.parseTask('# DILA-TASK-D\n\n## Title\nD\n\n## Status\nin_progress\n', 'D.md')
];
const catCounts = mod.countByCategory(catTasks);
eq(catCounts.coding, 2, 'đếm nhóm Coding = 2');
eq(catCounts.debugging, 1, 'đếm nhóm Debugging = 1');
eq(catCounts.done, 1, 'đếm nhóm Done = 1');
eq(mod.filterByCategory(catTasks, 'coding').length, 2, 'lọc Coding trả 2 task');
eq(mod.filterByCategory(catTasks, 'all').length, 4, 'nhóm "all" trả toàn bộ');
eq(mod.filterByCategory(catTasks, 'zzz').length, 4, 'nhóm không tồn tại → không lọc');

const grouped = mod.renderGrouped(catTasks, mod.SOURCES.dila);
ok(grouped.includes('class="task-group"'), 'renderGrouped tạo section nhóm');
ok(/group-head.*Coding/.test(grouped), 'nhóm Coding có tiêu đề');
ok(grouped.indexOf('data-category="coding"') < grouped.indexOf('data-category="done"'),
  'nhóm Coding đứng trước Done (ưu tiên việc đang làm)');
eq((grouped.match(/class="task-card"/g) || []).length, 4, 'grouped vẫn render đủ 4 card');

/* ------------------------------------------------------------------ */
console.log('\n[9] Tiêu đề: mã task đứng trước mô tả');
/* ------------------------------------------------------------------ */

eq(mod.titleWithId({ id: 'T22', title: 'Founding Date Pipeline — 59K Places → HOME Integration' }),
  'T22 : Founding Date Pipeline — 59K Places → HOME Integration',
  'T22 → "T22 : <title>"');
eq(mod.titleWithId({ id: 'T22', title: 'T22 — Founding Date Pipeline' }),
  'T22 — Founding Date Pipeline', 'title đã có mã → không lặp lại');
eq(mod.titleWithId({ id: 'T22', title: 'T22' }), 'T22', 'title trùng mã → giữ nguyên');
eq(mod.titleWithId({ id: '', title: 'Không mã' }), 'Không mã', 'không có id → giữ nguyên');

const t22 = mod.parseRealTask([
  '---', 'id: T22', 'title: Founding Date Pipeline — 59K Places → HOME Integration',
  'status: in_progress', 'updated: 2026-10-05', '---', '', '## Acceptance criteria', '- [ ] a'
].join('\n'), 'T22-nlp-fosi-zhi-founding-dates.md');
ok(/<h3 class="task-title">T22 : Founding Date Pipeline/.test(mod.cardHTML(t22)),
  'card render tiêu đề "T22 : …"');
ok(!mod.cardHTML(t22).includes('class="task-id"'), 'header không còn span mã task riêng');

/* ------------------------------------------------------------------ */
console.log('\n[10] Mô tả nhiệm vụ + mục tiêu hoàn thành (done_when)');
/* ------------------------------------------------------------------ */

const fmBlock = mod.parseFrontmatter([
  '---', 'id: T22', 'title: "Founding Date Pipeline"', 'status: in_progress',
  'depends_on: [T21, T22.1]', 'created: 2026-08-20',
  'done_when: >', '  Layer D (regex DILA notes) done ≥200 rows,',
  '  Layer E (Ollama raw_xml) authorized + scheduled,',
  '  Admin review queue UI hoàn tất', '---', '', 'body'
].join('\n'));
eq(fmBlock.id, 'T22', 'frontmatter đọc id');
eq(fmBlock.status, 'in_progress', 'frontmatter đọc status');
eq(fmBlock.depends_on, '[T21, T22.1]', 'frontmatter đọc depends_on');
ok(/Layer D/.test(fmBlock.done_when) && /Admin review queue UI hoàn tất/.test(fmBlock.done_when),
  'done_when block ">" gộp đúng nhiều dòng', fmBlock.done_when);
ok(fmBlock.done_when.indexOf('\n') === -1, 'block ">" thành 1 dòng (folded)');

// Task thật T22: done_when lấy từ frontmatter
const t22Path = path.join(ROOT, 'daoanh', 'tasks', 'T22-nlp-fosi-zhi-founding-dates.md');
if (fs.existsSync(t22Path)) {
  mod.setSourceState('real');
  const t22 = mod.parseRealTask(fs.readFileSync(t22Path, 'utf8'), 'T22-nlp-fosi-zhi-founding-dates.md', {});
  ok(/Founding Date Pipeline/.test(t22.title), 'T22 title đọc được');
  ok(t22.doneWhen.length > 20 && /Layer D/.test(t22.doneWhen),
    'T22 có mục tiêu hoàn thành (done_when)', t22.doneWhen.slice(0, 80));
  ok(t22.description.length > 0, 'T22 có mô tả nhiệm vụ', t22.description.slice(0, 80));
  ok(/T21/.test(t22.dependsOn), 'T22 có phụ thuộc T21', t22.dependsOn);

  const c22 = mod.cardHTML(t22);
  ok(c22.includes('class="panel brief"'), 'card có panel Mô tả & mục tiêu');
  ok(c22.includes('Mô tả nhiệm vụ'), 'card có heading Mô tả nhiệm vụ');
  ok(c22.includes('Mục tiêu hoàn thành (done_when)'), 'card có heading Mục tiêu hoàn thành');
  ok(c22.includes('Layer D'), 'card hiện nội dung done_when');
  ok(c22.includes('⛓ Phụ thuộc'), 'card hiện phụ thuộc');
} else {
  ok(false, 'không tìm thấy ' + t22Path);
}

// Task thật T245: mô tả lấy từ section "## Mục tiêu"
const t245Path = path.join(ROOT, 'daoanh', 'tasks', 'T245-m7-reference-linkage-geo-cross-ref.md');
const t245 = mod.parseRealTask(fs.readFileSync(t245Path, 'utf8'),
  'T245-m7-reference-linkage-geo-cross-ref.md', {});
ok(/Lưu từng liên kết/.test(t245.description), 'T245 mô tả lấy từ section "Mục tiêu"',
  t245.description.slice(0, 80));
mod.setSourceState('dila');

// DILA task không có section mô tả → không bịa panel
ok(!mod.cardHTML(t1).includes('class="panel brief"'), 'DILA task không có mô tả → không hiện panel rỗng');

/* ------------------------------------------------------------------ */
console.log('\n[11] Bù mô tả chi tiết từ docs (tasktodo/Handoff)');
/* ------------------------------------------------------------------ */

const bare = mod.parseRealTask('---\nid: T700\ntitle: "Bare task"\nstatus: pending\n---\n\n',
  'T700-bare.md', {});
eq(bare.description, '', 'task không có section mô tả → rỗng trước khi merge');

mod.mergeTaskContext(bare, {
  id: 'T700',
  description: 'Mô tả tổng hợp từ tasktodo: pipeline founding date 59K places',
  extra: [{ source: 'daoanh/docs/tasktodo.md', kind: 'tasktodo', text: 'Ngữ cảnh chi tiết từ tasktodo' }],
  sources: ['daoanh/docs/tasktodo.md'],
  done_when: 'Layer D ≥200 rows'
});
eq(bare.description, 'Mô tả tổng hợp từ tasktodo: pipeline founding date 59K places',
  'mergeTaskContext điền mô tả còn thiếu');
eq(bare.doneWhen, 'Layer D ≥200 rows', 'mergeTaskContext điền done_when nếu thiếu');
eq(bare.contextSources.join(','), 'daoanh/docs/tasktodo.md', 'ghi nhận nguồn docs');

const bareCard = mod.cardHTML(bare);
ok(bareCard.includes('Ngữ cảnh thêm'), 'card hiện section ngữ cảnh thêm');
ok(bareCard.includes('daoanh/docs/tasktodo.md'), 'card có link tới file nguồn');
ok(bareCard.includes('Mô tả tổng hợp từ tasktodo'), 'card hiện mô tả đã bù');

const keep = mod.parseRealTask('---\nid: T701\ntitle: "Keep"\nstatus: pending\n---\n\n## Mục tiêu\nMô tả gốc của task này\n',
  'T701-keep.md', {});
const beforeDesc = keep.description;
mod.mergeTaskContext(keep, { description: 'KHÔNG ĐƯỢC GHI ĐÈ' });
eq(keep.description, beforeDesc, 'không ghi đè mô tả đã có trong file task');
ok(keep.description.indexOf('KHÔNG ĐƯỢC GHI ĐÈ') === -1, 'mô tả gốc giữ nguyên');

/* ------------------------------------------------------------------ */
console.log('\n────────────────────────────────────────');
console.log(`KẾT QUẢ: ${pass} pass, ${fail} fail`);
if (fail) {
  console.log('Chi tiết fail:');
  failures.forEach(f => console.log('  - ' + f));
  process.exit(1);
}
console.log('TẤT CẢ TEST PASS');
