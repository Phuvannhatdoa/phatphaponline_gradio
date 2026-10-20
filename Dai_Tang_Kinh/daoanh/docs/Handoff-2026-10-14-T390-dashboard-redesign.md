# Handoff — T390 Dashboard redesign — 2026-10-14

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái |
|---|---|
| Task | T390, in_progress; Debug/root QA PASS, chờ Admin nghiệm thu |
| HEAD đầu phiên | fe6187b39fd6e5f4ded97d3beef5636ac0ac132c; xem git log tại root cho HEAD hiện hành |
| Build | Executive overview, KPI, chart, actions; giữ T358 và nội dung legacy |
| Tests | Focused 14/14 PASS (final2: 1.1m), gồm fallback metadata |
| Cổng chung | guard PASS; dup FAIL 9 ID cũ; pipeline dừng tại dup |
| DB / TTL / ETL | 0 mutation; không chạy data preflight hoặc production apply |
| Commit | Root đã giao scoped commit; xem git log/commit receipt cho SHA |

## 2. Đọc trong 2 phút

Trang đầu có tổng quan → biểu đồ → việc ưu tiên; nav tới agent, Harness, Board và module. Metric đếm record JSON thật; chart không dùng CDN. Snapshot generator: 311 record = 162 done + 34 in_progress + 87 pending + 28 blocked. Risk: 50 task chờ phụ thuộc, 1 SCC, 5 nhóm duplicate trong JSON; khác 9 ID trùng của repo guard. Admin cần xem desktop/mobile, đọc giới hạn snapshot, rồi quyết nghiệm thu sau Debug/root QA.

## 3. Phần đã xây dựng và chứng cứ

Status chart có nhóm rời nhau và bucket other; risk groups có thể giao nhau. Dependency phân giải unique ID/file-stem; SCC không tạo cạnh sai từ prefix T22.1 thành T22. Mỗi nhóm actions tối đa 5 record, dùng priority/owner/deps/checklist/action thật; bỏ sentinel YAML |/> khi generator chưa đọc multiline. Control mới chỉ GET local và nhận event renderer API; dùng textContent và link basename allowlist. Block T358 byte-equivalent; 8 regression tests PASS. Commands, kết quả và screenshot từ fixture actual JSON nằm trong session.

## 4. Cảnh báo bắt buộc

Worktree dùng chung; app.py, places.html và WIP T381 ngoài scope được giữ nguyên. Git chạy từ visjs-app; chưa stage/commit. Status done/checklist không chứng nhận QA production. Legacy DONE/API overrides ngoài T358 vẫn nguyên; control mới không gọi chúng. Timestamp thiếu timezone được ghi rõ; audit T358 ngày 12-10 khác progress snapshot ngày 14-10. Không API trả phí hoặc production apply.

## 5. Revert từng phần

| Phần | Hoàn tác | Mất dữ liệu? |
|---|---|---|
| HTML/tasktodo/generated JSON | Restore before-manifest backup sau exact after-hash guard; có drift thì inverse owned patch, không restore toàn file | Không DB; tránh mất WIP concurrent |
| JS/CSS/tests/task/docs mới | Gỡ hook/owned patch hoặc revert commit khi root cấp SHA; giữ session/Handoff | Không DB |
| Sau commit | git revert --no-edit <SHA> tại visjs-app; hiện chưa có SHA | Chỉ code/docs |

Đọc before-manifest.json và after-manifest.json trong session. Backup không phải commit. Không checkout/reset toàn repo hoặc xóa docs.

## 6. Bảng file tạo/sửa

| File | Thay đổi |
|---|---|
| dashboard/dashboard_process.html | Hook overview, hierarchy, local assets; giữ T358 |
| dashboard/process_overview.js/.css | Data model, chart, actions và responsive |
| tests/t390-dashboard-redesign.spec.js | 6 focused UI cases |
| tasks/T390-dashboard-process-executive-redesign.md | Scope, acceptance, status in_progress |
| docs/T390-dashboard-process-redesign.md | Contract số liệu, evidence, security, rollback |
| docs/tasktodo.md | Chỉ thêm block T390 |
| data/progress_data.json | Generator output working tree; loại khỏi commit vì diff T380/T381 ngoài scope |
| docs/sessions/2026-10-14_T390-dashboard-redesign/ | Backup, manifest, commands, screenshots |
| docs/Handoff-2026-10-14-T390-dashboard-redesign.md | Bàn giao 10 mục |

## 7. Sai lầm và điều đã bị bác bỏ

Assertion Board 4 cột bị kiểm chứng sai: legacy cố ý có 3 cột và ẩn DONE. Đổi test về 3, không sửa Board. Node REPL default 30s timeout/reset khi chờ test/generator; dùng explicit long timeout và yield, không claim PASS khi thiếu log. Visual mobile phát hiện action hiện | do YAML sentinel; renderer bỏ sentinel và dùng fallback, có regression test.

## 8. Việc chưa xong

Debug/root QA độc lập đã PASS 18/18 + final2/2; còn Admin visual nghiệm thu. Root đã giao scoped commit. Pipeline FAIL do 9 ID lịch sử ngoài scope. Tester-agent FAIL: 2/2 runtime ERR_CONNECTION_REFUSED tại localhost:5000. Runner in 3 static bước PASS nhưng lint stderr có ProgramFiles null và exit mask; không coi lint sạch. Production runtime và mobile device thật chưa được chứng nhận.

## 9. Lệnh kiểm tra nhanh

Tại daoanh:

- node --check dashboard/process_overview.js
- node node_modules/@playwright/test/cli.js test tests/t390-dashboard-redesign.spec.js tests/t358-dashboard-harness.spec.js --project=chromium --workers=1 --reporter=line
- npm run guard
- npm run dup:ids

Git chỉ tại visjs-app root. Đối chiếu after-manifest để kiểm hash.

## 10. Ghi chú cho agent kế tiếp

Đọc task/contract/session và log final2; đối chiếu snapshot labels, counts và unknown/missing không giả 0. Kiểm T358 local DONE giữ gate. Không chạy ETL, DB preflight hoặc full importer. Không dùng screenshot fixture làm evidence production. Giữ WIP ngoài scope; chờ root cấp commit. Observation §0 ghi đúng kết quả local khi service down.

## QA độc lập và quyết định commit — 2026-10-14

Root chuyển kết quả Debug và phê chuẩn scoped commit. **18/18 PASS (48.4s) + final snapshot 2/2 PASS (9.4s), tổng 20 checks**; không trình bày như một suite 20 test. Lệnh independent: node node_modules/@playwright/test/cli.js test, config/output riêng tại C:/Users/NAMTHI~1/AppData/Local/Temp/t390-independent-qa-W6rcTb; config lần 1 playwright.config.cjs, lần 2 final-snapshot.config.cjs. Receipt gốc independent-results.json và final-snapshot-results.json được sao nguyên vào session; hash SHA256 lần lượt 32847b70810859498d7a8edca497f673ba335f36dc3e28757fb30dba5d889ec7 và 2ecb304402d5f5c7b089a91cc0df515f0396412d723fca756caa5454ad0b5cd5.

QA xác nhận T3906 + T3588 + 4 probe; final JSON 2 checks riêng. Counts 311=162+34+87+28, risks 50 waiting / 1 SCC / 5 JSON duplicate groups; sáu scalar |, |-, |+, >, >-, >+ fallback về mở task gốc; 375px keyboard/receipt/reload và T358 byte-equivalent. Snapshot kiểm có SHA256 1309242a7d9bdf94631382de9f202a6966dfd6a6be625273ab59209dd6a13cf9.

Common gates vẫn giữ giới hạn: guard PASS; dup/pipeline FAIL 9 ID lịch sử; tester runtime 2/2 ERR_CONNECTION_REFUSED localhost:5000, lint stderr ProgramFiles null bị exit mask. Không chứng nhận full pipeline hoặc production runtime.

**data/progress_data.json không đưa vào commit**: diff có T380 status, T381 record/route/module và git-history ngoài T390. Giữ nguyên snapshot working tree đã regenerate, không stage cả file hoặc sửa tay generated JSON. Task T390 vẫn in_progress chờ Admin nghiệm thu; Debug/root QA scoped đã PASS. Không DB/TTL/ETL mutation.
