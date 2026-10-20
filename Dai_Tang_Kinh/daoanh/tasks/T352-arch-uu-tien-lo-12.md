---
id: T352
title: "Archive Uu-Tien — lô 12: rà soát và phân loại (9 file)"
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

# T352 — Archive Uu-Tien — lô 12: rà soát và phân loại (9 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-3-T91-study-planner-consolidated.md`
- `docs/integration/Uu-Tien-3-T92-chakra-balancer-consolidated.md`
- `docs/integration/Uu-Tien-3-T93-aura-reader-consolidated.md`
- `docs/integration/Uu-Tien-3-T94-mantra-composer-consolidated.md`
- `docs/integration/Uu-Tien-3-T95-color-therapist-consolidated.md`
- `docs/integration/Uu-Tien-3-T96-sound-healing-consolidated.md`
- `docs/integration/Uu-Tien-3-T97-chat-room-consolidated.md`
- `docs/integration/Uu-Tien-3-T98-ritual-items-manager-consolidated.md`
- `docs/integration/Uu-Tien-3-T99-data-backup-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
