# GIT-INDEX-AUDIT-02 — Remaining Deletion Audit
**Status**: FINAL · **Date**: 2026-09-30
**HEAD**: `f95079d7614270c5c7ec33784fc9e31fe900541f`
**Branch**: master
**Mode**: READ-ONLY — no restore, no commit, no code change, no DB change

---

## A. Timestamp
2026-09-30 (after T165-GIT-RECOVERY-01 recovery commit `dcdc921`)

## B. HEAD
`f95079d7614270c5c7ec33784fc9e31fe900541f`

## C. Branch
`master`

## D. CRITICAL FINDING — Nature of Anomaly Correction

The previous T165-GIT-RECOVERY-01 report anticipated "remaining staged deletions (~15 files)"
based on `D` entries visible in an earlier `git status --short` run.

**ACTUAL RESULT:**

```
git diff --cached --name-status --diff-filter=D
(empty — no output)
```

**STAGED DELETION COUNT = 0 (ZERO)**

The git index is CLEAN. There are zero staged deletions.

The "anomaly" is different in nature from what was anticipated:
- What was observed: ` D` entries in `git status --short` (second column D)
- Meaning: files exist in HEAD/index but are DELETED from the working tree (UNSTAGED)
- What was NOT present: `D ` entries (staged deletions)
- The files will NOT be committed as deletions unless explicitly `git add`'d

This is a **working-tree only anomaly** — it does not affect git history, committed state,
or future commits unless the deletion is explicitly staged.

## E. Staged Deletion Count
**0 (ZERO)**

## F. Working-Tree (Unstaged) Deletion Count
**16**

---

## G. Exact Working-Tree Deletion Inventory

Files present in HEAD/index, missing from working tree (unstaged):

```
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T166-review-reconciliation.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T169-groq-place-verify-pipeline-SPEC.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T169-groq-place-verify-pipeline.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T170-dila-place-person-v41-verify.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T171-person-name-standard-SPEC.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T171-person-name-standard.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T172-hanviet-charwise-debug.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T173-person-lineage-tab-merge.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T175-phase0c-canonical-person-identity-audit.md
D  Dai_Tang_Kinh/daoanh/docs/Mimo-Flash/T176-phase0c-rev2-canonical-person-identity-audit.md
D  Dai_Tang_Kinh/daoanh/docs/sessions/2026-09-25/t166/canonical_lock.py.phase1-preimpl.bak
D  Dai_Tang_Kinh/daoanh/docs/sessions/2026-09-25/t166/test_t166_canonical_lock.py.phase1-preimpl.bak
```

All are docs/spec/planning files or backup files. None are application code.

---

## H. Per-File Git History

| # | File (short) | Last Commit in History | Commit Description |
|---|--------------|----------------------|-------------------|
| 1 | T166-review-reconciliation.md | `84f9da1` | T166 REVIEW reconciliation (snapshot 09-26) |
| 2 | T168-rule-resolver-context-compiler-PLAN.md | `cebe7ed` | feat: T187 (last touched); `13b0ca5` = T182 "superseded" note |
| 3 | T169-groq-place-verify-pipeline-SPEC.md | `540cfb0` | feat: all code cloud sessions |
| 4 | T169-groq-place-verify-pipeline.md | `540cfb0` | feat: all code cloud sessions |
| 5 | T170-dila-place-person-v41-verify-SPEC.md | `5795d01` | P8.4R (modified content, not deleted) |
| 6 | T170-dila-place-person-v41-verify.md | `5795d01` | P8.4R (modified content, not deleted) |
| 7 | T171-person-name-standard-SPEC.md | `5795d01` | P8.4R (modified content, not deleted) |
| 8 | T171-person-name-standard.md | `5795d01` | P8.4R (modified content, not deleted) |
| 9 | T172-hanviet-charwise-debug-SPEC.md | `5795d01` | P8.4R (modified content, not deleted) |
| 10 | T172-hanviet-charwise-debug.md | `5795d01` | P8.4R (modified content, not deleted) |
| 11 | T173-person-lineage-tab-merge.md | `5795d01` | P8.4R (modified content, not deleted) |
| 12 | T174-t158-phase0-reuse-first-canonical-guard.md | `5795d01` | P8.4R (modified content, not deleted) |
| 13 | T175-phase0c-canonical-person-identity-audit.md | `540cfb0` | feat: all code cloud sessions |
| 14 | T176-phase0c-rev2-canonical-person-identity-audit.md | `5795d01` | P8.4R (modified by T194/T195 corrections) |
| 15 | canonical_lock.py.phase1-preimpl.bak | `540cfb0` | feat: all code cloud sessions |
| 16 | test_t166_canonical_lock.py.phase1-preimpl.bak | `540cfb0` | feat: all code cloud sessions |

Note on files #5–14: `5795d01` appears in history because it MODIFIED their content
(reduced lines) — but did NOT delete them. They still exist in HEAD at their committed state.
The working-tree file is missing because it was deleted locally before being staged/committed.

---

## I. Classification A/B/C

### Classification Rule Recap
- A = intentional deletion (explicit task/commit/architecture decision)
- B = unintended working-tree anomaly (no deletion decision documented)
- C = uncertain (insufficient evidence)

### Results

| # | File (short) | Class | Evidence |
|---|--------------|-------|---------|
| 1 | T166-review-reconciliation.md | **B** | Created `84f9da1`; no deletion task; active review doc |
| 2 | T168-rule-resolver-context-compiler-PLAN.md | **B** | "Superseded" refers to content, not file removal; still in HEAD |
| 3 | T169-groq-place-verify-pipeline-SPEC.md | **B** | Created `540cfb0`; no deletion task |
| 4 | T169-groq-place-verify-pipeline.md | **B** | Created `540cfb0`; no deletion task |
| 5 | T170-dila-place-person-v41-verify-SPEC.md | **B** | In HEAD (modified by T189/T190 corrections); active SPEC |
| 6 | T170-dila-place-person-v41-verify.md | **B** | In HEAD (modified by T189/T190 corrections); active doc |
| 7 | T171-person-name-standard-SPEC.md | **B** | In HEAD (modified by T190/T191); active SPEC |
| 8 | T171-person-name-standard.md | **B** | In HEAD (modified by T190/T191); active doc |
| 9 | T172-hanviet-charwise-debug-SPEC.md | **B** | In HEAD (modified `65e9324`); T172 completed feat |
| 10 | T172-hanviet-charwise-debug.md | **B** | In HEAD (modified `65e9324`); T172 session log |
| 11 | T173-person-lineage-tab-merge.md | **B** | In HEAD (modified `e6459cc`); pending feature plan |
| 12 | T174-t158-phase0-reuse-first-canonical-guard.md | **B** | In HEAD (modified `39c8ae9`); active planning doc |
| 13 | T175-phase0c-canonical-person-identity-audit.md | **B** | In HEAD since `540cfb0`; planning doc; no deletion |
| 14 | T176-phase0c-rev2-canonical-person-identity-audit.md | **B** | In HEAD (modified T194/T195); active audit doc |
| 15 | canonical_lock.py.phase1-preimpl.bak | **B** | Session reference backup; in HEAD; no deletion task |
| 16 | test_t166_canonical_lock.py.phase1-preimpl.bak | **B** | Session reference backup; in HEAD; no deletion task |

**Class A: 0** · **Class B: 16** · **Class C: 0**

---

## J. Explicit Deletion Task/Commit

No explicit deletion commit found for any of the 16 files.

T168 note: `13b0ca5` contains "S1-S8 => superseded" — this refers to content revision
(the plan steps were superseded by later work), not a decision to delete the file.
The file was subsequently modified again in `cebe7ed`, confirming it remained active.

---

## K. T165 Impact

None of the 16 working-tree-deleted files affect T165 or P8 in any way:
- No T165 implementation code
- No P8 pilot gate (`_P8_PILOT_GATE_ENABLED`)
- No `canonical_lock.py` modifications
- No `app.py` modifications
- No DILA governance data
- No translation cache

---

## L. P8 Impact

**NONE.** The 16 files are exclusively docs/specs/planning documents and .bak backups.

P8 implementation files confirmed PRESENT in working tree:

```
✅ tests/test_t165_phase8_entity_alignment.py    (549 lines, P8.1)
✅ tests/test_t165_phase8_alignment_persistence.py (388 lines, P8.2)
✅ tests/test_t165_phase8_pilot_gate.py           (426 lines, P8.3)
✅ scripts/t165_phase8_alignment_migrate.py       (239 lines, P8.2)
✅ docs/Mimo-Flash/T165-P8.4R-BLOCKER-VERIFICATION.md
```

---

## M. Files Requiring Admin Decision

No files require Admin authorization to classify — all 16 are B (unintended working-tree deletion).

**Recommended action for Admin:**
- `git restore -- <file>` to restore working-tree copies of any needed docs
- OR accept current state (files exist in HEAD/index, just absent from disk)
- The .bak files in sessions/2026-09-25/t166/ may be intentionally absent (Admin discretion)

No file requires a new commit — restoration is working-tree only.

---

## N. Recommended Safe Action by Class

| Class | Count | Recommended Action |
|-------|-------|-------------------|
| A | 0 | — (none) |
| B | 16 | `git restore -- <file>` to restore working-tree copy; no commit needed |
| C | 0 | — (none) |

For `.bak` files specifically: Admin discretion. They are reference backups.
Restoring them is safe; not restoring them is also safe (they remain in HEAD).

---

## O. Restore Executed
**NO** — This task is classification only. No `git restore` commands were run.

## P. Commit Created
**NO**

This audit artifact (`GIT-INDEX-AUDIT-02.md`) exists as an UNTRACKED file in the
working tree only. It has not been staged or committed.

## Q. Real DB Changed
**NO**

## R. Governance Changed
**NO** — `data_sources`, `legal_status`, `redistribution_allowed`, `commercial_use` unchanged.

## S. P8 Gate Remains OFF
**CONFIRMED** — `_P8_PILOT_GATE_ENABLED = False` at `app.py:17395` — not touched.

---

## T. Final Verdict

```
╔════════════════════════════════════════════════════════════════════╗
║  PASS — ALL REMAINING DELETIONS CLASSIFIED                         ║
╠════════════════════════════════════════════════════════════════════╣
║  CRITICAL FINDING: ZERO staged deletions in git index              ║
║  Remaining anomaly: 16 working-tree deletions (unstaged, B class)  ║
╠════════════════════════════════════════════════════════════════════╣
║  Staged deletions: 0                                               ║
║  Working-tree deletions: 16 (all B — unintended working-tree)      ║
║  Class A: 0 · Class B: 16 · Class C: 0                            ║
╠════════════════════════════════════════════════════════════════════╣
║  P8 files: ALL PRESENT ✅                                           ║
║  P8.4R artifact: PRESENT ✅                                         ║
║  Git index: CLEAN ✅                                                ║
║  DB/governance: UNCHANGED ✅                                        ║
╠════════════════════════════════════════════════════════════════════╣
║  Working-tree deletions do NOT affect commits or git operations.   ║
║  They can be restored with: git restore -- <file>                  ║
║  No Admin authorization required to restore them.                  ║
╚════════════════════════════════════════════════════════════════════╝
```

---

*GIT-INDEX-AUDIT-02 · Read-only audit · 2026-09-30 · Untracked (not committed)*
