// tests/e2e-runtime.spec.js
// Playwright E2E test - catches RUNTIME JavaScript errors

const { test, expect } = require('@playwright/test');

test.describe('PlaceVN Admin - Runtime Error Check', () => {
    let pageErrors = [];

    test.beforeEach(async ({ page }) => {
        pageErrors = [];
        
        // Capture ALL console messages
        page.on('console', msg => {
            if (msg.type() === 'error') {
                pageErrors.push({
                    type: 'console.error',
                    text: msg.text(),
                    location: msg.location()
                });
                console.log('❌ Console error:', msg.text());
            }
        });
        
        // Capture JS exceptions
        page.on('pageerror', error => {
            pageErrors.push({
                type: 'pageerror',
                text: error.message,
                stack: error.stack
            });
            console.log('❌ Page error:', error.message);
        });
        
        // Capture request failures
        page.on('requestfailed', request => {
            pageErrors.push({
                type: 'requestfailed',
                url: request.url(),
                failure: request.failure()
            });
            console.log('❌ Request failed:', request.url());
        });
    });

    test('placevn.html - no JS errors on load and click', async ({ page }) => {
        console.log('🚀 Testing placevn.html...');
        
        // Go to page
        const response = await page.goto('http://localhost:5000/daoanh/admin/placevn.html', {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        expect(response.status()).toBe(200);
        console.log('✅ Page loaded');
        
        // Wait for page to stabilize
        await page.waitForTimeout(2000);
        
        // Check NO errors so far
        const errorsBefore = pageErrors.filter(e => e.type === 'pageerror' || e.type === 'console.error');
        if (errorsBefore.length > 0) {
            console.log('❌ Errors on page load:', errorsBefore);
        }
        expect(errorsBefore.length).toBe(0);
        
        // Take screenshot
        await page.screenshot({ path: 'tests/screenshots/placevn-load.png', fullPage: true });
        console.log('📷 Screenshot saved');
        
        // Click "Mapping Tên Việt" button (text-based selector)
        const mappingBtn = page.getByText('Mapping Tên Việt');
        if (await mappingBtn.isVisible().catch(() => false)) {
            console.log('🖱️ Clicking Mapping Tên Việt...');
            await mappingBtn.click();
            await page.waitForTimeout(3000);
            
            // Check for errors after click
            const errorsAfterClick = pageErrors.filter(e => e.type === 'pageerror' || e.type === 'console.error');
            if (errorsAfterClick.length > 0) {
                console.log('❌ Errors after clicking Mapping:', errorsAfterClick);
            }
            expect(errorsAfterClick.length).toBe(0);
            console.log('✅ No errors after click');
            
            // Take screenshot
            await page.screenshot({ path: 'tests/screenshots/placevn-mapping.png', fullPage: true });
        } else {
            console.log('⚠️ Mapping Tên Việt button not found');
        }
        
        // Final check - no errors at all
        const allErrors = pageErrors.filter(e => e.type === 'pageerror' || e.type === 'console.error');
        if (allErrors.length > 0) {
            console.log('\n❌❌❌ RUNTIME ERRORS FOUND:');
            allErrors.forEach((e, i) => {
                console.log(`  ${i+1}. [${e.type}] ${e.text}`);
                if (e.location) console.log(`     at ${e.location.url}:${e.location.lineNumber}`);
            });
        }
        expect(allErrors.length).toBe(0);
    });

    test('placevn.html - API returns valid JSON', async ({ page }) => {
        console.log('🔍 Testing API endpoints...');
        
        const apiErrors = [];
        
        // Intercept API calls
        page.on('response', async response => {
            const url = response.url();
            if (url.includes('/api/') && response.status() !== 200) {
                apiErrors.push({
                    url: url,
                    status: response.status(),
                    body: await response.text().catch(() => 'Cannot read')
                });
                console.log(`❌ API error: ${url} - ${response.status()}`);
            }
        });
        
        await page.goto('http://localhost:5000/daoanh/admin/placevn.html', {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        await page.waitForTimeout(2000);
        
        // Click Mapping button to trigger API call
        const mappingBtn2 = page.getByText('Mapping Tên Việt');
        if (await mappingBtn2.isVisible().catch(() => false)) {
            await mappingBtn2.click();
            await page.waitForTimeout(3000);
        }
        
        if (apiErrors.length > 0) {
            console.log('\n❌❌❌ API ERRORS:');
            apiErrors.forEach((e, i) => {
                console.log(`  ${i+1}. ${e.url}`);
                console.log(`     Status: ${e.status}`);
                console.log(`     Body: ${e.body.substring(0, 100)}`);
            });
        }
        
        expect(apiErrors.length).toBe(0);
    });
});
