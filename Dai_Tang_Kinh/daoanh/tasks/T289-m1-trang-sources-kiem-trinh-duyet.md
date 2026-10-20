---
id: T289
title: "M1 — Kiểm trang admin/sources.html trên trình duyệt"
module: Data Governance / License Gate
priority: p1
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T288]
done_when: |
  Trang sources.html hiển thị 4 chỉ số, bảng lọc được, panel chi tiết, đổi trạng thái có audit.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T289 — M1 — Kiểm trang admin/sources.html trên trình duyệt

## 1. Mục tiêu

Trang sources.html hiển thị 4 chỉ số, bảng lọc được, panel chi tiết, đổi trạng thái có audit.

## 2. Hiện trạng (đã kiểm 2026-10-10)

admin/sources.html có sẵn (31 chữ "source"); chưa kiểm đủ tiêu chí M1.

## 3. Các bước (agent làm lần lượt)

1) Mở trang qua gateway 8080. 2) Kiểm từng tiêu chí M1. 3) Chụp màn hình điện thoại và máy tính.

## 4. Kiểm chứng

Chụp màn hình; đếm 25 nguồn đúng trạng thái.

## 5. Không làm trong task này

Không đổi trạng thái nguồn thật nếu không có Admin.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
