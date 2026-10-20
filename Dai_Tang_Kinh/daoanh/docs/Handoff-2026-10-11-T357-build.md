# Handoff — 2026-10-11 — T357 build

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái |
|---|---|
| Task | [T357](../tasks/T357-vnpa-etl-safety-remediation.md), former_ids:[T223] ETL branch |
| Scope | Code/fixture build; no production DB migration/apply hoặc TTL/XML change |
| Tests | New27PASS; T217/T220unit33PASS/12deselected; --help/import PASS |
| Guard/pipeline | Guard PASS; pipeline exit1 tại9baseline duplicates; later steps unrun |
| Static tester | lint/test/e2e exit0; JS test placeholder, static e2e only |
| QA/commit | Debug/root pending; chưa stage/commit; task in_progress |
| HEAD | 53272e5749c5c649d3642d9ce40133b5384aa300 (read-only snapshot; shared HEAD may move) |
| Session | [T357-build](sessions/2026-10-11_T357-build/README.md) |

## 2. Đọc trong 2 phút

Đã triển khai safe engine và delegate importer main, mặc định dry-run. Atomic commit, staged manifests, fail-closed scoped frozen reference/waiver, strict counts, durable run/inverse ledger, idempotency và hash/CAS rollback đã test trên temp SQLite. Không inferred biography birth/death. Initial helper đọc corpus ngoài fixture đã bị dừng và sửa; không che sự cố đó bằng claim no-read.

Ba việc root/Admin: Debug QA3files code/tests; root QA diff/results/limits; giao production schema/reference/writer-policy rehearsal riêng nếu đạt. Không chạy real ETL vì fixture PASS.

## 3. Đề xuất phần chữa dựng và kết quả

New scripts/t357_vnpa_safe_etl.py: explicit control schema preparation; ro/query_only baseline/schema/ref preflight → disk stage/logical diff → one BEGIN IMMEDIATE/COMMIT → ledger recovery → scoped inverse hash/CAS. scripts/etl_ttl_person_authority.py keeps parser/schema, removes unsafe legacy main; exact/ISO dates only, unique stable subject required. Tests actual engine mutations at9fault points preserve full fixture rowsets; post-COMMIT artifact failure replays without mutation. Protected aliases/curate/outside rows and expected managed memberships verified; all27 PASS. accepted count is staging validation, not source acceptance.

## 4. Cảnh báo bắt buộc

No production apply/migration/TTL writes. Main now requires explicit DB/input/output/reference; old --skip-preflight fails closed. Control schema is additive code/fixture only and is not automatically prepared during apply. Frozen index requires reviewed/issuer/locator/exact scope; missing index stops, never fallback corpus scan. Cooperative lock only covers this ETL, app quiescence still separate attestation. All git from visjs-app; shared WIP/hash drift must be preserved; no broad stage. TTL ignored, raw XML immutable.

## 5. Lệnh revert từng task

Existing files: outputs-manifest.json records current after_sha;00-inputs-before.json points exact backup. Run at daoanh, one explicit manifest path:

~~~powershell
$taskManifest = Get-Content -Raw -LiteralPath 'docs/sessions/2026-10-11_T357-build/outputs-manifest.json' | ConvertFrom-Json
$taskEntry = $taskManifest.files | Where-Object path -eq 'scripts/etl_ttl_person_authority.py'
if ((Get-FileHash -LiteralPath $taskEntry.path -Algorithm SHA256).Hash.ToLower() -ne $taskEntry.sha256) { throw 'Drift: stop' }
if ((Get-FileHash -LiteralPath $taskEntry.backup -Algorithm SHA256).Hash.ToLower() -ne $taskEntry.before_sha256) { throw 'Backup mismatch' }
Copy-Item -LiteralPath $taskEntry.backup -Destination $taskEntry.path
~~~

| Revert | Mất dữ liệu? |
|---|---|
| Hashguard restore code/docs/Dashboard | Không DB/TTL data change ở build này |
| New engine/tests/evidence | Retain/mark superseded, không blanket delete |
| Fixture data inverse | Scoped plan_hash+diff_hash/current-row CAS, one commit; preserve unrelated writes |

After authorized commit, git revert --no-edit SHA from git log tại repo root. No blind full-DB restore. Production rollback chưa thử.

## 6. Bảng file tạo/sửa

| File | Vai trò |
|---|---|
| scripts/t357_vnpa_safe_etl.py | New engine/control-schema/CLI |
| scripts/etl_ttl_person_authority.py | Delegate main + strict parser validation |
| tests/test_t357_vnpa_safe_etl.py | New isolated fixtures/fault injection |
| tasks/T357-vnpa-etl-safety-remediation.md | Build status/usage/limitations |
| docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md | Current build status; A–T historical preserved |
| docs/tasktodo.md;docs/ROLLBACK.md | Scoped T357 tracking/guarded rollback |
| data/progress_data.json | Existing generator only |
| Session/Handoff | Logs/backups/output hashes |

Exact paths/hashes in [outputs manifest](sessions/2026-10-11_T357-build/outputs-manifest.json); commit history comes from git log.

## 7. Sai lầm và bài học

Old T203 reference builder ignores write-scope for its reference scan; initial test read outside fixture, so stopped and replaced with frozen index + isolated classifier globals. No TTL/production DB mutation occurred. A list-vs-stream mapping hash mismatch caused false drift; unified digest and retested. Never infer isolation from passing scope parameter; test actual read path. Static JS test placeholder is not real ETL validation. Debug found rollback outside-trigger false success and invalid generation/self-edge acceptance after the earlier23-test snapshot. Both were verified defects and corrected: rollback final untouched/expected-before fingerprints fail with rollback_blocked, and incoming generation1..200/self-edge guards reject before RW. Existing curated generation is preserved; the bound is not historical acceptance. Two exact regression probes are included in final25PASS; independent recheck pending.

## 8. Việc CHƯA xong

Debug/root QA; actual production schema compatibility/control preparation; reviewed label references with source evidence; all-writer maintenance/gate proof; copy-DB rehearsal/rollback with approved scope; production run if delegated. Runtime UI/API tester not run, full pipeline blocked by9knownduplicates; no UI or production-data PASS. Task remains in_progress.

## 9. Lệnh kiểm tra nhanh

~~~powershell
python -B -X utf8 tests/test_t357_vnpa_safe_etl.py
python -B -X utf8 -m pytest -p no:cacheprovider tests/test_t217_vnpa_etl_preservation.py tests/test_t220_vnpa_etl_preserve_relations.py -q -k 'not Integration'
python -B -X utf8 scripts/t357_vnpa_safe_etl.py --help
npm.cmd run guard
npm.cmd run dup:ids
~~~

Fixtures are temp DB/TTL; never add Integration selector against production copy. See task §11 for fixture CLI/reference format.

## 10. Ghi chú cho agent kế tiếp

Read task §11 + session/tests/manifests; verify live file hashes/HEAD before edits. Preserve ontology T223 distinct from former ETL T223. Debug independent read-only QA, Code writer only when assigned, root final QA. Do not promote date/identity/lineage from accepted staging counts. Fresh source/reference/code/baseline requires fresh plan+ack; run_id collision or rollback drift stops. Local observation failure must be reported honestly.

Final Debug blocker: AFTER UPDATE ON vnpa_etl_runs could mutate an outside authority row after the last business-row verification. The authorizer now denies every trigger-origin INSERT/UPDATE/DELETE in both apply and rollback; unsupported trigger writes fail closed. Exact late-ledger apply and rollback regressions PASS in final27 tests (11.966s), with complete fixture business/control/sqlite_sequence rowsets unchanged on rejection. Earlier25-test PASS is a prior snapshot, not final acceptance. Independent recheck/root QA pending.

Final continuation verification: python -B -X utf8 tests/test_t357_vnpa_safe_etl.py passed27/27 in17.359s on unchanged code hashes; final guard exit0, dup:ids exit1 with the same9 historical conflicts and no T357. Dashboard regenerated successfully (277tasks,157done,28blocked) through the existing generator. Command outputs are in02-final-fixtures-guard-dup-dashboard.json. Local observation POST failed ECONNREFUSED127.0.0.1:37700 (4-second timeout configured), recorded in04-observation.json; nothing was stored by that unavailable service.
