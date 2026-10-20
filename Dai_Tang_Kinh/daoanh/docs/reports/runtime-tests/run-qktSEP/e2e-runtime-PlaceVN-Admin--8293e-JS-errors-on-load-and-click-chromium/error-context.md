# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e-runtime.spec.js >> PlaceVN Admin - Runtime Error Check >> placevn.html - no JS errors on load and click
- Location: tests\e2e-runtime.spec.js:45:5

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5000/daoanh/admin/placevn.html
Call log:
  - navigating to "http://localhost:5000/daoanh/admin/placevn.html", waiting until "networkidle"

```

# Test source

```ts
  1   | // tests/e2e-runtime.spec.js
  2   | // Playwright E2E test - catches RUNTIME JavaScript errors
  3   | 
  4   | const { test, expect } = require('@playwright/test');
  5   | 
  6   | test.describe('PlaceVN Admin - Runtime Error Check', () => {
  7   |     let pageErrors = [];
  8   | 
  9   |     test.beforeEach(async ({ page }) => {
  10  |         pageErrors = [];
  11  |         
  12  |         // Capture ALL console messages
  13  |         page.on('console', msg => {
  14  |             if (msg.type() === 'error') {
  15  |                 pageErrors.push({
  16  |                     type: 'console.error',
  17  |                     text: msg.text(),
  18  |                     location: msg.location()
  19  |                 });
  20  |                 console.log('❌ Console error:', msg.text());
  21  |             }
  22  |         });
  23  |         
  24  |         // Capture JS exceptions
  25  |         page.on('pageerror', error => {
  26  |             pageErrors.push({
  27  |                 type: 'pageerror',
  28  |                 text: error.message,
  29  |                 stack: error.stack
  30  |             });
  31  |             console.log('❌ Page error:', error.message);
  32  |         });
  33  |         
  34  |         // Capture request failures
  35  |         page.on('requestfailed', request => {
  36  |             pageErrors.push({
  37  |                 type: 'requestfailed',
  38  |                 url: request.url(),
  39  |                 failure: request.failure()
  40  |             });
  41  |             console.log('❌ Request failed:', request.url());
  42  |         });
  43  |     });
  44  | 
  45  |     test('placevn.html - no JS errors on load and click', async ({ page }, testInfo) => {
  46  |         console.log('🚀 Testing placevn.html...');
  47  |         
  48  |         // Go to page
> 49  |         const response = await page.goto('http://localhost:5000/daoanh/admin/placevn.html', {
      |                                     ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5000/daoanh/admin/placevn.html
  50  |             waitUntil: 'networkidle',
  51  |             timeout: 30000
  52  |         });
  53  |         
  54  |         expect(response.status()).toBe(200);
  55  |         console.log('✅ Page loaded');
  56  |         
  57  |         // Wait for page to stabilize
  58  |         await page.waitForTimeout(2000);
  59  |         
  60  |         // Check NO errors so far
  61  |         const errorsBefore = pageErrors.filter(e => e.type === 'pageerror' || e.type === 'console.error');
  62  |         if (errorsBefore.length > 0) {
  63  |             console.log('❌ Errors on page load:', errorsBefore);
  64  |         }
  65  |         expect(errorsBefore.length).toBe(0);
  66  |         
  67  |         // Take screenshot
  68  |         await page.screenshot({ path: testInfo.outputPath('placevn-load.png'), fullPage: true });
  69  |         console.log('📷 Screenshot saved');
  70  |         
  71  |         // Click "Mapping Tên Việt" button (text-based selector)
  72  |         const mappingBtn = page.getByText('Mapping Tên Việt');
  73  |         if (await mappingBtn.isVisible().catch(() => false)) {
  74  |             console.log('🖱️ Clicking Mapping Tên Việt...');
  75  |             await mappingBtn.click();
  76  |             await page.waitForTimeout(3000);
  77  |             
  78  |             // Check for errors after click
  79  |             const errorsAfterClick = pageErrors.filter(e => e.type === 'pageerror' || e.type === 'console.error');
  80  |             if (errorsAfterClick.length > 0) {
  81  |                 console.log('❌ Errors after clicking Mapping:', errorsAfterClick);
  82  |             }
  83  |             expect(errorsAfterClick.length).toBe(0);
  84  |             console.log('✅ No errors after click');
  85  |             
  86  |             // Take screenshot
  87  |             await page.screenshot({ path: testInfo.outputPath('placevn-mapping.png'), fullPage: true });
  88  |         } else {
  89  |             console.log('⚠️ Mapping Tên Việt button not found');
  90  |         }
  91  |         
  92  |         // Final check - no errors at all
  93  |         const allErrors = pageErrors.filter(e => e.type === 'pageerror' || e.type === 'console.error');
  94  |         if (allErrors.length > 0) {
  95  |             console.log('\n❌❌❌ RUNTIME ERRORS FOUND:');
  96  |             allErrors.forEach((e, i) => {
  97  |                 console.log(`  ${i+1}. [${e.type}] ${e.text}`);
  98  |                 if (e.location) console.log(`     at ${e.location.url}:${e.location.lineNumber}`);
  99  |             });
  100 |         }
  101 |         expect(allErrors.length).toBe(0);
  102 |     });
  103 | 
  104 |     test('placevn.html - API returns valid JSON', async ({ page }) => {
  105 |         console.log('🔍 Testing API endpoints...');
  106 |         
  107 |         const apiErrors = [];
  108 |         
  109 |         // Intercept API calls
  110 |         page.on('response', async response => {
  111 |             const url = response.url();
  112 |             if (url.includes('/api/') && response.status() !== 200) {
  113 |                 apiErrors.push({
  114 |                     url: url,
  115 |                     status: response.status(),
  116 |                     body: await response.text().catch(() => 'Cannot read')
  117 |                 });
  118 |                 console.log(`❌ API error: ${url} - ${response.status()}`);
  119 |             }
  120 |         });
  121 |         
  122 |         await page.goto('http://localhost:5000/daoanh/admin/placevn.html', {
  123 |             waitUntil: 'networkidle',
  124 |             timeout: 30000
  125 |         });
  126 |         
  127 |         await page.waitForTimeout(2000);
  128 |         
  129 |         // Click Mapping button to trigger API call
  130 |         const mappingBtn2 = page.getByText('Mapping Tên Việt');
  131 |         if (await mappingBtn2.isVisible().catch(() => false)) {
  132 |             await mappingBtn2.click();
  133 |             await page.waitForTimeout(3000);
  134 |         }
  135 |         
  136 |         if (apiErrors.length > 0) {
  137 |             console.log('\n❌❌❌ API ERRORS:');
  138 |             apiErrors.forEach((e, i) => {
  139 |                 console.log(`  ${i+1}. ${e.url}`);
  140 |                 console.log(`     Status: ${e.status}`);
  141 |                 console.log(`     Body: ${e.body.substring(0, 100)}`);
  142 |             });
  143 |         }
  144 |         
  145 |         expect(apiErrors.length).toBe(0);
  146 |     });
  147 | });
  148 | 
```