---
id: T318
title: "Archive — Dịch và xác minh (M44, M85, M94) sau T308"
module: Editorial / LLM Translation
priority: p3
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T308]
done_when: |
  Spec ghi rõ quan hệ với T170 (xác minh tên) và T269 (quy tắc dịch).
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T318 — Archive — Dịch và xác minh (M44, M85, M94) sau T308

## 1. Mục tiêu

Spec ghi rõ quan hệ với T170 (xác minh tên) và T269 (quy tắc dịch).

## 2. Hiện trạng (đã kiểm 2026-10-10)

Ba file trong _archive/M-series.

## 3. Các bước (agent làm lần lượt)

1) Đọc ba file. 2) Viết spec gộp, nối T170/T269.

## 4. Kiểm chứng

Không trùng quy tắc T269.

## 5. Không làm trong task này

Không gọi LLM mới.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
