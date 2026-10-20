---
id: T295
title: "M3 — Trang geo_review.html và API hàng đợi duyệt"
module: Địa lý / GIS
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T294]
done_when: |
  Duyệt từng cặp ứng viên: Chấp nhận/Từ chối/Để sau, có audit.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T295 — M3 — Trang geo_review.html và API hàng đợi duyệt

## 1. Mục tiêu

Duyệt từng cặp ứng viên: Chấp nhận/Từ chối/Để sau, có audit.

## 2. Hiện trạng (đã kiểm 2026-10-10)

admin/geo_review.html chưa có.

## 3. Các bước (agent làm lần lượt)

1) Theo mẫu admin/sources.html. 2) API GET/POST. 3) Thử 10 cặp mẫu.

## 4. Kiểm chứng

Mỗi thao tác có đúng 1 dòng audit.

## 5. Không làm trong task này

Không tự chấp nhận liên kết.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
