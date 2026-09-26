// tests/e2e-nexus-qa.spec.js
// T92 Phase 3 - Regression/QA: console + network + UI evidence cho tab Nexus (read-only).
// Nguyen tac QA: KHONG sua DB/data-source (chi GET; kiem tra khong co request ghi).
//
// LUU Y KIEN TRUC: tab Nexus nam trong `places.html` (goc repo) - app.py:5000
// KHONG phuc vu file nay (chi /daoanh/admin/*). Spec nay serve places.html qua Route
// interception (cung origin => baseUrl = localhost:5000 hoat dong), moi /daoanh/api/*
// di thang vao app.py that. Day la QA metric cho working tree hien tai (gom ca
// grouped-view default dang uncommitted cho place/person).
//
// RAT NEO:
//  - _nexusData/_nexusNetwork/_currentPlaceId la top-level `let` (KHONG phai
//    property cua window) => trong page.evaluate dung bare identifier.
//  - Auto-load (window.onload) chi goi selectItem (PLACE). Person root phai mo
//    theo real flow: set _currentEntityType/_currentPlaceId rui click tab Nexus.
//  - CSS /favicon bi 404 truoc day (console error) => route-mock sang 200 rong.
//  - Google map tiles (mt1.google.com) luon ERR_ABORTED trong moi truong sandbox
//    => loc trong requestfailed (cham /daoanh/api/*).

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const EVID_DIR = path.join(__dirname, '..', 'docs', 'sessions', '2026-09-05_T92_nexus_qa');
const PLACES_HTML = fs.readFileSync(path.join(__dirname, '..', 'places.html'), 'utf8');
const BASE = 'http://localhost:5000/daoanh/places.html';

function mergeEvidence(key, obj) {
    fs.mkdirSync(EVID_DIR, { recursive: true });
    const fp = path.join(EVID_DIR, 'evidence.json');
    let all = {};
    try { all = JSON.parse(fs.readFileSync(fp, 'utf8')); } catch (e) { /* first write */ }
    all[key] = obj;
    fs.writeFileSync(fp, JSON.stringify(all, null, 2));
}

async function shot(page, key, name) {
    fs.mkdirSync(EVID_DIR, { recursive: true });
    const fn = 'p-' + key + '-' + name + '.png';
    await page.screenshot({ path: path.join(EVID_DIR, fn) });
    return fn;
}

// Mock asset bi 404 (console-error truoc day) sang 200 rong.
async function attachAssetMocks(page) {
    await page.route('**/daoanh/styles/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
    await page.route('**/favicon.ico', r => r.fulfill({ status: 200, contentType: 'image/x-icon', body: '' }));
    await page.route('**/places.html.map', r => r.fulfill({ status: 200, contentType: 'application/json', body: '' }));
}

// Serve places.html cung origin (query string => phai dung predicate, glob khong match).
async function routePlaceHtml(page) {
    await page.route(u => u.href.includes('/daoanh/places.html'),
        r => r.fulfill({ status: 200, contentType: 'text/html', body: PLACES_HTML }));
}

async function openBase(page) {
    await attachAssetMocks(page);
    await routePlaceHtml(page);
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(700);
}

async function gotoNexus(page, rootId, type) {
    await attachAssetMocks(page);
    await routePlaceHtml(page);
    await page.goto(BASE + '?nexus_root=' + rootId + '&nexus_type=' + type, { waitUntil: 'domcontentloaded' });
    await waitNexusCanvas(page);
}

// Person root: real path tu app (xem note RAT NEO o dau file).
async function gotoNexusPerson(page, personId) {
    await openBase(page);
    await page.evaluate((id) => { _currentEntityType = 'person'; _currentPlaceId = id; }, personId);
    await page.click('#da-stabs .da-stab[data-t="nexus"]');
    await waitNexusCanvas(page);
}

async function waitNexusCanvas(page, timeout = 45000) {
    await page.waitForFunction(() => {
        const c = document.getElementById('nmp-canvas');
        return c && c.querySelectorAll('canvas').length >= 1 && _nexusData && _nexusData.center;
    }, null, { timeout });
}

async function uiSnapshot(page) {
    return page.evaluate(() => {
        const t = (s) => { const el = document.getElementById(s); return el ? el.textContent : ''; };
        const vis = (s) => { const el = document.getElementById(s); return !!el && getComputedStyle(el).display !== 'none'; };
        return {
            countText: t('nmp-filters-count'),
            statsText: t('nexus-stats'),
            evidenceSummary: t('nmp-evidence-summary'),
            nameVi: t('nmp-name-vi'),
            emptyVisible: vis('nmp-empty'),
            placeholderVisible: vis('nmp-placeholder'),
            canvasVisible: vis('nmp-canvas'),
            buttons: { share: vis('nmp-btn-share'), bookmark: vis('nmp-btn-bookmark'), export: vis('nmp-btn-export') }
        };
    });
}

// vis.Network khong co getNodes(); dùng getPositions() (map id->pos cua cac node dang hien thi).
async function netStatic(page) {
    return page.evaluate(() => {
        const net = _nexusNetwork;
        if (!net) return { count: 0, ids: [] };
        try {
            const pos = net.getPositions();
            const ids = Object.keys(pos);
            return { count: ids.length, ids: ids };
        } catch (e) {
            return { count: -2, ids: [] };
        }
    });
}

async function clusterIds(page) {
    const s = await netStatic(page);
    return s.ids.filter(id => {
        const x = String(id);
        return x.startsWith('g-') || x.startsWith('sg-');
    });
}

// Click vao node tren vis canvas (vi cluster/group node) truyen toa do that.
async function clickVisNode(page, nodeId, boxId = 'nmp-canvas') {
    const r = await page.evaluate(({ nodeId, boxId }) => {
        const net = _nexusNetwork;
        if (!net) return { clicked: false, reason: 'no-network' };
        const pos = net.getPositions([nodeId]);
        if (!pos || !pos[nodeId]) return { clicked: false, reason: 'no-pos' };
        const p = net.canvasToDOM(pos[nodeId]);
        const box = document.getElementById(boxId).getBoundingClientRect();
        return { clicked: true, x: box.left + p.x, y: box.top + p.y };
    }, { nodeId, boxId });
    if (!r.clicked) return r;
    await page.mouse.click(r.x, r.y);
    await page.waitForTimeout(1500);
    return r;
}

function attachCollectors(page) {
    const ctx = { consoleErrs: [], pageErrs: [], reqFails: [], apiM: new Set(), apiNexus: [] };
    page.on('console', m => { if (m.type() === 'error') ctx.consoleErrs.push(m.text()); });
    page.on('pageerror', e => ctx.pageErrs.push(String(e)));
    page.on('requestfailed', r => { const f = r.failure(); if (f) ctx.reqFails.push({ url: r.url(), err: f.errorText }); });
    page.on('request', r => { if (r.url().includes('/daoanh/api/')) ctx.apiM.add(r.method()); });
    page.on('response', async r => {
        if (r.url().includes('/api/nexus/')) {
            const method = r.request().method();
            try {
                const j = await r.json();
                ctx.apiNexus.push({ method: method, code: r.status(), ok: j.ok === true, nodes: j.nodes ? j.nodes.length : -1, center: j.center ? j.center.id : null, url: r.url() });
            } catch (e) {
                ctx.apiNexus.push({ method: method, code: r.status(), ok: false, err: 'json-parse' });
            }
        }
    });
    return ctx;
}

// 'Failed to load resource' la hint chung cua browser cho resource bi 404/khi
// chay ngoai moi truong that (vd tile map) - khong phai loi JS/logic.
const hardErrCount = (ctx) =>
    ctx.consoleErrs.filter(s => !/Failed to load resource/.test(s)).length + ctx.pageErrs.length;

test.describe('T92 Nexus — Regression/QA (console + network + UI) — working tree', () => {
    test.setTimeout(180000);

    test('A. Empty state — không root được chọn', async ({ page }) => {
        const ctx = attachCollectors(page);
        await openBase(page);
        await page.click('#da-stabs .da-stab[data-t="nexus"]');
        await page.waitForTimeout(2000);
        const state = await page.evaluate(() => ({
            emptyVisible: (() => { const el = document.getElementById('nmp-empty'); return !!el && el.style.display === 'flex'; })(),
            placeholderVisible: (() => { const el = document.getElementById('nmp-placeholder'); return !!el && el.style.display !== 'none' && el.style.display !== ''; })(),
            canvas: document.querySelectorAll('#nmp-canvas canvas').length
        }));
        expect(state.emptyVisible || state.placeholderVisible).toBe(true);
        expect(state.canvas).toBe(0);
        expect(ctx.apiNexus.length).toBe(0);
        expect(hardErrCount(ctx)).toBe(0);
        const sc = await shot(page, 'A', 'empty');
        mergeEvidence('A-empty', { state, hardErr: hardErrCount(ctx), screenshot: sc });
    });

    test('B. Place root PL000000023255 — grouped default view + evidence UI + contract', async ({ page }) => {
        const ctx = attachCollectors(page);
        await gotoNexus(page, 'PL000000023255', 'place');
        const ui = await uiSnapshot(page);
        const contract = await page.evaluate(() => ({
            center: (_nexusData.center || {}).id,
            nodes: (_nexusData.nodes || []).length,
            edges: (_nexusData.edges || []).length,
            groups: Object.keys(_nexusData.groups || {}).length,
            nullIds: (_nexusData.nodes || []).filter(n => !n.id).length,
            undefLabels: (_nexusData.nodes || []).filter(n => !n.label && !n.label_zh).length,
            navigableCount: (_nexusData.nodes || []).filter(n => n.navigable).length
        }));
        expect(contract.center).toBe('PL000000023255');
        expect(contract.nodes).toBeGreaterThan(0);
        expect(contract.nullIds).toBe(0);
        expect(contract.undefLabels).toBe(0);
        expect(ui.canvasVisible).toBe(true);
        const ns = await netStatic(page);
        expect(ns.count).toBeGreaterThan(1);
        const m = ui.statsText.match(/(\d+)\s*nút/);
        expect(m).toBeTruthy();
        expect(parseInt(m[1], 10)).toBe(contract.nodes);
        expect(ui.evidenceSummary).toContain('DILA');
        expect(contract.groups).toBeGreaterThan(0);
        expect(ui.countText).toMatch(/nhóm|group/i);
        const g = (await clusterIds(page)).filter(id => String(id).startsWith('g-'));
        expect(g.length).toBeGreaterThan(0);
        expect(ui.buttons.share).toBe(true);
        expect(ui.buttons.bookmark).toBe(true);
        expect(ui.buttons.export).toBe(true);
        expect(hardErrCount(ctx)).toBe(0);
        expect(ctx.apiNexus.length).toBeGreaterThan(0);
        const sc = await shot(page, 'B', 'grouped-default');
        mergeEvidence('B-place-root', { contract, ui: { stats: ui.statsText, countText: ui.countText, evidence: ui.evidenceSummary, groups: g }, screenshot: sc, apiNexus: ctx.apiNexus });
    });

    test('C. Expand/collapse group nodes trên canvas (place root)', async ({ page }) => {
        const ctx = attachCollectors(page);
        await gotoNexus(page, 'PL000000023255', 'place');
        const pick = g => g.find(x => /kinh_dien/.test(x)) || g.find(x => /tang_nhan/.test(x)) || g[0];
        const g = (await clusterIds(page)).filter(id => String(id).startsWith('g-'));
        expect(g.length).toBeGreaterThan(0);
        const node = pick(g);
        const before = (await netStatic(page)).count;
        const r1 = await clickVisNode(page, node, 'nmp-canvas');
        const expanded = (await netStatic(page)).count;
        const r2 = await clickVisNode(page, node, 'nmp-canvas');
        const collapsed = (await netStatic(page)).count;
        expect(r1.clicked).toBe(true);
        expect(r2.clicked).toBe(true);
        // Mo rong làm tang so node; thu gon quay ve (it nhat 1 lan thay doi).
        expect(expanded).not.toBe(before);
        expect(collapsed).not.toBe(expanded);
        expect(hardErrCount(ctx)).toBe(0);
        const sc = await shot(page, 'C', 'expand-collapse');
        mergeEvidence('C-expand-collapse', { node, before, expanded, collapsed, screenshot: sc });
    });

    test('D. Person root A005671 — grouped + expand DILA/Marcus', async ({ page }) => {
        const ctx = attachCollectors(page);
        await gotoNexusPerson(page, 'A005671');
        const ui = await uiSnapshot(page);
        const contract = await page.evaluate(() => ({
            center: (_nexusData.center || {}).id,
            nodes: (_nexusData.nodes || []).length,
            edges: (_nexusData.edges || []).length,
            groups: Object.keys(_nexusData.groups || {}).length,
            nullIds: (_nexusData.nodes || []).filter(n => !n.id).length,
            undefLabels: (_nexusData.nodes || []).filter(n => !n.label && !n.label_zh).length
        }));
        expect(contract.center).toBe('A005671');
        expect(contract.nodes).toBeGreaterThan(0);
        expect(contract.groups).toBeGreaterThan(0);
        expect(ui.canvasVisible).toBe(true);
        expect(ui.countText).toMatch(/nhóm|group/i);
        const g0 = (await clusterIds(page)).filter(id => String(id).startsWith('g-'));
        expect(g0.length).toBeGreaterThan(0);
        const targets = [];
        for (const key of ['dila', 'marcus']) {
            const hit = g0.find(x => String(x).toLowerCase().includes(key));
            if (hit) targets.push(hit);
        }
        for (const x of g0) { if (targets.length >= 2) break; if (!targets.includes(x)) targets.push(x); }
        const results = [];
        for (const t of targets.slice(0, 2)) {
            const before = (await netStatic(page)).count;
            const r1 = await clickVisNode(page, t, 'nmp-canvas');
            const mid = (await netStatic(page)).count;
            const r2 = await clickVisNode(page, t, 'nmp-canvas');
            const after = (await netStatic(page)).count;
            results.push({ node: t, clicked1: r1.clicked, clicked2: r2.clicked, before, mid, after });
        }
        const anyToggle = results.filter(r => r.clicked1 && r.mid !== r.before).length;
        expect(anyToggle).toBeGreaterThan(0);
        expect(hardErrCount(ctx)).toBe(0);
        const sc = await shot(page, 'D', 'person-grouped');
        mergeEvidence('D-person-root', { contract, ui: { stats: ui.statsText, countText: ui.countText, groups: g0 }, toggle: results, screenshot: sc });
    });

    test('E. Detail panel + set-as-root + deep-link (đường code chính thức trên data thật)', async ({ page }) => {
        const ctx = attachCollectors(page);
        await gotoNexus(page, 'PL000000023255', 'place');
        // Node truc tiep: navigable person (co DILA id) — khong phai center. Canvas-click
        // toi _nxPerson can qua g-tang_nhan->sg-dynasty; de QA duong code chinh thuc,
        // goi _nexusShowDetail(n, d) chinh la ham ma click-handler goi (places.html:5424-5425).
        const pk = await page.evaluate((cid) => {
            const n = (_nexusData.nodes || []).find(x => x.navigable && String(x.id) !== String(cid));
            return n ? { id: String(n.id), label: n.label || '', label_zh: n.label_zh || '', group: n.group, navigable: !!n.navigable } : null;
        }, 'PL000000023255');
        expect(pk).toBeTruthy();
        await page.evaluate((n) => _nexusShowDetail(n, _nexusData), pk);
        const det = await page.evaluate(() => {
            const el = document.getElementById('nmp-detail');
            const body = document.getElementById('nmp-detail-body');
            const acts = document.getElementById('nmp-detail-actions');
            return {
                open: !!el && el.style.display !== 'none' && el.style.display !== '',
                titleEl: document.getElementById('nmp-detail-title').textContent,
                setRootBtn: acts ? acts.textContent : '',
                deepLinkCount: body ? body.querySelectorAll('span[onclick*="da-stabs"]').length : 0,
                hasEvidence: body ? /Nguồn bằng chứng/.test(body.innerHTML) : false,
                hasQualityBadge: body ? /Chưa gắn ID DILA|gắn ID DILA|Cô lập|synthetic/i.test(body.innerHTML) : false,
                bodyText: body ? body.textContent.slice(0, 300) : ''
            };
        });
        expect(det.open).toBe(true);
        expect(det.titleEl).toBeTruthy();
        expect(det.setRootBtn).toContain('Set làm root');
        expect(det.deepLinkCount).toBeGreaterThan(0);
        expect(det.hasEvidence || det.hasQualityBadge).toBe(true);
        expect(hardErrCount(ctx)).toBe(0);
        // Set-as-root thật (click button) — re-fetch + re-render quanh root mới.
        await page.click('#nmp-detail-actions button');
        await page.waitForFunction((o) => _nexusData && _nexusData.center && String(_nexusData.center.id) !== o,
            'PL000000023255', { timeout: 45000 });
        const after = await page.evaluate(() => ({ center: _nexusData.center.id, nodes: (_nexusData.nodes || []).length, canvas: document.querySelectorAll('#nmp-canvas canvas').length }));
        expect(after.center).toBe(pk.id);
        expect(after.canvas).toBeGreaterThan(0);
        const sc = await shot(page, 'E', 'detail-setroot');
        mergeEvidence('E-detail', { target: pk, det, after, hardErr: hardErrCount(ctx), screenshot: sc });
    });

    test('F. Share + bookmark + export (JSON + PNG)', async ({ page }) => {
        const ctx = attachCollectors(page);
        await gotoNexus(page, 'PL000000023255', 'place');
        // Clipboard khong kha dung trong headless/insecure => stub lai de chung minh URL duoc tao.
        await page.evaluate(() => {
            window.__clip = null;
            try {
                Object.defineProperty(navigator, 'clipboard', {
                    configurable: true,
                    value: { writeText: (t) => { window.__clip = t; return Promise.resolve(); } }
                });
            } catch (e) { /* keep */ }
        });
        await page.click('#nmp-btn-share');
        await page.waitForTimeout(600);
        const sharedUrl = await page.evaluate(() => window.__clip);
        expect(sharedUrl).toBeTruthy();
        expect(sharedUrl).toContain('nexus_root=PL000000023255');
        expect(sharedUrl).toContain('nexus_type=place');
        const shareBtnText = await page.evaluate(() => document.getElementById('nmp-btn-share').textContent);
        expect(shareBtnText).toContain('Đã sao chép');
        // Bookmark: toggle luu/bo-luu trong localStorage (khong cham DB).
        await page.evaluate(() => localStorage.removeItem('nexus_bookmarks'));
        await page.click('#nmp-btn-bookmark');
        await page.waitForTimeout(400);
        const saved = await page.evaluate(() => (JSON.parse(localStorage.getItem('nexus_bookmarks') || '[]')).length === 1);
        await page.click('#nmp-btn-bookmark');
        await page.waitForTimeout(400);
        const unsaved = await page.evaluate(() => (JSON.parse(localStorage.getItem('nexus_bookmarks') || '[]')).length === 0);
        expect(saved).toBe(true);
        expect(unsaved).toBe(true);
        // Export: bat loi de biet ly do (neu co) + capture blob payload + download names.
        await page.evaluate(() => {
            window.__exportErr = null;
            window.__blobs = [];
            const _cU = URL.createObjectURL;
            URL.createObjectURL = (obj) => {
                if (obj instanceof Blob) { obj.text().then(t => window.__blobs.push({ type: obj.type, len: t.length, head: t.slice(0, 60) })).catch(() => {}); }
                return _cU(obj);
            };
            const orig = window._nexusExportGraph;
            window._nexusExportGraph = () => { try { orig(); } catch (e) { window.__exportErr = String(e); throw e; } };
        });
        const downloads = [];
        page.on('download', d => downloads.push(d.suggestedFilename()));
        await page.click('#nmp-btn-export');
        // Doc button trong cua so 2s (truoc khi revert text).
        await page.waitForTimeout(900);
        const exportBtnText = await page.evaluate(() => document.getElementById('nmp-btn-export').textContent);
        const exportErr = await page.evaluate(() => window.__exportErr);
        expect(exportErr).toBeFalsy();
        expect(exportBtnText).toContain('Đã xuất');
        await page.waitForTimeout(7000);
        const hasJson = downloads.some(n => /nexus-.*\.json/i.test(n || '')) || (await page.evaluate(() => window.__blobs.some(b => /json/.test(b.type))));
        const hasPng = downloads.some(n => /nexus-.*\.png/i.test(n || ''));
        const blobs = await page.evaluate(() => window.__blobs);
        expect(hasJson).toBe(true);
        expect(hasPng).toBe(true);
        expect(hardErrCount(ctx)).toBe(0);
        const sc = await shot(page, 'F', 'share-bookmark-export');
        mergeEvidence('F-share-bookmark-export', { sharedUrl, shareBtnText, downloads, blobs, hasJson, hasPng, saved, unsaved, exportErr, screenshot: sc });
    });

    test('G. Network QA: chỉ GET + /api/nexus 200 + không ghi DB/data-source', async ({ page }) => {
        const ctx = attachCollectors(page);
        await gotoNexusPerson(page, 'A005671');
        await page.waitForTimeout(800);
        const li = await page.evaluate(() => ({ center: _nexusData.center.id, nodes: (_nexusData.nodes || []).length }));
        expect(li.center).toBe('A005671');
        expect(li.nodes).toBeGreaterThan(0);
        const methods = [...ctx.apiM];
        expect(methods.every(m => m === 'GET')).toBe(true);
        expect(ctx.apiNexus.length).toBeGreaterThan(0);
        expect(ctx.apiNexus.every(r => r.method === 'GET')).toBe(true);
        expect(ctx.apiNexus.filter(r => r.code === 200 && r.ok && r.nodes > 0).length).toBeGreaterThan(0);
        const apiFail = ctx.reqFails.filter(f => f.url.includes('/daoanh/api/'));
        expect(apiFail).toHaveLength(0);
        expect(hardErrCount(ctx)).toBe(0);
        const sc = await shot(page, 'G', 'network');
        mergeEvidence('G-network', { li, methods, apiNexus: ctx.apiNexus, apiRequestFails: apiFail.length, hardErr: hardErrCount(ctx), screenshot: sc });
    });
});