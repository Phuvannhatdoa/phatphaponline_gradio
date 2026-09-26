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

## Estimated Effort: ~12 hours
