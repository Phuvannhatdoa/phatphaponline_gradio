---
name: qa-web-session-logger
description: >
  QA Session Logger for web testing with persistent bug tracking (NEW / UNDONE / DONE),
  designed for session-based QA in the Đại Tạng Kinh Puzzle Ecosystem.
---

# 🧠 CORE PURPOSE

This skill enables QA agent to:

- Run **session-based QA testing**
- Track bug lifecycle across sessions:
  - NEW → UNDONE → DONE
- Maintain persistent QA memory via `.md` logs
- Avoid redundant re-testing
- Produce structured outputs usable by @Plant and @Code

---

# 🚨 AUTO-TRIGGER CONDITIONS

Agent MUST activate this skill when:

- User mentions:
  - "QA", "test web", "bug report", "feedback"
  - "check lại", "recheck", "QA session"
- Or input includes:
  - `QA1.md`, `QA2.md`, `QA3.md`
- Or instruction:
  - "@QA run test", "@General act as QA"

---

# 📂 REQUIRED FILES

- `QA.md` OR `QA_LOGS.md` (persistent log)
- Optional:
  - `QA1.md`, `QA2.md`, `QA3.md` (session snapshots)

---

# 🔄 QA WORKFLOW (MANDATORY)

## STEP 1 — LOAD HISTORY

1. Read QA log file
2. Extract:

### DONE_IDS
- All bugs marked `DONE` or `IMPLEMENTED`

### ACTIVE_IDS
- All bugs marked `UNDONE` or `PENDING`

---

## STEP 2 — DEFINE CONTEXT

Set:

- Scope (what to test)
- Build version (if known)
- Priority areas:
  - ACTIVE bugs
  - Recently modified modules

---

## STEP 3 — QUICK TEST PLAN

Agent internally defines:

- 3–7 main flows
- Each flow:
  - 1–3 happy paths
  - 1–2 edge cases

---

## STEP 4 — EXECUTE TEST

For each issue:

---

### 🐞 BUG FORMAT
