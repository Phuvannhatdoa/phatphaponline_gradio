---
id: T349
title: "Archive Uu-Tien — lô 09: rà soát và phân loại (10 file)"
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

# T349 — Archive Uu-Tien — lô 09: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-2-T85-incense-calculator-consolidated.md`
- `docs/integration/Uu-Tien-3-T100-system-logs-consolidated.md`
- `docs/integration/Uu-Tien-3-T101-advanced-dharma-analytics-consolidated.md`
- `docs/integration/Uu-Tien-3-T102-buddhist-philosophy-consolidated.md`
- `docs/integration/Uu-Tien-3-T103-buddhist-psychology-consolidated.md`
- `docs/integration/Uu-Tien-3-T104-buddhist-ethics-modern-consolidated.md`
- `docs/integration/Uu-Tien-3-T105-advanced-buddhist-psychology-consolidated.md`
- `docs/integration/Uu-Tien-3-T106-buddhist-psychotherapy-consolidated.md`
- `docs/integration/Uu-Tien-3-T107-neuroscience-buddhist-consolidated.md`
- `docs/integration/Uu-Tien-3-T108-buddhist-counseling-techniques-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
