---
id: T299
title: "M2 — Script diff authority DILA (chỉ đọc, xuất TSV)"
module: Authority / Lineage
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T298]
done_when: |
  Script báo Thêm/Sửa/Xóa so với phiên bản trước, không ghi DB.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T299 — M2 — Script diff authority DILA (chỉ đọc, xuất TSV)

## 1. Mục tiêu

Script báo Thêm/Sửa/Xóa so với phiên bản trước, không ghi DB.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Chưa có. Nguồn: DILA Authority-Databases (CC BY-SA 3.0).

## 3. Các bước (agent làm lần lượt)

1) Lưu hash commit nguồn. 2) So sánh với bản trước. 3) Xuất docs/evidence/…T299_authority_diff.tsv.

## 4. Kiểm chứng

Chạy 2 lần: báo cáo giống nhau; số dòng entity_claims không đổi.

## 5. Không làm trong task này

Không áp dụng diff.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
