---
id: T438
title: "BUG-051: /daoanh/places lineage arrows missing (dark background, no arrows)"
status: done
created: 2026-10-20
updated: 2026-10-21
done_when: "Search 'Nghĩa Huyền' trên /daoanh/places hiện lineage tree với mũi tên teacher→student, không còn nền đen trống; console/network sạch lỗi liên quan."
---

## Triệu chứng

- Route: `http://127.0.0.1:8080/daoanh/places`
- Case: Search "Nghĩa Huyền" (hoặc bất kỳ monk nào)
- Kết quả search monk: hiện bình thường (✅)
- Lineage tree visualization: mũi tên teacher → student KHÔNG hiện (❌)
- Background khu vực lineage: đen xì (dark/black), trống

## Nguyên nhân nghi ngờ (chưa xác minh)

- VisJS/D3.js library load lỗi (404/CDN block)
- CSS khiến arrow/SVG bị ẩn (màu trùng nền, opacity, z-index)
- Canvas/SVG container dimensions = 0
- Data API không trả edges/relations cho node này
- JS exception chặn render trước khi vẽ arrow

## Phạm vi dự kiến

- Audit: mở browser, navigate `/daoanh/places`, search "Nghĩa Huyền", scroll tới lineage section.
- Thu thập: screenshot, console errors, network log (JS/CSS asset status), DOM inspect (`<svg>`/`<canvas>` có mặt? dimensions?).
- Trace root cause theo 1 trong các lớp: library/CDN | CSS | data/API | JS resolver/renderer.
- Sửa đúng lớp gây lỗi, fix nhỏ nhất. Không hard-code dữ liệu riêng cho "Nghĩa Huyền".
- Backup file sẽ đổi vào `docs/sessions/2026-10-20/BUG-051/` trước khi sửa.
- Không git commit (theo yêu cầu).

## Kết quả mong đợi

- Lineage tree hiện mũi tên nối teacher → student đúng schema/data thật.
- Không regression các tab/route khác (Events, Nexus, search khác).

## Root cause đã xác minh (2026-10-20)

Lớp gây lỗi: `renderer | layout` (UI thuần, không phải data/API — API `/daoanh/api/monk/<id>/lineage-tree` luôn trả đủ nodes/edges).

1. **CSS (chính):** `#lineage-inspector` (`places.html:745`) khai báo `flex:0 0 300px` nhưng thiếu `min-width:0`. Nội dung dài không ngắt dòng được (bio DILA, URL CBETA/Wikipedia) đẩy panel giãn tới 437px, bóp `#lineage-canvas` (vis.Network container) xuống còn 172×430px → cây vẫn có 80 nodes/79 edges nhưng canvas quá nhỏ nên hiện ra như ô đen trống.
2. **Race condition + camera lệch (phụ, lộ rõ với cây lớn có ancestor-spine T152):** trong `_renderHierarchyTree()` (`places.html:~6864-6886`), code gọi `_lineageNetwork.focus(center,...)` nhưng biến module-level `_lineageNetwork` chỉ được gán SAU đó (`_lineageNetwork = network;` ở line ~7118) — nếu sự kiện `afterDrawing` bắn trước, focus() không chạy, camera lệch khỏi node (đo được: camera x=4920 trong khi node trung tâm x=0).

## Fix đã làm

- `places.html:745` — thêm `min-width:0;max-width:300px;overflow-x:hidden` cho `#lineage-inspector`.
- `places.html:~6871-6886` — dùng closure `network` (instance vừa tạo) thay vì biến module-level `_lineageNetwork` khi gọi `.focus()`; thêm safety re-focus sau 150ms để bù layout engine (blockShifting/edgeMinimization) dịch tiếp vị trí node sau lần `afterDrawing` đầu.

Backup trước khi sửa: `docs/sessions/2026-10-20/BUG-051/places.html.bak-20261020_182252`.
Test: search "Nghĩa Huyền" (A003627) và "Mã Tổ Đạo Nhất" (A038890) trên browser thật, cả Cây DILA lẫn Phả hệ mở rộng — mũi tên hiện đúng, không đen, không lỗi console. Chi tiết: `docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md`.

## Xác nhận DONE

Admin xác nhận DONE 2026-10-21.

**Admin xác nhận DONE (2026-10-26).** Báo cáo: docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md (BUG-051). Commit docs xem git log.
