---
id: T310
title: "Ánh xạ TTL↔DILA — Admin lập bảng quyết định"
module: Lineage / Data Curation
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Mỗi dòng xung đột/rỗng có quyết định: A020018, A010511, A025951, A004146, 58 dòng ttl_filename rỗng.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T310 — Ánh xạ TTL↔DILA — Admin lập bảng quyết định

## 1. Mục tiêu

Mỗi dòng xung đột/rỗng có quyết định: A020018, A010511, A025951, A004146, 58 dòng ttl_filename rỗng.

## 2. Hiện trạng (đã kiểm 2026-10-10)

API anchor-by-dila báo conflict/unmapped đúng. Gỡ A025951 khỏi Kinh Triệu chưa làm (bị chặn quyền ghi).

## 3. Các bước (agent làm lần lượt)

1) Admin điền bảng. 2) Lưu tệp quyết định.

## 4. Kiểm chứng

Tệp có đủ dòng.

## 5. Không làm trong task này

Không tự quyết định ID.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
