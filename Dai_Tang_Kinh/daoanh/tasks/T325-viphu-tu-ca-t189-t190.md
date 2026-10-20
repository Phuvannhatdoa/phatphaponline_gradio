---
id: T325
title: "Viphu tu ca T189 + T190 — Ví dụ tra cứu Cử nhân và Tiến sĩ (5 ví dụ mỗi bên)"
module: Search examples
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

# T325 — Viphu tu ca T189 + T190 — Ví dụ tra cứu Cử nhân và Tiến sĩ (5 ví dụ mỗi bên)

## 1. Danh sách file phủ bởi task này

- `docs/integration/T189-viphu-tu-ca-cuu-tri.md`
- `docs/integration/T190-viphu-tu-ca-tri.md`

## 2. Việc cần làm

Đã có kết quả thực tế cho 5 truy vấn mỗi bên (ví dụ 404 cho /daoanh/api/search). Admin xác nhận trạng thái PENDING của hai file; sau đó tạo bảng kết quả đo lại trên server hiện tại.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
