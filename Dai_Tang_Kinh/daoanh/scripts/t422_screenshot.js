// T422: chụp ảnh cây TRƯỚC/SAU khi khử trùng cạnh DILA (46.006 -> 23.014).
// Dùng Edge (channel msedge) vì chromium chưa cài trong node_modules.
// So sánh số nét với t410-screenshot-probe.json (chụp TRƯỚC khi khử trùng).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, '..', 'docs', 'sessions', '2026-10-19', 'T422');
const BASE = 'http://127.0.0.1:8080/daoanh/places.html';
const IDS = ['A004980', 'A009460', 'A047924'];
const THEMES = ['dark', 'light'];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const results = [];
  for (const id of IDS) {
    for (const theme of THEMES) {
      const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
      const page = await ctx.newPage();
      try {
        await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.evaluate((t) => localStorage.setItem('pp-theme', t), theme);
        await page.goto(BASE + '?mode=lineage&focus=' + id + '&lm=tree', { waitUntil: 'domcontentloaded', timeout: 60000 });
        let canvasOk = true;
        try {
          await page.waitForSelector('#lineage-canvas canvas', { timeout: 45000 });
        } catch (e) { canvasOk = false; }
        await page.waitForSelector('#lineage-edge-legend', { state: 'visible', timeout: 20000 });
        await page.waitForTimeout(5000);
        const probe = await page.evaluate(() => {
          const cs = getComputedStyle(document.documentElement);
          const g = (n) => (cs.getPropertyValue(n) || '').trim();
          const canvasEl = document.querySelector('#lineage-canvas canvas');
          const hist = {};
          let spine = 0, dashed = 0, mainThick = 0;
          try {
            const eds = (_lineageNetwork && _lineageNetwork.body && _lineageNetwork.body.edges)
              ? _lineageNetwork.body.edges : [];
            const ids = eds.getIds ? eds.getIds() : [];
            ids.forEach((id) => {
              const e = eds.get(id);
              const t = e._edgeToken || '(none)';
              hist[t] = (hist[t] || 0) + 1;
              if (e._isSpine) spine++;
              if (e._edgeDashed) dashed++;
              if (e._isMain) mainThick++;
            });
          } catch (err) { hist.__err = String(err && err.message); }
          return {
            theme: document.documentElement.getAttribute('data-theme') || '(default)',
            edgeDila: g('--edge-dila'), edgeAgree: g('--edge-agree'),
            edgeCount: Object.keys(hist).reduce((a, k) => a + hist[k], 0),
            tokenHistogram: hist, spineEdges: spine, dashedEdges: dashed, mainThickEdges: mainThick,
            canvasSize: canvasEl ? (canvasEl.width + 'x' + canvasEl.height) : 'none'
          };
        });
        const file = path.join(OUT, `t422_after_${id}_${theme}.png`);
        await page.screenshot({ path: file });
        results.push({ id, theme, file, canvasOk, probe });
        console.log('OK', id, theme, '| canvasOk=' + canvasOk,
          '| edges=' + probe.edgeCount, JSON.stringify(probe.tokenHistogram),
          '| spine=' + probe.spineEdges, 'dashed=' + probe.dashedEdges);
      } catch (e) {
        results.push({ id, theme, error: e.message });
        console.log('FAIL', id, theme, e.message);
      } finally { await ctx.close(); }
    }
  }
  fs.writeFileSync(path.join(OUT, 't422-screenshot-probe.json'), JSON.stringify(results, null, 2), 'utf8');
  await browser.close();
  const failed = results.filter((r) => r.error);
  console.log(failed.length ? ('DONE with ' + failed.length + ' failure(s)') : 'DONE all screenshots ok');
  process.exit(failed.length ? 1 : 0);
})();
