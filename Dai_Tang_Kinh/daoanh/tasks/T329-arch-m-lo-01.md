---
id: T329
title: "Archive M-series — lô 01: rà soát và phân loại (10 file)"
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

# T329 — Archive M-series — lô 01: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/M10-education-buddhist.md`
- `docs/integration/M100-all-in-one-dharma-system.md`
- `docs/integration/M11-text-processing-ai.md`
- `docs/integration/M12-knowledge-graph-expansion.md`
- `docs/integration/M124-buddhist-philosophy-mind-science-consolidated.md`
- `docs/integration/M125-buddhist-text-encoding-consolidated.md`
- `docs/integration/M126-buddhist-meditation-technology-consolidated.md`
- `docs/integration/M127-buddhist-learning-analytics-consolidated.md`
- `docs/integration/M128-buddhist-vinaya-modernization-consolidated.md`
- `docs/integration/M129-buddhist-counseling-techniques-expanded-consolidated.md`

## 2. Việc cần làm

Với từng file: đọc tiêu đề và mục đích; ghi nhãn GIỮ-TÍCH-HỢP (kèm module đích) / VIẾT-LẠI / XÓA-ĐỀ-XUẤT. Không xóa; chỉ ghi nhãn vào bảng trong task này.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
