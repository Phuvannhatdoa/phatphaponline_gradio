---
id: T350
title: "Archive Uu-Tien — lô 10: rà soát và phân loại (10 file)"
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

# T350 — Archive Uu-Tien — lô 10: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-3-T109-buddhist-chaplaincy-consolidated.md`
- `docs/integration/Uu-Tien-3-T110-buddhist-engaged-social-work-consolidated.md`
- `docs/integration/Uu-Tien-3-T111-buddhist-language-translation-consolidated.md`
- `docs/integration/Uu-Tien-3-T112-buddhist-pilgrimage-consolidated.md`
- `docs/integration/Uu-Tien-3-T113-buddhist-art-iconography-consolidated.md`
- `docs/integration/Uu-Tien-3-T114-buddhist-festivals-consolidated.md`
- `docs/integration/Uu-Tien-3-T115-buddhist-rituals-consolidated.md`
- `docs/integration/Uu-Tien-3-T116-buddhist-architecture-consolidated.md`
- `docs/integration/Uu-Tien-3-T117-buddhist-history-consolidated.md`
- `docs/integration/Uu-Tien-3-T118-buddhist-comparative-religion-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
