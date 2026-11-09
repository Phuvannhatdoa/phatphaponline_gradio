---
id: T290
title: "M5 — Sinh credits.html từ data_sources"
module: Attribution
priority: p1
status: coding
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T283]
done_when: |
  credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T290 — M5 — Sinh credits.html từ data_sources

## 1. Mục tiêu

credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB.

## 2. Hiện trạng (đã kiểm 2026-10-10)

credits.html ở gốc daoanh/ đã có, chưa đối chiếu đủ nguồn.

## 3. Các bước (agent làm lần lượt)

1) So danh sách trang với data_sources. 2) Sinh nội dung từ DB (không gõ tay). 3) Kiểm.

## 4. Kiểm chứng

Số nguồn trên trang = số dòng SQL.

## 5. Không làm trong task này

Không đổi giấy phép trong DB.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
