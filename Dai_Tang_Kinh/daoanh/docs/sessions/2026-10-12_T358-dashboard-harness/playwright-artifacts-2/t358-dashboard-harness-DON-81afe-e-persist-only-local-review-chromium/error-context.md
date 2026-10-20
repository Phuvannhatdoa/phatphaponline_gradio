# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: t358-dashboard-harness.spec.js >> DONE requires typed confirmation; cancel/Escape no write; persist only local review
- Location: tests\t358-dashboard-harness.spec.js:64:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('#triageMessage')
Expected substring: "Báo cáo đã tải"
Received string:    "BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»i dÃ²ng cÃ²n thiáº¿u Ä‘iá»u kiá»‡n dev; local review khÃ´ng Ä‘Ã³ng task."
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('#triageMessage')
    8 × locator resolved to <p role="status" id="triageMessage" aria-live="polite">BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»i dÃ²ng …</p>
      - unexpected value "BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»i dÃ²ng cÃ²n thiáº¿u Ä‘iá»u kiá»‡n dev; local review khÃ´ng Ä‘Ã³ng task."

```

# Page snapshot

```yaml
- region "Triage / Execution â€” T358" [ref=e2]:
  - generic [ref=e3]:
    - heading "Triage / Execution â€” T358" [level=2] [ref=e4]
    - button "Táº£i láº¡i bÃ¡o cÃ¡o" [ref=e5]
  - paragraph [ref=e6]: DONE chá»‰ xÃ¡c nháºn Admin Ä‘Ã£ review trÃªn trÃ¬nh duyá»‡t nÃ y. NÃºt chá»‰ má»Ÿ khi dev cÃ³ Ä‘á»§ báº£n sá»a, tests vÃ QA Ä‘á»™c láºp; khÃ´ng Ä‘á»•i tráº¡ng thÃ¡i task hoáº·c dá»¯ liá»‡u production.
  - paragraph [ref=e7]: "Audit: 2026-10-12 (+07:00) Â· 2026-10-12-r1 Â· CÃ¡c báº±ng chá»©ng nÃ y lÃ snapshot, khÃ´ng pháº£i kiá»ƒm production má»›i."
  - status [ref=e8]: "BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»\x8di dÃ²ng cÃ²n thiáº¿u Ä‘iá»\x81u kiá»‡n dev; local review khÃ´ng Ä‘Ã³ng task."
  - generic "Thá»© tá»± triá»ƒn khai" [ref=e9]:
    - generic [ref=e10]: "Ưu tiên: T283 → T284 / T290"
    - generic [ref=e11]: "Cổng writer: T287 → T288"
    - generic [ref=e12]: "Song song: T319 · T322 · T323 · T81 · T277 / T328"
  - region "BÃ¡o cÃ¡o triage vÃ thá»±c thi; cuá»™n ngang Ä‘á»ƒ xem Ä‘á»§ cá»™t" [ref=e13]:
    - 'table "Task, chuyÃªn mÃ´n agent, Ä‘iá»u kiá»‡n vÃ hÃ nh Ä‘á»™ng cá»§a Admin" [ref=e14]':
      - caption [ref=e15]: "Task, chuyÃªn mÃ´n agent, Ä‘iá»\x81u kiá»‡n vÃ hÃ nh Ä‘á»™ng cá»§a Admin"
      - rowgroup [ref=e16]:
        - 'row "Task / nhÃ³m Agent Äiá»u kiá»‡n trÆ°á»›c Dev / báº±ng chá»©ng Admin lÃ m tiáº¿p Review" [ref=e17]':
          - columnheader "Task / nhÃ³m" [ref=e18]
          - columnheader "Agent" [ref=e19]
          - 'columnheader "Äiá»u kiá»‡n trÆ°á»›c" [ref=e20]'
          - columnheader "Dev / báº±ng chá»©ng" [ref=e21]
          - columnheader "Admin lÃ m tiáº¿p" [ref=e22]
          - columnheader "Review" [ref=e23]
      - rowgroup [ref=e24]:
        - 'row "T283 — Dọn chuỗi key trong docs/scripts T283: pending Task T283 Code bảo mật; Debug kiểm độc lập KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. Scan local chỉ tên file: 6 đường dẫn còn match; task cũ ghi 18. Chưa redact, không hiển thị chuỗi bí mật. PASS: Bản sửa đúng scope PASS: Tests/kiểm chứng acceptance PASS: Debug kiểm độc lập + root QA Scope T283 §29–37 Ưu tiên đầu tiên: giao redact 6 file theo diff/backup; kiểm scan không còn match. Việc revoke key cần Admin riêng, không suy từ redact. DONE review T283 — Dọn chuỗi key trong docs/scripts Äá»§ Ä‘iá»u kiá»‡n dev; chá» Admin xÃ¡c nháºn." [ref=e25]':
          - 'rowheader "T283 — Dọn chuỗi key trong docs/scripts T283: pending Task T283" [ref=e26]':
            - strong [ref=e27]: T283 — Dọn chuỗi key trong docs/scripts
            - generic [ref=e28]: "T283: pending"
            - link "Task T283" [ref=e30] [cursor=pointer]:
              - /url: ../tasks/T283-m0-xoa-key-khoi-tai-lieu.md
          - cell "Code bảo mật; Debug kiểm độc lập" [ref=e31]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e32]
          - 'cell "Scan local chỉ tên file: 6 đường dẫn còn match; task cũ ghi 18. Chưa redact, không hiển thị chuỗi bí mật. PASS: Bản sửa đúng scope PASS: Tests/kiểm chứng acceptance PASS: Debug kiểm độc lập + root QA Scope T283 §29–37" [ref=e33]':
            - paragraph [ref=e34]: "Scan local chỉ tên file: 6 đường dẫn còn match; task cũ ghi 18. Chưa redact, không hiển thị chuỗi bí mật."
            - list [ref=e35]:
              - listitem [ref=e36]: "PASS: Bản sửa đúng scope"
              - listitem [ref=e37]: "PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e38]: "PASS: Debug kiểm độc lập + root QA"
            - link "Scope T283 §29–37" [ref=e40] [cursor=pointer]:
              - /url: ../tasks/T283-m0-xoa-key-khoi-tai-lieu.md
          - 'cell "Ưu tiên đầu tiên: giao redact 6 file theo diff/backup; kiểm scan không còn match. Việc revoke key cần Admin riêng, không suy từ redact." [ref=e41]'
          - 'cell "DONE review T283 — Dọn chuỗi key trong docs/scripts Äá»§ Ä‘iá»u kiá»‡n dev; chá» Admin xÃ¡c nháºn." [ref=e42]':
            - button "DONE review T283 — Dọn chuỗi key trong docs/scripts" [ref=e43]: DONE
            - generic [ref=e44]: "Ä\x90á»§ Ä‘iá»\x81u kiá»‡n dev; chá»\x9d Admin xÃ¡c nháºn."
```

# Test source

```ts
  1   | const { test, expect } = require('@playwright/test');
  2   | const fs = require('node:fs');
  3   | const path = require('node:path');
  4   | const base = path.resolve(__dirname, '..');
  5   | const html = fs.readFileSync(path.join(base, 'dashboard/dashboard_process.html'), 'utf8');
  6   | const panel = html.match(/<!-- T358:START[\s\S]*?<!-- T358:END -->/)[0];
  7   | const script = fs.readFileSync(path.join(base, 'dashboard/triage_execution.js'), 'utf8');
  8   | const css = fs.readFileSync(path.join(base, 'dashboard/triage_execution.css'), 'utf8');
  9   | const actualReport = JSON.parse(fs.readFileSync(path.join(base, 'data/triage_execution_report.json'), 'utf8'));
  10  | const actualProgress = JSON.parse(fs.readFileSync(path.join(base, 'data/progress_data.json'), 'utf8'));
  11  | const prefix = 'ptda:harness:admin-review:v1:';
  12  | const copy = value => JSON.parse(JSON.stringify(value));
  13  | function ready() {
  14  |   const report = copy(actualReport);
  15  |   report.rows = [report.rows.find(row => row.row_id === 'T283')];
  16  |   const row = report.rows[0];
  17  |   row.prerequisites = [];
  18  |   row.development.completed = true;
  19  |   row.development.checks.forEach(check => { check.passed = true; check.evidence = [{href: '../tasks/T283-m0-xoa-key-khoi-tai-lieu.md', label: 'Fixture proof only'}]; });
  20  |   return report;
  21  | }
  22  | async function mount(page, report = actualReport, progress = actualProgress) {
  23  |   const state = {report: copy(report), progress: copy(progress), fail: false, requests: []};
  24  |   await page.route('**/*', async route => {
  25  |     const request = route.request();
  26  |     state.requests.push({method: request.method(), url: request.url()});
  27  |     const pathname = new URL(request.url()).pathname;
  28  |     let body;
  29  |     let contentType = 'application/json';
  30  |     if (pathname === '/dashboard/dashboard_process.html') {
  31  |       contentType = 'text/html';
  32  |       body = '<!doctype html><html lang="vi"><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:16px;background:#020617;font-family:sans-serif}.hx-btn{padding:8px;border:1px solid #64748b;background:#0f172a;color:white}.hx-card{padding:12px;border:1px solid #334155;border-radius:12px;box-sizing:border-box}</style><link rel="stylesheet" href="triage_execution.css"><script src="triage_execution.js" defer></script></head><body>' + panel + '</body></html>';
  33  |     } else if (pathname === '/dashboard/triage_execution.js') {body = script; contentType = 'application/javascript';}
  34  |     else if (pathname === '/dashboard/triage_execution.css') {body = css; contentType = 'text/css';}
  35  |     else if (pathname === '/data/triage_execution_report.json') { if (state.fail) return route.fulfill({status: 503,body: '{}'}); body = JSON.stringify(state.report); }
  36  |     else if (pathname === '/data/progress_data.json') body = JSON.stringify(state.progress);
  37  |     else return route.abort();
  38  |     await route.fulfill({status: 200, contentType, body});
  39  |   });
  40  |   await page.goto('http://t358.fixture/dashboard/dashboard_process.html');
> 41  |   await expect(page.locator('#triageMessage')).toContainText('Báo cáo đã tải');
      |                                                ^ Error: expect(locator).toContainText(expected) failed
  42  |   return state;
  43  | }
  44  | async function confirm(page) {
  45  |   await page.getByRole('button', {name: 'DONE review T283', exact: false}).click();
  46  |   await page.locator('#triageConfirmInput').fill('T283');
  47  |   await page.locator('#triageConfirmSave').click();
  48  |   await expect(page.locator('#triageMessage')).toContainText('Đã lưu review cục bộ');
  49  | }
  50  | 
  51  | test('T358 actual source is integrated; audited report locks every incomplete row', async ({page}) => {
  52  |   expect(html).toContain('<script src="triage_execution.js" defer>');
  53  |   expect(html.indexOf('id="triageExecution"')).toBeGreaterThan(html.indexOf('id="hxRoot"'));
  54  |   expect(html.indexOf('id="triageExecution"')).toBeLessThan(html.indexOf('Tiến độ H3 —'));
  55  |   await page.addInitScript(() => localStorage.setItem('adminDone_T283', '1'));
  56  |   await mount(page);
  57  |   await expect(page.locator('#triageRows tr')).toHaveCount(15);
  58  |   for (const button of await page.locator('.triage-done').all()) await expect(button).toBeDisabled();
  59  |   await expect(page.locator('#triageRows')).toContainText('T22 → T22');
  60  |   await expect(page.locator('#triageRows')).toContainText('T50 → T73 → T59 → T53 → T50');
  61  |   expect(await page.evaluate(() => Object.keys(localStorage).filter(key => key.startsWith('ptda:harness:')))).toEqual([]);
  62  | });
  63  | 
  64  | test('DONE requires typed confirmation; cancel/Escape no write; persist only local review', async ({page}) => {
  65  |   const state = await mount(page, ready());
  66  |   const before = JSON.stringify(state.progress);
  67  |   const button = page.locator('.triage-done');
  68  |   await expect(button).toBeEnabled();
  69  |   await button.focus();
  70  |   await page.keyboard.press('Enter');
  71  |   await expect(page.locator('#triageConfirmInput')).toBeFocused();
  72  |   await page.locator('#triageConfirmInput').fill('done');
  73  |   await expect(page.locator('#triageConfirmSave')).toBeDisabled();
  74  |   await page.keyboard.press('Escape');
  75  |   await expect(page.locator('#triageConfirm')).not.toBeVisible();
  76  |   await expect(button).toBeFocused();
  77  |   expect(await page.evaluate(() => localStorage.length)).toBe(0);
  78  |   await button.click();
  79  |   await page.locator('#triageCancel').click();
  80  |   expect(await page.evaluate(() => localStorage.length)).toBe(0);
  81  |   await confirm(page);
  82  |   const stored = await page.evaluate(() => ({keys: Object.keys(localStorage), value: JSON.parse(localStorage.getItem('ptda:harness:admin-review:v1:T283'))}));
  83  |   expect(stored.keys).toEqual([prefix + 'T283']);
  84  |   expect(stored.value.review_status).toBe('admin_reviewed');
  85  |   expect(stored.value).not.toHaveProperty('task_status');
  86  |   expect(stored.value).not.toHaveProperty('status');
  87  |   expect(JSON.stringify(state.progress)).toBe(before);
  88  |   expect(state.requests.every(request => request.method === 'GET')).toBe(true);
  89  |   expect(state.requests.some(request => request.url.includes('/api/'))).toBe(false);
  90  |   await page.reload();
  91  |   await expect(button).toHaveText('Đã review cục bộ');
  92  |   await expect(button).toBeDisabled();
  93  | });
  94  | 
  95  | test('changed revision/evidence/prerequisite makes stored review stale', async ({page}) => {
  96  |   const state = await mount(page, ready());
  97  |   await confirm(page);
  98  |   state.report.revision = 'fixture-new-revision';
  99  |   await page.locator('#triageReload').click();
  100 |   await expect(page.locator('.triage-done')).toHaveText('DONE');
  101 |   await expect(page.locator('.triage-done')).toBeEnabled();
  102 |   state.report.rows[0].prerequisites = [{label: 'Blocked dependency', satisfied: false}];
  103 |   await page.locator('#triageReload').click();
  104 |   await expect(page.locator('.triage-done')).toBeDisabled();
  105 |   await expect(page.locator('#triageRows')).toContainText('Chưa đủ điều kiện trước');
  106 | });
  107 | 
  108 | test('readiness fails closed for missing QA/proof, false completion, blocked or ambiguous task', async ({page}) => {
  109 |   const state = await mount(page, ready());
  110 |   const cases = [
  111 |     report => report.rows[0].development.completed = false,
  112 |     report => report.rows[0].development.checks.pop(),
  113 |     report => report.rows[0].development.checks[0].evidence = [{href:'javascript:alert(1)',label:'fake'}],
  114 |     report => report.rows[0].development.checks.push({key:'extra',label:'extra',passed:false,evidence:[]})
  115 |   ];
  116 |   for (const mutate of cases) {
  117 |     state.report = ready(); mutate(state.report);
  118 |     await page.locator('#triageReload').click();
  119 |     await expect(page.locator('.triage-done')).toBeDisabled();
  120 |   }
  121 |   state.report = ready();
  122 |   state.progress.tasks.find(task => task.id === 'T283').status = 'blocked';
  123 |   await page.locator('#triageReload').click();
  124 |   await expect(page.locator('.triage-done')).toBeDisabled();
  125 |   state.progress = copy(actualProgress);
  126 |   state.progress.tasks.push(copy(state.progress.tasks.find(task => task.id === 'T283')));
  127 |   await page.locator('#triageReload').click();
  128 |   await expect(page.locator('.triage-done')).toBeDisabled();
  129 |   await expect(page.locator('#triageRows')).toContainText('ID thiếu hoặc trùng');
  130 | });
  131 | 
  132 | test('untrusted report text and links are inert', async ({page}) => {
  133 |   const report = ready();
  134 |   report.rows[0].title = '<img src=x onerror="window.t358Xss=1">';
  135 |   report.rows[0].development.summary = '<script>window.t358Xss=2</script>';
  136 |   report.rows[0].evidence = [{href:'javascript:window.t358Xss=3',label:'<svg onload="window.t358Xss=4">'},{href:'../docs/../../outside.html',label:'escape'}];
  137 |   await mount(page, report);
  138 |   expect(await page.evaluate(() => window.t358Xss)).toBeUndefined();
  139 |   await expect(page.locator('#triageRows img, #triageRows svg, #triageRows script')).toHaveCount(0);
  140 |   await expect(page.locator('#triageRows a[href^="javascript:"]')).toHaveCount(0);
  141 |   await expect(page.locator('#triageRows')).toContainText('<img src=x');
```