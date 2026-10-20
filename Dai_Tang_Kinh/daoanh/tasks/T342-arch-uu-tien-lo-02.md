---
id: T342
title: "Archive Uu-Tien — lô 02: rà soát và phân loại (10 file)"
module: Archive review
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

# T342 — Archive Uu-Tien — lô 02: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-1-T15-user-behavior-analytics-consolidated.md`
- `docs/integration/Uu-Tien-1-T16-social-media-integration-consolidated.md`
- `docs/integration/Uu-Tien-1-T17-17-search-optimization-consolidated.md`
- `docs/integration/Uu-Tien-1-T18-18-visualization-philosophy-consolidated.md`
- `docs/integration/Uu-Tien-1-T19-19-mobile-integration-consolidated.md`
- `docs/integration/Uu-Tien-1-T20-integration-finalization-consolidated.md`
- `docs/integration/Uu-Tien-1-T21-curation-workflow-consolidated.md`
- `docs/integration/Uu-Tien-1-T22-festivals-community-consolidated.md`
- `docs/integration/Uu-Tien-1-T23-personalized-recommendations-consolidated.md`
- `docs/integration/Uu-Tien-1-T24-blockchain-dana-rights-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
