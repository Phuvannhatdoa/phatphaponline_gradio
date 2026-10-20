---
id: T285
title: "M0 — Hook PreToolUse chặn lệnh git ghi"
module: Nền dev & an toàn
priority: p0
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T284]
done_when: |
  Lệnh git ghi (add/commit/reset/push --force) bị chặn bằng hook, có thông báo lý do.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T285 — M0 — Hook PreToolUse chặn lệnh git ghi

## 1. Mục tiêu

Lệnh git ghi (add/commit/reset/push --force) bị chặn bằng hook, có thông báo lý do.

## 2. Hiện trạng (đã kiểm 2026-10-10)

.claude/settings.json chỉ có permissions.deny; không có hooks.

## 3. Các bước (agent làm lần lượt)

1) Viết script Python chạy được trên Windows (không giả định bash). 2) Đăng ký PreToolUse trong settings.json. 3) Thử: git add . bị chặn; git status chạy được.

## 4. Kiểm chứng

Thử trong phiên mới: git add bị chặn với thông báo; git status không bị chặn.

## 5. Không làm trong task này

Không bật lại thư mục .git. Không commit/push.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
