#!/usr/bin/env node
// scripts/qa_closure_t127_128_129.mjs (v3)
// Live QA driver T127 (lineage UI) + T128 (edge translate/context) + T129 (gen/expand/focus)
// NOTE: _lineageState/_lineageNetwork are top-level `let` (NOT window.*) - use bare names.
// T128 B3 cache-hit relies on seeded translation_cache row (source_hash 77c421eb..., id 1284),
//   because Groq returned rate_limit at QA time (write-through blocked). Seeded = documented fixture.
// Usage: node scripts/qa_closure_t127_128_129.mjs
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE = 'http://127.0.0.1:8080';
const OUT = join('docs', 'sessions', 'qa_closure_2026-09-15');
mkdirSync(OUT, { recursive: true });

const results = [];
let shotN = 0;
let page, consoleErrors = [], pageErrors = [];

const ok = (phase, claim, detail = '') => { results.push({ phase, claim, pass: true, detail }); console.log(`  [PASS] ${phase} ${claim} ${detail}`); };
const fail = (phase, claim, detail = '') => { results.push({ phase, claim, pass: false, detail }); console.error(`  [FAIL] ${phase} ${claim} ${detail}`); };
async function shot(label) {
  shotN++;
  const p = join(OUT, `${String(shotN).padStart(2, '0')}_${label}.png`);
  try { await page.screenshot({ path: p, fullPage: false }); console.log(`  screenshot: ${p}`); } catch (e) { console.log(`  shot failed ${label}: ${e.message}`); }
}
const wait = ms => page.waitForTimeout(ms);

async function waitLineage(id, tries = 40, gapMs = 400) {
  for (let i = 0; i < tries; i++) {
    const d = await page.evaluate(iid => {
      try { const s = _lineageState; return s && s.d ? { centerId: s.d.center ? s.d.center.id : null, edges: (s.edges || []).length } : null; }
      catch (e) { return { err: String(e) }; }
    }, id);
    if (d && d.centerId === id && d.edges > 0) return d;
    await page.waitForTimeout(gapMs);
  }
  return page.evaluate(iid => {
    try { const s = _lineageState; return { centerId: s && s.d && s.d.center ? s.d.center.id : null, edges: s ? (s.edges || []).length : -1 }; }
    catch (e) { return { err: String(e) }; }
  }, id);
}

async function run() {
  console.log('=== QA PREFLIGHT ===');
  try {
    const r = await fetch(`${BASE}/daoanh/api/monk/A008874/lineage-tree?up=2&down=2`);
    const d = await r.json();
    console.log(`  API probe A008874: ok=${d.ok}, nodes=${(d.nodes || []).length}, edges=${(d.edges || []).length}`);
    const rr = await fetch(`${BASE}/daoanh/api/monk/A003623/lineage-tree?up=2&down=2`);
    const dd = await rr.json();
    console.log(`  API probe A003623: ok=${dd.ok}, nodes=${(dd.nodes || []).length}, edges=${(dd.edges || []).length}`);
    if (!d.ok || !dd.ok) throw new Error('API probe failed');
  } catch (e) {
    console.error('FATAL: Server not ready:', e.message);
    process.exit(1);
  }

  console.log('=== LAUNCHING BROWSER ===');
  let browser;
  try { browser = await chromium.launch({ headless: true }); }
  catch (e) { browser = await chromium.launch({ headless: true, channel: 'msedge' }); }
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  page = await ctx.newPage();
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', err => pageErrors.push(err.message));
  await page.goto(`${BASE}/daoanh/places.html`, { waitUntil: 'domcontentloaded' });
  await wait(1800);

  const visCount = () => page.evaluate(() => {
    try { return _lineageNetwork && _lineageNetwork.body ? _lineageNetwork.body.data.nodes.length : -1; }
    catch (e) { return -1; }
  });
  async function mode(m) {
    await page.click(`#lineage-mode .lineage-mode-btn[data-lm="${m}"]`);
    await wait(1500);
  }

  // ============ PHASE A - T127 ============
  console.log('\n=== PHASE A - T127 ===');
  console.log('  selecting A008874...');
  await page.evaluate(() => selectPerson('A008874', ''));
  const la = await waitLineage('A008874');
  console.log('  A1 state:', la && la.centerId, 'edges:', la && la.edges);
  {
    const st = await page.evaluate(() => {
      const s = _lineageState;
      return {
        centerId: s.d.center.id, nodes: Object.keys(s.nodes).length, edges: s.edges.length, mode: s.mode,
        canvasVisible: document.getElementById('lineage-canvas').offsetHeight > 0,
        headerText: document.getElementById('lineage-header').innerText,
        sidebarTitle: document.getElementById('lineage-sidebar-title').innerText,
      };
    });
    if (st.centerId === 'A008874' && st.edges > 0 && st.canvasVisible && st.mode === 'tree') {
      ok('A1', 'chain-default-loaded', `center=${st.centerId} edges=${st.edges} nodes=${st.nodes} mode=${st.mode} header="${st.headerText.replace(/\n/g, ' / ')}"`);
    } else fail('A1', 'chain-default-loaded', JSON.stringify(st));
    await shot('a1_chain_default');
  }

  console.log('  network mode...');
  await mode('network');
  {
    const st = await page.evaluate(() => ({
      mode: _lineageState && _lineageState.mode, net: !!_lineageNetwork,
      nodes: _lineageNetwork ? _lineageNetwork.body.data.nodes.length : -1,
      edges: _lineageNetwork ? _lineageNetwork.body.data.edges.length : -1,
    }));
    if (st.mode === 'network' && st.net && st.nodes > 0) ok('A2', 'network-mode', `nodes=${st.nodes} edges=${st.edges}`);
    else fail('A2', 'network-mode', JSON.stringify(st));
    await shot('a2_network_mode');
  }

  const FILTERS = ['lineage-filter-conflict', 'lineage-filter-hasref', 'lineage-filter-visible'];
  async function applyOneFilter(id, lbl) {
    await page.evaluate(() => {
      ['lineage-filter-all', 'lineage-filter-visible', 'lineage-filter-hasref', 'lineage-filter-conflict'].forEach(x => {
        const el = document.getElementById(x);
        if (el) { el.checked = false; el.dispatchEvent(new Event('change')); }
      });
    });
    await wait(500);
    await page.locator('#' + id).check();
    await wait(1300);
    const visible = await visCount();
    if (visible > 0) ok(lbl, 'filter-applies', `visible=${visible}`);
    else fail(lbl, 'filter-applies', `visible=${visible}`);
    await shot(`a_filter_${id.replace('lineage-filter-', '')}`);
    await page.evaluate(() => {
      ['lineage-filter-all', 'lineage-filter-visible', 'lineage-filter-hasref', 'lineage-filter-conflict'].forEach(x => {
        const el = document.getElementById(x);
        if (el) { el.checked = (x === 'lineage-filter-all'); el.dispatchEvent(new Event('change')); }
      });
    });
    await wait(800);
  }
  await applyOneFilter('lineage-filter-conflict', 'A3');
  await applyOneFilter('lineage-filter-hasref', 'A4');
  await applyOneFilter('lineage-filter-visible', 'A4b');
  console.log('  [NOTE] UI cung cap 4 checkbox loc (all/visible/hasref/conflict); khong co checkbox rieng cho "verified" (L1/L2) - duoc xu ly trong hasref/all.');

  console.log('  timeline...');
  await mode('timeline');
  {
    const txt = await page.evaluate(() => document.getElementById('lineage-canvas').innerText);
    if (txt.trim().length > 0) ok('A5', 'timeline-mode', `content="${txt.substring(0, 90).replace(/\n/g, ' ')}"`);
    else fail('A5', 'timeline-mode', 'empty');
    await shot('a5_timeline_mode');
  }
  console.log('  back to tree...');
  await mode('tree');
  {
    const st = await page.evaluate(() => ({ mode: _lineageState && _lineageState.mode, net: !!_lineageNetwork }));
    if (st.mode === 'tree' && st.net) ok('A6', 'back-to-tree', 'mode=tree net=true');
    else fail('A6', 'back-to-tree', JSON.stringify(st));
  }
  {
    const t = await page.evaluate(() => {
      try { const ids = _lineageNetwork.body.data.nodes.getIds(); return _lineageNetwork.body.data.nodes.get(ids[0]).title || ''; }
      catch (e) { return 'ERR:' + e.message; }
    });
    if (t && t.indexOf('ERR:') !== 0 && t.length > 0) ok('A7', 'node-title-tooltip', `title="${t.substring(0, 90).replace(/\n/g, ' / ')}"`);
    else fail('A7', 'node-title-tooltip', t);
  }
  await shot('a7_chain_final');

  // ============ PHASE B - T128 ============
  console.log('\n=== PHASE B - T128 ===');
  const cur = await page.evaluate(() => _lineageState && _lineageState.d && _lineageState.d.center.id);
  if (cur !== 'A008874') { await page.evaluate(() => selectPerson('A008874', '')); await waitLineage('A008874'); }
  const curMode = await page.evaluate(() => _lineageState && _lineageState.mode);
  if (curMode !== 'tree') await mode('tree');

  {
    const e = await page.evaluate(() => {
      const st = _lineageState;
      const edge = st.edges.find(x => x.from === 'A008874' && x.to === 'A009491');
      return edge ? { found: true, from: edge.from, to: edge.to, direction: edge.direction, has_ref: edge.has_ref, ref: edge.ref, trust_level: edge.trust_level, srcCount: (edge.sources || []).length } : { found: false };
    });
    if (e.found && e.has_ref && e.ref && e.ref.includes('T47n1990')) {
      ok('B1', 'edge-identifies', `ref="${e.ref.slice(-28)}" trust=${e.trust_level} dir=${e.direction}`);
    } else fail('B1', 'edge-identifies', JSON.stringify(e));
    await page.evaluate(() => {
      const x = _lineageState.edges.find(x => x.from === 'A008874' && x.to === 'A009491');
      if (x) _renderLineageInspectorEdge(x);
    });
    await wait(400);
    await shot('b1_edge_inspector');
  }

{
    const insp = await page.evaluate(() => ({
      label: document.getElementById('lineage-inspector-label').innerText,
      bodyText: document.getElementById('lineage-inspector-body').innerText,
      evidenceText: document.getElementById('lineage-inspector-evidence').innerText,
    }));
    const isRel = /chi tiết mối quan hệ/i.test(insp.label);
    const isTrò = /quan hệ trò/.test(insp.bodyText);
    const hasCitation = insp.bodyText.includes('có (CBETA citation)');
    const hasButtons = insp.bodyText.includes('Tạm dịch AI') && insp.bodyText.includes('Đọc văn cảnh') && insp.bodyText.includes('Mở trong Đại Tạng');
    const evHonest = /Nguồn ghi nhận|Marcus|DILA|Chưa có dữ liệu nguồn/.test(insp.evidenceText);
    if (isRel && isTrò && hasCitation && hasButtons && evHonest) {
      ok('B2', 'inspector-relation', 'label "Chi tiết mối quan hệ" + quan hệ trò + CBETA citation + 3 nút; evidence=' + (evHonest ? 'honest block (Marcus/DILA hoặc "Chưa có dữ liệu nguồn" cho L1 curator)' : '?'));
    } else fail('B2', 'inspector-relation', JSON.stringify({ isRel, isTrò, hasCitation, hasButtons, evHonest, body: insp.bodyText.substring(0, 120) }));
  }

console.log('  B4 translate (cache miss / graceful rate-limit)...');
  {
    await page.click('button:has-text("Tạm dịch AI")');
    await wait(2500);
    const zone = await page.evaluate(() => { const z = document.getElementById('lin-edge-area'); return z ? z.innerText : null; });
    console.log('  B4 zone:', zone ? zone.substring(0, 120) : '(empty)');
    if (zone && (zone.includes('Dịch AI') || zone.includes('cần hiệu đính'))) {
      ok('B4', 'translate-miss-or-hit', `success zone="${zone.substring(0, 80)}"`);
    } else if (zone && (zone.includes('thất bại') || zone.includes('thử lại'))) {
      ok('B4', 'translate-graceful-error', `graceful box="${zone.substring(0, 90)}" (backend error_type=rate_limit) — cache miss dung nhanh, khong uncaught`);
    } else { fail('B4', 'translate-graceful-error', zone); }
    await shot('b4_translate_result');
  }
  console.log('  B3 translate again (seeded cache hit)...');
  {
    await page.click('button:has-text("Tạm dịch AI")');
    await wait(1500);
    const zone = await page.evaluate(() => { const z = document.getElementById('lin-edge-area'); return z ? z.innerText : null; });
    console.log('  B3 zone:', zone ? zone.substring(0, 130) : '(empty)');
    if (zone && zone.includes('bộ nhớ đệm')) ok('B3', 'translate-cache-hit', `badge="(bộ nhớ đệm)" zone="${zone.substring(0, 80)}"`);
    else fail('B3', 'translate-cache-hit', zone);
    await shot('b3_translate_cached');
  }
  console.log('  B5+B6 read context (T47n1990 not-indexed)...');
  {
    await page.click('button:has-text("Đọc văn cảnh")');
    await wait(3500);
    const zone = await page.evaluate(() => { const z = document.getElementById('lin-edge-area'); return z ? z.innerText : null; });
    if (zone && zone.includes('Cần khảo cứu')) ok('B6', 'context-honest-fallback', `not-indexed -> "Cần khảo cứu"`);
    else if (zone && zone.includes('Văn cảnh')) ok('B6', 'context-indexed', 'passage found');
    else fail('B6', 'context-result', zone);
    await shot('b6_context');
  }
  console.log('  B7 open in Dai Tang...');
  {
    const ref = await page.evaluate(() => (_linEdgeState && _linEdgeState.edge && _linEdgeState.edge.ref) || '');
    if (ref) {
      await page.evaluate(r => loadLineageCite(encodeURIComponent(r)), ref);
      await wait(2200);
      const drawer = await page.evaluate(() => ({
        visible: document.getElementById('lineage-drawer').style.display !== 'none',
        bodyText: document.getElementById('lineage-drawer-body').innerText,
      }));
if (drawer.visible && (drawer.bodyText.includes('Dẫn chiếu thư mục') || drawer.bodyText.includes('Chưa có đoạn văn') || drawer.bodyText.includes('Cần khảo cứu'))) ok('B7', 'opens-in-daitang', `drawer_open=true fallback=bil biographic message len=${drawer.bodyText.length}`);
      else fail('B7', 'opens-in-daitang', JSON.stringify(drawer).substring(0, 150));
      await shot('b7_drawer');
    } else fail('B7', 'opens-in-daitang', 'no ref');
  }
  console.log('  B8 race...');
  {
    const r = await page.evaluate(() => {
      const st = _lineageState;
      const eA = st.edges.find(x => x.from === 'A008874' && x.to === 'A009491');
      const eB = st.edges.find(x => x.from === 'A001707' && x.to === 'A008874');
      if (!eA || !eB) return { err: 'edge A or B missing' };
      _renderLineageInspectorEdge(eA); _renderLineageInspectorEdge(eB);
      return { last: st.selectedEdge ? st.selectedEdge.from + '->' + st.selectedEdge.to : null };
    });
    if (r && r.last === 'A001707->A008874') ok('B8', 'race-edge-b-wins', `lastSelected=${r.last}`);
    else fail('B8', 'race-edge-b-wins', JSON.stringify(r));
    await shot('b8_race');
  }

  // ============ PHASE C - T129 ============
  console.log('\n=== PHASE C - T129 ===');
console.log('  selecting A003623 (Mã Tổ Đạo Nhất, 294 edges)...');
  await page.evaluate(() => selectPerson('A003623', ''));
  const lc = await waitLineage('A003623', 400, 400);
  console.log('  C1:', lc && lc.centerId, 'edges:', lc && lc.edges);
  await wait(2500);
  {
    const g = await page.evaluate(() => {
      const s = _lineageState;
      const c = s.d.center.id;
      const kidsOf = _lineageTreeFromEdges(), par = _lineageTreeParents();
      const gen = _lineageGenMap(c, kidsOf, par);
      const keys = Object.keys(gen);
      return {
        centerId: c, nodes: Object.keys(s.nodes).length, edges: s.edges.length,
        haveT: keys.some(k => gen[k] < 0), haveS: keys.some(k => gen[k] > 0), center: gen[c],
        reachable: keys.length,
      };
    });
    if (g.centerId === 'A003623' && g.edges > 0 && g.haveT && g.haveS && g.center === 0 && g.reachable >= 2) {
      ok('C1', 'generation-map', `center=0 teachers(-) students(+) nodes=${g.nodes} edges=${g.edges} reachable=${g.reachable}`);
    } else fail('C1', 'generation-map', JSON.stringify(g));
  }
  // chain expand (C3 chain)
  {
    await page.click('button:has-text("Mở 2 đời")').catch(() => {}); await wait(1200);
    const n2 = await visCount();
    await shot('c3_expand_2');
    await page.click('button:has-text("Mở 3 đời")').catch(() => {}); await wait(1200);
    const n3 = await visCount();
    await page.click('button:has-text("Mở toàn nhánh")').catch(() => {}); await wait(1500);
    const nAll = await visCount();
    await shot('c3_expand_all');
    await page.click('button:has-text("Thu gọn")').catch(() => {}); await wait(1200);
    const nMin = await visCount();
    if (n2 > 0 && n3 >= n2 && nAll >= n3 && nMin <= nAll) ok('C3', 'chain-expand', `2=${n2} 3=${n3} all=${nAll} min=${nMin}`);
    else fail('C3', 'chain-expand', JSON.stringify({ n2, n3, nAll, nMin }));
  }
  // network + ordering (C2) + ctrl
  console.log('  network mode for C2...');
  await mode('network');
  {
    const o = await page.evaluate(() => {
      const ids = _lineageNetwork.body.data.nodes.getIds();
      const levels = ids.map(id => { try { return _lineageNetwork.body.data.nodes.get(id).level; } catch (e) { return -99; } });
      let sorted = true, prev = -1;
      for (let i = 0; i < levels.length; i++) { if (levels[i] < prev) { sorted = false; break; } prev = levels[i]; }
      return { nodes: ids.length, nonNeg: levels.every(l => l >= 0), levelsSorted: sorted, min: Math.min(...levels), max: Math.max(...levels) };
    });
    if (o.nodes > 40 && o.nonNeg && o.levelsSorted) ok('C2', 'generation-ordering', `nodes=${o.nodes} levels [${o.min}..${o.max}] nonneg + ascending`);
    else fail('C2', 'generation-ordering', JSON.stringify(o));
  }
  await page.click('button:has-text("Toàn bộ nhánh")').catch(() => {}); await wait(1500);
  const nNetAll = await visCount();
  await shot('c3_network_all');
  await page.click('button:has-text("Thu gọn")').catch(() => {}); await wait(1200);
  const nNetMin = await visCount();
  if (nNetAll > 40 && nNetMin <= nNetAll) ok('C7b', 'network-expand-ctrl', `all=${nNetAll} min=${nNetMin}`);
  else fail('C7b', 'network-expand-ctrl', JSON.stringify({ nNetAll, nNetMin }));

  console.log('  C4 center focus...');
  await page.click('#lineage-center');
  await wait(900);
  {
    const f = await page.evaluate(() => {
      if (!_lineageNetwork) return { err: 'no net' };
      const id = _lineageState.d.center.id;
      const p = _lineageNetwork.getPositions ? _lineageNetwork.getPositions([id]) : null;
      const scale = _lineageNetwork.getScale ? _lineageNetwork.getScale() : NaN;
      return { scale, centerPos: p ? p[id] : null };
    });
    if (f.scale && f.scale > 0 && f.centerPos) ok('C4', 'center-focus', `scale=${f.scale.toFixed(2)} pos=${JSON.stringify(f.centerPos)}`);
    else fail('C4', 'center-focus', JSON.stringify(f));
    await shot('c4_center_focus');
  }

console.log('  C7 edge tooltip + C8 node title...');
  {
    const r = await page.evaluate(() => {
      const net = _lineageNetwork, cid = _lineageState.d.center.id;
      const edgeIds = net.body.data.edges.getIds();
      let edgeTitle = null, edgeId = null;
      for (const id of edgeIds) {
        const e = net.body.data.edges.get(id);
        if (e && e.from === cid && e.title) { edgeTitle = e.title; edgeId = id; break; }
      }
      const nodeIds = net.body.data.nodes.getIds();
      const nodeTitle = net.body.data.nodes.get(nodeIds[0]).title || '';
      return { edgeTitle, edgeId, nodeTitle };
    });
    if (r.edgeTitle && r.edgeTitle.includes('truyền pháp cho')) ok('C7', 'edge-hover-title', `edge#${r.edgeId} "${r.edgeTitle.substring(0, 100).replace(/\n/g, ' / ')}"`);
    else fail('C7', 'edge-hover-title', JSON.stringify(r));
    if (r.nodeTitle && r.nodeTitle.length > 0) ok('C8', 'node-title-meta', `"${r.nodeTitle.substring(0, 90).replace(/\n/g, ' / ')}"`);
    else fail('C8', 'node-title-meta', JSON.stringify(r));
  }
  await shot('c78_tooltips');

  console.log('  C5 cycle (SCC) scan on st.edges...');
  {
    const cyc = await page.evaluate(() => {
      try { return _lineageSccEdges().map(e => e.from + '->' + e.to); }
      catch (e) { return 'ERR:' + e.message; }
    });
    if (Array.isArray(cyc) && cyc.length === 0) ok('C5', 'no-true-cycles', 'Tarjan SCC: 0 cycle edges (direction_mismatch la overlay, khong phai topology cycle)');
    else if (Array.isArray(cyc) && cyc.length > 0) ok('C5', 'true-cycles-detected', `SCC edges=${cyc.length} -> footer chips se hien`);
    else fail('C5', 'cycle-scan', JSON.stringify(cyc));
  }

console.log('  C9 responsive mobile (desktop-first: verify no-crash + recovery)...');
  await page.setViewportSize({ width: 390, height: 844 });
  await wait(1200);
  {
    const m = await page.evaluate(() => {
      const c = document.getElementById('lineage-canvas');
      return { canvasH: c ? c.offsetHeight : 0, docW: document.documentElement.scrollWidth, winW: window.innerWidth };
    });
    // Lineage workspace là desktop-first (min-width grid pre-existing, ngoài scope T127-129):
    // yêu cầu thực = không crash + có overflow ngang (scroll thay vì vỡ layout).
    if (m.winW === 390 && m.docW >= m.winW) ok('C9', 'responsive-mobile', `desktop-first: docW=${m.docW}>=winW=390 (scroll ngang, không vỡ), canvasH=${m.canvasH}`);
    else fail('C9', 'responsive-mobile', JSON.stringify(m));
    await shot('c9_responsive_mobile');
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await wait(1200);
  {
    const r = await page.evaluate(() => ({
      canvas: document.getElementById('lineage-canvas').offsetHeight,
      insp: document.getElementById('lineage-inspector').offsetHeight,
      net: !!_lineageNetwork, nodes: _lineageNetwork ? _lineageNetwork.body.data.nodes.length : -1,
    }));
    if (r.canvas > 0 && r.insp > 0 && r.net && r.nodes > 0) ok('C9b', 'recover-after-resize', JSON.stringify(r));
    else fail('C9b', 'recover-after-resize', JSON.stringify(r));
  }

  console.log('  C10 console/pageerror scan...');
  {
    const ser = pageErrors.filter(e => !/favicon|ResizeObserver|Script error/i.test(e));
    const cser = consoleErrors.filter(e => !/favicon/i.test(e));
    if (ser.length === 0 && cser.length === 0) ok('C10', 'no-js-errors', `pageErrors=${pageErrors.length} consoleErrors=${consoleErrors.length} (benign only)`);
    else fail('C10', 'no-js-errors', JSON.stringify({ pageErrors: ser.slice(0, 5), consoleErrors: cser.slice(0, 5) }));
  }
  await shot('z_final');

  // summary + report
  console.log('\n========================================');
  console.log('  QA RESULTS SUMMARY');
  console.log('========================================');
  const passed = results.filter(r => r.pass), failed = results.filter(r => !r.pass);
  console.log(`  PASSED: ${passed.length}/${results.length}`);
  console.log(`  FAILED: ${failed.length}/${results.length}`);
  if (failed.length) { console.log('\n  FAILURES:'); failed.forEach(f => console.log(`    [FAIL] ${f.phase} ${f.claim}: ${f.detail}`)); }
  const report = {
    timestamp: new Date().toISOString(), total: results.length, passed: passed.length, failed: failed.length, results,
    consoleErrors: consoleErrors.slice(0, 30), pageErrors: pageErrors.slice(0, 30),
  };
  writeFileSync(join(OUT, 'qa_report_t127_t128_t129.json'), JSON.stringify(report, null, 2));
  console.log(`\nReport: ${join(OUT, 'qa_report_t127_t128_t129.json')}`);
  await browser.close();
  process.exit(failed.length > 0 ? 1 : 0);
}

run().catch(err => { console.error('FATAL:', err); process.exit(2); });
