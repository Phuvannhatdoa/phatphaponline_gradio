---
id: T322
title: "Docs — Cập nhật REALITY_CHECK và 00_PLAN theo trạng thái thật"
module: Docs
priority: p2
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T231]
done_when: |
  REALITY_CHECK và 00_PLAN ghi đúng: M1 đã có T231; số liệu DB/route mới.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T322 — Docs — Cập nhật REALITY_CHECK và 00_PLAN theo trạng thái thật

## 1. Mục tiêu

REALITY_CHECK và 00_PLAN ghi đúng: M1 đã có T231; số liệu DB/route mới.

## 2. Hiện trạng (đã kiểm 2026-10-10)

REALITY_CHECK ghi số cũ (DB 1,4 GB, 156 bảng, 313 route).

## 3. Các bước (agent làm lần lượt)

1) Đo lại số liệu (chỉ đọc). 2) Sửa hai file (có sao lưu).

## 4. Kiểm chứng

Số trong tài liệu khớp lệnh đo.

## 5. Không làm trong task này

Không đổi số liệu bằng tay.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
