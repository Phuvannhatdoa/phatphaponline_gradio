
---

## 0. TASKTODO — Session Continuation Protocol

### Save tasktodo to memory
```bash
# After finishing a session, always run:
curl -s -X POST http://127.0.0.1:37700/api/sessions/observations \
  -H "Content-Type: application/json" \
  -d '{"contentSessionId":"daoanh-master","tool_name":"tasktodo","tool_input":{},"tool_response":"{\"current_task\":\"<task_name>\",\"status\":\"<done|in_progress|pending>\",\"next_task\":\"<next_task_name>\"}","cwd":"/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"}'
```

### Load tasktodo command
When user says `tasktodo`, the agent MUST:
1. Search claude-mem: `curl -s "http://127.0.0.1:37700/api/search/observations?query=tasktodo&limit=3"`
2. Read `docs/tasktodo.md` for full context
3. Read latest session logs: `ls -t docs/sessions/ | head -3`
4. Read git log: `git log --oneline -5`
5. Report current state + suggest next action

### Active Task List (auto-maintained in docs/tasktodo.md)
See `docs/tasktodo.md` for the authoritative task list.

### Commit Convention
```
<type>: <short description> + docs
```
Types: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `refactor`, `test`, `chore`

Always include `+ docs` in message if docs/sessions/ was updated.

---

## 10. Server Architecture (Post-Split 2026-05-14)

### Two-Server Setup

| Server | File | Port | Role |
|--------|------|------|------|
| **Auth Gateway** | `server.py` | **5001** | Login only (Gmail check, session mgmt, admin emails) |
| **Main Server** | `app.py` | **5000** | All business logic (Đạo Ảnh, TTL, Marcus, dossier, translation) |

### Run Commands

```bash
# Auth Gateway (login)
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python server.py        # port 5001

# Main Server (Đạo Ảnh + all APIs)
python app.py           # port 5000
```

### Route Ownership

| Path Prefix | Handled By |
|-------------|-----------|
| `/daoanh/login.html` | server.py:5001 |
| `/daoanh/api/login/*` | server.py:5001 |
| `/api/admin/emails` | server.py:5001 |
| `/daoanh/admin/` → placevn.html | app.py:5000 |
| `/daoanh/panorama/` → panorama.html | app.py:5000 |
| `/daoanh/api/admin/*` | app.py:5000 |
| `/daoanh/api/public/*` | app.py:5000 |
| `/daoanh/static/*` | app.py:5000 |
| `/api/*` (TTL, Marcus, dossier, etc.) | app.py:5000 |

### Key Changes
- server.py stripped from ~2,800 lines → ~125 lines (login only)
- app.py expanded from 429 lines → ~2,600 lines (all business logic)
- `/daoanh/admin/` now serves `placevn.html` (Đạo Ảnh mapping)
- `/daoanh/panorama/` serves `panorama.html` (TTL ontology)
- Nginx must route `/daoanh/api/login/*` to port 5001, everything else to port 5000

## 11. Tester Agent System (Mandatory Before Review)

### 🚀 Quick Start
Before requesting review from admin, **MUST** run tester agent:

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

Or using OpenCode:
```
/test
```

### ✅ What Tester Agent Checks
1. **Lint**: JavaScript syntax and style (ESLint)
2. **Test**: Unit/integration tests
3. **E2E**: End-to-end tests (check for JS console errors in HTML pages)

### 📋 Output Example
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
🚀 TESTER AGENT STARTING
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔

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

🎉 ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
   ALL TESTS PASSED, READY FOR REVIEW!
   ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
```

### ❌ If Tests Fail
```
❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌
   SOME TESTS FAILED!
   Please fix errors above and run again before asking for review.
   ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌
```

### 📂 Files Created
```
package.json          - Updated with lint, test, e2e, tester:agent scripts
scripts/tester-agent.mjs     - Main tester agent script
scripts/e2e-test.js          - E2E tests (check HTML/JS errors)
.opencode/plugins/tester-agent.js - OpenCode plugin (optional)
```

### 🔧 Technical Details
- **Lint**: Uses ESLint (or basic syntax check with `node -e`)
- **Test**: Runs unit tests (placeholder created if none exist)
- **E2E**: Checks HTML pages for JS syntax errors and inline event handlers
- **OpenCode Plugin**: Registers `/test` command (if plugin API available)

### 📝 Workflow Rule
1. Developer makes changes
2. Run `npm run tester:agent` (or `/test` in OpenCode)
3. If all pass → Request review from admin
4. If any fail → Fix errors → Run again
5. Admin ONLY reviews when "All tests passed" is shown

**NO EXCEPTIONS!** 🚫

---


---

## 12. Quick Command Reference for Tester Agent

### 🚀 For Devs (MUST run before review):

**Option 1: Full pipeline (recommended)**
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run pipeline
```

**Option 2: Tester agent only**
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

**Option 3: Global command (run from anywhere)**
```bash
tester-agent
```

### 📋 What Each Command Does:

| Command | Description | Expected Output |
|----------|-------------|-------------------|
| `npm run lint` | Check JS syntax in all HTML files | ✅ All lint checks passed! |
| `npm run test` | Run unit/integration tests | ✅ Tests passed! |
| `npm run e2e` | Check HTML pages for JS errors | ✅ All pages passed E2E checks! |
| `npm run tester:agent` | Run all 3 steps above | ✅ ALL TESTS PASSED, READY FOR REVIEW! |
| `npm run pipeline` | Run lint + test + e2e | ✅ PIPELINE COMPLETE: All checks passed! |
| `tester-agent` | Same as `npm run tester:agent` | ✅ ALL TESTS PASSED, READY FOR REVIEW! |

### 🎯 Workflow:

1. **Make changes** to code
2. **Run tester**: `npm run pipeline` or `tester-agent`
3. **If ✅ PASSED**: Request review from admin
4. **If ❌ FAILED**: Fix errors shown, run again
5. **Admin ONLY reviews** when "All tests passed" is shown

### 📝 Example Output (Success):

```
✅ LINT: All syntax checks PASSED!
✅ TEST: Tests passed!
✅ E2E: All pages passed E2E checks!

🎉 ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
   ALL TESTS PASSED, READY FOR REVIEW!
   ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
```

### 📂 Files Created for Tester Agent:

```
package.json              - Updated with lint, test, e2e, tester:agent, pipeline
scripts/tester-agent.mjs     - Main tester script (ES module)
scripts/e2e-test.js          - E2E checks (HTML/JS errors)
scripts/lint-check.sh        - Bash script for JS syntax check
.opencode/plugins/tester-agent.js - OpenCode plugin (optional)
README-tester-agent.md       - Documentation
AGENTS.md                - Updated with workflow + commands
```

**NO EXCEPTIONS!** 🚫
- Devs MUST run `npm run pipeline` before requesting review
- Admin ONLY reviews when tests pass
- Fix errors and re-run until "All tests passed"

---

