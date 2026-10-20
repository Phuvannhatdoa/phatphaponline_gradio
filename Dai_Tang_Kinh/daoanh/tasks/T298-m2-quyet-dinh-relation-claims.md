---
id: T298
title: "M2 — Admin quyết định relation_claims và giấy phép biographies"
module: Authority / Lineage
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Có quyết định: tạo bảng relation_claims (tên, cột) hay dùng chỗ có sẵn; DILA xác nhận biographies.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T298 — M2 — Admin quyết định relation_claims và giấy phép biographies

## 1. Mục tiêu

Có quyết định: tạo bảng relation_claims (tên, cột) hay dùng chỗ có sẵn; DILA xác nhận biographies.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Bảng relation_claims chưa có. Giấy phép biographies chưa xác nhận.

## 3. Các bước (agent làm lần lượt)

1) Admin quyết định. 2) Ghi vào tài liệu. 3) Admin liên hệ DILA.

## 4. Kiểm chứng

Có tệp quyết định.

## 5. Không làm trong task này

Không nạp biographies khi chưa xác nhận.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
