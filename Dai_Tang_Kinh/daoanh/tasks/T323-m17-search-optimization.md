---
id: T323
title: "M17 — Tối ưu tìm kiếm: đối chiếu code hiện có"
module: Search
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

# T323 — M17 — Tối ưu tìm kiếm: đối chiếu code hiện có

## 1. Danh sách file phủ bởi task này

- `docs/integration/M17-search-optimization.md`

## 2. Việc cần làm

FTS5 (places_search_fts, lexicon_fts) và /daoanh/api/admin/search_all đã có một phần. Đối chiếu từng tiêu chí M17 (fuzzy 90%, cache 70%, top-3 80%, API 200ms) với đo thật. File T260 mà M17 tham chiếu không tồn tại: tạo lại hoặc bỏ tham chiếu.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
