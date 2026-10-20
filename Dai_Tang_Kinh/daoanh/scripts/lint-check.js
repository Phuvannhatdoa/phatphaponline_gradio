#!/usr/bin/env node
/**
 * T391: Lint script cross-platform (thay cho scripts/lint-check.ps1).
 *
 * Ly do: `npm run lint` truoc day goi PowerShell truc tiep
 * ("powershell -ExecutionPolicy Bypass -File scripts/lint-check.ps1"),
 * chi chay duoc tren Windows. GitHub Actions deploy.yml dung
 * runs-on: ubuntu-latest -> khong co PowerShell -> buoc lint se fail
 * ngay khi duoc goi trong CI.
 *
 * Script nay giu nguyen logic cua lint-check.ps1 (kiem tra cu phap JS
 * trong cac the <script> inline cua 5 file admin HTML, bo qua block JSX),
 * nhung viet bang Node.js de chay duoc tren moi OS (Windows/Linux/macOS).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

const adminDir = path.join(process.cwd(), 'admin');

const checkFiles = [
  'placevn.html',
  'index.html',
  'zenlineage_review.html',
  'dila_person_index.html',
  'person.html',
];

// Regex khop the <script ...> khong co src=
const scriptOpenRe = /<script(?![^>]*\bsrc\s*=)[^>]*>/gi;
const jsxSkipRe = /dangerouslySetInnerHTML|return\s+<[A-Za-z]/;

let passed = 0;
let failed = 0;

console.log('Running lint checks...');

for (const filename of checkFiles) {
  const htmlFile = path.join(adminDir, filename);
  if (!fs.existsSync(htmlFile)) {
    console.log(`  WARN ${filename} not found, skipping`);
    continue;
  }

  console.log(`Checking ${filename}...`);
  const content = fs.readFileSync(htmlFile, 'utf8');

  let scriptIdx = 0;
  let match;
  scriptOpenRe.lastIndex = 0;
  while ((match = scriptOpenRe.exec(content)) !== null) {
    scriptIdx += 1;
    const start = match.index + match[0].length;
    const remaining = content.slice(start);
    const endIdx = remaining.indexOf('</script>');
    if (endIdx < 0) continue;
    const jsCode = remaining.slice(0, endIdx);

    if (jsxSkipRe.test(jsCode)) {
      console.log(`  Script block ${scriptIdx}: JSX (skip)`);
      passed += 1;
      continue;
    }

    const tmpFile = path.join(
      os.tmpdir(),
      `lint_${Date.now()}_${Math.random().toString(16).slice(2)}.js`
    );
    try {
      fs.writeFileSync(tmpFile, jsCode, 'utf8');
      const result = spawnSync(process.execPath, ['--check', tmpFile], {
        encoding: 'utf8',
      });
      if (result.status === 0) {
        console.log(`  Script block ${scriptIdx}: Syntax OK`);
        passed += 1;
      } else {
        console.log(`  Script block ${scriptIdx}: Syntax error`);
        if (result.stderr) console.log(result.stderr.split('\n').slice(0, 5).join('\n'));
        failed += 1;
      }
    } catch (err) {
      console.log(`  Script block ${scriptIdx}: node error: ${err.message}`);
      failed += 1;
    } finally {
      if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
    }
  }

  if (scriptIdx === 0) {
    console.log('  No inline script blocks found');
  }
}

console.log('');
if (failed === 0) {
  console.log(`Lint checks passed (${passed} script blocks validated)`);
  process.exit(0);
} else {
  console.log('Lint checks failed');
  process.exit(1);
}
