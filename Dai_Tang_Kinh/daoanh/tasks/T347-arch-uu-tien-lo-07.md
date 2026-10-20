---
id: T347
title: "Archive Uu-Tien — lô 07: rà soát và phân loại (10 file)"
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

# T347 — Archive Uu-Tien — lô 07: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-2-T65-emotion-analytics-consolidated.md`
- `docs/integration/Uu-Tien-2-T66-multi-device-sync-consolidated.md`
- `docs/integration/Uu-Tien-2-T67-chatbot-consolidated.md`
- `docs/integration/Uu-Tien-2-T68-mini-guidance-consolidated.md`
- `docs/integration/Uu-Tien-2-T69-sangha-connection-consolidated.md`
- `docs/integration/Uu-Tien-2-T70-mindfulness-stats-consolidated.md`
- `docs/integration/Uu-Tien-2-T71-retreat-management-consolidated.md`
- `docs/integration/Uu-Tien-2-T72-ritual-scheduler-consolidated.md`
- `docs/integration/Uu-Tien-2-T73-scripture-search-consolidated.md`
- `docs/integration/Uu-Tien-2-T74-community-forums-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
