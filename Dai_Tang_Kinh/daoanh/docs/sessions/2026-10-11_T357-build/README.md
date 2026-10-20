# Session 2026-10-11 — T357 build controls and fixtures

**Scope:** Admin/root approved ETL safety code + fixture tests and explicit additive control schema in code/fixtures. No production schema migration/apply, no TTL/XML write, no stage/commit. Code sole writer; Debug/root QA pending. Overall task in_progress. [Task](../../../tasks/T357-vnpa-etl-safety-remediation.md) · [Handoff](../../Handoff-2026-10-11-T357-build.md).

## Changes and acceptance

Importer entrypoint now delegates to safe engine default dry-run/plan. Parser subject/year validation is strict; no biography min/max dates. New engine: ro/query_only schema/baseline before RW, disk staging/typed manifests, reviewed frozen scoped reference and T203 classifier isolation, exact waiver, hashes/provenance, one BEGIN IMMEDIATE/COMMIT including run/inverse ledger, strict business/control affected counts and expected/protected rowsets, replay recovery, scoped inverse hash/CAS rollback. Explicit initialize-controls refuses the project production DB/hardlink; apply auto-DDL prohibited. Accepted count means validated staging rows, not academic accepted evidence.

## Tests/commands

- python -B -X utf8 tests/test_t357_vnpa_safe_etl.py:27/27 PASS11.966s. Nine actual mutation fault locations plus after-commit artifact failure/replay; source/rowset/ref/waiver/schema/mapping/drift, ignored/control counts, protected/unplanned triggers, inverse tamper and CAS, idempotency and no inferred dates. Frozen index test monkeypatches original authoritative_index to raise during plan/apply.
- python -B -X utf8 -m pytest tests/test_t217_vnpa_etl_preservation.py tests/test_t220_vnpa_etl_preserve_relations.py -q -k 'not Integration':33PASS,12deselected,0.44s; one Windows pytest cache warning. No production-copy Integration or T222 corpus checker run.
- --help PASS; module imports PASS. Static tester npm.cmd run lint/test/e2e all exit0; JS test is a placeholder, e2e is static. Runtime Playwright targets localhost5000/admin/API and remains unrun outside fixture scope; no UI claim from static checks.
- npm.cmd run pipeline: exit1 at dup:ids after guard PASS; same9 baseline conflicts T158/T168/T169/T170/T171/T177/T206/T215/T274. Later pipeline steps unrun, no full pipeline/tester PASS.
- Dashboard regenerated via existing script after docs/task changes; final output/hash in logs and outputs manifest.

## Failures corrected and limits

First fixture run unexpectedly invoked old check_labels→t203.classify→authoritative_index which read corpus TTL beyond fixture. Stopped immediately; production TTL/DB were not mutated, but those out-of-scope TTL reads did occur. Replaced reference lookup with reviewed frozen explicit index, clone function globals/scoped reader and regression forbidding the corpus index. Initial repeated fixture errors also exposed inconsistent mapping hash algorithms; unified streaming digest. The earlier23-test snapshot passed before independent QA; it did not cover the two blockers described below. These were implementation defects; no claim that the initial run was isolated/PASS.

Debug subsequently found two genuine blockers: a rollback trigger could mutate an outside row and still report success; invalid generation=-1 plus self teacher could commit. Fixed final inverse untouched-row fingerprints and expected-before verification, with rollback_blocked on conflict. Fixed incoming generation integer1..200 (safety bound only; curated existing values untouched) and self teacher/disciple rejection before RW. Exact regressions now PASS in the25-test suite11.966s; Debug recheck pending.

Cooperative ETL lock does not integrate all app writers. External-writer quiescence acknowledgment must be operationally verified before any future production run. Production schema/reference/source semantics not exercised; no real DB apply/migration. Full-copy backup is only performed on fixture apply; backup hash is provenance, logical manifest proof separate. Unknown schema/key/default/trigger effects fail closed; no migration invention.

## Backups, rollback, next

[Inputs](00-inputs-before.json) back up existing code/task/docs/Dashboard bytes as .txt. [Outputs manifest](outputs-manifest.json) lists after hashes. Existing-file rollback only when current hash matches after, then verify backup before hash and restore; drift requires inverse rebase. New artifacts retained if withdrawn. Future data rollback requires plan_hash+diff_hash, issuer/expiry/quiescence and full inverse ledger/current-row CAS. Debug read-only QA, root final QA and separately scoped production preparation/apply remain next.

Memory: no relevant registry/rollout facts used. Observation POST attempted separately with short timeout; exact result recorded, service success not assumed.

Final Debug blocker: AFTER UPDATE ON vnpa_etl_runs could mutate an outside authority row after the last business-row verification. The authorizer now denies every trigger-origin INSERT/UPDATE/DELETE in both apply and rollback; unsupported trigger writes fail closed. Exact late-ledger apply and rollback regressions PASS in final27 tests (11.966s), with complete fixture business/control/sqlite_sequence rowsets unchanged on rejection. Earlier25-test PASS is a prior snapshot, not final acceptance. Independent recheck/root QA pending.

Session started2026-10-11; final blocker repair/checks completed2026-10-12 (Asia/Bangkok). Build writer DONE for the assigned fixture scope; independent QA and production preparation remain PARTIAL/pending.

Final continuation verification: python -B -X utf8 tests/test_t357_vnpa_safe_etl.py passed27/27 in17.359s on unchanged code hashes; final guard exit0, dup:ids exit1 with the same9 historical conflicts and no T357. Dashboard regenerated successfully (277tasks,157done,28blocked) through the existing generator. Command outputs are in02-final-fixtures-guard-dup-dashboard.json. Local observation POST failed ECONNREFUSED127.0.0.1:37700 (4-second timeout configured), recorded in04-observation.json; nothing was stored by that unavailable service.
