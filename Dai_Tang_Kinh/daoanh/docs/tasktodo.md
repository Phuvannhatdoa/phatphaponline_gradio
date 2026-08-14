# TASKTODO — Đạo Ảnh Dev Roadmap

**Cập nhật:** 2026-08-14
**Context:** So sánh GUI thật (phatphaponline.org) vs docs/progress.md

> **Trạng thái tasks:** Task 1 ✅, Task 2 ✅, Task 3 ✅, Task 4 ✅, Task 5 ✅ (2026-07-29), Task 6 ⏭️ tiếp theo, Task 9 ✅ (2026-08-14)

---

## Trạng thái tổng quan

| Module | GUI | Docs | API | Task |
|--------|-----|------|-----|------|
| Landing Page `/` | ✅ | ✅ | N/A | — |
| Dashboard `/daoanh/admin/` | ✅ stats hiển thị | ✅ | ✅ `/daoanh/api/admin/dashboard/stats` 200 | **#9 ✅** |
| GIS Places `/daoanh/places/` | ✅ map + search | ✅ | ✅ | **#6** |
| PlaceVN Mapping | ✅ page load | ✅ | ✅ | — |
| Name Vi Map | ✅ queue + translate | ✅ | ✅ 48,412 records | **#1** |
| TTL Rebuild | ✅ v4.0 loading | ✅ | ✅ | — |
| Search All | ✅ | ✅ | ✅ | — |
| Keyword Import | ✅ | ✅ | ✅ | — |
| Entity API `/{id}` | ✅ | ✅ | ✅ Thiếu Lâm Tự | — |
| Passages API `/{id}/passages` | ✅ | ✅ | ⚠️ count=0 | **#2** |
| CBETA Catalog VN | ✅ | ✅ | ✅ 3,122 records | **#3** |

---

## Task Priority Queue

### 🔴 Task 1 — Seed monk từ persons.json (48K records)
- **Nguồn:** DILA / Khoá 1
- **Mô tả:** namevi-queue API có 48,412 records, nhưng chỉ 335/48,412 có `name_vi`. Cần ETL bulk auto-generate từ persons.json.
- **API evidence:** `GET /daoanh/api/admin/namevi-queue` → `{"all": 48412, "approved": 335}`
- **Cách tiếp cận:** 
  - Đọc persons.json → extract tên Hán + metadata
  - Chạy Hán-Việt transliteration cho từng tên
  - Bulk upsert vào namevi_map_places

### 🔴 Task 2 — Passage_VI + entity summary (CBETA)
- **Nguồn:** CBETA / Khoá 1
- **Mô tả:** `/entity/PL000000023255/passages` trả `count=0`. Cần import thêm CBETA texts, build PASSAGE_VI translations, entity summary API via LLM.
- **API evidence:** `{"count": 0, "passages": []}`
- **Cách tiếp cận:**
  - Kiểm tra dữ liệu CBETA hiện có trong cbeta.db
  - Import thêm texts nếu cần
  - Xây PASSAGE_VI table
  - Entity summary endpoint

### 🟡 Task 3 — Fuzzy matching title_zh ↔ place (CBETA Catalog)
- **Nguồn:** CBETA Catalog / Khoá 1
- **Mô tả:** Hiện dùng LIKE matching, cần RapidFuzz để match mờ.

### 🟡 Task 4 — Term glossaries → people/works (Marcus)
- **Nguồn:** Marcus / Khoá 1
- **Mô tả:** Chưa link Marcus với DILA people/works.

### 🟡 Task 5 — TTL VN → authority Person VN ✅ (2026-07-29)
- **Nguồn:** TTL / Khoá 2
- **Trạng thái:** Đã xây `vn_person_authority` + relations/places/works/events từ 16 file TTL (`data/ttl/old/`). ETL: `scripts/etl_ttl_person_authority.py`. Session log: `docs/sessions/2026-07-29_etl_ttl_person_authority.md`.
- **Còn lại:** ETL cho ~2000 file TTL còn lại, gắn `dila_id` cho 11 nhân vật chưa verified, tích hợp API/UI.

### 🟡 Task 6 — GIS cluster click handler
- **Nguồn:** GIS / Khoá 1
- **Mô tả:** Cluster chưa zoom-to-bounds khi click.

### 🟡 Task 7 — Wikipedia multi-language fallback
- **Nguồn:** Wikipedia / Khoá 1
- **Mô tả:** Cache refresh + fallback mạnh hơn.

### 🟡 Task 8 — Missing hanzi admin view
- **Nguồn:** Hán-Việt / Khoá 1
- **Mô tả:** Bảng missing_hanzi có nhưng chưa có UI admin.

### ⚪ Task 9 — Dashboard stats API 404 fix ✅ (2026-08-14)
- **Nguồn:** Hạ tầng / Khoá 1
- **Mô tả:** `/api/admin/dashboard/stats` trả 404.
- **Trạng thái:** ✅ Đã fix — thêm alias route `/api/admin/dashboard/stats` + `/daoanh/api/admin/dashboard/stats` vào `api_dashboard_stats()` (app.py:6057). Session log: `docs/sessions/2026-08-14_t09_dashboard_stats_api.md`.

---

## GUI Working Pages (confirmed 2026-07-29)

```
GET / → 200 Landing
GET /daoanh/admin/ → 200 Dashboard v4.0
GET /daoanh/places/ → 200 GIS Map
GET /daoanh/admin/placevn.html → 200 PlaceVN
GET /daoanh/admin/namevimap.html → 200 NameVi Map
GET /daoanh/admin/panorama.html → 200 TTL Rebuild v4.0
GET /daoanh/admin/search_all.html → 200 Search
GET /daoanh/admin/keyword_import.html → 200 Keyword Import
```

## API Working (confirmed 2026-07-29)

```
200 GET /daoanh/api/entity/PL000000023255  → Thiếu Lâm Tự
200 GET /daoanh/api/admin/namevi-queue     → 48,412 records
200 GET /daoanh/api/admin/places_search    → DB-mode OK
200 GET /daoanh/api/admin/dashboard/stats  → ✅ Fixed (2026-08-14) alias route
404 GET /daoanh/api/monk_names              → (thientong.py, not daoanh)
```
