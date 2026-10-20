---
id: T328
title: "Cline audit T253 — Tham chiếu person import (đã xong)"
module: Person import
priority: p3
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phủ toàn bộ, T323+)
depends_on: []
done_when: |
  Mọi file trong danh sách được rà soát và có nhãn; Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Task chỉ đọc và ghi nhãn trong tài liệu; không xóa file, không đổi DB.
outcome: >
  2026-10-10: tạo task phủ folder docs/integration. Chưa bắt đầu.
---

# T328 — Cline audit T253 — Tham chiếu person import (đã xong)

## 1. Danh sách file phủ bởi task này

- `docs/integration/2026-10-06-person-import-phase0-audit.md`

## 2. Việc cần làm

Đã DONE theo T253. Chỉ giữ làm tham chiếu. Kiểm lại hai blocker P0-1 và P0-2 đã được Admin chốt chưa; nếu chưa thì mở task riêng.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
