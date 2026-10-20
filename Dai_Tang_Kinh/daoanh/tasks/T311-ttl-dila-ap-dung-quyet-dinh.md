---
id: T311
title: "Ánh xạ TTL↔DILA — Áp dụng quyết định (backup + transaction)"
module: Lineage / Data Curation
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T310]
done_when: |
  DB cập nhật đúng theo bảng quyết định; API không còn xung đột ngoài danh sách chấp nhận.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T311 — Ánh xạ TTL↔DILA — Áp dụng quyết định (backup + transaction)

## 1. Mục tiêu

DB cập nhật đúng theo bảng quyết định; API không còn xung đột ngoài danh sách chấp nhận.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Cần quyền ghi DB (trước đó bị chặn).

## 3. Các bước (agent làm lần lượt)

1) Backup. 2) quick_check. 3) UPDATE trong transaction, kiểm số dòng. 4) COMMIT hoặc ROLLBACK.

## 4. Kiểm chứng

Gọi lại anchor-by-dila; số dòng vn_person_authority không đổi.

## 5. Không làm trong task này

Không xóa dòng.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
