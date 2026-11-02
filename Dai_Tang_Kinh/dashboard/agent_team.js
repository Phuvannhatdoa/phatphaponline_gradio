/**
 * DILA Team — Agent Dashboard
 *
 * Nguồn dữ liệu DUY NHẤT: các file Markdown trong /tasks/ (mỗi file = 1 task).
 * File này KHÔNG gọi agent nào, KHÔNG tự sinh progress, KHÔNG lưu state.
 * Toàn bộ số liệu (percent, done/total, bugs, blockers) đọc thẳng từ file task.
 *
 * Agents của DILA Team:
 *   claude_code_planner  — QA / Planner / Debugger
 *   opencode_developer   — Developer
 *   openrouter_tester   — Tester (OpenRouter FREE, model khác coder)
 *
 * Workflow:
 *   created → planning → coding → testing → bug_found → debugging → retesting
 *   → done_pending_admin → approved / rejected
 */

(function (global) {
  'use strict';

  var TASKS_DIR = '../tasks/';
  // BUG-052 fix (2026-10-26): dùng /api/dashboard-health (alias additive trong
  // serve.py) thay cho /api/health — path /api/health cũ bị local_gateway.py (8080)
  // cố ý KHÔNG proxy sang serve.py (để không đụng route /api/health riêng của
  // app.py:5000), nên gọi qua cổng 8080 sẽ luôn tới app.py và thiếu field "ok".
  var API_HEALTH = '/api/dashboard-health';
  var API_STATUS = '/api/task-status';
  var API_LIST = '/api/list';
  var API_REAL_STATUS = '/api/real-task-status';
  var API_NOTE = '/api/task-note';
  var REAL_STATUSES = ['pending', 'in_progress', 'debugging', 'blocked', 'done', 'deferred',
    'partial', 'superseded', 'cancelled', 'qa', 'review'];

  /**
   * 3 nguồn dữ liệu THẬT (không có dữ liệu bịa):
   *   dila → tasks/            task mẫu/chuẩn DILA Team (progress + 3 agent)
   *   real → daoanh/tasks/     task thật của dự án (YAML frontmatter + acceptance criteria)
   *   docs → daoanh/docs/      tài liệu Markdown thật (hiển thị title + trích đoạn)
   */
  var SOURCES = {
    dila: {
      id: 'dila', kind: 'task', base: '../tasks/', label: 'DILA tasks',
      note: 'tasks/ — task format DILA Team (Overall Progress + 3 agent)'
    },
    real: {
      id: 'real', kind: 'frontmatter', base: '../daoanh/tasks/', label: 'Task thật',
      note: 'daoanh/tasks/ — task thật của dự án (frontmatter YAML: id, title, status, updated)'
    },
    docs: {
      id: 'docs', kind: 'doc', base: '../daoanh/docs/', label: 'Docs thật',
      note: 'daoanh/docs/ — tài liệu Markdown thật (hiển thị tiêu đề + trích đoạn đầu)'
    }
  };
  var source = 'dila';
  // Task thật: hiển thị hết; docs cắt bớt để nhẹ (183 file, có file >200KB)
  var MAX_CARDS = { dila: 40, real: 2000, docs: 120 };

  /**
   * Nhóm trạng thái (Cate) để Admin click gom task theo giai đoạn làm việc.
   * Lớp HIỂN THỊ thuần: status gốc trong file giữ nguyên, không ghi lại thành nhóm.
   */
  var CATEGORIES = [
    { id: 'coding', label: '💻 Coding', statuses: ['in_progress', 'coding'] },
    { id: 'testing', label: '🧪 Testing', statuses: ['testing', 'retesting', 'qa', 'review'] },
    { id: 'debugging', label: '🐞 Debugging', statuses: ['debugging', 'bug_found'] },
    { id: 'blocked', label: '⛔ Blocked', statuses: ['blocked'] },
    { id: 'pending', label: '📋 Pending', statuses: ['pending', 'created', 'planning', 'deferred'] },
    { id: 'done', label: '✅ Done', statuses: ['done', 'approved', 'partial', 'superseded', 'cancelled'] }
  ];
  var OTHER_CATEGORY = { id: 'other', label: '• Khác', statuses: [] };

  /* ------------------------------------------------------------------ */
  /* Agent mapping                                                       */
  /* ------------------------------------------------------------------ */

  var AGENTS = [
    {
      key: 'planner',
      id: 'claude_code_planner',
      label: 'Claude Code Planner',
      role: 'QA / Planner / Debugger',
      barClass: 'claude',
      aliases: ['claude code planner', 'claude code', 'claude_code_planner', 'planner', 'claude']
    },
    {
      key: 'developer',
      id: 'opencode_developer',
      label: 'OpenCode Developer',
      role: 'Developer',
      barClass: 'opencode',
      aliases: ['opencode developer', 'opencode', 'opencode_developer', 'developer']
    },
    {
      key: 'tester',
      id: 'openrouter_tester',
      label: 'OpenRouter Tester',
      role: 'Tester',
      barClass: 'openrouter',
      aliases: ['openrouter tester', 'openrouter_tester', 'openrouter', 'tester', 'deepseek tester', 'deepseek_tester', 'deepseek', 'deepseek tester (qa)']
    }
  ];

  var WORKFLOW_MAIN = ['created', 'planning', 'coding', 'testing', 'done_pending_admin', 'approved'];
  var WORKFLOW_ALL = [
    'created', 'planning', 'coding', 'testing', 'bug_found',
    'debugging', 'retesting', 'done_pending_admin', 'approved', 'rejected'
  ];
  var BUG_STATES = ['bug_found', 'debugging', 'retesting'];

  /* ------------------------------------------------------------------ */
  /* Markdown parsing (không phụ thuộc thư viện ngoài)                    */
  /* ------------------------------------------------------------------ */

  function splitSections(md) {
    var lines = String(md).replace(/\r\n?/g, '\n').split('\n');
    var sections = [];   // {level, name, title(original), lines: []}
    var current = null;

    for (var i = 0; i < lines.length; i++) {
      var m = lines[i].match(/^(#{1,6})\s+(.*)$/);
      if (m) {
        if (current) sections.push(current);
        current = {
          level: m[1].length,
          name: m[2].trim().toLowerCase().replace(/\s+/g, ' '),
          title: m[2].trim(),
          lines: []
        };
      } else if (current) {
        current.lines.push(lines[i]);
      }
    }
    if (current) sections.push(current);
    return sections;
  }

  function findSection(sections, name) {
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].name === name) return sections[i];
    }
    return null;
  }

  function sectionText(sections, name) {
    var s = findSection(sections, name);
    return s ? s.lines.join('\n').trim() : '';
  }

  function parseOverallProgress(sections) {
    var text = sectionText(sections, 'overall progress');
    var done = /done\s*:\s*(\d+)/i.exec(text);
    var total = /total\s*:\s*(\d+)/i.exec(text);
    var percent = /percent\s*:\s*(-?\d+(?:\.\d+)?)/i.exec(text);
    return {
      done: done ? parseInt(done[1], 10) : 0,
      total: total ? parseInt(total[1], 10) : 0,
      percentText: percent ? percent[1] : null
    };
  }

  function parseNumberFromBugs(value) {
    var v = String(value || '').trim();
    if (!v || /^(-|none|n\/a|không|khong|0)\b/i.test(v)) return 0;
    var m = v.match(/-?\d+/);
    return m ? Math.max(0, parseInt(m[0], 10)) : 1;   // có mô tả nhưng không có số → tính 1 bug
  }

  function matchAgent(nameText) {
    var n = String(nameText || '').trim().toLowerCase();
    for (var i = 0; i < AGENTS.length; i++) {
      var a = AGENTS[i];
      for (var j = 0; j < a.aliases.length; j++) {
        if (n === a.aliases[j]) return a;
      }
    }
    // fuzzy: chứa alias
    for (var k = 0; k < AGENTS.length; k++) {
      var ag = AGENTS[k];
      for (var t = 0; t < ag.aliases.length; t++) {
        if (n.indexOf(ag.aliases[t]) !== -1) return ag;
      }
    }
    return null;
  }

  function parseAgents(sections) {
    var out = {};
    var inAgents = false;
    var active = null;

    for (var i = 0; i < sections.length; i++) {
      var sec = sections[i];
      if (sec.level === 2) {
        inAgents = (sec.name === 'agents');
        active = null;
        continue;
      }
      if (!inAgents || sec.level !== 3) continue;

      var meta = matchAgent(sec.title);
      if (!meta) continue;

      var text = sec.lines.join('\n');
      var status = /-\s*Status\s*:\s*(.+)/i.exec(text);
      var progress = /-\s*Progress\s*:\s*(\d+)\s*\/\s*(\d+)/i.exec(text);
      var percent = /-\s*Percent\s*:\s*(-?\d+(?:\.\d+)?)/i.exec(text);
      var bugs = /-\s*Bugs?\s*:\s*(.+)/i.exec(text);

      var done = progress ? parseInt(progress[1], 10) : 0;
      var total = progress ? parseInt(progress[2], 10) : 0;
      var agentPercent = null;
      if (percent) {
        agentPercent = Math.max(0, Math.min(100, Math.round(parseFloat(percent[1]))));
      } else if (total > 0) {
        agentPercent = Math.round((done / total) * 100);
      }

      out[meta.key] = {
        key: meta.key,
        id: meta.id,
        label: meta.label,
        role: meta.role,
        barClass: meta.barClass,
        status: status ? status[1].trim() : '—',
        done: done,
        total: total,
        progressText: progress ? (done + '/' + total) : '—',
        percent: agentPercent,
        bugs: bugs ? parseNumberFromBugs(bugs[1]) : 0
      };
      active = meta.key;
    }
    return out;
  }

  function parseChecklist(sections) {
    var text = sectionText(sections, 'acceptance criteria');
    var items = [];
    var lines = text.split('\n');
    for (var i = 0; i < lines.length; i++) {
      var m = lines[i].match(/^\s*[-*]\s*\[([ xX])\]\s*(.*)$/);
      if (m) items.push({ checked: m[1].toLowerCase() === 'x', text: m[2].trim() });
    }
    return items;
  }

  function parseBlockers(sections) {
    var text = sectionText(sections, 'blockers');
    var items = [];
    var lines = text.split('\n');
    for (var i = 0; i < lines.length; i++) {
      var m = lines[i].match(/^\s*[-*]\s+(.*)$/);
      if (!m) continue;
      var value = m[1].trim();
      if (!value) continue;
      if (/^(-|none|n\/a|không có|khong co|không)\b/i.test(value)) continue;
      items.push(value);
    }
    return items;
  }

  /**
   * Parse 1 file task → object.
   * Percent: ưu tiên trường "percent:"; nếu thiếu thì mới dùng done/total.
   * (Không suy diễn thêm — đúng yêu cầu "không tự tính %".)
   */
  function parseTask(mdText, fileName) {
    var sections = splitSections(mdText);

    var titleSection = findSection(sections, 'title');
    var title = titleSection ? titleSection.lines.join(' ').trim() : '';

    var statusSection = findSection(sections, 'status');
    var status = statusSection ? statusSection.lines.join(' ').trim().split('\n')[0].trim() : '';
    status = (status || 'unknown').toLowerCase().replace(/\s+/g, '_');

    var headingSection = sections.filter(function (s) { return s.level === 1; })[0];
    var headingId = headingSection ? headingSection.title.trim() : '';

    var overall = parseOverallProgress(sections);
    var agents = parseAgents(sections);

    var checklist = parseChecklist(sections);
    var blockers = parseBlockers(sections);
    var checklistDone = checklist.filter(function (c) { return c.checked; }).length;

    // Rule "Progress = done/total hoặc checklist":
    // thứ tự nguồn: percent field → done/total → checklist. Không có nguồn nào → null (không bịa số).
    var percent = null;
    var percentSource = 'none';
    if (overall.percentText !== null) {
      percent = Math.max(0, Math.min(100, Math.round(parseFloat(overall.percentText))));
      percentSource = 'percent-field';
    } else if (overall.total > 0) {
      percent = Math.round((overall.done / overall.total) * 100);
      percentSource = 'done/total';
    } else if (checklist.length > 0) {
      percent = Math.round((checklistDone / checklist.length) * 100);
      percentSource = 'checklist';
    }

    var totalBugs = 0;
    for (var k in agents) {
      if (Object.prototype.hasOwnProperty.call(agents, k)) totalBugs += agents[k].bugs || 0;
    }

    var lastUpdated = sectionText(sections, 'last updated').split('\n')[0].trim();
    var brief = parseBrief(mdText, sections, {}, false);

    return {
      file: fileName,
      id: headingId || String(fileName).replace(/\.md$/i, ''),
      title: title || '(không có Title)',
      status: status,
      description: brief.description,
      doneWhen: brief.doneWhen,
      dependsOn: '',
      created: '',
      overall: {
        done: overall.done,
        total: overall.total,
        percent: percent,
        percentSource: percentSource
      },
      agents: agents,
      checklist: checklist,
      checklistDone: checklistDone,
      checklistTotal: checklist.length,
      blockers: blockers,
      bugs: totalBugs,
      lastUpdated: lastUpdated || '—',
      notes: parseAdminNotes(sections)
    };
  }

  /* ------------------------------------------------------------------ */
  /* Parsers cho nguồn THẬT: daoanh/tasks (frontmatter) + daoanh/docs     */
  /* ------------------------------------------------------------------ */

  function sectionTextAny(sections, names) {
    for (var i = 0; i < names.length; i++) {
      var s = findSection(sections, names[i]);
      if (s) return s.lines.join('\n').trim();
    }
    return '';
  }

  /** Ghi chú Admin: section '## Admin Notes', bullet có timestamp `- [yyyy-mm-dd hh:mm] text`. */
  function parseAdminNotes(sections) {
    var text = sectionText(sections, 'admin notes');
    if (!text) return [];
    var out = [];
    text.split('\n').forEach(function (line) {
      var m = /^\s*[-*]\s+(.*)$/.exec(line);
      if (!m) return;
      var body = m[1].trim();
      if (!body) return;
      var sm = /^\[([^\]]+)\]\s*(.*)$/.exec(body);
      if (sm) out.push({ stamp: sm[1].trim(), text: sm[2].trim() });
      else out.push({ stamp: '', text: body });
    });
    return out;
  }

  /**
   * YAML frontmatter tối giản: `key: value`, `key: "value"` và block scalar `>` / `|` (nhiều dòng,
   * VD `done_when: >` của task thật). Không cần thư viện YAML.
   */
  function parseFrontmatter(text) {
    var m = /^---\r?\n([\s\S]*?)\r?\n---\s*\r?\n?/.exec(text);
    if (!m) return null;
    var out = {};
    var lines = m[1].split(/\r?\n/);
    var key = null, blockStyle = null, buf = [];

    function flush() {
      if (key && blockStyle) {
        var joined = buf.join('\n').trim();
        out[key] = blockStyle === '>'
          ? joined.replace(/\s*\n\s*/g, ' ').replace(/\s{2,}/g, ' ').trim()
          : joined;
      }
      key = null; blockStyle = null; buf = [];
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var kv = /^([A-Za-z0-9_-]+)\s*:\s*(.*)$/.exec(line);
      if (kv) {
        flush();
        var value = kv[2].trim();
        if (value === '>' || value === '|' || value === '>-' || value === '|-') {
          key = kv[1];
          blockStyle = value.charAt(0);
          continue;
        }
        if ((value.charAt(0) === '"' && value.charAt(value.length - 1) === '"') ||
            (value.charAt(0) === "'" && value.charAt(value.length - 1) === "'")) {
          value = value.slice(1, -1);
        }
        out[kv[1]] = value;
        continue;
      }
      if (key && blockStyle) {
        if (line.trim() === '' && buf.length === 0) continue;
        buf.push(line.trim());
      }
    }
    flush();
    return out;
  }

  var BRIEF_SECTIONS = ['mô tả nhiệm vụ', 'mô tả', 'mục tiêu', 'mục đích', 'tóm tắt', 'bối cảnh',
    'overview', 'summary', 'description', 'context', 'goal', 'objective'];

  function paragraphs(text, max) {
    return String(text || '')
      .split(/\n\s*\n/)
      .map(function (p) { return p.replace(/\s+/g, ' ').trim(); })
      .filter(Boolean)
      .slice(0, max || 3);
  }

  /**
   * "Mô tả nhiệm vụ" + "mục tiêu hoàn thành (done_when)" để Admin biết check gì khi xác nhận TaskDone.
   * - description: section Mô tả/Mục tiêu/…; nếu không có → đoạn văn đầu body (chỉ task thật).
   * - doneWhen: frontmatter `done_when` (kể cả block `>`), fallback section Done-when.
   */
  function parseBrief(text, sections, fm, allowFallback) {
    fm = fm || {};
    var desc = '';
    for (var i = 0; i < BRIEF_SECTIONS.length; i++) {
      var sec = findSection(sections, BRIEF_SECTIONS[i]);
      if (sec) {
        desc = paragraphs(sec.lines.join('\n'), 3).join('\n\n');
        if (desc) break;
      }
    }

    if (!desc && allowFallback) {
      var body = String(text).replace(/^---[\s\S]*?\n---\s*\n?/, '').split('\n');
      var para = [];
      for (var j = 0; j < body.length; j++) {
        var line = body[j].trim();
        if (!line) { if (para.length) break; continue; }
        if (/^#{1,6}\s/.test(line) || /^\|/.test(line) || /^[-*]\s*\[/.test(line)) {
          if (para.length) break;
          continue;
        }
        para.push(line.replace(/^>\s*/, '').replace(/^\*\*|\*\*$/g, ''));
      }
      desc = paragraphs(para.join(' '), 1).join(' ');
    }

    var doneWhen = String(fm.done_when || '').trim();
    if (!doneWhen) {
      doneWhen = sectionTextAny(sections,
        ['done when', 'mục tiêu hoàn thành', 'definition of done', 'done_when'])
        .split('\n').slice(0, 12).join('\n').trim();
    }

    return {
      description: desc,
      doneWhen: doneWhen,
      dependsOn: String(fm.depends_on || '').replace(/^\[|\]$/g, '').trim(),
      created: String(fm.created || '').trim()
    };
  }

  function fmtEpoch(sec) {
    if (!sec) return '—';
    var d = new Date(Number(sec) * 1000);
    if (isNaN(d.getTime())) return '—';
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  /**
   * Task thật của dự án (daoanh/tasks/*.md):
   *   --- id/title/status/updated/priority/module --- + "## Acceptance criteria" checklist.
   * Không có "## Overall Progress" → percent lấy từ checklist (đúng rule progress = done/total hoặc checklist);
   * không có block 3 agent → hiển thị "chưa có dữ liệu", không bịa.
   */
  function parseRealTask(mdText, fileName, meta) {
    var text = String(mdText).replace(/\r\n?/g, '\n');
    var fm = parseFrontmatter(text) || {};
    var sections = splitSections(text);

    var h1 = sections.filter(function (s) { return s.level === 1; })[0];
    var checklist = parseChecklist(sections);
    var blockers = parseBlockers(sections);
    var done = checklist.filter(function (c) { return c.checked; }).length;

    var percent = null;
    var percentSource = 'none';
    if (checklist.length > 0) {
      percent = Math.round((done / checklist.length) * 100);
      percentSource = 'checklist';
    }

    var status = String(fm.status || '').trim().toLowerCase() || 'unknown';

    var brief = parseBrief(text, sections, fm, true);

    return {
      kind: 'frontmatter',
      file: fileName,
      id: String(fm.id || fileName.replace(/\.md$/i, '')).trim(),
      title: String(fm.title || (h1 ? h1.title : fileName.replace(/\.md$/i, ''))).trim(),
      status: status,
      statusRaw: String(fm.status || '').trim(),
      description: brief.description,
      doneWhen: brief.doneWhen,
      dependsOn: brief.dependsOn,
      created: brief.created,
      overall: { done: done, total: checklist.length, percent: percent, percentSource: percentSource },
      agents: {},                       // task thật không ghi progress từng agent
      checklist: checklist,
      checklistDone: done,
      checklistTotal: checklist.length,
      blockers: blockers,
      bugs: 0,
      lastUpdated: String(fm.updated || fm.created || '').trim() || '—',
      module: String(fm.module || '').trim(),
      priority: String(fm.priority || '').trim(),
      notes: parseAdminNotes(sections),
      sourceDir: SOURCES[source] ? SOURCES[source].base : '../daoanh/tasks/'
    };
  }

  /** Tài liệu thật (daoanh/docs/*.md): title + meta + trích đoạn đầu. */
  function parseDocCard(mdText, fileName, meta) {
    var text = String(mdText).replace(/\r\n?/g, '\n');
    var sections = splitSections(text);
    var h1 = sections.filter(function (s) { return s.level === 1; })[0];

    var body = text.replace(/^---[\s\S]*?\n---\s*\n?/, '').split('\n');
    var excerpt = [];
    for (var i = 0; i < body.length && excerpt.length < 7; i++) {
      var line = body[i].replace(/^#{1,6}\s+/, '').replace(/^>\s*/, '').trim();
      if (!line) continue;
      if (line.indexOf('|') === 0) continue;
      excerpt.push(line.length > 220 ? line.slice(0, 220) + '…' : line);
    }

    return {
      kind: 'doc',
      file: fileName,
      id: fileName.replace(/\.md$/i, ''),
      title: h1 ? h1.title : fileName.replace(/\.md$/i, ''),
      status: 'doc',
      overall: { done: 0, total: 0, percent: null, percentSource: 'none' },
      agents: {},
      checklist: [],
      checklistDone: 0,
      checklistTotal: 0,
      blockers: [],
      bugs: 0,
      lastUpdated: fmtEpoch(meta && meta.modified),
      size: (meta && meta.size) || 0,
      excerpt: excerpt.join('\n'),
      sourceDir: SOURCES[source] ? SOURCES[source].base : '../daoanh/docs/'
    };
  }

  function taskNumber(task) {
    var m = String(task.id).match(/(\d+)/);
    return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER;
  }

  /* ------------------------------------------------------------------ */
  /* HTML helpers                                                        */
  /* ------------------------------------------------------------------ */

  function esc(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  var STATUS_CLASSES = WORKFLOW_ALL.concat(
    ['unknown', 'pending', 'in_progress', 'done', 'deferred', 'blocked', 'cancelled', 'qa', 'doc']
  );

  function statusClass(status) {
    var s = String(status || '').toLowerCase();
    return STATUS_CLASSES.indexOf(s) !== -1 ? s : 'unknown';
  }

  function stepperHTML(status) {
    var s = String(status || 'unknown');
    var isBugPath = BUG_STATES.indexOf(s) !== -1;
    var isRejected = s === 'rejected';

    // Đúng workflow spec: created → planning → coding → testing
    //   → bug_found → debugging → retesting   (nhánh lỗi, quay về Planner)
    //   → done_pending_admin → approved / rejected
    var seq = ['created', 'planning', 'coding', 'testing'];
    if (isBugPath) {
      seq = seq.concat(['bug_found', 'debugging', 'retesting']);
    }
    seq = seq.concat(['done_pending_admin', 'approved']);
    if (isRejected) seq = seq.concat(['rejected']);

    var currentIndex = seq.indexOf(s);
    if (currentIndex === -1) currentIndex = 0;

    var parts = [];
    for (var i = 0; i < seq.length; i++) {
      var cls = 'step';
      if (i < currentIndex) cls += ' done';
      else if (i === currentIndex) cls += ' current' + (isBugPath && BUG_STATES.indexOf(seq[i]) !== -1 ? ' bug' : '');
      if (i === seq.length - 1 && seq[i] === 'approved') cls += ' terminal';
      if (i === seq.length - 1 && seq[i] === 'rejected') cls += ' terminal';
      parts.push('<span class="' + cls + '">' + esc(seq[i]) + '</span>');
      if (i < seq.length - 1) parts.push('<span class="step-sep">›</span>');
    }

    if (isBugPath) {
      parts.push('<span class="step-loop">↺ bug quay về claude_code_planner (tạo fix task)</span>');
    }
    if (isRejected) {
      parts.push('<span class="step-loop">↺ rejected → claude_code_planner (re-plan)</span>');
    }
    return '<div class="stepper" data-stepper="' + esc(s) + '">' + parts.join('') + '</div>';
  }

  /** Agent phải hành động tiếp ở state hiện tại (null = Admin hoặc đã đóng). */
  function actorFor(status) {
    switch (status) {
      case 'created':
      case 'planning':
      case 'bug_found':      // rule: bug quay về Planner (nhận Bug Report, tạo fix task)
      case 'debugging':
        return 'planner';
      case 'coding':
        return 'developer';
      case 'testing':
      case 'retesting':
        return 'tester';
      default:
        return null;   // done_pending_admin → Admin duyệt; approved/rejected → kết thúc
    }
  }

  /* ------------------------------------------------------------------ */
  /* Loading & rendering                                                 */
  /* ------------------------------------------------------------------ */

  function parseTaskList(text) {
    // mode 1: JSON {"tasks":[{file: ...}]}
    try {
      var data = JSON.parse(text);
      if (data && Array.isArray(data.tasks)) {
        return data.tasks
          .map(function (t) { return typeof t === 'string' ? t : t && t.file; })
          .filter(Boolean);
      }
      if (Array.isArray(data)) return data.filter(function (f) { return typeof f === 'string'; });
    } catch (e) { /* không phải JSON → thử HTML */ }

    // mode 2: directory listing HTML (python -m http.server)
    var files = [];
    var re = /href="([^"?#]+\.md)"/gi;
    var m;
    var seen = {};
    while ((m = re.exec(text)) !== null) {
      var name = decodeURIComponent(m[1]).split('/').pop();
      if (!seen[name]) { seen[name] = true; files.push(name); }
    }
    return files;
  }

  function fetchJSON(url, options) {
    return fetch(url, options).then(function (res) {
      if (!res.ok) {
        var err = new Error('HTTP ' + res.status + ' — ' + url);
        err.status = res.status;
        throw err;
      }
      return res.json();
    });
  }

  /** Danh sách file .md của nguồn hiện tại: ưu tiên API JSON, fallback autoindex HTML. */
  function listSource() {
    var src = SOURCES[source];
    return fetchJSON(API_LIST + '?source=' + encodeURIComponent(source))
      .then(function (data) {
        var files = (data && data.files) || [];
        return files.map(function (f) { return { file: f.file, size: f.size, modified: f.modified }; });
      })
      .catch(function () {
        // static mode (python -m http.server): đọc autoindex
        return fetch(src.base + '?t=' + Date.now())
          .then(function (res) {
            if (!res.ok) throw new Error('Không đọc được ' + src.base + ' (HTTP ' + res.status + ')');
            return res.text();
          })
          .then(function (text) {
            return parseTaskList(text).map(function (file) { return { file: file }; });
          });
      });
  }

  function fetchOne(fileName) {
    var src = SOURCES[source];
    return fetch(src.base + encodeURIComponent(fileName) + '?t=' + Date.now())
      .then(function (res) { return res.ok ? res.text() : null; });
  }

  function loadSource() {
    var src = SOURCES[source];
    return listSource().then(function (files) {
      files = files.filter(function (f) { return f && f.file && /\.md$/i.test(f.file); });
      var limit = MAX_CARDS[source] || 60;
      var shown = files.slice(0, limit);

      return Promise.all(shown.map(function (entry) {
        return fetchOne(entry.file).then(function (md) {
          if (md === null) return null;
          if (src.kind === 'frontmatter') return parseRealTask(md, entry.file, entry);
          if (src.kind === 'doc') return parseDocCard(md, entry.file, entry);
          return parseTask(md, entry.file);
        }).catch(function (e) {
          console.warn('[DILA] bỏ qua', entry.file, e);
          return null;
        });
      })).then(function (tasks) {
        tasks = tasks.filter(Boolean);
        if (src.kind === 'doc') {
          tasks.sort(function (a, b) { return String(b.lastUpdated).localeCompare(String(a.lastUpdated)); });
        } else if (src.kind === 'frontmatter') {
          tasks.sort(function (a, b) { return taskNumber(b) - taskNumber(a); });
          // Bù mô tả chi tiết cho task thiếu: lấy ngữ cảnh từ docs/*.md (tasktodo, Handoff, docs)
          return loadTaskContexts().then(function (ctx) {
            tasks.forEach(function (t) { mergeTaskContext(t, ctx && ctx[t.file]); });
            return { tasks: tasks, total: files.length, shown: shown.length, source: source };
          });
        } else {
          tasks.sort(function (a, b) {
            var d = taskNumber(a) - taskNumber(b);
            return d !== 0 ? d : String(a.id).localeCompare(String(b.id));
          });
        }
        return { tasks: tasks, total: files.length, shown: shown.length, source: source };
      });
    });
  }

  var contextCache = null;

  /** Gộp ngữ cảnh mô tả (từ docs) vào task: chỉ điền khi task chưa có, luôn gắn nguồn. */
  function mergeTaskContext(task, c) {
    if (!c) return task;
    if (!task.description && c.description) task.description = c.description;
    if (!task.doneWhen && c.done_when) task.doneWhen = c.done_when;
    task.contextExtra = c.extra || [];
    task.contextSources = c.sources || [];
    return task;
  }

  /** Ngữ cảnh mô tả task (server quét docs/*.md, cache 5 phút). Chỉ áp cho task thật. */
  function loadTaskContexts() {
    if (contextCache) return Promise.resolve(contextCache);
    return fetchJSON('/api/task-contexts')
      .then(function (d) {
        contextCache = (d && d.contexts) || {};
        return contextCache;
      })
      .catch(function () { contextCache = {}; return contextCache; });
  }

  var mode = 'static';           // 'api' nếu server có /api/health
  var currentTasks = [];
  var lastMeta = null;
  var busy = {};
  var uiState = { q: '', status: '', category: 'all', view: 'list' };   // search + status + nhóm Cate

  function toast(message, kind) {
    var stack = document.getElementById('toastStack');
    if (!stack) return;
    var el = document.createElement('div');
    el.className = 'toast ' + (kind || 'info');
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(function () { el.remove(); }, 6000);
  }

  function detectMode() {
    return fetchJSON(API_HEALTH)
      .then(function (data) {
        mode = data && data.ok ? 'api' : 'static';
        return mode;
      })
      .catch(function () { mode = 'static'; return mode; });
  }

  function renderModeBadge() {
    var badge = document.getElementById('modeBadge');
    if (!badge) return;
    if (mode === 'api') {
      badge.dataset.mode = 'api';
      badge.textContent = 'admin write: ON';
      badge.title = 'Server tĩnh + endpoint POST /api/task-status (ghi Status)';
    } else {
      badge.dataset.mode = 'static';
      badge.textContent = 'read-only';
      badge.title = 'Không có endpoint ghi file — Approve/Reject sẽ tạo file .md mới để bạn thay thế.';
    }
  }

  function renderStats(tasks, meta) {
    var awaiting = tasks.filter(function (t) { return t.status === 'done_pending_admin'; }).length;
    var done = tasks.filter(function (t) { return t.status === 'approved' || t.status === 'rejected'; }).length;
    var bugs = tasks.reduce(function (s, t) { return s + t.bugs; }, 0);
    var blockers = tasks.reduce(function (s, t) { return s + t.blockers.length; }, 0);

    // Tổng số task = tổng file thật trong nguồn (không phải số card đang hiển thị)
    var total = (meta && meta.total) ? meta.total : tasks.length;

    setText('totalTasks', total);
    setText('inProgress', tasks.length - done);
    setText('awaitingAdmin', awaiting);
    setText('totalBugs', bugs);
    setText('totalBlockers', blockers);

    var note = document.getElementById('statsNote');
    if (note) {
      note.textContent = (meta && meta.total && meta.total !== tasks.length)
        ? '(số liệu chi tiết tính trên ' + tasks.length + '/' + meta.total + ' file đang hiển thị)'
        : '';
    }
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = String(value);
  }

  function overallPercent(task) {
    if (task.overall.percent !== null && task.overall.percent !== undefined) return task.overall.percent;
    return null;
  }

  function agentRowsHTML(task) {
    var activeKey = actorFor(task.status);
    return AGENTS.map(function (meta) {
      var a = task.agents[meta.key];
      var isActive = activeKey === meta.key;
      var rowCls = 'agent-bar-row' + (isActive ? ' active' : '');
      var ownerTag = isActive ? '<span class="agent-owner">▶ phụ trách</span>' : '';

      if (!a) {
        return '<div class="' + rowCls + '" data-agent="' + esc(meta.id) + '">' +
          '<span class="agent-name">' + esc(meta.label) + ownerTag +
          '<span class="agent-role">' + esc(meta.role) + '</span></span>' +
          '<div class="agent-progress-bar"><div class="progress-fill ' + esc(meta.barClass) + '" style="width:0%"></div></div>' +
          '<span class="agent-stats">chưa có dữ liệu</span></div>';
      }
      var pct = (a.percent === null || a.percent === undefined) ? 0 : a.percent;
      return '<div class="' + rowCls + '" data-agent="' + esc(meta.id) + '" data-percent="' + esc(pct) + '">' +
        '<span class="agent-name">' + esc(meta.label) + ownerTag +
        '<span class="agent-role">' + esc(meta.role) + '</span></span>' +
        '<div class="agent-progress-bar"><div class="progress-fill ' + esc(meta.barClass) + '" style="width:' + pct + '%"></div></div>' +
        '<span class="agent-stats" title="' + esc(a.status) + '">' + esc(a.status) + ' · ' + esc(a.progressText) +
        ' · ' + pct + '% · 🐞 ' + a.bugs + '</span></div>';
    }).join('');
  }

  function percentSourceLabel(src) {
    switch (src) {
      case 'percent-field': return 'từ percent:';
      case 'done/total': return 'từ done/total';
      case 'checklist': return 'từ checklist';
      default: return 'chưa có số liệu';
    }
  }

  /** Tiêu đề hiển thị: mã task luôn đứng trước mô tả — "T22 : Founding Date Pipeline …" */
  function titleWithId(task) {
    var id = String(task.id || '').trim();
    var title = String(task.title || '').trim();
    if (!id) return title;
    if (title.toLowerCase() === id.toLowerCase()) return title;
    // title đã bắt đầu bằng mã task (VD "T22 — ...") → không lặp lại
    if (title.toLowerCase().indexOf(id.toLowerCase()) === 0 &&
        /^[\s:—–\-|]/.test(title.slice(id.length))) {
      return title;
    }
    return id + ' : ' + title;
  }

  /** Cờ ưu tiên đặt ngay trước mã task: cấp 1 = 3 cờ (Gấp & Cần), cấp 2 = 2 cờ (Cần, không gấp), cấp 3 = 1 cờ (Không cần gấp). */
  var PRIO_LABEL = { 1: 'Gấp & Cần', 2: 'Cần, không gấp', 3: 'Không cần gấp' };
  /* Ưu tiên toàn dự án (179 task đang mở). Luật: Gấp = critical/p0, hoặc high đang làm và cập nhật từ 15/10,
     hoặc được chốt tay (đợt tích hợp DILA). Cần = high/p1 hoặc đang làm. Còn lại = Không cần gấp. Sửa tay được. */
  var TASK_PRIORITY_MAP = {"BUG-025":2,"T11":3,"T12":3,"T121":2,"T13":3,"T139":2,"T167":2,"T200":2,"T223":1,"T232":2,"T233":2,"T244":2,"T245":2,"T246":3,"T247":3,"T248":2,"T249":2,"T250":3,"T264":3,"T265":2,"T266":2,"T268":3,"T269":2,"T270":2,"T272":2,"T274":2,"T275":2,"T276":2,"T277":2,"T283":1,"T285":1,"T286":3,"T287":1,"T288":1,"T289":2,"T290":2,"T291":2,"T292":2,"T293":2,"T294":2,"T295":2,"T296":3,"T297":3,"T298":2,"T299":2,"T300":3,"T301":3,"T302":3,"T303":3,"T304":3,"T305":2,"T306":2,"T307":2,"T308":2,"T310":2,"T311":2,"T312":2,"T313":3,"T314":3,"T315":3,"T316":3,"T317":3,"T318":3,"T319":3,"T320":3,"T321":3,"T322":3,"T323":3,"T324":3,"T325":3,"T326":3,"T327":3,"T328":3,"T329":3,"T330":3,"T331":3,"T332":3,"T333":3,"T334":3,"T335":3,"T336":3,"T337":3,"T338":3,"T339":3,"T340":3,"T341":3,"T342":3,"T343":3,"T344":3,"T345":3,"T346":3,"T347":3,"T348":3,"T349":3,"T350":3,"T351":3,"T352":3,"T353":3,"T354":2,"T356":2,"T357":1,"T358":2,"T359":2,"T360":2,"T361":3,"T362":3,"T363":3,"T364":3,"T365":3,"T367":3,"T368":3,"T368b":3,"T369":3,"T370":3,"T371":3,"T374":2,"T376":2,"T377":2,"T378":2,"T379":2,"T382":1,"T389":2,"T391":2,"T407":3,"T409":3,"T410":2,"T413":1,"T415":2,"T416":1,"T417":2,"T419":2,"T424":1,"T425":1,"T426":2,"T427":3,"T427-2":3,"T429":3,"T435":3,"T440":2,"T441":2,"T442":2,"T444":2,"T447":1,"T449":2,"T450":3,"T451":2,"T455":1,"T456":2,"T457":1,"T458":3,"T459":3,"T460":3,"T461":2,"T462":2,"T463":2,"T467":2,"T469":2,"T470":2,"T471":2,"T472":2,"T473":1,"T474":3,"T477":1,"T478":1,"T479":2,"T480":2,"T481":1,"T482":1,"T50":2,"T53":2,"T54":3,"T56":3,"T57":3,"T58":3,"T59":3,"T60":3,"T61":3,"T74b":2,"T80":2};
  function prioFlagsHTML(task) {
    var map = TASK_PRIORITY_MAP;
    var level = map[String(task.id || '').trim()];
    if (!level) return '';
    var flags = '';
    for (var i = 0; i < 4 - level; i++) flags += '⚑';
    return '<span class="prio-flags prio-' + level + '" title="Ưu tiên: ' + esc(PRIO_LABEL[level]) + '">' + flags + '</span> ';
  }

  function cardHTML(task) {
    var pct = overallPercent(task);
    var pctWidth = pct === null ? 0 : pct;
    var pctText = pct === null ? '—' : pct + '%';
    var cls = statusClass(task.status);
    var canDecide = task.status === 'done_pending_admin';

    var checklistHTML = task.checklist.length
      ? task.checklist.map(function (c) {
        return '<li class="' + (c.checked ? 'checked' : '') + '">' +
          '<input type="checkbox" disabled ' + (c.checked ? 'checked' : '') + '>' +
          '<label>' + esc(c.text) + '</label></li>';
      }).join('')
      : '<li class="none" style="color:var(--muted);font-style:italic">Chưa có acceptance criteria</li>';

    var blockersHTML = task.blockers.length
      ? task.blockers.map(function (b) { return '<li>' + esc(b) + '</li>'; }).join('')
      : '<li class="none">Không có blocker</li>';

    var actions = '';
    if (canDecide) {
      actions =
        '<span class="footer-note waiting">READY_FOR_ADMIN — cần Admin duyệt</span>' +
        '<button class="btn btn-success btn-sm" type="button" id="approve-' + esc(task.file) + '">Approve</button>' +
        '<button class="btn btn-danger btn-sm" type="button" id="reject-' + esc(task.file) + '">Reject</button>';
    } else {
      actions = '<span class="footer-note">' + esc(task.status) +
        ' · chờ ' + esc(nextActor(task.status)) + '</span>';
    }

    // Task thật: đổi status ngay trên card (ghi frontmatter), cùng page với search/filter
    if (task.kind === 'frontmatter') {
      var opts = REAL_STATUSES.slice();
      if (opts.indexOf(task.status) === -1) opts.unshift(task.status);
      actions =
        '<label class="status-edit">Đổi status' +
        '<select class="status-select" id="status-' + esc(task.file) + '" data-file="' + esc(task.file) + '"' +
        (mode === 'api' ? '' : ' disabled title="cần chạy python dashboard/serve.py để ghi file"') + '>' +
        opts.map(function (s) {
          return '<option value="' + esc(s) + '"' + (s === task.status ? ' selected' : '') + '>' +
            esc(s) + '</option>';
        }).join('') +
        '</select></label>' +
        '<span class="footer-note">ghi frontmatter · cập nhật ' + esc(task.lastUpdated) + '</span>';
    }

    // Ghi chú Admin: panel hiển thị + editor inline (mô tả rõ bug rồi chuyển debugging/done)
    var notes = task.notes || [];
    var notesPanel = notes.length
      ? '<div class="panel notes"><h4>Admin notes <span class="count">' + notes.length + '</span></h4><ul>' +
        notes.map(function (n) {
          return '<li>' + (n.stamp ? '<b>' + esc(n.stamp) + '</b> ' : '') + esc(n.text) + '</li>';
        }).join('') + '</ul></div>'
      : '';

    var noteEditor =
      '<div class="note-editor" id="note-editor-' + esc(task.file) + '" hidden>' +
      '<textarea id="note-input-' + esc(task.file) + '" rows="3" maxlength="4000" ' +
      'placeholder="Mô tả rõ bug / hướng xử lý cho ' + esc(task.id) + '… (lưu vào ## Admin Notes)"></textarea>' +
      '<div class="note-actions">' +
      '<button type="button" class="btn btn-success btn-sm" id="note-save-' + esc(task.file) + '"' +
      (mode === 'api' ? '' : ' disabled title="cần chạy python dashboard/serve.py"') + '>Lưu ghi chú</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" id="note-cancel-' + esc(task.file) + '">Huỷ</button>' +
      '<span class="note-hint">' + (mode === 'api'
        ? 'ghi thêm 1 dòng có timestamp vào section ## Admin Notes (không sửa nội dung cũ)'
        : 'cần serve.py để ghi file') + '</span>' +
      '</div></div>';

    // Mô tả nhiệm vụ + mục tiêu hoàn thành (để Admin biết check gì khi xác nhận TaskDone)
    var extras = (task.contextExtra || []).slice(0, 2);
    var hasBrief = (task.description && task.description.length) ||
      (task.doneWhen && task.doneWhen.length) || extras.length > 0;
    var extraHTML = extras.map(function (e) {
      var lbl = String(e.source || '').split('/').pop();
      return '<div class="brief-extra"><a class="brief-src" href="/' + esc(e.source) +
        '" target="_blank" rel="noopener">' + esc(lbl) + '</a>' +
        '<p>' + esc(String(e.text || '').slice(0, 450)) + (String(e.text || '').length > 450 ? '…' : '') + '</p></div>';
    }).join('');
    var sourcesHTML = (task.contextSources && task.contextSources.length)
      ? '<p class="brief-meta">📚 Nguồn: ' + task.contextSources.map(function (s) {
        return '<a href="/' + esc(s) + '" target="_blank" rel="noopener">' + esc(String(s).split('/').pop()) + '</a>';
      }).join(' · ') + '</p>'
      : '';
    var briefPanel = hasBrief
      ? '<details class="panel brief">' +
        '<summary>📄 Mô tả nhiệm vụ &amp; mục tiêu hoàn thành</summary>' +
        '<div class="brief-body">' +
        (task.description
          ? '<h5>Mô tả nhiệm vụ</h5><p class="brief-desc">' + esc(task.description) + '</p>'
          : '') +
        (task.doneWhen
          ? '<h5>Mục tiêu hoàn thành (done_when)</h5><p class="brief-goal">' + esc(task.doneWhen) + '</p>'
          : '') +
        (extraHTML
          ? '<h5>Ngữ cảnh thêm (từ docs)</h5>' + extraHTML
          : '') +
        sourcesHTML +
        (task.dependsOn || task.created
          ? '<p class="brief-meta">' +
            (task.dependsOn ? '⛓ Phụ thuộc: ' + esc(task.dependsOn) + ' · ' : '') +
            (task.created ? '🗓 Tạo: ' + esc(task.created) : '') + '</p>'
          : '') +
        '</div></details>'
      : '';

    return '' +
      '<article class="task-card" id="card-' + esc(task.file) + '" data-task="' + esc(task.id) + '" data-status="' + esc(task.status) + '">' +
      '<div class="task-header">' +
      '<span class="task-status status-' + esc(cls) + '">' + esc(task.status) + '</span>' +
      '</div>' +
      '<div class="task-body">' +
      '<h3 class="task-title">' + prioFlagsHTML(task) + esc(titleWithId(task)) + '</h3>' +
      '<div class="task-meta">' +
      '<span title="Nguồn: ' + esc(task.overall.percentSource) + '">Tiến độ tổng: <b data-overall-percent data-percent-source="' +
      esc(task.overall.percentSource) + '">' + pctText + '</b>' +
      (task.overall.total ? ' (' + task.overall.done + '/' + task.overall.total + ')' : '') +
      ' <span class="src">' + esc(percentSourceLabel(task.overall.percentSource)) + '</span></span>' +
      '<span>Bugs: <b data-bug-count>' + task.bugs + '</b></span>' +
      '<span>Blockers: <b data-blocker-count>' + task.blockers.length + '</b></span>' +
      '<span>Cập nhật: ' + esc(task.lastUpdated) + '</span>' +
      (task.module ? '<span>📦 ' + esc(task.module) + '</span>' : '') +
      (task.priority ? '<span>⚑ ' + esc(task.priority) + '</span>' : '') +
      '</div>' +
      '<div class="progress-section">' +
      '<div class="progress-header"><span class="progress-label">Overall progress</span>' +
      '<span class="progress-value">' + pctText + '</span></div>' +
      '<div class="progress-bar"><div class="progress-fill overall" style="width:' + pctWidth + '%"></div></div>' +
      '</div>' +
      (task.kind === 'frontmatter' ? realTaskNote(task) : stepperHTML(task.status)) +
      (task.kind === 'frontmatter'
        ? '<div class="agent-empty">Agent: chưa có dữ liệu — task thật của dự án không ghi progress từng agent</div>'
        : '<div class="agent-bars">' + agentRowsHTML(task) + '</div>') +
      '<div class="panel checklist"><h4>Acceptance criteria <span class="count">' +
      task.checklistDone + '/' + task.checklistTotal + '</span></h4><ul>' + checklistHTML + '</ul></div>' +
      '<div class="panel blockers"><h4>Blockers <span class="count">' + task.blockers.length + '</span></h4><ul>' + blockersHTML + '</ul></div>' +
      briefPanel +
      notesPanel +
      noteEditor +
      '</div>' +
      '<div class="task-footer">' +
      '<button type="button" class="btn btn-ghost btn-sm note-btn" id="note-btn-' + esc(task.file) + '">✎ Ghi chú Admin</button>' +
      actions +
      '</div>' +
      '</article>';
  }

  function nextActor(status) {
    switch (status) {
      case 'created': return 'claude_code_planner (viết acceptance criteria)';
      case 'planning': return 'opencode_developer (code theo AC)';
      case 'coding': return 'openrouter_tester (test theo AC)';
      case 'testing': return 'openrouter_tester';
      case 'bug_found': return 'claude_code_planner (bug về Planner → tạo fix task)';
      case 'debugging': return 'claude_code_planner → opencode_developer (fix)';
      case 'retesting': return 'openrouter_tester';
      case 'done_pending_admin': return 'Admin duyệt (Approve / Reject)';
      case 'approved': return '—';
      case 'rejected': return 'claude_code_planner (re-plan)';
      default: return '—';
    }
  }

  function renderSourceNote(meta) {
    var el = document.getElementById('sourceNote');
    if (!el) return;
    var src = SOURCES[source];
    var time = new Date().toLocaleTimeString('vi-VN');
    var text = 'Nguồn: <b>' + esc(src.base.replace(/^\.\.\//, '')) + '</b> · ' + esc(src.note);
    if (src.kind === 'frontmatter') text += ' · <b>mới nhất trước</b>';
    if (meta) {
      text += ' · <b>' + meta.shown + '/' + meta.total + '</b> file (đọc lúc ' + esc(time) + ')';
      if (meta.total > meta.shown) {
        text += ' — <span class="src">còn ' + (meta.total - meta.shown) + ' file chưa hiển thị để dashboard nhẹ</span>';
      }
    }
    el.innerHTML = text;
  }

  /* ------------------------------------------------------------------ */
  /* Gộp A+B: search / lọc status / đổi status — cùng 1 page              */
  /* ------------------------------------------------------------------ */

  function filterTasks(tasks, query, status) {
    var needle = String(query || '').trim().toLowerCase();
    var st = String(status || '').trim().toLowerCase();
    return tasks.filter(function (t) {
      if (st && String(t.status || '').toLowerCase() !== st) return false;
      if (!needle) return true;
      var hay = [t.id, t.title, t.file, t.module, t.priority, t.status]
        .filter(Boolean).join(' ').toLowerCase();
      return hay.indexOf(needle) !== -1;
    });
  }

  function buildStatusFilter(tasks) {
    var sel = document.getElementById('statusFilter');
    if (!sel) return;
    var counts = {};
    tasks.forEach(function (t) {
      var s = String(t.status || 'unknown');
      counts[s] = (counts[s] || 0) + 1;
    });
    var current = uiState.status;
    var html = '<option value="">Tất cả status (' + tasks.length + ')</option>';
    Object.keys(counts).sort().forEach(function (s) {
      html += '<option value="' + esc(s) + '"' + (s === current ? ' selected' : '') + '>' +
        esc(s) + ' (' + counts[s] + ')</option>';
    });
    sel.innerHTML = html;
    if (current && !counts[current]) {
      uiState.status = '';
      sel.value = '';
    }
  }

  var autoTimer = null;
  function setAutoRefresh(on) {
    if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
    if (on) autoTimer = setInterval(function () { if (!document.hidden) refresh(); }, 300000);
  }

  function stampUpdated() {
    var el = document.getElementById('lastUpdated');
    if (el) el.textContent = 'cập nhật ' + new Date().toLocaleTimeString('vi-VN');
  }

  function renderKanban(tasks, board) {
    board.innerHTML = allCategories().map(function (cat) {
      var items = tasks.filter(function (t) { return categoryOf(t.status) === cat.id; });
      return '<div class="kanban-col"><h3>' + esc(cat.label) + ' <span class="kanban-count">' + items.length + '</span></h3>' +
        items.map(kanbanCardHTML).join('') + '</div>';
    }).join('');
  }

  /* Visual LIVE: lấy trạng thái sống từ /api/visual-live (tiến trình OpenCode + status task).
     Mỗi task là một hàng 3 đoạn: OpenCode dev → Tester test → Admin xác nhận. Chỉ đọc. */
  var VISUAL_STAGES = ['OpenCode dev', 'Tester test', 'Admin xác nhận'];
  var VISUAL_POLL_MS = 10000;
  var visualData = null;
  var visualTimer = null;

  function visualStageOf(row) {
    if (row.running) return 0;
    var s = String(row.status || '').toLowerCase();
    if (s === 'coding' || s === 'in_progress') return 0;
    if (s === 'testing') return 1;
    if (s === 'done') return 2;
    return -1;
  }

  function visualSegHTML(index, current, live) {
    var cls = index < current ? 'visual-seg-done' : (index === current ? 'visual-seg-now' : 'visual-seg-todo');
    if (index === current && live) cls += ' visual-seg-live';
    return '<div class="visual-seg visual-seg-s' + index + ' ' + cls + '"><span>' + esc(VISUAL_STAGES[index]) + '</span></div>';
  }

  function visualRowHTML(row) {
    var stage = visualStageOf(row);
    var tag = '';
    var testerState = row.tester_state || 'waiting';
    var testerRunning = stage === 1 && testerState === 'running';
    // Nút DONE chỉ hiện khi tester đã test xong (báo cáo mới hơn báo cáo coder) và không có tiến trình nào đang chạy
    var confirmBtn = (stage === 1 && testerState === 'done' && !row.running && !testerRunning)
      ? '<button type="button" class="btn btn-sm visual-done-btn" data-visual-done="' + esc(row.task_id) + '">DONE</button>'
      : '';
    if (row.running) {
      tag = '<span class="visual-live-tag">● OpenCode đang code' + (row.pid ? ' · pid ' + esc(row.pid) : '') + '</span>';
    } else if (testerRunning) {
      tag = '<span class="visual-live-tag">● Tester đang test</span>';
    } else if (stage === 1 && testerState === 'done') {
      tag = '<span class="visual-live-tag">Đã test xong · báo cáo ' + esc(row.tester_report) + '</span>';
    } else if (stage === 1) {
      tag = '<span class="visual-live-tag visual-live-wait">Chờ tester</span>';
    } else if (stage === 2) {
      tag = '<span class="visual-live-tag">Đã DONE (Admin xác nhận)</span>';
    }
    return '<article class="visual-row">' +
      '<div class="visual-row-head"><span class="kanban-card-id">' + esc(row.task_id) + '</span> ' +
      '<span class="visual-row-title">' + esc(row.title || '') + '</span>' + tag + confirmBtn + '</div>' +
      '<div class="visual-segs">' +
      [0, 1, 2].map(function (i) {
        var live = (i === 0 && !!row.running) || (i === 1 && testerRunning);
        return visualSegHTML(i, stage, live);
      }).join('') +
      '</div></article>';
  }

  function drawVisual() {
    var el = document.getElementById('visualBoard');
    if (!el) return;
    if (!visualData) { el.innerHTML = '<p class="loading">Đang đọc trạng thái OpenCode và tester…</p>'; return; }
    var rows = (visualData.tasks || []).filter(function (r) { return visualStageOf(r) !== -1; });
    var stamp = '<p class="visual-stamp">Cập nhật ' + esc(visualData.generated_at || '') + ' · tự làm mới mỗi 10 giây</p>';
    if (!rows.length) {
      el.innerHTML = stamp + '<p class="empty">Hiện không có task nào đang ở OpenCode hoặc tester.</p>';
      return;
    }
    el.innerHTML = stamp + rows.map(visualRowHTML).join('');
  }

  function confirmVisualDone(taskId, btn) {
    btn.disabled = true;
    fetch('/api/visual-confirm-done', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId })
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok || !res.d.ok) throw new Error(res.d.error || 'không xác nhận được');
        toast(taskId + ' đã xác nhận DONE');
        fetchVisualLive();
      })
      .catch(function (err) { btn.disabled = false; toast('Lỗi: ' + err.message); });
  }

  function fetchVisualLive() {
    fetch('/api/visual-live', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (d) { visualData = d; drawVisual(); })
      .catch(function () { drawVisual(); });
  }

  function startVisualLive() {
    if (visualTimer) return;
    fetchVisualLive();
    visualTimer = setInterval(function () { if (!document.hidden) fetchVisualLive(); }, VISUAL_POLL_MS);
  }

  function stopVisualLive() {
    if (visualTimer) { clearInterval(visualTimer); visualTimer = null; }
  }

  function kanbanCardHTML(task) {
    var pct = overallPercent(task);
    return '<article class="kanban-card status-' + statusClass(task.status) + '">' +
      '<div class="kanban-card-id">' + esc(task.id || '') + '</div>' +
      '<div class="kanban-card-title">' + esc(task.title || task.id || '') + '</div>' +
      '<div class="kanban-card-meta">' + esc(task.status || '') + (pct === null ? '' : ' · ' + pct + '%') + '</div>' +
      '</article>';
  }

  function rerender() {
    render(currentTasks, lastMeta);
  }

  /* ---------------- Cate: gom nhóm theo trạng thái ---------------- */

  function allCategories() { return CATEGORIES.concat([OTHER_CATEGORY]); }

  function categoryOf(status) {
    var s = String(status || '').toLowerCase();
    for (var i = 0; i < CATEGORIES.length; i++) {
      if (CATEGORIES[i].statuses.indexOf(s) !== -1) return CATEGORIES[i].id;
    }
    return OTHER_CATEGORY.id;
  }

  function categoryById(id) {
    if (!id || id === 'all') return null;
    var all = allCategories();
    for (var i = 0; i < all.length; i++) if (all[i].id === id) return all[i];
    return null;
  }

  function countByCategory(tasks) {
    var counts = {};
    allCategories().forEach(function (c) { counts[c.id] = 0; });
    tasks.forEach(function (t) { counts[categoryOf(t.status)]++; });
    return counts;
  }

  function filterByCategory(tasks, categoryId) {
    var cat = categoryById(categoryId);
    if (!cat) return tasks;
    return tasks.filter(function (t) { return categoryOf(t.status) === cat.id; });
  }

  /** Chip Cate: bấm để chỉ xem nhóm đó (VD Coding / Testing / Debugging) */
  function buildCategoryTabs(tasks) {
    var host = document.getElementById('categoryTabs');
    if (!host) return;
    var counts = countByCategory(tasks);
    var active = uiState.category || 'all';
    var html = '<button type="button" class="cat-chip' + (active === 'all' ? ' active' : '') +
      '" data-category="all">Tất cả <span class="n">' + tasks.length + '</span></button>';
    allCategories().forEach(function (cat) {
      var n = counts[cat.id] || 0;
      // vẫn hiện chip kể cả khi 0 task → Admin thấy đủ cấu trúc trạng thái
      html += '<button type="button" class="cat-chip' + (active === cat.id ? ' active' : '') +
        (n ? '' : ' empty') + '" data-category="' + esc(cat.id) + '">' + esc(cat.label) +
        ' <span class="n">' + n + '</span></button>';
    });
    host.innerHTML = html;
  }

  /** Khi xem "Tất cả": gom card thành từng nhóm có tiêu đề trạng thái. */
  function renderGrouped(tasks, src) {
    var cardFn = src.kind === 'doc' ? docCardHTML : cardHTML;
    var out = [];
    allCategories().forEach(function (cat) {
      var items = tasks.filter(function (t) { return categoryOf(t.status) === cat.id; });
      if (!items.length) return;
      out.push('<section class="task-group" data-category="' + esc(cat.id) + '">' +
        '<h3 class="group-head">' + esc(cat.label) +
        ' <span class="count">' + items.length + '</span></h3>' +
        '<div class="group-grid">' + items.map(cardFn).join('') + '</div></section>');
    });
    return out.join('');
  }

  /** Đổi status task thật (ghi frontmatter daoanh/tasks) — cùng page, không mở file. */
  function changeRealStatus(file, newStatus) {
    if (mode !== 'api') {
      toast('Cần chạy python dashboard/serve.py để ghi được file', 'err');
      return Promise.resolve(null);
    }
    return fetchJSON(API_REAL_STATUS, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: file, status: newStatus })
    }).then(function (data) {
      toast(data.file + ': ' + data.old + ' → ' + data.status, 'ok');

      // Admin xác nhận DONE → server chạy build_progress_data.py + gọi Tiểu Thiên báo Done
      var n = data.notify;
      if (n && !n.dry) {
        if (n.queued) {
          toast('⏳ Đang chạy build_progress_data + Tiểu Thiên báo "' + n.title + '" (nền)…', 'info');
          pollNotifyResult();
        } else if (n.ok) {
          toast('🔔 ' + n.title + ' — đã build progress data + Tiểu Thiên đã báo' +
            (n.message ? ' (' + n.message + ')' : ''), 'ok');
        } else {
          var bad = (n.steps || []).filter(function (s) { return !s.ok; })
            .map(function (s) { return s.step + (s.error ? ': ' + s.error : ''); });
          toast('⚠️ status đã là done nhưng bước sau lỗi: ' + (bad.join(', ') || 'không rõ'), 'err');
        }
      }
      return refresh();
    }).catch(function (err) {
      toast('Không đổi được status: ' + (err && err.message ? err.message : err), 'err');
      return refresh();
    });
  }

  /** Hỏi server xem pipeline "build_progress_data + Tiểu Thiên" chạy nền xong chưa. */
  function pollNotifyResult(attempt) {
    attempt = attempt || 0;
    if (mode !== 'api' || typeof fetch !== 'function') return;
    fetchJSON('/api/notify-done/last').then(function (d) {
      var last = d && d.last;
      if (!last) return;
      if (last.state === 'running' && attempt < 60) {
        setTimeout(function () { pollNotifyResult(attempt + 1); }, 3000);
        return;
      }
      var r = last.result || {};
      if (last.state === 'done') {
        toast('🔔 ' + (r.title || last.title || 'Task Done') +
          ' — build progress data OK + Tiểu Thiên đã báo', 'ok');
      } else if (last.state === 'error') {
        var bad = (r.steps || []).filter(function (s) { return !s.ok; })
          .map(function (s) { return s.step + (s.error ? ': ' + s.error : ''); });
        toast('⚠️ Báo Done lỗi: ' + (bad.join(', ') || r.error || 'không rõ'), 'err');
      }
    }).catch(function () { /* server cũ/static mode: bỏ qua */ });
  }

  /** Lưu ghi chú Admin vào file task (append vào ## Admin Notes). */
  function saveNote(file, note) {
    if (mode !== 'api') {
      toast('Cần chạy python dashboard/serve.py để ghi file', 'err');
      return Promise.resolve(false);
    }
    var srcId = SOURCES[source].kind === 'frontmatter' ? 'real' : 'dila';
    return fetchJSON(API_NOTE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: srcId, file: file, note: note })
    }).then(function (data) {
      toast('Đã thêm ghi chú vào ' + data.file + ' @ ' + data.stamp, 'ok');
      return refresh().then(function () { return true; });
    }).catch(function (err) {
      toast('Lưu ghi chú thất bại: ' + (err && err.message ? err.message : err), 'err');
      return false;
    });
  }

  function renderStatsDocs(tasks) {
    setText('totalTasks', tasks.length);
    setText('inProgress', '—');
    setText('awaitingAdmin', '—');
    setText('totalBugs', '—');
    setText('totalBlockers', '—');
    var note = document.getElementById('statsNote');
    if (note) note.textContent = '';
  }

  function docCardHTML(doc) {
    var src = SOURCES[source];
    var href = src.base + encodeURIComponent(doc.file);
    var sizeKb = doc.size ? (doc.size / 1024).toFixed(1) + ' KB' : '—';
    var excerpt = doc.excerpt
      ? doc.excerpt.split('\n').map(function (l) { return '<p>' + esc(l) + '</p>'; }).join('')
      : '<p class="src">(không có nội dung văn bản)</p>';

    return '' +
      '<article class="task-card doc-card" data-doc="' + esc(doc.file) + '">' +
      '<div class="task-header">' +
      '<span class="task-id">' + esc(doc.file) + '</span>' +
      '<span class="task-status status-doc">doc</span>' +
      '</div>' +
      '<div class="task-body">' +
      '<h3 class="task-title">' + esc(doc.title) + '</h3>' +
      '<div class="task-meta">' +
      '<span>📄 ' + esc(sizeKb) + '</span>' +
      '<span>🕒 ' + esc(doc.lastUpdated) + '</span>' +
      '</div>' +
      '<div class="doc-excerpt">' + excerpt + '</div>' +
      '</div>' +
      '<div class="task-footer">' +
      '<span class="footer-note">Tài liệu thật — chỉ đọc</span>' +
      '<a class="btn btn-primary btn-sm" href="' + esc(href) + '" target="_blank" rel="noopener">Mở file ↗</a>' +
      '</div>' +
      '</article>';
  }

  function realTaskNote(task) {
    return '<div class="stepper-note">Task thật của dự án · status gốc: <b>' + esc(task.status) + '</b>' +
      ' · chưa áp workflow DILA (không tự suy diễn state)</div>';
  }

  function render(tasks, meta) {
    currentTasks = tasks;
    lastMeta = meta || null;
    var src = SOURCES[source];
    renderModeBadge();
    renderSourceNote(meta);
    buildStatusFilter(tasks);
    buildCategoryTabs(tasks);
    if (src.kind === 'doc') renderStatsDocs(tasks);
    else renderStats(tasks, meta);

    var visible = filterTasks(tasks, uiState.q, uiState.status);
    visible = filterByCategory(visible, uiState.category);
    var hasFilter = uiState.q || uiState.status || (uiState.category && uiState.category !== 'all');
    if (meta && hasFilter) {
      var note = document.getElementById('statsNote');
      if (note) {
        var cat = categoryById(uiState.category);
        var t = 'đang lọc' + (cat ? ' nhóm ' + cat.label : '') + ': ' + visible.length + '/' + tasks.length + ' card' +
          (meta.total !== tasks.length ? ' (tổng nguồn ' + meta.total + ' file)' : '');
        note.textContent = (note.textContent ? note.textContent + ' · ' : '') + t;
      }
    }

    var container = document.getElementById('tasksContainer');
    var board = document.getElementById('kanbanBoard');
    var visualBoard = document.getElementById('visualBoard');
    if (visualBoard && container) {
      var visualOn = uiState.view === 'visual' && SOURCES[source].kind !== 'doc';
      visualBoard.hidden = !visualOn;
      if (board) board.hidden = true;
      container.hidden = visualOn;
      if (visualOn) { startVisualLive(); drawVisual(); return; }
      stopVisualLive();
    }
    if (board && container) {
      var kanban = uiState.view === 'kanban' && SOURCES[source].kind !== 'doc';
      board.hidden = !kanban;
      container.hidden = kanban;
      if (kanban) { renderKanban(visible, board); return; }
    }
    if (!container) return;

    if (!tasks.length) {
      container.innerHTML = '<p class="empty">Không có file <code>.md</code> nào trong <code>' +
        esc(src.base) + '</code>.</p>';
      return;
    }
    if (!visible.length) {
      container.innerHTML = '<p class="empty">Không có task nào khớp bộ lọc. ' +
        'Bấm <b>Xoá lọc</b> để xem tất cả.</p>';
      return;
    }

    // Xem "Tất cả" + không lọc gì → gom card theo nhóm trạng thái (Cate)
    var grouped = (!uiState.q && !uiState.status &&
      (!uiState.category || uiState.category === 'all'));
    if (grouped) {
      container.innerHTML = renderGrouped(visible, src);
    } else {
      container.innerHTML = '<div class="group-grid">' +
        visible.map(src.kind === 'doc' ? docCardHTML : cardHTML).join('') + '</div>';
    }

    if (src.kind === 'task') {
      visible.forEach(function (task) {
        if (task.status !== 'done_pending_admin') return;
        var approve = document.getElementById('approve-' + task.file);
        var reject = document.getElementById('reject-' + task.file);
        if (approve) approve.addEventListener('click', function () { decide(task, 'approved'); });
        if (reject) reject.addEventListener('click', function () { decide(task, 'rejected'); });
      });
    }

    if (src.kind === 'frontmatter') {
      visible.forEach(function (task) {
        var sel = document.getElementById('status-' + task.file);
        if (!sel) return;
        sel.addEventListener('change', function () {
          changeRealStatus(task.file, sel.value);
        });
      });
    }

    // Editor ghi chú Admin: dùng được cho cả task DILA và task thật
    if (src.kind !== 'doc') {
      visible.forEach(function (task) {
        var btn = document.getElementById('note-btn-' + task.file);
        var ed = document.getElementById('note-editor-' + task.file);
        var ta = document.getElementById('note-input-' + task.file);
        var save = document.getElementById('note-save-' + task.file);
        var cancel = document.getElementById('note-cancel-' + task.file);

        if (btn && ed) btn.addEventListener('click', function () {
          ed.hidden = !ed.hidden;
          if (!ed.hidden && ta && ta.focus) ta.focus();
        });
        if (cancel && ed) cancel.addEventListener('click', function () { ed.hidden = true; });
        if (save) save.addEventListener('click', function () {
          var value = ta ? ta.value : '';
          if (!String(value).trim()) { toast('Ghi chú đang trống', 'err'); return; }
          saveNote(task.file, value).then(function (okFlag) {
            if (okFlag) {
              if (ed) ed.hidden = true;
              if (ta) ta.value = '';
            }
          });
        });
      });
    }
  }

  /* ------------------------------------------------------------------ */
  /* Approve / Reject — cập nhật đúng dòng "## Status" trong file task     */
  /* ------------------------------------------------------------------ */

  function setButtonBusy(file, isBusy) {
    ['approve-', 'reject-'].forEach(function (prefix) {
      var btn = document.getElementById(prefix + file);
      if (btn) btn.disabled = isBusy;
    });
  }

  function replaceStatusLine(md, newStatus) {
    var lines = String(md).replace(/\r\n?/g, '\n').split('\n');
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim().toLowerCase() !== '## status') continue;
      for (var j = i + 1; j < lines.length; j++) {
        if (lines[j].trim() === '') continue;
        if (/^#/.test(lines[j].trim())) break;
        lines[j] = newStatus;
        return lines.join('\n');
      }
    }
    return null;
  }

  function decide(task, status) {
    if (busy[task.file]) return;
    busy[task.file] = true;
    setButtonBusy(task.file, true);

    var actionLabel = status === 'approved' ? 'Approve' : 'Reject';
    var confirmed = global.confirm
      ? global.confirm(actionLabel + ' ' + task.id + '?\n\nFile: tasks/' + task.file + '\nStatus mới: ' + status)
      : true;
    if (!confirmed) {
      busy[task.file] = false;
      setButtonBusy(task.file, false);
      return;
    }

    var useApi = mode === 'api';
    var request = useApi
      ? fetchJSON(API_STATUS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file: task.file, status: status })
      }).then(function (data) {
        toast(task.id + ' → ' + status + ' (đã ghi vào tasks/' + task.file + ')', 'ok');
        return data;
      })
      : Promise.reject(new Error('static-mode'));

    request
      .then(function () {
        return refresh();
      })
      .catch(function (err) {
        if (useApi) {
          toast('Không ghi được file: ' + (err && err.message ? err.message : err), 'err');
          busy[task.file] = false;
          setButtonBusy(task.file, false);
          return;
        }
        // static mode: tải về bản .md đã sửa để Admin tự thay thế
        fetch(TASKS_DIR + encodeURIComponent(task.file) + '?t=' + Date.now())
          .then(function (res) { return res.text(); })
          .then(function (md) {
            var updated = replaceStatusLine(md, status);
            if (!updated) throw new Error('file không có section "## Status"');
            downloadText(task.file, updated);
            toast('Server chưa có quyền ghi: đã tải ' + task.file + ' (status=' + status +
              '). Thay file trong tasks/ rồi bấm Làm mới.', 'info');
          })
          .catch(function (e2) {
            toast('Approve/Reject thất bại: ' + (e2 && e2.message ? e2.message : e2), 'err');
          })
          .then(function () {
            busy[task.file] = false;
            setButtonBusy(task.file, false);
          });
      });
  }

  function downloadText(fileName, text) {
    var blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }

  /* ------------------------------------------------------------------ */
  /* Boot                                                                */
  /* ------------------------------------------------------------------ */

  function isFileProtocol() {
    return typeof global.location !== 'undefined' && global.location.protocol === 'file:';
  }

  function showFatal(title, lines) {
    var container = document.getElementById('tasksContainer');
    if (!container) return;
    container.innerHTML = '<div class="fatal">' +
      '<h3>⚠️ ' + esc(title) + '</h3>' +
      lines.map(function (l) { return '<p>' + l + '</p>'; }).join('') +
      '</div>';
  }

  function refresh() {
    return detectMode()
      .then(loadSource)
      .then(function (result) { render(result.tasks, result); stampUpdated(); return result.tasks; })
      .catch(function (err) {
        console.error('[DILA]', err);
        showFatal('Không đọc được nguồn dữ liệu: ' + SOURCES[source].base, [
          'Chi tiết: <code>' + esc(err && err.message ? err.message : String(err)) + '</code>',
          '<b>Cách đúng:</b> chạy server từ thư mục <code>Dai_Tang_Kinh</code>:',
          '<code>python dashboard/serve.py --port 8090</code>',
          '→ <b>http://127.0.0.1:8090/dashboard/agent_team.html</b>',
          'Nếu dùng <code>python -m http.server</code>: phải chạy ở <code>Dai_Tang_Kinh</code> (nơi có cả <code>dashboard/</code> và <code>tasks/</code>), không chạy trong <code>dashboard/</code>.'
        ]);
        renderStats([]);
      });
  }

  function setSource(next) {
    if (!SOURCES[next]) return;
    source = next;
    // giữ nguồn trên URL để F5 vẫn đúng
    try {
      var url = new URL(global.location.href);
      url.searchParams.set('source', source);
      global.history.replaceState(null, '', url);
    } catch (e) { /* môi trường không có URL */ }

    updateSourceTabs();
    return refresh();
  }

  function updateSourceTabs() {
    var tabs = document.querySelectorAll('#sourceTabs [data-source]');
    for (var i = 0; i < tabs.length; i++) {
      var el = tabs[i];
      if (el.getAttribute('data-source') === source) el.classList.add('active');
      else el.classList.remove('active');
      el.setAttribute('aria-selected', el.getAttribute('data-source') === source ? 'true' : 'false');
    }
  }

  function boot() {
    if (isFileProtocol()) {
      // Mở bằng double-click: browser chặn fetch file:// → phải chỉ rõ cách chạy server
      showFatal('Đang mở file trực tiếp (file://) nên dashboard không đọc được /tasks/', [
        'Trình duyệt chặn <code>fetch()</code> với <code>file://</code> (CORS), nên mọi số liệu sẽ là 0.',
        '<b>Cách đúng:</b> chạy server rồi mở bằng http:',
        '<code>python dashboard/serve.py --port 8090</code>',
        '→ <b>http://127.0.0.1:8090/dashboard/agent_team.html</b>',
        'Hoặc chỉ-đọc: <code>python -m http.server 8090</code> (chạy ở thư mục <code>Dai_Tang_Kinh</code>) rồi mở cùng URL.'
      ]);
      renderStats([]);
      return;
    }

    if (typeof global.location !== 'undefined' && global.location.search) {
      var m = /[?&]source=([a-z]+)/i.exec(global.location.search);
      if (m && SOURCES[m[1].toLowerCase()]) source = m[1].toLowerCase();
    }

    var btn = document.getElementById('refreshBtn');
    if (btn) btn.addEventListener('click', function () { refresh(); });

    var vList = document.getElementById('viewList'), vKanban = document.getElementById('viewKanban');
    var vVisual = document.getElementById('viewVisual');
    function setView(v) {
      uiState.view = v;
      if (vList) vList.classList.toggle('btn-primary', v === 'list');
      if (vKanban) vKanban.classList.toggle('btn-primary', v === 'kanban');
      if (vVisual) vVisual.classList.toggle('btn-primary', v === 'visual');
      rerender();
    }
    if (vList) vList.addEventListener('click', function () { setView('list'); });
    if (vKanban) vKanban.addEventListener('click', function () { setView('kanban'); });
    if (vVisual) vVisual.addEventListener('click', function () { setView('visual'); });
    var visualBoardEl = document.getElementById('visualBoard');
    if (visualBoardEl) visualBoardEl.addEventListener('click', function (e) {
      var btn = e.target.closest('button[data-visual-done]');
      if (btn) confirmVisualDone(btn.dataset.visualDone, btn);
    });

    var auto = document.getElementById('autoRefresh');
    if (auto) auto.addEventListener('change', function () { setAutoRefresh(auto.checked); });
    setAutoRefresh(!auto || auto.checked);

    // A+B trên cùng 1 page: search + lọc status, render lại tại chỗ (không gọi server)
    var search = document.getElementById('searchInput');
    if (search) search.addEventListener('input', function () { uiState.q = search.value; rerender(); });

    var filter = document.getElementById('statusFilter');
    if (filter) filter.addEventListener('change', function () { uiState.status = filter.value; rerender(); });

    var clear = document.getElementById('clearFilter');
    if (clear) clear.addEventListener('click', function () {
      uiState.q = '';
      uiState.status = '';
      uiState.category = 'all';
      if (search) search.value = '';
      if (filter) filter.value = '';
      rerender();
    });

    // Chip Cate: click để gom về 1 trạng thái (Coding / Testing / Debugging…)
    var catHost = document.getElementById('categoryTabs');
    if (catHost && catHost.addEventListener) {
      catHost.addEventListener('click', function (ev) {
        var target = ev && ev.target;
        while (target && target !== catHost &&
               !(target.getAttribute && target.getAttribute('data-category'))) {
          target = target.parentNode;
        }
        if (!target || target === catHost) return;
        uiState.category = target.getAttribute('data-category') || 'all';
        rerender();
      });
    }

    var tabs = document.querySelectorAll('#sourceTabs [data-source]');
    for (var i = 0; i < tabs.length; i++) {
      (function (el) {
        el.addEventListener('click', function () { setSource(el.getAttribute('data-source')); });
      })(tabs[i]);
    }
    updateSourceTabs();
    return refresh();
  }

  if (typeof document !== 'undefined' && document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else if (typeof document !== 'undefined') {
    boot();
  }

  // xuất cho test/CLI (không dùng trong browser)
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      parseTask: parseTask,
      parseRealTask: parseRealTask,
      parseDocCard: parseDocCard,
      parseFrontmatter: parseFrontmatter,
      parseBrief: parseBrief,
      parseTaskList: parseTaskList,
      splitSections: splitSections,
      stepperHTML: stepperHTML,
      cardHTML: cardHTML,
      docCardHTML: docCardHTML,
      render: render,
      statusClass: statusClass,
      nextActor: nextActor,
      AGENTS: AGENTS,
      WORKFLOW_MAIN: WORKFLOW_MAIN,
      SOURCES: SOURCES,
      setSourceState: function (s) { if (SOURCES[s]) source = s; },
      getSourceState: function () { return source; },
      setSource: setSource,
      boot: boot,
      refresh: refresh,
      updateSourceTabs: updateSourceTabs,
      filterTasks: filterTasks,
      changeRealStatus: changeRealStatus,
      saveNote: saveNote,
      loadTaskContexts: loadTaskContexts,
      mergeTaskContext: mergeTaskContext,
      pollNotifyResult: pollNotifyResult,
      parseAdminNotes: parseAdminNotes,
      buildStatusFilter: buildStatusFilter,
      buildCategoryTabs: buildCategoryTabs,
      categoryOf: categoryOf,
      countByCategory: countByCategory,
      filterByCategory: filterByCategory,
      renderGrouped: renderGrouped,
      titleWithId: titleWithId,
      CATEGORIES: CATEGORIES,
      setUiState: function (q, status, category) {
        uiState.q = q || '';
        uiState.status = status || '';
        uiState.category = category || 'all';
      },
      getUiState: function () { return uiState; }
    };
  }
})(typeof window !== 'undefined' ? window : globalThis);
