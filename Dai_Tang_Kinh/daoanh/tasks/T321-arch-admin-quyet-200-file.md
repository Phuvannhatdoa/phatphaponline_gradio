---
id: T321
title: "Archive — Admin quyết định giữ/xóa ~200 file không mục tiêu"
module: Docs
priority: p3
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Có danh sách giữ/xóa do Admin ký.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T321 — Archive — Admin quyết định giữ/xóa ~200 file không mục tiêu

## 1. Mục tiêu

Có danh sách giữ/xóa do Admin ký.

## 2. Hiện trạng (đã kiểm 2026-10-10)

~200 file tính năng và bản Uu-Tien không có kế hoạch tích hợp.

## 3. Các bước (agent làm lần lượt)

1) Admin đánh dấu từng nhóm. 2) Không xóa nếu chưa duyệt.

## 4. Kiểm chứng

Có tệp quyết định.

## 5. Không làm trong task này

Không xóa file trong _archive khi chưa duyệt.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
