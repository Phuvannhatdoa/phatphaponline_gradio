# Session: Admin Dashboard — Menu Panel Update (tích hợp tính năng đã hoàn thiện)

**Date:** 2026-08-31
**Branch/Task:** Dashboard admin menu update
**Status:** DONE

## Objective
Cập nhật menu panel của dashboard admin (`admin/index.html` — served tại `http://localhost:8080/daoanh/admin`) để thêm các chức năng **đã hoàn thiện cho admin sử dụng** sau quá trình tích hợp, đồng thời xác minh toàn bộ các mục menu trỏ tới trang hợp lệ (không 404) và e2e pass.

## Audit — trang admin hoàn thiện (kết quả khảo sát)
Đã rà soát toàn bộ trang trong `admin/` để xác định trang nào **production-ready + wired API thật** so với demo/test/legacy:

| Trang | Trạng thái | Ghi chú |
|-------|-----------|---------|
| placevn.html | ✅ Canonical | Đạo Ảnh mapping admin home |
| place_update.html | ✅ | Triage place thiếu thông tin |
| keyword_import.html | ✅ | Import chú thích Phật học |
| translation_rules.html | ✅ | Quy Tắc Dịch AI |
| translation_cache.html | ✅ | Cache Bản Dịch |
| cbeta-dashboard.html | ✅ | CBETA analytics |
| panorama.html | ✅ | TTL rebuild workbench |
| **namevimap.html** | ✅ | Name Vi Map (thêm vào menu) |
| **dila_index.html** | ✅ | DILA Place Index browse/export (thêm) |
| **bio-review.html** | ✅ | Bio VI Draft Review (thêm) |
| **missing_hanzi.html** | ✅ | Missing Hán tự override (thêm) |
| **search_all.html** | ✅ | Search All (thêm) |
| places.html | ⚠️ | Demo cũ, bị placevn thay thế → KHÔNG thêm |
| test_entity.html | 🧪 | Trang test/debug → KHÔNG thêm |
| ttl_queue.html | ❌ | Endpoint đã xoá, bị panorama thay → KHÔNG thêm |

## Thay đổi — `admin/index.html`
### Section "Place VN" (thêm 2 mục sau keyword_import, trước translation_rules)
- `namevimap.html` — **Name Vi Map** (icon `fa-language`, màu #8b5cf6) — quản lý tên tiếng Việt, 10 API thật.
- `dila_index.html` — **DILA Place Index** (icon `fa-database`, màu #60a5fa) — tra cứu/xuất DILA place.

### Section "Đại Tạng Kinh" (thêm 3 mục sau cbeta-dashboard)
- `bio-review.html` — **Bio VI Draft Review** (icon `fa-file-pen`, màu #fb923c) — duyệt tiểu sử.
- `missing_hanzi.html` — **Missing Hán tự** (icon `fa-font`, màu #f43f5e) — bổ sung override.
- `search_all.html` — **Search All** (icon `fa-magnifying-glass`, màu #34d399) — tra cứu tổng hợp.

Lưu ý: icon `fa-hanji` không tồn tại trong Font Awesome 6 → dùng `fa-font` thay thế cho Missing Hán tự.

## Verification
- Toàn bộ `<a href>` trong sidebar trỏ tới file tồn tại trong `admin/` (10 target, không 404).
- `http://localhost:8080/daoanh/admin` (gateway 8080) trả HTTP 200 và chứa đủ 5 mục mới.
- Kiểm tra từng trang đích: namevimap, dila_index, bio-review, missing_hanzi, search_all, translation_rules, translation_cache đều trả **HTTP 200**.
- `npm run e2e` (scripts/e2e-test.js): `admin/index.html` → Script block 1 Syntax OK, ALL pages PASSED.
- `npm run lint`: `admin/index.html` được kiểm; lỗi `get_format:185` là false-positive môi trường ESM (đã biết, `|| exit 0`).

## Files Changed
- `admin/index.html` — cập nhật sidebar menu panel.
- `docs/sessions/2026-08-31_admin_menu_panel_update.md` (log này).

## Next Steps
- Commit thay đổi `admin/index.html` + session log (không cuốn theo các thay đổi chưa commit khác từ phiên song song: app.py, search.js, translation_*.html, T73/T75 task files...).
- `admin/ttl_queue.html` bị hỏng (endpoint `/api/fuzzy/matches`, `/api/ttl/old/*`, `/api/ttl/save` không còn) — cân nhắc rewire sang `/api/queue` + `/api/get_ttl/` + `/api/save-ttl` hoặc gỡ nếu không còn dùng.
