---
id: T348
title: "Archive Uu-Tien — lô 08: rà soát và phân loại (10 file)"
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

# T348 — Archive Uu-Tien — lô 08: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-2-T75-dream-interpretation-consolidated.md`
- `docs/integration/Uu-Tien-2-T76-meditation-progress-consolidated.md`
- `docs/integration/Uu-Tien-2-T77-study-tracker-consolidated.md`
- `docs/integration/Uu-Tien-2-T78-prayer-beads-counter-consolidated.md`
- `docs/integration/Uu-Tien-2-T79-mantra-tracker-consolidated.md`
- `docs/integration/Uu-Tien-2-T80-incense-management-consolidated.md`
- `docs/integration/Uu-Tien-2-T81-prayer-times-consolidated.md`
- `docs/integration/Uu-Tien-2-T82-temple-manager-consolidated.md`
- `docs/integration/Uu-Tien-2-T83-festival-calendar-consolidated.md`
- `docs/integration/Uu-Tien-2-T84-text-converter-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
