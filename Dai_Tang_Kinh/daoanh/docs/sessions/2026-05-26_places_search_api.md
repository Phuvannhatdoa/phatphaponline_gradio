# Session: Tích hợp Search API cho Places GIS Map

**Ngày:** 2026-05-26
**Task:** Tích hợp search API + frontend cho `places.html` (GIS map)

## Mô tả

Thêm API search và detail cho địa danh, kết nối `places/index.html` vào database `lineage.db` để search trực tiếp thay vì dùng hardcoded data. Search hỗ trợ cả tên Hán, tên Việt, và DILA ID.

## Liên hệ ROADMAP

- **Nguồn liên quan:** DILA (Place Authority)
- **Khoá ROADMAP:** 
  - "Khoá 4 — Mở rộng thế giới - kéo hết dữ liệu DILA Place lên dashboard"
  - Dòng ROADMAP: "Viết API search Place trực tiếp trên DILA SQLite, cho ô search trên cùng truy được mọi Place."
  - Dòng ROADMAP: "Làm trang DILA Place Index (bảng + filter) để duyệt toàn corpus DILA Place."

## Thiết kế / Giải pháp

### Database strategy
- **Bảng `places`** (59k rows, 58k có GPS): query chính — có GPS coordinates để hiển thị marker
- **Bảng `namevi_map_places`** (118k rows, 100% có name_vi): supplement — có tên Việt đầy đủ
- **JOIN strategy**: Query `places` trước (ưu tiên vì có GPS), supplement từ `namevi_map_places` nếu thiếu kết quả
- **Dedup**: Theo `id` (places) / `dila_id` (namevi_map), dùng `seen` set

### API endpoints
1. `GET /daoanh/api/places/search?q=...&limit=20` — search both tables, return GPS + names
2. `GET /daoanh/api/places/<id>` — full detail from places + namevi_map_places LEFT JOIN

### Frontend
- Debounced search (400ms) trên `#searchInput`
- Gọi API → clear markers cũ → add markers mới → flyTo first result
- Select item hiển thị detail pane (hỗ trợ cả hardcoded và API data)

## File đã tạo/sửa

| File | Thay đổi |
|------|----------|
| `app.py` | +2 API endpoints: `api_places_search` (line ~1321), `api_places_detail` (line ~1360) |
| `places/index.html` | +Search JS: `doSearch()`, `addMarkerFromResult()`, `clearDynamicMarkers()`, debounce handler |
| `places.html` | Sync từ `places/index.html` (giữ source template đồng bộ) |
| `docs/sessions/2026-05-26_places_search_api.md` | File này |

## Cách chạy/test

```bash
# Test search API
curl "http://127.0.0.1:5000/daoanh/api/places/search?q=Thiếu"
curl "http://127.0.0.1:5000/daoanh/api/places/search?q=少林&limit=5"

# Test detail API
curl "http://127.0.0.1:5000/daoanh/api/places/PL022435"

# Frontend
# Mở https://phatphaponline.org/daoanh/places/ → gõ "Thiếu Lâm" vào search box
```

## Kết quả test

### API test
```
# Search "Thiếu" → 3 results:
  PL022435: Thiếu Lâm Tự (34.507018, 112.935331)
  PL051442: Thiếu Lâm Cung (23.687076, 120.354204)
  PL000000023255: Thiếu Lâm Tự (34.507018, 112.935331)

# Detail PL022435 → Thiếu Lâm Tự, GPS ok
```

### Tester agent: ✅ 4/4 passed
- lint: ✅
- test: ✅
- e2e: ✅
- e2e:runtime: ✅
