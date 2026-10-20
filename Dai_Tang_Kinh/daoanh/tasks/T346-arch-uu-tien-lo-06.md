---
id: T346
title: "Archive Uu-Tien — lô 06: rà soát và phân loại (10 file)"
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

# T346 — Archive Uu-Tien — lô 06: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-2-T55-haptic-suits-consolidated.md`
- `docs/integration/Uu-Tien-2-T56-immersive-sound-consolidated.md`
- `docs/integration/Uu-Tien-2-T57-living-dharma-knowledge-graphs-consolidated.md`
- `docs/integration/Uu-Tien-2-T58-dharma-events-consolidated.md`
- `docs/integration/Uu-Tien-2-T59-dharma-shop-consolidated.md`
- `docs/integration/Uu-Tien-2-T60-dharma-shop-consolidated.md`
- `docs/integration/Uu-Tien-2-T61-augmented-reality-dharma-consolidated.md`
- `docs/integration/Uu-Tien-2-T62-biofeedback-integration-consolidated.md`
- `docs/integration/Uu-Tien-2-T63-emotion-analysis-consolidated.md`
- `docs/integration/Uu-Tien-2-T64-lotus-done-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
