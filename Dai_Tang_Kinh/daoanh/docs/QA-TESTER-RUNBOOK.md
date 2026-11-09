# QA-TESTER-RUNBOOK — OpenCode QA Workflow Guide

## Overview
This document defines the **@tester** QA workflow for validating code changes introduced by OpenCode Developers. It provides step‑by‑step instructions for running validation and interpreting reports.

## When to Use This Book
You are an OpenCode Developer who has just created a DEV‑REPORT (`docs/sessions/<YYYY-MM-DD>_<Txxx>‑<title>/DEV-REPORT.md`) for a task defined in `docs/tasktodo.md`. The next required step is to have the code validated by an independent QA agent (`@tester`) before the task can be approved for commit.

## Preparation Steps
1. **Ensure a DEV‑REPORT exists** – created by you (OpenCode Developer) after finishing code changes.
2. **Check for a session folder** – `docs/sessions/<YYYY-MM-DD>_<Txxx>‑<title>/` with the DEV‑REPORT.
3. **Locate the package.json** – `daoanh/package.json` contains the `qa:task` script.

## Running the QA Validation

### Option A: Using the OpenCode @tester agent
```bash
@testester T457
```
Replace `T457` with the actual task ID you are validating.

### Option B: Using npm script
```bash
npm run qa:task -- T457
```

### Option C: Running the generic tester:agent (if available)
```bash
npm run tester:agent
```
This typically validates the most recent task; for explicit control, use Option A or B.

## What @tester Does

### 1. Reads and Analyzes Task and DEV‑REPORT
- Opens `docs/tasktodo.md` to locate the target task Txxx.
- Loads the corresponding task file (`tasks/Txxx-*.md`).
- Reads your DEV‑REPORT (`docs/sessions/<YYYY-MM-DD>_<Txxx>‑<title>/DEV-REPORT.md`).

### 2. Performs Automated Tests
Runs the mandatory QA pipeline:
```bash
npm run guard          # SSOT repo‑root guard (fails if nested .git appears in daoanh/)
npm run dup:ids       # duplicate task‑ID check
npm run lint          # JavaScript syntax lint
npm run test          # unit tests
npm run e2e           # HTML/JS error checks
```
If the task defines additional test suites (e.g., `test:t95`, `test:t165`), these are also executed.

### 3. Checks Out‑of‑Scope Changes
Compares `git diff --name-only` against the files declared in your DEV‑REPORT. Any modifications outside the declared scope are flagged.

### 4. Runs Independent Validation
- Verifies schema integrity, checksums, and record counts.
- For ETL/JSONL/XML/TTL files: validates parse‑ability, record counts, duplicate keys, and source preservation.
- For DB/TTL/Production: **read‑only only** – aborts if any write operation is attempted.
- Flags `EVIDENCE_INCOMPLETE` if a command succeeds without sufficient output.

### 5. Generates a QA Report
Creates a markdown report in:
```
docs/qa_reports/QA-<YYYY-MM-DD>-<Txxx>.md
```
The report includes:
- Task ID, timestamp, git HEAD SHA
- Declared task scope vs. actual changes
- Commands run and their outputs
- Validation results (PASS/FAIL/PASS_WITH_WARNINGS/EVIDENCE_INCOMPLETE)
- Any blockers or issues

## Interpreting the QA Report

### PASS
All tests pass, no out‑of‑scope changes, no production/DB/TTL mutations, and full evidence is present.

### PASS_WITH_WARNINGS
Functional verification passed, but there are non‑blocking warnings (e.g., minor lint warnings).

### FAIL
Any test failure, out‑of‑scope change, production/DB/TTL mutation, or insufficient evidence.

### EVIDENCE_INCOMPLETE
Command succeeded but lacked sufficient output to confirm validation.

## Next Steps Based on the Report

### If PASS or PASS_WITH_WARNINGS
Your code changes are ready for Admin review. You and the Admin can proceed with committing the changes.

### If FAIL
Fix the issues highlighted in the report (typically: failed tests, out‑of‑scope changes, or production/DB/TTL mutations). After fixing, re‑run the @tester validation.

### If EVIDENCE_INCOMPLETE
Investigate why the command lacked output. Ensure that commands produce sufficient evidence (e.g., do not suppress output). Re‑run after fixes.

## Developer Best Practices

1. **Follow the DEV‑REPORT format** – include all required sections for proper QA validation.
2. **Keep changes scoped** – only modify files explicitly declared in the task specification.
3. **Run local tests** – perform a quick `npm run lint` and `npm run test` before invoking @tester to catch obvious issues early.
4. **Document evidence** – ensure that all commands run in the DEV‑REPORT have clear output and exit codes.
5. **Avoid production changes** – @tester will flag any accidental DB/TTL/legacy/production mutations.

## Example Workflow

1. `tasks/T457‑example‑task.md` defines a new feature.
2. You complete the feature and create a DEV‑REPORT in `docs/sessions/2026-10-24_T457‑example‑task/DEV-REPORT.md`.
3. You run: `@tester T457`
4. @tester generates `docs/qa_reports/QA-2026-10-24-T457.md` with results.
5. If PASS, you and the Admin approve the task and commit the changes.
6. If FAIL, you fix the issues and repeat from step 2.

## Limitations

- @tester **does not** edit any files.
- @tester **does not** run DB migrations or perform INSERT/UPDATE/DELETE operations.
- @tester **does not** autonomously close tasks or change task statuses.
- All final task approval and production deployment decisions are made by the Developer and Admin.

## Contact
If you encounter any issues with the @tester workflow, consult the AGENTS.md file in the daoanh directory for additional guidance.