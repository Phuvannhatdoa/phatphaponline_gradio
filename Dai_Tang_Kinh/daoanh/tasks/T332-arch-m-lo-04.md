---
id: T332
title: "Archive M-series — lô 04: rà soát và phân loại (10 file)"
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

# T332 — Archive M-series — lô 04: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/M28-online-course-management.md`
- `docs/integration/M29-flashcards-spaced-repetition.md`
- `docs/integration/M30-data-analytics-practice.md`
- `docs/integration/M31-voice-assistant.md`
- `docs/integration/M32-blockchain-research.md`
- `docs/integration/M33-meditation-tracker.md`
- `docs/integration/M34-research-ai-assistant.md`
- `docs/integration/M35-buddhist-calendar.md`
- `docs/integration/M36-decentralized-storage.md`
- `docs/integration/M37-meditation-music.md`

## 2. Việc cần làm

Với từng file: đọc tiêu đề và mục đích; ghi nhãn GIỮ-TÍCH-HỢP (kèm module đích) / VIẾT-LẠI / XÓA-ĐỀ-XUẤT. Không xóa; chỉ ghi nhãn vào bảng trong task này.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
