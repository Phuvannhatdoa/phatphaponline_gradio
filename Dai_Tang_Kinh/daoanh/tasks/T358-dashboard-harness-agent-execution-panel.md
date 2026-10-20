---
id: T358
title: "Dashboard Harness — triage và agent execution review"
status: in_progress
created: 2026-10-12
parent: T263
former_ids: []
depends_on: []
---

## Mục tiêu và scope

Hiển thị audit local trong Harness tại dashboard/dashboard_process.html: T283→T284/T290, T287→T288; song song T319/T322/T323/T81/T277/T328; blockers T274/T200–T223, dependency cycles và duplicate IDs. Root đã cấp T358 sau kiểm hai tầng; không tái dùng T223/T356/T357.

Code là writer cho HTML/JS/CSS, derived report, focused UI tests và tài liệu. Debug kiểm độc lập; root QA với Admin. Không sửa task được triage, production DB/TTL/ETL, không gọi API ngoài và chưa commit.

## Contract DONE

DONE chỉ ghi receipt admin_reviewed vào localStorage riêng của panel. Không gọi API task-done, không ghi frontmatter, task_status_overrides hay production. Không suy readiness từ task.status hoặc receipt cũ.

Gate đòi ID hiện hành duy nhất, task không blocked, prerequisites explicit satisfied=true, development.completed=true, checks implementation/tests/independent_qa mỗi loại đúng một PASS và có link evidence nội bộ hợp lệ; mọi check bổ sung cũng PASS. Snapshot hiện tại chưa task nào đủ; mọi DONE khóa. Root/Code chỉ cập nhật report sau bằng chứng và QA, Admin không có nút bỏ qua dev gate.

Admin mở dialog, nhập đúng row/task ID rồi xác nhận; Hủy/Escape không ghi. Receipt gắn exact evidence token/revision/task metadata, đổi điều kiện thì review cũ không còn hiệu lực. localStorage chỉ tiện ích trình duyệt, không phải quyền bảo mật hoặc task SSOT.

## Tiêu chí nghiệm thu

- [x] Đủ các chuỗi/task/blocker và source/locator; lịch sử không bị coi là fresh PASS.
- [x] Focused Playwright test: gate, confirmation, persistence, stale/corrupt storage, XSS, failure, responsive và keyboard.
- [x] Chỉ GET report/progress; không task/DB/API mutation.
- [x] Regenerate progress_data qua script hiện có; guard/dup/tester/pipeline báo đúng kết quả và giới hạn.
- [x] Debug QA độc lập và root QA: root xác nhận QA PASS 2026-10-12. Frontmatter vẫn in_progress; không tự đổi trạng thái task triage.

## Chứng cứ, test và rollback

[Contract](../docs/T358-dashboard-harness-execution.md), [session](../docs/sessions/2026-10-12_T358-dashboard-harness/README.md), [Handoff](../docs/Handoff-2026-10-12-T358-dashboard-harness.md). Backup/hash trước sửa nằm ở before-manifest.json trong session. Rollback source chỉ từ backup sau hash guard hoặc revert commit khi được root giao; không xóa docs, không restore DB. Focused fixture tests không dùng app/production DB.

## Trạng thái

IN_PROGRESS — code/report/docs đã triển khai, focused suite 8/8 PASS; Debug/root QA PASS được root xác nhận; root giao commit scoped. Pipeline dừng ở 9 duplicate IDs có sẵn; tester runtime ngoài scope FAIL, chưa đủ cổng Admin review. Các task triage vẫn giữ frontmatter riêng.
