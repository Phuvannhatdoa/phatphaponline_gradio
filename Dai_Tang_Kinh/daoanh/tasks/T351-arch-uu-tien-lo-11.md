---
id: T351
title: "Archive Uu-Tien — lô 11: rà soát và phân loại (10 file)"
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

# T351 — Archive Uu-Tien — lô 11: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-3-T119-buddhist-economics-consolidated.md`
- `docs/integration/Uu-Tien-3-T120-buddhist-bioethics-consolidated.md`
- `docs/integration/Uu-Tien-3-T121-buddhist-environmental-ethics-consolidated.md`
- `docs/integration/Uu-Tien-3-T122-buddhist-digital-ethics-consolidated.md`
- `docs/integration/Uu-Tien-3-T123-buddhist-epistemology-consolidated.md`
- `docs/integration/Uu-Tien-3-T86-chanting-timer-consolidated.md`
- `docs/integration/Uu-Tien-3-T87-prostration-counter-consolidated.md`
- `docs/integration/Uu-Tien-3-T88-malas-counter-consolidated.md`
- `docs/integration/Uu-Tien-3-T89-scripture-export-consolidated.md`
- `docs/integration/Uu-Tien-3-T90-meditation-timer-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
