# Handoff — 2026-10-11 — T357 VNPA ETL safety

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Task / former IDs | [T357](../tasks/T357-vnpa-etl-safety-remediation.md) / [T223] nhánh production ETL |
| HEAD snapshot | 53272e5749c5c649d3642d9ce40133b5384aa300; không phải commit task này |
| Scope / trạng thái | docs/plan-only; kế hoạch Admin approved; task in_progress |
| Session | [2026-10-11_T357](sessions/2026-10-11_T357/README.md) |
| DB / TTL / importer | Không query/ghi DB, không ghi TTL/raw XML, không chạy/sửa importer |
| Kiểm hiện tại | Guard PASS; dup FAIL cùng 9 conflicts có sẵn; targeted docs PASS; Dashboard exit0; không pipeline/build PASS |
| QA / commit | Debug/root QA chờ; chưa stage/commit |

## 2. Đọc trong 2 phút

Đã viết remediation đầy đủ, chuyển tracking nhánh report ETL từ T223 sang T357 với former_ids:[T223], giữ filename và mọi phần chứng cứ lịch sử A–T, thêm erratum U. T223 ontology 29 nhóm không đổi quyền/quyết định. Preflight hiện mở writable schema trước gate, thiếu module thì skip; importer có ba commit, nên claim atomic/quiescence bằng WAL bị bác bỏ bằng code. Regex min/max không được thành sinh/tử canonical.

Ba việc root/Admin cần làm: QA kế hoạch và giới hạn historical/current; giao Debug kiểm docs/delta độc lập; chốt scope build tiếp gồm ledger/writer gate và fixture tests trước mọi production apply. Không xin chạy ETL trong lượt này.

## 3. Đề xuất phần chữa dựng

[T357](../tasks/T357-vnpa-etl-safety-remediation.md) §3–9: read-only fail-closed preflight → bounded staging → typed rowset diff → một transaction/commit gồm preserve + durable run ledger → strict affected-rowcounts/errors → idempotency và provenance → dates candidate quarantine → scoped CAS rollback. Oracle: fault trước COMMIT phải giữ toàn rowset; protected rows/fields bằng nhau; rerun không mutation; drift thì dừng. Đây là tiêu chí build tương lai, chưa báo đạt bằng docs.

Code evidence: etl_ttl_person_authority.py :336–337/:366–367/:420/:522/:565/:444–460/:470/:490/:501; source SHA và backup mapping ở [inputs manifest](sessions/2026-10-11_T357/00-inputs-before.json). Không biến count/spot checks/main-db hash lịch sử thành full logical proof.

## 4. Cảnh báo bắt buộc

Worktree/HEAD dùng chung; mọi git từ visjs-app root, không nuốt WIP session khác. Không stage/commit trước root QA. Lỗi metadata/index Windows và private lock T356 lịch sử không được xử lý trong scope này. TTL không được Git bảo vệ: lượt này không sửa TTL. Raw XML bất biến. WAL writer serialization không thay maintenance/writer mutex; future DB restore phải coordinate mọi writer. T223 ontology/A021395/teacher/số đời không được duyệt bởi remediation ETL.

## 5. Lệnh revert từng task

Rollback docs hiện có bằng after-hash guard rồi copy byte backup. Chạy tại daoanh, thay một path thuộc manifest; không xóa docs mới hoặc dữ liệu:

~~~powershell
$taskManifest = Get-Content -Raw -LiteralPath 'docs/sessions/2026-10-11_T357/06-outputs-manifest.json' | ConvertFrom-Json
$taskEntry = $taskManifest.files | Where-Object path -eq 'docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md'
if (-not $taskEntry.backup) { throw 'Không có backup cho file mới' }
if ((Get-FileHash -LiteralPath $taskEntry.path -Algorithm SHA256).Hash.ToLower() -ne $taskEntry.sha256) { throw 'Drift: dừng và rebase inverse diff' }
if ((Get-FileHash -LiteralPath $taskEntry.backup -Algorithm SHA256).Hash.ToLower() -ne $taskEntry.before_sha256) { throw 'Backup hash sai' }
Copy-Item -LiteralPath $taskEntry.backup -Destination $taskEntry.path
~~~

| Phạm vi | Mất dữ liệu? |
|---|---|
| Restore doc/Dashboard đúng hash | Chỉ bỏ phần docs-phase; DB/TTL không thay đổi |
| Task/session/Handoff mới | Giữ evidence, ghi superseded nếu rút kế hoạch |
| Future ETL | Chưa thực hiện; contract scoped inverse/CAS ở task §8, không blind full-DB restore |

Sau commit được giao riêng, dùng git revert --no-edit SHA từ git log tại repo root và kiểm diff; không dùng placeholder SHA như commit có thật.

## 6. Bảng file tạo/sửa

| File/nhóm | Thay đổi |
|---|---|
| tasks/T357-vnpa-etl-safety-remediation.md | Mới; plan phases A–G, acceptance, former_ids |
| docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md | Tracking T357 + historical status + erratum U |
| tasks/T223-..., tasks/T200-..., tasks/T253-... | Chỉ thêm ranh giới ownership/current link |
| docs/Mimo-Flash/T221-..., T202-POST-REVIEW-02.md | Historical preflight/inference limits + current link |
| docs/plans/identity-evidence-remediation-20261009.md | Link ETL transport/SSOT/date quarantine |
| docs/integration/Cline/2026-10-06-person-import-phase0-audit.md; docs/reports/T202-logic-review-20261009/README.md | Additive current follow-up, giữ audit cũ |
| docs/tasktodo.md; docs/ROLLBACK.md | T357 entry, T223 ontology status boundary, docs hashguard rollback |
| data/progress_data.json | Generator exit0: 15 modules,319 endpoints,277 tasks; T357 in_progress |
| docs/sessions/2026-10-11_T357/; Handoff này | Backup, commands, manifest và bàn giao |

Exact paths/hashes/bytes ở [outputs manifest](sessions/2026-10-11_T357/06-outputs-manifest.json), không thay bằng danh sách tối thiểu commit.

## 7. Sai lầm và bài học

ID T223 có hai nghĩa; không copy ID task ontology sang nhánh ETL. Baseline mới có T274 trùng, nên số 8 duplicate cũ không còn hiện hành. Thiếu module preflight và ba commit là failure modes thực; WAL không chứng minh điều ngược lại. Backup task .md trong docs bị scanner coi là task mới; dùng .md.txt. Không dùng số tổng hoặc stdout cắt để suy ra 0 write. Không ghi claim DB hỏng khi chưa kiểm.

## 8. Việc CHƯA xong

Ưu tiên: Debug/root QA docs; chốt transaction/write-gate/durable ledger support ở build-phase; giao Code triển khai đúng scope; fixture fault-injection/regressions + copy-DB dry-run và rollback rehearsal; rồi quyết production run riêng. Overall T357 vẫn in_progress. Các duplicate lịch sử ngoài scope cần ownership riêng; không sửa để làm pipeline xanh.

## 9. Lệnh kiểm tra nhanh

Tại daoanh: npm.cmd run guard; npm.cmd run dup:ids; rg -n 'T357|former_ids|task:' tasks/T357-vnpa-etl-safety-remediation.md docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md docs/tasktodo.md. Đọc [session logs](sessions/2026-10-11_T357/README.md) và hash manifest. Dashboard từ gitroot: python -B -X utf8 Dai_Tang_Kinh/daoanh/scripts/build_progress_data.py. Không chạy importer để verify docs.

## 10. Ghi chú cho agent kế tiếp

Đọc task + erratum U + manifest; xác nhận live HEAD/docs hashes trước ghi; giữ T223 ontology khác T357 ETL. Code là writer, Debug read-only independent QA, root final QA. Phases future phải kiểm schema thật và dừng khi contract thiếu; không invent migration/DB status. Kế hoạch đã approved không là production write trong lượt docs này. Logs 02–05 chứa final checks; tasktodo giữ một U+FFFD có sẵn, không tăng. Observation 4s timeout: ECONNREFUSED 127.0.0.1:37700, không lưu được; 07-observation.json ghi đúng kết quả local. Docs writer DONE, Debug/root QA pending; không đồng nghĩa task/code/apply DONE.

Root QA follow-up: Dashboard T223.desc formerly showed the historical unresolved-ID warning. The source now has an explicit current Mục tiêu summary: T223 ontology blocked, ETL remediation tracked in T357 and not implemented. Historical warning and report A–T remain below; report begins with current state. Generator rerun after writes; final checks in 08-qa-summary.json, hashes refreshed in 06-outputs-manifest.json. Existing-file write required hash-guarded r+ after UNKNOWN; no bytes were lost.
