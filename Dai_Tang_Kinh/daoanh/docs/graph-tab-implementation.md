# Graph Tab Implementation — 2026-09-04

## Đã hoàn thành

| Hạng mục | Trạng thái |
|----------|-----------|
| A — Audit findings | Xong (`docs/graph-tab-audit.md`) |
| B — Quy tắc alias + relationship | Xong |
| C — Thiết kế lại overlay (header, filter chips, legend, canvas, detail panel, nearby strip, rel table) | Xong |
| D — Sidebar alias với toggle | Xong |
| E — Deduplication (alias, nodes, edges) + fallback | Xong |
| F — Responsive (CSS media query), accessibility (aria-pressed) | Xong |
| H — Kiểm thử | Pass (xem bên dưới) |
| I — Tài liệu này | Xong |

---

## Nguyên nhân lỗi (trước khi sửa)

### 1. Alias render 2 lần
`renderGraphTab()` viết alias vào `#graph-altnames` (sidebar).
`_renderGraphMainPanel()` viết alias vào `#gmp-altnames` (overlay).
Cả hai vùng hiện cùng lúc → người dùng thấy 2 danh sách alias.

**Fix:** Xóa hoàn toàn `#gmp-altnames` khỏi overlay HTML và khỏi JS. Alias chỉ còn trong sidebar `#graph-altnames`, có toggle "Hiển thị trong đồ thị".

### 2. Header overlay hiển thị "少室寺 / 少室寺"
`name_vi` trong DB chưa được dịch → fallback về `name_zh`. Cả `gmp-name-vi` lẫn `gmp-name-zh` hiện cùng chuỗi Hán.

**Fix:** `if (nameZh) nameZh.textContent = (lzh && lzh !== lvi) ? lzh : '';` — khi 2 chuỗi giống nhau, ẩn `nameZh`.

### 3. Không có filter, cluster, legend, relationship table
Thiếu hoàn toàn trong implementation cũ.

**Fix:** Thêm toàn bộ theo spec C, D, E.

### 4. Tab re-render mỗi lần switch
`loadTabData` không check cache trước khi gọi API.

**Fix:** Cache bằng `_graphData` — nếu entity chưa đổi thì dùng data cũ.

---

## File thay đổi

| File | Dòng thay đổi | Nội dung |
|------|--------------|---------|
| `places.html` | ~138 | Thêm CSS `.gmp-chip`, `.gmp-chip-on/off`, `.gmp-relrow` |
| `places.html` | ~619–700 | Rewrite HTML `#graph-main-panel` |
| `places.html` | ~840 | Reset `_graphData` + `_graphExpanded` khi `selectItem()` |
| `places.html` | ~1783–1788 | Cache logic: `if (_graphData.center.id === placeId)` |
| `places.html` | ~1830 | Reset `_graphData` + `_graphExpanded` khi `selectPerson()` |
| `places.html` | ~2902–3340 | Rewrite JS: `renderGraphTab`, `_gmpBuildDatasets`, `_gmpBuildRelList`, `_gmpRelRowClick`, `_gmpShowNodeDetail`, `_gmpCloseDetail`, `_gmpToggleFilter`, `_gmpAliasToggle`, `_gmpExpandAll`, `_gmpCollapseAll`, `_renderGraphMainPanel` |
| `app.py` | Không đổi | API đã đúng |

Backup: `docs/sessions/2026-09-04/places.html.bak`

---

## Data model sau khi sửa

### Luồng dữ liệu

```
API /daoanh/api/places/<id>/graph
  → center: { id, label (name_vi or name_zh), label_zh }
  → alt_names: [ string ] — alias DILA, KHÔNG phải node
  → nodes: [ { id, label, label_zh, group, navigable, dila_id?, source?, title? } ]
      group: "text" | "person" | "place"
  → edges: [ { from, to, label, ref?, has_ref? } ]
```

### Phân loại node trong rendering

| group | Hiển thị | Shape | Màu |
|-------|---------|-------|-----|
| center | Luôn hiện | star | vàng #ad7c1c |
| text | Filter "Kinh điển" | box | cyan #0b7a96 |
| person | Filter "Tăng nhân" | dot | cam #c4891a |
| place | Chip "Địa Danh Lân Cận" (strip) | không vào graph | xanh #3a9e6e |
| alias (synthetic) | Filter "Tên thay thế", toggle OFF mặc định | ellipse | tím #6a5f8d |

---

## Quy tắc deduplication

1. **Alias**: `trim() + normalize('NFC')` — skip trùng key.
2. **Nodes**: theo `n.id` — dùng `Set` loại trùng trước khi render.
3. **Edges**: theo `from|to|label` — loại trùng trước khi render.
4. **Relationship table rows**: cùng key `from|to|label` — skip.

---

## Logic cluster

- Ngưỡng: `CLUSTER_THRESHOLD = 5`
- Khi group có > 5 node VÀ group chưa expanded: render 1 gateway node `[N Tăng nhân]`
- Click "Mở rộng" → `_graphExpanded[group] = true` → re-render với nodes đầy đủ
- Click "Thu gọn" → `_graphExpanded = {}` → re-render với cluster
- Cluster reset khi chọn entity mới (`_graphExpanded = {}` trong `selectItem`/`selectPerson`)

---

## Logic filter

State: `_graphFilters = { text, person, place, alias, pending }`
- `text`, `person`, `place`: mặc định `true`
- `alias`: mặc định `false` (toggle qua sidebar checkbox VÀ filter chip)
- `pending`: reserved, mặc định `false`

Khi toggle: `_gmpToggleFilter(btn)` flip state → gọi `_renderGraphMainPanel(_graphData, true)`.
Khi alias sidebar toggle: `_gmpAliasToggle(checked)` đồng bộ state + filter chip + re-render.

---

## Hướng dẫn thêm alias / relationship

### Thêm alias mới
Alias đến từ DILA XML (`placeName type="alternative"`). Không sửa trực tiếp code.
Để thêm alias: cập nhật `places_dila.raw_xml` với `<placeName type="alternative">Tên mới</placeName>`.

### Thêm relationship type mới
Trong `api_places_graph` (`app.py`): thêm vào `nodes[]` và `edges[]`.
Edge cần: `{ "from": id, "to": id, "label": "loại quan hệ tiếng Việt", "ref": "nguồn dẫn" }`.

### Thêm verified status
Hiện `edges` chưa có field `verified`. Để phân biệt nét liền/nét đứt:
- Thêm field `"verified": true/false` vào edge trong API
- Trong `_gmpBuildDatasets`: map `verified=true → dashes:false`, `verified=false → dashes:[4,4]`

---

## Dữ liệu demo hoặc cần kiểm tra

| Loại | Trạng thái | Ghi chú |
|------|-----------|---------|
| `nexus_events` (24 tăng nhân) | Có dữ liệu local | Có thể thiếu trên VPS — app.py đã wrap `try/except` |
| `cbeta_catalog_vn` (3 text hubs) | Có | Join theo `sh_number` |
| `alt_names` (4 aliases) | Từ DILA XML | Học thuật, không tự thêm |
| Edge `verified` field | Chưa có | API chưa trả field này — tất cả edge hiện là nét liền |
| Filter "Chờ kiểm tra" | Chip ẩn (`display:none`) | Reserved cho khi có `confidence < threshold` |
| Địa danh lân cận (cùng tỉnh) | Có nhưng ít | Hiện trong "Địa Danh Lân Cận" strip, không vào graph chính |

---

## Việc cần chủ dự án quyết định tiếp

1. **`name_vi` cho các địa danh lớn**: PL000000023255 (Thiếu Lâm Tự) có `name_vi` NULL → header hiện tên Hán. Cần admin ZQ review và điền "Thiếu Lâm Tự" vào `places.name_vi`.

2. **Thêm field `verified` vào nexus_events edges**: Để phân biệt nét liền/nét đứt theo status. Cần schema migration.

3. **VPS deployment**: Sửa chỉ trong `places.html` (không sửa `app.py`), có thể deploy an toàn qua `scp`.

4. **Filter "Chờ kiểm tra"**: Khi nào có field `confidence` trên edge thì bật chip này.

5. **Mobile**: Trên màn nhỏ (<680px) detail panel ẩn; relationship table là view chính. Có thể cần thêm view mode "list only" cho mobile.

---

## Cách test

```
URL: http://localhost:8080/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255
```

1. Click tab "🕸 Đồ Thị"
2. Sidebar: "Tên Thay Thế (4)" chỉ xuất hiện 1 lần, có toggle, checkbox mặc định OFF
3. Overlay: header entity + filter chips (Kinh điển 3, Tăng nhân 24) + legend + graph
4. Graph: 1 node trung tâm (star), 3 text hub (box), 1 cluster [24 Tăng nhân]
5. Click "Mở rộng" → cluster mở ra nodes riêng lẻ
6. Click "Thu gọn" → về cluster
7. Toggle "Tăng nhân" chip OFF → cluster biến mất
8. Tick checkbox "Hiển thị trong đồ thị" → 4 alias node xuất hiện bên trái với edge dashed
9. Click row "Tục Cao Tăng Truyện" trong bảng → row highlight + detail panel bên phải
10. Switch tab Thực Thể ↔ Đồ Thị 5 lần → graph không nhân đôi node
11. Không có console error
12. Map và các tab khác vẫn hoạt động
