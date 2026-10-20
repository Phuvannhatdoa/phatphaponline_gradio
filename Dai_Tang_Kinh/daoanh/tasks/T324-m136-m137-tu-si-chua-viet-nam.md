---
id: T324
title: "M136 + M137 — Dữ liệu tu sĩ và chùa Việt Nam: viết lại theo SQLite và cổng license"
module: Lineage / VN data
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

# T324 — M136 + M137 — Dữ liệu tu sĩ và chùa Việt Nam: viết lại theo SQLite và cổng license

## 1. Danh sách file phủ bởi task này

- `docs/integration/M136-buddhist-temple-data-extraction-consolidated.md`
- `docs/integration/M137-vietnamese-monk-data-extraction-consolidated.md`

## 2. Việc cần làm

Hai spec đề xuất PostgreSQL/MySQL (dự án dùng SQLite) và scrape nguồn không qua cổng license. Viết một spec gộp mới: nguồn đã qua M1, ghi vào bảng có sẵn, nối T170 và T275. Không cào dữ liệu khi chưa có giấy phép.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
