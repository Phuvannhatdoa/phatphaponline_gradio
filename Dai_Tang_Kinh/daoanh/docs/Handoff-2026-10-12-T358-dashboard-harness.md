# Handoff — 2026-10-12 — T358 Harness execution panel

## 1. Bảng thông tin đọc nhanh

| Mục | Kết quả |
|---|---|
| Task/session | T358; docs/sessions/2026-10-12_T358-dashboard-harness/ |
| HEAD đầu phiên | 82bd04876ea0e6046730e040ff820ad430f3f8b1; không stage/commit |
| Focused UI | 8/8 PASS trên snapshot final (24.1s); node --check PASS |
| Generator | PASS exit 0: 291 task, 15 module, 324 endpoint đối chiếu; regex route 319 không phải inventory đầy đủ |
| Guard / dup | Guard PASS; dup FAIL 9 ID lịch sử, T358 không trùng |
| Tester / pipeline | Tester exit 1 (runtime PlaceVN/CDN blocked); pipeline exit 1 tại dup, không ALL TESTS PASSED |
| Preflight / DB / TTL | Không data preflight/apply/migration; 0 production DB/TTL/ETL write |

## 2. Đọc trong 2 phút

Đã thêm panel 15 dòng trong Harness, đủ sequence/specialty/prereq/dev evidence/Admin next action. Report hiện 0 ready, mọi DONE khóa. Khi dev đủ explicit build/tests/QA, Admin nhập đúng ID để lưu admin_reviewed cục bộ; không đổi task/frontmatter/overrides/production.

Admin/root: (1) đọc giới hạn validation; (2) giao Debug QA độc lập trên snapshot rồi root QA; (3) ưu tiên T283 hoặc T287 theo sequence, không coi UI T358 PASS là các task triage đã hoàn tất. Chưa xin Admin build review khi cổng chung còn FAIL.

## 3. Phần chữa dựng và bằng chứng

| Vấn đề | Thực hiện | Đo/kiểm |
|---|---|---|
| Triage chưa hiện trong Harness | Hook HTML + isolated JS/CSS + derived JSON | 15 rows: 11 task + 4 blocker; source/test/report links |
| DONE thiếu dev gate/review boundary | Explicit prerequisite + implementation/tests/independent_qa PASS evidence; typed dialog; exact-content token | Fixture gate/confirmation/reload/stale/no /api/ write PASS |
| Mobile/accessibility/XSS | textContent/allowlist links, table region, native dialog/focus/Escape | Browser fixtures PASS; mobile-review-fixture.png đã xem, rõ nhãn/focus, vừa 375px |

## 4. Cảnh báo bắt buộc

Worktree dùng chung: tasktodo đổi thêm T366 giữa phiên. CAS đã dừng, backup live mới rồi giữ toàn entry T366; không sửa task/code đó. Generated progress gồm trạng thái repo hiện tại. Commit T358 loại data/progress_data.json: remaining diff chỉ T366–T371/module/history khác; T358 record đã ở HEAD và giống live. Working generated snapshot 291 rows giữ nguyên. Không git add thư mục, không đổi default index/ref. HEAD cuối f0025b8 (T366); T358 source/task đã được commit bởi session khác giữa phiên (b46f81b fix: biography không load + AI dịch báo lỗi sai (person.html)), không phải Agent Code stage/commit. Kiểm git log/diff và head-drift-note.json trước chốt patch.

LocalStorage có thể bị người dùng chỉnh/xóa, không authentication hay SSOT. Chỉ claim XSS-safe cho panel mới, không mọi code Dashboard cũ. T274 duplicate ID/coverage thiếu và T200/T223 entity decision không được auto-DONE. TTL ignored, không data restore cho UI này.

## 5. Revert từng task

| Cách | Mất dữ liệu? |
|---|---|
| Revert patch T358 source/docs sau root review; giữ logs | Không DB/TTL |
| Restore 3 file có sẵn từ before backups chỉ sau so hash after-manifest | Không DB; cần giữ concurrent WIP; tasktodo phải dùng bản concurrent-T366, không bản đầu |
| Xóa local receipt bằng DevTools localStorage.removeItem('ptda:harness:admin-review:v1:T283') | Chỉ mất review cục bộ T283, không task/production |

Commit scoped được root giao sau QA PASS; SHA tra git log, không tự nhét hash tạo vòng self-reference. Khi revert: từ visjs-app root dùng git revert --no-edit <SHA-T358>, không git checkout/reset toàn file. Không xóa docs/session để rollback.

## 6. Bảng file tạo/sửa

| File | Thay đổi |
|---|---|
| dashboard/dashboard_process.html | Hook assets/panel và flow nhãn role |
| dashboard/triage_execution.js, .css | Gate/render/confirmation/storage/responsive |
| data/triage_execution_report.json | Audit snapshot + explicit dev conditions |
| tests/t358-dashboard-harness.spec.js | 8 browser acceptance fixtures cô lập |
| tasks/T358-dashboard-harness-agent-execution-panel.md | Task ID/status/scope/acceptance |
| docs/T358-dashboard-harness-execution.md | Contract/source/limits/rollback |
| docs/tasktodo.md | Chỉ thêm T358, giữ T366/concurrent changes |
| data/progress_data.json | Generated bằng script hiện có, không manual edit |
| session + Handoff này | Backup/manifest/logs/screenshot/validation |

## 7. Sai lầm và bài học

exec_command output rỗng/exit 0 không tạo artifact, đã bị bác bỏ là test PASS. Ghi source qua template làm mất regex escaping: syntax check bắt FAIL, đổi sang allowlist segments. Fixture thiếu UTF-8 meta tạo mojibake dù source bytes đúng; đã sửa fixture và 8/8 PASS. Giữ log hai lần thất bại, không xóa lịch sử.

Tester báo lint PASSED nhưng stderr có ProgramFiles/LOCALAPPDATA null và npm lint có || exit 0; không lấy summary này làm bằng chứng lint toàn repo sạch. Relevant source node --check và focused Playwright là bằng chứng trực tiếp. Runtime unrelated PlaceVN FAIL CDN ERR_NETWORK_ACCESS_DENIED/L is not defined; không sửa ngoài scope để che gate.

## 8. Việc chưa xong

1. Debug/root QA PASS được root xác nhận 2026-10-12; root giao commit scoped. Task frontmatter giữ in_progress, cổng chung vẫn FAIL.
2. Cổng chung: 9 duplicate IDs có sẵn + tester runtime CDN/environment; cần scope riêng/root quyết, pipeline chưa PASS, bước sau dup chưa chạy.
3. Các task triage chưa được triển khai trong T358, report 0 ready. Khi evidence thật + QA, writer cập nhật revision/checks/proofs rồi Admin review.
4. Observation §0 đã thử POST timeout 1800ms: ECONNREFUSED, chưa save memory remote; local session đầy đủ.

## 9. Kiểm tra nhanh

Từ daoanh: node --check dashboard/triage_execution.js; node node_modules/@playwright/test/cli.js test tests/t358-dashboard-harness.spec.js --reporter=list --max-failures=1 --output=docs/sessions/<NEW-RUN>/playwright-artifacts; npm.cmd run guard; npm.cmd run dup:ids.

Xem focused-tests-final.json/pipeline.json/tester.json/generator.json trong session; so after-manifest.json. Targeted doc/link checks PASS; 1 U+FFFD tasktodo tồn tại trước và giữ nguyên, block T358 sạch. Live HTML/JS/CSS/report GET localhost:8080 đều 200 (live-http-get.json). Mở http://localhost:8080/dashboard/dashboard_process.html, đến Harness; các DONE hiện khóa; dùng fixture test, không tự đổi report ready để demo live.

## 10. Agent kế tiếp

Đọc task/contract, kiểm hash/current status và WIP trước ghi. Debug chỉ đọc/kiểm độc lập, root điều phối. Không gọi API task-done/undone cũ cho panel; không inferring dev readiness từ task.status hay localStorage. Không đọc/ghi corpus/DB vì UI task. Ghi kết luận DONE/PARTIAL/BLOCKED cùng phạm vi; root cấp riêng commit khi QA đủ. Lưu session observation honest và Handoff theo convention.
