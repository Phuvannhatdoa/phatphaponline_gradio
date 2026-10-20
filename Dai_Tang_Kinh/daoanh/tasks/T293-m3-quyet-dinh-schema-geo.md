---
id: T293
title: "M3 — Admin quyết định schema geo_cross_ref"
module: Địa lý / GIS
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Có quyết định bằng văn bản: thêm những cột nào, có tạo bảng geo_review_queue không.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T293 — M3 — Admin quyết định schema geo_cross_ref

## 1. Mục tiêu

Có quyết định bằng văn bản: thêm những cột nào, có tạo bảng geo_review_queue không.

## 2. Hiện trạng (đã kiểm 2026-10-10)

geo_cross_ref 190 dòng, có confidence, chưa có cột độ chính xác riêng.

## 3. Các bước (agent làm lần lượt)

1) Admin trả lời. 2) Ghi vào tài liệu quyết định.

## 4. Kiểm chứng

Có tệp quyết định.

## 5. Không làm trong task này

Không đổi DB trong task này.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
