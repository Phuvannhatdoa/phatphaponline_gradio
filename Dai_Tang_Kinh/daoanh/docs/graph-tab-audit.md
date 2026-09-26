# Graph Tab Audit — 2026-09-04

## 1. File đã khảo sát

- `places.html` (4725 dòng)
- `app.py` (route `api_places_graph` — dòng 4415–4548)

---

## 2. Kiến trúc hiện tại

### Layout 2 vùng khi tab Đồ Thị active

| Vùng | Element | Nội dung |
|------|---------|---------|
| Left sidebar | `#tp-graph` → `#graph-altnames` + `#graph-stats` | Alias chips + stats text |
| Right overlay | `#graph-main-panel` (`position:absolute;inset:0;z-index:10`) | Header entity + `#gmp-altnames` + `#gmp-nearby` + `#gmp-canvas` |

Cả hai vùng đều hiện cùng lúc khi graph tab active.

### Flow call khi tab graph click

1. `loadTabData('graph', placeId)` → `fetch('/daoanh/api/places/<id>/graph')` → `renderGraphTab(d)`
2. `renderGraphTab(d)` → update `#graph-altnames` (sidebar) + `#graph-stats` + gọi `_renderGraphMainPanel(d)`
3. `_renderGraphMainPanel(d)` → update `#gmp-altnames` (overlay) + build vis.js

---

## 3. Nguyên nhân lỗi

### 3.1. Alias xuất hiện 2 lần

**Nguyên nhân:** `alt_names` được render ở 2 nơi:

- `renderGraphTab()` dòng 2842–2848 → `#graph-altnames` (sidebar `#tp-graph`)
- `_renderGraphMainPanel()` dòng 2892–2900 → `#gmp-altnames` (overlay `#graph-main-panel`)

Cả hai đều hiện, người dùng thấy alias 2 lần.

### 3.2. Header overlay hiển thị "少室寺 / 少室寺 / PL000000023255"

**Nguyên nhân:** API trả về `center.label` = `label_vi` = `place_row['name_vi'] or name_zh`.
Nếu `name_vi` trong DB chưa được dịch sang tiếng Việt mà lưu luôn tên Hán ("少室寺" hay "少林寺"),
cả `gmp-name-vi` lẫn `gmp-name-zh` đều hiện cùng một chuỗi Hán tự.

Thực tế với PL000000023255 (Thiếu Lâm Tự / 少林寺): API trả `label_vi = name_vi or name_zh`.
Nếu DB có `name_vi = NULL` thì fallback về `name_zh = '少林寺'`.
Kết quả header: "少林寺 / 少林寺 / PL000000023255" — trông như lặp.

### 3.3. Không có filter, cluster, legend, relationship table

Graph chỉ render raw nodes/edges từ API mà không có:
- Filter chips theo nhóm
- Cluster node cho nhóm lớn (24 tăng nhân)
- Legend màu
- Danh sách quan hệ bên dưới

### 3.4. Tab re-render mỗi lần switch

`loadTabData()` đặt `_tabLoaded[key] = true` ngay đầu hàm nhưng KHÔNG kiểm tra trước
khi gọi fetch, nên mỗi lần switch sang tab graph đều gọi lại API và re-render.
Đối với vis.js: `_graphNetwork.destroy()` được gọi trước khi tạo mới — đúng.
Nhưng không cần fetch/render lại nếu entity chưa đổi.

### 3.5. gmp-altnames không nên hiện trong overlay

Spec B.2: alias không được render thành node graph và không được đếm là "địa điểm liên quan".
Hiện tại `gmp-altnames` hiện alias như một dải chip dưới header — người dùng có thể nhầm đây
là node/thực thể riêng.

---

## 4. Dữ liệu API hiện tại (PL000000023255)

Từ API `/daoanh/api/places/PL000000023255/graph`:
- `alt_names`: 4 items (陟岵寺, 僧人寺, 少林, 少室寺) — từ DILA XML
- `nodes`: text nodes (kinh điển CBETA) + place nodes (lân cận cùng tỉnh) + person nodes (nexus_events)
- `edges`: từ center → text/place/person
- Persons: qua `nexus_events` table → có thể ~24 rows (nếu table tồn tại)
- Texts: từ `listbibl` trong `places_dila` → ~3 hubs (Cao Tăng Truyện)

---

## 5. Kết luận

Thay đổi cần làm:
1. Xóa `gmp-altnames` khỏi overlay — alias chỉ hiện trong sidebar `#graph-altnames`
2. Sidebar: thêm toggle "Hiển thị trong đồ thị" cho alias
3. Overlay: thêm filter chips, legend, detail panel, relationship table
4. Cluster node khi >5 nodes cùng nhóm
5. `_renderGraphMainPanel` idempotent: destroy đúng cách trước khi rebuild
6. `loadTabData` graph: cache theo entity ID để không re-fetch khi switch tab

---

## 6. File sẽ sửa

- `places.html` — HTML `#graph-main-panel` (dòng 619–638) + JS `renderGraphTab`/`_renderGraphMainPanel` (dòng 2826–3015)
- Không sửa `app.py` (API data model đã đúng)
