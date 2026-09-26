---
id: T17
title: Knowledge Graph Visualization (frontend graph viz)
module: DILA Integration Layer
priority: low
status: done
depends_on: []
created: 2026-08-13
updated: 2026-08-19
done_when: Trang hiển thị đồ thị entity (person/place/text + edges) tương tác được
---

# T17 — Knowledge Graph Visualization (frontend graph viz)

## Mục tiêu
DEV_HISTORY audit 2026-08-11: không có frontend graph viz cho entity — P0 trong competitive roadmap. Cần hiển thị đồ thị tri thức entity (tương tự visjs/D3 đã dùng trong thientong).

## Cách tiếp cận
- Chọn thư viện (vis-network/D3) tương thích dark theme.
- API trả graph cho entity (nodes person/place/text + edges relation/citation).
- Trang/sidebar hiển thị, click node → navigate entity.
- Hỗ trợ mở rộng node con.

## Cập nhật 2026-08-19 — Build xong (tab "🕸 Đồ Thị", `places.html`)

**Bối cảnh:** tab "Đồ Thị" đã tồn tại từ trước nhưng chỉ là placeholder tạm dùng regex-scrape
(`persons_mentioned` trên `places_dila.note`, không có nguồn authority) + RapidFuzz
(`cbeta_catalog_place_fuzzy`) — vi phạm rule content-integrity (CLAUDE.md, case 2026-08-19). Dọn
sạch 2 phần đó và build lại đúng thiết kế T16/T17 gốc.

**Đã build:**
- Thư viện: `vis-network@10.0.1` (unpkg CDN) — cùng phiên bản/CDN đã dùng ở `backups/bk-test-tong-phai.html` (dự án thientong), giữ nhất quán.
- API `GET /daoanh/api/places/<id>/graph` — viết lại: bỏ `persons_mentioned` (regex, không nguồn) + `text_links` fuzzy; thay bằng JOIN `places_dila.listbibl` → `cbeta_catalog_vn` (cùng pattern "Kinh Điển Liên Quan" T-series đã audit 2026-08-19), trả `{center, nodes, edges, alt_names}`.
- API mới `GET /daoanh/api/monk/<dila_id>/graph` — bọc dữ liệu Marcus SNA đã verify (T04: `marcus_people_link`/`marcus_networks`) thành cùng format `{center, nodes, edges}`; mỗi edge có `ref` trích dẫn CBETA thật.
- `places.html`: `renderGraphTab()` viết lại dùng `vis.Network` thay vì HTML card tĩnh; `<div id="graph-canvas">` mới trong tab panel; click node điều hướng (place→`selectItem()`, person→`selectPerson()` mới thêm) — lazy load: click 1 node person sẽ fetch lại `/monk/<id>/graph` của chính node đó và vẽ lại đồ thị quanh nó (mở rộng node con đúng yêu cầu T17).
- `selectPerson(dilaId, label)` (mới) — entity mode thứ 2 cho `places.html` (trước đây chỉ có place); search box tự thử `/daoanh/api/monk-resolve` song song với place search, gợi ý "👤 Tăng nhân" riêng trong dropdown.
- Bug tự phát hiện + tự sửa trong lúc build: `selectItem()`/`selectPerson()` reset tab-panel bằng `ct.innerHTML=''` — xóa mất luôn `#graph-canvas`/`#graph-altnames` (con cố định mới thêm) trước khi `renderGraphTab` chạy. Fix: bỏ qua innerHTML-reset riêng cho tab `graph`, gọi `_graphNetwork.destroy()` thay thế.

**Test đã chạy (curl + browser thật, Claude Browser tool):**
- `GET /places/PL000000023255/graph` (Thiếu Lâm Tự) → 4 alt_names thật + 3 node kinh điển (JOIN cbeta_catalog_vn) — verify OK.
- `GET /monk/A000005/graph` → 7 edge thầy/trò thật (1 thầy + 6 trò), mỗi edge có `ref` CBETA — verify OK.
- Browser: `selectItem('PL000000023255')` → tab Đồ Thị → canvas render đúng (340×340px, vis-network DOM xác nhận qua `innerHTML`) — PASS.
- Browser: `selectPerson('A000005', ...)` → header đổi "· TĂNG NHÂN · DILA", chip "✓ MARCUS", đồ thị Marcus render — PASS.
- Browser: click node học trò (giả lập gọi lại `selectPerson('A000668', ...)`, đúng code path click handler dùng) → chuyển sang đồ thị của A000668 (Minh Mãn), xác nhận lazy-load hoạt động — PASS.
- Browser: search box gõ "鑑堂一" → dropdown hiện "👤 Tăng nhân" đúng A000005 → click → tự chuyển tab Đồ Thị + render — PASS (test qua `mousedown` event thật, không chỉ gọi hàm trực tiếp).
- Không phát sinh console error mới (2 error còn lại trong console — "Invalid LatLng NaN" ở `doSearch()` khi bấm Enter, và 1 lỗi 404 không rõ nguồn — đều **pre-existing**, không liên quan tới thay đổi lần này; chưa điều tra thêm vì ngoài scope).

**Còn thiếu để "hoàn thiện" đúng nghĩa T16 gốc:** node "person" cho một PLACE (vd: "tăng nhân từng trụ trì/tu tại chùa X") vẫn CHƯA làm được — không có bất kỳ cột nào trong `places`/`places_dila`/`people` liên kết person↔place (đã kiểm tra schema, xác nhận không tồn tại). Đây chính là việc T16 (Nexus Points, parse CBETA TEI thật `<div type="event" where="#PLxxx"><persName>`) cần làm — vẫn `pending`, xem `tasks/T16-nexus-points.md`. Khi T16 xong, chỉ cần thêm node group "person" vào response của `/daoanh/api/places/<id>/graph` — renderer vis-network hiện tại đã hỗ trợ sẵn (group `person` đã có màu/logic điều hướng).

## Acceptance criteria (checklist)
- [x] API trả graph entity (nodes + edges) — 2 endpoint (place + person), cả 2 đều 100% nguồn dẫn
- [x] Frontend render đồ thị dark theme — vis-network, token `daoanh-design.css`
- [x] Click node → navigate — verify cả place→place và person→person
- [x] Mở rộng node con (lazy load) — click person node tự fetch + vẽ lại quanh node đó
