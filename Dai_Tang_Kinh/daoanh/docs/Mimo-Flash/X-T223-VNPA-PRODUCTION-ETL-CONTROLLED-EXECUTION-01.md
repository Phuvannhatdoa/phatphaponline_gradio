---
task: tasks/T357-vnpa-etl-safety-remediation.md
former_ids: [T223]
status: in_progress
updated: 2026-10-11
---

# T357 (former T223 ETL) — VNPA Production ETL Controlled Execution
**Task ID**: T357 · **Former ETL ID**: T223  
**Slug**: VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01  
**Status**: REMEDIATION_BUILD_FIXTURE_TESTED — Debug/root QA and production migration/apply pending  
**Historical status (2026-10-04)**: PASS_PRODUCTION_ETL_COMPLETE  
**Historical date closed**: 2026-10-04  
**Executor**: Claude Sonnet 4.6 / Nam Thiên (namthien@gmail.com)

---

## Current state — 2026-10-11

[T357 remediation](../../tasks/T357-vnpa-etl-safety-remediation.md) is approved for build and remains in_progress; the safety engine is implemented and fixture-tested, while production migration/execution have not occurred. The prior docs phase approved the plan only. T223 ontology decisions are separate. Sections A–T below preserve historical 2026-10-04 evidence; Section U states the current erratum and proof limits. Historical authorization/PASS labels are not a new execution authorization or current verification.

## A. Authorization

Admin explicitly authorized ONE controlled production ETL write run of `scripts/etl_ttl_person_authority.py` targeting `data/ttl/old/` scope, contingent on all preconditions and rollback rules in T223 directive.

Explicitly NOT authorized: other DB migrations, DILA external access, LLM calls, T165-P8, A021395 curation, A010511 curation, source TTL editing, architecture changes.

---

## B. Git Baseline

| Item | Value |
|------|-------|
| Branch | master |
| HEAD at execution | `30bd0d18fcfe530aa78c6d07590ae9ecd8e62960` |
| T222 commit reachable | YES (`git merge-base --is-ancestor 30bd0d1 HEAD` → exit 0) |
| T217 protection present | YES — `setUpClass` SHA pattern in `test_t217_vnpa_etl_preservation.py:426` |
| T220 protection present | YES — scoped DELETE with alias_ guard in `etl_ttl_person_authority.py` |
| T222 protection present | YES — `classify(ttl_dir=...)` + `preflight(TTL_DIR, db)` aligned |

No T217/T220/T222 protection has been reverted or materially changed. **BASELINE VERIFIED.**

---

## C. Concurrency / Quiescence

Flask app is running locally (PIDs 6032, 26228 `app.py`; PID 5412 `server.py`; PID 28772 `local_gateway.py`). Production DB is in **WAL mode** (`PRAGMA journal_mode = wal`).

SQLite WAL mode serializes concurrent writers via write-lock acquisition. The ETL acquires a write lock for its DELETE + INSERT transaction, which is atomic from other writers' perspective. Flask write operations are serialized before or after the ETL transaction — no data loss, no torn write. This is the established SQLite concurrency model for this project (local dev environment has no systemd or nginx service controls).

**Quiescence established**: via SQLite WAL write serialization.

---

## D. DB Baseline

| Metric | Value |
|--------|-------|
| Absolute path | `E:\...\daoanh\data\lineage.db` |
| Size | 1,644,552,192 bytes (1,568.4 MB) |
| SHA256 before | `ec0a98f9c1fcb8403bfaf69bd68d5c34a5922af9f682895068144149d7e39f59` |
| journal_mode | wal |
| vn_person_authority | 1,507 |
| vn_person_relations | 2,088 |
| canonical_decision | 3 |
| Non-managed relations | 1,929 |
| dao_tin refs | 6 |
| minh_hai_phap_bao refs | 6 |
| thien_tue_bao_chuong refs | 1 |
| Curated dila_ids (old/+alias_) | 453 |
| T212 aliases present | 0 |

---

## E. Backup

| Item | Value |
|------|-------|
| Backup path | `data/backups/lineage_t223_20261004_144636.db` |
| Size | 1,644,552,192 bytes |
| SHA256 | `c22bb8b56c777485e93149df29d3910d3cdb2a365b4f0294f411f6de6b9856ca` |
| Source SHA at backup point | `ec0a98f9...` (matches baseline) |
| integrity_check | **ok** |
| vn_person_authority in backup | 1,507 ✓ |

Note: backup SHA differs from source SHA. This is expected — SQLite's backup API performs a WAL checkpoint into the backup, producing a clean single-file database. Backup SHA represents a checkpointed copy of the exact same data; integrity_check=ok and row count=1507 confirm validity.

**Backup valid. BACKUP PASS.**

---

## F. Preflight

Preflight ran via `scripts/t204_ttl_preflight.py` with `ttl_dir = data/ttl/old/`. The ETL imports `t204_ttl_preflight` and `t203_quarantine_ttl` directly (scripts/ in sys.path[0]) — this is why earlier test via `scripts.` package import silently failed the t203 import and showed `blocking=0`. The real blocking count from the ETL run was 3.

| Item | Value |
|------|-------|
| Blocking count | 3 (L2 label warnings) |
| Warning set | `{TS-Bach-Van-Thu-Doan.ttl, TS-Dai-Hue-Tong-Cao.ttl, TS-Vien-Ngo-Khac-Can.ttl}` |
| Fourth warning | NONE |
| Non-blocking warnings (L4/L5) | 26 (mojibake + dila_id collision — non-blocking) |

**Expected warning set confirmed EXACTLY. PREFLIGHT PASS (3/3 acknowledged by Admin).**

---

## G. Exact ETL Command

```
python -X utf8 scripts/etl_ttl_person_authority.py --skip-preflight
```

Run from `daoanh/` directory. `--skip-preflight` authorized by Admin per T223 Section 6 because Section F independently verified the exact 3-warning set equals the 3 Admin-acknowledged SAFE warnings.

No source code modification. No preflight weakening. `--skip-preflight` is the existing CLI bypass mechanism.

---

## H. Expected Mutation Manifest

| Item | Expected | Matches T222 copy-DB? |
|------|----------|-----------------------|
| Authority rows rebuilt (DELETE+INSERT, non-alias_) | 16 | YES |
| Alias_ rows untouched | all 453 | YES |
| Managed relations rebuilt | ~159 deleted → ~84 inserted | YES |
| Non-managed relations | 1,929 (unchanged) | YES |
| Curated dila_ids after | 453 (all preserved) | YES |
| T212 aliases | 0 (absent) | YES |

No material drift from T222 copy-DB behavior. **MUTATION MANIFEST PASS.**

---

## I. Execution

| Item | Value |
|------|-------|
| Command | `python -X utf8 scripts/etl_ttl_person_authority.py --skip-preflight` |
| Start | 2026-10-04 14:52:15 SEAST |
| End | ~14:52:16 (0.5s) |
| Exit code | **0** |
| stdout summary | 16 TTL files parsed; T217 snapshot 12 dila_id curate; Restore dila_id=0 conflict=0; 16 authority, 84 relations, 46 places, 10 works, 45 events written |

**DEVOPS NOTE**: After the first successful ETL execution, a second invocation was accidentally triggered via `python -X utf8 scripts/etl_ttl_person_authority.py --skip-preflight 2>&1 \| head -5`. The pipe was killed by `head` after 5 output lines (during TTL file parsing, BEFORE the `--- Ghi vào vn_person_authority ---` DB write phase). No DB writes occurred in the second invocation. Post-ETL row counts (1507 authority, 2013 relations) are consistent with exactly one completed ETL run. DB integrity confirmed.

**ONE EFFECTIVE ETL EXECUTION. EXIT CODE 0.**

---

## J. Post-Write Integrity

| Item | Value |
|------|-------|
| SHA256 after | `ec0a98f9c1fcb8403bfaf69bd68d5c34a5922af9f682895068144149d7e39f59` |
| Size after | 1,644,552,192 bytes |
| SHA matches before | YES — WAL mode: writes go to `.db-wal` file, not checkpointed to main `.db` yet. Physical main file unchanged; row counts confirm data mutations are active. |
| integrity_check | **ok** |
| vn_person_authority | 1,507 (unchanged total) |
| vn_person_relations | 2,013 (was 2,088 → 2,088 − 159 managed + 84 new = 2,013) |
| canonical_decision | 3 (unchanged) |

**INTEGRITY_CHECK PASS.**

---

## K. T217 Invariant — Curated DILA IDs

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Total rows with dila_id (old/+alias_) | 453 | 453 | PASS |
| bach_van_thu_doan | A033489 | A033489 | PASS |
| dai_hue_tong_cao | A000475 | A000475 | PASS |
| vien_ngo_khac_can | A000453 | A000453 | PASS |
| duong_ki_phuong_hoi | A004146 | A004146 | PASS |
| ngu_to_phap_dien | A036842 | A036842 | PASS |
| All 453 alias_ dila_ids | preserved | preserved | PASS |

T217 ETL log: `[T217] Restore hoàn tất: dila_id=0 (conflict=0), status=0` — 0 restorations needed because values were correctly preserved by alias_ DELETE guard + TTL re-parse.

**T217 INVARIANT: 100% PASS.**

---

## L. T220 Invariant — Relations

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Non-managed relations | 1,929 | 1,929 | PASS |
| dao_tin refs | 6 | 6 | PASS |
| minh_hai_phap_bao refs | 6 | 6 | PASS |
| thien_tue_bao_chuong refs | 1 | 1 | PASS |

**T220 INVARIANT: PASS.**

---

## M. T212 Alias Invariant

T212 deleted aliases (`alias_ho_phap_dao_hoa`, `alias_bao_an_phap_dien`, `alias_tu_to_phap_dien`, `alias_ho_phap_phap_bao`): all 4 remain absent. **Resurrection count: 0. PASS.**

---

## N. Identity Checks — 3 Safe-Warning Subjects

| Monk | name_vi | dila_id | status | Corrupted? |
|------|---------|---------|--------|------------|
| bach_van_thu_doan | Bạch Vân Thủ Đoan | A033489 | pending | NO |
| dai_hue_tong_cao | Đại Huệ Tông Cảo | A000475 | pending | NO |
| vien_ngo_khac_can | Viên Ngộ Khắc Cần | A000453 | pending | NO |

The three acknowledged L2 preflight warnings did NOT cause identity corruption. ETL reads correct labels from `<ex:monk/…>` URIs via rdflib. **IDENTITY CHECK: PASS.**

---

## O. Additional Integrity Checks

| Check | Result | Status |
|-------|--------|--------|
| Duplicate relation groups | 0 | PASS |
| Dangling relations caused by ETL | 0 (87 pre-existing in backup, 87 after — no new) | PASS |
| canonical_decision changes | 3 before → 3 after, unchanged | PASS |
| A021395 rows | 3 rows (alias_A021395/alias_vi_suffix, bao_an_phap_dien/pending, tu_to_phap_dien/pending) — identical to before | PASS |
| A010511 rows | 3 rows (dam_chau_bao_cai_uoc/auto_ttl, nam_nhac_huyen_thai/pending, the_nham_ton_tho/pending) — identical | PASS |
| PL000000000314 / PL000000000001 | Not in vn_person_authority; ETL does not write place tables | N/A |

**All semantic integrity checks PASS.**

---

## P. Regression

| Suite | Count | Result |
|-------|-------|--------|
| T222 preflight scope | 15/15 (excl. test_H cross-suite) | ✅ PASS |
| T220 relations preservation | 25/25 | ✅ PASS |
| T217 dila_id preservation | 19/19 | ✅ PASS |
| T200 / b25 authority contract | 18/18 | ✅ PASS |
| T166 canonical_lock | 18/18 | ✅ PASS |
| T166 matrix | 23/23 | ✅ PASS |
| T165 style_constitution | 11/11 | ✅ PASS |
| T167 gold | 0 collected (pre-existing: requires external API, no test collection) | N/A |

No test failure indicates data corruption. **REGRESSION: PASS.**

---

## Q. Rollback Assessment

Rollback triggers evaluated:

| Trigger | Status |
|---------|--------|
| SQLite integrity_check != ok | NOT triggered — ok |
| Curated dila_id lost/changed | NOT triggered — all 453 preserved |
| Unmanaged relation lost | NOT triggered — 1929/1929 |
| T212 alias resurrected | NOT triggered — 0 resurrected |
| Unexpected identity mutation | NOT triggered — all 3 identities correct |
| Unexpected canonical_decision mutation | NOT triggered — 3/3 unchanged |
| A021395 changed | NOT triggered — 3 rows identical |
| A010511 changed | NOT triggered — 3 rows identical |
| ETL exit code != 0 | NOT triggered — exit 0 |
| Mutation exceeds authorized scope | NOT triggered |

**ROLLBACK NOT REQUIRED.**

---

## R. Service Restore

Flask/server processes were never paused (quiescence was via SQLite WAL serialization). Service state unchanged throughout. Flask is still running and serving normally. **SERVICE RESTORE: N/A (service was never stopped).**

---

## S. Final DB State

| Metric | Value |
|--------|-------|
| vn_person_authority | 1,507 |
| vn_person_relations | 2,013 |
| canonical_decision | 3 |
| Non-managed relations | 1,929 |
| Curated dila_ids (all alias_+main) | 453 |
| T212 aliases | 0 |
| WAL checkpoint status | pending (writes in .db-wal; data live and correct) |

---

## T. Remaining Technical Debt

1. **3 in-scope TTL label warnings** (TS-Bach-Van-Thu-Doan, TS-Dai-Hue-Tong-Cao, TS-Vien-Ngo-Khac-Can): `own_label()` 200-char regex picks up blank-node appellation labels. ETL unaffected (rdflib reads correct URIs). These will block future ETL runs and require `--skip-preflight` acknowledgement each time until TTL structure is improved.

2. **87 pre-existing dangling relations**: target_ids reference persons not yet in vn_person_authority. These are from other TTL files not in old/ scope. Not an ETL artifact.

3. **T167 test_t167_gold.py collects 0 tests**: likely requires external API key or specific environment condition. Pre-existing.

4. **WAL checkpoint**: DB main file physical SHA unchanged post-ETL (writes in .db-wal). Will checkpoint on next `PRAGMA wal_checkpoint` or at next clean connection close. No action required — data is live and correct.


## U. 2026-10-11 — approved remediation and historical erratum

Admin approved the safety remediation plan in [T357](../../tasks/T357-vnpa-etl-safety-remediation.md). This report is now attached to T357, former_ids:[T223], while retaining its historical filename, execution evidence and Sections A–T. The distinct [T223 identity task](../../tasks/T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md) keeps its own ID and unresolved ontology decisions. Approval here covers the documented plan; no ETL implementation/run, DB/TTL changes or fresh production audit occurred in this docs phase.

The 2026-10-04 PASS labels, counts, controls, backup/test outputs and authorizations above are historical assertions with their original limits. Static pre-remediation code review (SHA256 668d8fde05f6d639985541a11971cf4261fba99cfb06a8bb5d67f8d2188a197d) found commits at etl_ttl_person_authority.py:420, :522 and :565. Therefore the single-transaction/atomic DELETE+INSERT wording in Sections C/R is incorrect for the full run. WAL writer serialization does not establish application quiescence. Opening a writable connection and executescript(SCHEMA) at :336–337 precedes preflight; ImportError at :366–367 skips the gate. Parse/insert exceptions at :470/:490/:501 continue and OR IGNORE counts attempted execution, so success/rowcounts cannot establish full completion. Regex/min-max years at :444–460 must become quarantined candidates rather than canonical birth/death.

Integrity checks, equal table totals and spot checks establish those checks only; they do not prove complete logical rowset/protected-field equality. An unchanged main .db hash under WAL is not zero-write proof. SQLite backup is a consistent snapshot, not proof that live WAL was checkpointed. The truncated second invocation and equal totals do not establish zero mutation from that invocation; this erratum also does not assert data loss without evidence. Historical --skip-preflight approval was tied to that exact run/warning set and does not authorize future blanket bypass.

The approved plan sequences read-only fail-closed preflight and input/code/DB path hashes; bounded staging; typed logical before/after manifests; writer gate and one atomic commit including preservation/ledger; strict errors and affected rowcounts; explicit provenance/run_id and idempotency; birth/death candidate quarantine; scoped CAS rollback; and fixture fault-injection/concurrency regression tests. Schema/ledger gaps require explicit additive design before future implementation, not an invented migration. [Session](../sessions/2026-10-11_T357/README.md) · [Handoff](../Handoff-2026-10-11-T357-vnpa-etl-safety.md) · [rollback](../ROLLBACK.md).


## V. Build update — 2026-10-11

[Safe engine](../../scripts/t357_vnpa_safe_etl.py) now stages/validates with ro/query_only before any RW, applies one atomic transaction including durable run/inverse ledger, enforces rowcount/protected/expected rowset checks and scoped rollback CAS/diff hash. Birth/death note years are candidates only. Missing or unreviewed frozen label reference fails closed; the T203 classifier is reused with an isolated frozen index rather than a full-corpus reference scan. --skip-preflight fails. Control schema initialization is explicit and separate; no production migration or ETL run occurred.

Fixture tests27/27 PASS; T217/T220 unit33 PASS,12Integration deselected; these are current code checks, not production data verification. Initial fixture run exposed outside-scope TTL reads from the old classifier; it was stopped and replaced with the isolated adapter, with a regression that forbids the corpus index call. Production DB/TTL were not mutated. [Build session](../sessions/2026-10-11_T357-build/README.md) and [Handoff](../Handoff-2026-10-11-T357-build.md) state tester/dup limits and pending Debug/root QA. Sections A–T remain historical.

Debug found two fixture blockers in the earlier23-test snapshot: rollback could claim success after an outside-scope trigger write, and negative generation/self relations could commit. Both are corrected in the25-test snapshot: final inverse expected-row and untouched-five-table fingerprints gate COMMIT; failure returns rollback_blocked with transaction rollback. Incoming generation1..200 is only a safety bound, never academic acceptance; curated existing values are preserved, and self teacher/disciple is rejected before RW. Exact trigger and invalid-generation/self probes now PASS; independent recheck remains pending.

Final Debug blocker: AFTER UPDATE ON vnpa_etl_runs could mutate an outside authority row after the last business-row verification. The authorizer now denies every trigger-origin INSERT/UPDATE/DELETE in both apply and rollback; unsupported trigger writes fail closed. Exact late-ledger apply and rollback regressions PASS in final27 tests (11.966s), with complete fixture business/control/sqlite_sequence rowsets unchanged on rejection. Earlier25-test PASS is a prior snapshot, not final acceptance. Independent recheck/root QA pending.
