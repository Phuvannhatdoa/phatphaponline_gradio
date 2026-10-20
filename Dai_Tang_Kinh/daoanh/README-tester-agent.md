# Tester Agent System

## 🚀 Quick Start

Before requesting review from admin, **MUST** run tester agent:

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

Or using OpenCode:
```
/test
```

## ✅ What Tester Agent Checks

1. **Lint**: JavaScript syntax and style (ESLint)
2. **Test**: Unit/integration tests
3. **E2E**: End-to-end tests (check for JS console errors in HTML pages)

## 📋 Output Example

```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
🚀 TESTER AGENT STARTING
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔

============================================================
📋 Running: LINT
📝 Description: Check JavaScript syntax and style (ESLint)
💻 Command: npm run lint
============================================================

✅ lint PASSED

============================================================
📋 Running: TEST
📝 Description: Run unit/integration tests
💻 Command: npm run test
============================================================

✅ test PASSED

============================================================
📋 Running: E2E
📝 Description: End-to-end tests (check for JS console errors)
💻 Command: npm run e2e
============================================================

✅ e2e PASSED

============================================================
📊 TESTER AGENT SUMMARY
============================================================
✅ Passed (3/3): lint, test, e2e
❌ Failed (0/3): none
============================================================

🎉 ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
   ALL TESTS PASSED, READY FOR REVIEW!
   ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
```

## ❌ If Tests Fail

```
❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌
   SOME TESTS FAILED!
   Please fix errors above and run again before asking for review.
   ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌
```

## 📂 Files Created

```
package.json          - Updated with lint, test, e2e, tester:agent scripts
scripts/tester-agent.mjs     - Main tester agent script
scripts/e2e-test.js          - E2E tests (check HTML/JS errors)
.opencode/plugins/tester-agent.js - OpenCode plugin (optional)
README-tester-agent.md       - This file
```

## 🔧 Technical Details

- **Lint**: Uses ESLint (or basic syntax check with `node -e`)
- **Test**: Runs unit tests (placeholder created if none exist)
- **E2E**: Checks HTML pages for JS syntax errors and inline event handlers
- **OpenCode Plugin**: Registers `/test` command (if plugin API available)

## 📝 Workflow Rule

1. Developer makes changes
2. Run `npm run tester:agent` (or `/test` in OpenCode)
3. If all pass → Request review from admin
4. If any fail → Fix errors → Run again
5. Admin ONLY reviews when "All tests passed" is shown

**NO EXCEPTIONS!** 🚫

## 🛠️ Manual Commands

If you want to run individual checks:

```bash
npm run lint    # Check JavaScript syntax
npm run test    # Run unit tests
npm run e2e     # Run end-to-end tests
npm run tester:agent  # Run all three
```

## 🔍 Example Error Output

If lint fails:
```
============================================================
📋 Running: LINT
============================================================

❌ lint FAILED (exit code: 1)

/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/admin/placevn.html
  123:15  error  Missing catch or finally after try

❌ lint FAILED (exit code: 1)
```

Fix the error and run again!
