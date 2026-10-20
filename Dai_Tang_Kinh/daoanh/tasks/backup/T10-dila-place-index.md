---
id: T10
title: DILA Place Index + API thống kê/export
module: DILA Authority
priority: high
status: done
depends_on: [T09]
created: 2026-08-13
updated: 2026-08-18
done_when: Trang "DILA Place Index" (bảng + filter) + API search trực tiếp trên SQLite DILA + export CSV/JSON
---

# T10 — DILA Place Index + API thống kê/export

## Mục tiêu
Khoá 4 — "kéo hết" dữ liệu DILA Place lên dashboard: search Place trực tiếp trên DILA SQLite, trang "DILA Place Index" (bảng + filter), API thống kê + export CSV/JSON cho nghiên cứu.

## Cách tiếp cận
- API search Place trên SQLite DILA (không phụ thuộc LIKE mờ).
- Trang DILA Place Index: bảng + filter (category, dynasty, province).
- API thống kê (count theo category/tỉnh/thế kỷ) + export CSV/JSON.
- Sau đó mới refine "Bối cảnh lịch sử & khảo cổ" + CBETA citation theo nguồn DILA.

## Acceptance criteria (checklist)
- [x] API search Place trực tiếp trên DILA SQLite
- [x] Trang DILA Place Index (bảng + filter) hiển thị — /daoanh/admin/dila_index.html
- [x] API thống kê hoạt động — /daoanh/api/dila/stats
- [x] Export CSV/JSON hoạt động
- [x] Không break places_search hiện tại (placevn.html)
