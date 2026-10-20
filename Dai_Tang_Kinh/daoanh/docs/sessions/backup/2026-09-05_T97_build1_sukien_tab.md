# 2026-09-05 — T97 Build 1: Tab Sự Kiện (Phase 0 Audit + Phase 4 UI)

## Phase 0 — Audit Verified Findings

### Tab Niên Đại
- API: `GET /daoanh/api/places/<id>/timeline` — WORKING
- Nguồn: Wikidata P571 (founding year) + `place_timeline_events` (3,688 rows) + `time_periods` (117,429 rows)
- CLAUDE.md ghi `time_periods = 0 rows` là **SAI** — thực tế 117,429 rows (115,921 có start_year)
- 181 places có Wikidata QID mapping trong `geo_cross_ref`

### Tab Sự Kiện
- `renderSukienTab(d)` → `_renderPendingTab('sukien')` → "⚠ Chức năng đang phát triển" — **STUB**
- Không có backend API

### Data có sẵn (không cần schema mới cho Phase 4)

| Bảng | Rows | Dùng cho |
|------|------|---------|
| `nexus_events` | 10,458 | person-place co-mention từ CBETA passages |
| `event_text_link` | 17,284 | person-place links với CBETA ref cụ thể |
| `vn_person_events` | 5,351 | person events (birth/death/active) từ TTL |
| `place_timeline_events` | 3,688 | static events per place |
| `time_periods` | 117,429 | DILA dynasty/era periods |

### POC Thiếu Lâm Tự (PL000000023255, Wikidata Q232771)

| Nguồn | Count |
|-------|-------|
| `place_timeline_events` | 4 (founding 495 CE × 2 src) |
| `nexus_events` | 24 (monks từ 唐高僧傳) |
| `event_text_link` | 31 (cbeta refs T50n2060_p...) |

Sample nexus: Thích Huyền Trang (A009306) · ppb:7320 · 唐高僧傳  
Sample link: T50n2060_p0457c16 (exact span)

---

## Build 1 — Tab Sự Kiện

### Backend (app.py — sau line 6152)

Thêm route `GET /daoanh/api/places/<id>/events`:
- Query `nexus_events` LEFT JOIN `people` ON `p.id = ne.person_dila_id`
- Query `event_text_link` LEFT JOIN `people` ON `p.id = etl.entity_id`
- Dedup bằng `(entity_id, cbeta_ref)` set
- Return `{ok, dila_id, total, nexus_events[], text_links[], note}`
- Evidence-first: mỗi record có `passage_id` hoặc `cbeta_ref`

**Bug fix trong quá trình build:**  
`people.id` thay vì `people.dila_id` — `people` table dùng `id` field (DILA person IDs: A000001...) không phải `dila_id`.

### Frontend (places.html)

- Thay `renderSukienTab(null)` → `loadSukienTab(placeId)` trong tab switch handler
- Thêm `loadSukienTab(placeId)`: fetch `/api/places/<id>/events` → `renderSukienTab(d)`
- Thêm `renderSukienTab(d)`: 2 section cards:
  1. "Tăng Nhân Đề Cập Trong Kinh Điển" — nexus_events với name_vi + source_book + passage_id badge
  2. "Trích Dẫn Kinh Điển Cụ Thể" — text_links với cbeta_ref badge (📖 T50n2060_p...)
- Empty-state khi không có data (không lỗi)
- Footer: "Nguồn: CBETA · evidence-first"

### Verify (direct DB — server chưa restart)

```
nexus_events Thiếu Lâm Tự: 24 records, name_vi PASS
event_text_link Thiếu Lâm Tự: 31 records, cbeta_ref PASS
py_compile app.py: OK
```

Server cần restart để test live UI. Chạy `launch.bat`.

---

## Files thay đổi

| File | Thay đổi |
|------|---------|
| `app.py` | Thêm route `api_places_events` (T97 — ~70 lines) |
| `places.html` | `loadSukienTab` + `renderSukienTab` thật (thay stub) |
| `docs/sessions/2026-09-05_T97_build1_sukien_tab.md` | Session log này |
| `tasks/T97-timeline-event-evidence-layer.md` | Status update |

## Rollback

```bash
git revert <sha>
```

Rollback sạch: chỉ xóa route + restore stub `renderSukienTab`. DB không thay đổi.

## Kế tiếp

- **Phase 2**: Deterministic time mention parser cho raw Hán văn (regex → precision flag)
- **Phase 3**: Admin UI tạo/duyệt event candidate
- Cần restart server và verify UI Tab Sự Kiện với Thiếu Lâm Tự
