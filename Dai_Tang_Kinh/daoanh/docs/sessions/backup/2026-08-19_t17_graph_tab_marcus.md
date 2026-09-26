# 2026-08-19 — T17: Knowledge Graph Viz thật cho tab "Đồ Thị" + gắn Marcus (T04)

## Mô tả ngắn task

User hỏi tab "🕸 Đồ Thị" trên `places.html` có phải là mạng lưới truyền thừa Marcus không —
phát hiện KHÔNG phải: tab đó dùng dữ liệu hoàn toàn khác (regex-scrape tên trong `places_dila.note`
+ RapidFuzz `cbeta_catalog_place_fuzzy`), không liên quan gì tới `marcus_people_link`/`marcus_networks`
(T04). Người dùng chọn hướng "a": dọn rác fuzzy/regex không đạt chuẩn nguồn 100%, đồng thời hiện
thực hóa đúng T16/T17 (Nexus Points / Knowledge Graph Visualization) và gắn Marcus lên tab này.

## Phân tích trước khi build

- Đọc `tasks/T16-nexus-points.md` + `tasks/T17-knowledge-graph-viz.md` (2 task file gốc, `pending`
  từ 2026-08-13) — xác nhận tab "Đồ Thị" hiện tại chỉ là placeholder tạm (fallback message của
  chính code cũ đã tự ghi "Task T16, T17"), chưa từng được build đúng thiết kế.
- Kiểm tra schema thật (`PRAGMA table_info`) của `places`, `places_dila`, `people`,
  `marcus_reference`, `marcus_networks` — xác nhận **không tồn tại bất kỳ cột nào** liên kết
  person↔place trong toàn bộ DB. `places_dila.raw_xml` là TEI thật (namespace `ns0:`) nhưng không
  có `persName`. → Marcus (person↔person) không thể gắn vào graph của 1 PLACE một cách có nguồn
  dẫn thật; phải làm graph **theo entity type** (place graph riêng, person graph riêng).
- Kiểm tra pattern "Kinh Điển Liên Quan" đã được audit/sửa đúng chuẩn ở chỗ khác trong app.py
  (`api_places_cbeta`, JOIN `places_dila.listbibl` → `cbeta_catalog_vn`, Nguyễn Minh Tiến CC
  BY-SA 4.0) — dùng lại đúng pattern này thay vì fuzzy.

## Thiết kế đã chọn

**Backend (`app.py`):**
1. Viết lại `GET /daoanh/api/places/<id>/graph` — bỏ `persons_mentioned` (regex trên `note`, không
   nguồn) + `text_links` (RapidFuzz). Trả `{ok, entity_type:"place", center, alt_names, nodes, edges}`
   — `alt_names` giữ nguyên (DILA `placeName type="alternative"`, real attribute, verify 7.139/59.164
   dòng có), `nodes`/`edges` xây từ JOIN `listbibl`→`cbeta_catalog_vn` (kinh điển) + `places` cùng
   tỉnh (lân cận, structural).
2. API mới `GET /daoanh/api/monk/<dila_id>/graph` — bọc dữ liệu Marcus đã verify (T04) thành cùng
   format `{center, nodes, edges}`; mỗi edge có `ref` trích dẫn CBETA thật từ `marcus_networks`.

**Frontend (`places.html`):**
3. Thêm `vis-network@10.0.1` (unpkg CDN — cùng bản đã dùng ở `backups/bk-test-tong-phai.html`,
   dự án thientong, giữ nhất quán trong hệ sinh thái visjs-app).
4. `renderGraphTab()` viết lại hoàn toàn: dùng `vis.Network` vẽ canvas thật thay vì HTML card tĩnh;
   click node điều hướng (place→`selectItem()`, person→`selectPerson()` mới); click node person =
   fetch lại graph của chính node đó và vẽ lại quanh nó (lazy load / mở rộng node con, đúng yêu cầu
   T17 checklist).
5. `selectPerson(dilaId, label)` (hàm mới) — entity mode thứ 2 cho `places.html` (trước chỉ có
   place); search box tự thử `/daoanh/api/monk-resolve` song song place-search, dropdown hiện gợi ý
   "👤 Tăng nhân" riêng biệt.

## Bug tự phát hiện + tự sửa trong lúc build

`selectItem()`/`selectPerson()` có đoạn reset chung cho 3 tab con (cbeta/graph/timeline):
`ct.innerHTML = ''`. Trước đây tab "Đồ Thị" chỉ có 1 div rỗng nên vô hại; sau khi thêm cấu trúc con
cố định (`#graph-altnames`, `#graph-canvas`, `#graph-empty`), dòng reset này xoá mất chính các div
đó TRƯỚC KHI `renderGraphTab()` chạy → lỗi `Cannot read properties of null`. Phát hiện qua test
browser thật (không thấy qua đọc code tĩnh), sửa bằng cách loại trừ tab `graph` khỏi innerHTML-reset
(chỉ gọi `_graphNetwork.destroy()` thay thế). Có 2 chỗ giống hệt nhau (trong `selectItem` và
`selectPerson`) — sửa cả hai, verify riêng từng cái qua browser.

## Danh sách file đã tạo/sửa

- `app.py` — viết lại `api_places_graph`, thêm `api_monk_graph` (route mới `/daoanh/api/monk/<id>/graph`)
- `places.html` — thêm CDN vis-network, cấu trúc HTML tab Đồ Thị, `renderGraphTab()` viết lại,
  `selectPerson()` (mới), `runAutocomplete()` cập nhật (gợi ý tăng nhân), fix bug reset innerHTML
- `tasks/T17-knowledge-graph-viz.md` — status → `done`, chi tiết build + test
- `tasks/T16-nexus-points.md` — ghi chú xác nhận không có person↔place link thật trong DB, vẫn `pending`
- `tasks/T04-marcus-glossaries-link.md` — tick "gắn vào places.html", cập nhật cách gắn (qua Đồ Thị, không phải sidebar chính)
- `docs/tasktodo.md` — cập nhật dòng Task 4
- `docs/sessions/2026-08-19_t17_graph_tab_marcus.md` — session log này

## Test đã chạy

curl trực tiếp (port 5000) + browser thật (Claude Browser tool, không chỉ gọi hàm qua console —
có test cả `mousedown` thật trên dropdown item):

```
GET /daoanh/api/places/PL000000023255/graph   → 4 alt_names + 3 node kinh điển (JOIN thật)
GET /daoanh/api/monk/A000005/graph            → 7 edge thầy/trò thật, mỗi edge có ref CBETA
```

Browser: `selectItem` → tab Đồ Thị → canvas 340×340px vis-network render OK · `selectPerson` →
header "· TĂNG NHÂN · DILA" + chip "✓ MARCUS" + graph Marcus render OK · click node học trò
(A000668) → graph vẽ lại quanh Minh Mãn, xác nhận lazy-load OK · gõ "鑑堂一" vào search → dropdown
hiện "👤 Tăng nhân" đúng A000005 → mousedown thật → tự chuyển tab + render OK · chuyển lại place
mode (Shaolin) sau khi ở person mode → không còn state cũ, render đúng lại · không phát sinh console
error mới (2 error còn lại — "Invalid LatLng NaN" trong `doSearch()` khi nhấn Enter, và 1 lỗi 404
không rõ nguồn — đều pre-existing, ngoài scope, chưa điều tra).

## Liên hệ ROADMAP

- Khoá liên quan: Khoá 1 — GIS/DILA Integration Layer, Marcus SNA
- Việc còn lại: T16 (Nexus Points, parse CBETA TEI thật cho person↔place) vẫn `pending` — khi xong
  chỉ cần thêm node `group:"person"` vào response của `/daoanh/api/places/<id>/graph`, renderer
  hiện tại đã hỗ trợ sẵn group này (dùng cho Marcus). term_glossaries thật (Marcus glossary repo)
  vẫn ngoài scope, task riêng sau.
