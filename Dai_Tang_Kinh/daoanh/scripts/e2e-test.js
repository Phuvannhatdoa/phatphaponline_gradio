#!/usr/bin/env node
/**
 * E2E Test Script - Check for JavaScript errors in HTML pages
 * Run with: node scripts/e2e-test.js
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const projectRoot = path.join(__dirname, '..');

// Pages to test
const pages = [
  { name: "placevn.html", path: "admin/placevn.html" },
  { name: "index.html", path: "admin/index.html" },
  { name: "dashboard_process.html", path: "dashboard/dashboard_process.html" }
];

let hasErrors = false;

function testPage(page) {
  console.log(`\n📋 Testing: ${page.name}`);
  console.log(`📂 Path: ${page.path}`);
  
  try {
    const fullPath = path.join(projectRoot, page.path);
    
    if (!fs.existsSync(fullPath)) {
      console.error(`❌ File not found: ${fullPath}`);
      return false;
    }
    
    const htmlContent = fs.readFileSync(fullPath, 'utf8');
    
    // Match ONLY inline script tags (not external scripts with src), skip text/babel (JSX)
    const scriptRegex = /<script(?![^>]*\bsrc\s*=[^>]*>)(?!\s*type\s*=\s*["']text\/babel["'])([\s\S]*?)<\/script>/g;
    const matches = htmlContent.match(scriptRegex) || [];
    
    if (matches.length === 0) {
      console.log(`⚠️  No inline script tags found in ${page.name}`);
      return true;
    }
    
    let pageHasErrors = false;
    
    matches.forEach((script, index) => {
      const jsMatch = script.match(/<script[^>]*>([\s\S]*?)<\/script>/);
      
      if (jsMatch && jsMatch[1]) {
        const jsCode = jsMatch[1];
        
        try {
          // Write to temp file and use node --check for syntax validation
          const tmpFile = path.join(os.tmpdir(), `e2e-check-${Date.now()}-${index}.js`);
          fs.writeFileSync(tmpFile, jsCode);
          
          try {
            execSync(`node --check "${tmpFile}" 2>&1`, { stdio: "pipe" });
            console.log(`  ✅ Script block ${index + 1}: Syntax OK`);
          } catch (checkErr) {
            const errorOutput = checkErr.stderr ? checkErr.stderr.toString() : checkErr.message;
            console.error(`  ❌ Script block ${index + 1}: Syntax error`);
            console.error(`     ${errorOutput.split("\n")[0]}`);
            pageHasErrors = true;
            hasErrors = true;
          } finally {
            // Clean up temp file
            try { fs.unlinkSync(tmpFile); } catch(e) {}
          }
        } catch (err) {
          console.error(`  ❌ Script block ${index + 1}: Check error - ${err.message}`);
          pageHasErrors = true;
          hasErrors = true;
        }
      }
    });
    
    // Check for inline event handlers (should use addEventListener)
    const inlineOnclick = htmlContent.match(/onclick\s*=/g);
    if (inlineOnclick && inlineOnclick.length > 0) {
      console.warn(`  ⚠️  Found ${inlineOnclick.length} inline onclick handler(s). Consider using addEventListener.`);
    }
    
    if (!pageHasErrors) {
      console.log(`✅ ${page.name}: All checks passed`);
    }
    
    return !pageHasErrors;
  } catch (err) {
    console.error(`❌ Error testing ${page.name}: ${err.message}`);
    hasErrors = true;
    return false;
  }
}

function main() {
  console.log(`\n${"🔍".repeat(20)}`);
  console.log(`🚀 E2E TESTING STARTING`);
  console.log(`${"🔍".repeat(20)}\n`);
  
  console.log(`📂 Project root: ${projectRoot}\n`);
  
  for (const page of pages) {
    testPage(page);
  }
  
  console.log(`\n${"=".repeat(60)}`);
  console.log(`📊 E2E TEST SUMMARY`);
  console.log(`${"=".repeat(60)}`);
  
  if (hasErrors) {
    console.error(`\n❌ Some pages have errors. Please fix before review.\n`);
    process.exit(1);
  } else {
    console.log(`\n✅ All pages passed E2E checks!\n`);
    process.exit(0);
  }
}

main().catch((err) => {
  console.error("Unexpected error:", err);
  process.exit(1);
});
