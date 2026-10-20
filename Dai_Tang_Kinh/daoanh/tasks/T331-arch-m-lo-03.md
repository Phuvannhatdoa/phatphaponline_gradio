---
id: T331
title: "Archive M-series — lô 03: rà soát và phân loại (10 file)"
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

# T331 — Archive M-series — lô 03: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/M18-visualization-philosophy.md`
- `docs/integration/M19-mobile-integration.md`
- `docs/integration/M20-integration-finalization.md`
- `docs/integration/M21-mobile-responsive-kinh.md`
- `docs/integration/M22-ar-vr-temple-experience.md`
- `docs/integration/M23-personalized-recommendations.md`
- `docs/integration/M24-blockchain-dana-rights.md`
- `docs/integration/M25-holy-days-notifications.md`
- `docs/integration/M26-temple-schedule-management.md`
- `docs/integration/M27-connection-monk-disciple.md`

## 2. Việc cần làm

Với từng file: đọc tiêu đề và mục đích; ghi nhãn GIỮ-TÍCH-HỢP (kèm module đích) / VIẾT-LẠI / XÓA-ĐỀ-XUẤT. Không xóa; chỉ ghi nhãn vào bảng trong task này.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
