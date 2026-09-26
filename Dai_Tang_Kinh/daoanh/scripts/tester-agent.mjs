#!/usr/bin/env node
/**
 * TESTER AGENT - Full Pipeline (Lint + E2E + Runtime)
 * Runs ALL checks and reports PASS/FAIL properly
 */

import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = join(__dirname, '..');

console.log('\n🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔');
console.log('🚀 TESTER AGENT STARTING (FULL PIPELINE)');
console.log('🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔\n');

const results = {
  lint: { passed: false, output: '' },
  test: { passed: false, output: '' },
  e2e: { passed: false, output: '' },
  runtime: { passed: false, output: '' }
};

// Run LINT
console.log('============================================================');
console.log('📋 Running: LINT');
console.log('📝 Description: Check JavaScript syntax and style');
console.log('============================================================\n');

try {
  results.lint.output = execSync('npm run lint', {
    cwd: ROOT_DIR,
    encoding: 'utf-8',
    timeout: 60000
  });
  results.lint.passed = true;
  console.log('✅ lint PASSED\n');
} catch (err) {
  results.lint.output = err.stdout || err.message;
  console.log('❌ lint FAILED\n');
  console.log(err.stdout || err.message);
}

// Run TEST
console.log('============================================================');
console.log('📋 Running: TEST');
console.log('📝 Description: Run unit/integration tests');
console.log('============================================================\n');

try {
  results.test.output = execSync('npm run test', {
    cwd: ROOT_DIR,
    encoding: 'utf-8',
    timeout: 60000
  });
  results.test.passed = true;
  console.log('✅ test PASSED\n');
} catch (err) {
  results.test.output = err.stdout || err.message;
  console.log('❌ test FAILED\n');
  console.log(err.stdout || err.message);
}

// Run E2E (static)
console.log('============================================================');
console.log('📋 Running: E2E (Static)');
console.log('📝 Description: Check HTML/JS errors (static analysis)');
console.log('============================================================\n');

try {
  results.e2e.output = execSync('npm run e2e', {
    cwd: ROOT_DIR,
    encoding: 'utf-8',
    timeout: 60000
  });
  results.e2e.passed = true;
  console.log('✅ e2e PASSED\n');
} catch (err) {
  results.e2e.output = err.stdout || err.message;
  console.log('❌ e2e FAILED\n');
  console.log(err.stdout || err.message);
}

// Run E2E (runtime with Playwright)
console.log('============================================================');
console.log('📋 Running: E2E (Runtime with Playwright)');
console.log('📝 Description: Catch RUNTIME JS errors in browser');
console.log('============================================================\n');

try {
  results.runtime.output = execSync('npm run e2e:runtime', {
    cwd: ROOT_DIR,
    encoding: 'utf-8',
    timeout: 120000
  });
  results.runtime.passed = true;
  console.log('✅ e2e:runtime PASSED\n');
} catch (err) {
  results.runtime.output = err.stdout || err.message;
  console.log('❌ e2e:runtime FAILED\n');
  console.log(err.stdout || err.message);
}

// Summary
console.log('\n============================================================');
console.log('📊 TESTER AGENT SUMMARY');
console.log('============================================================\n');

const passed = Object.values(results).filter(r => r.passed).length;
const failed = Object.values(results).filter(r => !r.passed).length;
const total = Object.keys(results).length;

console.log(`✅ Passed (${passed}/${total}): ${Object.entries(results).filter(([_, r]) => r.passed).map(([name]) => name).join(', ')}`);
if (failed > 0) {
  console.log(`❌ Failed (${failed}/${total}): ${Object.entries(results).filter(([_, r]) => !r.passed).map(([name]) => name).join(', ')}`);
}

console.log('\n============================================================');

if (passed === total) {
  console.log('\n🎉 ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅');
  console.log('   ALL TESTS PASSED, READY FOR REVIEW!');
  console.log('   ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅\n');
  console.log('🔔 NOTIFICATION: BEEP BEEP! Code is ready for review! 🔔');
  process.exit(0);
} else {
  console.log('\n❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌');
  console.log('   SOME TESTS FAILED!');
  console.log('   Please fix errors above and run again before asking for review.');
  console.log('   ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌\n');
  console.log('🔔 NOTIFICATION: BEEP BEEP! Tests FAILED! Fix errors! 🔔');
  process.exit(1);
}
