---
id: T03
title: Fuzzy matching title_zh ↔ place (CBETA Catalog) — DEPRECATED
module: CBETA
priority: low
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-19
done_when: N/A — approach đã bị thay thế bằng JOIN trực tiếp (xem T20)
---

# T03 — Fuzzy matching title_zh ↔ place (CBETA Catalog)

## ⚠ DEPRECATED (2026-08-19)

Approach fuzzy matching bị xác định là vi phạm nguyên tắc nội dung hệ thống:
- `cbeta_catalog_place_fuzzy` là bảng code-generated (RapidFuzz string match), không phải authority data
- Kết quả sai: `少室寺` match `少室六門` vì string similarity, không phải vì DILA nói liên quan
- Đã **xóa toàn bộ** block "Kinh Điển Liên Quan · Fuzzy Match" khỏi `app.py` và `places.html`

## Thay thế

Block mới "Kinh Điển Liên Quan" dùng **JOIN trực tiếp**:
- `places_dila.listbibl` → parse T-series refs → JOIN `cbeta_catalog_vn` (Nguyễn Minh Tiến)
- Coverage: 86% T-series, 100% accuracy
- Xem **T20** để biết roadmap đến 100% coverage

## Lịch sử
- 2026-07-29: Tạo task, implement RapidFuzz
- 2026-08-18: Fuzzy rescore endpoint tồn tại trong code (`/api/admin/cbeta/fuzzy_rescore`)
- 2026-08-19: Block UI removed, approach deprecated, T20 created để track gap
