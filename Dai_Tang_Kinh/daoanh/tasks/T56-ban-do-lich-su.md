---
id: T56
title: "Bản Đồ Lịch Sử — Dynasty Map & Temporal Slider"
module: GIS / Timeline / UI
priority: medium
status: pending
depends_on: [T21, T31, T32, T39]
created: 2026-08-26
updated: 2026-08-26
done_when: >
  Bản đồ hiển thị chùa qua các triều đại với overlay ranh giới lịch sử,
  temporal animation slider theo năm lập chùa, marker cluster màu theo triều đại.
  Không ghi đè Leaflet map + Tab Bản Đồ hiện có.
---

# T56 — Bản Đồ Lịch Sử (Dynasty Map & Temporal Slider)

## Mục tiêu
Thêm lớp lịch sử lên bản đồ hiện có: hiển thị chùa theo triều đại + animation theo thời gian.

## Hiện Trạng (Codebase)
- Leaflet + MarkerCluster map trên places.html/placevn.html (DONE)
- `lineage_chronology`: 3,196 rows có dynasty, century, GPS coords
- Tab Niên Đại (T21): timeline theo từng place — `GET /daoanh/api/places/<id>/timeline`
- `GET /daoanh/api/places/unified?dynasty=` — GPS locations + dynasty filter
- `GET /daoanh/api/chronology/events?dynasty=` — event query
- `_get_dynasty_context()` — DILA time_periods lookup (dynasty name, era, start year)
- T39 Wikidata P571 spatial — ~1,500 founding dates pending import
- BGIS/T31 — 33 GPS cross-refs (KHÔNG có founding date)

## Khoảng Trống (Gap)
- Bản đồ hiện dùng **tile layer hiện đại**, không có ranh giới triều đại lịch sử
- Chưa có temporal animation slider (năm lập chùa)
- Chưa có marker cluster màu theo triều đại
- Tab Bản Đồ (`data-t="bandoo"`) hiện là placeholder

## Subtasks

### T56a — Temporal Slider Data
- Cần 1 trường `founding_year` gộp được cho map-level query
- Nguồn: `lineage_chronology` (3,196) + `place_timeline_events` (nếu có) + Wikidata P571 (T39)
- Bảng mới `map_chronology(place_id, lat, lng, founding_year, dynasty)` — precomputed cho hiệu năng
- KHÔNG thêm cột vào `places_dila` (bất biến) — bảng cô lập riêng

### T56b — Map Layer Theo Triều Đại
- Route: `GET /daoanh/api/places/map-timeline?min_year=&max_year=&dynasty=`
- Trả về clusters + markers với `founding_year` + `dynasty`
- Frontend: filter/dropdown triều đại + color code

### T56c — Temporal Animation Slider
- Slider năm (vd 100–2000 CE) — kéo → markers lập chùa trong năm đó nổi bật
- Animation play/pause when dragging
- Dùng `map_chronology.founding_year`

### T56d — Tích Hợp Vào Tab Bản Đồ
- Hoàn thiện tab Bản Đồ placeholder → map lịch sử tương tác
- Giữ Leaflet map hiện có làm nền + layer lịch sử overlay

## API Changes
- New: `GET /daoanh/api/places/map-timeline`
- New: `GET /daoanh/api/places/map-timeline/dynasties` — list dynasties + year range

## Frontend
- Update: `places.html` tab Bản Đồ — map lịch sử + slider
- Giữ nguyên Leaflet map + MarkerCluster

## Không Xung Đột Với
- Leaflet map hiện có (overlay layer mới, không thay thế)
- T21/T31/T32 — dùng lại founding dates, không sửa
- T31 BGIS — không dùng cho founding date (chỉ GPS)

## Ghi chú triển khai 2026-10-08 — PHƯƠNG ÁN (b)

**Admin đã chọn phương án (b): KHÔNG tạo bảng `map_chronology`.** Route API query
runtime trực tiếp, không bảng precompute.

**Phát hiện khi audit (sửa giả định sai trong spec gốc):**
- `lineage_chronology` **KHÔNG có GPS/place_id** — bảng này chỉ có 2 category:
  `person` (46.944 dòng) và `work` (2.616 dòng), **0 dòng category `place`**. Giả
  định "3.196 rows có dynasty, century, GPS coords" trong mục Hiện Trạng phía
  trên là **sai** — không áp dụng được cho T56.
- Nguồn founding year/GPS thật dùng được: `place_timeline_events` (3.688 dòng,
  PL id, `event_type='founding'` có 2.251 dòng có `year`) JOIN `places_dila`
  (GPS `geo_lat`/`geo_long`, 3.595/3.688 dòng khớp có GPS).
- Dynasty không có cột sẵn trong `place_timeline_events` — suy từ `founding_year`
  qua hàm có sẵn `_get_dynasty_context()` (hardcoded CE range, KHÔNG tự suy từ
  note/era theo quy tắc evidence-first `docs/rules/data-integrity.md`).

**Đã làm (T56a + T56b — không cần bảng mới):**
- `GET /daoanh/api/places/map-timeline?min_year=&max_year=&dynasty=&limit=`
- `GET /daoanh/api/places/map-timeline/dynasties`
- Cả hai chỉ SELECT trên `place_timeline_events`/`places_dila`/`namevi_map_places`,
  bọc `try/except sqlite3.OperationalError` → trả rỗng có `warning:"schema_lag"`
  nếu VPS thiếu bảng, không sập route.

**KHÔNG làm (ghi rõ để không ai hiểu nhầm):**
- **T56c (Temporal Animation Slider)** — chưa làm phần UI play/pause kéo slider.
- **T56d (Tích hợp tab Bản Đồ)** — **không đụng** tab `data-t="bandoo"` hiện có
  trong `places.html`: tab này **không phải placeholder** như mô tả cũ — nó đã
  render mini-map Leaflet cho entity đang chọn (`renderBandooTab()`,
  `places.html` dòng ~10728). Route mới (`map-timeline`) là API cho một bản đồ
  lịch sử toàn cục/theo triều đại — khác mục đích với tab per-entity hiện có;
  ghép UI cho đúng sẽ cần quyết định thiết kế (dùng tab riêng hay overlay lên map
  chính `#map`) — để Admin chốt trước khi làm UI, tránh phá tab đang hoạt động.

**Test đã chạy:** `python -m py_compile app.py` OK; `app.test_client()` cho cả
hai route: lọc `min_year/max_year`, lọc `dynasty=唐` (đã phát hiện và sửa 1 bug
logic: filter dynasty áp SAU khi SQL đã LIMIT theo năm tăng dần → bỏ sót triều
đại muộn; sửa bằng cách fetch hết rồi lọc Python khi có `dynasty` filter), biên
rỗng (`min_year=5000`), tham số sai kiểu (`min_year=abc` → fallback bỏ qua, không
500), không tham số (limit mặc định 500). `dynasties` trả 17 triều đại.

## Estimated Effort: ~12 hours
