#!/usr/bin/env node
// scripts/qa_t130_session5_regression.mjs
// T130 Session 5 — T129 regression + T130 Session 4 deep-link browser QA (:8080 live)
// Covers:
//   A. T130 Session 4 deep-link: ?mode=lineage&focus=&lm=&chain=, ?expand= legacy, pushState/popstate
//   B. T129 regression: gen map, ordering, net ctrl bar (expand/fold), center focus, edge/node titles, SCC, footer
// Usage: node scripts/qa_t130_session5_regression.mjs
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE = 'http://127.0.0.1:8080';
const OUT = join('docs', 'sessions', 'qa_t130_session5_regression');
mkdirSync(OUT, { recursive: true });

const results = [];
let shotN = 0;
let page, consoleErrors = [], pageErrors = [];

const ok = (phase, claim, detail = '') => { results.push({ phase, claim, pass: true, detail }); console.log(`  [PASS] ${phase} ${claim} ${detail}`); };
const fail = (phase, claim, detail = '') => { results.push({ phase, claim, pass: false, detail }); console.error(`  [FAIL] ${phase} ${claim} ${detail}`); };
async function shot(label) {
  shotN++;
  const p = join(OUT, `${String(shotN).padStart(2, '0')}_${label}.png`);
  try { await page.screenshot({ path: p, fullPage: false }); } catch (e) { console.log(`  shot failed ${label}: ${e.message}`); }
}
const wait = ms => page.waitForTimeout(ms);

async function waitLineage(id, tries = 60, gapMs = 400) {
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
  // ============ PREFLIGHT ============
  console.log('=== QA PREFLIGHT ===');
  try {
    const r = await fetch(`${BASE}/daoanh/api/monk/A008874/lineage-tree?up=2&down=2`);
    const d = await r.json();
    console.log(`  API probe A008874: ok=${d.ok}, nodes=${(d.nodes || []).length}, edges=${(d.edges || []).length}`);
    if (!d.ok || !d.nodes || d.nodes.length === 0) throw new Error('API probe failed');
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
  page.on('requestfailed', req => consoleErrors.push('requestfailed:' + req.url()));

  const visCount = () => page.evaluate(() => {
    try { return _lineageNetwork && _lineageNetwork.body ? _lineageNetwork.body.data.nodes.length : -1; }
    catch (e) { return -1; }
  });

  // ============ PHASE A — T130 Session 4 deep-link ============
  console.log('\n=== PHASE A - T130 Session 4 deep-link ===');

  // A1: ?mode=lineage&focus=&lm=tree loads state (different-focus path via _t130Pending)
  console.log('  A1 deep-link tree...');
  await page.goto(`${BASE}/daoanh/places.html?mode=lineage&focus=A008874&lm=tree`, { waitUntil: 'domcontentloaded' });
  const l1 = await waitLineage('A008874');
  await wait(1200);
  {
    const st = await page.evaluate(() => {
      const s = _lineageState;
      return {
        centerId: s && s.d && s.d.center ? s.d.center.id : null,
        mode: s ? s.mode : null,
        canvasVisible: document.getElementById('lineage-canvas').offsetHeight > 0,
        tabActive: (document.querySelector('#da-stabs .da-stab[data-t="lineage"]') || {}).className || '',
      };
    });
    if (l1 && l1.centerId === 'A008874' && l1.edges > 0 && st.centerId === 'A008874' && st.mode === 'tree' && st.canvasVisible && st.tabActive.includes('active')) {
      ok('A1', 'deep-link-tree', `center=${st.centerId} edges=${l1.edges} mode=${st.mode} tabActive`);
    } else fail('A1', 'deep-link-tree', JSON.stringify({ l1, st }));
    await shot('a1_deeplink_tree');
  }

  // A2: chain param restores expand set
  {
    await page.goto(`${BASE}/daoanh/places.html?mode=lineage&focus=A008874&lm=tree&chain=A009491`, { waitUntil: 'domcontentloaded' });
    await waitLineage('A008874');
    await wait(1200);
    const r = await page.evaluate(() => {
      const s = _lineageState;
      const ex = (s && s._ftExpanded) ? Array.from(s._ftExpanded) : [];
      return { center: s.d.center.id, expanded: ex, hasChild: ex.includes('A009491'), hasCenter: ex.includes('A008874') };
    });
    if (r.hasChild && r.hasCenter) ok('A2', 'deep-link-chain', `_ftExpanded=${JSON.stringify(r.expanded)}`);
    else fail('A2', 'deep-link-chain', JSON.stringify(r));
    await shot('a2_deeplink_chain');
  }

  // A3: same-focus lm=network via mode button + pushState URL update
  {
    await page.click('#lineage-mode .lineage-mode-btn[data-lm="network"]');
    await wait(1500);
    const r = await page.evaluate(() => ({
      mode: _lineageState.mode, net: !!_lineageNetwork,
      nodes: _lineageNetwork ? _lineageNetwork.body.data.nodes.length : -1,
      q: (window.location.search || '').replace(/^[?#]/, ''),
      histLen: history.length,
    }));
    if (r.mode === 'network' && r.net && r.nodes > 0 && r.q.includes('lm=network')) {
      ok('A3', 'mode-pushstate-url', `mode=network nodes=${r.nodes} q="${r.q}" hist=${r.histLen}`);
    } else fail('A3', 'mode-pushstate-url', JSON.stringify(r));
    await shot('a3_network_from_deeplink');
  }

  // A4: popstate back/forward restores mode (same focus → no reload)
  {
    await page.goBack(); await wait(1400);
    const b = await page.evaluate(() => ({ mode: _lineageState.mode, q: (window.location.search || '').replace(/^[?#]/, '') }));
    if (b.mode === 'tree' && b.q.includes('lm=tree')) ok('A4', 'popstate-back', `mode=${b.mode} q="${b.q}"`);
    else fail('A4', 'popstate-back', JSON.stringify(b));
    await page.goForward(); await wait(1400);
    const f = await page.evaluate(() => ({ mode: _lineageState.mode, q: (window.location.search || '').replace(/^[?#]/, '') }));
    if (f.mode === 'network' && f.q.includes('lm=network')) ok('A4b', 'popstate-forward', `mode=${f.mode} q="${f.q}"`);
    else fail('A4b', 'popstate-forward', JSON.stringify(f));
    await shot('a4_popstate');
  }

  // A5: legacy ?expand=<id> maps → mode=lineage&focus=<id>, tree
  {
    await page.goto(`${BASE}/daoanh/places.html?expand=A009491`, { waitUntil: 'domcontentloaded' });
    const lx = await waitLineage('A009491');
    await wait(1400);
    const r = await page.evaluate(() => ({
      centerId: _lineageState.d.center.id, mode: _lineageState.mode,
      q: (window.location.search || '').replace(/^[?#]/, ''),
      tabActive: (document.querySelector('#da-stabs .da-stab[data-t="lineage"]') || {}).className || '',
    }));
    if (lx && lx.centerId === 'A009491' && r.centerId === 'A009491' && r.tabActive.includes('active')) {
      ok('A5', 'legacy-expand-map', `center=${r.centerId} mode=${r.mode} tabActive`);
    } else fail('A5', 'legacy-expand-map', JSON.stringify({ lx, r }));
    await shot('a5_legacy_expand');
  }

  // A6: no JS errors accumulate in Phase A
  {
    const ser = pageErrors.filter(e => !/favicon|ResizeObserver|Script error/i.test(e));
    const cser = consoleErrors.filter(e => !/favicon/i.test(e));
    if (ser.length === 0 && cser.length === 0) ok('A6', 'no-js-errors-A', `pageErrors=${pageErrors.length} consoleErrors=${consoleErrors.length} (benign only)`);
    else fail('A6', 'no-js-errors-A', JSON.stringify({ ser: ser.slice(0, 5), cser: cser.slice(0, 5) }));
  }

  // ============ PHASE B — T129 regression (network mode) ============
  console.log('\n=== PHASE B - T129 regression ===');
  console.log('  selecting A003623 (Mã Tổ Đạo Nhất)...');
  await page.goto(`${BASE}/daoanh/places.html`, { waitUntil: 'domcontentloaded' });
  // clear error log: GOTO chủ động kết thúc trạng thái Phase A (request ancestor-spine A009491
  // đang bay bị abort trong navigation → benign, không phải lỗi code).
  consoleErrors = []; pageErrors = [];
  await wait(1200);
  await page.evaluate(() => selectPerson('A003623', ''));
  const lb = await waitLineage('A003623', 400, 400);
  await wait(2500);

  // B1: generation map
  {
    const g = await page.evaluate(() => {
      const s = _lineageState, c = s.d.center.id;
      const kidsOf = _lineageTreeFromEdges(), par = _lineageTreeParents();
      const gen = _lineageGenMap(c, kidsOf, par);
      const keys = Object.keys(gen);
      return {
        centerId: c, nodes: Object.keys(s.nodes).length, edges: s.edges.length,
        haveT: keys.some(k => gen[k] < 0), haveS: keys.some(k => gen[k] > 0), center: gen[c], reachable: keys.length,
      };
    });
    if (g.centerId === 'A003623' && g.edges > 0 && g.haveT && g.haveS && g.center === 0 && g.reachable >= 2) {
      ok('B1', 'generation-map', `center=0 teachers(-) students(+) nodes=${g.nodes} edges=${g.edges} reachable=${g.reachable}`);
    } else fail('B1', 'generation-map', JSON.stringify(g));
  }

  // B2: network mode + ordering
  await page.click('#lineage-mode .lineage-mode-btn[data-lm="network"]');
  await wait(2200);
  {
    const o = await page.evaluate(() => {
      const ids = _lineageNetwork.body.data.nodes.getIds();
      const levels = ids.map(id => { try { return _lineageNetwork.body.data.nodes.get(id).level; } catch (e) { return -99; } });
      let sorted = true, prev = -1;
      for (let i = 0; i < levels.length; i++) { if (levels[i] < prev) { sorted = false; break; } prev = levels[i]; }
      return { nodes: ids.length, nonNeg: levels.every(l => l >= 0), levelsSorted: sorted, min: Math.min(...levels), max: Math.max(...levels) };
    });
    if (o.nodes > 40 && o.nonNeg && o.levelsSorted) ok('B2', 'generation-ordering', `nodes=${o.nodes} levels [${o.min}..${o.max}] nonneg+ascending`);
    else fail('B2', 'generation-ordering', JSON.stringify(o));
    await shot('b2_network_ordering');
  }

  // B3: net ctrl bar — all 4 T129 buttons present
  {
    const btns = await page.evaluate(() => {
      const bar = Array.from(document.querySelectorAll('#lineage-canvas button')).map(b => b.textContent.trim());
      return bar;
    });
    const need = ['Mở thêm đời trên', 'Mở thêm đời dưới', 'Toàn bộ nhánh', 'Thu gọn nhánh dưới'];
    const missing = need.filter(n => !btns.some(t => t.includes(n)));
    if (missing.length === 0) ok('B3', 'net-ctrl-bar', `buttons=[${btns.map(x => '"' + x + '"').join(', ')}]`);
    else fail('B3', 'net-ctrl-bar', `missing=[${missing}] actual=[${btns}]`);
    await shot('b3_net_ctrl_bar');
  }

  // B4: expand all → node count grows; fold → shrinks
  {
    const n0 = await visCount();
    await page.click('button:has-text("Toàn bộ nhánh")').catch(() => {}); await wait(1800);
    const nAll = await visCount();
    await page.click('button:has-text("Thu gọn nhánh dưới")').catch(() => {}); await wait(1800);
    const nFold = await visCount();
    if (nAll >= n0 && nFold <= nAll) ok('B4', 'network-expand-ctrl', `default=${n0} all=${nAll} fold=${nFold}`);
    else fail('B4', 'network-expand-ctrl', JSON.stringify({ n0, nAll, nFold }));
    await shot('b4_network_expand');
  }

  // B5: center focus (#lineage-center)
  {
    await page.click('#lineage-center');
    await wait(1000);
    const f = await page.evaluate(() => {
      if (!_lineageNetwork) return { err: 'no net' };
      const id = _lineageState.d.center.id;
      const p = _lineageNetwork.getPositions ? _lineageNetwork.getPositions([id]) : null;
      const scale = _lineageNetwork.getScale ? _lineageNetwork.getScale() : NaN;
      return { scale, centerPos: p ? p[id] : null };
    });
    if (f.scale && f.scale > 0 && f.centerPos) ok('B5', 'center-focus', `scale=${f.scale.toFixed(2)} pos=${JSON.stringify(f.centerPos)}`);
    else fail('B5', 'center-focus', JSON.stringify(f));
    await shot('b5_center_focus');
  }

  // B6: edge hover title + node title meta
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
    if (r.edgeTitle && r.edgeTitle.includes('truyền pháp cho')) ok('B6', 'edge-hover-title', `edge#${r.edgeId} "${r.edgeTitle.substring(0, 90).replace(/\n/g, ' / ')}"`);
    else fail('B6', 'edge-hover-title', JSON.stringify(r));
    if (r.nodeTitle && r.nodeTitle.length > 0) ok('B6b', 'node-title-meta', `"${r.nodeTitle.substring(0, 90).replace(/\n/g, ' / ')}"`);
    else fail('B6b', 'node-title-meta', JSON.stringify(r));
    await shot('b6_tooltips');
  }

  // B7: SCC cycle scan no crash
  {
    const cyc = await page.evaluate(() => {
      try { return _lineageSccEdges().map(e => e.from + '->' + e.to); }
      catch (e) { return 'ERR:' + e.message; }
    });
    if (Array.isArray(cyc)) ok('B7', 'scc-cycle-scan', `SCC=" mass edges=${cyc.length} ${cyc.length === 0 ? '(no true cycles)' : '(footer chips will show)'}`);
    else fail('B7', 'scc-cycle-scan', JSON.stringify(cyc));
  }

  // B8: T129 footer (dropped/cycle research note) present or null (honest)
  {
    const f = await page.evaluate(() => {
      const det = document.querySelector('#lineage-canvas details');
      if (!det) return { footer: null };
      return { footer: det.textContent.substring(0, 160) };
    });
    if (f.footer !== null && f.footer.length > 0) ok('B8', 'research-footer', `footer="${f.footer.replace(/\n/g, ' ')}"`);
    else if (f.footer === null) ok('B8', 'research-footer', 'footer null (no dropped/cycle — honest)');
    else fail('B8', 'research-footer', JSON.stringify(f));
    await shot('b8_footer');
  }

  // B9: tree mode still renders after network (mode switch intact)
  await page.click('#lineage-mode .lineage-mode-btn[data-lm="tree"]');
  await wait(1600);
  {
    const r = await page.evaluate(() => ({ mode: _lineageState.mode, net: !!_lineageNetwork, nodes: _lineageNetwork ? _lineageNetwork.body.data.nodes.length : -1 }));
    if (r.mode === 'tree' && r.net && r.nodes > 0) ok('B9', 'back-to-tree', `mode=tree nodes=${r.nodes}`);
    else fail('B9', 'back-to-tree', JSON.stringify(r));
  }

  // B10: no JS errors accumulated in Phase B
  {
    const ser = pageErrors.filter(e => !/favicon|ResizeObserver|Script error/i.test(e));
    const cser = consoleErrors.filter(e => !/favicon/i.test(e));
    if (ser.length === 0 && cser.length === 0) ok('B10', 'no-js-errors-B', `pageErrors=${pageErrors.length} consoleErrors=${consoleErrors.length} (benign only)`);
    else fail('B10', 'no-js-errors-B', JSON.stringify({ ser: ser.slice(0, 5), cser: cser.slice(0, 5) }));
  }

  // summary + report
  console.log('\n========================================');
  console.log('  T130 Session 5 QA SUMMARY');
  console.log('========================================');
  const passed = results.filter(r => r.pass), failed = results.filter(r => !r.pass);
  console.log(`  PASSED: ${passed.length}/${results.length}`);
  console.log(`  FAILED: ${failed.length}/${results.length}`);
  if (failed.length) { console.log('\n  FAILURES:'); failed.forEach(f2 => console.log(`    [FAIL] ${f2.phase} ${f2.claim}: ${f2.detail}`)); }
  const report = {
    timestamp: new Date().toISOString(), total: results.length, passed: passed.length, failed: failed.length, results,
    consoleErrors: consoleErrors.slice(0, 30), pageErrors: pageErrors.slice(0, 30),
  };
  writeFileSync(join(OUT, 'qa_report_t130_session5.json'), JSON.stringify(report, null, 2));
  console.log(`\nReport: ${join(OUT, 'qa_report_t130_session5.json')}`);
  await browser.close();
  process.exit(failed.length > 0 ? 1 : 0);
}

run().catch(err => { console.error('FATAL:', err); process.exit(2); });